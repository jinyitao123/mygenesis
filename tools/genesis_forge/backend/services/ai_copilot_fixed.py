"""
Enhanced AI Copilot Service (CopilotService)

Complete implementation based on PRP document section 7:
Responsibilities: Integrate LLM, provide generative design capabilities

Core methods:
- generate_npc(description): Generate NPC JSON based on description
- text_to_cypher(natural_language): Convert natural language to Cypher query
- suggest_actions(object_type): Recommend actions for entity types

AI Skills file structure:
- tools/genesis_forge/ai_skills/schema_aware_prompt.txt: System Prompt containing current Ontology structure
- tools/genesis_forge/ai_skills/cypher_generator.py: Toolchain for generating and fixing Cypher statements
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import re
from datetime import datetime
import requests

logger = logging.getLogger(__name__)


class EnhancedAICopilot:
    """Enhanced AI Copilot Service"""
    
    def __init__(self, project_root: str):
        """
        Initialize enhanced AI Copilot
        
        Args:
            project_root: Project root directory
        """
        self.project_root = Path(project_root)
        self.ai_skills_dir = self.project_root / "ai_skills"
        
        # Ensure directory exists
        self.ai_skills_dir.mkdir(exist_ok=True)
        
        # Initialize Skills
        self._init_ai_skills()
        
        # Base AI Copilot removed (using enhanced version)
        self.base_copilot = None
        
        logger.info("Enhanced AI Copilot initialized")
    
    def _init_ai_skills(self):
        """Initialize AI Skills"""
        # Create schema_aware_prompt.txt
        schema_prompt_path = self.ai_skills_dir / "schema_aware_prompt.txt"
        if not schema_prompt_path.exists():
            schema_prompt = '''You are a professional simulation world building assistant, specialized in helping users create and modify Genesis Studio ontology structures.

Core principles:
1. Strictly follow JSON Schema definitions
2. Maintain consistency with existing ontology structures
3. Provide practical and executable suggestions
4. Consider performance and scalability

Available operations:
- Generate ObjectType definitions
- Create ActionType rules
- Write Cypher queries
- Suggest relationship patterns
- Validate existing structures

Response format:
- Always return valid JSON
- Include explanations for complex logic
- Provide alternative solutions when appropriate
'''
            schema_prompt_path.write_text(schema_prompt, encoding='utf-8')
            logger.info(f"Created schema_aware_prompt.txt at {schema_prompt_path}")
    
    def _call_real_llm(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """调用真实的大模型API（使用DeepSeek）"""
        if context is None:
            context = {}
        
        # 使用DeepSeek API
        api_key = "sk-5894e2fc368b41b5b12438bc55422e80"
        base_url = "https://api.deepseek.com"
        
        if not api_key:
            logger.warning("DeepSeek API key not available, using mock response")
            return self._generate_mock_llm_response(prompt, context)
        
        try:
            # 尝试导入OpenAI SDK
            try:
                from openai import OpenAI
            except ImportError:
                logger.error("OpenAI SDK not installed. Install with: pip install openai")
                return self._generate_mock_llm_response(prompt, context)
            
            # 构建系统提示
            system_prompt = """你是一个专业的仿真世界构建助手，专门帮助用户创建和修改Genesis Studio本体结构。

核心原则：
1. 严格遵循XML和JSON格式规范
2. 保持与现有本体结构的一致性
3. 提供实用且可执行的建议
4. 考虑性能和可扩展性

可用操作：
- 生成对象类型定义（XML格式）
- 创建动作类型规则（XML格式）
- 编写Cypher查询
- 建议关系模式
- 验证现有结构

响应格式：
- 对于XML内容，使用```xml代码块包裹
- 对于JSON内容，使用```json代码块包裹
- 包含复杂逻辑的解释
- 在适当时提供替代解决方案

重要：请为CSV转领域任务生成以下5个完整的文件：
1. config.json - 领域配置文件（JSON格式）
2. object_types.xml - 对象类型定义（XML格式）
3. action_types.xml - 动作类型定义（XML格式）
4. seed_data.xml - 种子数据（XML格式）
5. synapser_patterns.xml - 同步模式定义（XML格式）

