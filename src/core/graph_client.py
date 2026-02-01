from neo4j import GraphDatabase
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class GraphClient:
    """Neo4j 图数据库客户端 v0.3
    
    负责所有与 Neo4j 的交互，支持 v0.3 语义驱动的仿真宇宙。
    关键特性：
    1. 懒加载检查：支持分形生成，只在需要时填充细节
    2. 通用节点创建：支持 Action 本体驱动的数据插入
    3. 智能查询：为动力学引擎提供数据支持
    4. 推演支持：支持全局时钟和 NPC 自主行为
    
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
        logger.info("Neo4j 连接已建立 (v0.3)")
    
    def get_driver(self):
        """获取 Neo4j 驱动实例（供 ActionDriver 等组件复用）
        
        Returns:
            Neo4j 驱动实例
        """
        return self.driver
    
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
    
    def create_nodes_from_json(self, nodes_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """v0.3 核心：通用节点创建器（支持分形生成）
        
        将 LLM 生成的 JSON 节点数据批量插入 Neo4j。
        支持懒加载模式：只创建骨架，后续填充细节。
        
        Args:
            nodes_data: 节点数据列表，每个节点至少包含 id 和 label
            
        Returns:
            创建统计：{"created": 已创建节点数, "skipped": 跳过节点数}
        """
        created = 0
        skipped = 0
        
        with self.driver.session() as session:
            for node in nodes_data:
                node_id = node.get("id")
                label = node.get("label", "Entity")
                
                if not node_id:
                    logger.warning(f"跳过无 ID 的节点: {node}")
                    skipped += 1
                    continue
                
                # 检查节点是否已存在（防止重复创建）
                existing = session.run(
                    "MATCH (n {id: $id}) RETURN n.id LIMIT 1",
                    id=node_id
                ).single()
                
                if existing:
                    logger.debug(f"节点已存在，跳过: {node_id}")
                    skipped += 1
                    continue
                
                # 构建属性
                properties = {}
                if "properties" in node:
                    properties = node["properties"]
                else:
                    # 从节点中提取除 id 和 label 外的所有属性
                    properties = {k: v for k, v in node.items() 
                                 if k not in ["id", "label"]}
                
                # 合并 id 到 properties
                all_props = {"id": node_id}
                all_props.update(properties)
                
                # 创建节点
                query = f"CREATE (n:{label} $props)"
                session.run(query, props=all_props)  # type: ignore
                created += 1
                logger.debug(f"创建节点: {node_id} ({label})")
        
        stats = {"created": created, "skipped": skipped}
        logger.info(f"节点创建完成: {stats}")
        return stats
    
    def create_relationships_from_json(self, edges_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """v0.3 核心：通用关系创建器
        
        批量创建节点间的关系。
        
        Args:
            edges_data: 边数据列表，每个边包含 source, target, type
            
        Returns:
            创建统计：{"created": 已创建关系数, "skipped": 跳过关系数}
        """
        created = 0
        skipped = 0
        
        with self.driver.session() as session:
            for edge in edges_data:
                source_id = edge.get("source")
                target_id = edge.get("target")
                rel_type = edge.get("type") or edge.get("label", "RELATED_TO")
                
                if not source_id or not target_id:
                    logger.warning(f"跳过无效关系: {edge}")
                    skipped += 1
                    continue
                
                # 检查关系是否已存在（防止重复）
                existing = session.run("""
                    MATCH (a {id: $sid})-[r:%s]-(b {id: $tid})
                    RETURN r LIMIT 1
                """ % rel_type, sid=source_id, tid=target_id).single()
                
                if existing:
                    logger.debug(f"关系已存在，跳过: {source_id}-[{rel_type}]->{target_id}")
                    skipped += 1
                    continue
                
                # 提取关系属性
                properties = {}
                if "properties" in edge:
                    properties = edge["properties"]
                else:
                    properties = {k: v for k, v in edge.items() 
                                 if k not in ["source", "target", "type", "label"]}
                
                # 创建关系
                if properties:
                    query = f"""
                    MATCH (a {{id: $sid}}), (b {{id: $tid}})
                    CREATE (a)-[r:{rel_type}]->(b)
                    SET r = $props
                    """
                    session.run(query, sid=source_id, tid=target_id, props=properties)  # type: ignore
                else:
                    query = f"""
                    MATCH (a {{id: $sid}}), (b {{id: $tid}})
                    CREATE (a)-[r:{rel_type}]->(b)
                    """
                    session.run(query, sid=source_id, tid=target_id)  # type: ignore
                
                created += 1
                logger.debug(f"创建关系: {source_id}-[{rel_type}]->{target_id}")
        
        stats = {"created": created, "skipped": skipped}
        logger.info(f"关系创建完成: {stats}")
        return stats
    
    def get_location_meta(self, location_id: str) -> Dict[str, Any]:
        """v0.3 核心：懒加载检查器
        
        检查地点节点是否已有足够细节，决定是否需要调用 LLM 填充。
        遵循 v0.3 分形生成策略：骨架 → 细节填充。
        
        Args:
            location_id: 地点节点 ID
            
        Returns:
            地点元数据，包含：
            - has_details: 是否已有细节描述
            - detail_level: 细节等级 (0-骨架, 1-基础, 2-丰富)
            - node_count: 该地点内的实体数量
            - needs_expansion: 是否需要扩展（懒加载触发条件）
        """
        with self.driver.session() as session:
            # 查询地点基本信息
            query = """
            MATCH (loc {id: $id})
            OPTIONAL MATCH (loc)-[:CONTAINS]->(content)
            RETURN 
                loc.id as id,
                loc.name as name,
                loc.description as description,
                loc.detail_level as detail_level,
                count(content) as entity_count
            """
            
            result = session.run(query, id=location_id).single()
            
            if not result:
                return {
                    "has_details": False,
                    "detail_level": 0,
                    "node_count": 0,
                    "needs_expansion": True
                }
            
            detail_level = result.get("detail_level") or 0
            description = result.get("description") or ""
            entity_count = result.get("entity_count") or 0
            
            # 判断是否需要扩展
            # Rule: 如果 detail_level < 2 且 entity_count < 3，需要扩展
            needs_expansion = (detail_level < 2 and entity_count < 3)
            
            return {
                "id": result.get("id"),
                "name": result.get("name"),
                "has_details": bool(description and len(description) > 10),
                "detail_level": detail_level,
                "node_count": entity_count,
                "needs_expansion": needs_expansion
            }
    
    def get_player_status(self) -> Optional[Dict[str, Any]]:
        """获取玩家当前状态及周围环境
        
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
    
    def get_npc_details(self, npc_id: str) -> Optional[Dict[str, Any]]:
        """v0.3 核心：获取 NPC 完整详情（用于生成式对话）
        
        查询 NPC 的所有属性，包括人设、阵营、位置、对话等。
        为 LLM 对话生成提供完整上下文。
        
        Args:
            npc_id: NPC 节点 ID
            
        Returns:
            NPC 完整信息字典
            None: 如果未找到 NPC
        """
        with self.driver.session() as session:
            query = """
            MATCH (n:NPC {id: $id})-[:LOCATED_AT]->(loc:Location)
            OPTIONAL MATCH (n)-[:BELONGS_TO]->(f:Faction)
            RETURN 
                n.id as id,
                n.name as name,
                n.dialogue as dialogue,
                n.disposition as disposition,
                loc.id as location_id,
                loc.name as location_name,
                f.id as faction_id,
                f.name as faction_name,
                properties(n) as props
            """
            
            result = session.run(query, id=npc_id).single()
            if not result:
                return None
            
            props = dict(result["props"])
            for key in ["id", "name", "dialogue", "disposition"]:
                props.pop(key, None)
            
            return {
                "id": result["id"],
                "name": result["name"],
                "dialogue": result["dialogue"],
                "disposition": result["disposition"],
                "location": {
                    "id": result["location_id"],
                    "name": result["location_name"]
                } if result["location_id"] else None,
                "faction": {
                    "id": result["faction_id"],
                    "name": result["faction_name"]
                } if result["faction_id"] else None,
                "properties": props
            }
    
    def get_npc_details_by_name(self, npc_name: str) -> Optional[Dict[str, Any]]:
        """根据名称获取 NPC 详情
        
        Args:
            npc_name: NPC 中文名称
            
        Returns:
            NPC 完整信息字典
            None: 如果未找到 NPC
        """
        with self.driver.session() as session:
            query = """
            MATCH (n:NPC {name: $name})-[:LOCATED_AT]->(loc:Location)
            OPTIONAL MATCH (n)-[:BELONGS_TO]->(f:Faction)
            RETURN 
                n.id as id,
                n.name as name,
                n.dialogue as dialogue,
                n.disposition as disposition,
                loc.id as location_id,
                loc.name as location_name,
                f.id as faction_id,
                f.name as faction_name,
                properties(n) as props
            """
            
            result = session.run(query, name=npc_name).single()  # type: ignore
            if not result:
                return None
            
            # 构建完整信息字典
            props = dict(result["props"])
            # 移除已单独列出的字段
            for key in ["id", "name", "dialogue", "disposition"]:
                props.pop(key, None)
            
            return {
                "id": result["id"],
                "name": result["name"],
                "dialogue": result["dialogue"],
                "disposition": result["disposition"],
                "location": {
                    "id": result["location_id"],
                    "name": result["location_name"]
                } if result["location_id"] else None,
                "faction": {
                    "id": result["faction_id"],
                    "name": result["faction_name"]
                } if result["faction_id"] else None,
                "properties": props
            }
    
    def execute_move(self, target_name: str) -> Tuple[bool, str]:
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
    
    def run_global_tick(self) -> List[str]:
        """
        v0.3 核心：全局图谱推演 - 让世界活起来
        
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
            move_query = """
            MATCH (n:NPC)-[old:LOCATED_AT]->(curr:Location)
            MATCH (curr)-[:CONNECTED_TO]-(next:Location)
            WHERE n.hp > 0 
              AND rand() < 0.2  // 20% 概率移动
              AND NOT n.name CONTAINS '宫门'  // 宫门卫兵坚守岗位！
            
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
                logger.info(f"[世界推演] {record['npc']} 从 {record['from_loc']} 移动到了 {record['to_loc']}")
            
            # -------------------------------------------------------
            # 2. 视野外战斗推演 (NPC vs NPC)
            # -------------------------------------------------------
            battle_query = """
            MATCH (n1:NPC)-[:LOCATED_AT]->(loc:Location)<-[:LOCATED_AT]-(n2:NPC)
            WHERE n1.id < n2.id  // 避免重复计算
            AND n1.hp > 0 AND n2.hp > 0
            
            // 检查敌对关系
            MATCH (n1)-[:BELONGS_TO]->(f1:Faction)-[:HOSTILE_TO]-(f2:Faction)<-[:BELONGS_TO]-(n2)
            
            // 只有当玩家不在这个房间时
            WHERE NOT EXISTS {
                MATCH (:Player)-[:LOCATED_AT]->(loc)
            }
            
            // 简单的互相伤害逻辑
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
            # 3. 死亡清理
            # -------------------------------------------------------
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
    
    def run_smart_simulation(self, player_id: str) -> List[Dict]:
        """
        基于图谱关系的智能推演
        
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
    
    def get_entity_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """根据 ID 获取任意实体
        
        Args:
            entity_id: 实体节点 ID
            
        Returns:
            实体属性字典，包含所有属性和标签
            None: 如果未找到实体
        """
        with self.driver.session() as session:
            query = """
            MATCH (n {id: $id})
            RETURN n, labels(n) as labels
            """
            result = session.run(query, id=entity_id).single()
            if not result:
                return None
            
            entity = dict(result["n"])
            entity["labels"] = result["labels"]
            return entity
    
    def check_relationship_exists(self, source_id: str, target_id: str, 
                                 rel_type: Optional[str] = None) -> bool:
        """检查两个实体间是否存在特定关系
        
        Args:
            source_id: 源实体 ID
            target_id: 目标实体 ID
            rel_type: 关系类型（可选），如果为 None 则检查任意关系
            
        Returns:
            bool: 是否存在指定关系
        """
        with self.driver.session() as session:
            if rel_type:
                query = """
                MATCH (a {id: $sid})-[r:%s]-(b {id: $tid})
                RETURN r LIMIT 1
                """ % rel_type
            else:
                query = """
                MATCH (a {id: $sid})--(b {id: $tid})
                RETURN 1 LIMIT 1
                """
            
            result = session.run(query, sid=source_id, tid=target_id).single()  # type: ignore
            return result is not None
    
    def get_entity_property(self, entity_id: str, property_name: str) -> Any:
        """获取实体特定属性值
        
        Args:
            entity_id: 实体节点 ID
            property_name: 属性名
            
        Returns:
            属性值，如果属性不存在返回 None
        """
        with self.driver.session() as session:
            query = """
            MATCH (n {id: $id})
            RETURN n[$prop] as value
            """
            result = session.run(query, id=entity_id, prop=property_name).single()
            return result["value"] if result else None
    
    def set_entity_property(self, entity_id: str, property_name: str, value: Any) -> bool:
        """设置实体属性值
        
        Args:
            entity_id: 实体节点 ID
            property_name: 属性名
            value: 属性值
            
        Returns:
            bool: 是否设置成功
        """
        with self.driver.session() as session:
            query = """
            MATCH (n {id: $id})
            SET n[$prop] = $value
            RETURN n.id
            """
            result = session.run(query, id=entity_id, prop=property_name, value=value).single()
            return result is not None