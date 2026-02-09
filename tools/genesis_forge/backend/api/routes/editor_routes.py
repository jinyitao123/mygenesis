"""
编辑器路由模块
统一管理所有编辑器相关的API路由
"""

import json
import logging
from flask import request, jsonify
from backend.core.request_context import RequestContext

logger = logging.getLogger(__name__)

def register_editor_routes(app, domain_manager):
    """注册编辑器路由"""
    
    # 1. 保存文件内容
    @app.route('/api/v1/editor/save', methods=['POST'])
    def editor_save():
        """保存文件内容"""
        try:
            file_path = request.form.get('file_path')
            content = request.form.get('content')
            
            if not file_path or content is None:
                return jsonify({"error": "缺少文件路径或内容"}), 400
            
            # 解析文件路径，确定保存位置
            if file_path.startswith('objects/'):
                # 保存对象类型
                type_key = file_path.replace('objects/', '').replace('.json', '')
                current_domain = RequestContext.get_current_domain()
                files_content = domain_manager.get_domain_files(current_domain)
                
                # 更新schema中的对象类型
                if files_content.get('schema'):
                    schema_data = json.loads(files_content['schema'])
                    object_types = schema_data.get('object_types', [])
                    
                    # 查找并更新或添加对象类型
                    updated = False
                    for i, obj in enumerate(object_types):
                        if obj.get('type_key') == type_key:
                            object_types[i] = json.loads(content)
                            updated = True
                            break
                    
                    if not updated:
                        object_types.append(json.loads(content))
                    
                    schema_data['object_types'] = object_types
                    success = domain_manager.save_domain_file(current_domain, 'schema', json.dumps(schema_data, indent=2))
                    
                    if success:
                        return jsonify({"status": "success", "message": "对象类型保存成功"})
                    else:
                        return jsonify({"error": "保存失败"}), 500
            
            return jsonify({"error": "不支持的文件类型"}), 400
            
        except Exception as e:
            logger.error(f"保存文件失败: {e}")
            return jsonify({"error": f"保存失败: {str(e)}"}), 500
    
    # 2. 保存对象类型（表单方式）
    @app.route('/api/v1/editor/save/object', methods=['POST'])
    def save_object():
        """保存对象类型（表单方式）"""
        try:
            type_key = request.form.get('type_key')
            display_name = request.form.get('display_name')
            description = request.form.get('description')
            
            if not type_key:
                return jsonify({"error": "缺少类型键"}), 400
            
            # 构建对象类型数据
            object_data = {
                "type_key": type_key,
                "name": display_name or type_key,
                "description": description or "",
                "properties": {},
                "visual_assets": [],
                "tags": []
            }
            
            # 处理属性
            property_names = request.form.getlist('property_name[]')
            property_types = request.form.getlist('property_type[]')
            property_defaults = request.form.getlist('property_default[]')
            
            properties = {}
            for i in range(len(property_names)):
                if property_names[i]:
                    prop_name = property_names[i]
                    prop_type = property_types[i] if i < len(property_types) else "string"
                    prop_default = property_defaults[i] if i < len(property_defaults) else ""
                    
                    properties[prop_name] = prop_type
                    if prop_default:
                        # 这里可以添加默认值处理逻辑
                        pass
            
            object_data["properties"] = properties
            
            # 保存到领域
            current_domain = RequestContext.get_current_domain()
            files_content = domain_manager.get_domain_files(current_domain)
            
            if files_content.get('schema'):
                schema_data = json.loads(files_content['schema'])
                object_types = schema_data.get('object_types', [])
                
                # 查找并更新或添加对象类型
                updated = False
                for i, obj in enumerate(object_types):
                    if obj.get('type_key') == type_key:
                        object_types[i] = object_data
                        updated = True
                        break
                
                if not updated:
                    object_types.append(object_data)
                
                schema_data['object_types'] = object_types
                success = domain_manager.save_domain_file(current_domain, 'schema', json.dumps(schema_data, indent=2))
                
                if success:
                    return jsonify({"status": "success", "message": "对象类型保存成功"})
                else:
                    return jsonify({"error": "保存失败"}), 500
            else:
                return jsonify({"error": "没有找到schema文件"}), 400
            
        except Exception as e:
            logger.error(f"保存对象失败: {e}")
            return jsonify({"error": f"保存失败: {str(e)}"}), 500
    
    # 3. 验证内容
    @app.route('/api/v1/editor/validate', methods=['POST'])
    def editor_validate():
        """验证内容"""
        try:
            content = request.form.get('content')
            
            if not content:
                return jsonify({"error": "没有提供内容"}), 400
            
            # 尝试解析JSON
            try:
                data = json.loads(content)
                return jsonify({
                    "status": "success", 
                    "message": "JSON格式正确",
                    "data": data
                })
            except json.JSONDecodeError as e:
                return jsonify({
                    "status": "error",
                    "message": f"JSON格式错误: {str(e)}",
                    "line": e.lineno,
                    "column": e.colno
                }), 400
                
        except Exception as e:
            logger.error(f"验证失败: {e}")
            return jsonify({"error": f"验证失败: {str(e)}"}), 500
    
    # 4. 兼容性路由
    @app.route('/api/editor/save', methods=['POST'])
    def editor_save_compat():
        """保存文件内容 (兼容性路由)"""
        return editor_save()
    
    @app.route('/api/editor/save/object', methods=['POST'])
    def save_object_compat():
        """保存对象类型 (兼容性路由)"""
        return save_object()
    
    @app.route('/api/editor/validate', methods=['POST'])
    def editor_validate_compat():
        """验证内容 (兼容性路由)"""
        return editor_validate()
    
    logger.info("编辑器路由注册完成")
    return app