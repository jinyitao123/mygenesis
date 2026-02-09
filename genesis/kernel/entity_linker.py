"""
Entity Linker - 实体链接器

职责：
- 将自然语言中的实体提及映射到数据库中的实体ID
- 支持模糊匹配、同义词扩展、拼音匹配
- 处理指代消解（如"那个守卫"、"他"）
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)


class EntityLinker:
    """实体链接器 - 自然语言 → 实体ID"""

    def __init__(self, synonyms: Optional[Dict[str, List[str]]] = None):
        """初始化实体链接器
        
        Args:
            synonyms: 同义词映射字典，格式为 {主词: [别名1, 别名2, ...]}
                     如果为None，则使用空字典（由上层从ontology加载）
        """
        # 同义词库 - 从ontology层注入，保持核心层通用性
        self.synonyms = synonyms or {}

    def link_entity(
        self,
        mention: str,
        candidates: List[Dict[str, Any]],
        entity_type: str = "any"
    ) -> Optional[Dict[str, Any]]:
        """
        将提及链接到候选实体

        Args:
            mention: 用户输入中的实体提及（如"那个守卫"）
            candidates: 候选实体列表（来自当前场景）
            entity_type: 实体类型限制（location/npc/any）

        Returns:
            匹配到的实体，未匹配则返回 None
        """
        if not mention or not candidates:
            return None

        mention = mention.strip().lower()

        # 步骤 1: 去除指代词
        clean_mention = self._remove_pronouns(mention)
        logger.debug(f"[EntityLinker] Clean mention: '{mention}' -> '{clean_mention}'")

        # 步骤 2: 精确匹配
        for candidate in candidates:
            name = candidate.get('name', '').lower()
            logger.debug(f"[EntityLinker] Checking candidate: '{name}' vs '{clean_mention}'")
            if clean_mention == name:
                logger.info(f"[EntityLinker] Exact match: '{clean_mention}' -> '{candidate.get('name')}'")
                return candidate

        # 步骤 3: 包含匹配
        for candidate in candidates:
            name = candidate.get('name', '').lower()
            if clean_mention in name or name in clean_mention:
                return candidate

        # 步骤 4: 同义词匹配
        for candidate in candidates:
            name = candidate.get('name', '')
            synonyms = self.synonyms.get(name, [name])
            for syn in synonyms:
                if clean_mention in syn.lower() or syn.lower() in clean_mention:
                    return candidate

        # 步骤 5: 模糊匹配（相似度 > 0.6）
        best_match = None
        best_score = 0.0

        for candidate in candidates:
            name = candidate.get('name', '').lower()
            score = SequenceMatcher(None, clean_mention, name).ratio()
            if score > best_score and score > 0.6:
                best_score = score
                best_match = candidate

        if best_match:
            logger.info(f"[EntityLinker] Fuzzy match: '{mention}' -> '{best_match['name']}' (score={best_score:.2f})")
            return best_match

        return None

    def _remove_pronouns(self, text: str) -> str:
        """
        去除指代词和量词

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        # 去除常见指代词和量词
        pronouns = [
            "那个", "这个", "那个", "这些", "那些",
            "一个", "一位", "一名", "个", "位", "名",
            "的", "了", "在", "向", "往"
        ]

        result = text
        for pronoun in pronouns:
            result = result.replace(pronoun, "")

        return result.strip()

    def extract_target_from_pattern(
        self,
        user_input: str,
        pattern: str,
        keyword: str
    ) -> Optional[str]:
        """
        从模板中提取目标实体

        Args:
            user_input: 用户输入
            pattern: 匹配的模式模板（如"攻击{target}"）
            keyword: 匹配的关键词

        Returns:
            提取的目标名称
        """
        # 找到关键词位置
        keyword_pos = user_input.lower().find(keyword.lower())
        if keyword_pos == -1:
            return None

        # 提取关键词后的内容作为目标
        after_keyword = user_input[keyword_pos + len(keyword):].strip()

        # 去除常见后缀词
        suffixes = ["去", "到", "向", "在", "的", "了"]
        for suffix in suffixes:
            if after_keyword.endswith(suffix):
                after_keyword = after_keyword[:-1]

        return after_keyword.strip() if after_keyword else None

    def build_entity_index(self, status: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        从游戏状态构建实体索引

        Args:
            status: 游戏状态（包含 exits, entities 等）

        Returns:
            按类型分类的实体索引
        """
        index = {
            "location": [],
            "npc": [],
            "item": [],
            "any": []
        }

        # 添加出口（地点）
        for exit_loc in status.get("exits", []):
            if exit_loc:
                index["location"].append(exit_loc)
                index["any"].append(exit_loc)

        # 添加可见实体
        for entity in status.get("entities", []):
            if entity:
                # 根据类型分类
                entity_type = entity.get("type", "NPC")
                if entity_type in ["NPC"]:
                    index["npc"].append(entity)
                elif entity_type in ["Item"]:
                    index["item"].append(entity)

                index["any"].append(entity)

        return index
