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
            node: 节点数据，必须包含 id, label, properties
        """
        node_id = node.get("id")
        label = node.get("label", "Entity")
        properties = node.get("properties", {})
        
        if not node_id:
            raise ValueError("节点必须包含 id 字段")
        
        # 构建 Cypher 查询
        query = f"CREATE (n:{label} {{id: $id}}) SET n += $props"
        session.run(query, id=node_id, props=properties)
    
    def _create_edge(self, session, edge: Dict[str, Any]) -> None:
        """创建单个关系（内部方法）
        
        Args:
            session: Neo4j 会话
            edge: 边数据，必须包含 source, target, type
        """
        source_id = edge.get("source")
        target_id = edge.get("target")
        rel_type = edge.get("type", "RELATED_TO")
        properties = edge.get("properties", {})
        
        if not source_id or not target_id:
            raise ValueError("关系必须包含 source 和 target 字段")
        
        # 构建 Cypher 查询：匹配源节点和目标节点，然后创建关系
        query = f"""
        MATCH (a), (b)
        WHERE a.id = $source_id AND b.id = $target_id
        CREATE (a)-[r:{rel_type}]->(b)
        SET r += $props
        """
        session.run(query, source_id=source_id, target_id=target_id, props=properties)

    def get_player_status(self) -> Optional[Dict[str, Any]]:
        """获取玩家当前状态及周围环境
        
        查询玩家位置、当前地点描述、可通行出口、同区域实体等。
        这是游戏主循环的核心查询，为 LLM 意图解析提供上下文。
        
        Returns:
            包含以下字段的字典：
            - player: 玩家属性字典
            - location: 当前位置属性字典
            - exits: 可通行出口列表
            - entities: 同区域实体列表（NPC、物品等）
            None: 如果找不到玩家实体
        """
        query = """
        MATCH (p:Player)-[:LOCATED_AT]->(loc:Location)
        WITH p, loc
        LIMIT 1
        OPTIONAL MATCH (loc)-[:CONNECTED_TO]-(exits:Location)
        OPTIONAL MATCH (entity)-[:LOCATED_AT]->(loc)
        WHERE entity.id <> p.id AND (entity:NPC OR entity:Item)
        RETURN 
            p AS player,
            loc AS location,
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