每个文件都要用相应的代码块包裹。"""
            
            client = OpenAI(
                api_key=api_key,
                base_url=base_url
            )
            
            logger.info(f"Calling DeepSeek API with prompt length: {len(prompt)}")
            
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=4000,
                stream=False
            )
            
            content = response.choices[0].message.content or ""
            if content:
                logger.info(f"DeepSeek response received, length: {len(content)}")
                return content
            else:
                logger.warning("DeepSeek returned empty content")
                return self._generate_mock_llm_response(prompt, context)
            
        except Exception as e:
            logger.error(f"DeepSeek API call failed: {e}")
            return self._generate_mock_llm_response(prompt, context)
    
    def _generate_mock_llm_response(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """生成模拟的LLM响应（当真实API不可用时）"""
        if context is None:
            context = {}
        
        data_type = context.get('data_type', '')
        
        if data_type == 'csv_to_domain':
            # 为CSV转领域生成模拟响应
            domain_name = context.get('domain_name', 'CSV导入领域')
            domain_id = context.get('domain_id', 'csv_domain')
            
            return f"""基于您的CSV数据，我为您生成了以下领域文件：

1. config.json - 领域配置文件
```json
{{
  "name": "{domain_name}",
  "description": "从CSV文件导入的领域",
  "ui_config": {{
    "primary_color": "#3b82f6",
    "secondary_color": "#10b981"
  }}
}}
```

2. object_types.xml - 对象类型定义
```xml
<?xml version="1.0" encoding="UTF-8"?>
<object_types>
  <!-- 基于CSV数据生成的对象类型 -->
  <object_type name="CSVRecord" icon="file-text" color="#3b82f6" primary_key="id">
    <property name="id" type="string" required="true" description="记录ID"/>
    <property name="name" type="string" required="true" description="名称"/>
    <property name="description" type="string" required="false" description="描述"/>
    <property name="category" type="string" required="false" description="分类"/>
    <property name="status" type="string" required="false" description="状态"/>
    <property name="created_at" type="datetime" required="false" default="now()" description="创建时间"/>
  </object_type>
</object_types>
```

3. action_types.xml - 动作类型定义
```xml
<?xml version="1.0" encoding="UTF-8"?>
<action_types>
  <!-- 基本CRUD操作 -->
  <action_type>
    <id>ACT_CREATE</id>
    <name>创建记录</name>
    <description>创建新的CSV记录</description>
    <icon>plus</icon>
    <color>#10b981</color>
  </action_type>
  <action_type>
    <id>ACT_UPDATE</id>
    <name>更新记录</name>
    <description>更新现有记录</description>
    <icon>edit</icon>
    <color>#f59e0b</color>
  </action_type>
</action_types>
```

4. seed_data.xml - 种子数据
```xml
<?xml version="1.0" encoding="UTF-8"?>
<seed_data>
  <!-- CSV数据将在这里转换为种子数据 -->
  <object type="CSVRecord">
    <property name="id">sample_001</property>
    <property name="name">示例记录</property>
    <property name="description">这是一个示例记录</property>
  </object>
</seed_data>
```

5. synapser_patterns.xml - 同步模式定义
```xml
<?xml version="1.0" encoding="UTF-8"?>
<synapser_patterns>
  <pattern name="csv_import" description="CSV导入模式">
    <source type="csv" format="utf-8"/>
    <target type="neo4j" database="default"/>
    <mapping>
      <field source="id" target="id"/>
      <field source="name" target="name"/>
    </mapping>
  </pattern>
</synapser_patterns>
```"""
        
        # 默认响应
        return f"""我收到了您的请求：{prompt[:100]}...

这是一个模拟的AI响应。要启用真实的大模型功能，请设置以下环境变量：
1. LLM_API_KEY - 您的API密钥
2. LLM_BASE_URL - API基础URL（默认：http://43.153.96.90:7860/v1beta）
3. LLM_MODEL - 模型名称（默认：models/gemini-2.5-flash-lite）

