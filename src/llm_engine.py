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
        simple_status = {
            "location": context.get("location", {}).get("name"),
            "exits": [e.get("name") for e in context.get("exits", [])],
            "entities": [e.get("name") for e in context.get("entities", [])],
            "player_faction": context.get("player_faction", {}).get("name")
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
