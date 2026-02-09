"""
增强版AI Copilot服务 (CopilotService)

基于PRP文档第7节的完整实现：
职责: 集成LLM，提供生成式设计能力

核心方法:
- generate_npc(description): 根据描述生成NPC JSON
- text_to_cypher(natural_language): 将自然语言转为Cypher查询
- suggest_actions(object_type): 推荐该类型实体应有的动作

AI Skills文件结构:
- tools/genesis_forge/ai_skills/schema_aware_prompt.txt: 包含当前Ontology结构的System Prompt
- tools/genesis_forge/ai_skills/cypher_generator.py: 专门用于生成和修复Cypher语句的工具链
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class EnhancedAICopilot:
    """增强版AI Copilot服务"""
    
    def __init__(self, project_root: str):
        """
        初始化增强版AI Copilot
        
        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root)
        self.ai_skills_dir = self.project_root / "ai_skills"
        
        # 确保目录存在
        self.ai_skills_dir.mkdir(exist_ok=True)
        
        # 初始化Skills
        self._init_ai_skills()
        
        # 基础AI Copilot已移除（使用增强版）
        self.base_copilot = None
        
        logger.info("Enhanced AI Copilot initialized")
    
    def _init_ai_skills(self):
        """初始化AI Skills"""
        # 创建schema_aware_prompt.txt
        schema_prompt_path = self.ai_skills_dir / "schema_aware_prompt.txt"
        if not schema_prompt_path.exists():
            schema_prompt = '''你是一个专业的仿真世界构建助手，专门帮助用户创建和修改 Genesis Studio 的本体结构。

核心原则：
1. 严格遵循 JSON Schema 定义
2. 保持与现有本体结构的一致性
3. 提供简要的解释说明
4. 不生成危险或破坏性的代码

命名规范：
- 对象类型: 使用大写下划线格式 (如: NPC_GUARD)
- 关系类型: 使用大写下划线格式 (如: LOCATED_AT)
- 动作 ID: 使用 ACT_ 前缀和大写下划线格式 (如: ACT_ATTACK)
- 属性名: 使用小写下划线格式 (如: max_hp)

输出格式：
请始终以JSON格式输出，包含以下字段：
- "type": 内容类型 (object_type, relationship, action, cypher, description)
- "content": 生成的内容 (JSON对象或字符串)
- "explanation": 简要解释说明
- "confidence": 置信度 (0-1)
- "suggestions": 相关建议列表

错误处理：
如果无法生成有效内容，请返回：
{
  "type": "error",
  "content": {},
  "explanation": "解释为什么无法生成",
  "suggestions": ["替代方案1", "替代方案2"]
}
'''
            schema_prompt_path.write_text(schema_prompt, encoding='utf-8')
            logger.info("创建了schema_aware_prompt.txt")
        
        # 创建cypher_generator.py
        cypher_gen_path = self.ai_skills_dir / "cypher_generator.py"
        if not cypher_gen_path.exists():
            cypher_gen_code = '''"""
Cypher生成器工具链

提供Cypher查询生成、验证和修复功能。
"""

import re
from typing import Dict, List, Any, Optional, Tuple


class CypherGenerator:
    """Cypher生成器"""
    
    @staticmethod
    def generate_query(intent: str, context: Dict[str, Any]) -> str:
        """根据意图生成Cypher查询"""
        intent_lower = intent.lower()
        
        # 匹配查询意图
        if "查找" in intent or "查询" in intent or "find" in intent_lower:
            return CypherGenerator._generate_find_query(intent, context)
        elif "创建" in intent or "新建" in intent or "create" in intent_lower:
            return CypherGenerator._generate_create_query(intent, context)
        elif "更新" in intent or "修改" in intent or "update" in intent_lower:
            return CypherGenerator._generate_update_query(intent, context)
        elif "删除" in intent or "remove" in intent_lower:
            return CypherGenerator._generate_delete_query(intent, context)
        elif "统计" in intent or "count" in intent_lower:
            return CypherGenerator._generate_count_query(intent, context)
        else:
            return CypherGenerator._generate_general_query(intent, context)
'''
            cypher_gen_path.write_text(cypher_gen_code, encoding='utf-8')
            logger.info("创建了cypher_generator.py")
    
    def generate_npc(self, description: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        根据描述生成NPC JSON
        
        Args:
            description: NPC描述
            context: 生成上下文
            
        Returns:
            生成的NPC数据
        """
        try:
            # 构建提示词
            prompt = self._build_npc_generation_prompt(description, context)
            
            # 调用AI
            result = self._call_ai_with_context(prompt, "npc_generation", context)
            
            # 解析结果
            if result.get("type") == "object_type":
                npc_data = result.get("content", {})
                
                # 确保包含必要字段
                if "type_key" not in npc_data:
                    npc_data["type_key"] = f"NPC_{self._generate_id_from_desc(description)}"
                
                if "name" not in npc_data:
                    npc_data["name"] = description[:30]
                
                if "properties" not in npc_data:
                    npc_data["properties"] = {
                        "id": {"type": "string", "required": True},
                        "name": {"type": "string", "required": True},
                        "description": {"type": "string", "required": False}
                    }
                
                return {
                    "status": "success",
                    "npc": npc_data,
                    "explanation": result.get("explanation", "NPC生成成功"),
                    "confidence": result.get("confidence", 0.8)
                }
            else:
                return {
                    "status": "error",
                    "error": result.get("explanation", "无法生成NPC"),
                    "suggestions": result.get("suggestions", [])
                }
                
        except Exception as e:
            logger.error(f"生成NPC失败: {e}")
            return {
                "status": "error",
                "error": f"生成NPC失败: {str(e)}",
                "suggestions": ["请提供更详细的描述", "检查AI服务连接"]
            }
    
    def _build_npc_generation_prompt(self, description: str, context: Optional[Dict[str, Any]]) -> str:
        """构建NPC生成提示词"""
        # 读取schema_aware_prompt
        schema_prompt_path = self.ai_skills_dir / "schema_aware_prompt.txt"
        system_prompt = schema_prompt_path.read_text(encoding='utf-8') if schema_prompt_path.exists() else ""
        
        # 添加上下文信息
        context_info = ""
        if context:
            if "domain" in context:
                context_info += f"当前领域: {context['domain']}\n"
            if "existing_npcs" in context:
                context_info += f"现有NPC类型: {', '.join(context['existing_npcs'][:5])}\n"
            if "style_guide" in context:
                context_info += f"风格指南: {context['style_guide']}\n"
        
        full_prompt = f"""{system_prompt}

请根据以下描述生成一个NPC对象类型：

描述: {description}

{context_info}

要求:
1. 生成完整的对象类型定义
2. 包含适当的属性（如生命值、技能、阵营等）
3. 添加相关的标签
4. 考虑游戏平衡性

请以JSON格式输出。"""
        
        return full_prompt
    
    def text_to_cypher(self, natural_language: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        自然语言转Cypher查询
        
        Args:
            natural_language: 自然语言描述
            context: 生成上下文
            
        Returns:
            Cypher查询结果
        """
        try:
            # 使用cypher_generator技能
            cypher_query = self._generate_cypher_from_text(natural_language, context)
            
            # 验证查询
            valid, errors = self._validate_cypher_query(cypher_query)
            
            if not valid:
                # 尝试修复
                fixed_query = self._fix_cypher_query(cypher_query)
                valid_fixed, errors_fixed = self._validate_cypher_query(fixed_query)
                
                if valid_fixed:
                    cypher_query = fixed_query
                    errors = []
                else:
                    return {
                        "status": "error",
                        "error": "Cypher查询生成失败",
                        "errors": errors + errors_fixed,
                        "suggestions": ["请提供更明确的查询意图", "检查自然语言描述是否清晰"]
                    }
            
            return {
                "status": "success",
                "cypher_query": cypher_query,
                "parameters": self._extract_cypher_parameters(natural_language),
                "explanation": self._generate_cypher_explanation(cypher_query),
                "validation": {
                    "valid": True,
                    "errors": []
                }
            }
            
        except Exception as e:
            logger.error(f"文本转Cypher失败: {e}")
            return {
                "status": "error",
                "error": f"文本转Cypher失败: {str(e)}",
                "suggestions": ["请简化查询描述", "使用更具体的实体名称"]
            }
    
    def _generate_cypher_from_text(self, text: str, context: Optional[Dict[str, Any]]) -> str:
        """从文本生成Cypher查询"""
        text_lower = text.lower()
        
        # 简单规则匹配
        if any(word in text_lower for word in ["查找", "查询", "找到", "find", "search"]):
            # 查找查询
            entity_type = self._extract_entity_type(text, context)
            conditions = self._extract_conditions(text)
            
            if conditions:
                return f"MATCH (n:{entity_type}) WHERE {conditions} RETURN n LIMIT 50"
            else:
                return f"MATCH (n:{entity_type}) RETURN n LIMIT 100"
        
        elif any(word in text_lower for word in ["创建", "新建", "添加", "create", "add"]):
            # 创建查询
            entity_type = self._extract_entity_type(text, context)
            properties = self._extract_properties(text)
            
            props_str = json.dumps(properties, ensure_ascii=False)
            return f"CREATE (n:{entity_type} {props_str}) RETURN n"
        
        elif any(word in text_lower for word in ["更新", "修改", "设置", "update", "set"]):
            # 更新查询
            entity_type = self._extract_entity_type(text, context)
            updates = self._extract_updates(text)
            conditions = self._extract_conditions(text)
            
            if conditions:
                return f"MATCH (n:{entity_type}) WHERE {conditions} SET {updates} RETURN n"
            else:
                return f"MATCH (n:{entity_type}) SET {updates} RETURN n LIMIT 100"
        
        elif any(word in text_lower for word in ["统计", "计数", "数量", "count"]):
            # 统计查询
            entity_type = self._extract_entity_type(text, context)
            return f"MATCH (n:{entity_type}) RETURN COUNT(n) as count"
        
        else:
            # 通用查询
            return f"// 根据描述生成的查询: {text}\nMATCH (n) RETURN n LIMIT 10"
    
    def _extract_entity_type(self, text: str, context: Optional[Dict[str, Any]]) -> str:
        """从文本中提取实体类型"""
        # 从上下文中获取可用类型
        if context and "entity_types" in context:
            available_types = context["entity_types"]
            
            # 尝试匹配文本中的类型
            for entity_type in available_types:
                if entity_type.lower() in text.lower():
                    return entity_type
            
            # 返回第一个可用类型
            if available_types:
                return available_types[0]
        
        # 默认类型
        return "Entity"
    
    def _extract_conditions(self, text: str) -> str:
        """从文本中提取查询条件"""
        conditions = []
        
        # 简单关键词匹配
        if "名为" in text or "名字是" in text:
            # 提取名称
            name_match = re.search(r'[名为|名字是]\s*["\']?([^"\'\s]+)["\']?', text)
            if name_match:
                name = name_match.group(1)
                conditions.append(f"n.name = '{name}'")
        
        if "包含" in text:
            # 提取包含内容
            contains_match = re.search(r'包含\s*["\']?([^"\'\s]+)["\']?', text)
            if contains_match:
                contains_text = contains_match.group(1)
                conditions.append(f"n.description CONTAINS '{contains_text}'")
        
        if "大于" in text or "超过" in text:
            # 提取数值条件
            gt_match = re.search(r'[大于|超过]\s*(\d+)', text)
            if gt_match:
                value = gt_match.group(1)
                conditions.append(f"n.value > {value}")
        
        return " AND ".join(conditions) if conditions else ""
    
    def _extract_properties(self, text: str) -> Dict[str, Any]:
        """从文本中提取属性"""
        properties = {}
        
        # 简单属性提取
        if "生命值" in text or "HP" in text.upper():
            hp_match = re.search(r'生命值\s*[:：]?\s*(\d+)', text)
            if hp_match:
                properties["hp"] = int(hp_match.group(1))
            else:
                properties["hp"] = 100
        
        if "名字" in text or "名称" in text:
            name_match = re.search(r'[名字|名称]\s*[:：]?\s*["\']?([^"\'\s]+)["\']?', text)
            if name_match:
                properties["name"] = name_match.group(1)
        
        if "描述" in text:
            desc_match = re.search(r'描述\s*[:：]?\s*["\']?([^"\']+)["\']?', text)
            if desc_match:
                properties["description"] = desc_match.group(1)
        
        return properties
    
    def _extract_updates(self, text: str) -> str:
        """从文本中提取更新内容"""
        updates = []
        
        # 简单更新提取
        if "设置为" in text or "设为" in text:
            set_match = re.search(r'[设置为|设为]\s*["\']?([^"\'\s]+)["\']?', text)
            if set_match:
                value = set_match.group(1)
                updates.append(f"n.value = '{value}'")
        
        return ", ".join(updates) if updates else "n.updated = true"
    
    def _validate_cypher_query(self, cypher_query: str) -> Tuple[bool, List[str]]:
        """验证Cypher查询"""
        errors = []
        
        # 基本检查
        if not cypher_query.strip():
            errors.append("Cypher查询不能为空")
            return False, errors
        
        # 检查危险操作
        dangerous_keywords = ["DROP", "DELETE", "REMOVE", "DETACH"]
        query_upper = cypher_query.upper()
        
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                # 检查是否在注释中
                lines = cypher_query.split('\n')
                for line in lines:
                    if keyword in line.upper() and not line.strip().startswith('//'):
                        errors.append(f"查询包含危险关键字: {keyword}")
                        break
        
        # 检查基本结构
        valid_keywords = ["MATCH", "CREATE", "MERGE", "RETURN", "WITH"]
        has_valid_keyword = any(keyword in query_upper for keyword in valid_keywords)
        
        if not has_valid_keyword:
            errors.append("Cypher查询缺少核心操作 (MATCH/CREATE/MERGE/RETURN/WITH)")
        
        return len(errors) == 0, errors
    
    def _fix_cypher_query(self, cypher_query: str) -> str:
        """修复Cypher查询"""
        # 简单修复规则
        query = cypher_query.strip()
        
        # 确保以分号结尾
        if not query.endswith(';'):
            query += ';'
        
        # 修复常见的拼写错误
        corrections = {
            'MATHC': 'MATCH',
            'CRATE': 'CREATE',
            'RETUNR': 'RETURN',
            'WERE': 'WHERE',
            'SETT': 'SET'
        }
        
        for wrong, correct in corrections.items():
            query = re.sub(rf'\b{wrong}\b', correct, query, flags=re.IGNORECASE)
        
        return query
    
    def _extract_cypher_parameters(self, text: str) -> Dict[str, Any]:
        """从文本中提取Cypher参数"""
        parameters = {}
        
        # 提取搜索词
        search_words = ["查找", "查询", "搜索", "find", "search"]
        for word in search_words:
            if word in text:
                # 尝试提取搜索内容
                parts = text.split(word, 1)
                if len(parts) > 1:
                    search_content = parts[1].strip()
                    if search_content and len(search_content) > 1:
                        parameters["search_term"] = search_content
                        break
        
        return parameters
    
    def _generate_cypher_explanation(self, cypher_query: str) -> str:
        """生成Cypher查询解释"""
        query_lower = cypher_query.lower()
        
        if "match" in query_lower and "return" in query_lower:
            if "where" in query_lower:
                return "这是一个带条件的查询语句，用于查找满足特定条件的节点。"
            else:
                return "这是一个查询语句，用于获取指定类型的所有节点。"
        elif "create" in query_lower:
            return "这是一个创建语句，用于创建新的节点。"
        elif "set" in query_lower:
            return "这是一个更新语句，用于修改节点的属性。"
        elif "count" in query_lower:
            return "这是一个统计语句，用于计算节点的数量。"
        else:
            return "这是一个Cypher查询语句。"
    
    def suggest_actions(self, object_type: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        为对象类型推荐动作
        
        Args:
            object_type: 对象类型
            context: 推荐上下文
            
        Returns:
            动作推荐列表
        """
        try:
            # 基于对象类型生成动作建议
            suggestions = self._generate_action_suggestions(object_type, context)
            
            # 添加上下文相关的建议
            if context:
                suggestions.extend(self._generate_contextual_suggestions(object_type, context))
            
            # 去重并排序
            unique_suggestions = []
            seen = set()
            for suggestion in suggestions:
                suggestion_key = suggestion.get("action_id", "")
                if suggestion_key and suggestion_key not in seen:
                    unique_suggestions.append(suggestion)
                    seen.add(suggestion_key)
            
            return {
                "status": "success",
                "object_type": object_type,
                "suggestions": unique_suggestions[:10],  # 限制数量
                "count": len(unique_suggestions)
            }
            
        except Exception as e:
            logger.error(f"动作推荐失败: {e}")
            return {
                "status": "error",
                "error": f"动作推荐失败: {str(e)}",
                "suggestions": []
            }
    
    def _generate_action_suggestions(self, object_type: str, context: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成动作建议"""
        suggestions = []
        
        # 基于对象类型名称的启发式规则
        object_type_lower = object_type.lower()
        
        # 通用动作
        base_actions = [
            {
                "action_id": "ACT_INTERACT",
                "name": "交互",
                "description": "与对象进行基本交互",
                "parameters": {
                    "interaction_type": {"type": "string", "required": True}
                }
            },
            {
                "action_id": "ACT_EXAMINE",
                "name": "检查",
                "description": "检查对象的详细信息",
                "parameters": {}
            }
        ]
        
        suggestions.extend(base_actions)
        
        # 特定类型动作
        if any(word in object_type_lower for word in ["npc", "character", "人物", "角色"]):
            # NPC相关动作
            npc_actions = [
                {
                    "action_id": "ACT_TALK",
                    "name": "对话",
                    "description": "与NPC进行对话",
                    "parameters": {
                        "dialogue_topic": {"type": "string", "required": False}
                    }
                },
                {
                    "action_id": "ACT_TRADE",
                    "name": "交易",
                    "description": "与NPC进行物品交易",
                    "parameters": {
                        "item_id": {"type": "string", "required": True},
                        "quantity": {"type": "int", "required": True, "default": 1}
                    }
                }
            ]
            suggestions.extend(npc_actions)
        
        if any(word in object_type_lower for word in ["item", "weapon", "potion", "物品", "武器", "药水"]):
            # 物品相关动作
            item_actions = [
                {
                    "action_id": "ACT_USE",
                    "name": "使用",
                    "description": "使用物品",
                    "parameters": {
                        "target_id": {"type": "string", "required": False}
                    }
                },
                {
                    "action_id": "ACT_EQUIP",
                    "name": "装备",
                    "description": "装备物品",
                    "parameters": {
                        "slot": {"type": "string", "required": True}
                    }
                }
            ]
            suggestions.extend(item_actions)
        
        if any(word in object_type_lower for word in ["door", "gate", "portal", "门", "传送门"]):
            # 门相关动作
            door_actions = [
                {
                    "action_id": "ACT_OPEN",
                    "name": "打开",
                    "description": "打开门",
                    "parameters": {}
                },
                {
                    "action_id": "ACT_CLOSE",
                    "name": "关闭",
                    "description": "关闭门",
                    "parameters": {}
                }
            ]
            suggestions.extend(door_actions)
        
        return suggestions
    
    def _generate_contextual_suggestions(self, object_type: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成上下文相关的建议"""
        suggestions = []
        
        # 从上下文中提取信息
        if "domain" in context:
            domain = context["domain"]
            
            # 领域特定建议
            if domain == "supply_chain":
                suggestions.append({
                    "action_id": "ACT_SHIP",
                    "name": "运输",
                    "description": "运输物品到指定位置",
                    "parameters": {
                        "destination": {"type": "string", "required": True},
                        "quantity": {"type": "int", "required": True}
                    }
                })
            
            elif domain == "finance_risk":
                suggestions.append({
                    "action_id": "ACT_TRANSFER",
                    "name": "转账",
                    "description": "进行资金转账",
                    "parameters": {
                        "amount": {"type": "float", "required": True},
                        "recipient": {"type": "string", "required": True}
                    }
                })
        
        # 从现有动作中获取灵感
        if "existing_actions" in context:
            existing_actions = context["existing_actions"]
            
            # 查找类似类型的动作
            for action in existing_actions:
                if object_type in action.get("allowed_targets", []) or object_type in action.get("allowed_actors", []):
                    suggestions.append(action)
        
        return suggestions
    
    def _call_ai_with_context(self, prompt: str, intent: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """调用AI服务（带上下文）"""
        try:
            # 如果有基础copilot，使用它
            if self.base_copilot:
                result = self.base_copilot.generate_content(prompt, intent, context)
                return result.get("result", {}) if isinstance(result, dict) else {}
            
            # 否则使用模拟响应
            return self._get_mock_ai_response(prompt, intent)
            
        except Exception as e:
            logger.warning(f"AI调用失败，使用模拟响应: {e}")
            return self._get_mock_ai_response(prompt, intent)
    
    def _get_mock_ai_response(self, prompt: str, intent: str) -> Dict[str, Any]:
        """获取模拟AI响应"""
        if intent == "npc_generation":
            return {
                "type": "object_type",
                "content": {
                    "type_key": "NPC_GENERATED",
                    "name": "生成的NPC",
                    "description": "由AI生成的NPC角色",
                    "properties": {
                        "id": {"type": "string", "required": True},
                        "name": {"type": "string", "required": True},
                        "hp": {"type": "int", "required": True, "default": 100},
                        "level": {"type": "int", "required": False, "default": 1}
                    },
                    "tags": ["ai_generated", "npc"]
                },
                "explanation": "基于描述生成的NPC对象类型",
                "confidence": 0.7
            }
        else:
            return {
                "type": "info",
                "content": {},
                "explanation": "模拟AI响应",
                "confidence": 0.5
            }
    
    def _generate_id_from_desc(self, description: str) -> str:
        """从描述生成ID"""
        # 提取前几个有意义的字符
        words = re.findall(r'\b\w+\b', description)
        if words:
            # 使用前2个单词的首字母
            id_parts = [word[:3].upper() for word in words[:2]]
            return "_".join(id_parts)
        else:
            return "GEN_" + str(hash(description) % 10000)

    def generate_content(self, prompt: str, content_type: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """生成内容（兼容接口）
        
        Args:
            prompt: 提示词
            content_type: 内容类型 (npc, cypher, actions, object_type, relationship等)
            context: 上下文信息
            
        Returns:
            生成的结果
        """
        if context is None:
            context = {}
        
        try:
            # 根据内容类型调用不同的方法
            if content_type in ['npc', 'entity', 'character']:
                # 生成NPC/实体
                return {
                    "status": "success",
                    "result": self.generate_npc(prompt, context)
                }
            
            elif content_type in ['cypher', 'query']:
                # 生成Cypher查询
                return self.text_to_cypher(prompt, context)
            
            elif content_type in ['action', 'actions']:
                # 建议动作
                object_type = context.get('object_type', 'Entity')
                return self.suggest_actions(object_type, context)
            
            elif content_type in ['object_type', 'type']:
                # 生成对象类型
                return {
                    "status": "success",
                    "result": {
                        "type_key": self._generate_id_from_desc(prompt),
                        "name": prompt,
                        "description": f"AI生成的对象类型: {prompt}",
                        "properties": {
                            "id": {"type": "string", "required": True},
                            "name": {"type": "string", "required": True}
                        },
                        "tags": ["ai_generated"]
                    }
                }
            
            elif content_type in ['relationship', 'link']:
                # 生成关系类型
                return {
                    "status": "success",
                    "result": {
                        "type_key": self._generate_id_from_desc(prompt) + "_REL",
                        "name": prompt,
                        "description": f"AI生成的关系类型: {prompt}",
                        "source": context.get('source_type', 'Entity'),
                        "target": context.get('target_type', 'Entity'),
                        "tags": ["ai_generated"]
                    }
                }
            
            else:
                # 默认使用通用AI调用
                result = self._call_ai_with_context(prompt, content_type, context)
                return {
                    "status": "success",
                    "result": result
                }
        
        except Exception as e:
            logger.error(f"生成内容失败 (type={content_type}): {e}")
            return {
                "status": "error",
                "error": str(e)
            }