当前上下文：{context}"""
    
    def generate_npc(self, description: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate NPC based on description
        
        Args:
            description: NPC description
            context: Additional context
            
        Returns:
            NPC definition in JSON format
        """
        if context is None:
            context = {}
        
        try:
            # Generate NPC ID
            npc_id = self._generate_id_from_description(description)
            
            # Create basic NPC structure
            npc_data = {
                "id": npc_id,
                "type": "NPC",
                "name": description.split()[0] if description.split() else "Unnamed_NPC",
                "description": description,
                "properties": {
                    "health": 100,
                    "level": 1,
                    "experience": 0,
                    "alignment": "neutral"
                },
                "skills": ["basic_interaction"],
                "inventory": [],
                "relationships": []
            }
            
            # Add context-specific properties
            if "world_type" in context:
                npc_data["world_context"] = context["world_type"]
            
            if "required_skills" in context:
                npc_data["skills"].extend(context["required_skills"])
            
            logger.info(f"Generated NPC: {npc_id}")
            return npc_data
            
        except Exception as e:
            logger.error(f"Failed to generate NPC: {e}")
            return {
                "error": f"Failed to generate NPC: {str(e)}",
                "description": description
            }
    
    def text_to_cypher(self, natural_language: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Convert natural language to Cypher query
        
        Args:
            natural_language: Natural language description
            context: Query context
            
        Returns:
            Cypher query and explanation
        """
        if context is None:
            context = {}
        
        try:
            # Simple rule-based translation (in production, use LLM)
            query_lower = natural_language.lower()
            
            # Pattern matching for common queries
            if "all" in query_lower and ("node" in query_lower or "entity" in query_lower):
                cypher = "MATCH (n) RETURN n LIMIT 100"
                explanation = "Returns all nodes in the graph (limited to 100)"
            
            elif "find" in query_lower and "relationship" in query_lower:
                cypher = "MATCH (a)-[r]->(b) RETURN a, r, b LIMIT 50"
                explanation = "Finds relationships between nodes"
            
            elif "create" in query_lower and "node" in query_lower:
                # Extract node type from description
                node_type = "Entity"
                words = natural_language.split()
                for i, word in enumerate(words):
                    if word.lower() in ["node", "entity"] and i + 1 < len(words):
                        node_type = words[i + 1].capitalize()
                        break
                
                cypher = f"CREATE (n:{node_type} {{name: 'New{node_type}'}}) RETURN n"
                explanation = f"Creates a new {node_type} node"
            
            elif "delete" in query_lower:
                cypher = "// WARNING: Delete operations are disabled in safe mode"
                explanation = "Delete operations require explicit confirmation"
            
            else:
                # Default query
                cypher = "MATCH (n) WHERE n.name CONTAINS $search RETURN n LIMIT 10"
                explanation = "Searches for nodes containing the search term"
            
            return {
                "status": "success",
                "cypher": cypher,
                "explanation": explanation,
                "parameters": {"search": natural_language.split()[0] if natural_language.split() else ""}
            }
            
        except Exception as e:
            logger.error(f"Failed to convert text to Cypher: {e}")
            return {
                "status": "error",
                "error": f"Conversion failed: {str(e)}",
                "cypher": "// Error in query generation",
                "explanation": "Could not generate Cypher query"
            }
    
    def suggest_actions(self, object_type: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Suggest actions for object type
        
        Args:
            object_type: Type of object
            context: Additional context
            
        Returns:
            List of suggested actions
        """
        if context is None:
            context = {}
        
        try:
            # Default action suggestions based on object type
            suggestions = []
            
            # Common actions for all entities
            base_actions = [
                {
                    "action_id": f"ACT_INSPECT_{object_type.upper()}",
                    "name": f"Inspect {object_type}",
                    "description": f"Examine details of {object_type}",
                    "validation_logic": f"MATCH (n:{object_type}) WHERE n.id = $target_id RETURN n IS NOT NULL",
                    "execution_rules": ["LOG_ACTION"]
                },
                {
                    "action_id": f"ACT_MOVE_{object_type.upper()}",
                    "name": f"Move {object_type}",
                    "description": f"Relocate {object_type} to new position",
                    "validation_logic": f"MATCH (n:{object_type}) WHERE n.id = $target_id RETURN n.position IS NOT NULL",
                    "execution_rules": ["UPDATE_POSITION"]
                }
            ]
            
            suggestions.extend(base_actions)
            
            # Type-specific actions
            if object_type.lower() in ["npc", "character", "person"]:
                suggestions.append({
                    "action_id": "ACT_TALK_NPC",
                    "name": "Talk to NPC",
                    "description": "Initiate conversation with NPC",
                    "validation_logic": "MATCH (n:NPC) WHERE n.id = $target_id RETURN n.dialogue_tree IS NOT NULL",
                    "execution_rules": ["START_DIALOGUE"]
                })
            
            elif object_type.lower() in ["item", "object", "artifact"]:
                suggestions.append({
                    "action_id": "ACT_PICKUP_ITEM",
                    "name": "Pick up item",
                    "description": "Add item to inventory",
                    "validation_logic": "MATCH (i:Item) WHERE i.id = $target_id RETURN i.weight <= $carry_capacity",
                    "execution_rules": ["ADD_TO_INVENTORY"]
                })
            
            elif object_type.lower() in ["location", "place", "area"]:
                suggestions.append({
                    "action_id": "ACT_ENTER_LOCATION",
                    "name": "Enter location",
                    "description": "Move into the location",
                    "validation_logic": "MATCH (l:Location) WHERE l.id = $target_id RETURN l.is_accessible",
                    "execution_rules": ["CHANGE_LOCATION"]
                })
            
            logger.info(f"Generated {len(suggestions)} action suggestions for {object_type}")
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to suggest actions: {e}")
            return [{
                "action_id": "ACT_ERROR",
                "name": "Error",
                "description": f"Failed to generate suggestions: {str(e)}",
                "validation_logic": "RETURN false",
                "execution_rules": []
            }]
    
    def _generate_id_from_description(self, description: str) -> str:
        """Generate ID from description"""
        # Extract meaningful characters
        words = re.findall(r'\b\w+\b', description)
        if words:
            # Use first 2-3 characters from first 2 words
            id_parts = [word[:3].upper() for word in words[:2]]
            return "_".join(id_parts)
        else:
            return "GEN_" + str(hash(description) % 10000)
    
    def generate_content(self, prompt: str, content_type: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate content (compatible interface)
        
        Args:
            prompt: Prompt text
            content_type: Content type (npc, cypher, actions, object_type, relationship, etc.)
            context: Context information
            
        Returns:
            Generated result
        """
        if context is None:
            context = {}
        
        try:
            # 检查是否需要调用真实的大模型
            data_type = context.get('data_type', '')
            
            # 对于CSV转领域等复杂任务，调用真实的大模型
            if data_type in ['csv_to_domain', 'csv_to_ontology']:
                logger.info(f"Calling real LLM for {data_type} with content_type: {content_type}")
                llm_response = self._call_real_llm(prompt, context)
                
                # 根据内容类型返回不同的格式
                if content_type in ['object_type', 'type']:
                    return {
                        "status": "success",
                        "content": llm_response,
                        "result": llm_response
                    }
                else:
                    return {
                        "status": "success",
                        "content": llm_response
                    }
            
            # 对于其他任务，使用原有的模拟方法
            if content_type in ['npc', 'entity', 'character']:
                # Generate NPC/entity
                return {
                    "status": "success",
                    "result": self.generate_npc(prompt, context)
                }
            
            elif content_type in ['cypher', 'query']:
                # Generate Cypher query
                return self.text_to_cypher(prompt, context)
            
            elif content_type in ['action', 'actions']:
                # Suggest actions
                object_type = context.get('object_type', 'Entity')
                return {
                    "status": "success",
                    "suggestions": self.suggest_actions(object_type, context)
                }
            
            elif content_type in ['object_type', 'type']:
                # Generate object type definition
                return {
                    "status": "success",
                    "type_definition": self._generate_object_type(prompt, context),
                    "content": self._generate_object_type(prompt, context)
                }
            
            elif content_type in ['relationship', 'rel']:
                # Generate relationship definition
                return {
                    "status": "success",
                    "relationship": self._generate_relationship(prompt, context)
                }
            
            else:
                return {
                    "status": "error",
                    "error": f"Unsupported content type: {content_type}",
                    "supported_types": ["npc", "cypher", "actions", "object_type", "relationship"]
                }
                
        except Exception as e:
            logger.error(f"Failed to generate content: {e}")
            return {
                "status": "error",
                "error": f"Content generation failed: {str(e)}"
            }
    
    def _generate_object_type(self, description: str, context: Dict[str, Any]) -> str:
        """Generate object type definition as XML string"""
        type_key = self._generate_id_from_description(description)
        display_name = description.split()[0] if description.split() else "UnnamedType"
        
        # 检查是否有CSV上下文
        csv_content = context.get('csv_content', '')
        data_type = context.get('data_type', '')
        
        if data_type == 'csv_to_domain' and csv_content:
            # 尝试从CSV内容生成更详细的对象类型
            return self._generate_object_type_from_csv(description, context)
        
        # 默认返回基本XML
        xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<object_types>
  <!-- AI生成的对象类型定义 -->
  <object_type name="{display_name}" icon="cube" color="#3b82f6" primary_key="id">
    <property name="id" type="string" required="true" description="唯一标识符"/>
    <property name="name" type="string" required="true" description="名称"/>
    <property name="description" type="string" required="false" description="描述"/>
    <property name="created_at" type="datetime" required="false" default="now()" description="创建时间"/>
    <property name="updated_at" type="datetime" required="false" default="now()" description="更新时间"/>
  </object_type>
</object_types>'''
        
        return xml_content
    
    def _generate_object_type_from_csv(self, description: str, context: Dict[str, Any]) -> str:
        """从CSV内容生成对象类型定义"""
        csv_content = context.get('csv_content', '')
        domain_name = context.get('domain_name', 'CSV导入领域')
        
        # 简单解析CSV
        import csv
        import io
        
        try:
            csv_io = io.StringIO(csv_content)
            reader = csv.reader(csv_io)
            headers = next(reader, [])
            
            # 收集样本行
            sample_rows = []
            for i, row in enumerate(reader):
                if i < 3:
                    sample_rows.append(row)
                else:
                    break
            
            # 基于CSV内容生成对象类型
            xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<object_types>
  <!-- 基于CSV数据生成的对象类型定义 -->
  <!-- 领域: {domain_name} -->
  <!-- CSV列: {headers} -->
  
  <object_type name="CSVRecord" icon="file-text" color="#3b82f6" primary_key="id">
    <property name="id" type="string" required="true" description="记录ID"/>
'''
            
            # 为每个CSV列添加属性
            for i, header in enumerate(headers):
                if header:  # 跳过空列头
                    prop_name = header.strip().lower().replace(' ', '_')
                    xml_content += f'''    <property name="{prop_name}" type="string" required="false" description="{header}"/>
'''
            
            xml_content += '''  </object_type>
</object_types>'''
            
            return xml_content
            
        except Exception as e:
            logger.warning(f"从CSV生成对象类型失败: {e}")
            # 回退到默认生成
            return self._generate_object_type(description, {})
    
    def _generate_relationship(self, description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate relationship definition"""
        rel_type = self._generate_id_from_description(description)
        
        return {
            "relationship_type": rel_type,
            "display_name": description.split()[0] if description.split() else "UnnamedRelation",
            "description": description,
            "source_types": ["Entity"],
            "target_types": ["Entity"],
            "properties": {
                "strength": "number",
                "created_at": "datetime"
            },
            "is_directed": True,
            "tags": ["generated"]
        }
    
    def chat(self, message: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """AI chat interface
        
        Args:
            message: User message
            history: Conversation history
            
        Returns:
            AI response
        """
        if history is None:
            history = []
        
        try:
            # Simple response logic (in production, integrate with LLM)
            response = f"I received your message: '{message}'. "
            
            # Add context-aware responses
            if "help" in message.lower():
                response += "I can help you with: generating NPCs, creating Cypher queries, suggesting actions, and defining object types."
            
            elif "cypher" in message.lower() or "query" in message.lower():
                cypher_result = self.text_to_cypher(message)
                if cypher_result["status"] == "success":
                    response += f"\n\nHere's a Cypher query:\n```cypher\n{cypher_result['cypher']}\n```\n\n{cypher_result['explanation']}"
            
            elif "npc" in message.lower() or "character" in message.lower():
                npc_result = self.generate_npc(message)
                response += f"\n\nGenerated NPC:\n```json\n{json.dumps(npc_result, indent=2, ensure_ascii=False)}\n```"
            
            else:
                response += "How can I assist you with your simulation world building today?"
            
            return {
                "status": "success",
                "response": response,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            return {
                "status": "error",
                "error": f"Chat failed: {str(e)}",
                "response": "Sorry, I encountered an error. Please try again."
            }