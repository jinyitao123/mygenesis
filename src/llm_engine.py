"""
LLM Engine v0.3 - 生成式引擎

实现分形生成策略：
1. 世界种子生成 (Meta-Lore)
2. 骨架生成 (核心节点 + 连接)
3. 本地细节填充 (动态补全)

支持：
- Action Ontology 生成
- 意图解析与语义理解
- NPC 生成式对话
"""

import json
import os
import re
from typing import Dict, Any, Optional, List
import requests
import logging

logger = logging.getLogger(__name__)


class LLMEngine:
    """LLM 语义引擎 v0.3 (Gemini API)

    负责与 Gemini API 交互，实现分形世界生成和意图解析。
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ) -> None:
        """初始化 LLM 引擎"""
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.base_url = base_url or os.getenv(
            "LLM_BASE_URL",
            "http://43.153.96.90:7860/v1beta"
        )

        if not self.api_key:
            raise ValueError("必须提供 LLM API 密钥")

        self.world_seed_model = os.getenv(
            "WORLD_SEED_MODEL",
            "models/gemini-2.5-flash-lite"
        )
        self.world_gen_model = os.getenv(
            "WORLD_GEN_MODEL",
            "models/gemini-2.5-flash-lite"
        )
        self.intent_model = os.getenv(
            "INTENT_MODEL",
            "models/gemini-2.5-flash-lite"
        )
        self.action_model = os.getenv(
            "ACTION_MODEL",
            "models/gemini-2.5-flash-lite"
        )

        logger.info("LLM 引擎初始化完成 v0.3 (Gemini API)")

    def _call_api(self, model: str, contents: list) -> str:
        """调用 Gemini API"""
        url = f"{self.base_url}/{model}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {"contents": contents}

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            if "candidates" in data and len(data["candidates"]) > 0:
                candidate = data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    return candidate["content"]["parts"][0].get("text", "")
            logger.error(f"API 响应格式异常: {data}")
            return ""
        except Exception as e:
            logger.error(f"API 调用失败: {e}")
            raise

    def _safe_parse_json(self, content: str) -> Any:
        """安全解析 JSON，处理 Markdown 代码块"""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            raise ValueError("无法从响应中提取 JSON")

    # =========================================================================
    # v0.3 核心：分形世界生成
    # =========================================================================

    def generate_world_seed(self, user_prompt: str) -> Dict[str, Any]:
        """Step 1: 生成世界种子 (Meta-Lore)"""
        system_prompt = """你是一个游戏世界设计师。根据用户描述，生成世界种子。

你需要生成：
1. 世界观主题 (themes)
2. 地点骨架 (locations): 3-5个核心地点
3. 阵营骨架 (factions): 2-3个核心阵营
4. 核心冲突 (conflicts)

输出格式（纯 JSON）：
{
    "themes": ["主题1", "主题2"],
    "locations": [
        {"id": "loc_start", "name": "起始地点", "description": "..."}
    ],
    "factions": [
        {"id": "faction_good", "name": "正义阵营", "stance": "friendly"}
    ],
    "conflicts": [
        {"description": "主要冲突描述", "parties": ["阵营A", "阵营B"]}
    ]
}"""

        try:
            contents = [
                {"role": "user", "parts": [{"text": system_prompt + "\n\n用户描述: " + user_prompt}]}
            ]
            content = self._call_api(self.world_seed_model, contents)
            seed = self._safe_parse_json(content)
            logger.info(f"世界种子生成成功: {len(seed.get('locations', []))} 地点骨架")
            return seed
        except Exception as e:
            logger.error(f"世界种子生成失败: {e}")
            return self._fallback_seed_template(user_prompt)

    def _fallback_seed_template(self, prompt: str) -> Dict[str, Any]:
        """备用世界种子模板"""
        return {
            "themes": ["冒险", "探索"],
            "locations": [
                {"id": "start", "name": "起始地点", "description": "一切开始的地方"}
            ],
            "factions": [
                {"id": "neutral", "name": "中立阵营", "stance": "neutral"}
            ],
            "conflicts": [
                {"description": "探索未知的冒险", "parties": ["玩家", "世界"]}
            ]
        }

    def generate_world_skeleton(self, seed: Dict[str, Any]) -> Dict[str, Any]:
        """Step 2: 生成世界骨架"""
        locations = seed.get('locations', [])
        factions = seed.get('factions', [])
        themes = seed.get('themes', [])

        system_prompt = f"""你是图数据库生成器。基于以下世界种子，生成完整的图结构。

