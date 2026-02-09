"""
Rule Engine - 规则引擎

职责：
- 根据 rule.type 路由到不同存储后端
- 支持的规则类型：
  - modify_graph: 修改当前状态 → Neo4j
  - record_event: 记录事件 → PostgreSQL Event Ledger
  - memorize: 语义记忆 → PostgreSQL + pgvector
  - record_telemetry: 遥测数据 → VictoriaMetrics (未来扩展)
"""

from typing import Dict, Any, Optional
from genesis.kernel.connectors.neo4j_connector import Neo4jConnector
from genesis.kernel.connectors.postgres_connector import PostgresConnector
import logging

logger = logging.getLogger(__name__)


class RuleEngine:
    """规则引擎 - 多模态存储路由"""

    def __init__(self, neo4j_conn: Neo4jConnector, postgres_conn: PostgresConnector):
        """
        初始化规则引擎

        Args:
            neo4j_conn: Neo4j 连接器实例 (L1)
            postgres_conn: PostgreSQL 连接器实例 (L2/L3)
        """
        self.neo4j = neo4j_conn
        self.postgres = postgres_conn

    def execute_rule(self, rule: Dict[str, Any], context: Dict[str, Any], action_id: str) -> Dict[str, Any]:
        """
        执行单个规则

        Args:
            rule: 规则定义，包含 type, description, statement 等
            context: 执行上下文，包含参数 (如 source_id, target_id, damage)
            action_id: 动作 ID (用于事件记录)

        Returns:
            执行结果字典
        """
        rule_type = rule.get('type')

        if rule_type == 'modify_graph':
            return self._execute_modify_graph(rule, context)
        elif rule_type == 'record_event':
            return self._execute_record_event(rule, context, action_id)
        elif rule_type == 'memorize':
            return self._execute_memorize(rule, context)
        elif rule_type == 'record_telemetry':
            return self._execute_record_telemetry(rule, context)
        else:
            logger.warning(f"[RuleEngine] Unknown rule type: {rule_type}")
            return {"success": False, "message": f"未知的规则类型: {rule_type}"}

    def _execute_modify_graph(self, rule: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        L1: 修改当前状态 → Neo4j

        Args:
            rule: 包含 statement 的 Cypher 查询
            context: 参数上下文

        Returns:
            执行结果
        """
        statement = rule.get('statement', '')
        description = rule.get('description', '修改图状态')

        if not statement:
            logger.error("[RuleEngine] modify_graph rule missing statement")
            return {"success": False, "message": "规则缺少 statement 字段"}

        try:
            # Reason: 使用 execute_write 确保写操作的事务性
            result = self.neo4j.execute_write(statement, context)

            # Reason: 简化返回，只记录成功状态和影响行数
            affected_count = len(result) if isinstance(result, list) else 1

            logger.info(f"[RuleEngine] L1 Modify Graph: {description} - 影响 {affected_count} 条记录")
            return {"success": True, "message": description, "affected": affected_count}

        except Exception as e:
            logger.error(f"[RuleEngine] Neo4j write failed: {e}")
            return {"success": False, "message": f"Neo4j 写入失败: {e}"}

    def _execute_record_event(self, rule: Dict[str, Any], context: Dict[str, Any], action_id: str) -> Dict[str, Any]:
        """
        L2: 记录事件 → PostgreSQL Event Ledger

        Args:
            rule: 包含 summary_template 的事件摘要模板
            context: 执行上下文 (包含 initiator_id, target_id 等)
            action_id: 动作类型 ID

        Returns:
            执行结果
        """
        summary_template = rule.get('summary_template', '{action_type}')
        description = rule.get('description', '记录事件')

        # Reason: 使用模板生成摘要，支持动态变量
        # 为缺失的变量提供默认值
        formatted_context = context.copy()
        formatted_context['action_type'] = action_id
        
        # 为常见缺失变量提供默认值
        if 'target_name' not in formatted_context:
            formatted_context['target_name'] = '周围环境'
        if 'source_name' not in formatted_context:
            formatted_context['source_name'] = '玩家'
        if 'damage' not in formatted_context:
            formatted_context['damage'] = 0
            
        try:
            summary = summary_template.format(**formatted_context)
        except KeyError as e:
            logger.warning(f"[RuleEngine] Template variable missing: {e}, using fallback")
            summary = f"{action_id} 执行完成"

        event_data = {
            "action_type": action_id,
            "initiator_id": context.get('source_id'),
            "initiator_name": context.get('source_name'),
            "target_id": context.get('target_id'),
            "target_name": context.get('target_name'),
            "summary": summary,
            "context": context,
            "changes": rule.get('changes', {})
        }

        try:
            event_id = self.postgres.log_event(event_data)
            logger.info(f"[RuleEngine] L2 Record Event: {summary} (ID: {event_id})")
            return {"success": True, "message": description, "event_id": event_id}

        except Exception as e:
            logger.error(f"[RuleEngine] PostgreSQL event logging failed: {e}")
            return {"success": False, "message": f"事件记录失败: {e}"}

    def _replace_template_vars(self, template: str, context: Dict[str, Any]) -> str:
        """
        替换模板字符串中的变量
        
        Args:
            template: 包含 {variable} 的模板字符串
            context: 变量上下文
            
        Returns:
            替换后的字符串
        """
        if not template:
            return ""
            
        try:
            # 简单的字符串格式化
            return template.format(**context)
        except KeyError as e:
            logger.warning(f"[RuleEngine] Template variable missing: {e} in '{template}'")
            # 尝试部分替换
            result = template
            for key, value in context.items():
                placeholder = f"{{{key}}}"
                if placeholder in result:
                    result = result.replace(placeholder, str(value))
            return result
        except Exception as e:
            logger.error(f"[RuleEngine] Template replacement failed: {e}")
            return template
    
    def _execute_memorize(self, rule: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        L3: 语义记忆 → PostgreSQL + pgvector

        Args:
            rule: 包含 entity_id, content, memory_type 等字段
            context: 执行上下文

        Returns:
            执行结果
        """
        # 处理模板变量替换
        raw_entity_id = rule.get('entity_id', '')
        entity_id = self._replace_template_vars(raw_entity_id, context)
        
        # 如果替换失败且是模板字符串，尝试直接获取
        if not entity_id and raw_entity_id and '{' in raw_entity_id:
            # 尝试从模板中提取变量名
            import re
            match = re.search(r'{(\w+)}', raw_entity_id)
            if match:
                var_name = match.group(1)
                entity_id = context.get(var_name)
        
        if not entity_id:
            entity_id = context.get('target_id')
            
        content = self._replace_template_vars(rule.get('content', ''), context)
        if not content:
            content = context.get('content', '')
            
        memory_type = rule.get('memory_type', 'event')

        if not entity_id or not content:
            logger.warning("[RuleEngine] memorize rule missing entity_id or content")
            logger.info(f"[RuleEngine] Debug - raw_entity_id: '{raw_entity_id}', entity_id: '{entity_id}'")
            logger.info(f"[RuleEngine] Debug - content: '{content}', context keys: {list(context.keys())}")
            return {"success": False, "message": "规则缺少 entity_id 或 content 字段"}

        try:
            # Reason: PostgresConnector.memorize 期望 content 为字符串，不是 dict
            memory_id = self.postgres.memorize(
                content=str(content),
                entity_id=entity_id,
                memory_type=memory_type
            )
            logger.info(f"[RuleEngine] L3 Memorize: {memory_type} for {entity_id} (ID: {memory_id})")
            return {"success": True, "message": "记忆已保存", "memory_id": memory_id}

        except Exception as e:
            logger.error(f"[RuleEngine] PostgreSQL memorize failed: {e}")
            return {"success": False, "message": f"记忆保存失败: {e}"}

    def _execute_record_telemetry(self, rule: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        L4: 遥测数据 → VictoriaMetrics (未来扩展)

        Args:
            rule: 包含 metric_name, entity_id, property, value 等字段
            context: 执行上下文

        Returns:
            执行结果 (当前为占位实现)
        """
        metric_name = rule.get('metric_name', 'unknown_metric')
        entity_id = rule.get('entity_id', '')
        property_name = rule.get('property', 'value')
        value = rule.get('value', 0)

        # Reason: VictoriaMetrics 尚未集成，暂时记录到日志
        logger.info(
            f"[RuleEngine] L4 Telemetry (placeholder): "
            f"{metric_name}[{entity_id}] {property_name}={value}"
        )

        # Reason: 返回成功以不阻塞主流程，实际实现需要集成 VictoriaMetrics
        return {
            "success": True,
            "message": "遥测已记录 (占位实现)",
            "metric_name": metric_name,
            "entity_id": entity_id,
            "property": property_name,
            "value": value
        }

    def execute_rules(self, rules: list, context: Dict[str, Any], action_id: str) -> list:
        """
        批量执行规则列表

        Args:
            rules: 规则列表
            context: 执行上下文
            action_id: 动作 ID

        Returns:
            执行结果列表
        """
        results = []

        for rule in rules:
            try:
                result = self.execute_rule(rule, context, action_id)
                results.append({
                    "rule": rule,
                    "result": result
                })
            except Exception as e:
                logger.error(f"[RuleEngine] Rule execution failed: {e}")
                results.append({
                    "rule": rule,
                    "result": {"success": False, "message": f"规则执行异常: {e}"}
                })

        return results
