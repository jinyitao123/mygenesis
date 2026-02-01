import json
import os
import re
from typing import Dict, Any, Optional
import requests
import logging

logger = logging.getLogger(__name__)


class LLMEngine:
    """LLM 语义引擎 (Gemini API 版本)
    
    负责与 Gemini API 交互，实现：
    1. 世界生成：将自然语言描述转换为图数据库 JSON 结构
    2. 意图解析：将玩家输入解析为结构化动作
    3. 叙事生成：为游戏事件生成 RPG 风格描述
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        base_url: Optional[str] = None
    ) -> None:
        """初始化 LLM 引擎
        
        Args:
            api_key: API 密钥（默认从环境变量 LLM_API_KEY 读取）
            base_url: API 基础 URL（默认从环境变量 LLM_BASE_URL 读取）
        """
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.base_url = base_url or os.getenv(
            "LLM_BASE_URL", 
            "http://43.153.96.90:7860/v1beta"
        )
        
        if not self.api_key:
            raise ValueError("必须提供 LLM API 密钥")
        
        self.world_gen_model = os.getenv(
            "WORLD_GEN_MODEL", 
            "models/gemini-2.5-flash-lite"
        )
        self.intent_model = os.getenv(
            "INTENT_MODEL", 
            "models/gemini-2.5-flash-lite"
        )
        logger.info("LLM 引擎初始化完成 (Gemini API)")
    
    def _call_api(self, model: str, contents: list) -> str:
        """调用 Gemini API
        
        Args:
            model: 模型名称
            contents: 对话内容列表
        
        Returns:
            API 返回的文本内容
        """
        url = f"{self.base_url}/{model}:generateContent"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "contents": contents
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            # Reason: Gemini API 返回格式与 OpenAI 不同
            if "candidates" in data and len(data["candidates"]) > 0:
                candidate = data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    text = candidate["content"]["parts"][0].get("text", "")
                    return text
            
            logger.error(f"API 响应格式异常: {data}")
            return ""
            
        except Exception as e:
            logger.error(f"API 调用失败: {e}")
            raise
    
    def generate_world_schema(
        self, 
        user_prompt: str
    ) -> Dict[str, Any]:
        """根据用户描述生成世界图谱 JSON
        
        使用 Gemini API 生成结构化的世界数据，包含节点（实体）和边（关系）。
        
        Args:
            user_prompt: 用户的世界观描述（如"充满僵尸的废弃医院"）
        
        Returns:
            包含 nodes 和 edges 的字典
            如果 API 调用失败，返回静态备用模板
        """
        system_prompt = """你是一个专业的游戏世界设计器。生成符合以下本体的游戏世界 JSON。

# Ontology Rules
1. 节点类型 (Labels):
   - Player: {id, name, hp=100, faction='PlayerFaction'}
   - Location: {id, name, description}
   - NPC: {id, name, hp, damage, faction, dialogue, disposition}
   - Faction: {id, name, description}

2. 关系类型 (Types):
   - LOCATED_AT: (Entity) -> (Location)
   - CONNECTED_TO: (Location) -> (Location)
   - BELONGS_TO: (Player/NPC) -> (Faction)
   - HOSTILE_TO: (Faction) -> (Faction)

3. 生成要求:
   - 必须生成 2-3 个 Faction 节点 (例如: 官府, 叛军, 平民)。
   - 每个 NPC 必须 BELONGS_TO 一个 Faction。
   - 必须生成至少一组 HOSTILE_TO 关系 (定义谁恨谁)。
   - NPC 必须有 dialogue (中文对话) 和 disposition (aggressive/neutral/friendly)。
   - 确保地图 (Location) 是连通的。

