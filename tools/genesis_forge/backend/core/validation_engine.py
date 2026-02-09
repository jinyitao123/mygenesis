"""
Pydantic 验证引擎

基于PRP文档的验证需求：
1. Schema验证：JSON结构必须符合Pydantic定义
2. 引用完整性：所有引用必须存在
3. 类型合规性：实例属性必须符合Schema定义
4. 图拓扑约束：关系连接必须符合约束

错误代码：
- ERR_SCHEMA_01: ValidationError - JSON结构不符合Pydantic定义
- ERR_REF_03: IntegrityError - 引用了不存在的实体ID
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import xml.etree.ElementTree as ET

from .models import (
    OntologyModel, ObjectTypeDefinition, RelationshipDefinition,
    ActionTypeDefinition, WorldSnapshot, validate_ontology_integrity
)

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """验证错误异常"""
    def __init__(self, error_code: str, message: str, details: Optional[Dict] = None):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(f"{error_code}: {message}")


class ValidationEngine:
    """Pydantic验证引擎"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.ontology_cache: Dict[str, OntologyModel] = {}
    
    def validate_json_schema(self, json_data: Dict[str, Any], model_class) -> Tuple[bool, List[str]]:
        """
        验证JSON数据是否符合Pydantic模型
        
        Args:
            json_data: JSON数据
            model_class: Pydantic模型类
            
        Returns:
            (是否有效, 错误消息列表)
        """
        errors = []
        
        try:
            # 尝试解析为Pydantic模型
            model_instance = model_class(**json_data)
            return True, []
        except Exception as e:
            error_msg = f"JSON结构验证失败: {str(e)}"
            errors.append(error_msg)
            logger.error(f"ERR_SCHEMA_01: {error_msg}")
            return False, errors
    
    def validate_object_type(self, obj: ObjectTypeDefinition) -> Tuple[bool, List[str]]:
        """
        验证对象类型定义
        
        Args:
            obj: ObjectTypeDefinition 实例
            
        Returns:
            (是否有效, 错误消息列表)
        """
        errors = []
        
        try:
            # 验证 type_key 格式
            if not obj.type_key or not isinstance(obj.type_key, str):
                errors.append("type_key 不能为空且必须是字符串")
            elif not all(c.isupper() or c == '_' for c in obj.type_key.replace('0', '').replace('1', '').replace('2', '').replace('3', '').replace('4', '').replace('5', '').replace('6', '').replace('7', '').replace('8', '').replace('9', '')):
                # 简单检查：如果不是全大写和下划线，给出警告但不报错
                pass  # 允许混合格式
            
            # 验证必填字段
            if not obj.name:
                errors.append("name 不能为空")
            
            if not obj.description:
                errors.append("description 不能为空")
            
            # 验证 properties 格式
            if obj.properties:
                for prop_name, prop_schema in obj.properties.items():
                    if not prop_schema.name:
                        errors.append(f"属性 {prop_name} 的 name 不能为空")
            
            if errors:
                return False, errors
            
            return True, []
            
        except Exception as e:
            error_msg = f"对象类型验证失败: {str(e)}"
            errors.append(error_msg)
            logger.error(f"ERR_SCHEMA_01: {error_msg}")
            return False, errors
    
    def validate_ontology_file(self, file_path: Path, file_type: str) -> Tuple[bool, List[str]]:
        """
        验证本体文件
        
        Args:
            file_path: 文件路径
            file_type: 文件类型 (schema, seed, actions, patterns)
            
        Returns:
            (是否有效, 错误消息列表)
        """
        errors = []
        
        if not file_path.exists():
            errors.append(f"文件不存在: {file_path}")
            return False, errors
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            if file_type == "schema":
                # 验证Schema文件
                return self._validate_schema_file(content)
            elif file_type == "seed":
                # 验证Seed文件
                return self._validate_seed_file(content)
            elif file_type == "actions":
                # 验证Actions文件
                return self._validate_actions_file(content)
            elif file_type == "patterns":
                # 验证Patterns文件
                return self._validate_patterns_file(content)
            else:
                errors.append(f"未知文件类型: {file_type}")
                return False, errors
                
        except Exception as e:
            error_msg = f"文件读取失败: {str(e)}"
            errors.append(error_msg)
            logger.error(f"文件验证失败: {error_msg}")
            return False, errors
    
    def _validate_schema_file(self, content: str) -> Tuple[bool, List[str]]:
        """验证Schema文件"""
        errors = []
        
        try:
            # 尝试解析为JSON
            data = json.loads(content)
            
            # 验证为OntologyModel
            valid, schema_errors = self.validate_json_schema(data, OntologyModel)
            if not valid:
                errors.extend(schema_errors)
                return False, errors
            
            # 创建OntologyModel实例进行进一步验证
            ontology = OntologyModel(**data)
            
            # 验证本体完整性
            integrity_errors = validate_ontology_integrity(ontology)
            if integrity_errors:
                errors.extend(integrity_errors)
                return False, errors
            
            # 缓存验证通过的模型
            self.ontology_cache[ontology.domain] = ontology
            
            return True, []
            
        except json.JSONDecodeError as e:
            error_msg = f"JSON解析失败: {str(e)}"
            errors.append(error_msg)
            logger.error(f"ERR_SCHEMA_01: {error_msg}")
            return False, errors
        except Exception as e:
            error_msg = f"Schema验证失败: {str(e)}"
            errors.append(error_msg)
            logger.error(f"ERR_SCHEMA_01: {error_msg}")
            return False, errors
    
    def _validate_seed_file(self, content: str) -> Tuple[bool, List[str]]:
        """验证Seed文件"""
        errors = []
        
        try:
            # 尝试解析为JSON
            data = json.loads(content)
            
            # 验证为WorldSnapshot
            valid, schema_errors = self.validate_json_schema(data, WorldSnapshot)
            if not valid:
                errors.extend(schema_errors)
                return False, errors
            
            snapshot = WorldSnapshot(**data)
            
            # 验证节点和关系的完整性
            node_errors = self._validate_seed_nodes(snapshot.nodes)
            if node_errors:
                errors.extend(node_errors)
            
            link_errors = self._validate_seed_links(snapshot.links)
            if link_errors:
                errors.extend(link_errors)
            
            if errors:
                return False, errors
            
            return True, []
            
        except json.JSONDecodeError as e:
            error_msg = f"JSON解析失败: {str(e)}"
            errors.append(error_msg)
            logger.error(f"ERR_SCHEMA_01: {error_msg}")
            return False, errors
        except Exception as e:
            error_msg = f"Seed验证失败: {str(e)}"
            errors.append(error_msg)
            logger.error(f"ERR_SCHEMA_01: {error_msg}")
            return False, errors
    
    def _validate_seed_nodes(self, nodes: List[Dict[str, Any]]) -> List[str]:
        """验证Seed节点"""
        errors = []
        
        # 检查节点ID唯一性
        node_ids = set()
        for node in nodes:
            node_id = node.get("id")
            if not node_id:
                errors.append("节点缺少ID")
                continue
            
            if node_id in node_ids:
                errors.append(f"节点ID重复: {node_id}")
                continue
            
            node_ids.add(node_id)
            
            # 检查节点类型
            node_type = node.get("type")
            if not node_type:
                errors.append(f"节点 {node_id} 缺少类型")
                continue
            
            # TODO: 检查节点类型是否在Schema中定义
            # 需要加载对应的OntologyModel进行验证
        
        return errors
    
    def _validate_seed_links(self, links: List[Dict[str, Any]]) -> List[str]:
        """验证Seed关系"""
        errors = []
        
        # 收集所有节点ID用于验证引用
        node_ids = set()
        # TODO: 从nodes参数获取节点ID
        
        for link in links:
            link_id = link.get("id")
            source = link.get("source")
            target = link.get("target")
            link_type = link.get("type")
            
            if not all([link_id, source, target, link_type]):
                errors.append("关系缺少必要字段 (id, source, target, type)")
                continue
            
            # 检查源节点和目标节点是否存在
            if source not in node_ids:
                errors.append(f"关系 {link_id} 引用了不存在的源节点: {source}")
            
            if target not in node_ids:
                errors.append(f"关系 {link_id} 引用了不存在的目标节点: {target}")
            
            # TODO: 检查关系类型是否在Schema中定义
            # 需要加载对应的OntologyModel进行验证
        
        return errors
    
    def _validate_actions_file(self, content: str) -> Tuple[bool, List[str]]:
        """验证Actions文件"""
        errors = []
        
        try:
            # 尝试解析为JSON
            data = json.loads(content)
            
            # 验证为ActionTypeDefinition列表
            if not isinstance(data, list):
                errors.append("Actions文件必须是JSON数组")
                return False, errors
            
            action_ids = set()
            for action_data in data:
                # 验证每个动作
                valid, action_errors = self.validate_json_schema(action_data, ActionTypeDefinition)
                if not valid:
                    errors.extend(action_errors)
                    continue
                
                action = ActionTypeDefinition(**action_data)
                
                # 检查动作ID唯一性
                if action.action_id in action_ids:
                    errors.append(f"动作ID重复: {action.action_id}")
                else:
                    action_ids.add(action.action_id)
            
            if errors:
                return False, errors
            
            return True, []
            
        except json.JSONDecodeError as e:
            error_msg = f"JSON解析失败: {str(e)}"
            errors.append(error_msg)
            logger.error(f"ERR_SCHEMA_01: {error_msg}")
            return False, errors
        except Exception as e:
            error_msg = f"Actions验证失败: {str(e)}"
            errors.append(error_msg)
            logger.error(f"ERR_SCHEMA_01: {error_msg}")
            return False, errors
    
    def _validate_patterns_file(self, content: str) -> Tuple[bool, List[str]]:
        """验证Patterns文件"""
        errors = []
        
        try:
            # 尝试解析为JSON
            data = json.loads(content)
            
            # Patterns文件应该是字典格式
            if not isinstance(data, dict):
                errors.append("Patterns文件必须是JSON对象")
                return False, errors
            
            # 验证基本结构
            required_keys = ["patterns", "intents", "entities"]
            for key in required_keys:
                if key not in data:
                    errors.append(f"缺少必要键: {key}")
            
            if errors:
                return False, errors
            
            # 验证patterns数组
            patterns = data.get("patterns", [])
            if not isinstance(patterns, list):
                errors.append("patterns必须是数组")
            
            # 验证intents字典
            intents = data.get("intents", {})
            if not isinstance(intents, dict):
                errors.append("intents必须是对象")
            
            # 验证entities字典
            entities = data.get("entities", {})
            if not isinstance(entities, dict):
                errors.append("entities必须是对象")
            
            if errors:
                return False, errors
            
            return True, []
            
        except json.JSONDecodeError as e:
            error_msg = f"JSON解析失败: {str(e)}"
            errors.append(error_msg)
            logger.error(f"ERR_SCHEMA_01: {error_msg}")
            return False, errors
        except Exception as e:
            error_msg = f"Patterns验证失败: {str(e)}"
            errors.append(error_msg)
            logger.error(f"ERR_SCHEMA_01: {error_msg}")
            return False, errors
    
    def validate_cypher_query(self, cypher_query: str) -> Tuple[bool, List[str]]:
        """
        验证Cypher查询语法
        
        Args:
            cypher_query: Cypher查询语句
            
        Returns:
            (是否有效, 错误消息列表)
        """
        errors = []
        
        # 基本语法检查
        if not cypher_query.strip():
            errors.append("Cypher查询不能为空")
            return False, errors
        
        # 检查是否包含危险操作
        dangerous_keywords = ["DROP", "DELETE", "REMOVE", "DETACH"]
        for keyword in dangerous_keywords:
            if keyword in cypher_query.upper():
                errors.append(f"Cypher查询包含危险关键字: {keyword}")
        
        # 检查基本结构
        cypher_upper = cypher_query.upper()
        valid_keywords = ["MATCH", "CREATE", "MERGE", "RETURN"]
        has_valid_keyword = any(keyword in cypher_upper for keyword in valid_keywords)
        
        # 检查是否有拼写错误的关键词
        cypher_keywords = [
            "MATCH", "CREATE", "MERGE", "RETURN", "WHERE", "SET", "DELETE",
            "DETACH", "REMOVE", "WITH", "UNWIND", "CALL", "YIELD",
            "ORDER", "BY", "LIMIT", "SKIP", "AS", "AND", "OR", "NOT",
            "IN", "STARTS", "ENDS", "CONTAINS", "IS", "NULL", "TRUE", "FALSE"
        ]
        
        # 检查是否有类似关键词的拼写错误
        words = cypher_upper.replace('(', ' ').replace(')', ' ').replace('{', ' ').replace('}', ' ').split()
        for word in words:
            if len(word) > 2 and word.isalpha():
                # 检查是否接近某个有效关键词
                for keyword in valid_keywords:
                    if self._similarity_score(word, keyword) > 0.6 and word != keyword:
                        errors.append(f"Cypher语法错误: '{word}' 可能是 '{keyword}' 的拼写错误")
                        break
        
        if not has_valid_keyword:
            errors.append("Cypher查询缺少核心操作 (MATCH/CREATE/MERGE/RETURN)")
        
        if errors:
            logger.error(f"ERR_CYPHER_02: Cypher语法错误")
            return False, errors
        
        return True, []
    
    def _similarity_score(self, s1: str, s2: str) -> float:
        """计算两个字符串的相似度 (0-1)"""
        if len(s1) != len(s2):
            return 0.0
        
        matches = sum(c1 == c2 for c1, c2 in zip(s1, s2))
        return matches / len(s1)
    
    def validate_reference_integrity(self, source_data: Dict[str, Any], target_ontology: OntologyModel) -> List[str]:
        """
        验证引用完整性
        
        Args:
            source_data: 源数据
            target_ontology: 目标本体模型
            
        Returns:
            错误消息列表
        """
        errors = []
        
        # 检查类型引用
        if "type" in source_data:
            obj_type = source_data["type"]
            if obj_type not in target_ontology.object_types:
                errors.append(f"引用了不存在的对象类型: {obj_type}")
        
        # 检查关系引用
        if "relationships" in source_data:
            for rel in source_data["relationships"]:
                rel_type = rel.get("type")
                if rel_type and rel_type not in target_ontology.relationships:
                    errors.append(f"引用了不存在的关系类型: {rel_type}")
        
        # 检查动作引用
        if "actions" in source_data:
            for action in source_data["actions"]:
                action_id = action.get("action_id")
                if action_id and action_id not in target_ontology.action_types:
                    errors.append(f"引用了不存在的动作类型: {action_id}")
        
        if errors:
            for error in errors:
                logger.error(f"ERR_REF_03: {error}")
        
        return errors
    
    def validate_domain_configuration(self, domain_name: str) -> Dict[str, Any]:
        """
        验证领域配置完整性
        
        Args:
            domain_name: 领域名称
            
        Returns:
            验证结果
        """
        result = {
            "domain": domain_name,
            "valid": False,
            "errors": [],
            "warnings": [],
            "files": {}
        }
        
        domain_path = self.project_root / "domains" / domain_name
        
        if not domain_path.exists():
            result["errors"].append(f"领域目录不存在: {domain_path}")
            return result
        
        # 检查必要文件
        required_files = ["schema.json", "seed.json", "actions.json", "patterns.json"]
        file_types = ["schema", "seed", "actions", "patterns"]
        
        for file_type, required_file in zip(file_types, required_files):
            file_path = domain_path / required_file
            result["files"][file_type] = {
                "exists": file_path.exists(),
                "path": str(file_path)
            }
            
            if file_path.exists():
                # 验证文件内容
                valid, file_errors = self.validate_ontology_file(file_path, file_type)
                result["files"][file_type]["valid"] = valid
                result["files"][file_type]["errors"] = file_errors
                
                if not valid:
                    result["errors"].extend([f"{file_type}: {err}" for err in file_errors])
            else:
                result["warnings"].append(f"缺少文件: {required_file}")
                result["files"][file_type]["valid"] = False
                result["files"][file_type]["errors"] = ["文件不存在"]
        
        # 检查配置文件
        config_file = domain_path / "config.json"
        if config_file.exists():
            try:
                config_data = json.loads(config_file.read_text(encoding='utf-8'))
                result["config"] = config_data
            except Exception as e:
                result["warnings"].append(f"配置文件解析失败: {str(e)}")
        
        # 确定整体有效性
        result["valid"] = len(result["errors"]) == 0
        
        return result