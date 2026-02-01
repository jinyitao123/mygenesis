class ActionDriver:
    def __init__(self, neo4j_driver):
        self.driver = neo4j_driver
        self.actions_registry = {} # 存储 Action 本体定义

    def load_actions(self, actions_list):
        """加载 LLM 生成的 Action 本体"""
        count = 0
        for act in actions_list:
            self.actions_registry[act['id']] = act
            count += 1
        return count

    def get_available_actions_desc(self):
        """返回给 LLM 的可用动作列表"""
        return ", ".join([f"{k}({v['name']})" for k, v in self.actions_registry.items()])

    def execute_action(self, action_id, source_id, target_id):
        """
        ★ 核心：通用行动执行器
        不包含业务逻辑，只执行 Cypher
        """
        rule = self.actions_registry.get(action_id)
        if not rule: return False, f"未知的法则: {action_id}"

        with self.driver.session() as session:
            # 1. 验证前置条件 (Condition Check)
            # 动态拼装 Cypher：查找实体 -> 应用 WHERE 条件
            check_cypher = f"""
            MATCH (source), (target)
            WHERE source.id = $sid AND target.id = $tid
            AND ({rule['condition']}) 
            RETURN source.id
            """
            try:
                result = session.run(check_cypher, sid=source_id, tid=target_id).single()
                if not result:
                    return False, f"条件不满足，无法执行 {rule['name']}。"
            except Exception as e:
                return False, f"规则校验异常: {e}"

            # 2. 执行效果 (Effect Execution)
            effect_cypher = f"""
            MATCH (source), (target)
            WHERE source.id = $sid AND target.id = $tid
            {rule['effect']}
            """
            try:
                session.run(effect_cypher, sid=source_id, tid=target_id)
                
                # 3. 生成反馈
                # 简单起见，返回模板消息
                msg = f"执行成功: {rule['name']}"
                if 'narrative_template' in rule:
                    # 获取更新后的属性用于填充模板(简化版)
                    msg = rule['narrative_template']
                
                return True, msg
            except Exception as e:
                return False, f"世界变更异常: {e}"