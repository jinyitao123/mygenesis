"""
ECA (Event-Condition-Action) 规则引擎

基于PRP文档的规则模型架构：
Intent (Event) -> Validation (Condition) -> Rules (Action)

核心组件：
1. Event: 用户意图/系统事件
2. Condition: 验证逻辑 (Cypher/Python)
3. Action: 执行链 (修改图/记录事件/生成记忆)
"""

import logging
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import json
from datetime import datetime

from backend.core.models import ActionTypeDefinition, OntologyModel
from backend.core.validation_engine import ValidationEngine

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """事件类型枚举"""
    USER_INTENT = "user_intent"          # 用户意图
    SYSTEM_EVENT = "system_event"        # 系统事件
    STATE_CHANGE = "state_change"        # 状态变化
    TIMER_EVENT = "timer_event"          # 定时器事件
    EXTERNAL_TRIGGER = "external_trigger" # 外部触发


class RuleType(str, Enum):
    """规则类型枚举"""
    MODIFY_GRAPH = "modify_graph"        # 修改图数据
    RECORD_EVENT = "record_event"        # 记录事件
    MEMORIZE = "memorize"                # 生成向量记忆
    NOTIFY = "notify"                    # 发送通知
    EXECUTE_SCRIPT = "execute_script"    # 执行脚本


class ValidationType(str, Enum):
    """验证类型枚举"""
    CYPHER_CHECK = "cypher_check"        # Cypher验证
    PYTHON_EXPRESSION = "python_expression" # Python表达式
    CUSTOM_FUNCTION = "custom_function"  # 自定义函数


class Event:
    """事件类"""
    
    def __init__(self, 
                 event_type: EventType,
                 source: str,
                 data: Dict[str, Any],
                 timestamp: Optional[datetime] = None):
        self.event_type = event_type
        self.source = source
        self.data = data
        self.timestamp = timestamp or datetime.now()
        self.event_id = f"{event_type.value}_{self.timestamp.strftime('%Y%m%d_%H%M%S_%f')}"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "source": self.source,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """从字典创建"""
        return cls(
            event_type=EventType(data["event_type"]),
            source=data["source"],
            data=data["data"],
            timestamp=datetime.fromisoformat(data["timestamp"])
        )


