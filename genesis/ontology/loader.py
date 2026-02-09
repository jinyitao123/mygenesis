"""
Ontology Loader - 本体加载器

职责：
- 从 JSON 文件加载 Ontology 定义
- 提供 Object Types, Action Types, Seed Data 的访问接口
- 验证 Ontology 数据的完整性和有效性
"""

import json
import xml.etree.ElementTree as ET
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)


class OntologyLoader:
    """本体加载器 - 加载和管理 Ontology 定义"""

    def __init__(self, ontology_dir: str = "ontology"):
        """
        初始化本体加载器

        Args:
            ontology_dir: Ontology JSON 文件所在目录
        """
        self.ontology_dir = Path(ontology_dir)
        self.object_types = {}
        self.link_types = {}
        self.action_types = {}
        self.seed_data = {}
        self.synapser_patterns = {}
        self.synonyms = {}

    def load_all(self, use_xml: bool = False) -> Dict[str, bool]:
        """
        加载所有 Ontology 文件

        Args:
            use_xml: 是否使用 XML 格式加载种子数据

        Returns:
            加载结果字典 {"文件名": bool}
        """
        results = {}

        # 加载对象类型
        results["object_types.json"] = self._load_object_types()

        # 加载动作类型
        results["action_types.json"] = self._load_action_types()

        # 加载种子数据（支持 JSON 或 XML）
        if use_xml:
            results["seed_data.xml"] = self._load_seed_data_xml()
        else:
            results["seed_data.json"] = self._load_seed_data()

        # 加载意图映射
        results["synapser_patterns.json"] = self._load_synapser_patterns()

        success_count = sum(1 for v in results.values() if v)
        total_count = len(results)

        logger.info(f"[OntologyLoader] Loaded {success_count}/{total_count} ontology files (XML mode: {use_xml})")

        return results

    def _load_json_file(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        读取 JSON 文件

        Args:
            filename: 文件名

        Returns:
            解析后的 JSON 数据，失败则返回 None
        """
        file_path = self.ontology_dir / filename

        if not file_path.exists():
            logger.error(f"[OntologyLoader] File not found: {file_path}")
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.debug(f"[OntologyLoader] Loaded {filename}")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"[OntologyLoader] JSON decode error in {filename}: {e}")
            return None
        except Exception as e:
            logger.error(f"[OntologyLoader] Error loading {filename}: {e}")
            return None

    def _load_xml_file(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        读取 XML 文件并转换为 JSON 格式

        Args:
            filename: 文件名

        Returns:
            转换后的 JSON 数据，失败则返回 None
        """
        file_path = self.ontology_dir / filename

        if not file_path.exists():
            logger.error(f"[OntologyLoader] File not found: {file_path}")
            return None

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # 转换 XML 为 JSON 格式
            data = self._convert_xml_to_json(root)
            logger.debug(f"[OntologyLoader] Loaded XML {filename}")
            return data
        except ET.ParseError as e:
            logger.error(f"[OntologyLoader] XML parse error in {filename}: {e}")
            return None
        except Exception as e:
            logger.error(f"[OntologyLoader] Error loading XML {filename}: {e}")
            return None

    def _convert_xml_to_json(self, root: ET.Element) -> Dict[str, Any]:
        """
        将 XML 世界数据转换为 JSON 格式

        Args:
            root: XML 根元素

        Returns:
            JSON 格式的世界数据
        """
        seed_nodes = []
        seed_links = []
        
        # 解析节点
        for node_elem in root.findall('./Nodes/Node'):
            node_id = node_elem.get('id')
            node_type = node_elem.get('type')
            
            if node_id is None or node_type is None:
                continue
                
            properties: Dict[str, Any] = {"id": node_id}
            
            # 解析属性
            for prop in node_elem.findall('Property'):
                key = prop.get('key')
                value = prop.text
                value_type = prop.get('type', 'string')
                
                if key is not None and value is not None:
                    # 类型转换
                    typed_value = self._cast_xml_value(value, value_type)
                    properties[key] = typed_value
            
            seed_nodes.append({
                "id": node_id,
                "type": node_type,
                "properties": properties
            })
        
        # 解析关系
        for link_elem in root.findall('./Links/Link'):
            link_type = link_elem.get('type')
            source = link_elem.get('source')
            target = link_elem.get('target')
            
            if link_type and source and target:
                seed_links.append({
                    "type": link_type,
                    "source": source,
                    "target": target
                })
        
        return {
            "seed_nodes": seed_nodes,
            "seed_links": seed_links
        }

    def _cast_xml_value(self, value: str, target_type: str) -> Any:
        """
        XML 值类型转换器

        Args:
            value: 原始字符串值
            target_type: 目标类型

        Returns:
            转换后的值
        """
        value = value.strip()
        
        if target_type == 'int':
            return int(value)
        elif target_type == 'float':
            return float(value)
        elif target_type == 'bool':
            return value.lower() in ('true', '1', 'yes', '是')
        else:
            return value  # 默认 string

    def _load_object_types(self) -> bool:
        """
        加载对象类型定义（支持 XML 和 JSON）

        Returns:
            是否加载成功
        """
        # 首先尝试加载 XML
        xml_data = self._load_object_types_xml()
        if xml_data:
            self.object_types = xml_data.get('object_types', {})
            self.link_types = xml_data.get('link_types', {})
            logger.info(f"[OntologyLoader] Loaded object types from XML: {len(self.object_types)} object types, {len(self.link_types)} link types")
            return True
        
        # XML 加载失败，回退到 JSON
        data = self._load_json_file("object_types.json")
        if not data:
            return False

        # Reason: 提取 object_types 和 link_types
        self.object_types = data.get('object_types', {})
        self.link_types = data.get('link_types', {})

        # Reason: 验证完整性
        if not self.object_types:
            logger.warning("[OntologyLoader] No object_types found")
            return False

        logger.info(f"[OntologyLoader] Loaded {len(self.object_types)} object types, {len(self.link_types)} link types from JSON")
        return True
    
    def _load_object_types_xml(self) -> Optional[Dict[str, Any]]:
        """
        从 XML 加载对象类型定义
        
        Returns:
            解析后的数据，失败则返回 None
        """
        file_path = self.ontology_dir / "object_types.xml"
        
        if not file_path.exists():
            logger.debug("[OntologyLoader] object_types.xml not found, will use JSON")
            return None
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            data = self._parse_object_types_xml(root)
            logger.debug("[OntologyLoader] Loaded object_types.xml")
            return data
        except ET.ParseError as e:
            logger.error(f"[OntologyLoader] XML parse error in object_types.xml: {e}")
            return None
        except Exception as e:
            logger.error(f"[OntologyLoader] Error loading object_types.xml: {e}")
            return None

    def _load_action_types(self) -> bool:
        """
        加载动作类型定义（支持 XML 和 JSON）

        Returns:
            是否加载成功
        """
        # 首先尝试加载 XML
        xml_data = self._load_action_types_xml()
        if xml_data:
            self.action_types = xml_data.get('action_types', {})
            logger.info(f"[OntologyLoader] Loaded action types from XML: {len(self.action_types)} action types")
            return True
        
        # XML 加载失败，回退到 JSON
        data = self._load_json_file("action_types.json")
        if not data:
            return False

        self.action_types = data.get('action_types', {})

        if not self.action_types:
            logger.warning("[OntologyLoader] No action_types found")
            return False

        logger.info(f"[OntologyLoader] Loaded {len(self.action_types)} action types from JSON")
        return True
    
    def _load_action_types_xml(self) -> Optional[Dict[str, Any]]:
        """
        从 XML 加载动作类型定义
        
        Returns:
            解析后的数据，失败则返回 None
        """
        file_path = self.ontology_dir / "action_types.xml"
        
        if not file_path.exists():
            logger.debug("[OntologyLoader] action_types.xml not found, will use JSON")
            return None
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            data = self._parse_action_types_xml(root)
            logger.debug("[OntologyLoader] Loaded action_types.xml")
            return data
        except ET.ParseError as e:
            logger.error(f"[OntologyLoader] XML parse error in action_types.xml: {e}")
            return None
        except Exception as e:
            logger.error(f"[OntologyLoader] Error loading action_types.xml: {e}")
            return None

    def _load_seed_data(self) -> bool:
        """
        加载种子数据

        Returns:
            是否加载成功
        """
        data = self._load_json_file("seed_data.json")
        if not data:
            return False

        self.seed_data = {
            "seed_nodes": data.get('seed_nodes', []),
            "seed_links": data.get('seed_links', [])
        }

        logger.info(f"[OntologyLoader] Loaded seed data: {len(self.seed_data['seed_nodes'])} nodes, {len(self.seed_data['seed_links'])} links")
        return True

    def _load_seed_data_xml(self) -> bool:
        """
        从 XML 加载种子数据

        Returns:
            是否加载成功
        """
        data = self._load_xml_file("seed_data.xml")
        if not data:
            return False

        self.seed_data = {
            "seed_nodes": data.get('seed_nodes', []),
            "seed_links": data.get('seed_links', [])
        }

        logger.info(f"[OntologyLoader] Loaded seed data from XML: {len(self.seed_data['seed_nodes'])} nodes, {len(self.seed_data['seed_links'])} links")
        return True

    def _load_synapser_patterns(self) -> bool:
        """
        加载意图映射模式（支持 XML 和 JSON）

        Returns:
            是否加载成功
        """
        # 首先尝试加载 XML
        xml_data = self._load_synapser_patterns_xml()
        if xml_data:
            self.synapser_patterns = xml_data.get('synapser_patterns', {})
            logger.info(f"[OntologyLoader] Loaded synapser patterns from XML: {len(self.synapser_patterns)} patterns, {len(self.synonyms)} synonyms")
            return True
        
        # XML 加载失败，回退到 JSON
        data = self._load_json_file("synapser_patterns.json")
        if not data:
            return False

        self.synapser_patterns = data.get('synapser_patterns', {})
        self.synonyms = data.get('synonyms', {})

        logger.info(f"[OntologyLoader] Loaded {len(self.synapser_patterns)} synapser patterns, {len(self.synonyms)} synonyms from JSON")
        return True
    
    def _load_synapser_patterns_xml(self) -> Optional[Dict[str, Any]]:
        """
        从 XML 加载意图映射模式
        
        Returns:
            解析后的数据，失败则返回 None
        """
        file_path = self.ontology_dir / "synapser_patterns.xml"
        
        if not file_path.exists():
            logger.debug("[OntologyLoader] synapser_patterns.xml not found, will use JSON")
            return None
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            data = self._parse_synapser_patterns_xml(root)
            logger.debug("[OntologyLoader] Loaded synapser_patterns.xml")
            
            # 存储同义词库到实例变量
            self.synonyms = data.get('synonyms', {})
            
            return data
        except ET.ParseError as e:
            logger.error(f"[OntologyLoader] XML parse error in synapser_patterns.xml: {e}")
            return None
        except Exception as e:
            logger.error(f"[OntologyLoader] Error loading synapser_patterns.xml: {e}")
            return None

    def get_object_types(self) -> Dict[str, Any]:
        """
        获取对象类型定义

        Returns:
            对象类型字典
        """
        return self.object_types

    def get_link_types(self) -> Dict[str, Any]:
        """
        获取关系类型定义

        Returns:
            关系类型字典
        """
        return self.link_types

    def get_action_types(self) -> Dict[str, Any]:
        """
        获取动作类型定义

        Returns:
            动作类型字典
        """
        return self.action_types

    def get_seed_data(self) -> Dict[str, List]:
        """
        获取种子数据

        Returns:
            包含 seed_nodes 和 seed_links 的字典
        """
        return self.seed_data

    def get_synapser_patterns(self) -> Dict[str, Any]:
        """获取 Synapser 模式"""
        return self.synapser_patterns
    
    def get_synonyms(self) -> Dict[str, List[str]]:
        """获取同义词库"""
        return self.synonyms

    def get_object_type_def(self, type_name: str) -> Optional[Dict[str, Any]]:
        """
        获取特定对象类型的定义

        Args:
            type_name: 对象类型名称

        Returns:
            对象类型定义，不存在则返回 None
        """
        return self.object_types.get(type_name)

    def get_action_type_def(self, action_id: str) -> Optional[Dict[str, Any]]:
        """
        获取特定动作类型的定义

        Args:
            action_id: 动作 ID

        Returns:
            动作类型定义，不存在则返回 None
        """
        return self.action_types.get(action_id)

    def validate(self) -> Dict[str, List[str]]:
        """
        验证 Ontology 数据的完整性

        Returns:
            验证结果字典 {"错误类型": [错误消息]}
        """
        errors = {}

        # 验证对象类型
        for type_name, type_def in self.object_types.items():
            if 'properties' not in type_def:
                errors.setdefault("missing_properties", []).append(
                    f"Object type {type_name} missing properties"
                )

        # 验证动作类型
        for action_id, action_def in self.action_types.items():
            if 'parameters' not in action_def:
                errors.setdefault("missing_parameters", []).append(
                    f"Action {action_id} missing parameters"
                )
            if 'validation' not in action_def:
                errors.setdefault("missing_validation", []).append(
                    f"Action {action_id} missing validation"
                )
            if 'rules' not in action_def:
                errors.setdefault("missing_rules", []).append(
                    f"Action {action_id} missing rules"
                )

        # 验证种子数据
        node_ids = {node['id'] for node in self.seed_data.get('seed_nodes', [])}
        for link in self.seed_data.get('seed_links', []):
            if link['source'] not in node_ids:
                errors.setdefault("invalid_link_source", []).append(
                    f"Link source {link['source']} not found in seed nodes"
                )
            if link['target'] not in node_ids:
                errors.setdefault("invalid_link_target", []).append(
                    f"Link target {link['target']} not found in seed nodes"
                )

        if errors:
            logger.error(f"[OntologyLoader] Validation failed: {errors}")
        else:
            logger.info("[OntologyLoader] Validation passed")

        return errors
    
    def _parse_object_types_xml(self, root: ET.Element) -> Dict[str, Any]:
        """
        解析对象类型 XML
        
        Args:
            root: XML 根元素
            
        Returns:
            包含 object_types 和 link_types 的字典
        """
        object_types = {}
        link_types = {}
        
        # 解析对象类型
        for obj_elem in root.findall('./ObjectType'):
            type_name = obj_elem.get('name')
            display_name = obj_elem.get('display_name', '')
            description = obj_elem.get('description', '')
            primary_key = obj_elem.get('primary_key', 'id')
            
            if not type_name:
                continue
            
            properties = {}
            for prop_elem in obj_elem.findall('./Property'):
                prop_name = prop_elem.get('name')
                prop_type = prop_elem.get('type', 'string')
                required = prop_elem.get('required', 'false').lower() == 'true'
                default = prop_elem.get('default')
                description = prop_elem.get('description', '')
                enum = prop_elem.get('enum')
                
                if prop_name:
                    prop_def = {
                        'type': prop_type,
                        'required': required,
                        'description': description
                    }
                    if default is not None:
                        prop_def['default'] = self._cast_xml_value(default, prop_type)
                    if enum:
                        prop_def['enum'] = [e.strip() for e in enum.split(',')]
                    
                    properties[prop_name] = prop_def
            
            object_types[type_name] = {
                'display_name': display_name,
                'description': description,
                'primary_key': primary_key,
                'properties': properties
            }
        
        # 解析关系类型
        for link_elem in root.findall('./LinkType'):
            link_name = link_elem.get('name')
            display_name = link_elem.get('display_name', '')
            description = link_elem.get('description', '')
            source = link_elem.get('source', '')
            target = link_elem.get('target', '')
            bidirectional = link_elem.get('bidirectional', 'false').lower() == 'true'
            
            if link_name:
                link_types[link_name] = {
                    'display_name': display_name,
                    'description': description,
                    'source': source,
                    'target': target,
                    'bidirectional': bidirectional
                }
        
        return {
            'object_types': object_types,
            'link_types': link_types
        }
    
    def _parse_action_types_xml(self, root: ET.Element) -> Dict[str, Any]:
        """
        解析动作类型 XML
        
        Args:
            root: XML 根元素
            
        Returns:
            包含 action_types 的字典
        """
        action_types = {}
        
        for action_elem in root.findall('./ActionType'):
            action_name = action_elem.get('name')
            display_name = action_elem.get('display_name', '')
            description = action_elem.get('description', '')
            
            if not action_name:
                continue
            
            # 解析参数
            parameters = []
            params_elem = action_elem.find('./Parameters')
            if params_elem:
                for param_elem in params_elem.findall('./Parameter'):
                    param_name = param_elem.get('name')
                    param_type = param_elem.get('type', 'string')
                    object_type = param_elem.get('object_type')
                    param_description = param_elem.get('description', '')
                    required = param_elem.get('required', 'true').lower() == 'true'
                    
                    if param_name:
                        param_def = {
                            'name': param_name,
                            'type': param_type,
                            'required': required,
                            'description': param_description
                        }
                        if object_type:
                            param_def['object_type'] = object_type
                        
                        parameters.append(param_def)
            
            # 解析验证规则
            validation = {}
            validation_elem = action_elem.find('./Validation')
            if validation_elem:
                validation = {
                    'logic_type': validation_elem.get('logic_type', ''),
                    'error_message': validation_elem.get('error_message', '')
                }
                statement_elem = validation_elem.find('./Statement')
                if statement_elem is not None and statement_elem.text:
                    validation['statement'] = statement_elem.text.strip()
            
            # 解析执行规则
            rules = []
            rules_elem = action_elem.find('./Rules')
            if rules_elem:
                for rule_elem in rules_elem.findall('./Rule'):
                    rule_type = rule_elem.get('type', '')
                    rule_description = rule_elem.get('description', '')
                    rule_content = rule_elem.get('content', '')
                    memory_type = rule_elem.get('memory_type', '')
                    
                    rule_def = {
                        'type': rule_type,
                        'description': rule_description
                    }
                    
                    # 查找 Statement 或 SummaryTemplate 子元素
                    statement_elem = rule_elem.find('./Statement')
                    if statement_elem is not None and statement_elem.text:
                        rule_def['statement'] = statement_elem.text.strip()
                    
                    summary_elem = rule_elem.find('./SummaryTemplate')
                    if summary_elem is not None and summary_elem.text:
                        rule_def['summary_template'] = summary_elem.text.strip()
                    
                    if rule_content:
                        rule_def['content'] = rule_content
                    if memory_type:
                        rule_def['memory_type'] = memory_type
                    
                    rules.append(rule_def)
            
            action_types[action_name] = {
                'display_name': display_name,
                'description': description,
                'parameters': parameters,
                'validation': validation,
                'rules': rules
            }
        
        return {'action_types': action_types}
    
    def _parse_synapser_patterns_xml(self, root: ET.Element) -> Dict[str, Any]:
        """
        解析意图模式 XML
        
        Args:
            root: XML 根元素
            
        Returns:
            包含 synapser_patterns 和 synonyms 的字典
        """
        patterns = {}
        synonyms = {}
        
        # 解析模式
        for pattern_elem in root.findall('./Pattern'):
            action = pattern_elem.get('action')
            requires_target = pattern_elem.get('requires_target', 'false').lower() == 'true'
            target_type = pattern_elem.get('target_type')
            
            if not action:
                continue
            
            # 解析关键词
            keywords_elem = pattern_elem.find('./Keywords')
            keywords = []
            if keywords_elem is not None and keywords_elem.text:
                keywords = [k.strip() for k in keywords_elem.text.split(',')]
            
            # 解析模板
            templates = []
            templates_elem = pattern_elem.find('./Templates')
            if templates_elem:
                for template_elem in templates_elem.findall('./Template'):
                    if template_elem.text:
                        templates.append(template_elem.text.strip())
            
            patterns[action] = {
                'keywords': keywords,
                'requires_target': requires_target,
                'target_type': target_type,
                'templates': templates
            }
        
        # 解析同义词库
        synonyms_elem = root.find('./Synonyms')
        if synonyms_elem:
            for group_elem in synonyms_elem.findall('./SynonymGroup'):
                primary = group_elem.get('primary')
                if not primary:
                    continue
                
                aliases = []
                for alias_elem in group_elem.findall('./Alias'):
                    if alias_elem.text:
                        aliases.append(alias_elem.text.strip())
                
                # 为主词添加自身作为同义词
                synonyms[primary] = [primary] + aliases
                
                # 为每个别名添加主词和其他别名作为同义词
                for alias in aliases:
                    synonyms[alias] = [primary, alias] + [a for a in aliases if a != alias]
        
        return {
            'synapser_patterns': patterns,
            'synonyms': synonyms
        }
