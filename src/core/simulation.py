"""
Simulation Engine v0.3 - 全局推演模块

负责整个世界的时间推进和 NPC 自主行为。
实现真正的自主推演式仿真。

特性：
- 全局时钟系统
- NPC 自主移动和决策
- 视野外战斗
- 事件生成与传闻系统
- 与 ActionDriver 集成
"""

import random
from typing import Dict, List, Any, Optional, Tuple
import logging
from src.core.action_driver import ActionDriver
from src.core.graph_client import GraphClient

logger = logging.getLogger(__name__)


class SimulationEngine:
    """全局推演引擎
    
    管理整个世界的时间推进，让 NPC 自主行动，
    实现“世界在玩家视野外也持续演变”。
    
    四模块协同：
    1. GraphClient: 读取当前世界状态
    2. ActionDriver: 执行 Action 规则
    3. LLM: 生成叙事描述（可选）
    4. 本引擎: 决策和调度
    """
    
    def __init__(self, graph_client: GraphClient, action_driver: ActionDriver):
        """初始化推演引擎
        
        Args:
            graph_client: 图数据库客户端
            action_driver: 动力学引擎
        """
        self.graph = graph_client
        self.action_driver = action_driver
        self.tick_count = 0
        logger.info("推演引擎初始化完成")
    
    def run_tick(self, player_location_id: Optional[str] = None) -> List[str]:
        """执行一次全局时钟推演
        
        这是 v0.3 的核心方法，每次玩家行动后调用。
        让整个世界推进一个时间单位。
        
        Args:
            player_location_id: 玩家当前位置（用于判断视野）
            
        Returns:
            传闻事件列表（供消息系统显示）
        """
        self.tick_count += 1
        logger.info(f"===== 全局时钟 Tick {self.tick_count} =====")
        
        events = []
        
        # 1. NPC 移动推演
        move_events = self._simulate_npc_movement()
        events.extend(move_events)
        
        # 2. 视野外战斗推演
        if player_location_id:
            battle_events = self._simulate_offscreen_battles(player_location_id)
            events.extend(battle_events)
        
        # 3. NPC 自主行为（使用 ActionDriver）
        action_events = self._simulate_npc_actions(player_location_id)
        events.extend(action_events)
        
        # 4. 死亡清理
        self._cleanup_dead_entities()
        
        # 5. 生成传闻（过滤并格式化事件）
        rumors = self._generate_rumors(events)
        
        logger.info(f"Tick {self.tick_count} 完成，生成 {len(rumors)} 条传闻")
        return rumors
    
    def _simulate_npc_movement(self) -> List[Dict[str, Any]]:
        """模拟 NPC 移动
        
        随机选取一部分 NPC，让他们在地图上移动。
        某些 NPC（如守卫）坚守岗位不移动。
        
        Returns:
            移动事件列表
        """
        events = []
        
        with self.graph.driver.session() as session:
            # 查询所有活着的、可以移动的 NPC
            query = """
            MATCH (n:NPC)-[old:LOCATED_AT]->(curr:Location)
            MATCH (curr)-[:CONNECTED_TO]-(next:Location)
            WHERE n.hp > 0 
              AND rand() < 0.15  // 15% 概率移动
              AND NOT n.name CONTAINS '守卫'
              AND NOT n.name CONTAINS '门卫'
            WITH n, old, curr, next, rand() as r
            ORDER BY r LIMIT 1
            DELETE old
            CREATE (n)-[:LOCATED_AT]->(next)
            RETURN n.name as npc, curr.name as from_loc, next.name as to_loc, n.id as npc_id
            """
            
            results = session.run(query)
            for record in results:
                event = {
                    "type": "movement",
                    "npc": record["npc"],
                    "npc_id": record["npc_id"],
                    "from": record["from_loc"],
                    "to": record["to_loc"],
                    "description": f"{record['npc']} 从 {record['from_loc']} 移动到了 {record['to_loc']}"
                }
                events.append(event)
                logger.debug(f"[移动] {event['description']}")
        
        return events
    
    def _simulate_offscreen_battles(self, player_location_id: str) -> List[Dict[str, Any]]:
        """模拟视野外战斗
        
        敌对阵营的 NPC 在同一房间（且玩家不在场）会互相战斗。
        
        Args:
            player_location_id: 玩家位置（排除视野内）
            
        Returns:
            战斗事件列表
        """
        events = []
        
        with self.graph.driver.session() as session:
            # 查找视野外的敌对阵营 NPC
            query = """
            MATCH (n1:NPC)-[:LOCATED_AT]->(loc:Location)<-[:LOCATED_AT]-(n2:NPC)
            WHERE n1.id < n2.id  // 避免重复计算
              AND n1.hp > 0 AND n2.hp > 0
              AND loc.id <> $player_loc  // 玩家不在场
            
            // 检查敌对关系
            MATCH (n1)-[:BELONGS_TO]->(f1:Faction)-[:HOSTILE_TO]-(f2:Faction)<-[:BELONGS_TO]-(n2)
            
            // 战斗结算
            SET n1.hp = n1.hp - n2.damage
            SET n2.hp = n2.hp - n1.damage
            
            RETURN 
                n1.name as fighter1, n2.name as fighter2,
                n1.id as id1, n2.id as id2,
                loc.name as place,
                n1.hp as hp1, n2.hp as hp2
            """
            
            results = session.run(query, player_loc=player_location_id)
            
            for record in results:
                fighter1, fighter2 = record["fighter1"], record["fighter2"]
                hp1, hp2 = record["hp1"], record["hp2"]
                place = record["place"]
                
                # 判断战斗结果
                if hp1 <= 0 and hp2 <= 0:
                    outcome = f"听说在 {place}，{fighter1} 和 {fighter2} 同归于尽了！"
                    event_type = "mutual_death"
                elif hp1 <= 0:
                    outcome = f"听说在 {place}，{fighter2} 杀死了 {fighter1}！"
                    event_type = "death"
                elif hp2 <= 0:
                    outcome = f"听说在 {place}，{fighter1} 杀死了 {fighter2}！"
                    event_type = "death"
                else:
                    outcome = f"听说在 {place}，{fighter1} 和 {fighter2} 打得两败俱伤！"
                    event_type = "battle"
                
                event = {
                    "type": event_type,
                    "fighter1": fighter1,
                    "fighter2": fighter2,
                    "location": place,
                    "hp1": hp1,
                    "hp2": hp2,
                    "description": outcome,
                    "is_rumor": True  # 标记为可传播传闻
                }
                events.append(event)
                logger.info(f"[视野外战斗] {outcome}")
        
        return events
    
    def _simulate_npc_actions(self, player_location_id: Optional[str]) -> List[Dict[str, Any]]:
        """模拟 NPC 自主行为（使用 ActionDriver）
        
        NPC 根据当前状态自主决定行动，如治疗、警戒、搜索等。
        
        Args:
            player_location_id: 玩家位置
            
        Returns:
            行为事件列表
        """
        events = []
        
        # 获取所有活着的 NPC
        with self.graph.driver.session() as session:
            query = """
            MATCH (n:NPC)-[:LOCATED_AT]->(loc:Location)
            WHERE n.hp > 0
            RETURN n.id as id, n.name as name, n.hp as hp, n.damage as damage,
                   loc.id as loc_id, loc.name as loc_name
            """
            
            npcs = list(session.run(query))
        
        # 每个 NPC 根据状态决定行动
        for npc_record in npcs:
            npc_id = npc_record["id"]
            npc_name = npc_record["name"]
            hp = npc_record["hp"]
            loc_id = npc_record["loc_id"]
            
            # 简单的决策逻辑
            if hp < 30:
                # 低血量：尝试治疗自己（如果可能）
                # 这里可以扩展为使用 ActionDriver 执行 HEAL 动作
                logger.debug(f"[NPC决策] {npc_name} 血量低({hp})，考虑治疗")
            
            # 检查是否有玩家在场
            if loc_id == player_location_id:
                # 与玩家同区域：可能发起攻击或对话
                logger.debug(f"[NPC决策] {npc_name} 与玩家同区域")
        
        return events
    
    def _cleanup_dead_entities(self) -> None:
        """清理死亡实体
        
        将 HP <= 0 的 NPC 标记为尸体，
        并从游戏中移除（或转换为 Corpse 节点）。
        """
        with self.graph.driver.session() as session:
            query = """
            MATCH (n:NPC)
            WHERE n.hp <= 0
            SET n.name = n.name + '的尸体'
            REMOVE n:NPC
            SET n:Corpse
            RETURN n.name as name, n.id as id
            """
            
            results = session.run(query)
            for record in results:
                logger.info(f"[死亡清理] {record['name']} (id: {record['id']})")
    
    def _generate_rumors(self, events: List[Dict[str, Any]]) -> List[str]:
        """从事件生成传闻
        
        筛选重要事件，格式化为可显示的传闻文本。
        
        Args:
            events: 原始事件列表
            
        Returns:
            传闻文本列表
        """
        rumors = []
        
        for event in events:
            # 只选择标记为传闻的事件
            if event.get("is_rumor", False) or event.get("type") in ["death", "mutual_death", "battle"]:
                rumor = event.get("description", str(event))
                rumors.append(rumor)
            
            # 某些移动事件也可能成为传闻（如重要 NPC 移动）
            elif event.get("type") == "movement":
                # 可以根据 NPC 重要性决定是否传播
                pass
        
        # 限制传闻数量，避免刷屏
        if len(rumors) > 5:
            rumors = random.sample(rumors, 5)
        
        return rumors
    
    def get_world_summary(self) -> Dict[str, Any]:
        """获取世界状态摘要
        
        用于调试和日志记录。
        
        Returns:
            世界统计信息
        """
        with self.graph.driver.session() as session:
            # 统计各类节点
            stats_query = """
            MATCH (p:Player) RETURN count(p) as player_count
            """
            player_count = session.run(stats_query).single()["player_count"]
            
            stats_query = """
            MATCH (n:NPC) WHERE n.hp > 0 RETURN count(n) as npc_count
            """
            npc_count = session.run(stats_query).single()["npc_count"]
            
            stats_query = """
            MATCH (c:Corpse) RETURN count(c) as corpse_count
            """
            corpse_result = session.run(stats_query).single()
            corpse_count = corpse_result["corpse_count"] if corpse_result else 0
            
            stats_query = """
            MATCH (l:Location) RETURN count(l) as location_count
            """
            location_count = session.run(stats_query).single()["location_count"]
        
        return {
            "tick": self.tick_count,
            "players": player_count,
            "alive_npcs": npc_count,
            "corpses": corpse_count,
            "locations": location_count
        }
    
    def check_lazy_loading(self, location_id: str, seed: Dict[str, Any]) -> bool:
        """检查并触发懒加载
        
        如果地点需要扩展，调用 LLM 生成细节。
        
        Args:
            location_id: 地点 ID
            seed: 世界种子
            
        Returns:
            是否进行了扩展
        """
        from src.llm_engine import LLMEngine
        
        # 获取地点元数据
        meta = self.graph.get_location_meta(location_id)
        
        if meta.get("needs_expansion", False):
            logger.info(f"地点 {meta.get('name', location_id)} 需要扩展，触发懒加载...")
            
            # 调用 LLM 生成细节
            llm = LLMEngine()
            details = llm.expand_location_details(
                location_id,
                meta.get("name", "未知地点"),
                seed
            )
            
            # 更新地点描述
            self.graph.set_entity_property(
                location_id,
                "description",
                details.get("description", meta.get("description", ""))
            )
            self.graph.set_entity_property(location_id, "detail_level", 2)
            
            # 创建地点内的实体
            nodes_to_create = []
            edges_to_create = []
            
            import uuid
            
            for item in details.get("items", []):
                item["label"] = "Item"
                # Ensure item has an id
                if "id" not in item:
                    item["id"] = f"item_{uuid.uuid4().hex[:8]}"
                nodes_to_create.append(item)
                edges_to_create.append({
                    "source": location_id,
                    "target": item["id"],
                    "type": "CONTAINS"
                })
            
            for npc in details.get("npcs", []):
                npc["label"] = "NPC"
                npc["detail_level"] = 1
                # Ensure npc has an id
                if "id" not in npc:
                    npc["id"] = f"npc_{uuid.uuid4().hex[:8]}"
                nodes_to_create.append(npc)
                edges_to_create.append({
                    "source": npc["id"],
                    "target": location_id,
                    "type": "LOCATED_AT"
                })
            
            # 批量创建
            if nodes_to_create:
                self.graph.create_nodes_from_json(nodes_to_create)
            if edges_to_create:
                self.graph.create_relationships_from_json(edges_to_create)
            
            logger.info(f"懒加载完成：创建了 {len(nodes_to_create)} 个实体")
            return True
        
        return False