4. 输出格式:
   纯 JSON，包含 "nodes" 和 "edges" 列表。不要使用 Markdown 代码块。"""
        
        try:
            contents = [
                {
                    "role": "user",
                    "parts": [{"text": system_prompt + "\n\n创建这个世界: " + user_prompt}]
                }
            ]
            
            content = self._call_api(self.world_gen_model, contents)
            
            # Reason: LLM 可能返回 Markdown 代码块，需要提取 JSON
            try:
                world_json = json.loads(content)
            except json.JSONDecodeError:
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    world_json = json.loads(json_match.group())
                else:
                    raise ValueError("无法从响应中提取 JSON")
            
            # 基础验证
            if "nodes" not in world_json or "edges" not in world_json:
                raise ValueError("LLM 返回的 JSON 缺少必要字段")
            
            logger.info(
                f"世界生成成功：{len(world_json['nodes'])} 节点，"
                f"{len(world_json['edges'])} 关系"
            )
            return world_json
            
        except Exception as e:
            logger.error(f"世界生成失败: {e}，使用备用模板")
            return self._fallback_world_template(user_prompt)
    
    def _fallback_world_template(self, prompt: str) -> Dict[str, Any]:
        """备用世界模板（当 LLM 失败时使用）"""
        return {
            "nodes": [
                {
                    "id": "player1",
                    "label": "Player",
                    "properties": {"name": "冒险者", "hp": 100}
                },
                {
                    "id": "start_room",
                    "label": "Location",
                    "properties": {
                        "name": "起始房间", 
                        "description": "一个简单的房间"
                    }
                },
                {
                    "id": "enemy1",
                    "label": "NPC",
                    "properties": {"name": "守卫", "damage": 5}
                }
            ],
            "edges": [
                {
                    "source": "player1", 
                    "target": "start_room", 
                    "type": "LOCATED_AT"
                },
                {
                    "source": "enemy1", 
                    "target": "start_room", 
                    "type": "LOCATED_AT"
                }
            ]
        }
    
    def interpret_action(self, player_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """将玩家自然语言输入解析为结构化意图
        
        使用 Gemini API 解析意图，返回包含 intent、target、narrative 的字典。
        上下文（当前位置、出口、可见实体）注入到 prompt 中以提高准确性。
        
        Args:
            player_input: 玩家输入的自然语言（如"逃到书房去"）
            context: 当前游戏状态上下文
                - location: 当前位置信息
                - exits: 可通行出口列表
                - entities: 可见实体列表
                - player: 玩家状态
        
        Returns:
            包含以下字段的字典：
            - intent: 意图类型 (MOVE|ATTACK|LOOK|UNKNOWN)
            - target: 目标名称（如有）
            - narrative: 中文动作描述（用于AI旁白）
        """
        # 简化 status 以减少 token 消耗
        player_faction = context.get("player_faction")
        simple_status = {
            "location": context.get("location", {}).get("name"),
            "exits": [e.get("name") for e in context.get("exits", [])],
            "entities": [e.get("name") for e in context.get("entities", [])],
            "player_faction": player_faction.get("name") if player_faction else None
        }
        
        system_prompt = f"""你是一个文字冒险游戏的意图解析器。

当前游戏状态：
{json.dumps(simple_status, ensure_ascii=False, indent=2)}

玩家输入："{player_input}"

任务：解析意图并返回 JSON。

Intent 类型:
- MOVE: 移动 (target 必须是当前 exits 中的名称)
- TALK: 对话 (target 必须是 entities 中的 NPC 名称)
- INSPECT: 观察 (target 可以是 location, NPC 或 item)
- ATTACK: 攻击 (target 是 entities 中的敌人名称)
- WAIT: 等待/跳过
- UNKNOWN: 无法理解

规则:
1. narrative 应该是流畅的 RPG 风格中文描述。
2. 如果意图是 UNKNOWN，narrative 说明为什么不理解。

