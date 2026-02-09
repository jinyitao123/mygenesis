"""
Action Driver - 动作驱动器 (Palantir 模式)

职责：
- 实现完整的 Validation → Rules 操作闭环
- 加载和管理 Action Ontology 定义
- 执行动作：验证前置条件 → 执行规则 → 返回结果

对比当前项目：
- 旧：ActionDriver 只有简单条件检查后直接执行
- 新：完整的四阶段验证流程 + 多模态存储路由
"""

from typing import Dict, Any, Optional, List
from genesis.kernel.connectors.neo4j_connector import Neo4jConnector
from genesis.kernel.rule_engine import RuleEngine
from genesis.kernel.object_manager import ObjectManager
import logging

logger = logging.getLogger(__name__)


class ActionDriver:
    """动作驱动器 - Validation → Rules 闭环"""

    def __init__(self, neo4j_conn: Neo4jConnector, rule_engine: RuleEngine, 
                 object_manager: ObjectManager):
        """
        初始化动作驱动器

        Args:
            neo4j_conn: Neo4j 连接器实例
            rule_engine: 规则引擎实例
            object_manager: 对象管理器实例 (用于对象验证)
        """
        self.neo4j = neo4j_conn
        self.rule_engine = rule_engine
        self.obj_mgr = object_manager
        self.actions_registry = {}  # 存储 Action 本体定义

    def load_actions(self, actions_list: List[Dict[str, Any]]) -> int:
        """
        加载 LLM 生成的 Action Ontology

        Args:
            actions_list: 动作定义列表，每个包含 id, name, validation, rules 等

        Returns:
            加载的动作数量
        """
        count = 0
        for act in actions_list:
            action_id = act.get('id')
            if not action_id:
                logger.warning("[ActionDriver] Action missing 'id', skipping")
                continue

            self.actions_registry[action_id] = act
            count += 1
            logger.debug(f"[ActionDriver] Loaded action: {action_id}")

        logger.info(f"[ActionDriver] Loaded {count} actions")
        return count

    def get_available_actions_desc(self) -> str:
        """
        返回给 LLM 的可用动作列表

        Returns:
            格式化的动作描述字符串
        """
        return ", ".join([
            f"{k}({v['display_name']})"
            for k, v in self.actions_registry.items()
        ])

    def execute(self, action_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        ★ 核心：通用动作执行器 - Validation → Rules 闭环

        执行流程：
        1. 参数验证 (Validate Parameters)
        2. 对象引用验证 (Validate Object References)
        3. 动作规则验证 (Validate Action Rules)
        4. 执行规则效果 (Execute Rules)

        Args:
            action_id: 动作 ID (如 "ACT_ATTACK")
            parameters: 动作参数 (如 {"source_id": "player_001", "target_id": "npc_001"})

        Returns:
            {
                "success": bool,
                "message": str,
                "validation_data": dict,
                "rule_reports": list
            }
        """
        # 阶段 0: 检查动作是否存在
        action_def = self.actions_registry.get(action_id)
        if not action_def:
            return {
                "success": False,
                "message": f"未知的动作: {action_id}",
                "validation_data": {},
                "rule_reports": []
            }

        # 阶段 1: 参数验证
        param_result = self._validate_parameters(action_def, parameters)
        if not param_result["valid"]:
            return {
                "success": False,
                "message": param_result["message"],
                "validation_data": {"stage": "parameters"},
                "rule_reports": []
            }

        # 阶段 2: 对象引用验证
        obj_ref_result = self._validate_object_references(action_def, parameters)
        if not obj_ref_result["valid"]:
            return {
                "success": False,
                "message": obj_ref_result["message"],
                "validation_data": {"stage": "object_references", **obj_ref_result.get("data", {})},
                "rule_reports": []
            }

        # 阶段 3: 动作规则验证 (Cypher Check)
        action_validation = self._validate_action(action_def, parameters)
        if not action_validation["valid"]:
            return {
                "success": False,
                "message": action_validation.get("message", action_def.get('validation', {}).get('error_message', '验证失败')),
                "validation_data": {"stage": "action_rules", **action_validation.get("data", {})},
                "rule_reports": []
            }

        # 阶段 4: 执行规则效果
        # Reason: 将验证阶段的数据合并到上下文中，供 rules 使用
        validation_data = action_validation.get("data", {})
        obj_ref_data = obj_ref_result.get("data", {})
        enriched_context = {**parameters, **obj_ref_data, **validation_data}

        rules = action_def.get('rules', [])
        rule_reports = self.rule_engine.execute_rules(rules, enriched_context, action_id)

        # 检查是否有规则执行失败
        failed_rules = [r for r in rule_reports if not r["result"].get("success", False)]
        if failed_rules:
            return {
                "success": False,
                "message": f"规则执行失败: {failed_rules[0]['result'].get('message', '未知错误')}",
                "validation_data": action_validation.get("data", {}),
                "rule_reports": rule_reports
            }

        # 成功返回
        success_message = action_def.get('narrative_template', f"执行成功: {action_def.get('display_name', action_id)}")
        try:
            success_message = success_message.format(**parameters, **action_validation.get("data", {}))
        except KeyError:
            # Reason: 如果模板变量不存在，使用原始消息
            pass

        return {
            "success": True,
            "message": success_message,
            "validation_data": action_validation.get("data", {}),
            "rule_reports": rule_reports
        }

    def _validate_parameters(self, action_def: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        阶段 1: 验证参数定义和类型

        Args:
            action_def: 动作定义
            parameters: 用户提供的参数

        Returns:
            {"valid": bool, "message": str}
        """
        param_defs = action_def.get('parameters', [])

        for param_def in param_defs:
            param_name = param_def.get('name')
            required = param_def.get('required', False)

            # 检查必需参数
            if required and param_name not in parameters:
                return {
                    "valid": False,
                    "message": f"缺少必需参数: {param_name}"
                }

            # TODO: 未来可添加类型验证
            # param_type = param_def.get('type')
            # if param_type == 'object_ref' and param_name in parameters:
            #     # 验证对象引用格式
            #     pass

        return {"valid": True}

    def _validate_object_references(self, action_def: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        阶段 2: 验证对象引用存在性

        Args:
            action_def: 动作定义
            parameters: 用户提供的参数

        Returns:
            {"valid": bool, "message": str, "data": dict}
        """
        param_defs = action_def.get('parameters', [])
        data = {}

        for param_def in param_defs:
            param_name = param_def.get('name')
            param_type = param_def.get('type')

            # Reason: 只验证 object_ref 类型的参数
            if param_type == 'object_ref' and param_name in parameters:
                object_type = param_def.get('object_type')
                object_id = parameters[param_name]

                # Reason: 使用 ObjectManager 检查对象是否存在
                obj = self.obj_mgr.get_object(object_type, object_id)
                if not obj:
                    return {
                        "valid": False,
                        "message": f"{object_type} '{object_id}' 不存在",
                        "data": data
                    }

                data[f"{param_name}_exists"] = True
                data[f"{param_name}_name"] = obj.get('name', object_id)

        return {"valid": True, "data": data}

    def _validate_action(self, action_def: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        阶段 3: 执行业务规则验证 (Cypher Check)

        Args:
            action_def: 动作定义
            parameters: 用户提供的参数

        Returns:
            {"valid": bool, "message": str, "data": dict}
        """
        validation = action_def.get('validation', {})
        logic_type = validation.get('logic_type', 'always_allow')

        # Reason: 支持 "always_allow" 类型，跳过验证
        if logic_type == 'always_allow':
            return {"valid": True, "data": {}}

        # Reason: 支持 "cypher_check" 类型，执行 Cypher 查询验证
        if logic_type == 'cypher_check':
            statement = validation.get('statement', '')
            if not statement:
                logger.warning(f"[ActionDriver] cypher_check rule missing statement")
                return {"valid": True, "data": {}}  # 缺少语句默认通过

            try:
                result = self.neo4j.run_query(statement, parameters)

                # Reason: Cypher 查询应该返回验证结果，解析返回值
                if result and len(result) > 0:
                    first_result = result[0]

                    # Reason: 支持多种返回格式
                    # 格式 1: 直接返回字段 "is_valid"
                    if 'is_valid' in first_result:
                        is_valid = first_result['is_valid']
                        return {
                            "valid": is_valid,
                            "data": first_result
                        }

                    # 格式 2: 有记录表示有效
                    return {
                        "valid": True,
                        "data": first_result
                    }

                # Reason: 无结果表示验证失败
                return {
                    "valid": False,
                    "data": {},
                    "message": validation.get('error_message', '验证失败：条件不满足')
                }

            except Exception as e:
                logger.error(f"[ActionDriver] Cypher validation failed: {e}")
                return {
                    "valid": False,
                    "data": {},
                    "message": f"规则校验异常: {e}"
                }

        # Reason: 未知类型默认通过
        logger.warning(f"[ActionDriver] Unknown validation type: {logic_type}")
        return {"valid": True, "data": {}}
