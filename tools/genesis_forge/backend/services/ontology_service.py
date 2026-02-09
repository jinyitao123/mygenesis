"""
本体管理服务 (OntologyService)

基于PRP文档的原子服务实现：
职责: 对JSON/XML文件的CRUD，包含版本控制

核心方法:
- load_schema(domain): 加载特定领域的定义
- save_entity(type, data): 保存实体定义并校验
- get_version_history(): 获取Git提交记录
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import hashlib

from backend.core.models import (
    OntologyModel, ObjectTypeDefinition, RelationshipDefinition,
    ActionTypeDefinition, WorldSnapshot, validate_ontology_integrity
)
from backend.core.validation_engine import ValidationEngine

logger = logging.getLogger(__name__)


class OntologyService:
    """本体管理服务"""
    
    def __init__(self, project_root: str, validation_engine: ValidationEngine):
        """
        初始化本体服务
        
        Args:
            project_root: 项目根目录
            validation_engine: 验证引擎
        """
        self.project_root = Path(project_root)
        self.validation_engine = validation_engine
        self.ontology_cache: Dict[str, OntologyModel] = {}
        self.version_history: Dict[str, List[Dict]] = {}
        
        # 确保目录存在
        self.ontology_dir = self.project_root / "ontology"
        self.ontology_dir.mkdir(exist_ok=True)
        
        # 版本控制目录
        self.versions_dir = self.ontology_dir / "versions"
        self.versions_dir.mkdir(exist_ok=True)
    
    def load_schema(self, domain: str) -> Tuple[bool, Optional[OntologyModel], List[str]]:
        """
        加载特定领域的本体定义
        
        Args:
            domain: 领域名称
            
        Returns:
            (是否成功, 本体模型, 错误消息)
        """
        try:
            # 检查缓存
            if domain in self.ontology_cache:
                logger.info(f"从缓存加载本体: {domain}")
                return True, self.ontology_cache[domain], []
            
            # 查找领域文件
            domain_path = self.project_root / "domains" / domain
            schema_file = domain_path / "schema.json"
            
            if not schema_file.exists():
                # 尝试XML格式
                schema_file = domain_path / "schema.xml"
                if not schema_file.exists():
                    return False, None, [f"领域 {domain} 的schema文件不存在"]
            
            # 读取文件内容
            content = schema_file.read_text(encoding='utf-8')
            
            # 根据文件类型解析
            if schema_file.suffix == '.json':
                data = json.loads(content)
            elif schema_file.suffix == '.xml':
                # 简单XML解析（实际项目中可能需要更复杂的解析）
                data = self._parse_simple_xml(content)
            else:
                return False, None, [f"不支持的schema文件格式: {schema_file.suffix}"]
            
            # 验证并创建本体模型
            valid, errors = self.validation_engine.validate_json_schema(data, OntologyModel)
            if not valid:
                return False, None, errors
            
            ontology = OntologyModel(**data)
            
            # 验证本体完整性
            integrity_errors = validate_ontology_integrity(ontology)
            if integrity_errors:
                logger.warning(f"本体完整性警告: {integrity_errors}")
            
            # 缓存结果
            self.ontology_cache[domain] = ontology
            
            logger.info(f"成功加载本体: {domain}, 包含 {len(ontology.object_types)} 个对象类型")
            return True, ontology, []
            
        except Exception as e:
            error_msg = f"加载本体失败: {str(e)}"
            logger.error(error_msg)
            return False, None, [error_msg]
    
    def _parse_simple_xml(self, xml_content: str) -> Dict[str, Any]:
        """简单XML解析（用于兼容性）"""
        # 这是一个简化的XML解析器，实际项目中应该使用专业的XML库
        import xml.etree.ElementTree as ET
        
        try:
            root = ET.fromstring(xml_content)
            data = {"domain": "unknown", "object_types": {}, "relationships": {}, "action_types": {}}
            
            # 解析domain
            domain_elem = root.find("domain")
            if domain_elem is not None:
                data["domain"] = domain_elem.text or "unknown"
            
            # 解析对象类型
            object_types_elem = root.find("object_types")
            if object_types_elem is not None:
                for obj_elem in object_types_elem.findall("object_type"):
                    type_key = obj_elem.get("key", "")
                    if type_key:
                        data["object_types"][type_key] = {
                            "type_key": type_key,
                            "name": obj_elem.get("name", type_key),
                            "description": obj_elem.get("description", ""),
                            "properties": {},
                            "tags": []
                        }
            
            return data
        except Exception as e:
            logger.warning(f"XML解析失败，返回空本体: {e}")
            return {"domain": "unknown", "object_types": {}, "relationships": {}, "action_types": {}}
    
    def save_entity(self, entity_type: str, entity_data: Dict[str, Any], 
                   domain: str, validate: bool = True) -> Tuple[bool, List[str]]:
        """
        保存实体定义
        
        Args:
            entity_type: 实体类型 ('object_type', 'relationship', 'action_type')
            entity_data: 实体数据
            domain: 领域名称
            validate: 是否验证
            
        Returns:
            (是否成功, 错误消息)
        """
        try:
            # 加载现有本体
            success, ontology, errors = self.load_schema(domain)
            if not success:
                return False, errors
            
            # 验证实体数据
            if validate:
                valid, validation_errors = self._validate_entity(entity_type, entity_data, ontology)
                if not valid:
                    return False, validation_errors
            
            # 更新本体
            if entity_type == 'object_type':
                type_key = entity_data.get('type_key')
                if type_key:
                    obj_def = ObjectTypeDefinition(**entity_data)
                    ontology.object_types[type_key] = obj_def
                    
            elif entity_type == 'relationship':
                rel_type = entity_data.get('relation_type')
                if rel_type:
                    rel_def = RelationshipDefinition(**entity_data)
                    ontology.relationships[rel_type] = rel_def
                    
            elif entity_type == 'action_type':
                action_id = entity_data.get('action_id')
                if action_id:
                    action_def = ActionTypeDefinition(**entity_data)
                    ontology.action_types[action_id] = action_def
            
            else:
                return False, [f"不支持的实体类型: {entity_type}"]
            
            # 保存更新后的本体
            save_success, save_errors = self._save_ontology(ontology, domain)
            if not save_success:
                return False, save_errors
            
            # 清除缓存
            if domain in self.ontology_cache:
                del self.ontology_cache[domain]
            
            logger.info(f"成功保存实体: {entity_type} 到领域 {domain}")
            return True, []
            
        except Exception as e:
            error_msg = f"保存实体失败: {str(e)}"
            logger.error(error_msg)
            return False, [error_msg]
    
    def _validate_entity(self, entity_type: str, entity_data: Dict[str, Any], 
                        ontology: OntologyModel) -> Tuple[bool, List[str]]:
        """验证实体数据"""
        errors = []
        
        try:
            if entity_type == 'object_type':
                # 验证对象类型
                obj_def = ObjectTypeDefinition(**entity_data)
                
                # 检查type_key格式
                if not obj_def.type_key.isupper() or '_' not in obj_def.type_key:
                    errors.append("type_key必须使用大写下划线格式 (如: NPC_GUARD)")
                
                # 检查属性定义
                for prop_name, prop_schema in obj_def.properties.items():
                    if not prop_schema.name:
                        errors.append(f"属性 {prop_name} 缺少名称")
            
            elif entity_type == 'relationship':
                # 验证关系定义
                rel_def = RelationshipDefinition(**entity_data)
                
                # 检查源和目标类型是否存在
                for source_type in rel_def.source_constraint:
                    if source_type not in ontology.object_types:
                        errors.append(f"源类型 {source_type} 不存在")
                
                for target_type in rel_def.target_constraint:
                    if target_type not in ontology.object_types:
                        errors.append(f"目标类型 {target_type} 不存在")
            
            elif entity_type == 'action_type':
                # 验证动作类型
                action_def = ActionTypeDefinition(**entity_data)
                
                # 检查执行者和目标类型是否存在
                for actor_type in action_def.allowed_actors:
                    if actor_type != "SYSTEM" and actor_type != "ADMIN" and actor_type not in ontology.object_types:
                        errors.append(f"执行者类型 {actor_type} 不存在")
                
                for target_type in action_def.allowed_targets:
                    if target_type not in ontology.object_types:
                        errors.append(f"目标类型 {target_type} 不存在")
            
            if errors:
                return False, errors
            
            return True, []
            
        except Exception as e:
            return False, [f"实体验证失败: {str(e)}"]
    
    def _save_ontology(self, ontology: OntologyModel, domain: str) -> Tuple[bool, List[str]]:
        """保存本体到文件"""
        try:
            # 创建版本备份
            self._create_version_backup(domain, ontology)
            
            # 保存到领域目录
            domain_path = self.project_root / "domains" / domain
            domain_path.mkdir(exist_ok=True)
            
            # 保存为JSON
            schema_file = domain_path / "schema.json"
            with open(schema_file, 'w', encoding='utf-8') as f:
                json.dump(ontology.dict(), f, ensure_ascii=False, indent=2)
            
            logger.info(f"本体已保存到: {schema_file}")
            return True, []
            
        except Exception as e:
            error_msg = f"保存本体失败: {str(e)}"
            logger.error(error_msg)
            return False, [error_msg]
    
    def _create_version_backup(self, domain: str, ontology: OntologyModel):
        """创建版本备份"""
        try:
            # 生成版本ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            content_hash = hashlib.md5(
                json.dumps(ontology.dict(), sort_keys=True).encode()
            ).hexdigest()[:8]
            version_id = f"{timestamp}_{content_hash}"
            
            # 保存版本文件
            version_file = self.versions_dir / f"{domain}_{version_id}.json"
            with open(version_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "domain": domain,
                    "version_id": version_id,
                    "timestamp": timestamp,
                    "ontology": ontology.dict()
                }, f, ensure_ascii=False, indent=2)
            
            # 更新版本历史
            if domain not in self.version_history:
                self.version_history[domain] = []
            
            self.version_history[domain].append({
                "version_id": version_id,
                "timestamp": timestamp,
                "file": str(version_file)
            })
            
            # 限制历史记录数量
            if len(self.version_history[domain]) > 50:
                self.version_history[domain] = self.version_history[domain][-50:]
            
            logger.info(f"创建版本备份: {domain} -> {version_id}")
            
        except Exception as e:
            logger.warning(f"创建版本备份失败: {e}")
    
    def get_version_history(self, domain: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取版本历史
        
        Args:
            domain: 领域名称
            limit: 返回的最大记录数
            
        Returns:
            版本历史列表
        """
        try:
            # 如果内存中没有历史记录，从文件系统加载
            if domain not in self.version_history:
                self._load_version_history(domain)
            
            history = self.version_history.get(domain, [])
            return history[-limit:] if limit > 0 else history
            
        except Exception as e:
            logger.error(f"获取版本历史失败: {e}")
            return []
    
    def _load_version_history(self, domain: str):
        """从文件系统加载版本历史"""
        try:
            history = []
            
            # 查找该领域的所有版本文件
            pattern = f"{domain}_*.json"
            for version_file in self.versions_dir.glob(pattern):
                try:
                    with open(version_file, 'r', encoding='utf-8') as f:
                        version_data = json.load(f)
                    
                    history.append({
                        "version_id": version_data.get("version_id", ""),
                        "timestamp": version_data.get("timestamp", ""),
                        "file": str(version_file)
                    })
                except Exception as e:
                    logger.warning(f"加载版本文件失败 {version_file}: {e}")
            
            # 按时间戳排序
            history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            self.version_history[domain] = history
            
            logger.info(f"加载了 {len(history)} 个版本记录: {domain}")
            
        except Exception as e:
            logger.error(f"加载版本历史失败: {e}")
            self.version_history[domain] = []
    
    def restore_version(self, domain: str, version_id: str) -> Tuple[bool, List[str]]:
        """
        恢复特定版本
        
        Args:
            domain: 领域名称
            version_id: 版本ID
            
        Returns:
            (是否成功, 错误消息)
        """
        try:
            # 查找版本文件
            version_file = self.versions_dir / f"{domain}_{version_id}.json"
            if not version_file.exists():
                return False, [f"版本文件不存在: {version_file}"]
            
            # 加载版本数据
            with open(version_file, 'r', encoding='utf-8') as f:
                version_data = json.load(f)
            
            ontology_data = version_data.get("ontology", {})
            if not ontology_data:
                return False, ["版本数据无效"]
            
            # 验证本体
            valid, errors = self.validation_engine.validate_json_schema(ontology_data, OntologyModel)
            if not valid:
                return False, errors
            
            # 恢复本体
            ontology = OntologyModel(**ontology_data)
            
            # 保存到当前领域
            save_success, save_errors = self._save_ontology(ontology, domain)
            if not save_success:
                return False, save_errors
            
            # 清除缓存
            if domain in self.ontology_cache:
                del self.ontology_cache[domain]
            
            logger.info(f"成功恢复版本: {domain} -> {version_id}")
            return True, []
            
        except Exception as e:
            error_msg = f"恢复版本失败: {str(e)}"
            logger.error(error_msg)
            return False, [error_msg]
    
    def export_ontology(self, domain: str, format: str = "json") -> Tuple[bool, Optional[str], List[str]]:
        """
        导出本体
        
        Args:
            domain: 领域名称
            format: 导出格式 ('json', 'xml', 'yaml')
            
        Returns:
            (是否成功, 导出内容, 错误消息)
        """
        try:
            # 加载本体
            success, ontology, errors = self.load_schema(domain)
            if not success:
                return False, None, errors
            
            if format == "json":
                # 导出为JSON
                export_data = ontology.dict()
                content = json.dumps(export_data, ensure_ascii=False, indent=2)
                
            elif format == "xml":
                # 导出为XML
                content = self._export_to_xml(ontology)
                
            elif format == "yaml":
                # 导出为YAML
                try:
                    import yaml
                    export_data = ontology.dict()
                    content = yaml.dump(export_data, allow_unicode=True, default_flow_style=False)
                except ImportError:
                    return False, None, ["YAML导出需要PyYAML库"]
                    
            else:
                return False, None, [f"不支持的导出格式: {format}"]
            
            return True, content, []
            
        except Exception as e:
            error_msg = f"导出本体失败: {str(e)}"
            logger.error(error_msg)
            return False, None, [error_msg]
    
    def _export_to_xml(self, ontology: OntologyModel) -> str:
        """将本体导出为XML"""
        import xml.etree.ElementTree as ET
        
        # 创建根元素
        root = ET.Element("ontology")
        
        # 添加domain
        domain_elem = ET.SubElement(root, "domain")
        domain_elem.text = ontology.domain
        
        # 添加version
        version_elem = ET.SubElement(root, "version")
        version_elem.text = ontology.version
        
        # 添加对象类型
        if ontology.object_types:
            object_types_elem = ET.SubElement(root, "object_types")
            for type_key, obj_type in ontology.object_types.items():
                obj_elem = ET.SubElement(object_types_elem, "object_type")
                obj_elem.set("key", type_key)
                obj_elem.set("name", obj_type.name)
                if obj_type.description:
                    obj_elem.set("description", obj_type.description)
        
        # 添加关系
        if ontology.relationships:
            relationships_elem = ET.SubElement(root, "relationships")
            for rel_key, rel_def in ontology.relationships.items():
                rel_elem = ET.SubElement(relationships_elem, "relationship")
                rel_elem.set("type", rel_key)
                rel_elem.set("name", rel_def.name)
                if rel_def.description:
                    rel_elem.set("description", rel_def.description)
        
        # 转换为字符串
        rough_string = ET.tostring(root, encoding='unicode')
        
        # 美化输出
        import xml.dom.minidom
        dom = xml.dom.minidom.parseString(rough_string)
        return dom.toprettyxml(indent="  ")
    
    def search_entities(self, domain: str, query: str, 
                       entity_types: List[str] = None) -> Dict[str, List[Dict]]:
        """
        搜索实体
        
        Args:
            domain: 领域名称
            query: 搜索查询
            entity_types: 实体类型列表 ('object_type', 'relationship', 'action_type')
            
        Returns:
            搜索结果
        """
        try:
            # 加载本体
            success, ontology, errors = self.load_schema(domain)
            if not success:
                return {"error": errors}
            
            if entity_types is None:
                entity_types = ['object_type', 'relationship', 'action_type']
            
            results = {
                "object_types": [],
                "relationships": [],
                "action_types": []
            }
            
            query_lower = query.lower()
            
            # 搜索对象类型
            if 'object_type' in entity_types:
                for type_key, obj_type in ontology.object_types.items():
                    if (query_lower in type_key.lower() or 
                        query_lower in obj_type.name.lower() or
                        (obj_type.description and query_lower in obj_type.description.lower())):
                        
                        results["object_types"].append({
                            "type_key": type_key,
                            "name": obj_type.name,
                            "description": obj_type.description,
                            "property_count": len(obj_type.properties),
                            "tags": obj_type.tags
                        })
            
            # 搜索关系
            if 'relationship' in entity_types:
                for rel_key, rel_def in ontology.relationships.items():
                    if (query_lower in rel_key.lower() or 
                        query_lower in rel_def.name.lower() or
                        (rel_def.description and query_lower in rel_def.description.lower())):
                        
                        results["relationships"].append({
                            "relation_type": rel_key,
                            "name": rel_def.name,
                            "description": rel_def.description,
                            "source_constraint": rel_def.source_constraint,
                            "target_constraint": rel_def.target_constraint
                        })
            
            # 搜索动作类型
            if 'action_type' in entity_types:
                for action_key, action_def in ontology.action_types.items():
                    if (query_lower in action_key.lower() or 
                        query_lower in action_def.name.lower() or
                        (action_def.description and query_lower in action_def.description.lower())):
                        
                        results["action_types"].append({
                            "action_id": action_key,
                            "name": action_def.name,
                            "description": action_def.description,
                            "parameter_count": len(action_def.parameters),
                            "allowed_actors": action_def.allowed_actors
                        })
            
            return results
            
        except Exception as e:
            logger.error(f"搜索实体失败: {e}")
            return {"error": [str(e)]}