JSON 格式: {{"intent": "...", "target": "...", "narrative": "..."}}"""
        
        try:
            contents = [
                {
                    "role": "user",
                    "parts": [{"text": system_prompt}]
                }
            ]
            
            content = self._call_api(self.intent_model, contents)
            
            # Reason: 尝试解析 JSON，处理可能的格式问题
            try:
                action = json.loads(content)
            except json.JSONDecodeError:
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    action = json.loads(json_match.group())
                else:
                    raise ValueError("无法从响应中提取 JSON")
            
            # 验证必要字段
            if "intent" not in action:
                action["intent"] = "UNKNOWN"
            if "target" not in action:
                action["target"] = ""
            if "narrative" not in action:
                action["narrative"] = player_input
            
            logger.info(f"意图解析: {player_input} -> {action['intent']}({action.get('target', '')})")
            return action
            
        except Exception as e:
            logger.error(f"意图解析失败: {e}")
            return {
                "intent": "UNKNOWN",
                "target": "",
                "narrative": f"你不确定如何执行这个动作：{player_input}"
            }

    def generate_narrative(self, event_type: str, details: Dict[str, Any]) -> str:
        try:
            contents = [{"role": "user", "parts": [{"text": f"描述：{event_type} {json.dumps(details, ensure_ascii=False)}"}]}]
            return self._call_api(self.intent_model, contents)[:100]
        except Exception:
            return f"[{event_type}]"
    
    def generate_npc_response(self, player_input: str, npc_data: Dict, player_data: Dict, memory_context: str = "") -> str:
        """
        ★ 生成式对话：基于图谱人设 + 记忆上下文的实时对话生成
        
        双脑协同：
        - 左脑(Neo4j): 提供NPC静态人设
        - 右脑(Postgres): 提供动态记忆上下文
        - LLM: 结合两者生成自然回复
        
        Args:
            player_input: 玩家说的话
            npc_data: NPC 数据 (name, faction, disposition, location, dialogue)
            player_data: 玩家数据 (name, faction)
            memory_context: 记忆上下文（从向量库检索的相关记忆）
        
        Returns:
            LLM 生成的 NPC 回复
        """
        # 构建记忆部分（如果有）
        memory_section = ""
        if memory_context and memory_context != "暂无相关记忆":
            memory_section = f"""
# 相关记忆（你们之前的互动）
{memory_context}

# 记忆使用规则
- 如果玩家提到之前的事情，请参考记忆回答。
- 如果记忆中有你对玩家做出的承诺，请兑现。
- 如果记忆显示玩家曾帮助过你，请表示感谢。
- 回答时要自然，不要生硬地背诵记忆。
"""
        
        system_prompt = f"""你正在扮演一个游戏里的 NPC。请根据以下人设和记忆回答玩家的话。

# NPC 档案 (你的身份)
名字: {npc_data.get('name', '未知')}
阵营: {npc_data.get('faction', '无阵营')}
性格: {npc_data.get('disposition', 'neutral')} (aggressive=粗鲁好战, neutral=冷漠平淡, friendly=热情友好)
当前位置: {npc_data.get('location', '未知地点')}
背景台词风格: "{npc_data.get('dialogue', '...')}" (参考这种语气和用词风格)

# 玩家档案 (对方身份)
名字: {player_data.get('name', '无名氏')}
阵营: {player_data.get('faction', '无阵营')}
{memory_section}
# 角色扮演规则
1. 保持完全的角色扮演，不要跳出戏说"我是一个AI"之类的话。
2. 如果玩家问名字、身份，按你的人设回答，可以编一个符合背景的名字。
3. 语气控制：
   - 如果玩家阵营与你敌对 (HOSTILE_TO 关系)，语气要充满敌意、威胁、不耐烦
   - 如果是同一阵营或友好，要恭敬、热情、愿意帮助
   - 如果是中立，要冷淡、公事公办
4. 回答简短有力（30-50字），符合古代/战国背景的语言风格。
5. 可以反问玩家，增加互动感。

记住：你就是 {npc_data.get('name')}，不是AI。

现在，玩家对你说: "{player_input}""""
        
        try:
            contents = [
                {"role": "user", "parts": [{"text": system_prompt}]},
                {"role": "user", "parts": [{"text": f"玩家对你说: \"{player_input}\""}]}
            ]
            
            response = self._call_api(self.intent_model, contents)
            
            # 清理回复，移除可能的引号
            reply = response.strip().strip('"').strip("'")
            
            logger.info(f"生成式对话: {npc_data.get('name')} -> {reply[:30]}...")
            return reply
            
        except Exception as e:
            logger.error(f"生成式对话失败: {e}")
            # 失败时回退到静态台词
            return npc_data.get('dialogue', '...')
