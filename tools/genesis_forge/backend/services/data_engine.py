"""
Data Engine - 数据生成引擎

职责：
1. 基于用户定义的映射配置，严格生成实例数据
2. 处理属性映射和关系创建
3. 确保数据一致性（去重、类型转换）
4. 生成符合 Genesis Ontology 规范的 seed_data.xml

设计理念：严格遵循 Schema，智能创建隐式节点，保持数据完整性
"""

import pandas as pd
import xml.etree.ElementTree as ET
from xml.dom import minidom
import uuid
import logging
from typing import Dict, Any, List, Optional, Set, Tuple
import re

logger = logging.getLogger(__name__)


class DataEngine:
    """数据清洗与生成引擎"""
    
    @staticmethod
    def generate_seed_xml(csv_path: str, schema_config: Dict[str, Any], 
                         existing_seed_path: Optional[str] = None) -> str:
        """
        阶段 3: 提交 (Commit) - Data 部分
        基于映射配置，将 CSV 转换为 seed_data.xml 的节点和关系
        
        Args:
            csv_path: CSV 文件路径
            schema_config: 用户确认的 Schema 配置
            existing_seed_path: 现有 seed_data.xml 路径（可选）
            
        Returns:
            生成的 XML 字符串
        """
        try:
            # 导入SchemaEngine来使用编码检测
            from backend.core.schema_engine_v5 import SchemaEngine
            
            # 检测文件编码
            detected_encoding = SchemaEngine.detect_file_encoding(csv_path)
            logger.info(f"Detected encoding for {csv_path}: {detected_encoding}")
            
            # 使用检测到的编码读取CSV
            df = pd.read_csv(csv_path, encoding=detected_encoding)
            logger.info(f"Loaded CSV with {len(df)} rows, {len(df.columns)} columns, encoding: {detected_encoding}")
                
        except Exception as e:
            logger.error(f"Failed to read CSV {csv_path}: {e}")
            raise
        
        # 加载或创建 XML 结构
        root, nodes_elem, links_elem = DataEngine._load_or_create_xml(existing_seed_path)
        
        # 收集现有节点 ID（用于去重）
        existing_ids = DataEngine._collect_existing_ids(nodes_elem)
        
        # 跟踪创建的关系目标节点
        created_target_nodes: Set[str] = set()
        
        # 处理每一行数据
        for row_idx, row in df.iterrows():
            try:
                # 1. 确定实体 ID
                entity_id = DataEngine._determine_entity_id(row, schema_config, row_idx)
                
                # 跳过重复 ID
                if entity_id in existing_ids:
                    logger.debug(f"Skipping duplicate ID: {entity_id}")
                    continue
                
                # 2. 创建主节点
                node = ET.SubElement(nodes_elem, "Node")
                node.set("id", entity_id)
                node.set("type", schema_config['object_type'])
                
                # 3. 映射属性和创建关系
                DataEngine._process_row_mappings(row, node, links_elem, schema_config, 
                                               existing_ids, created_target_nodes)
                
                # 添加到现有 ID 集合
                existing_ids.add(entity_id)
                
                logger.debug(f"Created node: {entity_id} ({schema_config['object_type']})")
                
            except Exception as e:
                logger.error(f"Error processing row {row_idx}: {e}")
                continue
        
        # 格式化 XML
        xml_str = DataEngine._format_xml(root)
        logger.info(f"Generated XML with {len(nodes_elem.findall('Node'))} nodes, "
                   f"{len(links_elem.findall('Link'))} links")
        
        return xml_str
    
    @staticmethod
    def _load_or_create_xml(existing_seed_path: Optional[str]) -> Tuple[ET.Element, ET.Element, ET.Element]:
        """加载现有 XML 或创建新结构"""
        if existing_seed_path:
            try:
                tree = ET.parse(existing_seed_path)
                root = tree.getroot()
                
                # 查找或创建 Nodes 元素
                nodes_elem = root.find("Nodes")
                if nodes_elem is None:
                    nodes_elem = ET.SubElement(root, "Nodes")
                
                # 查找或创建 Links 元素
                links_elem = root.find("Links")
                if links_elem is None:
                    links_elem = ET.SubElement(root, "Links")
                
                logger.info(f"Loaded existing seed_data.xml")
                return root, nodes_elem, links_elem
                
            except (FileNotFoundError, ET.ParseError) as e:
                logger.info(f"Creating new XML structure: {e}")
        
        # 创建新的 XML 结构
        root = ET.Element("World")
        version_elem = ET.SubElement(root, "Version")
        version_elem.text = "0.1.0"
        description_elem = ET.SubElement(root, "Description")
        description_elem.text = "游戏世界种子数据 - 从 CSV 导入生成"
        
        nodes_elem = ET.SubElement(root, "Nodes")
        links_elem = ET.SubElement(root, "Links")
        
        return root, nodes_elem, links_elem
    
    @staticmethod
    def _collect_existing_ids(nodes_elem: ET.Element) -> Set[str]:
        """收集现有节点 ID"""
        existing_ids = set()
        for node in nodes_elem.findall("Node"):
            node_id = node.get("id")
            if node_id:
                existing_ids.add(node_id)
        return existing_ids
    
    @staticmethod
    def _determine_entity_id(row: pd.Series, schema_config: Dict[str, Any], 
                           row_idx: Any) -> str:
        """确定实体 ID"""
        # 首先检查是否有配置为 ID 的列
        for prop in schema_config['properties']:
            if prop.get('target_key') == 'id' and prop['name'] in row:
                id_value = row[prop['name']]
                if pd.notna(id_value):
                    return str(id_value).strip()
        
        # 检查是否有名为 'id' 的列
        if 'id' in row and pd.notna(row['id']):
            return str(row['id']).strip()
        
        # 生成唯一 ID
        prefix = schema_config['object_type'].lower()
        unique_suffix = uuid.uuid4().hex[:8]
        return f"{prefix}_{unique_suffix}_{row_idx}"
    
    @staticmethod
    def _process_row_mappings(row: pd.Series, node: ET.Element, links_elem: ET.Element,
                            schema_config: Dict[str, Any], existing_ids: Set[str],
                            created_target_nodes: Set[str]) -> None:
        """处理行的所有映射"""
        source_id = node.get("id")
        
        for prop_config in schema_config['properties']:
            csv_col = prop_config['name']
            if csv_col not in row:
                continue
            
            val = row[csv_col]
            if pd.isna(val):
                continue
            
            mapping_type = prop_config.get('mapping_type', 'property')
            
            if mapping_type == 'property':
                DataEngine._add_property(node, prop_config, val)
                
            elif mapping_type == 'link':
                DataEngine._create_link(row, prop_config, source_id, links_elem,
                                      existing_ids, created_target_nodes)
    
    @staticmethod
    def _add_property(node: ET.Element, prop_config: Dict[str, Any], value: Any) -> None:
        """添加属性到节点"""
        target_key = prop_config.get('target_key')
        if not target_key:
            return
        
        # 类型转换
        converted_value = DataEngine._convert_value(value, prop_config.get('type', 'string'))
        
        # 创建 Property 元素
        p = ET.SubElement(node, "Property")
        p.set("key", target_key)
        p.set("type", prop_config.get('type', 'string'))
        
        # 设置值
        if prop_config.get('type') == 'bool':
            p.text = str(converted_value).lower()
        else:
            p.text = str(converted_value)
    
    @staticmethod
    def _convert_value(value: Any, target_type: str) -> Any:
        """转换值为目标类型"""
        str_value = str(value).strip()
        
        if target_type == 'int':
            try:
                return int(float(str_value)) if str_value else 0
            except (ValueError, TypeError):
                return 0
        elif target_type == 'float':
            try:
                return float(str_value) if str_value else 0.0
            except (ValueError, TypeError):
                return 0.0
        elif target_type == 'bool':
            if isinstance(value, bool):
                return value
            str_lower = str_value.lower()
            return str_lower in ('true', 'yes', '1', '是', '真')
        else:  # string
            return str_value
    
    @staticmethod
    def _create_link(row: pd.Series, prop_config: Dict[str, Any], source_id: Optional[str],
                    links_elem: ET.Element, existing_ids: Set[str],
                    created_target_nodes: Set[str]) -> None:
        """创建关系"""
        csv_col = prop_config['name']
        if csv_col not in row:
            return
        
        val = row[csv_col]
        if pd.isna(val):
            return
        
        link_type = prop_config.get('link_type', 'RELATED_TO')
        target_type = prop_config.get('link_target_type', 'Entity')
        
        # 生成目标节点 ID
        target_id = DataEngine._generate_target_id(val, target_type)
        
        # 确保目标节点存在
        if target_id not in existing_ids and target_id not in created_target_nodes:
            DataEngine._create_target_node(links_elem, target_id, target_type, val, existing_ids)
            created_target_nodes.add(target_id)
        
        # 创建关系
        if source_id is None:
            logger.warning(f"Cannot create link: source_id is None for target {target_id}")
            return
            
        link = ET.SubElement(links_elem, "Link")
        link.set("type", link_type)
        link.set("source", source_id)
        link.set("target", target_id)
        
        logger.debug(f"Created link: {source_id} --[{link_type}]--> {target_id}")
    
    @staticmethod
    def _generate_target_id(value: Any, target_type: str) -> str:
        """生成目标节点 ID"""
        # 清理值并生成 ID
        clean_value = str(value).strip().lower()
        clean_value = re.sub(r'[^a-z0-9]', '_', clean_value)
        clean_value = re.sub(r'_+', '_', clean_value).strip('_')
        
        # 如果值为空，使用默认
        if not clean_value:
            clean_value = "unknown"
        
        # 生成 ID
        prefix = target_type.lower()
        return f"{prefix}_{clean_value}"
    
    @staticmethod
    def _create_target_node(parent_elem: ET.Element, target_id: str, 
                          target_type: str, value: Any, existing_ids: Set[str]) -> None:
        """创建目标节点"""
        # 找到 Nodes 元素（可能是父元素的父元素）
        nodes_elem = parent_elem
        while nodes_elem is not None and nodes_elem.tag != "Nodes":
            nodes_elem = nodes_elem.find('..')  # 使用find查找父元素
        
        if nodes_elem is None:
            logger.warning(f"Cannot find Nodes element for target node {target_id}")
            return
        
        # 创建目标节点
        target_node = ET.SubElement(nodes_elem, "Node")
        target_node.set("id", target_id)
        target_node.set("type", target_type)
        
        # 添加名称属性
        name_prop = ET.SubElement(target_node, "Property")
        name_prop.set("key", "name")
        name_prop.set("type", "string")
        name_prop.text = str(value).strip()
        
        # 添加到现有 ID 集合
        existing_ids.add(target_id)
        
        logger.debug(f"Created target node: {target_id} ({target_type})")
    
    @staticmethod
    def _format_xml(root: ET.Element) -> str:
        """格式化 XML 输出"""
        # 转换为字符串
        xml_str = ET.tostring(root, encoding='unicode', method='xml')
        
        # 使用 minidom 美化
        try:
            parsed = minidom.parseString(xml_str)
            pretty_xml = parsed.toprettyxml(indent="    ")
            
            # 清理 minidom 添加的额外空行
            lines = []
            for line in pretty_xml.split('\n'):
                if line.strip():
                    lines.append(line)
            
            return '\n'.join(lines)
        except Exception as e:
            logger.warning(f"Failed to prettify XML: {e}")
            return xml_str
    
    @staticmethod
    def validate_data_generation(df: pd.DataFrame, schema_config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证数据生成配置
        
        Args:
            df: 数据框
            schema_config: Schema 配置
            
        Returns:
            (是否有效, 警告消息列表)
        """
        warnings = []
        
        # 检查必需列是否存在
        for prop in schema_config['properties']:
            if prop['name'] not in df.columns:
                warnings.append(f"列 '{prop['name']}' 在 CSV 中不存在")
        
        # 检查 ID 列唯一性
        id_columns = []
        for prop in schema_config['properties']:
            if prop.get('target_key') == 'id':
                id_columns.append(prop['name'])
        
        for id_col in id_columns:
            if id_col in df.columns:
                unique_count = df[id_col].nunique()
                total_count = len(df)
                if unique_count < total_count:
                    warnings.append(f"ID 列 '{id_col}' 有重复值: {unique_count}/{total_count} 唯一")
        
        # 检查关系目标值的唯一性
        for prop in schema_config['properties']:
            if prop.get('mapping_type') == 'link' and prop['name'] in df.columns:
                unique_targets = df[prop['name']].nunique()
                warnings.append(f"关系列 '{prop['name']}' 将创建 {unique_targets} 个不同的目标节点")
        
        return len(warnings) == 0, warnings
    
    @staticmethod
    def generate_sample_xml(schema_config: Dict[str, Any]) -> str:
        """
        生成示例 XML（用于预览）
        
        Args:
            schema_config: Schema 配置
            
        Returns:
            示例 XML 字符串
        """
        root = ET.Element("World")
        version_elem = ET.SubElement(root, "Version")
        version_elem.text = "0.1.0"
        description_elem = ET.SubElement(root, "Description")
        description_elem.text = f"示例数据 - {schema_config['object_type']}"
        
        nodes_elem = ET.SubElement(root, "Nodes")
        links_elem = ET.SubElement(root, "Links")
        
        # 创建示例节点
        for i in range(3):
            node_id = f"{schema_config['object_type'].lower()}_example_{i+1}"
            node = ET.SubElement(nodes_elem, "Node")
            node.set("id", node_id)
            node.set("type", schema_config['object_type'])
            
            # 添加示例属性
            for prop in schema_config['properties']:
                if prop.get('mapping_type') == 'property':
                    p = ET.SubElement(node, "Property")
                    p.set("key", prop.get('target_key', prop['name']))
                    p.set("type", prop.get('type', 'string'))
                    
                    # 示例值
                    if prop.get('type') == 'int':
                        p.text = str((i + 1) * 10)
                    elif prop.get('type') == 'bool':
                        p.text = "true" if i % 2 == 0 else "false"
                    else:
                        p.text = f"示例值 {i+1}"
        
        # 创建示例关系
        for prop in schema_config['properties']:
            if prop.get('mapping_type') == 'link':
                for i in range(2):
                    link = ET.SubElement(links_elem, "Link")
                    link.set("type", prop.get('link_type', 'RELATED_TO'))
                    link.set("source", f"{schema_config['object_type'].lower()}_example_{i+1}")
                    link.set("target", f"{prop.get('link_target_type', 'Entity').lower()}_example")
        
        return DataEngine._format_xml(root)