"""
Enhanced Domain Manager - 增强版领域模组管理器

支持：
1. 从 E:\Documents\MyGame\domains 加载真实数据
2. 解析XML文件为结构化数据
3. 提供完整的领域信息给前端
"""

import os
import shutil
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class EnhancedDomainManager:
    """增强版领域模组管理器"""
    
    def __init__(self, project_root: str):
        """
        初始化增强版领域管理器
        
        Args:
            project_root: 项目根目录路径 (E:\Documents\MyGame)
        """
        self.project_root = Path(project_root)
        self.domains_dir = self.project_root / "domains"
        self.ontology_dir = self.project_root / "ontology"
        
        # 确保目录存在
        self.domains_dir.parent.mkdir(parents=True, exist_ok=True)
        self.domains_dir.mkdir(exist_ok=True)
        self.ontology_dir.mkdir(exist_ok=True)
        
        # 当前激活的领域
        self.active_domain = None
        
        # 领域文件映射
        self.file_mapping = {
            "schema": "object_types.xml",
            "seed": "seed_data.xml", 
            "actions": "action_types.xml",
            "patterns": "synapser_patterns.xml"
        }
        
        logger.info(f"EnhancedDomainManager initialized: domains_dir={self.domains_dir}")
    
    def list_domains(self) -> List[str]:
        """列出所有可用的领域"""
        domains = []
        for item in self.domains_dir.iterdir():
            if item.is_dir():
                domains.append(item.name)
        return sorted(domains)
    
    def get_domain_info(self, domain_name: str) -> Dict[str, Any]:
        """获取领域详细信息"""
        domain_path = self.domains_dir / domain_name
        
        if not domain_path.exists():
            return {"error": f"Domain {domain_name} not found"}
        
        info = {
            "id": domain_name,
            "name": domain_name,
            "description": "",
            "files": {},
            "config": None,
            "object_types": [],
            "action_rules": [],
            "seed_data": []
        }
        
        # 加载配置
        config_file = domain_path / "config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    info["config"] = config
                    info["name"] = config.get("name", domain_name)
                    info["description"] = config.get("description", "")
                    
                    # 从配置中提取对象类型
                    features = config.get("features", {})
                    object_types = features.get("object_types", [])
                    if object_types:
                        info["object_types"] = [
                            {"name": ot, "description": f"{ot} 对象类型"}
                            for ot in object_types
                        ]
                    
                    # 从配置中提取动作类型
                    action_types = features.get("action_types", [])
                    if action_types:
                        info["action_rules"] = [
                            {"name": at, "description": f"{at} 动作规则"}
                            for at in action_types
                        ]
                    
                    # 从配置中提取默认对象
                    default_objects = config.get("default_objects", [])
                    if default_objects:
                        info["seed_data"] = default_objects[:10]  # 限制数量
                        
            except Exception as e:
                logger.error(f"Failed to load config for {domain_name}: {e}")
        
        # 检查并解析XML文件
        for file_type, filename in self.file_mapping.items():
            file_path = domain_path / filename
            if file_path.exists():
                try:
                    content = self._parse_xml_file(file_path)
                    info["files"][file_type] = content
                    
                    # 从XML中提取结构化数据
                    if file_type == "schema" and content:
                        info["object_types"].extend(self._extract_object_types_from_xml(content))
                    elif file_type == "actions" and content:
                        info["action_rules"].extend(self._extract_action_rules_from_xml(content))
                    elif file_type == "seed" and content:
                        info["seed_data"].extend(self._extract_seed_data_from_xml(content))
                        
                except Exception as e:
                    logger.error(f"Failed to parse {filename} for {domain_name}: {e}")
                    info["files"][file_type] = str(e)
            else:
                info["files"][file_type] = None
        
        return info
    
    def _parse_xml_file(self, file_path: Path) -> Optional[str]:
        """解析XML文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content or content == "test":
                    return None
                
                # 尝试解析XML
                try:
                    root = ET.fromstring(content)
                    # 如果解析成功，返回美化后的XML
                    return self._prettify_xml(root)
                except ET.ParseError:
                    # 如果不是有效的XML，返回原始内容
                    return content
        except Exception as e:
            logger.error(f"Failed to read XML file {file_path}: {e}")
            return None
    
    def _prettify_xml(self, elem: ET.Element, level: int = 0) -> str:
        """美化XML输出"""
        indent = "  " * level
        if len(elem) == 0:
            return f"{indent}<{elem.tag}>{elem.text or ''}</{elem.tag}>"
        
        result = f"{indent}<{elem.tag}>\n"
        for child in elem:
            result += self._prettify_xml(child, level + 1) + "\n"
        result += f"{indent}</{elem.tag}>"
        return result
    
    def _extract_object_types_from_xml(self, xml_content: str) -> List[Dict[str, Any]]:
        """从XML中提取对象类型"""
        object_types = []
        try:
            # 清理XML内容
            import re
            cleaned_xml = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', xml_content)
            cleaned_xml = re.sub(r'[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F\u0080-\u009F]', '', cleaned_xml)
            
            root = ET.fromstring(cleaned_xml)
            
            # 查找对象类型定义
            for obj_type in root.findall('.//ObjectType'):
                name = obj_type.get('name') or obj_type.findtext('Name')
                description = obj_type.get('description') or obj_type.findtext('Description') or ""
                
                if name:
                    # 提取属性
                    properties = {}
                    for prop in obj_type.findall('.//Property'):
                        prop_name = prop.get('name') or prop.findtext('Name')
                        prop_type = prop.get('type') or prop.findtext('Type') or "string"
                        if prop_name:
                            properties[prop_name] = {
                                "type": prop_type,
                                "description": prop.get('description') or prop.findtext('Description') or ""
                            }
                    
                    object_types.append({
                        "name": name,
                        "description": description,
                        "properties": properties
                    })
        except Exception as e:
            logger.error(f"Failed to extract object types from XML: {e}")
        
        return object_types
    
    def _extract_action_rules_from_xml(self, xml_content: str) -> List[Dict[str, Any]]:
        """从XML中提取动作规则"""
        action_rules = []
        try:
            # 清理XML内容，移除无效字符
            import re
            # 移除控制字符和非XML字符，但保留中文字符
            cleaned_xml = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', xml_content)
            # 移除无效的Unicode字符（某些emoji）
            cleaned_xml = re.sub(r'[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F\u0080-\u009F]', '', cleaned_xml)
            
            root = ET.fromstring(cleaned_xml)
            
            # 查找动作规则定义
            for action in root.findall('.//action_type'):
                name = action.get('id') or action.findtext('id') or action.findtext('ID') or action.findtext('Name')
                description = action.get('description') or action.findtext('description') or action.findtext('Description') or ""
                
                if name:
                    # 提取源和目标（从preconditions/effects中提取）
                    source = None
                    target = None
                    
                    # 尝试从preconditions中提取源
                    preconditions = action.find('preconditions')
                    if preconditions is not None:
                        for precondition in preconditions.findall('precondition'):
                            obj_type = precondition.findtext('object_type')
                            if obj_type:
                                source = obj_type
                                break
                    
                    # 尝试从effects中提取目标
                    effects = action.find('effects')
                    if effects is not None:
                        for effect in effects.findall('effect'):
                            obj_type = effect.findtext('object_type')
                            if obj_type:
                                target = obj_type
                                break
                    
                    action_rules.append({
                        "name": name,
                        "description": description,
                        "source": source,
                        "target": target,
                        "conditions": None  # 这个XML格式没有直接的conditions字段
                    })
        except Exception as e:
            logger.error(f"Failed to extract action rules from XML: {e}")
        
        return action_rules
    
    def _extract_seed_data_from_xml(self, xml_content: str) -> List[Dict[str, Any]]:
        """从XML中提取种子数据"""
        seed_data = []
        try:
            # 清理XML内容
            import re
            cleaned_xml = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', xml_content)
            cleaned_xml = re.sub(r'[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F\u0080-\u009F]', '', cleaned_xml)
            
            root = ET.fromstring(cleaned_xml)
            
            # 查找实体定义
            for entity in root.findall('.//Entity'):
                entity_id = entity.get('id') or entity.findtext('ID')
                entity_type = entity.get('type') or entity.findtext('Type')
                
                if entity_id:
                    # 提取属性
                    properties = {}
                    for prop in entity.findall('.//Property'):
                        prop_name = prop.get('name') or prop.findtext('Name')
                        prop_value = prop.get('value') or prop.findtext('Value')
                        if prop_name:
                            properties[prop_name] = prop_value
                    
                    seed_data.append({
                        "id": entity_id,
                        "name": entity_id,
                        "type": entity_type or "unknown",
                        "properties": properties
                    })
        except Exception as e:
            logger.error(f"Failed to extract seed data from XML: {e}")
        
        return seed_data
    
    def get_active_domain_files(self) -> Dict[str, str]:
        """获取当前激活领域的文件内容"""
        if not self.active_domain:
            return {}
        
        domain_path = self.domains_dir / self.active_domain
        files_content = {}
        
        for file_type, filename in self.file_mapping.items():
            file_path = domain_path / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        files_content[file_type] = f.read()
                except Exception as e:
                    logger.error(f"Failed to read {filename}: {e}")
                    files_content[file_type] = ""
            else:
                files_content[file_type] = ""
        
        return files_content
    
    def get_domain_files(self, domain_name: str) -> Dict[str, str]:
        """获取指定领域的文件内容"""
        domain_path = self.domains_dir / domain_name
        
        if not domain_path.exists():
            return {}
        
        files_content = {}
        
        for file_type, filename in self.file_mapping.items():
            file_path = domain_path / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        files_content[file_type] = f.read()
                except Exception as e:
                    logger.error(f"Failed to read {filename} for {domain_name}: {e}")
                    files_content[file_type] = ""
            else:
                files_content[file_type] = ""
        
        return files_content
    
    def activate_domain(self, domain_name: str) -> bool:
        """激活领域模组"""
        domain_path = self.domains_dir / domain_name
        
        if not domain_path.exists():
            logger.error(f"Domain not found: {domain_name}")
            return False
        
        try:
            copied_files = []
            missing_files = []
            
            # 复制领域文件到 ontology 目录
            for target_type, source_filename in self.file_mapping.items():
                source_file = domain_path / source_filename
                target_file = self.ontology_dir / source_filename
                
                if source_file.exists():
                    shutil.copy2(source_file, target_file)
                    copied_files.append(source_filename)
                else:
                    missing_files.append(source_filename)
            
            if copied_files:
                self.active_domain = domain_name
                logger.info(f"Activated domain: {domain_name}, copied files: {copied_files}")
                if missing_files:
                    logger.warning(f"Missing files for {domain_name}: {missing_files}")
                return True
            else:
                logger.error(f"No files found for domain: {domain_name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to activate domain {domain_name}: {e}")
            return False
    
    def save_domain_file(self, domain_name: str, file_type: str, content: str) -> bool:
        """保存领域文件"""
        if file_type not in self.file_mapping:
            logger.error(f"Invalid file type: {file_type}")
            return False
        
        domain_path = self.domains_dir / domain_name
        domain_path.mkdir(exist_ok=True)
        
        filename = self.file_mapping[file_type]
        file_path = domain_path / filename
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Saved {filename} for domain: {domain_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to save {filename} for {domain_name}: {e}")
            return False