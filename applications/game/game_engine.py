"""
Game Engine - 游戏核心引擎

职责：
- 协调所有 Kernel 组件 (ObjectManager, ActionDriver, Synapser)
- 管理游戏状态和世界数据
- 处理游戏主循环逻辑
- 提供高阶游戏 API
"""

import logging
from typing import Dict, Any, Optional, List

from genesis.kernel.object_manager import ObjectManager
from genesis.kernel.rule_engine import RuleEngine
from genesis.kernel.action_driver import ActionDriver
from genesis.kernel.synapser import Synapser
from genesis.kernel.connectors.neo4j_connector import Neo4jConnector
from genesis.kernel.connectors.postgres_connector import PostgresConnector
from genesis.ontology.loader import OntologyLoader

logger = logging.getLogger(__name__)


class GameEngine:
    """游戏核心引擎 - 协调所有组件"""

    def __init__(self, neo4j_conn: Neo4jConnector, postgres_conn: PostgresConnector,
                 ontology_dir: str = "ontology", use_xml: bool = True):
        """
        初始化游戏引擎

        Args:
            neo4j_conn: Neo4j 连接器
            postgres_conn: PostgreSQL 连接器
            ontology_dir: Ontology 文件目录
            use_xml: 是否使用 XML 格式加载本体数据 (默认: True)
        """
        self.neo4j = neo4j_conn
        self.postgres = postgres_conn
        self.use_xml = use_xml

        # 加载 Ontology (支持 XML 和 JSON 双模式)
        self.ontology = OntologyLoader(ontology_dir)
        load_results = self.ontology.load_all(use_xml=use_xml)

        if not all(load_results.values()):
            failed = [k for k, v in load_results.items() if not v]
            raise RuntimeError(f"Failed to load ontology files: {failed}")

        # 初始化 Kernel 组件
        self.obj_mgr = ObjectManager(
            {
                'object_types': self.ontology.get_object_types(),
                'link_types': self.ontology.get_link_types()
            },
            neo4j_conn
        )

        self.rule_engine = RuleEngine(neo4j_conn, postgres_conn)

        self.action_driver = ActionDriver(
            neo4j_conn, self.rule_engine, self.obj_mgr
        )

        # 加载 Action Ontology
        actions_list = [
            {"id": k, **v}
            for k, v in self.ontology.get_action_types().items()
        ]
        self.action_driver.load_actions(actions_list)

        # 初始化 Synapser，传入同义词库
        synonyms = self.ontology.get_synonyms()
        self.synapser = Synapser(synonyms=synonyms)
        self.synapser.load_synapser_patterns(self.ontology.get_synapser_patterns())

        self.player_id = "player_001"
        self.game_running = False

        mode = "XML" if use_xml else "JSON"
        logger.info(f"[GameEngine] Initialized successfully with {mode} ontology")

    def initialize_world(self) -> bool:
        """
        初始化游戏世界 (加载种子数据)

        Returns:
            是否初始化成功
        """
        try:
            seed_data = self.ontology.get_seed_data()

            # 创建节点
            for node in seed_data.get('seed_nodes', []):
                node_type = node.get('type')
                properties = node.get('properties', {})
                properties['id'] = node.get('id')

                # Reason: 如果对象已存在，跳过创建
                existing = self.obj_mgr.get_object(node_type, node.get('id'))
                if existing:
                    logger.debug(f"[GameEngine] Node {node.get('id')} already exists")
                    continue

                self.obj_mgr.create_object(node_type, properties)

            # 创建关系
            for link in seed_data.get('seed_links', []):
                try:
                    self.obj_mgr.create_link(
                        link['type'],
                        link['source'],
                        link['target']
                    )
                except Exception as e:
                    logger.warning(f"[GameEngine] Failed to create link {link}: {e}")

            logger.info(f"[GameEngine] World initialized with {len(seed_data.get('seed_nodes', []))} nodes")
            return True

        except Exception as e:
            logger.error(f"[GameEngine] World initialization failed: {e}")
            return False

    def get_player_status(self) -> Optional[Dict[str, Any]]:
        """
        获取玩家状态及周围环境

        Returns:
            包含 player, location, exits, entities, faction 的字典
        """
        try:
            # 获取玩家信息
            player = self.obj_mgr.get_object("Player", self.player_id)
            if not player:
                logger.error(f"[GameEngine] Player {self.player_id} not found")
                return None

            # 获取当前位置
            locations = self.obj_mgr.get_related_objects("Player", self.player_id, "LOCATED_AT")
            if not locations:
                logger.error(f"[GameEngine] Player {self.player_id} has no location")
                return None

            location = locations[0]

            # 获取出口 (CONNECTED_TO 关系)
            location_id = location.get('id') if location else None
            if not location_id:
                logger.error("[GameEngine] Location has no id")
                return None

            exits = self.obj_mgr.get_related_objects(
                "Location", location_id, "CONNECTED_TO"
            )

            # 获取同地点的其他实体
            all_entities = self.obj_mgr.get_related_objects(
                "Location", location_id, "LOCATED_AT"
            )
            # Reason: 过滤掉玩家自己
            entities = [e for e in all_entities if e.get('id') != self.player_id]

            # 获取玩家阵营
            factions = self.obj_mgr.get_related_objects("Player", self.player_id, "BELONGS_TO")
            player_faction = factions[0] if factions else None

            return {
                "player": player,
                "location": location,
                "exits": exits,
                "entities": entities,
                "player_faction": player_faction
            }

        except Exception as e:
            logger.error(f"[GameEngine] Get player status failed: {e}")
            return None

    def process_input(self, user_input: str) -> Dict[str, Any]:
        """
        处理玩家输入

        Args:
            user_input: 玩家输入的自然语言

        Returns:
            处理结果字典
        """
        # 获取当前状态
        status = self.get_player_status()
        if not status:
            return {"success": False, "message": "无法获取游戏状态"}

        # 解析意图
        context = {
            "location": status.get("location"),
            "exits": status.get("exits", []),
            "entities": status.get("entities", []),
            "player_faction": status.get("player_faction"),
            "available_actions": list(self.ontology.get_action_types().keys())
        }

        intent = self.synapser.parse_intent(user_input, context)

        # 执行动作
        action_id = intent.get("action_id", "UNKNOWN")
        if action_id == "UNKNOWN":
            return {
                "success": False,
                "message": intent.get("narrative", "无法理解该指令"),
                "narrative": intent.get("narrative", "")
            }

        # 准备参数
        params = intent.get("params", {})
        params["source_id"] = self.player_id
        params["source_name"] = status.get("player", {}).get("name", "玩家")

        # 执行动作
        result = self.action_driver.execute(action_id, params)

        return {
            "success": result.get("success"),
            "message": result.get("message"),
            "narrative": intent.get("narrative", ""),
            "action_id": action_id,
            "intent": intent,
            "action_result": result
        }

    def run_simulation_tick(self) -> List[Dict[str, Any]]:
        """
        运行一次世界推演 (NPC 行动等)

        Returns:
            推演事件列表
        """
        events = []
        status = self.get_player_status()

        if not status:
            return events

        entities = status.get("entities", [])
        player = status.get("player", {})

        for entity in entities:
            # 检查是否是敌对的
            disposition = entity.get("disposition", 'neutral')
            damage = entity.get("damage", 0)

            if disposition == 'aggressive' and damage > 0:
                # 攻击玩家
                try:
                    # 更新玩家 HP
                    current_hp = player.get('hp', 0)
                    new_hp = max(0, current_hp - damage)

                    self.obj_mgr.update_object(
                        "Player",
                        self.player_id,
                        {"hp": new_hp}
                    )

                    events.append({
                        "type": "attack",
                        "source": entity.get("name", "未知"),
                        "target": player.get("name", "玩家"),
                        "damage": damage,
                        "message": f"{entity.get('name')} 攻击了你！造成 {damage} 点伤害！"
                    })

                except Exception as e:
                    logger.error(f"[GameEngine] NPC attack failed: {e}")

        return events

    def check_game_over(self) -> Optional[str]:
        """
        检查游戏是否结束

        Returns:
            结束原因，如果未结束则返回 None
        """
        status = self.get_player_status()
        if not status:
            return "无法获取游戏状态"

        player = status.get("player", {})
        hp = player.get("hp", 0)

        if hp <= 0:
            return "你倒下了...游戏结束。"

        return None

    def get_available_actions(self) -> List[str]:
        """
        获取可用动作列表

        Returns:
            动作 ID 列表
        """
        return list(self.ontology.get_action_types().keys())

    def get_help_text(self) -> str:
        """
        获取帮助文本

        Returns:
            帮助信息字符串
        """
        actions = self.ontology.get_action_types()
        action_descs = [
            f"- {action_id}: {action.get('display_name', action_id)}"
            for action_id, action in actions.items()
        ]

        return f"""可用指令类型：
{chr(10).join(action_descs)}

提示：
- 移动: "去藏书室", "前往厨房"
- 攻击: "攻击强盗", "打守卫"
- 对话: "和女仆说话", "询问守卫"
- 观察: "查看周围", "检查物品"
        - 等待: "等待", "休息"
"""
