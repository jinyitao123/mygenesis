"""
Neo4j Loader - XML 到 Neo4j 图数据库导入器
职责：
1. 解析 seed_data.xml 文件
2. 将节点和关系写入 Neo4j
3. 支持增量更新和全量覆盖
4. 提供图谱查询接口
设计理念：遵循 Genesis Ontology 规范，确保数据一致性
"""

import xml.etree.ElementTree as ET
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
import sys

logger = logging.getLogger(__name__)

# 添加父目录到路径以导入服务
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

try:
    from services.neo4j_service import get_neo4j_service, INeo4jService
except ImportError:
    # Fallback for backwards compatibility
    INeo4jService = Any
    logger.warning("Neo4j service abstraction not available, using legacy connection")


class Neo4jLoader:
    """Neo4j 图数据库加载器 - 使用服务抽象层"""
    
    def __init__(self, neo4j_service: Optional[INeo4jService] = None):
        """
        初始化加载器
        
        Args:
            neo4j_service: Neo4j 服务实例，如果为 None 则使用全局服务
        """
        if neo4j_service is not None:
            self.neo4j = neo4j_service
        else:
            # 使用全局服务实例
            try:
                from services.neo4j_service import get_neo4j_service
                self.neo4j = get_neo4j_service()
            except ImportError:
                # Fallback to legacy connection
                try:
                    from genesis.kernel.connectors.neo4j_connector import Neo4jConnector
                    from dotenv import load_dotenv
                    import os
                    load_dotenv()
                    
                    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
                    user = os.getenv("NEO4J_USER", "neo4j")
                    password = os.getenv("NEO4J_PASSWORD", "password")
                    self.neo4j = Neo4jConnector(uri, user, password)
                except ImportError:
                    self.neo4j = None
                    logger.warning("Neo4j connection not available")
    
    def parse_seed_xml(self, seed_xml: str) -> Tuple[List[Dict], List[Dict]]:
        """
        解析 seed_data.xml 文件
        
        Args:
            seed_xml: XML 字符串内容
            
        Returns:
            (nodes, links) 元组
        """
        try:
            root = ET.fromstring(seed_xml)
        except ET.ParseError as e:
            logger.error(f"XML 解析失败: {e}")
            raise ValueError(f"XML 格式错误: {e}")
        
        nodes = []
        links = []
        
        # 解析节点
        for node_elem in root.findall(".//Node"):
            node_id = node_elem.get("id")
            node_type = node_elem.get("type")
            
            if not node_id or not node_type:
                logger.warning(f"跳过无效节点: id={node_id}, type={node_type}")
                continue
            
            properties = {}
            for prop_elem in node_elem.findall(".//Property"):
                key = prop_elem.get("key")
                prop_type = prop_elem.get("type", "string")
                value = prop_elem.text or ""
                
                # 类型转换
                if prop_type == "int" and value:
                    value = int(value)
                elif prop_type == "float" and value:
                    value = float(value)
                elif prop_type == "bool" and value:
                    value = value.lower() == "true"
                
                properties[key] = value
            
            nodes.append({
                "id": node_id,
                "type": node_type,
                "properties": properties
            })
        
        # 解析关系
        for link_elem in root.findall(".//Link"):
            link_type = link_elem.get("type")
            source = link_elem.get("source")
            target = link_elem.get("target")
            
            if not all([link_type, source, target]):
                logger.warning(f"跳过无效关系: type={link_type}, source={source}, target={target}")
                continue
            
            links.append({
                "type": link_type,
                "source": source,
                "target": target
            })
        
        logger.info(f"解析完成: {len(nodes)} 个节点, {len(links)} 个关系")
        return nodes, links
    
    def load_to_neo4j(self, seed_xml: str, clear_existing: bool = True) -> Dict[str, Any]:
        """
        将 XML 数据加载到 Neo4j
        
        Args:
            seed_xml: XML 字符串内容
            clear_existing: 是否先清空现有数据
            
        Returns:
            加载统计信息 {"nodes": N, "links": N}
        """
        nodes, links = self.parse_seed_xml(seed_xml)
        
        logger.info(f"解析到 {len(nodes)} 个节点, {len(links)} 个关系")
        
        if not nodes:
            logger.warning("没有节点数据可加载")
            return {"nodes": 0, "links": 0, "status": "warning", "message": "无节点数据"}
        
        stats: Dict[str, Any] = {"nodes": 0, "links": 0}
        
        try:
            # 清空现有数据（按类型删除，保留标签）
            if clear_existing:
                logger.info("清空现有图谱数据...")
                try:
                    self._safe_run_transaction("""
                        MATCH (n)
                        WHERE n.domain IS NOT NULL
                        DETACH DELETE n
                    """)
                except Exception as clear_error:
                    logger.warning(f"清空数据时出错（可能没有数据）: {clear_error}")
            
            # 解析domain属性
            try:
                xml_root = ET.fromstring(seed_xml)
                domain = xml_root.get("domain", "unknown")
            except:
                domain = "unknown"
            
            # 加载节点
            for node in nodes:
                props = node["properties"].copy()
                props["id"] = node["id"]
                props["type"] = node["type"]
                props["domain"] = domain
                
                # 创建节点，使用类型作为标签
                labels = f":Entity:{node['type']}"
                self._safe_run_transaction(f"""
                    MERGE (n{labels} {{id: $id}})
                    SET n.type = $type,
                        n.domain = $domain,
                        n.label = COALESCE($name, $id)
                """, {
                    "id": node["id"],
                    "type": node["type"],
                    "domain": props["domain"],
                    "name": props.get("name")
                })
                
                # 设置属性
                for key, value in node["properties"].items():
                    if key not in ["id", "type", "domain", "name", "label"]:
                        # 安全地设置属性
                        self._safe_run_transaction(f"""
                            MATCH (n:Entity {{id: $id}})
                            SET n.`{key}` = $value
                        """, {"id": node["id"], "value": value})
                
                stats["nodes"] += 1
            
            # 加载关系
            for link in links:
                self._safe_run_transaction("""
                    MATCH (source:Entity {id: $source})
                    MATCH (target:Entity {id: $target})
                    MERGE (source)-[r:RELATIONSHIP {type: $type}]->(target)
                    SET r.source = $source,
                        r.target = $target
                """, {
                    "type": link["type"],
                    "source": link["source"],
                    "target": link["target"]
                })
                stats["links"] += 1
            
            logger.info(f"Neo4j 加载完成: {stats}")
            stats["status"] = "success"
            return stats
            
        except Exception as e:
            logger.error(f"加载失败: {e}")
            stats["status"] = "error"
            stats["message"] = str(e)
            return stats
    
    def _safe_run_transaction(self, query: str, params: Optional[Dict] = None) -> bool:
        """安全地执行事务（处理 neo4j 可能是 None 的情况）"""
        if self.neo4j is None:
            logger.warning("Neo4j not connected, skipping transaction")
            return False
        
        try:
            if hasattr(self.neo4j, 'run_transaction'):
                self.neo4j.run_transaction(query, params)
            else:
                logger.warning(f"Neo4j service does not support run_transaction")
                return False
            return True
        except Exception as e:
            logger.error(f"Transaction execution failed: {e}")
            return False
    
    def _safe_run_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """安全地执行查询（处理 neo4j 可能是 None 的情况）"""
        if self.neo4j is None:
            logger.warning("Neo4j not connected, returning empty result")
            return []
        
        try:
            if hasattr(self.neo4j, 'run_query'):
                return self.neo4j.run_query(query, params)
            else:
                logger.warning(f"Neo4j service does not support run_query")
                return []
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return []
    
    def query_graph(self, node_type: Optional[str] = None, limit: int = 100, domain: Optional[str] = None) -> Dict[str, Any]:
        """
        查询图谱数据
        
        Args:
            node_type: 可选，按节点类型过滤
            limit: 最大返回节点数
            domain: 可选，按领域过滤
            
        Returns:
            图谱数据字典
        """
        try:
            # 构建查询条件
            where_conditions = []
            query_params: Dict[str, Any] = {"limit": limit}
            
            if node_type:
                where_conditions.append("n.type = $type")
                query_params["type"] = node_type
            
            if domain:
                where_conditions.append("n.domain = $domain")
                query_params["domain"] = domain
            
            where_clause = " AND ".join(where_conditions) if where_conditions else ""
            
            # 查询节点
            if where_clause:
                nodes_result = self._safe_run_query(f"""
                    MATCH (n:Entity)
                    WHERE {where_clause}
                    RETURN n.id as id, n.type as type, n.label as label, properties(n) as props
                    LIMIT $limit
                """, query_params)
            else:
                nodes_result = self._safe_run_query("""
                    MATCH (n:Entity)
                    RETURN n.id as id, n.type as type, n.label as label, properties(n) as props
                    LIMIT $limit
                """, {"limit": limit})
            
            nodes = []
            for record in nodes_result:
                props = record.get("props", {})
                # 移除内部属性
                for internal in ["id", "type", "domain", "label"]:
                    props.pop(internal, None)
                
                nodes.append({
                    "id": record.get("id"),
                    "type": record.get("type"),
                    "label": record.get("label"),
                    "properties": props
                })
            
            # 查询关系
            links_result = self._safe_run_query("""
                MATCH (s:Entity)-[r:RELATIONSHIP]->(t:Entity)
                RETURN r.type as type, s.id as source, t.id as target
            """)
            
            links = []
            for record in links_result:
                links.append({
                    "type": record.get("type"),
                    "source": record.get("source"),
                    "target": record.get("target")
                })
            
            return {
                "status": "success",
                "nodes": nodes,
                "links": links,
                "stats": {
                    "node_count": len(nodes),
                    "link_count": len(links)
                }
            }
            
        except Exception as e:
            logger.error(f"查询失败: {e}")
            return {
                "status": "error",
                "message": str(e),
                "nodes": [],
                "links": []
            }
    
    def get_node_types(self) -> List[str]:
        """获取所有节点类型"""
        try:
            result = self._safe_run_query("""
                MATCH (n:Entity)
                RETURN DISTINCT n.type as type
                ORDER BY type
            """)
            return [r.get("type") for r in result if r.get("type")]
        except Exception as e:
            logger.error(f"获取节点类型失败: {e}")
            return []
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """获取图谱统计信息"""
        try:
            node_result = self._safe_run_query("""
                MATCH (n:Entity)
                RETURN count(n) as count
            """)
            node_count = node_result[0].get("count", 0) if node_result else 0
            
            link_result = self._safe_run_query("""
                MATCH ()-[r:RELATIONSHIP]->()
                RETURN count(r) as count
            """)
            link_count = link_result[0].get("count", 0) if link_result else 0
            
            node_types = self.get_node_types()
            
            return {
                "status": "success",
                "node_count": node_count,
                "link_count": link_count,
                "node_types": node_types
            }
        except Exception as e:
            logger.error(f"获取统计失败: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def update_node(self, node_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新节点属性
        
        Args:
            node_id: 节点 ID
            properties: 要更新的属性字典
            
        Returns:
            操作结果
        """
        try:
            # 构建 SET 子句
            set_clauses = ["n.id = $id"]
            params: Dict[str, Any] = {"id": node_id}
            
            for key, value in properties.items():
                param_key = f"prop_{key}"
                set_clauses.append(f"n.`{key}` = ${param_key}")
                params[param_key] = value
            
            cypher = f"""
                MATCH (n:Entity {{id: $id}})
                SET {', '.join(set_clauses)}
                SET n.label = COALESCE(n.name, n.id)
            """
            
            self._safe_run_transaction(cypher, params)
            
            logger.info(f"Updated node: {node_id}")
            return {
                "status": "success",
                "message": f"节点 {node_id} 更新成功",
                "node_id": node_id
            }
            
        except Exception as e:
            logger.error(f"更新节点失败: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def delete_node(self, node_id: str) -> Dict[str, Any]:
        """
        删除节点及其关联关系
        
        Args:
            node_id: 节点 ID
            
        Returns:
            操作结果
        """
        try:
            self._safe_run_transaction("""
                MATCH (n:Entity {id: $id})
                DETACH DELETE n
            """, {"id": node_id})
            
            logger.info(f"Deleted node: {node_id}")
            return {
                "status": "success",
                "message": f"节点 {node_id} 删除成功",
                "node_id": node_id
            }
            
        except Exception as e:
            logger.error(f"删除节点失败: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def delete_all_nodes(self) -> Dict[str, Any]:
        """
        删除当前领域的所有节点
        
        Returns:
            操作结果
        """
        try:
            # 获取当前领域
            result = self._safe_run_query("""
                MATCH (n:Entity)
                WHERE n.domain IS NOT NULL
                RETURN DISTINCT n.domain as domain
                LIMIT 1
            """)
            
            domain = None
            if result and result[0]:
                domain = result[0].get("domain")
            
            if domain:
                self._safe_run_transaction("""
                    MATCH (n:Entity {domain: $domain})
                    DETACH DELETE n
                """, {"domain": domain})
            
            logger.info(f"Deleted all nodes for domain: {domain}")
            return {
                "status": "success",
                "message": "清空图库成功"
            }
            
        except Exception as e:
            logger.error(f"清空图库失败: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
