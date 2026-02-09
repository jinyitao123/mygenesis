"""
Schema Engine - 强类型本体推导引擎 (v5.0)

职责：
1. 读取 CSV，通过统计学推断字段类型（int/float/bool/enum/string/date）
2. 智能建议映射关系（属性 vs 关系）
3. 将用户确认的 Schema 合并到现有的 object_types.xml
4. 根据 Schema 和 CSV 生成 seed_data.xml

支持的数据类型：
- int: 整数
- float: 浮点数
- bool: 布尔值
- string: 字符串
- enum: 枚举值（唯一值数量 <= 10 的字符串）
- date: 日期时间
"""

import pandas as pd
import xml.etree.ElementTree as ET
from xml.dom import minidom
import logging
from typing import Dict, Any, List, Optional, Tuple
import re
from datetime import datetime
import json
import os
import requests

logger = logging.getLogger(__name__)


class SchemaEngine:
    """强类型本体推导与合并引擎"""
    
    # 数据类型定义
    DATA_TYPES = ['int', 'float', 'bool', 'string', 'enum', 'date']
    
    # LLM 配置
    LLM_API_KEY = os.getenv("LLM_API_KEY", "kimyitao")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://43.153.96.90:7860/v1beta")
    LLM_MODEL = os.getenv("LLM_MODEL", "models/gemini-2.5-flash-lite")
    
    @staticmethod
    def detect_file_encoding(file_path: str) -> str:
        """
        检测文件编码
        
        Args:
            file_path: 文件路径
            
        Returns:
            检测到的编码，如果失败则返回 'utf-8'
        """
        # 常见的中文编码优先级
        common_encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16', 'latin1', 'cp1252']
        
        # 尝试读取文件并检测
        for encoding in common_encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    # 尝试读取前几行
                    for i, line in enumerate(f):
                        if i >= 5:  # 读取5行测试
                            break
                    logger.info(f"Encoding test passed: {encoding}")
                    return encoding
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.warning(f"Error testing encoding {encoding}: {e}")
                continue
        
        logger.warning(f"Could not detect encoding for {file_path}, defaulting to utf-8")
        return 'utf-8'
    
    @staticmethod
    def infer_target_type_from_csv(csv_path: str, current_domain: str = "") -> str:
        """
        使用 LLM 从 CSV 文件推断最合适的对象类型
        
        Args:
            csv_path: CSV 文件路径
            current_domain: 当前领域名称
            
        Returns:
            推断的对象类型名称
        """
        try:
            # 检测文件编码
            detected_encoding = SchemaEngine.detect_file_encoding(csv_path)
            logger.info(f"Detected encoding for {csv_path}: {detected_encoding}")
            
            # 使用检测到的编码读取CSV
            df = pd.read_csv(csv_path, encoding=detected_encoding)
            logger.info(f"Successfully read CSV with encoding: {detected_encoding}")
                
        except Exception as e:
            logger.error(f"Failed to read CSV {csv_path}: {e}")
            return "Entity"  # 默认回退
            
        # 获取 CSV 头部和样本数据
        headers = list(df.columns)
        sample_data = {}
        for col in headers:
            sample_values = df[col].head(3).fillna('').astype(str).tolist()
            sample_data[col] = sample_values
            
        # 构建 LLM 提示
        prompt = f"""你是一个本体建模专家。请分析以下 CSV 数据，推断最适合的对象类型。

当前领域：{current_domain or "通用"}

CSV 列名：{headers}

样本数据（每列前3行）：
{json.dumps(sample_data, ensure_ascii=False, indent=2)}

请根据以下规则推断：
1. 分析列名含义和样本数据模式
2. 考虑当前领域上下文
3. 使用简洁、描述性的英文类型名称（首字母大写）
4. 如果是通用数据，使用 Entity、Object、Item 等
5. 如果是特定领域数据，使用领域相关名称

输出格式（必须是纯 JSON，不要其他文字）：
{{
    "inferred_type": "推断的类型名称",
    "confidence": 0.0-1.0之间的置信度,
    "reasoning": "简要推理过程（中文）"
}}"""
        
        try:
            inferred_type = SchemaEngine._call_llm_for_inference(prompt)
            return inferred_type
        except Exception as e:
            logger.error(f"LLM inference failed: {e}")
            # 回退到基于列名的简单推断
            return SchemaEngine._fallback_inference(headers, current_domain)
    
    @staticmethod
    def _call_llm_for_inference(prompt: str) -> str:
        """调用 LLM API 进行类型推断"""
        url = f"{SchemaEngine.LLM_BASE_URL}/{SchemaEngine.LLM_MODEL}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {SchemaEngine.LLM_API_KEY}"
        }
        data = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}]
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            content = result.get("candidates", [{}])[0].get(
                "content", {}
            ).get("parts", [{}])[0].get("text", "")
            
            # 提取 JSON
            import re
            match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
            if match:
                content = match.group(1)
            else:
                match = re.search(r'\{.*\}', content, re.DOTALL)
                if match:
                    content = match.group(0)
            
            result_json = json.loads(content)
            return result_json.get("inferred_type", "Entity")
            
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise
    
    @staticmethod
    def _fallback_inference(headers: List[str], current_domain: str) -> str:
        """回退推断逻辑"""
        header_str = "|".join(headers).lower()
        
        # 基于常见模式
        patterns = [
            (r'plate_no|driver_name|capacity_ton|fuel_level', 'Truck'),
            (r'warehouse|location|capacity|current_load', 'Warehouse'),
            (r'tracking_no|weight|volume|destination', 'Package'),
            (r'order_no|customer|total_amount|status', 'Order'),
            (r'supplier|rating|lead_time|contact', 'Supplier'),
            (r'patient|doctor|diagnosis|treatment', 'Patient'),
            (r'account|balance|transaction', 'Account'),
            (r'server|ip_address|cpu_usage|memory', 'Server'),
            (r'npc_|hp|mp|level|role|faction', 'NPC'),
            (r'sensor|reading|timestamp|location', 'Sensor'),
            (r'employee|department|salary|position', 'Employee'),
            (r'product|price|stock|category', 'Product'),
            (r'customer|email|phone|address', 'Customer'),
            (r'vehicle|make|model|year', 'Vehicle'),
            (r'building|floor|room|area', 'Building')
        ]
        
        for pattern, type_name in patterns:
            if re.search(pattern, header_str):
                return type_name
        
        # 基于领域
        if current_domain and current_domain != "empty":
            words = current_domain.split('_')
            domain_type = ''.join(word.capitalize() for word in words)
            return domain_type
        
        return "Entity"
    
    @staticmethod
    def infer_schema_proposal(csv_path: str, target_type_name: str) -> Dict[str, Any]:
        """
        阶段 1: 提议 (Proposal)
        分析 CSV，返回一个 JSON 格式的 Schema 建议，供前端向导显示。
        
        Args:
            csv_path: CSV 文件路径
            target_type_name: 目标对象类型名称（如 NPC, Truck）
            
        Returns:
            包含智能建议的 Schema 提案
        """
        try:
            # 检测文件编码
            detected_encoding = SchemaEngine.detect_file_encoding(csv_path)
            logger.info(f"Detected encoding for {csv_path}: {detected_encoding}")
            
            # 使用检测到的编码读取CSV
            df = pd.read_csv(csv_path, encoding=detected_encoding)
            logger.info(f"Successfully read CSV with encoding: {detected_encoding}")
                
        except Exception as e:
            logger.error(f"Failed to read CSV {csv_path}: {e}")
            raise
        
        proposal = {
            "object_type": target_type_name,
            "properties": [],
            "suggested_links": [],
            "csv_columns": list(df.columns),
            "sample_data": {},
            "csv_path": csv_path
        }
        
        # 为每列生成样本数据（前3行）
        for col in df.columns:
            sample_values = df[col].head(3).fillna('').astype(str).tolist()
            proposal["sample_data"][col] = sample_values
        
        for idx, col in enumerate(df.columns):
            # 推断数据类型
            type_info = SchemaEngine._infer_data_type(df[col])
            
            # 启发式规则：判断是否是关系候选
            is_link_candidate = SchemaEngine._is_link_candidate(col, df[col], type_info['type'])
            
            # 建议目标键名（标准化）
            target_key = SchemaEngine._suggest_target_key(col)
            
            # 建议映射类型
            mapping_type = SchemaEngine._suggest_mapping_type(col, is_link_candidate, type_info['type'])
            
            # 如果是关系候选，建议关系类型和目标类型
            link_suggestion = None
            if is_link_candidate:
                link_suggestion = SchemaEngine._suggest_link_config(col, df[col])
            
            prop_def = {
                "index": idx,
                "name": col,                 # CSV 列名
                "target_key": target_key,    # 建议的本体属性名
                "type": type_info['type'],   # 推断的数据类型
                "type_confidence": type_info.get('confidence', 1.0),
                "is_link_candidate": is_link_candidate,
                "mapping_type": mapping_type,  # 'property', 'link', 或 'ignore'
                "link_suggestion": link_suggestion,
                "description": f"从 CSV 列 '{col}' 导入",
                "unique_values": int(df[col].nunique()) if type_info['type'] in ['string', 'enum'] else None,
                "null_count": int(df[col].isna().sum()),
                "min_value": type_info.get('min'),
                "max_value": type_info.get('max'),
                "default_value": type_info.get('default')
            }
            proposal["properties"].append(prop_def)
            
            # 如果是关系候选，添加到建议关系列表
            if is_link_candidate and link_suggestion:
                proposal["suggested_links"].append({
                    "source_column": col,
                    "link_type": link_suggestion["link_type"],
                    "target_type": link_suggestion["target_type"],
                    "description": f"从 {col} 到 {link_suggestion['target_type']} 的关系"
                })
        
        logger.info(f"Generated schema proposal for {target_type_name} with {len(proposal['properties'])} properties")
        return proposal
    
    @staticmethod
    def _infer_data_type(series: pd.Series) -> Dict[str, Any]:
        """
        推断列的数据类型和约束
        
        Returns:
            {
                'type': 'int'|'float'|'bool'|'string'|'enum'|'date',
                'confidence': float,
                'min': Any,
                'max': Any,
                'default': Any,
                'nullable': bool
            }
        """
        # 去除空值
        non_null = series.dropna()
        if len(non_null) == 0:
            return {'type': 'string', 'confidence': 0.0, 'nullable': True}
        
        # 1. 尝试布尔值
        bool_values = ['true', 'false', 'yes', 'no', '1', '0', '是', '否', '真', '假']
        if non_null.astype(str).str.lower().isin(bool_values).all():
            return {
                'type': 'bool',
                'confidence': 1.0,
                'default': False,
                'nullable': series.isna().any()
            }
        
        # 2. 尝试整数
        try:
            int_series = pd.to_numeric(non_null, errors='coerce')
            if int_series.notna().all() and (int_series == int_series.astype(int)).all():
                return {
                    'type': 'int',
                    'confidence': 1.0,
                    'min': int(int_series.min()),
                    'max': int(int_series.max()),
                    'default': int(int_series.mode().iloc[0]) if not int_series.mode().empty else 0,
                    'nullable': series.isna().any()
                }
        except:
            pass
        
        # 3. 尝试浮点数
        try:
            float_series = pd.to_numeric(non_null, errors='coerce')
            if float_series.notna().all():
                return {
                    'type': 'float',
                    'confidence': 1.0,
                    'min': float(float_series.min()),
                    'max': float(float_series.max()),
                    'default': float(float_series.mode().iloc[0]) if not float_series.mode().empty else 0.0,
                    'nullable': series.isna().any()
                }
        except:
            pass
        
        # 4. 尝试日期
        try:
            # 尝试常见日期格式
            date_formats = ['%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y', '%m/%d/%Y', 
                          '%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S']
            
            for date_format in date_formats:
                try:
                    date_series = pd.to_datetime(non_null, format=date_format, errors='coerce')
                    if date_series.notna().all():
                        return {
                            'type': 'date',
                            'confidence': 1.0,
                            'format': date_format,
                            'nullable': series.isna().any()
                        }
                except:
                    continue
            
            # 如果指定格式失败，尝试自动推断（会有警告）
            date_series = pd.to_datetime(non_null, errors='coerce')
            if date_series.notna().all():
                return {
                    'type': 'date',
                    'confidence': 0.8,
                    'nullable': series.isna().any()
                }
        except:
            pass
        
        # 5. 尝试枚举（唯一值数量 <= 10）
        unique_count = non_null.nunique()
        if unique_count <= 10 and unique_count > 0:
            options = sorted(non_null.unique().tolist())
            return {
                'type': 'enum',
                'confidence': 0.9,
                'options': options,
                'default': options[0],
                'nullable': series.isna().any()
            }
        
        # 6. 默认字符串
        return {
            'type': 'string',
            'confidence': 1.0,
            'max_length': int(non_null.astype(str).str.len().max()),
            'nullable': series.isna().any()
        }
    
    @staticmethod
    def _is_link_candidate(column_name: str, series: pd.Series, dtype: str) -> bool:
        """判断列是否是关系候选"""
        column_lower = column_name.lower()
        
        # 基于列名的启发式规则
        link_keywords = [
            'id', 'ref', 'parent', 'owner', 'belongs_to', 'part_of', 'member_of',
            'dept', 'department', 'faction', 'location', 'boss', 'manager',
            'team', 'group', 'category', 'type', 'class', 'role', 'warehouse',
            'target', 'source', 'parent_id', 'ref_id', 'category_id'
        ]
        
        # 检查列名是否包含关系关键词
        if any(keyword in column_lower for keyword in link_keywords):
            return True
        
        # 检查值是否看起来像 ID 或引用
        if dtype == 'string':
            sample_values = series.dropna().head(10).astype(str)
            # ID 格式：前缀_编号
            if sample_values.str.match(r'^[A-Za-z]+_[A-Za-z0-9]+$').any():
                return True
            # UUID 格式
            if sample_values.str.match(r'^[0-9a-f]{8}-[0-9a-f]{4}').any():
                return True
        
        return False
    
    @staticmethod
    def _suggest_target_key(column_name: str) -> str:
        """建议标准化的目标键名"""
        # 转换为小写，替换空格为下划线
        key = column_name.lower().strip()
        key = re.sub(r'\s+', '_', key)
        key = re.sub(r'[^a-z0-9_]', '', key)
        
        # 常见缩写扩展
        abbreviations = {
            'dept': 'department',
            'loc': 'location',
            'desc': 'description',
            'addr': 'address',
            'tel': 'telephone',
            'mgr': 'manager',
            'emp': 'employee',
            'cust': 'customer',
            'qty': 'quantity',
            'amt': 'amount',
            'num': 'number',
            'cap': 'capacity'
        }
        
        for abbr, full in abbreviations.items():
            if key == abbr:
                key = full
            elif key.startswith(abbr + '_'):
                key = key.replace(abbr + '_', full + '_')
        
        return key
    
    @staticmethod
    def _suggest_mapping_type(column_name: str, is_link_candidate: bool, dtype: str) -> str:
        """建议映射类型"""
        column_lower = column_name.lower()
        
        # 明确忽略的列
        ignore_keywords = ['index', 'row', 'seq', 'no', 'timestamp', 'created_at', 'updated_at']
        if any(keyword in column_lower for keyword in ignore_keywords):
            return "ignore"
        
        # 如果是关系候选，建议作为关系
        if is_link_candidate:
            return "link"
        
        # 默认作为属性
        return "property"
    
    @staticmethod
    def _suggest_link_config(column_name: str, series: pd.Series) -> Optional[Dict[str, str]]:
        """为关系列建议配置"""
        column_lower = column_name.lower()
        
        # 基于列名的关系类型推断
        if 'dept' in column_lower or 'department' in column_lower:
            return {"link_type": "BELONGS_TO", "target_type": "Department"}
        elif 'faction' in column_lower:
            return {"link_type": "BELONGS_TO", "target_type": "Faction"}
        elif 'warehouse' in column_lower or 'wh_' in column_lower:
            return {"link_type": "DOCKED_AT", "target_type": "Warehouse"}
        elif 'location' in column_lower or 'loc' in column_lower:
            return {"link_type": "LOCATED_AT", "target_type": "Location"}
        elif 'parent' in column_lower or 'boss' in column_lower or 'manager' in column_lower:
            return {"link_type": "REPORTS_TO", "target_type": "Employee"}
        elif 'team' in column_lower or 'group' in column_lower:
            return {"link_type": "MEMBER_OF", "target_type": "Team"}
        elif 'category' in column_lower or 'type' in column_lower or 'class' in column_lower:
            return {"link_type": "CATEGORIZED_AS", "target_type": "Category"}
        elif 'target' in column_lower:
            return {"link_type": "TARGETS", "target_type": "Entity"}
        elif 'owner' in column_lower:
            return {"link_type": "OWNED_BY", "target_type": "User"}
        
        # 默认关系
        return {"link_type": "RELATED_TO", "target_type": "Entity"}
    
    @staticmethod
    def merge_schema_to_xml(existing_xml_content: str, new_schema_config: Dict[str, Any]) -> str:
        """
        阶段 3: 提交 (Commit) - Schema 部分
        将用户确认后的 Schema 配置合并到 object_types.xml
        
        Args:
            existing_xml_content: 现有 object_types.xml 内容
            new_schema_config: 用户确认的 Schema 配置
            
        Returns:
            合并后的 XML 字符串
        """
        target_type = new_schema_config['object_type']
        
        try:
            # 尝试解析现有 XML
            if existing_xml_content.strip():
                root = ET.fromstring(existing_xml_content)
            else:
                # 创建新的 XML 结构
                root = ET.Element("ObjectTypes")
                root.set("domain", "unknown")
        except ET.ParseError:
            # 解析失败，创建新的
            root = ET.Element("ObjectTypes")
            root.set("domain", "unknown")
        
        # 查找或创建 ObjectType
        object_type = None
        for ot in root.findall(".//ObjectType"):
            if ot.get("name") == target_type:
                object_type = ot
                break
        
        if object_type is None:
            # 创建新的 ObjectType
            object_type = ET.SubElement(root, "ObjectType")
            object_type.set("name", target_type)
            object_type.set("color", "#3b82f6")
            object_type.set("icon", "cube")
            object_type.set("primary_key", "id")
        
        # 添加/更新 Property
        properties = new_schema_config.get('properties', [])
        for prop_config in properties:
            if prop_config.get('mapping_type') != 'property':
                continue
            
            # 查找现有属性
            existing_prop = None
            for prop in object_type.findall("Property"):
                if prop.get("name") == prop_config['target_key']:
                    existing_prop = prop
                    break
            
            if existing_prop is None:
                # 创建新属性
                prop_elem = ET.SubElement(object_type, "Property")
                prop_elem.set("name", prop_config['target_key'])
                prop_elem.set("type", prop_config['type'])
                
                if prop_config.get('min_value') is not None:
                    prop_elem.set("min", str(prop_config['min_value']))
                if prop_config.get('max_value') is not None:
                    prop_elem.set("max", str(prop_config['max_value']))
                if prop_config.get('default_value') is not None:
                    prop_elem.set("default", str(prop_config['default_value']))
                
                prop_elem.set("description", prop_config.get('description', ''))
        
        # 添加 LinkType（如果需要）
        links = new_schema_config.get('links', [])
        link_types_elem = root.find("LinkTypes")
        if link_types_elem is None:
            link_types_elem = ET.SubElement(root, "LinkTypes")
        
        for link_config in links:
            existing_link = None
            for link in link_types_elem.findall("LinkType"):
                if (link.get("name") == link_config['link_type'] and
                    link.get("source") == target_type):
                    existing_link = link
                    break
            
            if existing_link is None:
                link_elem = ET.SubElement(link_types_elem, "LinkType")
                link_elem.set("name", link_config['link_type'])
                link_elem.set("source", target_type)
                link_elem.set("target", link_config['target_type'])
                link_elem.set("color", "#64748b")
        
        # 格式化输出
        xml_str = ET.tostring(root, encoding='unicode')
        # 使用 minidom 美化
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="    ")
        # 去除空行
        lines = [line for line in pretty_xml.split('\n') if line.strip()]
        return '\n'.join(lines)
    
    @staticmethod
    def generate_seed_xml(csv_path: str, schema_config: Dict[str, Any], existing_seed_xml: Optional[str] = None) -> str:
        """
        阶段 3: 提交 (Commit) - Data 部分
        根据 CSV 和 Schema 配置生成 seed_data.xml
        
        Args:
            csv_path: CSV 文件路径
            schema_config: Schema 配置（包含属性映射和关系映射）
            existing_seed_xml: 现有的 seed_data.xml 内容（可选，用于增量更新）
            
        Returns:
            生成的 XML 字符串
        """
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            logger.error(f"Failed to read CSV {csv_path}: {e}")
            raise
        
        target_type = schema_config['object_type']
        
        # 解析现有 XML（如果有）
        root: ET.Element
        nodes_elem: Optional[ET.Element]
        links_elem: Optional[ET.Element]
        
        if existing_seed_xml and existing_seed_xml.strip():
            try:
                root = ET.fromstring(existing_seed_xml)
                nodes_elem = root.find("Nodes")
                links_elem = root.find("Links")
                if nodes_elem is None:
                    nodes_elem = ET.SubElement(root, "Nodes")
                if links_elem is None:
                    links_elem = ET.SubElement(root, "Links")
            except ET.ParseError:
                root = ET.Element("World")
                nodes_elem = ET.SubElement(root, "Nodes")
                links_elem = ET.SubElement(root, "Links")
        else:
            root = ET.Element("World")
            root.set("domain", schema_config.get('domain', 'unknown'))
            nodes_elem = ET.SubElement(root, "Nodes")
            links_elem = ET.SubElement(root, "Links")
        
        # 收集所有需要创建的隐式目标节点
        implicit_nodes = {}  # target_type -> {target_id -> True}
        
        # 属性映射
        property_mappings = {}
        link_mappings = []
        
        for prop in schema_config.get('properties', []):
            if prop['mapping_type'] == 'property':
                property_mappings[prop['name']] = {
                    'target_key': prop['target_key'],
                    'type': prop['type']
                }
            elif prop['mapping_type'] == 'link':
                link_mappings.append({
                    'source_column': prop['name'],
                    'link_type': prop['link_suggestion']['link_type'],
                    'target_type': prop['link_suggestion']['target_type']
                })
                implicit_nodes[prop['link_suggestion']['target_type']] = {}
        
        # 生成节点
        for i in range(len(df)):
            row = df.iloc[i]
            node_id = f"{target_type.lower()}_{i + 1}"
            
            # 查找现有节点或创建新节点
            existing_node = None
            if nodes_elem is not None:
                for node in nodes_elem.findall("Node"):
                    if node.get("type") == target_type:
                        # 检查是否已有相同主键的节点
                        props = node.findall("Property")
                        for prop in props:
                            if (prop.get("key") == schema_config.get('primary_key', 'id') and
                                prop.text == str(row.get(schema_config.get('primary_key_column', 'id'), node_id))):
                                existing_node = node
                                break
                        if existing_node:
                            break
            
            if existing_node is not None:
                node_elem = existing_node
                # 清除现有属性
                for prop in list(node_elem.findall("Property")):
                    node_elem.remove(prop)
            else:
                node_elem = ET.SubElement(nodes_elem, "Node")
                node_elem.set("id", node_id)
                node_elem.set("type", target_type)
            
            # 添加属性
            for csv_col, mapping in property_mappings.items():
                if csv_col in row:
                    value = row[csv_col]
                    if pd.isna(value):
                        continue
                    
                    prop_elem = ET.SubElement(node_elem, "Property")
                    prop_elem.set("key", mapping['target_key'])
                    prop_elem.set("type", mapping['type'])
                    prop_elem.text = str(value)
            
            # 处理关系
            for link_mapping in link_mappings:
                csv_col = link_mapping['source_column']
                if csv_col in row and not pd.isna(row[csv_col]):
                    target_id = str(row[csv_col])
                    target_type_name = link_mapping['target_type']
                    
                    # 记录隐式节点
                    implicit_nodes[target_type_name][target_id] = True
                    
                    # 创建关系
                    link_elem = ET.SubElement(links_elem, "Link")
                    link_elem.set("type", link_mapping['link_type'])
                    source_id = node_elem.get("id")
                    if source_id:
                        link_elem.set("source", source_id)
                    target_id_str = target_id.lower().replace(' ', '_')
                    link_elem.set("target", target_id_str)
        
        # 创建隐式节点
        for target_type_name, target_ids in implicit_nodes.items():
            for target_id in target_ids:
                # 检查是否已存在
                exists = False
                normalized_id = target_id.lower().replace(' ', '_')
                for node in nodes_elem.findall("Node"):
                    if node.get("id") == normalized_id:
                        exists = True
                        break
                
                if not exists:
                    implicit_node = ET.SubElement(nodes_elem, "Node")
                    implicit_node.set("id", normalized_id)
                    implicit_node.set("type", target_type_name)
                    
                    # 添加主键属性
                    prop_elem = ET.SubElement(implicit_node, "Property")
                    prop_elem.set("key", "name")
                    prop_elem.set("type", "string")
                    prop_elem.text = target_id
        
        # 格式化输出
        xml_str = ET.tostring(root, encoding='unicode')
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="    ")
        lines = [line for line in pretty_xml.split('\n') if line.strip()]
        return '\n'.join(lines)
    
    @staticmethod
    def validate_data_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证数据是否符合 Schema 定义
        
        Args:
            data: 要验证的数据字典
            schema: Schema 定义
            
        Returns:
            (是否通过, 错误列表)
        """
        errors = []
        
        for prop_name, prop_config in schema.get('properties', {}).items():
            value = data.get(prop_name)
            prop_type = prop_config.get('type', 'string')
            required = prop_config.get('required', False)
            
            # 检查必填项
            if required and (value is None or value == ''):
                errors.append(f"属性 '{prop_name}' 是必填项")
                continue
            
            if value is None or value == '':
                continue
            
            # 类型验证
            if prop_type == 'int':
                try:
                    int(value)
                except (ValueError, TypeError):
                    errors.append(f"属性 '{prop_name}' 必须是整数")
                    
            elif prop_type == 'float':
                try:
                    float(value)
                except (ValueError, TypeError):
                    errors.append(f"属性 '{prop_name}' 必须是浮点数")
                    
            elif prop_type == 'bool':
                if str(value).lower() not in ['true', 'false', '1', '0', 'yes', 'no']:
                    errors.append(f"属性 '{prop_name}' 必须是布尔值")
                    
            elif prop_type == 'enum':
                options = prop_config.get('options', [])
                if value not in options:
                    errors.append(f"属性 '{prop_name}' 的值 '{value}' 不在允许的选项中: {options}")
            
            # 范围验证
            if prop_type in ['int', 'float']:
                try:
                    num_value = float(value)
                    if 'min' in prop_config and num_value < float(prop_config['min']):
                        errors.append(f"属性 '{prop_name}' 的值 {value} 小于最小值 {prop_config['min']}")
                    if 'max' in prop_config and num_value > float(prop_config['max']):
                        errors.append(f"属性 '{prop_name}' 的值 {value} 大于最大值 {prop_config['max']}")
                except (ValueError, TypeError):
                    pass
        
        return len(errors) == 0, errors