class Condition:
    """条件类"""
    
    def __init__(self,
                 condition_type: ValidationType,
                 expression: str,
                 parameters: Optional[Dict[str, Any]] = None,
                 description: Optional[str] = None):
        self.condition_type = condition_type
        self.expression = expression
        self.parameters = parameters or {}
        self.description = description
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        评估条件
        
        Args:
            context: 评估上下文
            
        Returns:
            条件是否满足
        """
        try:
            if self.condition_type == ValidationType.CYPHER_CHECK:
                return self._evaluate_cypher(context)
            elif self.condition_type == ValidationType.PYTHON_EXPRESSION:
                return self._evaluate_python(context)
            elif self.condition_type == ValidationType.CUSTOM_FUNCTION:
                return self._evaluate_custom(context)
            else:
                logger.error(f"未知的条件类型: {self.condition_type}")
                return False
        except Exception as e:
            logger.error(f"条件评估失败: {e}")
            return False
    
    def _evaluate_cypher(self, context: Dict[str, Any]) -> bool:
        """评估Cypher条件"""
        # TODO: 实现Cypher查询执行
        # 这里需要连接到Neo4j并执行查询
        logger.info(f"评估Cypher条件: {self.expression}")
        logger.info(f"参数: {self.parameters}")
        logger.info(f"上下文: {context}")
        
        # 模拟实现 - 实际需要集成Neo4j驱动
        return True
    
    def _evaluate_python(self, context: Dict[str, Any]) -> bool:
        """评估Python表达式"""
        try:
            # 安全地评估Python表达式
            # 注意：实际使用中需要限制可用的函数和模块
            local_vars = {**context, **self.parameters}
            
            # 简单的表达式评估
            # 这里使用eval，实际生产环境应该使用更安全的替代方案
            result = eval(self.expression, {"__builtins__": {}}, local_vars)
            
            return bool(result)
        except Exception as e:
            logger.error(f"Python表达式评估失败: {e}")
            return False
    
    def _evaluate_custom(self, context: Dict[str, Any]) -> bool:
        """评估自定义函数"""
        # TODO: 实现自定义函数调用
        # 需要注册自定义函数到规则引擎
        logger.info(f"评估自定义条件: {self.expression}")
        return True


class RuleAction:
    """规则动作类"""
    
    def __init__(self,
                 rule_type: RuleType,
                 configuration: Dict[str, Any],
                 description: Optional[str] = None):
        self.rule_type = rule_type
        self.configuration = configuration
        self.description = description
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行规则动作
        
        Args:
            context: 执行上下文
            
        Returns:
            执行结果
        """
        try:
            if self.rule_type == RuleType.MODIFY_GRAPH:
                return self._execute_modify_graph(context)
            elif self.rule_type == RuleType.RECORD_EVENT:
                return self._execute_record_event(context)
            elif self.rule_type == RuleType.MEMORIZE:
                return self._execute_memorize(context)
            elif self.rule_type == RuleType.NOTIFY:
                return self._execute_notify(context)
            elif self.rule_type == RuleType.EXECUTE_SCRIPT:
                return self._execute_script(context)
            else:
                logger.error(f"未知的规则类型: {self.rule_type}")
                return {"success": False, "error": f"未知规则类型: {self.rule_type}"}
        except Exception as e:
            logger.error(f"规则执行失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _execute_modify_graph(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行图修改"""
        # TODO: 实现Neo4j图修改
        cypher_query = self.configuration.get("cypher_query", "")
        parameters = self.configuration.get("parameters", {})
        
        logger.info(f"执行图修改: {cypher_query}")
        logger.info(f"参数: {parameters}")
        
        # 模拟实现
        return {
            "success": True,
            "message": "图修改执行成功",
            "changes": 1
        }
    
    def _execute_record_event(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """记录事件"""
        event_data = self.configuration.get("event_data", {})
        event_type = self.configuration.get("event_type", "system_event")
        
        logger.info(f"记录事件: {event_type}")
        logger.info(f"事件数据: {event_data}")
        
        # 模拟实现
        return {
            "success": True,
            "message": "事件记录成功",
            "event_id": f"event_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        }
    
    def _execute_memorize(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """生成向量记忆"""
        content = self.configuration.get("content", "")
        embedding_model = self.configuration.get("embedding_model", "default")
        
        logger.info(f"生成向量记忆: {content[:50]}...")
        logger.info(f"嵌入模型: {embedding_model}")
        
        # 模拟实现
        return {
            "success": True,
            "message": "向量记忆生成成功",
            "embedding_id": f"embed_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        }
    
    def _execute_notify(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """发送通知"""
        message = self.configuration.get("message", "")
        recipients = self.configuration.get("recipients", [])
        notification_type = self.configuration.get("type", "info")
        
        logger.info(f"发送通知: {message}")
        logger.info(f"接收者: {recipients}")
        logger.info(f"类型: {notification_type}")
        
        # 模拟实现
        return {
            "success": True,
            "message": "通知发送成功",
            "notification_id": f"notify_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        }
    
    def _execute_script(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行脚本"""
        script = self.configuration.get("script", "")
        language = self.configuration.get("language", "python")
        
        logger.info(f"执行脚本: {language}")
        logger.info(f"脚本内容: {script[:100]}...")
        
        # 模拟实现
        return {
            "success": True,
            "message": "脚本执行成功",
            "output": "脚本执行完成"
        }


class Rule:
    """规则类"""
    
    def __init__(self,
                 rule_id: str,
                 name: str,
                 event_pattern: Dict[str, Any],
                 conditions: List[Condition],
                 actions: List[RuleAction],
                 priority: int = 0,
                 enabled: bool = True,
                 description: Optional[str] = None):
        self.rule_id = rule_id
        self.name = name
        self.event_pattern = event_pattern
        self.conditions = conditions
        self.actions = actions
        self.priority = priority
        self.enabled = enabled
        self.description = description
    
    def matches(self, event: Event) -> bool:
        """
        检查事件是否匹配规则
        
        Args:
            event: 事件对象
            
        Returns:
            是否匹配
        """
        if not self.enabled:
            return False
        
        # 检查事件类型
        if "event_type" in self.event_pattern:
            if self.event_pattern["event_type"] != event.event_type.value:
                return False
        
        # 检查事件源
        if "source" in self.event_pattern:
            if self.event_pattern["source"] != event.source:
                return False
        
        # 检查事件数据
        if "data_pattern" in self.event_pattern:
            data_pattern = self.event_pattern["data_pattern"]
            if not self._match_data_pattern(event.data, data_pattern):
                return False
        
        return True
    
    def _match_data_pattern(self, data: Dict[str, Any], pattern: Dict[str, Any]) -> bool:
        """匹配数据模式"""
        for key, value in pattern.items():
            if key not in data:
                return False
            
            if isinstance(value, dict) and "pattern" in value:
                # 正则表达式匹配
                import re
                pattern_str = value["pattern"]
                if not re.match(pattern_str, str(data[key])):
                    return False
            elif isinstance(value, list):
                # 列表匹配（值在列表中）
                if data[key] not in value:
                    return False
            else:
                # 精确匹配
                if data[key] != value:
                    return False
        
        return True
    
    def execute(self, event: Event, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行规则
        
        Args:
            event: 触发事件
            context: 执行上下文
            
        Returns:
            执行结果
        """
        if not self.matches(event):
            return {"success": False, "error": "事件不匹配规则"}
        
        # 评估所有条件
        for condition in self.conditions:
            if not condition.evaluate(context):
                return {
                    "success": False,
                    "error": f"条件不满足: {condition.description or condition.expression}",
                    "failed_condition": condition.expression
                }
        
        # 执行所有动作
        results = []
        for action in self.actions:
            result = action.execute(context)
            results.append(result)
            
            if not result.get("success", False):
                return {
                    "success": False,
                    "error": f"动作执行失败: {action.description or action.rule_type.value}",
                    "failed_action": action.rule_type.value,
                    "partial_results": results
                }
        
        return {
            "success": True,
            "message": "规则执行成功",
            "results": results,
            "rule_id": self.rule_id,
            "event_id": event.event_id
        }


class RuleEngine:
    """规则引擎"""
    
    def __init__(self, validation_engine: ValidationEngine):
        self.validation_engine = validation_engine
        self.rules: Dict[str, Rule] = {}
        self.event_history: List[Event] = []
        self.max_history_size = 1000
    
    def register_rule(self, rule: Rule) -> bool:
        """注册规则"""
        if rule.rule_id in self.rules:
            logger.warning(f"规则已存在: {rule.rule_id}")
            return False
        
        self.rules[rule.rule_id] = rule
        logger.info(f"规则注册成功: {rule.rule_id} - {rule.name}")
        return True
    
    def unregister_rule(self, rule_id: str) -> bool:
        """取消注册规则"""
        if rule_id not in self.rules:
            logger.warning(f"规则不存在: {rule_id}")
            return False
        
        del self.rules[rule_id]
        logger.info(f"规则取消注册: {rule_id}")
        return True
    
    def process_event(self, event: Event, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        处理事件
        
        Args:
            event: 事件对象
            context: 执行上下文
            
        Returns:
            执行结果列表
        """
        # 记录事件
        self.event_history.append(event)
        if len(self.event_history) > self.max_history_size:
            self.event_history = self.event_history[-self.max_history_size:]
        
        # 准备上下文
        execution_context = context or {}
        execution_context["event"] = event.to_dict()
        execution_context["timestamp"] = event.timestamp.isoformat()
        
        # 查找匹配的规则
        matched_rules = []
        for rule in self.rules.values():
            if rule.matches(event):
                matched_rules.append(rule)
        
        # 按优先级排序
        matched_rules.sort(key=lambda r: r.priority, reverse=True)
        
        # 执行匹配的规则
        results = []
        for rule in matched_rules:
            try:
                result = rule.execute(event, execution_context)
                result["rule_id"] = rule.rule_id
                result["rule_name"] = rule.name
                results.append(result)
                
                # 如果规则执行失败，记录错误但不停止其他规则
                if not result.get("success", False):
                    logger.error(f"规则执行失败: {rule.rule_id} - {result.get('error')}")
                
            except Exception as e:
                logger.error(f"规则执行异常: {rule.rule_id} - {e}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "rule_id": rule.rule_id,
                    "rule_name": rule.name
                })
        
        return results
    
    def load_rules_from_action_definitions(self, action_definitions: List[ActionTypeDefinition]) -> int:
        """
        从动作定义加载规则
        
        Args:
            action_definitions: 动作定义列表
            
        Returns:
            加载的规则数量
        """
        loaded_count = 0
        
        for action_def in action_definitions:
            # 创建规则
            rule = self._create_rule_from_action(action_def)
            if rule:
                if self.register_rule(rule):
                    loaded_count += 1
        
        logger.info(f"从动作定义加载了 {loaded_count} 个规则")
        return loaded_count
    
    def _create_rule_from_action(self, action_def: ActionTypeDefinition) -> Optional[Rule]:
        """从动作定义创建规则"""
        try:
            # 创建事件模式
            event_pattern = {
                "event_type": EventType.USER_INTENT.value,
                "data_pattern": {
                    "action": action_def.action_id
                }
            }
            
            # 创建条件
            conditions = []
            if action_def.validation_logic:
                condition_type = ValidationType.CYPHER_CHECK
                expression = action_def.validation_logic.get("cypher_query", "")
                
                if expression:
                    condition = Condition(
                        condition_type=condition_type,
                        expression=expression,
                        parameters=action_def.validation_logic.get("parameters", {}),
                        description=f"验证 {action_def.name}"
                    )
                    conditions.append(condition)
            
            # 创建动作
            actions = []
            for rule_config in action_def.execution_chain:
                rule_type = RuleType(rule_config.get("type", "modify_graph"))
                action = RuleAction(
                    rule_type=rule_type,
                    configuration=rule_config.get("configuration", {}),
                    description=rule_config.get("description")
                )
                actions.append(action)
            
            # 创建规则
            rule = Rule(
                rule_id=f"rule_{action_def.action_id}",
                name=action_def.name,
                event_pattern=event_pattern,
                conditions=conditions,
                actions=actions,
                priority=10,  # 默认优先级
                description=action_def.description
            )
            
            return rule
            
        except Exception as e:
            logger.error(f"从动作定义创建规则失败: {action_def.action_id} - {e}")
            return None
    
    def get_rule_stats(self) -> Dict[str, Any]:
        """获取规则统计信息"""
        total_rules = len(self.rules)
        enabled_rules = sum(1 for r in self.rules.values() if r.enabled)
        
        # 按事件类型统计
        event_type_stats = {}
        for rule in self.rules.values():
            event_type = rule.event_pattern.get("event_type", "unknown")
            event_type_stats[event_type] = event_type_stats.get(event_type, 0) + 1
        
        return {
            "total_rules": total_rules,
            "enabled_rules": enabled_rules,
            "disabled_rules": total_rules - enabled_rules,
            "event_type_stats": event_type_stats,
            "event_history_size": len(self.event_history)
        }
    
    def clear_event_history(self) -> None:
        """清空事件历史"""
        self.event_history = []
        logger.info("事件历史已清空")
    
    def export_rules(self, file_path: str) -> bool:
        """导出规则到文件"""
        try:
            rules_data = []
            for rule in self.rules.values():
                rule_data = {
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "event_pattern": rule.event_pattern,
                    "conditions": [
                        {
                            "condition_type": c.condition_type.value,
                            "expression": c.expression,
                            "parameters": c.parameters,
                            "description": c.description
                        }
                        for c in rule.conditions
                    ],
                    "actions": [
                        {
                            "rule_type": a.rule_type.value,
                            "configuration": a.configuration,
                            "description": a.description
                        }
                        for a in rule.actions
                    ],
                    "priority": rule.priority,
                    "enabled": rule.enabled,
                    "description": rule.description
                }
                rules_data.append(rule_data)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(rules_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"规则导出成功: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"规则导出失败: {e}")
            return False
    
    def import_rules(self, file_path: str) -> int:
        """从文件导入规则"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)
            
            imported_count = 0
            for rule_data in rules_data:
                try:
                    # 创建条件对象
                    conditions = []
                    for cond_data in rule_data.get("conditions", []):
                        condition = Condition(
                            condition_type=ValidationType(cond_data["condition_type"]),
                            expression=cond_data["expression"],
                            parameters=cond_data.get("parameters", {}),
                            description=cond_data.get("description")
                        )
                        conditions.append(condition)
                    
                    # 创建动作对象
                    actions = []
                    for action_data in rule_data.get("actions", []):
                        action = RuleAction(
                            rule_type=RuleType(action_data["rule_type"]),
                            configuration=action_data["configuration"],
                            description=action_data.get("description")
                        )
                        actions.append(action)
                    
                    # 创建规则对象
                    rule = Rule(
                        rule_id=rule_data["rule_id"],
                        name=rule_data["name"],
                        event_pattern=rule_data["event_pattern"],
                        conditions=conditions,
                        actions=actions,
                        priority=rule_data.get("priority", 0),
                        enabled=rule_data.get("enabled", True),
                        description=rule_data.get("description")
                    )
                    
                    if self.register_rule(rule):
                        imported_count += 1
                        
                except Exception as e:
                    logger.error(f"导入规则失败 {rule_data.get('rule_id')}: {e}")
            
            logger.info(f"规则导入成功: {imported_count} 个规则")
            return imported_count
            
        except Exception as e:
            logger.error(f"规则导入失败: {e}")
            return 0