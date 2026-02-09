"""
本体管理路由模块
统一管理所有本体相关的API路由
"""

import json
import logging
import xml.etree.ElementTree as ET
from flask import request, jsonify
from backend.core.models import OntologyModel
from backend.core.request_context import RequestContext
from backend.core.exceptions import SchemaValidationError

logger = logging.getLogger(__name__)

def register_ontology_routes(app, domain_manager, validation_engine):
    """注册本体管理路由"""
    
    # 1. 验证本体
    @app.route('/api/v1/ontology/validate', methods=['POST'])
    def validate_ontology():
        """验证本体完整性"""
        try:
            data = request.json
            if not data:
                return jsonify({"error": "没有提供数据"}), 400
            
            # 验证JSON Schema
            valid, errors = validation_engine.validate_json_schema(data, OntologyModel)
            
            if valid:
                return jsonify({
                    "status": "success",
                    "message": "本体验证通过"
                })
            else:
                return jsonify({
                    "status": "error",
                    "error_code": "ERR_SCHEMA_01",
                    "errors": errors
                }), 400
                
        except Exception as e:
            logger.error(f"本体验证失败: {e}")
            return jsonify({"error": f"本体验证失败: {str(e)}"}), 500
    
    # 2. 检查本体完整性
    @app.route('/api/v1/ontology/integrity', methods=['GET'])
    def check_ontology_integrity():
        """检查本体完整性"""
        try:
            # 获取当前领域
            current_domain = RequestContext.get_current_domain()
            
            # 获取当前领域文件
            files_content = domain_manager.get_domain_files(current_domain)
            logger.info(f"获取领域 {current_domain} 的文件，keys: {list(files_content.keys())}")
            
            schema_content = files_content.get("schema", "")
            if schema_content:
                logger.info(f"Schema内容长度: {len(schema_content)} 字符")
                logger.info(f"Schema内容前200字符: {schema_content[:200] if len(schema_content) > 200 else schema_content}")
            
            if not schema_content:
                return jsonify({
                    "status": "error",
                    "message": f"领域 {current_domain} 没有Schema定义"
                }), 400
            
            # 解析并验证 - 支持XML和JSON格式
            schema_data = {}
            
            try:
                # 首先尝试解析为JSON
                schema_data = json.loads(schema_content)
                logger.info(f"Schema是JSON格式，成功解析")
            except json.JSONDecodeError:
                # 如果不是JSON，尝试解析为XML
                logger.info(f"Schema是XML格式，尝试从XML中提取本体数据")
                try:
                    # 使用XML转换器从XML中提取数据
                    from backend.core.xml_converter import XMLConverter
                    
                    # XML文件包含对象类型定义，需要转换为OntologyModel格式
                    # 首先，尝试从XML中提取基本信息
                    root = ET.fromstring(schema_content)
                    
                    # 构建基本的schema数据 - 符合OntologyModel要求
                    schema_data = {
                        "domain": current_domain,
                        "object_types": {},
                        "relationships": {},
                        "action_types": {},
                        "world_snapshots": {},
                        "domain_concepts": []
                    }
                    
                    # 从XML中提取对象类型 - 符合ObjectTypeDefinition模型
                    for obj_elem in root.findall(".//ObjectType"):
                        obj_name = obj_elem.get("name")
                        if obj_name:
                            # 转换type_key为大写下划线格式
                            if obj_name.isupper() and ' ' not in obj_name:
                                type_key = obj_name
                            else:
                                type_key = obj_name.upper().replace(' ', '_').replace('-', '_')
                            
                            # 构建符合ObjectTypeDefinition要求的数据结构
                            obj_def = {
                                "type_key": type_key,
                                "name": obj_name,
                                "description": obj_elem.get("description", ""),
                                "properties": {},
                                "visual_assets": [],
                                "tags": []
                            }
                            
                            # 提取属性 - 符合PropertyDefinition模型
                            for prop_elem in obj_elem.findall(".//Property"):
                                prop_name = prop_elem.get("name")
                                if prop_name:
                                    # 构建符合PropertyDefinition要求的数据结构
                                    obj_def["properties"][prop_name] = {
                                        "name": prop_name,
                                        "type": prop_elem.get("type", "string"),
                                        "description": prop_elem.get("description", ""),
                                        "default_value": None,
                                        "is_required": False,
                                        "constraints": {}
                                    }
                            
                            schema_data["object_types"][obj_name] = obj_def
                    
                    # 从XML中提取关系类型 - 符合RelationshipDefinition模型
                    link_types_elem = root.find(".//LinkTypes")
                    if link_types_elem is not None:
                        for link_elem in link_types_elem.findall(".//LinkType"):
                            link_name = link_elem.get("name")
                            if link_name:
                                # 构建符合RelationshipDefinition要求的数据结构
                                schema_data["relationships"][link_name] = {
                                    "relation_type": link_name,
                                    "name": link_name,
                                    "source_type": link_elem.get("source", "Unknown"),
                                    "target_type": link_elem.get("target", "Unknown"),
                                    "description": link_elem.get("description", ""),
                                    "properties": {},
                                    "constraints": []
                                }
                    
                    logger.info(f"从XML中提取了 {len(schema_data['object_types'])} 个对象类型和 {len(schema_data['relationships'])} 个关系类型")
                    
                except Exception as xml_error:
                    logger.error(f"XML解析失败: {xml_error}")
                    return jsonify({
                        "status": "error",
                        "message": f"领域 {current_domain} 的Schema既不是有效的JSON也不是有效的XML格式: {str(xml_error)}"
                    }), 400
            
            # 确保数据符合OntologyModel要求
            # 1. 添加domain字段（如果缺失）
            if "domain" not in schema_data:
                schema_data["domain"] = current_domain
            
            # 2. 转换relationships为字典（如果是列表）
            if "relationships" in schema_data and isinstance(schema_data["relationships"], list):
                relationships_dict = {}
                for rel in schema_data["relationships"]:
                    if isinstance(rel, dict):
                        rel_name = rel.get("name") or rel.get("type")
                        if rel_name:
                            relationships_dict[rel_name] = rel
                schema_data["relationships"] = relationships_dict
            
            # 3. 转换objectTypes为字典（如果是列表）
            if "objectTypes" in schema_data and isinstance(schema_data["objectTypes"], list):
                object_types_dict = {}
                for obj in schema_data["objectTypes"]:
                    if isinstance(obj, dict):
                        obj_name = obj.get("name") or obj.get("type_key")
                        if obj_name:
                            object_types_dict[obj_name] = obj
                schema_data["objectTypes"] = object_types_dict
            
            # 4. 确保其他字段存在
            if "object_types" not in schema_data and "objectTypes" in schema_data:
                schema_data["object_types"] = schema_data["objectTypes"]
            
            if "action_types" not in schema_data:
                schema_data["action_types"] = {}
            
            if "world_snapshots" not in schema_data:
                schema_data["world_snapshots"] = {}
            
            if "domain_concepts" not in schema_data:
                schema_data["domain_concepts"] = []
            
            try:
                ontology = OntologyModel(**schema_data)
            except Exception as model_error:
                logger.error(f"OntologyModel创建失败: {model_error}")
                
                # 对于Pydantic验证错误，提取详细信息
                error_message = str(model_error)
                error_details = []
                
                # 尝试从错误消息中提取结构化信息
                if "validation errors for OntologyModel" in error_message:
                    # 这是一个Pydantic验证错误
                    lines = error_message.split('\n')
                    for line in lines:
                        if 'type=value_error' in line or 'type=missing' in line:
                            # 提取字段名和错误信息
                            parts = line.strip().split()
                            if parts:
                                field_name = parts[0]
                                error_type = "validation_error"
                                if 'type=value_error' in line:
                                    error_type = "value_error"
                                elif 'type=missing' in line:
                                    error_type = "missing_field"
                                
                                error_details.append({
                                    "field": field_name,
                                    "type": error_type,
                                    "message": line.strip()
                                })
                
                return jsonify({
                    "status": "error",
                    "message": "本体数据格式错误",
                    "error": error_message,
                    "errors": error_details if error_details else [{"field": "unknown", "message": error_message}],
                    "schema_data_keys": list(schema_data.keys())
                }), 400
            
            # 验证完整性
            errors = validation_engine.validate_reference_integrity(
                schema_data, ontology
            )
            
            if errors:
                return jsonify({
                    "status": "warning",
                    "error_code": "ERR_REF_03",
                    "errors": errors
                })
            else:
                return jsonify({
                    "status": "success",
                    "message": "本体完整性检查通过"
                })
                
        except Exception as e:
            logger.error(f"完整性检查失败: {e}")
            return jsonify({"error": f"完整性检查失败: {str(e)}"}), 500
    
    # 3. 保存本体数据
    @app.route('/api/v1/ontology/save', methods=['POST'])
    def save_ontology_api():
        """保存本体数据"""
        try:
            data = request.json
            if not data:
                return jsonify({"status": "error", "message": "没有提供数据"}), 400
            
            domain = data.get('domain', RequestContext.get_current_domain())
            ontology_data = data.get('ontology', '')
            
            if not ontology_data:
                return jsonify({"status": "error", "message": "没有提供本体数据"}), 400
            
            # 保存到领域目录
            success = domain_manager.save_domain_file(domain, "schema", ontology_data)
            
            if success:
                logger.info(f"Saved ontology for domain: {domain}")
                return jsonify({
                    "status": "success",
                    "message": "本体数据保存成功",
                    "domain": domain
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": "本体数据保存失败"
                }), 500
                
        except Exception as e:
            logger.error(f"保存本体失败: {e}")
            return jsonify({
                "status": "error",
                "message": f"保存失败: {str(e)}"
            }), 500
    
    # 4. 兼容性路由
    @app.route('/api/save_ontology', methods=['POST'])
    def save_ontology_compat():
        """保存本体数据 (兼容性路由)"""
        return save_ontology_api()
    
    logger.info("本体管理路由注册完成")
    return app