世界种子：
- 主题: {json.dumps(themes, ensure_ascii=False)}
- 地点: {json.dumps([l['name'] for l in locations], ensure_ascii=False)}
- 阵营: {json.dumps([f['name'] for f in factions], ensure_ascii=False)}

生成节点 (nodes):
- Player: 1个玩家节点
- Location: 所有地点节点
- Faction: 所有阵营节点
- NPC: 3-5个核心NPC

生成关系 (edges):
- LOCATED_AT: 玩家/NPC -> 地点
- CONNECTED_TO: 地点 -> 地点（形成连通图）
- BELONGS_TO: NPC -> 阵营
- HOSTILE_TO: 阵营 -> 阵营

输出格式: {{"nodes": [...], "edges": [...]}}"""

        try:
            contents = [{"role": "user", "parts": [{"text": system_prompt}]}]
            content = self._call_api(self.world_gen_model, contents)
            world_json = self._safe_parse_json(content)

            for node in world_json.get('nodes', []):
                if 'detail_level' not in node:
                    node['detail_level'] = 0

            logger.info(f"世界骨架生成成功: {len(world_json.get('nodes', []))} 节点")
            return world_json
        except Exception as e:
            logger.error(f"世界骨架生成失败: {e}")
            return self._fallback_world_template()

    def _fallback_world_template(self) -> Dict[str, Any]:
        """备用世界模板"""
        return {
            "nodes": [
                {"id": "player1", "label": "Player", "name": "冒险者", "hp": 100},
                {"id": "start_room", "label": "Location", "name": "起始房间", "description": "一个简单的房间"},
                {"id": "enemy1", "label": "NPC", "name": "守卫", "damage": 5}
            ],
            "edges": [
                {"source": "player1", "target": "start_room", "type": "LOCATED_AT"},
                {"source": "enemy1", "target": "start_room", "type": "LOCATED_AT"}
            ]
        }

    def expand_location_details(self, location_id: str, location_name: str,
                                seed: Dict[str, Any]) -> Dict[str, Any]:
        """Step 3a: 懒加载 - 扩展地点细节"""
        themes = seed.get('themes', [])
        system_prompt = f"""为地点生成详细内容。

地点: {location_name} (id: {location_id})
主题: {json.dumps(themes, ensure_ascii=False)}

生成：
1. 详细描述（2-3句话）
2. 物品 (Item): 2-3个
3. 额外 NPC: 1-2个
4. 氛围

输出 JSON: {{"description": "...", "items": [...], "npcs": [...], "atmosphere": "..."}}"""

        try:
            contents = [{"role": "user", "parts": [{"text": system_prompt}]}]
            content = self._call_api(self.world_gen_model, contents)
            return self._safe_parse_json(content)
        except Exception as e:
            logger.error(f"地点细节扩展失败: {e}")
            return {"description": f"一个普通的{location_name}", "items": [], "npcs": []}

    def expand_npc_details(self, npc_id: str, npc_name: str,
                           faction: str, seed: Dict[str, Any]) -> Dict[str, Any]:
        """Step 3b: 懒加载 - 扩展 NPC 细节"""
        themes = seed.get('themes', [])
        system_prompt = f"""为 NPC 生成完整人设。

NPC: {npc_name} (id: {npc_id})
阵营: {faction}
主题: {json.dumps(themes, ensure_ascii=False)}

生成：hp, damage, dialogue, disposition, backstory

