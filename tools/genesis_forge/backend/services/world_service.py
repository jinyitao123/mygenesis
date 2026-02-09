"""
世界仿真服务 (WorldService)

基于PRP文档的原子服务实现：
职责: 与Neo4j交互，提供图谱数据预览和沙箱执行

核心方法:
- preview_graph(query): 返回前端可视化所需的节点/边数据
- validate_connectivity(): 检查地图是否连通
- reset_seed_data(): 重置世界到初始状态
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime

from backend.core.models import WorldSnapshot, Neo4jNode, Neo4jRelationship
from backend.core.validation_engine import ValidationEngine

logger = logging.getLogger(__name__)


class WorldService:
    """世界仿真服务"""
    
    def __init__(self, project_root: str, validation_engine: ValidationEngine):
        """
        初始化世界服务
        
        Args:
            project_root: 项目根目录
            validation_engine: 验证引擎
        """
        self.project_root = Path(project_root)
        self.validation_engine = validation_engine
        self.neo4j_loader = None  # 延迟加载
        
        # 缓存
        self.graph_cache: Dict[str, Any] = {}
        self.cache_timeout = 300  # 5分钟缓存
        
    def _get_neo4j_loader(self):
        """获取Neo4j加载器（延迟加载）"""
        if self.neo4j_loader is None:
            try:
                from .neo4j_loader import Neo4jLoader
                self.neo4j_loader = Neo4jLoader()
                logger.info("Neo4j加载器初始化成功")
            except Exception as e:
                logger.warning(f"Neo4j加载器初始化失败: {e}")
                self.neo4j_loader = None
        
        return self.neo4j_loader
    
    def preview_graph(self, query: Optional[str] = None, 
                     node_type: Optional[str] = None,
                     limit: int = 100) -> Dict[str, Any]:
        """
        预览世界图谱
        
        Args:
            query: 自定义Cypher查询
            node_type: 节点类型过滤
            limit: 返回的最大节点数
            
        Returns:
            图谱数据
        """
        try:
            loader = self._get_neo4j_loader()
            if loader is None:
                return self._get_mock_graph_data()
            
            # 生成缓存键
            cache_key = f"preview_{query}_{node_type}_{limit}"
            
            # 检查缓存
            if cache_key in self.graph_cache:
                cached_data, cached_time = self.graph_cache[cache_key]
                if (datetime.now() - cached_time).seconds < self.cache_timeout:
                    logger.debug(f"使用缓存的图谱数据: {cache_key}")
                    return cached_data
            
            if query:
                # 使用自定义查询
                # 验证查询安全性
                valid, errors = self.validation_engine.validate_cypher_query(query)
                if not valid:
                    logger.warning(f"Cypher查询验证失败: {errors}")
                    return self._get_mock_graph_data()
                
                try:
                    result = loader.neo4j.run_transaction(query)
                    graph_data = self._format_query_result(result)
                except Exception as e:
                    logger.error(f"执行Cypher查询失败: {e}")
                    return self._get_mock_graph_data()
            else:
                # 使用默认查询
                graph_data = loader.query_graph(node_type=node_type, limit=limit)
            
            # 缓存结果
            self.graph_cache[cache_key] = (graph_data, datetime.now())
            
            return graph_data
            
        except Exception as e:
            logger.error(f"预览图谱失败: {e}")
            return self._get_mock_graph_data()
    
    def _format_query_result(self, result) -> Dict[str, Any]:
        """格式化查询结果"""
        nodes = []
        links = []
        node_ids = set()
        
        for record in result:
            # 处理记录中的节点和关系
            for key, value in record.items():
                if hasattr(value, 'labels'):
                    # 这是一个节点
                    node_id = getattr(value, 'id', str(id(value)))
                    if node_id not in node_ids:
                        nodes.append({
                            "id": node_id,
                            "labels": list(value.labels),
                            "properties": dict(value)
                        })
                        node_ids.add(node_id)
                
                elif hasattr(value, 'type'):
                    # 这是一个关系
                    rel_id = getattr(value, 'id', str(id(value)))
                    source_id = getattr(value.start_node, 'id', None)
                    target_id = getattr(value.end_node, 'id', None)
                    
                    if source_id and target_id:
                        links.append({
                            "id": rel_id,
                            "source": source_id,
                            "target": target_id,
                            "type": value.type,
                            "properties": dict(value)
                        })
        
        return {
            "nodes": nodes,
            "links": links,
            "stats": {
                "node_count": len(nodes),
                "link_count": len(links)
            }
        }
    
    def _get_mock_graph_data(self) -> Dict[str, Any]:
        """获取模拟图谱数据"""
        return {
            "nodes": [
                {
                    "id": "node_1",
                    "labels": ["Entity"],
                    "properties": {"name": "示例节点1", "type": "entity"}
                },
                {
                    "id": "node_2", 
                    "labels": ["Entity"],
                    "properties": {"name": "示例节点2", "type": "entity"}
                },
                {
                    "id": "node_3",
                    "labels": ["Location"],
                    "properties": {"name": "示例位置", "type": "location"}
                }
            ],
            "links": [
                {
                    "id": "link_1",
                    "source": "node_1",
                    "target": "node_2",
                    "type": "RELATED_TO",
                    "properties": {"strength": 0.8}
                },
                {
                    "id": "link_2",
                    "source": "node_2",
                    "target": "node_3",
                    "type": "LOCATED_AT",
                    "properties": {"distance": 10}
                }
            ],
            "stats": {
                "node_count": 3,
                "link_count": 2
            },
            "mock": True
        }
    
    def validate_connectivity(self, domain: str) -> Dict[str, Any]:
        """
        验证图谱连通性
        
        Args:
            domain: 领域名称
            
        Returns:
            连通性验证结果
        """
        try:
            loader = self._get_neo4j_loader()
            if loader is None:
                return {
                    "status": "warning",
                    "message": "Neo4j未连接，使用模拟验证",
                    "connected": True,
                    "isolated_nodes": [],
                    "mock": True
                }
            
            # 检查孤岛节点（没有关系的节点）
            query = """
            MATCH (n)
            WHERE NOT (n)--()
            RETURN n.id as node_id, labels(n) as node_type, n.name as node_name
            LIMIT 50
            """
            
            result = loader.neo4j.run_transaction(query)
            isolated_nodes = [dict(record) for record in result]
            
            # 检查图是否连通（通过随机节点是否能到达大部分节点）
            connectivity_query = """
            MATCH (n)
            WITH n LIMIT 1
            MATCH path = (n)-[*1..5]-()
            RETURN COUNT(DISTINCT n) as start_nodes, 
                   COUNT(DISTINCT endNode(path)) as reachable_nodes
            """
            
            connectivity_result = list(loader.neo4j.run_transaction(connectivity_query))
            if connectivity_result:
                start_nodes = connectivity_result[0].get("start_nodes", 0)
                reachable_nodes = connectivity_result[0].get("reachable_nodes", 0)
                
                # 获取总节点数
                total_query = "MATCH (n) RETURN COUNT(n) as total_nodes"
                total_result = list(loader.neo4j.run_transaction(total_query))
                total_nodes = total_result[0].get("total_nodes", 0) if total_result else 0
                
                if total_nodes > 0:
                    connectivity_ratio = reachable_nodes / total_nodes
                else:
                    connectivity_ratio = 1.0
            else:
                connectivity_ratio = 0.0
            
            result_data = {
                "status": "success",
                "connected": len(isolated_nodes) == 0 and connectivity_ratio > 0.5,
                "isolated_nodes": isolated_nodes,
                "connectivity_ratio": connectivity_ratio,
                "isolated_count": len(isolated_nodes)
            }
            
            if isolated_nodes:
                result_data["message"] = f"发现 {len(isolated_nodes)} 个孤岛节点"
                result_data["status"] = "warning"
            elif connectivity_ratio < 0.5:
                result_data["message"] = f"图连通性较低: {connectivity_ratio:.2%}"
                result_data["status"] = "warning"
            else:
                result_data["message"] = "图谱连通性良好"
            
            return result_data
            
        except Exception as e:
            logger.error(f"连通性验证失败: {e}")
            return {
                "status": "error",
                "message": f"连通性验证失败: {str(e)}",
                "connected": False,
                "isolated_nodes": []
            }
    
    def reset_seed_data(self, domain: str) -> Dict[str, Any]:
        """
        重置世界到初始状态
        
        Args:
            domain: 领域名称
            
        Returns:
            重置结果
        """
        try:
            # 加载seed数据
            domain_path = self.project_root / "domains" / domain
            seed_file = domain_path / "seed.json"
            
            if not seed_file.exists():
                # 尝试XML格式
                seed_file = domain_path / "seed.xml"
                if not seed_file.exists():
                    return {
                        "status": "error",
                        "message": f"领域 {domain} 的seed文件不存在"
                    }
            
            # 读取seed数据
            content = seed_file.read_text(encoding='utf-8')
            
            # 验证seed数据
            if seed_file.suffix == '.json':
                data = json.loads(content)
                valid, errors = self.validation_engine.validate_json_schema(data, WorldSnapshot)
            else:
                # XML格式需要特殊处理
                data = self._parse_seed_xml(content)
                valid, errors = self.validation_engine.validate_json_schema(data, WorldSnapshot)
            
            if not valid:
                return {
                    "status": "error",
                    "message": f"Seed数据验证失败: {errors}"
                }
            
            snapshot = WorldSnapshot(**data)
            
            # 重置Neo4j数据库
            loader = self._get_neo4j_loader()
            if loader is None:
                return {
                    "status": "warning",
                    "message": "Neo4j未连接，无法重置世界",
                    "mock": True
                }
            
            # 清空现有数据
            clear_result = loader.delete_all_nodes()
            
            # 加载seed数据
            stats = loader.load_to_neo4j(content, clear_existing=False)
            
            # 清除缓存
            self.graph_cache.clear()
            
            return {
                "status": "success",
                "message": "世界重置成功",
                "stats": stats,
                "seed_info": {
                    "snapshot_id": snapshot.snapshot_id,
                    "name": snapshot.name,
                    "node_count": len(snapshot.nodes),
                    "link_count": len(snapshot.links)
                }
            }
            
        except Exception as e:
            logger.error(f"重置世界失败: {e}")
            return {
                "status": "error",
                "message": f"重置世界失败: {str(e)}"
            }
    
    def _parse_seed_xml(self, xml_content: str) -> Dict[str, Any]:
        """解析Seed XML文件"""
        import xml.etree.ElementTree as ET
        
        try:
            root = ET.fromstring(xml_content)
            data = {
                "snapshot_id": root.get("id", "seed_1"),
                "name": root.get("name", "初始世界"),
                "description": root.get("description", ""),
                "nodes": [],
                "links": []
            }
            
            # 解析节点
            nodes_elem = root.find("nodes")
            if nodes_elem is not None:
                for node_elem in nodes_elem.findall("node"):
                    node_data = {
                        "id": node_elem.get("id", ""),
                        "labels": node_elem.get("labels", "").split(",") if node_elem.get("labels") else ["Entity"],
                        "properties": {}
                    }
                    
                    # 解析属性
                    for prop_elem in node_elem.findall("property"):
                        prop_name = prop_elem.get("name")
                        prop_value = prop_elem.text
                        if prop_name and prop_value:
                            node_data["properties"][prop_name] = prop_value
                    
                    data["nodes"].append(node_data)
            
            # 解析关系
            links_elem = root.find("links")
            if links_elem is not None:
                for link_elem in links_elem.findall("link"):
                    link_data = {
                        "id": link_elem.get("id", ""),
                        "source": link_elem.get("source", ""),
                        "target": link_elem.get("target", ""),
                        "type": link_elem.get("type", "RELATED_TO"),
                        "properties": {}
                    }
                    
                    # 解析属性
                    for prop_elem in link_elem.findall("property"):
                        prop_name = prop_elem.get("name")
                        prop_value = prop_elem.text
                        if prop_name and prop_value:
                            link_data["properties"][prop_name] = prop_value
                    
                    data["links"].append(link_data)
            
            return data
            
        except Exception as e:
            logger.warning(f"XML解析失败，返回空seed: {e}")
            return {
                "snapshot_id": "empty",
                "name": "空世界",
                "description": "XML解析失败",
                "nodes": [],
                "links": []
            }
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """
        获取图谱统计信息
        
        Returns:
            统计信息
        """
        try:
            loader = self._get_neo4j_loader()
            if loader is None:
                return self._get_mock_statistics()
            
            # 获取节点类型统计
            node_stats_query = """
            MATCH (n)
            RETURN labels(n) as node_types, COUNT(*) as count
            ORDER BY count DESC
            """
            
            # 获取关系类型统计
            rel_stats_query = """
            MATCH ()-[r]->()
            RETURN type(r) as rel_type, COUNT(*) as count
            ORDER BY count DESC
            """
            
            # 获取属性统计
            prop_stats_query = """
            MATCH (n)
            UNWIND keys(n) as prop_key
            RETURN prop_key, COUNT(*) as count
            ORDER BY count DESC
            LIMIT 20
            """
            
            node_stats = list(loader.neo4j.run_transaction(node_stats_query))
            rel_stats = list(loader.neo4j.run_transaction(rel_stats_query))
            prop_stats = list(loader.neo4j.run_transaction(prop_stats_query))
            
            # 计算总节点数和关系数
            total_nodes = sum(record.get("count", 0) for record in node_stats)
            total_rels = sum(record.get("count", 0) for record in rel_stats)
            
            return {
                "status": "success",
                "total_nodes": total_nodes,
                "total_relationships": total_rels,
                "node_types": [
                    {"type": str(record.get("node_types", [])), "count": record.get("count", 0)}
                    for record in node_stats
                ],
                "relationship_types": [
                    {"type": record.get("rel_type", ""), "count": record.get("count", 0)}
                    for record in rel_stats
                ],
                "top_properties": [
                    {"property": record.get("prop_key", ""), "count": record.get("count", 0)}
                    for record in prop_stats
                ],
                "density": total_rels / max(total_nodes, 1)  # 平均每个节点的关系数
            }
            
        except Exception as e:
            logger.error(f"获取图谱统计失败: {e}")
            return self._get_mock_statistics()
    
    def _get_mock_statistics(self) -> Dict[str, Any]:
        """获取模拟统计信息"""
        return {
            "status": "warning",
            "message": "使用模拟统计信息",
            "total_nodes": 3,
            "total_relationships": 2,
            "node_types": [
                {"type": "['Entity']", "count": 2},
                {"type": "['Location']", "count": 1}
            ],
            "relationship_types": [
                {"type": "RELATED_TO", "count": 1},
                {"type": "LOCATED_AT", "count": 1}
            ],
            "top_properties": [
                {"property": "name", "count": 3},
                {"property": "type", "count": 3}
            ],
            "density": 0.67,
            "mock": True
        }
    
    def execute_sandbox_query(self, cypher_query: str, 
                             parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        在沙箱中执行Cypher查询
        
        Args:
            cypher_query: Cypher查询语句
            parameters: 查询参数
            
        Returns:
            执行结果
        """
        try:
            # 验证查询安全性
            valid, errors = self.validation_engine.validate_cypher_query(cypher_query)
            if not valid:
                return {
                    "status": "error",
                    "message": f"Cypher查询验证失败: {errors}",
                    "error_code": "ERR_CYPHER_02"
                }
            
            loader = self._get_neo4j_loader()
            if loader is None:
                return {
                    "status": "warning",
                    "message": "Neo4j未连接，无法执行查询",
                    "mock": True,
                    "result": []
                }
            
            # 执行查询
            if parameters:
                result = loader.neo4j.run_transaction(cypher_query, parameters)
            else:
                result = loader.neo4j.run_transaction(cypher_query)
            
            # 格式化结果
            formatted_result = []
            for record in result:
                record_dict = {}
                for key, value in record.items():
                    if hasattr(value, '__dict__'):
                        # 处理Neo4j对象
                        if hasattr(value, 'labels'):
                            record_dict[key] = {
                                "type": "node",
                                "id": getattr(value, 'id', str(id(value))),
                                "labels": list(value.labels),
                                "properties": dict(value)
                            }
                        elif hasattr(value, 'type'):
                            record_dict[key] = {
                                "type": "relationship",
                                "id": getattr(value, 'id', str(id(value))),
                                "relationship_type": value.type,
                                "properties": dict(value)
                            }
                        else:
                            record_dict[key] = str(value)
                    else:
                        record_dict[key] = value
                formatted_result.append(record_dict)
            
            return {
                "status": "success",
                "message": "查询执行成功",
                "result": formatted_result,
                "row_count": len(formatted_result)
            }
            
        except Exception as e:
            logger.error(f"沙箱查询执行失败: {e}")
            return {
                "status": "error",
                "message": f"查询执行失败: {str(e)}",
                "result": []
            }
    
    def export_graph_data(self, format: str = "json") -> Tuple[bool, Optional[str], List[str]]:
        """
        导出图谱数据
        
        Args:
            format: 导出格式 ('json', 'csv', 'graphml')
            
        Returns:
            (是否成功, 导出内容, 错误消息)
        """
        try:
            loader = self._get_neo4j_loader()
            if loader is None:
                return False, None, ["Neo4j未连接"]
            
            if format == "json":
                # 导出为JSON
                graph_data = self.preview_graph(limit=1000)  # 限制导出数量
                content = json.dumps(graph_data, ensure_ascii=False, indent=2)
                
            elif format == "csv":
                # 导出为CSV
                content = self._export_to_csv()
                
            elif format == "graphml":
                # 导出为GraphML
                content = self._export_to_graphml()
                
            else:
                return False, None, [f"不支持的导出格式: {format}"]
            
            return True, content, []
            
        except Exception as e:
            error_msg = f"导出图谱数据失败: {str(e)}"
            logger.error(error_msg)
            return False, None, [error_msg]
    
    def _export_to_csv(self) -> str:
        """导出为CSV格式"""
        graph_data = self.preview_graph(limit=1000)
        
        # 生成节点CSV
        nodes_csv = "id,labels,properties\n"
        for node in graph_data.get("nodes", []):
            labels_str = ";".join(node.get("labels", []))
            props_str = json.dumps(node.get("properties", {}), ensure_ascii=False)
            nodes_csv += f'{node.get("id", "")},"{labels_str}","{props_str}"\n'
        
        # 生成关系CSV
        links_csv = "id,source,target,type,properties\n"
        for link in graph_data.get("links", []):
            props_str = json.dumps(link.get("properties", {}), ensure_ascii=False)
            links_csv += f'{link.get("id", "")},{link.get("source", "")},{link.get("target", "")},{link.get("type", "")},"{props_str}"\n'
        
        return f"=== 节点数据 ===\n{nodes_csv}\n=== 关系数据 ===\n{links_csv}"
    
    def _export_to_graphml(self) -> str:
        """导出为GraphML格式"""
        graph_data = self.preview_graph(limit=500)
        
        graphml = """<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns
         http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">
"""
        
        # 添加属性定义
        graphml += '  <key id="label" for="node" attr.name="label" attr.type="string"/>\n'
        graphml += '  <key id="type" for="edge" attr.name="type" attr.type="string"/>\n'
        
        # 开始图定义
        graphml += '  <graph id="G" edgedefault="directed">\n'
        
        # 添加节点
        for node in graph_data.get("nodes", []):
            node_id = node.get("id", "")
            labels = node.get("labels", [])
            label = labels[0] if labels else "Node"
            
            graphml += f'    <node id="{node_id}">\n'
            graphml += f'      <data key="label">{label}</data>\n'
            
            # 添加自定义属性
            for prop_key, prop_value in node.get("properties", {}).items():
                if prop_key not in ["id", "label"]:
                    graphml += f'      <data key="{prop_key}">{prop_value}</data>\n'
            
            graphml += '    </node>\n'
        
        # 添加边
        for link in graph_data.get("links", []):
            link_id = link.get("id", "")
            source = link.get("source", "")
            target = link.get("target", "")
            link_type = link.get("type", "edge")
            
            graphml += f'    <edge id="{link_id}" source="{source}" target="{target}">\n'
            graphml += f'      <data key="type">{link_type}</data>\n'
            
            # 添加自定义属性
            for prop_key, prop_value in link.get("properties", {}).items():
                if prop_key not in ["id", "type"]:
                    graphml += f'      <data key="{prop_key}">{prop_value}</data>\n'
            
            graphml += '    </edge>\n'
        
        graphml += '  </graph>\n'
        graphml += '</graphml>'
        
        return graphml