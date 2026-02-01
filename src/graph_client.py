from neo4j import GraphDatabase
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class GraphClient:
    """Neo4j 图数据库客户端
    
    负责所有与 Neo4j 的交互，包括节点创建、关系建立、查询执行等。
    所有 Cypher 查询必须通过此类执行，确保数据一致性。
    """
    
    def __init__(self, uri: str, user: str, password: str):
        """初始化 Neo4j 连接
        
        Args:
            uri: Neo4j 连接 URI (如 bolt://localhost:7687)
            user: 用户名
            password: 密码
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        logger.info("Neo4j 连接已建立")
    
    def close(self) -> None:
        """关闭数据库连接"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j 连接已关闭")
    
    def clear_world(self) -> None:
        """清空整个世界：删除所有节点和关系
        
        警告：此操作不可逆，会删除图数据库中的所有数据！
        """
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("世界已清空")
    
    def create_world(self, world_json: Dict[str, List[Dict]]) -> None:
        """根据 JSON 数据批量创建世界
        
        创建所有节点和关系。节点必须先于关系创建。
        
        Args:
            world_json: 包含 nodes 和 edges 的字典
                - nodes: 节点列表，每个节点有 id, label, properties
                - edges: 边列表，每个边有 source, target, type, properties
        
        Raises:
            ValueError: 当 world_json 格式无效时
        """
        if not isinstance(world_json, dict):
            raise ValueError("world_json 必须是字典")
        
        nodes = world_json.get("nodes", [])
        edges = world_json.get("edges", [])
        
        with self.driver.session() as session:
            # Step 1: 创建所有节点
            for node in nodes:
                self._create_node(session, node)
            
            # Step 2: 创建所有关系
            for edge in edges:
                self._create_edge(session, edge)
            
            logger.info(f"世界创建完成：{len(nodes)} 个节点，{len(edges)} 条关系")
    
    def _create_node(self, session, node: Dict[str, Any]) -> None:
        """创建单个节点（内部方法）
        
        Args:
            session: Neo4j 会话
            node: 节点数据，包含 id, label, 和其他属性
        """
        node_id = node.get("id")
        label = node.get("label", "Entity")
        
        if not node_id:
            raise ValueError("节点必须包含 id 字段")
        
        # 兼容两种格式：
        # 1. 标准格式: {id, label, properties: {...}}
        # 2. LLM格式: {id, label, name, hp, ...} (属性直接平铺)
        if "properties" in node:
            properties = node["properties"]
        else:
            # 从节点中提取除 id 和 label 外的所有属性
            properties = {k: v for k, v in node.items() if k not in ["id", "label"]}
        
        # 设置默认值
        if label == "Player" and "hp" not in properties:
            properties["hp"] = 100
        if label == "NPC" and "damage" not in properties:
            properties["damage"] = 5
        
        # 合并 id 到 properties
        all_props = {"id": node_id}
        all_props.update(properties)
        
        # 使用参数化查询一次性创建带所有属性的节点
        query = f"CREATE (n:{label} $props)"
        session.run(query, props=all_props)
    
    def _create_edge(self, session, edge: Dict[str, Any]) -> None:
        """创建单个关系（内部方法）
        
        Args:
            session: Neo4j 会话
            edge: 边数据，包含 source, target, type/label
        """
        source_id = edge.get("source")
        target_id = edge.get("target")
        # 兼容 type 和 label 两种字段名
        rel_type = edge.get("type") or edge.get("label", "RELATED_TO")
        
        if not source_id or not target_id:
            raise ValueError("关系必须包含 source 和 target 字段")
        
        # 兼容两种属性格式
        if "properties" in edge:
            properties = edge["properties"]
        else:
            properties = {k: v for k, v in edge.items() 
                         if k not in ["source", "target", "type", "label"]}
        
        # 构建 Cypher 查询 - 使用 ON CREATE SET 确保属性被设置
        if properties:
            query = f"""
            MATCH (a {{id: $source_id}}), (b {{id: $target_id}})
            CREATE (a)-[r:{rel_type}]->(b)
            SET r = $props
            """
            session.run(query, source_id=source_id, target_id=target_id, props=properties)
        else:
            query = f"""
            MATCH (a {{id: $source_id}}), (b {{id: $target_id}})
            CREATE (a)-[r:{rel_type}]->(b)
            """
            session.run(query, source_id=source_id, target_id=target_id)

    def get_player_status(self) -> Optional[Dict[str, Any]]:
        """获取玩家当前状态及周围环境 (v0.2 包含 Faction)
        
        查询玩家位置、当前地点描述、可通行出口、同区域实体等。
        这是游戏主循环的核心查询，为 LLM 意图解析提供上下文。
        
        Returns:
            包含以下字段的字典：
            - player: 玩家属性字典
            - location: 当前位置属性字典
            - player_faction: 玩家阵营
            - exits: 可通行出口列表
            - entities: 同区域实体列表（NPC、物品等）
            None: 如果找不到玩家实体
        """
        query = """
        MATCH (p:Player)-[:LOCATED_AT]->(loc:Location)
        WITH p, loc
        LIMIT 1
        OPTIONAL MATCH (p)-[:BELONGS_TO]->(pf:Faction)
        OPTIONAL MATCH (loc)-[:CONNECTED_TO]-(exits:Location)
        OPTIONAL MATCH (entity)-[:LOCATED_AT]->(loc)
        WHERE entity.id <> p.id AND (entity:NPC OR entity:Item)
        RETURN 
            p AS player,
            loc AS location,
            pf AS player_faction,
            collect(DISTINCT exits) AS exits,
            collect(DISTINCT entity) AS entities
        """
        
        with self.driver.session() as session:
            result = session.run(query).single()
            if not result:
                logger.warning("未找到玩家实体")
                return None
            
            return {
                "player": dict(result["player"]),
                "location": dict(result["location"]),
                "player_faction": dict(result["player_faction"]) if result["player_faction"] else None,
                "exits": [dict(n) for n in result["exits"] if n],
                "entities": [dict(n) for n in result["entities"] if n]
            }
    
    def execute_move(self, target_name: str) -> tuple[bool, str]:
        """执行移动动作
        
        先验证目标地点是否与当前位置连通（通过 CONNECTED_TO 关系），
        只有在连通的情况下才更新玩家位置。
        
        Args:
            target_name: 目标地点的中文名称
        
        Returns:
            (success, message) 元组
            - success: 是否移动成功
            - message: 操作结果的中文描述
        """
        with self.driver.session() as session:
            # Step 1: 验证连通性（防止穿墙）
            check_query = """
            MATCH (p:Player)-[:LOCATED_AT]->(cur:Location)
            MATCH (cur)-[:CONNECTED_TO]-(tgt:Location {name: $target_name})
            RETURN tgt
            """
            check_result = session.run(check_query, target_name=target_name).single()
            
            if not check_result:
                # Reason: 必须通过图谱关系验证连通性，防止 LLM 幻觉导致穿墙
                return False, f"去不了那里，路不通。"
            
            # Step 2: 更新玩家位置
            move_query = """
            MATCH (p:Player)-[r:LOCATED_AT]->()
            MATCH (tgt:Location {name: $target_name})
            DELETE r
            CREATE (p)-[:LOCATED_AT]->(tgt)
            """
            session.run(move_query, target_name=target_name)
            
            logger.info(f"玩家移动到了 {target_name}")
            return True, f"移动到了 {target_name}"
    
    def update_player_hp(self, delta: int) -> None:
        """更新玩家血量
        
        Args:
            delta: 血量变化值（正数为治疗，负数为伤害）
        """
        with self.driver.session() as session:
            session.run(
                "MATCH (p:Player) SET p.hp = p.hp + $delta",
                delta=delta
            )
            action = "恢复" if delta > 0 else "失去"
            logger.info(f"玩家 {action} {abs(delta)} 点生命值")
    
    def get_npc_dialogue(self, npc_name: str) -> Optional[Dict]:
        """获取 NPC 的对话和性情
        
        Args:
            npc_name: NPC 的中文名称
        
        Returns:
            包含 dialogue 和 disposition 的字典，如果未找到返回 None
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n:NPC {name: $name})
                RETURN n.dialogue as dialogue, n.disposition as disposition
            """, name=npc_name).single()
            return dict(result) if result else None
    
    def run_smart_simulation(self, player_id: str) -> List[Dict]:
        """
        ★ v0.2 核心：基于图谱关系的智能推演
        
        规则：只有当 NPC 所属的阵营与玩家阵营存在 HOSTILE_TO 关系时，
        或者 NPC 的 disposition 为 aggressive 时，才发起攻击。
        
        Args:
            player_id: 玩家节点 ID
        
        Returns:
            攻击事件列表，每个事件包含 name, damage, disposition
        """
        with self.driver.session() as session:
            query = """
            // 1. 找到玩家和其阵营
            MATCH (p:Player {id: $pid})
            OPTIONAL MATCH (p)-[:BELONGS_TO]->(pf:Faction)
            
            // 2. 找到同房间的活着的 NPC
            WITH p, pf
            MATCH (p)-[:LOCATED_AT]->(loc)<-[:LOCATED_AT]-(n:NPC)
            WHERE n.hp > 0
            
            // 3. 查找 NPC 的阵营及其敌对关系
            OPTIONAL MATCH (n)-[:BELONGS_TO]->(nf:Faction)
            OPTIONAL MATCH (nf)-[hostile:HOSTILE_TO]->(pf)
            
            // 4. 判定攻击条件：有敌对关系 OR NPC个性就是好战
            WITH n, hostile
            WHERE hostile IS NOT NULL OR n.disposition = 'aggressive'
            
            RETURN n.name as name, n.damage as damage, n.disposition as disposition
            """
            
            results = session.run(query, pid=player_id)
            return [dict(record) for record in results]
    
    def run_global_tick(self) -> List[str]:
        """
        ★ v0.3 核心：全局图谱推演 - 让世界活起来
        
        在玩家每次行动后调用，让整个世界的 NPC 都行动一次。
        实现真正的自主推演式仿真，而非触发式。
        
        Returns:
            传闻事件列表，供消息系统显示
        """
        events = []
        
        with self.driver.session() as session:
            # -------------------------------------------------------
            # 1. NPC 移动推演 (让 NPC 在地图上游走)
            # -------------------------------------------------------
            # 逻辑：随机选取 30% 的 NPC，让他们移动到相邻的房间
            move_query = """
            MATCH (n:NPC)-[old:LOCATED_AT]->(curr:Location)
            MATCH (curr)-[:CONNECTED_TO]-(next:Location)
            WHERE n.hp > 0 AND rand() < 0.3  // 30% 概率移动
            
            // 随机选一个出口
            WITH n, old, curr, next, rand() as r
            ORDER BY r LIMIT 1
            
            // 更新位置
            DELETE old
            CREATE (n)-[:LOCATED_AT]->(next)
            
            RETURN n.name as npc, curr.name as from_loc, next.name as to_loc
            """
            
            result = session.run(move_query)
            for record in result:
                # 系统日志，玩家不一定能直接看到
                logger.info(f"[世界推演] {record['npc']} 从 {record['from_loc']} 移动到了 {record['to_loc']}")
            
            # -------------------------------------------------------
            # 2. 视野外战斗推演 (NPC vs NPC)
            # -------------------------------------------------------
            # 逻辑：如果有两个敌对阵营的 NPC 在同一个房间（且玩家不在场），他们会互殴
            battle_query = """
            MATCH (n1:NPC)-[:LOCATED_AT]->(loc:Location)<-[:LOCATED_AT]-(n2:NPC)
            WHERE n1.id < n2.id  // 避免重复计算
            AND n1.hp > 0 AND n2.hp > 0
            
            // 检查敌对关系
            MATCH (n1)-[:BELONGS_TO]->(f1:Faction)-[:HOSTILE_TO]-(f2:Faction)<-[:BELONGS_TO]-(n2)
            
            // 只有当玩家不在这个房间时 (玩家在场走另一套逻辑)
            WHERE NOT EXISTS {
                MATCH (:Player)-[:LOCATED_AT]->(loc)
            }
            
            // 简单的互相伤害逻辑 (在图数据库内直接结算)
            SET n1.hp = n1.hp - n2.damage
            SET n2.hp = n2.hp - n1.damage
            
            RETURN n1.name as fighter1, n2.name as fighter2, loc.name as place,
                   n1.hp as hp1, n2.hp as hp2
            """
            
            result = session.run(battle_query)
            for record in result:
                fighter1, fighter2 = record['fighter1'], record['fighter2']
                place = record['place']
                hp1, hp2 = record['hp1'], record['hp2']
                
                # 判断胜负
                if hp1 <= 0 and hp2 <= 0:
                    outcome = f"听说在 {place}，{fighter1} 和 {fighter2} 同归于尽了！"
                elif hp1 <= 0:
                    outcome = f"听说在 {place}，{fighter2} 杀死了 {fighter1}！"
                elif hp2 <= 0:
                    outcome = f"听说在 {place}，{fighter1} 杀死了 {fighter2}！"
                else:
                    outcome = f"听说在 {place}，{fighter1} 和 {fighter2} 打得两败俱伤！"
                
                events.append(outcome)
                logger.info(f"[世界推演] 战斗: {fighter1} vs {fighter2} @ {place}")
            
            # -------------------------------------------------------
            # 3. 死亡清理 (可选)
            # -------------------------------------------------------
            # 清理 HP <= 0 的 NPC（或者保留尸体？）
            clean_query = """
            MATCH (n:NPC)
            WHERE n.hp <= 0
            SET n.name = n.name + '的尸体'
            REMOVE n:NPC
            SET n:Corpse
            RETURN n.name as name
            """
            
            result = session.run(clean_query)
            for record in result:
                logger.info(f"[世界推演] {record['name']} 被标记为尸体")
        
        return events