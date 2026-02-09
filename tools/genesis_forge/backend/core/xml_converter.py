"""
健壮的XML转换工具 - 将JSON本体数据转换为标准XML格式

支持：
1. 将OntologyModel转换为object_types.xml
2. 将种子数据转换为seed_data.xml
3. 完整的XML验证和错误处理
4. 支持复杂的数据类型转换
"""

import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict, List, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)


class XMLConverter:
    """XML转换器 - 将JSON本体数据转换为标准XML格式"""
    
    @staticmethod
    def convert_ontology_to_xml(ontology: Dict[str, Any], domain: str) -> str:
        """
        将本体数据转换为object_types.xml格式
        
        Args:
            ontology: 本体数据字典
            domain: 领域名称
            
        Returns:
            XML字符串
        """
        try:
            # 创建根元素
            root = ET.Element("ObjectTypes")
            root.set("domain", domain)
            
            # 添加对象类型
            object_types = ontology.get("objectTypes", {}) or ontology.get("object_types", {})
            if isinstance(object_types, list):
                # 如果是列表，转换为字典
                object_types_dict = {}
                for obj in object_types:
                    if isinstance(obj, dict):
                        name = obj.get("name") or obj.get("type_key")
                        if name:
                            object_types_dict[name] = obj
                object_types = object_types_dict
            
            for obj_name, obj_def in object_types.items():
                if not isinstance(obj_def, dict):
                    continue
                    
                obj_elem = ET.SubElement(root, "ObjectType")
                obj_elem.set("name", str(obj_name))
                
                # 设置可选属性
                if obj_def.get("color"):
                    obj_elem.set("color", str(obj_def["color"]))
                if obj_def.get("icon"):
                    obj_elem.set("icon", str(obj_def["icon"]))
                if obj_def.get("primary_key"):
                    obj_elem.set("primary_key", str(obj_def["primary_key"]))
                
                # 添加属性定义
                properties = obj_def.get("properties", {})
                if isinstance(properties, dict):
                    for prop_name, prop_def in properties.items():
                        prop_elem = ET.SubElement(obj_elem, "Property")
                        prop_elem.set("name", str(prop_name))
                        
                        if isinstance(prop_def, dict):
                            prop_elem.set("type", str(prop_def.get("type", "string")))
                            if prop_def.get("description"):
                                prop_elem.set("description", str(prop_def["description"]))
                        else:
                            prop_elem.set("type", "string")
            
            # 添加关系类型
            link_types_elem = ET.SubElement(root, "LinkTypes")
            
            relationships = ontology.get("relationships", {})
            if isinstance(relationships, list):
                # 如果是列表，转换为字典
                relationships_dict = {}
                for rel in relationships:
                    if isinstance(rel, dict):
                        name = rel.get("name") or rel.get("type")
                        if name:
                            relationships_dict[name] = rel
                relationships = relationships_dict
            
            for rel_name, rel_def in relationships.items():
                if not isinstance(rel_def, dict):
                    continue
                    
                link_elem = ET.SubElement(link_types_elem, "LinkType")
                link_elem.set("name", str(rel_name))
                link_elem.set("source", str(rel_def.get("sourceType", "Unknown")))
                link_elem.set("target", str(rel_def.get("targetType", "Unknown")))
                
                if rel_def.get("color"):
                    link_elem.set("color", str(rel_def["color"]))
            
            # 美化XML输出
            xml_str = XMLConverter._prettify_xml(root)
            return xml_str
            
        except Exception as e:
            logger.error(f"转换本体到XML失败: {e}")
            # 返回一个基本的XML结构
            return f'''<?xml version="1.0" ?>
<ObjectTypes domain="{domain}">
    <ObjectType name="Entity" color="#3b82f6" icon="cube" primary_key="id">
        <Property name="label" type="string" description="节点标签"/>
        <Property name="type" type="string" description="节点类型"/>
    </ObjectType>
    <LinkTypes>
        <LinkType name="RELATES_TO" source="Entity" target="Entity" color="#64748b"/>
    </LinkTypes>
</ObjectTypes>'''
    
    @staticmethod
    def convert_seed_data_to_xml(seed_data: Dict[str, Any], domain: str) -> str:
        """
        将种子数据转换为seed_data.xml格式
        
        Args:
            seed_data: 种子数据字典
            domain: 领域名称
            
        Returns:
            XML字符串
        """
        try:
            # 创建根元素
            root = ET.Element("World")
            root.set("domain", domain)
            
            # 添加节点
            nodes_elem = ET.SubElement(root, "Nodes")
            
            # 处理实体数据
            entities = seed_data.get("entities", [])
            if not isinstance(entities, list):
                entities = []
            
            for entity in entities:
                if not isinstance(entity, dict):
                    continue
                    
                node_elem = ET.SubElement(nodes_elem, "Node")
                
                # 设置节点ID和类型
                node_id = entity.get("id") or f"entity_{len(nodes_elem)}"
                node_type = entity.get("type", "Unknown")
                node_elem.set("id", str(node_id))
                node_elem.set("type", str(node_type))
                
                # 添加属性
                properties = entity.get("properties", {})
                if isinstance(properties, dict):
                    for prop_key, prop_value in properties.items():
                        if prop_value is None:
                            continue
                            
                        prop_elem = ET.SubElement(node_elem, "Property")
                        prop_elem.set("key", str(prop_key))
                        
                        # 推断属性类型
                        prop_type = XMLConverter._infer_type(prop_value)
                        prop_elem.set("type", prop_type)
                        
                        # 设置属性值
                        if prop_type == "string":
                            prop_elem.text = str(prop_value)
                        elif prop_type in ["int", "float", "bool"]:
                            prop_elem.text = str(prop_value)
                        else:
                            # 复杂类型转换为JSON字符串
                            prop_elem.text = json.dumps(prop_value, ensure_ascii=False)
            
            # 添加关系
            links_elem = ET.SubElement(root, "Links")
            
            # 处理关系数据
            relations = seed_data.get("relations", [])
            if not isinstance(relations, list):
                relations = []
            
            for relation in relations:
                if not isinstance(relation, dict):
                    continue
                    
                source = relation.get("source")
                target = relation.get("target")
                rel_type = relation.get("type", "RELATES_TO")
                
                if source and target:
                    link_elem = ET.SubElement(links_elem, "Link")
                    link_elem.set("type", str(rel_type))
                    link_elem.set("source", str(source))
                    link_elem.set("target", str(target))
            
            # 美化XML输出
            xml_str = XMLConverter._prettify_xml(root)
            return xml_str
            
        except Exception as e:
            logger.error(f"转换种子数据到XML失败: {e}")
            # 返回一个基本的XML结构
            return f'''<?xml version="1.0" ?>
<World domain="{domain}">
    <Nodes>
        <Node id="entity_1" type="Entity">
            <Property key="label" type="string">示例实体</Property>
            <Property key="type" type="string">Entity</Property>
        </Node>
    </Nodes>
    <Links>
        <Link type="RELATES_TO" source="entity_1" target="entity_1"/>
    </Links>
</World>'''
    
    @staticmethod
    def _infer_type(value: Any) -> str:
        """推断值的类型"""
        if isinstance(value, bool):
            return "bool"
        elif isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, (list, dict)):
            return "json"
        else:
            return "string"
    
    @staticmethod
    def _prettify_xml(elem: ET.Element) -> str:
        """美化XML输出"""
        try:
            rough_string = ET.tostring(elem, encoding='unicode')
            reparsed = minidom.parseString(rough_string)
            return reparsed.toprettyxml(indent="    ")
        except:
            # 如果美化失败，返回原始XML
            return ET.tostring(elem, encoding='unicode', method='xml')
    
    @staticmethod
    def validate_xml(xml_content: str) -> bool:
        """验证XML格式是否正确"""
        try:
            ET.fromstring(xml_content)
            return True
        except ET.ParseError as e:
            logger.error(f"XML验证失败: {e}")
            return False
    
    @staticmethod
    def convert_graph_data_to_seed_xml(graph_data: Dict[str, Any], domain: str) -> str:
        """
        将图谱数据转换为seed_data.xml格式
        
        Args:
            graph_data: 图谱数据
            domain: 领域名称
            
        Returns:
            XML字符串
        """
        try:
            elements = graph_data.get("elements", [])
            if not isinstance(elements, list):
                elements = []
            
            # 提取节点和边
            nodes = []
            links = []
            
            for element in elements:
                if not isinstance(element, dict):
                    continue
                    
                element_type = element.get("type")
                element_data = element.get("data", {})
                
                if element_type == "node":
                    # 处理节点
                    node_id = element_data.get("id") or f"node_{len(nodes)}"
                    node_type = element_data.get("type", "Unknown")
                    
                    node = {
                        "id": node_id,
                        "type": node_type,
                        "properties": {}
                    }
                    
                    # 复制所有属性
                    for key, value in element_data.items():
                        if key not in ["id", "type", "source", "target"]:
                            node["properties"][key] = value
                    
                    nodes.append(node)
                    
                elif element_type == "edge":
                    # 处理边
                    source = element_data.get("source")
                    target = element_data.get("target")
                    edge_type = element_data.get("type", "RELATES_TO")
                    
                    if source and target:
                        link = {
                            "type": edge_type,
                            "source": source,
                            "target": target,
                            "properties": {}
                        }
                        
                        # 复制所有属性
                        for key, value in element_data.items():
                            if key not in ["source", "target", "type"]:
                                link["properties"][key] = value
                        
                        links.append(link)
            
            # 构建种子数据
            seed_data = {
                "entities": nodes,
                "relations": links
            }
            
            # 转换为XML
            return XMLConverter.convert_seed_data_to_xml(seed_data, domain)
            
        except Exception as e:
            logger.error(f"转换图谱数据到XML失败: {e}")
            return XMLConverter.convert_seed_data_to_xml({"entities": [], "relations": []}, domain)