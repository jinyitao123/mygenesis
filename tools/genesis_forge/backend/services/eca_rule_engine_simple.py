"""
简化版ECA规则引擎 (RuleExecutionService)

基于PRP文档第3节的实现：
规则模型采用 ECA (Event-Condition-Action) 变体模式：
Intent (Event) -> Validation (Condition) -> Rules (Action)
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class ECARuleEngine:
    """ECA规则引擎"""
    
    def __init__(self, validation_engine=None):
        self.validation_engine = validation_engine
        self.rules = {}
        logger.info("ECA规则引擎初始化完成")
    
    def simulate_action(self, action_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        模拟运行动作
        
        Args:
            action_id: 动作ID
            parameters: 动作参数
            
        Returns:
            模拟结果
        """
        try:
            # 创建模拟事件
            event = {
                "event_type": "user_intent",
                "source": "simulation",
                "data": {
                    "action": action_id,
                    "parameters": parameters
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # 处理事件
            result = self.process_event(event, {"simulation": True})
            
            return {
                "status": "success",
                "action_id": action_id,
                "simulated": True,
                "execution_result": result
            }
            
        except Exception as e:
            logger.error(f"动作模拟失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "action_id": action_id
            }
    
    def process_event(self, event: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        处理事件
        
        Args:
            event: 事件数据
            context: 处理上下文
            
        Returns:
            处理结果
        """
        try:
            # 生成事件ID
            if "event_id" not in event:
                event_hash = hashlib.md5(json.dumps(event, sort_keys=True).encode()).hexdigest()[:8]
                event["event_id"] = f"event_{event_hash}"
            
            # 查找匹配的规则
            matched_rules = self._find_matching_rules(event)
            
            if not matched_rules:
                return {
                    "status": "no_match",
                    "event_id": event["event_id"],
                    "matched_rules": 0
                }
            
            # 执行规则
            execution_results = []
            
            for rule_id, rule in matched_rules:
                rule_result = self._execute_rule(rule_id, rule, event, context)
                execution_results.append(rule_result)
            
            return {
                "status": "success",
                "event_id": event["event_id"],
                "matched_rules": len(matched_rules),
                "results": execution_results
            }
            
        except Exception as e:
            logger.error(f"处理事件失败: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _find_matching_rules(self, event: Dict[str, Any]) -> List[Tuple[str, Dict]]:
        """查找匹配的规则"""
        matched_rules = []
        
        for rule_id, rule in self.rules.items():
            if self._rule_matches_event(rule, event):
                matched_rules.append((rule_id, rule))
        
        return matched_rules
    
    def _rule_matches_event(self, rule: Dict[str, Any], event: Dict[str, Any]) -> bool:
        """检查规则是否匹配事件"""
        # 检查事件类型
        rule_event_type = rule.get("event_type")
        if rule_event_type and rule_event_type != event.get("event_type"):
            return False
        
        # 检查动作ID
        rule_action = rule.get("action")
        if rule_action:
            event_data = event.get("data", {})
            event_action = event_data.get("action")
            if event_action != rule_action:
                return False
        
        return True
    
    def _execute_rule(self, rule_id: str, rule: Dict[str, Any], 
                     event: Dict[str, Any], context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """执行规则"""
        rule_result = {
            "rule_id": rule_id,
            "success": False,
            "conditions_passed": False,
            "actions_executed": [],
            "errors": []
        }
        
        try:
            # 1. 评估条件
            conditions = rule.get("conditions", [])
            conditions_passed = self._evaluate_conditions(conditions, event, context)
            
            if not conditions_passed:
                rule_result["errors"].append("条件评估未通过")
                return rule_result
            
            rule_result["conditions_passed"] = True
            
            # 2. 执行动作
            actions = rule.get("actions", [])
            actions_result = self._execute_actions(actions, event, context)
            
            rule_result["actions_executed"] = actions_result["executed_actions"]
            rule_result["errors"].extend(actions_result["errors"])
            
            # 3. 确定执行结果
            rule_result["success"] = actions_result["success"]
            
            return rule_result
            
        except Exception as e:
            logger.error(f"规则执行失败: {rule_id}, 错误: {e}")
            rule_result["errors"].append(str(e))
            return rule_result
    
    def _evaluate_conditions(self, conditions: List[Dict[str, Any]], 
                           event: Dict[str, Any], context: Optional[Dict[str, Any]]) -> bool:
        """评估条件"""
        if not conditions:
            return True
        
        # 合并上下文
        eval_context = {}
        if context:
            eval_context.update(context)
        eval_context["event"] = event
        
        for condition in conditions:
            condition_type = condition.get("type")
            
            try:
                if condition_type == "cypher_check":
                    passed = self._evaluate_cypher_condition(condition, eval_context)
                elif condition_type == "python_expression":
                    passed = self._evaluate_python_condition(condition, eval_context)
                else:
                    logger.warning(f"未知的条件类型: {condition_type}")
                    passed = True
                
                if not passed:
                    return False
                
            except Exception as e:
                logger.error(f"条件评估失败: {condition_type}, 错误: {e}")
                return False
        
        return True
    
    def _evaluate_cypher_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """评估Cypher条件"""
        # 简化实现：总是返回True
        return True
    
    def _evaluate_python_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """评估Python条件"""
        expression = condition.get("expression", "")
        
        if not expression:
            return True
        
        try:
            # 安全地评估Python表达式
            local_vars = {**context}
            result = eval(expression, {"__builtins__": {}}, local_vars)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Python条件评估失败: {e}")
            return False
    
    def _execute_actions(self, actions: List[Dict[str, Any]], 
                        event: Dict[str, Any], context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """执行动作"""
        result = {
            "success": True,
            "executed_actions": [],
            "errors": []
        }
        
        if not actions:
            return result
        
        # 合并上下文
        exec_context = {}
        if context:
            exec_context.update(context)
        exec_context["event"] = event
        
        for action in actions:
            action_type = action.get("type")
            action_description = action.get("description", action_type)
            
            try:
                action_result = None
                
                if action_type == "modify_graph":
                    action_result = self._execute_modify_graph(action, exec_context)
                elif action_type == "record_event":
                    action_result = self._execute_record_event(action, exec_context)
                elif action_type == "notify":
                    action_result = self._execute_notify(action, exec_context)
                else:
                    logger.warning(f"未知的动作类型: {action_type}")
                    action_result = {"status": "skipped", "reason": f"未知动作类型: {action_type}"}
                
                # 记录执行结果
                result["executed_actions"].append({
                    "type": action_type,
                    "description": action_description,
                    "result": action_result
                })
                
            except Exception as e:
                logger.error(f"动作执行失败: {action_type}, 错误: {e}")
                result["errors"].append(f"{action_type}: {str(e)}")
                result["success"] = False
        
        return result
    
    def _execute_modify_graph(self, action: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行图修改动作"""
        cypher_query = action.get("cypher_query", "")
        
        # 验证Cypher语法
        if self.validation_engine and cypher_query:
            valid, errors = self.validation_engine.validate_cypher_query(cypher_query)
            if not valid:
                return {
                    "status": "error",
                    "error": f"Cypher语法错误: {errors}"
                }
        
        return {
            "status": "simulated",
            "cypher_query": cypher_query,
            "message": "图修改动作已模拟执行"
        }
    
    def _execute_record_event(self, action: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行事件记录动作"""
        event_type = action.get("event_type", "system_event")
        event_data = action.get("data", {})
        
        logger.info(f"记录事件: {event_type}")
        
        return {
            "status": "success",
            "event_type": event_type,
            "event_data": event_data
        }
    
    def _execute_notify(self, action: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行通知动作"""
        message = action.get("content", "")
        
        logger.info(f"发送通知: {message[:50]}...")
        
        return {
            "status": "success",
            "message": message
        }
    
    def add_rule(self, rule_id: str, rule: Dict[str, Any]) -> bool:
        """添加规则"""
        try:
            # 验证规则
            if not self._validate_rule(rule):
                return False
            
            self.rules[rule_id] = rule
            logger.info(f"添加规则: {rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"添加规则失败: {e}")
            return False
    
    def _validate_rule(self, rule: Dict[str, Any]) -> bool:
        """验证规则"""
        # 检查必要字段
        if "name" not in rule:
            logger.error("规则缺少 name 字段")
            return False
        
        # 验证条件
        conditions = rule.get("conditions", [])
        for condition in conditions:
            if not self._validate_condition(condition):
                return False
        
        # 验证动作
        actions = rule.get("actions", [])
        for action in actions:
            if not self._validate_action(action):
                return False
        
        return True
    
    def _validate_condition(self, condition: Dict[str, Any]) -> bool:
        """验证条件"""
        if "type" not in condition:
            logger.error("条件缺少 type 字段")
            return False
        
        condition_type = condition["type"]
        
        if condition_type == "cypher_check":
            if "query" not in condition:
                logger.error("Cypher条件缺少 query 字段")
                return False
            
            # 验证Cypher语法
            if self.validation_engine:
                cypher_query = condition["query"]
                valid, errors = self.validation_engine.validate_cypher_query(cypher_query)
                if not valid:
                    logger.error(f"Cypher条件语法错误: {errors}")
                    return False
        
        elif condition_type == "python_expression":
            if "expression" not in condition:
                logger.error("Python条件缺少 expression 字段")
                return False
        
        else:
            logger.warning(f"未知的条件类型: {condition_type}")
        
        return True
    
    def _validate_action(self, action: Dict[str, Any]) -> bool:
        """验证动作"""
        if "type" not in action:
            logger.error("动作缺少 type 字段")
            return False
        
        action_type = action["type"]
        
        if action_type == "modify_graph":
            if "cypher_query" not in action:
                logger.error("图修改动作缺少 cypher_query 字段")
                return False
            
            # 验证Cypher语法
            if self.validation_engine:
                cypher_query = action["cypher_query"]
                valid, errors = self.validation_engine.validate_cypher_query(cypher_query)
                if not valid:
                    logger.error(f"图修改动作Cypher语法错误: {errors}")
                    return False
        
        elif action_type == "record_event":
            if "event_type" not in action:
                logger.error("事件记录动作缺少 event_type 字段")
                return False
        
        elif action_type == "notify":
            if "content" not in action:
                logger.error("通知动作缺少 content 字段")
                return False
        
        else:
            logger.warning(f"未知的动作类型: {action_type}")
        
        return True
    
    def load_example_rules(self):
        """加载示例规则"""
        example_rules = {
            "attack_rule": {
                "name": "攻击动作规则",
                "description": "处理攻击动作",
                "event_type": "user_intent",
                "action": "ACT_ATTACK",
                "conditions": [
                    {
                        "type": "python_expression",
                        "expression": "event.get('data', {}).get('parameters', {}).get('distance', 0) < 2",
                        "description": "检查距离是否小于2米"
                    }
                ],
                "actions": [
                    {
                        "type": "modify_graph",
                        "cypher_query": "MATCH (source {id: $source_id}), (target {id: $target_id}) SET target.hp = target.hp - $damage RETURN target.hp",
                        "description": "扣除目标HP"
                    },
                    {
                        "type": "record_event",
                        "event_type": "combat_event",
                        "data": {
                            "action": "attack",
                            "damage": "$damage",
                            "attacker": "$source_id",
                            "target": "$target_id"
                        },
                        "description": "记录战斗事件"
                    }
                ]
            },
            "move_rule": {
                "name": "移动动作规则",
                "description": "处理移动动作",
                "event_type": "user_intent",
                "action": "ACT_MOVE",
                "conditions": [
                    {
                        "type": "cypher_check",
                        "query": "MATCH path = (source {id: $source_id})-[*1..5]-(target {id: $target_id}) RETURN path IS NOT NULL as reachable",
                        "description": "检查路径是否连通"
                    }
                ],
                "actions": [
                    {
                        "type": "modify_graph",
                        "cypher_query": "MATCH (entity {id: $entity_id}), (location {id: $location_id}) MERGE (entity)-[r:LOCATED_AT]->(location) SET r.timestamp = timestamp() RETURN entity, location",
                        "description": "更新位置关系"
                    }
                ]
            }
        }
        
        for rule_id, rule in example_rules.items():
            self.add_rule(rule_id, rule)
        
        logger.info(f"加载了 {len(example_rules)} 个示例规则")


# 创建规则引擎实例的工厂函数
def create_rule_engine(validation_engine=None):
    """创建规则引擎实例"""
    engine = ECARuleEngine(validation_engine)
    engine.load_example_rules()
    return engine