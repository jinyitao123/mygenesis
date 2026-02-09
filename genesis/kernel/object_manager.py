"""
Object Manager - 对象管理器

负责对象的 CRUD 操作，提供通用的对象管理接口。
特点：
- 零业务逻辑，通用性强
- 属性名安全验证（防 Cypher 注入）
- 支持对象类型定义验证

对比当前项目：
- 旧：GraphClient.create_nodes_from_json() - 批量创建，无验证
- 新：ObjectManager.create_object() - 单对象创建，带验证
"""

import re
import xml.etree.ElementTree as ET
import json
from typing import Dict, List, Any, Optional, cast, Union
from genesis.kernel.connectors.neo4j_connector import Neo4jConnector
import logging

logger = logging.getLogger(__name__)


class ObjectManager:
    """对象管理器 - 通用对象 CRUD"""
    
    def __init__(self, object_types: Dict[str, Any], neo4j_conn: Neo4jConnector):
        """
        初始化对象管理器
        
        Args:
            object_types: 对象类型定义（来自 object_types.json）
            neo4j_conn: Neo4j 连接器实例
        """
        self.object_types = object_types.get('object_types', {})
        self.link_types = object_types.get('link_types', {})
        self.neo4j = neo4j_conn
    
    def _validate_property_name(self, prop_name: str) -> bool:
        """
        验证属性名是否安全（防止 Cypher 注入）
        
        Args:
            prop_name: 属性名
            
        Returns:
            是否安全
        """
        # 只允许字母、数字、下划线，且不能以数字开头
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', prop_name))
    
    def _validate_properties_for_type(self, object_type: str, properties: Dict[str, Any], 
                                    allow_undefined: bool = False) -> None:
        """
        验证属性是否适合对象类型
        
        Args:
            object_type: 对象类型
            properties: 属性字典
            allow_undefined: 是否允许未定义的属性
            
        Raises:
            ValueError: 如果属性无效
        """
        type_def = self.object_types.get(object_type)
        if not type_def:
            raise ValueError(f"Unknown object type: {object_type}")
        
        defined_props = type_def.get('properties', {})
        
        for prop_name in properties.keys():
            # 1. 验证属性名安全
            if not self._validate_property_name(prop_name):
                raise ValueError(f"Invalid property name: '{prop_name}'. "
                               "Only letters, numbers and underscores are allowed.")
            
            # 2. 验证属性是否定义（如果 allow_undefined 为 False）
            if not allow_undefined and prop_name not in defined_props:
                raise ValueError(f"Property '{prop_name}' is not defined for object type '{object_type}'. "
                               f"Defined properties: {list(defined_props.keys())}")
    
    def create_object(self, object_type: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建新对象
        
        Args:
            object_type: 对象类型（例如：'Player', 'NPC'）
            properties: 对象属性（必须包含 'id'）
            
        Returns:
            创建的对象数据
            
        Raises:
            ValueError: 如果对象类型未知或属性无效
        """
        # 1. 验证对象类型
        if object_type not in self.object_types:
            raise ValueError(f"Unknown object type: {object_type}. "
                           f"Available types: {list(self.object_types.keys())}")
        
        # 2. 验证必须有 id
        if 'id' not in properties:
            raise ValueError("Property 'id' is required")
        
        # 3. 验证属性
        self._validate_properties_for_type(object_type, properties, allow_undefined=False)
        
        # 4. 构建 Cypher 查询 (同时返回 n.id)
        prop_items = [f"{k}: ${k}" for k in properties.keys()]
        prop_str = ", ".join(prop_items)
        cypher = f"CREATE (n:{object_type} {{{prop_str}}}) RETURN n, n.id as node_id"

        # 5. 执行创建
        try:
            result = self.neo4j.execute_write(cypher, properties)
            if result:
                logger.info(f"[ObjectManager] Created {object_type}: {properties['id']}")
                node_data = dict(result[0].get('n', {}))
                node_data['id'] = result[0].get('node_id') or properties['id']
                return node_data
            else:
                raise RuntimeError("Create returned no data")
        except Exception as e:
            logger.error(f"[ObjectManager] Failed to create {object_type}: {e}")
            raise
    
    def get_object(self, object_type: str, object_id: str) -> Optional[Dict[str, Any]]:
        """
        获取单个对象
        
        Args:
            object_type: 对象类型
            object_id: 对象 ID
            
        Returns:
            对象数据，如果不存在则返回 None
        """
        type_def = self.object_types.get(object_type)
        if not type_def:
            raise ValueError(f"Unknown object type: {object_type}")
        
        # 获取主键字段（默认 'id'）
        pk = type_def.get('primary_key', 'id')
        
        cypher = f"MATCH (n:{object_type} {{{pk}: $id}}) RETURN n, n.id as node_id"

        try:
            result = self.neo4j.run_query(cypher, {"id": object_id})
            if result and result[0].get('n'):
                node_data = dict(result[0]['n'])  # Convert Node to dict
                # Reason: 使用查询返回的 n.id 或回退到参数
                node_data['id'] = result[0].get('node_id') or object_id
                return node_data
            return None
        except Exception as e:
            logger.error(f"[ObjectManager] Failed to get {object_type}/{object_id}: {e}")
            raise
    
    def update_object(self, object_type: str, object_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新对象属性
        
        Args:
            object_type: 对象类型
            object_id: 对象 ID
            properties: 要更新的属性（不能包含 'id'）
            
        Returns:
            更新后的对象数据
        """
        # 不能更新 id
        if 'id' in properties:
            del properties['id']
        
        if not properties:
            raise ValueError("No properties to update")
        
        type_def = self.object_types.get(object_type)
        if not type_def:
            raise ValueError(f"Unknown object type: {object_type}")
        
        pk = type_def.get('primary_key', 'id')
        
        # 验证属性
        self._validate_properties_for_type(object_type, properties, allow_undefined=False)
        
        # 构建 SET 子句
        set_clauses = [f"n.{k} = ${k}" for k in properties.keys()]
        set_str = ", ".join(set_clauses)
        
        cypher = f"""
        MATCH (n:{object_type} {{{pk}: $id}})
        SET {set_str}
        RETURN n
        """
        
        params = {"id": object_id, **properties}
        
        try:
            result = self.neo4j.execute_write(cypher, params)
            if result:
                logger.info(f"[ObjectManager] Updated {object_type}: {object_id}")
                return result[0].get('n', {})
            else:
                raise ValueError(f"{object_type} with {pk}={object_id} not found")
        except Exception as e:
            logger.error(f"[ObjectManager] Failed to update {object_type}/{object_id}: {e}")
            raise
    
    def delete_object(self, object_type: str, object_id: str) -> bool:
        """
        删除对象（级联删除关系）
        
        Args:
            object_type: 对象类型
            object_id: 对象 ID
            
        Returns:
            是否成功删除
        """
        type_def = self.object_types.get(object_type)
        if not type_def:
            raise ValueError(f"Unknown object type: {object_type}")
        
        pk = type_def.get('primary_key', 'id')
        cypher = f"MATCH (n:{object_type} {{{pk}: $id}}) DETACH DELETE n"
        
        try:
            self.neo4j.run_transaction(cypher, {"id": object_id})
            logger.info(f"[ObjectManager] Deleted {object_type}: {object_id}")
            return True
        except Exception as e:
            logger.error(f"[ObjectManager] Failed to delete {object_type}/{object_id}: {e}")
            raise
    
    def query_objects(self, object_type: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        查询对象列表
        
        Args:
            object_type: 对象类型
            filters: 过滤条件（属性名=值）
            
        Returns:
            对象列表
        """
        type_def = self.object_types.get(object_type)
        if not type_def:
            raise ValueError(f"Unknown object type: {object_type}")
        
        if filters:
            # 验证过滤属性名安全性
            for prop_name in filters.keys():
                if not self._validate_property_name(prop_name):
                    raise ValueError(f"Invalid filter property name: '{prop_name}'")
            
            where_clauses = [f"n.{k} = ${k}" for k in filters.keys()]
            where_str = " AND ".join(where_clauses)
            cypher = f"MATCH (n:{object_type}) WHERE {where_str} RETURN n, n.id as node_id"
            result = self.neo4j.run_query(cypher, filters)
        else:
            cypher = f"MATCH (n:{object_type}) RETURN n, n.id as node_id"
            result = self.neo4j.run_query(cypher)

        # Reason: Convert Neo4j Node objects to dicts and ensure id field
        records = []
        for record in result:
            node = record.get('n')
            if node:
                node_dict = dict(node)  # Convert Node to dict
                # Reason: 使用查询返回的 n.id
                node_dict['id'] = record.get('node_id')
                records.append(node_dict)
        return records
    
    def create_link(self, link_type: str, source_id: str, target_id: str, 
                   source_type: Optional[str] = None, target_type: Optional[str] = None,
                   properties: Optional[Dict[str, Any]] = None):
        """
        创建对象间的关系链接
        
        Args:
            link_type: 关系类型（例如：'LOCATED_AT', 'CONNECTED_TO'）
            source_id: 源对象 ID
            target_id: 目标对象 ID
            source_type: 源对象类型（如果为 None，则从 link_types 推断）
            target_type: 目标对象类型（如果为 None，则从 link_types 推断）
            properties: 关系属性（可选）
        """
        # 获取关系类型定义
        link_def = self.link_types.get(link_type)
        if link_def:
            # 从定义推断类型
            if not source_type:
                source_types = link_def.get('source', '').split('|')
                source_type = source_types[0] if source_types else None
            if not target_type:
                target_type = link_def.get('target', '')
        
        if not source_type or not target_type:
            raise ValueError(f"Cannot determine source/target type for link {link_type}")
        
        # 获取主键字段
        source_type_def = self.object_types.get(source_type, {})
        source_pk = source_type_def.get('primary_key', 'id')
        
        target_type_def = self.object_types.get(target_type, {})
        target_pk = target_type_def.get('primary_key', 'id')
        
        # 构建属性字符串
        prop_items = []
        if properties:
            # 验证关系属性名安全性
            for prop_name in properties.keys():
                if not self._validate_property_name(prop_name):
                    raise ValueError(f"Invalid relationship property name: '{prop_name}'")
            for k, v in properties.items():
                prop_items.append(f"{k}: ${k}")
        
        prop_str = ", ".join(prop_items)
        
        # 构建 Cypher - 使用 MERGE 避免重复创建关系
        if prop_str:
            cypher = f"""
            MATCH (source:{source_type} {{{source_pk}: $source_id}})
            MATCH (target:{target_type} {{{target_pk}: $target_id}})
            MERGE (source)-[r:{link_type} {{{prop_str}}}]->(target)
            RETURN r
            """
        else:
            cypher = f"""
            MATCH (source:{source_type} {{{source_pk}: $source_id}})
            MATCH (target:{target_type} {{{target_pk}: $target_id}})
            MERGE (source)-[r:{link_type}]->(target)
            RETURN r
            """
        
        params = {
            "source_id": source_id,
            "target_id": target_id,
            **(properties or {})
        }
        
        try:
            self.neo4j.run_transaction(cypher, params)
            logger.debug(f"[ObjectManager] Created link {link_type}: {source_id} -> {target_id}")
        except Exception as e:
            logger.error(f"[ObjectManager] Failed to create link: {e}")
            raise
    
    def get_related_objects(self, object_type: str, object_id: str, link_type: str, 
                           direction: str = "outgoing") -> List[Dict[str, Any]]:
        """
        获取关联的对象
        
        Args:
            object_type: 对象类型
            object_id: 对象 ID
            link_type: 关系类型
            direction: 方向 ('outgoing', 'incoming', 'both')
            
        Returns:
            关联对象列表
        """
        type_def = self.object_types.get(object_type, {})
        pk = type_def.get('primary_key', 'id')
        
        if direction == "outgoing":
            cypher = f"""
            MATCH (n:{object_type} {{{pk}: $id}})-[:{link_type}]->(related)
            RETURN related, related.id as related_id
            """
        elif direction == "incoming":
            cypher = f"""
            MATCH (n:{object_type} {{{pk}: $id}})<-[:{link_type}]-(related)
            RETURN related, related.id as related_id
            """
        else:  # both
            cypher = f"""
            MATCH (n:{object_type} {{{pk}: $id}})-[:{link_type}]-(related)
            RETURN related, related.id as related_id
            """

        result = self.neo4j.run_query(cypher, {"id": object_id})
        # Reason: Convert Neo4j Node objects to dicts and ensure id field
        records = []
        for record in result:
            node = record.get('related')
            if node:
                node_dict = dict(node)  # Convert Node to dict
                # Reason: 使用查询返回的 related.id
                node_dict['id'] = record.get('related_id')
                records.append(node_dict)
        return records
    
    def get_all_object_types(self) -> List[Dict[str, Any]]:
        """
        获取所有对象类型定义
        
        Returns:
            对象类型列表
        """
        return [
            {
                "type_id": type_id,
                "display_name": def_.get('display_name', type_id),
                "description": def_.get('description', ''),
                "properties": def_.get('properties', {})
            }
            for type_id, def_ in self.object_types.items()
        ]

    # ==================== XML 适配器方法 ====================
    
    def load_world_from_xml(self, xml_file_path: str):
        """
        [新增] XML 专用加载入口
        1. 解析 XML
        2. 转换数据类型
        3. 调用通用创建接口
        
        Args:
            xml_file_path: XML 文件路径
            
        Raises:
            ET.ParseError: XML 格式错误
            Exception: 其他解析或创建错误
        """
        try:
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            
            # 1. 解析节点 (Nodes)
            parsed_nodes = []
            for node_elem in root.findall('./Nodes/Node'):
                entity_data = self._parse_node_element(node_elem)
                parsed_nodes.append(entity_data)
                
            # 2. 解析关系 (Links)
            parsed_links = []
            for link_elem in root.findall('./Links/Link'):
                link_data = self._parse_link_element(link_elem)
                parsed_links.append(link_data)

            # 3. 执行批量创建 (复用原有的逻辑)
            self._batch_create_entities(parsed_nodes)
            self._batch_create_relations(parsed_links)
            
            logger.info(f"[ObjectManager] 成功从 XML 加载世界: {len(parsed_nodes)} 节点, {len(parsed_links)} 关系")

        except ET.ParseError as e:
            logger.error(f"[ObjectManager] XML 格式错误: {e}")
            raise
        except Exception as e:
            logger.error(f"[ObjectManager] 世界初始化失败: {e}")
            raise

    def _parse_node_element(self, element: ET.Element) -> Dict[str, Any]:
        """
        逻辑：将 <Node> 标签转换为内部字典
        
        Args:
            element: XML Node 元素
            
        Returns:
            节点数据字典
        """
        # 提取基础属性
        node_id = element.get('id')
        node_type = element.get('type')
        
        if node_id is None:
            raise ValueError("XML Node 元素缺少 'id' 属性")
        if node_type is None:
            raise ValueError("XML Node 元素缺少 'type' 属性")
        
        properties: Dict[str, Any] = {
            "id": node_id,
            "name": "Unknown" # 默认值
        }

        # 提取 <Property> 子标签并进行类型转换
        for prop in element.findall('Property'):
            key = prop.get('key')
            raw_value = prop.text
            value_type = prop.get('type', 'string') # 默认为 string
            
            # ★ 核心逻辑：类型强转
            if key is not None:  # 确保 key 不为 None
                typed_value = self._cast_value(raw_value, value_type)
                properties[key] = typed_value
                logger.debug(f"[ObjectManager] XML属性解析: key={key}, raw_value={raw_value}, type={value_type}, typed_value={typed_value}")

        return {
            "id": node_id,
            "type": node_type,
            "properties": properties
        }

    def _parse_link_element(self, element: ET.Element) -> Dict[str, Any]:
        """
        逻辑：将 <Link> 标签转换为内部字典
        
        Args:
            element: XML Link 元素
            
        Returns:
            关系数据字典
        """
        return {
            "type": element.get('type'),
            "source": element.get('source'),
            "target": element.get('target')
        }

    def _cast_value(self, value: Optional[str], target_type: str) -> Any:
        """
        类型转换器：处理 XML 纯文本问题
        
        Args:
            value: 原始字符串值（可能为 None）
            target_type: 目标类型 ('int', 'float', 'bool', 'json', 'string')
            
        Returns:
            转换后的值
        """
        if value is None:
            return ""
            
        value = value.strip()
        
        if target_type == 'int':
            return int(value)
        elif target_type == 'float':
            return float(value)
        elif target_type == 'bool':
            return value.lower() in ('true', '1', 'yes', '是')
        elif target_type == 'json':
            return json.loads(value)
        else:
            return value # 默认 string

    def _batch_create_entities(self, nodes: List[Dict]):
        """批量创建实体 - 复用现有的创建逻辑"""
        for node in nodes:
            try:
                self.create_object(node['type'], node['properties'])
            except Exception as e:
                logger.warning(f"[ObjectManager] 创建实体失败 {node['id']}: {e}")
                # 继续创建其他实体

    def _batch_create_relations(self, links: List[Dict]):
        """批量创建关系 - 复用现有的创建逻辑"""
        for link in links:
            try:
                self.create_link(
                    link['type'], 
                    link['source'], 
                    link['target']
                )
            except Exception as e:
                logger.warning(f"[ObjectManager] 创建关系失败 {link['source']}->{link['target']}: {e}")
                # 继续创建其他关系