输出 JSON: {{"hp": 50, "damage": 10, "dialogue": "...", "disposition": "neutral", "backstory": "..."}}"""

        try:
            contents = [{"role": "user", "parts": [{"text": system_prompt}]}]
            content = self._call_api(self.world_gen_model, contents)
            return self._safe_parse_json(content)
        except Exception as e:
            logger.error(f"NPC 细节扩展失败: {e}")
            return {"hp": 50, "damage": 10, "dialogue": "...", "disposition": "neutral"}

    # =========================================================================
    # Action Ontology 生成
    # =========================================================================

    def generate_action_ontology(self, seed: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成 Action 本体定义"""
        system_prompt = """生成 Action Ontology（可执行的游戏动作）。

每个 Action 包含：
- id: 唯一标识符
- name: 动作名称（中文）
- condition: Cypher 条件表达式
- effect: Cypher 效果语句
- narrative_template: 叙事模板

生成 5-8 个核心 Action：ATTACK, MOVE, TALK, INSPECT, USE, GIVE, STEAL, WAIT

输出格式（JSON 数组）：
[{"id": "...", "name": "...", "condition": "...", "effect": "...", "narrative_template": "..."}, ...]"""

        try:
            contents = [{"role": "user", "parts": [{"text": system_prompt}]}]
            content = self._call_api(self.action_model, contents)
            actions = self._safe_parse_json(content)
            if not isinstance(actions, list):
                actions = [actions]
            logger.info(f"Action Ontology 生成成功: {len(actions)} 个动作")
            return actions
        except Exception as e:
            logger.error(f"Action Ontology 生成失败: {e}")
            return self._fallback_actions()

    def _fallback_actions(self) -> List[Dict[str, Any]]:
        """备用 Action 定义"""
        return [
            {
                "id": "ATTACK",
                "name": "攻击",
                "condition": "source.hp > 0 AND target.hp > 0",
                "effect": "SET target.hp = target.hp - source.damage",
                "narrative_template": "{source} 攻击了 {target}"
            },
            {
                "id": "MOVE",
                "name": "移动",
                "condition": "true",
                "effect": "",
                "narrative_template": "{source} 移动到了 {target}"
            },
            {
                "id": "WAIT",
                "name": "等待",
                "condition": "true",
                "effect": "",
                "narrative_template": "{source} 静观其变"
            }
        ]

    # =========================================================================
    # 意图解析
    # =========================================================================

    def interpret_action(self, player_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """将玩家自然语言输入解析为结构化意图"""
        player_faction = context.get("player_faction")
        simple_status = {
            "location": context.get("location", {}).get("name"),
            "exits": [e.get("name") for e in context.get("exits", [])],
            "entities": [e.get("name") for e in context.get("entities", [])],
            "player_faction": player_faction.get("name") if player_faction else None
        }

        available_actions = context.get("available_actions", ["MOVE", "ATTACK", "TALK", "INSPECT", "WAIT"])

        system_prompt = f"""你是意图解析器。

当前状态：
{json.dumps(simple_status, ensure_ascii=False, indent=2)}

可用动作：{json.dumps(available_actions, ensure_ascii=False)}

玩家输入："{player_input}"

解析为 JSON：{{"intent": "...", "target": "...", "narrative": "..."}}

Intent 类型: MOVE, TALK, INSPECT, ATTACK, WAIT, UNKNOWN"""

        try:
            contents = [{"role": "user", "parts": [{"text": system_prompt}]}]
            content = self._call_api(self.intent_model, contents)
            action = self._safe_parse_json(content)

            if "intent" not in action:
                action["intent"] = "UNKNOWN"
            if "target" not in action:
                action["target"] = ""
            if "narrative" not in action:
                action["narrative"] = player_input

            if action["intent"] not in available_actions and action["intent"] != "UNKNOWN":
                action["intent"] = "UNKNOWN"

            logger.info(f"意图解析: {player_input} -> {action['intent']}")
            return action
        except Exception as e:
            logger.error(f"意图解析失败: {e}")
            return {"intent": "UNKNOWN", "target": "", "narrative": f"你不确定如何执行这个动作：{player_input}"}

    # =========================================================================
    # NPC 对话生成
    # =========================================================================

    def generate_npc_response(self, player_input: str, npc_data: Dict,
                              player_data: Dict, memory_context: str = "") -> str:
        """生成式对话"""
        memory_section = ""
        if memory_context and memory_context != "暂无相关记忆":
            memory_section = f"""
相关记忆：
{memory_context}

记住这些互动，自然引用但不要生硬背诵。"""

        system_prompt = f"""你是 NPC {npc_data.get('name', '未知')}。

人设：
- 名字: {npc_data.get('name', '未知')}
- 阵营: {npc_data.get('faction', '无阵营')}
- 性格: {npc_data.get('disposition', 'neutral')}
- 台词风格: {npc_data.get('dialogue', '...')}

玩家：
- 名字: {player_data.get('name', '无名氏')}
- 阵营: {player_data.get('faction', '无阵营')}

{memory_section}

规则：
1. 保持角色扮演
2. aggressive=粗鲁好战, friendly=热情友好, neutral=冷淡
3. 回答简短（30-50字）
4. 可以反问玩家

玩家对你说: "{player_input}"""

        try:
            contents = [{"role": "user", "parts": [{"text": system_prompt}]}]
            response = self._call_api(self.intent_model, contents)
            reply = response.strip().strip('"').strip("'")
            logger.info(f"生成式对话: {npc_data.get('name')} -> {reply[:30]}...")
            return reply
        except Exception as e:
            logger.error(f"生成式对话失败: {e}")
            return npc_data.get('dialogue', '...')

    def generate_narrative(self, event_type: str, details: Dict[str, Any]) -> str:
        """生成事件叙事"""
        try:
            prompt = f"描述 RPG 事件：{event_type} 详情：{json.dumps(details, ensure_ascii=False)}"
            contents = [{"role": "user", "parts": [{"text": prompt}]}]
            return self._call_api(self.intent_model, contents)[:100]
        except Exception:
            return f"[{event_type}]"

    # =========================================================================
    # 兼容 v0.2 的接口
    # =========================================================================

    def generate_world_schema(self, user_prompt: str) -> Dict[str, Any]:
        """兼容 v0.2 的接口：一次性生成完整世界"""
        logger.info("使用 v0.3 分形生成策略生成世界...")

        seed = self.generate_world_seed(user_prompt)
        world_json = self.generate_world_skeleton(seed)

        # 立即填充所有细节（兼容模式）
        expanded_nodes = []

        for node in world_json.get('nodes', []):
            if node.get('label') == 'Location' and node.get('detail_level', 0) < 2:
                details = self.expand_location_details(node['id'], node.get('name', '未知'), seed)
                node['description'] = details.get('description', node.get('description', ''))
                node['detail_level'] = 2

                for item in details.get('items', []):
                    item['label'] = 'Item'
                    expanded_nodes.append(item)
                    world_json['edges'].append({
                        "source": node['id'],
                        "target": item['id'],
                        "type": "CONTAINS"
                    })

                for npc in details.get('npcs', []):
                    npc['label'] = 'NPC'
                    expanded_nodes.append(npc)
                    world_json['edges'].append({
                        "source": npc['id'],
                        "target": node['id'],
                        "type": "LOCATED_AT"
                    })

            elif node.get('label') == 'NPC' and node.get('detail_level', 0) < 2:
                faction = "未知"
                for edge in world_json.get('edges', []):
                    if edge.get('source') == node.get('id') and edge.get('type') == 'BELONGS_TO':
                        faction = edge.get('target', '未知')
                        break

                details = self.expand_npc_details(node['id'], node.get('name', '未知'), faction, seed)
                node.update(details)
                node['detail_level'] = 2

        world_json['nodes'].extend(expanded_nodes)

        logger.info(f"世界生成完成: {len(world_json['nodes'])} 节点, {len(world_json['edges'])} 关系")
        return world_json
