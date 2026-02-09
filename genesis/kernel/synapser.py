"""
Synapser - 意图解析器

职责：
- 将自然语言映射到 Action
- 支持基于 Pattern 的匹配和 LLM 辅助理解
- 返回结构化意图 (action_id + params)

对比当前项目：
- 旧：LLMEngine.interpret_action() - 单一 LLM 解析
- 新：Synapser + Pattern 匹配 + Entity Linking + LLM 回退
"""

import json
import os
from typing import Dict, Any, Optional, List
import logging
from genesis.kernel.entity_linker import EntityLinker

logger = logging.getLogger(__name__)


class Synapser:
    """意图解析器 - 自然语言 → Action"""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, synonyms: Optional[Dict[str, List[str]]] = None):
        """
        初始化意图解析器

        Args:
            api_key: LLM API 密钥
            base_url: LLM API 基础 URL
            synonyms: 同义词库字典 {主词: [同义词列表]}
        """
        self.api_key = api_key or os.getenv("LLM_API_KEY") or "kimyitao"
        self.base_url = base_url or os.getenv(
            "LLM_BASE_URL",
            "http://43.153.96.90:7860/v1beta"
        )

        self.intent_model = os.getenv(
            "INTENT_MODEL",
            "models/gemini-2.5-flash-lite"
        )

        # 意图模式映射 (从 Synapser Patterns 加载)
        self.patterns = {}
        self._load_patterns()

        # 初始化实体链接器，传入同义词库
        self.entity_linker = EntityLinker(synonyms=synonyms or {})

    def _load_patterns(self) -> None:
        """加载意图模式映射 (简化版，未来从 JSON 加载)"""
        # Reason: 基础模式映射，用于快速匹配常见意图
        self.patterns = {
            "ACT_MOVE": {
                "keywords": ["去", "走", "移动", "前往", "到", "去往", "进入"],
                "requires_target": True,
                "target_type": "location"
            },
            "ACT_ATTACK": {
                "keywords": ["攻击", "打", "杀", "战斗", "袭击", "击打"],
                "requires_target": True,
                "target_type": "entity"
            },
            "ACT_TALK": {
                "keywords": ["说话", "问", "询问", "打听", "聊", "对话"],
                "requires_target": True,
                "target_type": "npc"
            },
            "ACT_INSPECT": {
                "keywords": ["看", "查看", "观察", "检查", "环顾", "描述", "环顾四周"],
                "requires_target": False,
                "target_type": "any"
            },
            "ACT_WAIT": {
                "keywords": ["等待", "休息", "静观", "跳过"],
                "requires_target": False,
                "target_type": None
            }
        }
        logger.info(f"[Synapser] Loaded {len(self.patterns)} intent patterns")

    def parse_intent(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        将自然语言解析为结构化意图

        Args:
            user_input: 用户输入 (如 "攻击那个僵尸")
            context: 当前游戏状态
                - location: 当前位置信息
                - exits: 可通行出口列表
                - entities: 可见实体列表
                - available_actions: 可用动作 ID 列表

        Returns:
            {
                "action_id": str,      # 动作 ID (如 "ACT_ATTACK")
                "params": dict,        # 动作参数
                "narrative": str,     # 中文描述
                "confidence": float    # 置信度
            }
        """
        # 步骤 1: 尝试模式匹配 (快速路径)
        pattern_result = self._match_pattern(user_input, context)
        if pattern_result:
            logger.info(f"[Synapser] Pattern matched: {pattern_result['action_id']}")
            return pattern_result

        # 步骤 2: 回退到 LLM 解析
        logger.info(f"[Synapser] Pattern not matched, using LLM")
        try:
            llm_result = self._parse_with_llm(user_input, context)
            return llm_result
        except Exception as e:
            logger.error(f"[Synapser] LLM parsing failed: {e}")
            # 步骤 3: 最终回退
            return self._fallback_result(user_input)

    def _match_pattern(self, user_input: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        基于关键词的模式匹配

        Args:
            user_input: 用户输入
            context: 游戏上下文

        Returns:
            匹配结果，如果不匹配则返回 None
        """
        user_input_lower = user_input.lower().strip()
        
        # 调试信息
        logger.debug(f"[Synapser] Parsing input: '{user_input}' -> lower: '{user_input_lower}'")
        logger.debug(f"[Synapser] Available patterns: {list(self.patterns.keys())}")

        # 遍历所有意图模式
        for action_id, pattern in self.patterns.items():
            keywords = pattern.get("keywords", [])
            # 调试：打印关键词（安全编码）
            try:
                keywords_str = ', '.join(keywords)
                logger.debug(f"[Synapser] Checking pattern {action_id}: keywords={keywords_str}")
            except:
                logger.debug(f"[Synapser] Checking pattern {action_id}: {len(keywords)} keywords")
            
            # 检查是否有关键词匹配
            for keyword in keywords:
                try:
                    if keyword in user_input_lower:
                        logger.info(f"[Synapser] Pattern match found: '{keyword}' in '{user_input_lower}' -> {action_id}")
                        result = {
                            "action_id": action_id,
                            "params": {},
                            "narrative": f"你{user_input}",
                            "confidence": 0.7
                        }

                        # 提取目标
                        if pattern.get("requires_target", False):
                            target = self._extract_target(
                                user_input, user_input_lower, keyword, pattern.get("target_type", "any"), context
                            )
                            if target:
                                result["params"]["target"] = target["id"]
                                result["params"]["target_name"] = target["name"]
                                result["narrative"] = f"你{keyword}{target['name']}"
                                logger.info(f"[Synapser] Target extracted: {target['name']} -> {target['id']}")
                            else:
                                # Reason: 目标未找到，返回失败
                                logger.info(f"[Synapser] Target not found for {action_id}, mention: '{user_input}' after keyword '{keyword}'")
                                continue  # 继续尝试其他模式

                        return result
                except Exception as e:
                    logger.debug(f"[Synapser] Error checking keyword '{keyword}': {e}")
                    continue
                    logger.debug(f"[Synapser] Pattern match: '{keyword}' in '{user_input_lower}' -> {action_id}")
                    result = {
                        "action_id": action_id,
                        "params": {},
                        "narrative": f"你{user_input}",
                        "confidence": 0.7
                    }

                    # 提取目标
                    if pattern["requires_target"]:
                        target = self._extract_target(
                            user_input, user_input_lower, keyword, pattern["target_type"], context
                        )
                        if target:
                            result["params"]["target"] = target["id"]
                            result["params"]["target_name"] = target["name"]
                            result["narrative"] = f"你{keyword}{target['name']}"
                        else:
                            # Reason: 目标未找到，返回失败
                            return None

                    return result

        return None

    def _extract_target(
        self, user_input: str, user_input_lower: str, keyword: str,
        target_type: str, context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        从用户输入中提取目标实体 (使用 EntityLinker)

        Args:
            user_input: 原始用户输入
            user_input_lower: 小写用户输入
            keyword: 匹配的关键词
            target_type: 目标类型 (location/entity/npc)
            context: 游戏上下文

        Returns:
            匹配的目标实体，包含 id 和 name
        """
        # Reason: 构建实体索引
        entity_index = self.entity_linker.build_entity_index(context)

        # Reason: 提取目标提及（关键词后的文本）
        mention = self.entity_linker.extract_target_from_pattern(
            user_input, f"{keyword}{{target}}", keyword
        )

        if not mention:
            # Reason: 尝试从整个输入中提取（去掉关键词）
            mention = user_input_lower.replace(keyword, "").strip()

        if not mention:
            return None

        # Reason: 获取候选列表
        candidates = entity_index.get(target_type, entity_index.get("any", []))

        # Reason: 使用 EntityLinker 进行匹配
        matched = self.entity_linker.link_entity(mention, candidates, target_type)

        return matched

    def _parse_with_llm(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用 LLM 解析意图 (回退路径)

        Args:
            user_input: 用户输入
            context: 游戏上下文

        Returns:
            解析结果
        """
        available_actions = context.get("available_actions", list(self.patterns.keys()))

        system_prompt = f"""你是意图解析器。将玩家输入映射为结构化意图。

当前状态：
{json.dumps({
    "location": context.get("location", {}).get("name"),
    "exits": [e.get('name', e) if isinstance(e, dict) else e for e in context.get("exits", [])],
    "entities": [e.get('name', e) if isinstance(e, dict) else e for e in context.get("entities", [])]
}, ensure_ascii=False, indent=2)}

可用动作：{json.dumps(available_actions, ensure_ascii=False)}

玩家输入："{user_input}"

解析规则（必须严格遵守）：
1. intent 必须是可用动作之一
2. target 如果有，必须在 exits 或 entities 列表中
3. narrative 必须是简短的中文动作描述，不要复读用户原话

输出格式（严格 JSON，不要任何其他文字）：
{{
    "action_id": "动作ID",
    "target": "目标名称或空字符串",
    "narrative": "描述玩家动作的中文短句"
}}"""

        try:
            content = self._call_api(self.intent_model, system_prompt)
            action = self._extract_json(content)

            # Reason: 防御性检查：确保 action 是字典
            if not isinstance(action, dict):
                logger.warning(f"[Synapser] LLM returned non-dict: {type(action)}")
                return self._fallback_result(user_input)

            # 验证 action_id
            action_id = action.get("action_id", "UNKNOWN")
            if action_id not in available_actions:
                logger.warning(f"[Synapser] Unknown action_id: {action_id}")
                return self._fallback_result(user_input)

            result = {
                "action_id": action_id,
                "params": {},
                "narrative": action.get("narrative", user_input),
                "confidence": 0.9  # LLM 解析置信度较高
            }

            # 提取目标参数
            target = action.get("target", "")
            if target:
                result["params"]["target"] = target
                result["params"]["target_name"] = target

            logger.info(f"[Synapser] LLM parsed: {action_id} -> {target}")
            return result

        except Exception as e:
            logger.error(f"[Synapser] LLM parsing failed: {e}")
            return self._fallback_result(user_input)

    def _call_api(self, model: str, prompt: str) -> str:
        """
        调用 LLM API

        Args:
            model: 模型名称
            prompt: 提示词

        Returns:
            API 返回的文本内容
        """
        import requests

        url = f"{self.base_url}/{model}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}]
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()

            result = response.json()
            # Reason: Gemini API 返回格式: candidates[0].content.parts[0].text
            content = result.get("candidates", [{}])[0].get(
                "content", {}
            ).get("parts", [{}])[0].get("text", "")

            return content

        except Exception as e:
            logger.error(f"[Synapser] API call failed: {e}")
            raise

    def _extract_json(self, content: str) -> Any:
        """
        从文本中提取 JSON

        Args:
            content: API 返回的文本

        Returns:
            解析后的 JSON 对象
        """
        try:
            # Reason: 尝试直接解析
            return json.loads(content)
        except json.JSONDecodeError:
            # Reason: 尝试提取 JSON 代码块
            import re
            match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
            if match:
                return json.loads(match.group(1))

            # Reason: 尝试提取花括号内容
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                return json.loads(match.group(0))

            raise ValueError("无法提取 JSON")

    def _fallback_result(self, user_input: str) -> Dict[str, Any]:
        """
        返回回退结果

        Args:
            user_input: 用户输入

        Returns:
            默认的 UNKNOWN 结果
        """
        return {
            "action_id": "UNKNOWN",
            "params": {},
            "narrative": f"不理解：{user_input}",
            "confidence": 0.0
        }

    def load_synapser_patterns(self, patterns: Dict[str, Any]) -> None:
        """
        加载 Synapser Patterns (从 JSON 文件加载)

        Args:
            patterns: 模式映射字典
        """
        # 合并模式，而不是覆盖
        for action_id, pattern in patterns.items():
            if action_id in self.patterns:
                # 合并关键词
                existing_keywords = self.patterns[action_id].get("keywords", [])
                new_keywords = pattern.get("keywords", [])
                merged_keywords = list(set(existing_keywords + new_keywords))
                self.patterns[action_id]["keywords"] = merged_keywords
                
                # 更新其他字段
                for key in ["requires_target", "target_type"]:
                    if key in pattern:
                        self.patterns[action_id][key] = pattern[key]
            else:
                # 添加新动作模式
                self.patterns[action_id] = pattern
        
        logger.info(f"[Synapser] Merged {len(patterns)} custom patterns, total: {len(self.patterns)}")
