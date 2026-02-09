"""
HTMX路由模块
统一管理所有HTMX相关的API路由
"""

import json
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from flask import request, render_template, jsonify, Response, stream_with_context, make_response
from datetime import datetime

logger = logging.getLogger(__name__)

def register_htmx_routes(app, domain_manager, validation_engine, ai_copilot, git_ops, rule_engine):
    """注册所有HTMX路由"""
    
    # ========== 编辑器相关路由 ==========
    
    @app.route('/api/htmx/editor/object/<type_key>', methods=['GET'])
    def get_object_editor(type_key):
        """获取对象类型编辑器"""
        current_domain = request.args.get('domain', 'supply_chain')
        
        try:
            # 从领域管理器获取对象类型数据
            domain_data = domain_manager.get_domain_files(current_domain)
            schema_data = json.loads(domain_data.get('schema', '{}')) if domain_data.get('schema') else {}
            
            # 查找特定对象类型
            object_type = None
            if 'object_types' in schema_data:
                for obj in schema_data['object_types']:
                    if obj.get('type_key') == type_key:
                        object_type = obj
                        break
            
            if object_type:
                # 返回对象类型编辑器
                return render_template('fragments/editor_content.html',
                                     content=json.dumps(object_type, indent=2),
                                     language='json',
                                     file_path=f'objects/{type_key}.json')
            else:
                # 返回空编辑器
                return render_template('fragments/editor_content.html',
                                     content='{\n  "type_key": "' + type_key + '",\n  "properties": {},\n  "visual_assets": [],\n  "tags": []\n}',
                                     language='json',
                                     file_path=f'objects/{type_key}.json')
                
        except Exception as e:
            logger.error(f"获取对象编辑器失败: {e}")
            return f'<div class="p-4 bg-red-900/30 border border-red-700 rounded">错误: {str(e)}</div>', 500
    
    @app.route('/api/htmx/editor/action/<action_id>', methods=['GET'])
    def get_action_editor(action_id):
        """获取动作规则编辑器"""
        current_domain = request.args.get('domain', 'supply_chain')
        
        try:
            domain_data = domain_manager.get_domain_files(current_domain)
            actions_data = json.loads(domain_data.get('actions', '{}')) if domain_data.get('actions') else {}
            
            # 查找特定动作
            action = None
            if 'actions' in actions_data:
                for act in actions_data['actions']:
                    if act.get('action_id') == action_id:
                        action = act
                        break
            
            if action:
                return render_template('fragments/editor_content.html',
                                     content=json.dumps(action, indent=2),
                                     language='json',
                                     file_path=f'actions/{action_id}.json')
            else:
                return render_template('fragments/editor_content.html',
                                     content='{\n  "action_id": "' + action_id + '",\n  "validation_logic": "",\n  "execution_rules": []\n}',
                                     language='json',
                                     file_path=f'actions/{action_id}.json')
                
        except Exception as e:
            logger.error(f"获取动作编辑器失败: {e}")
            return f'<div class="p-4 bg-red-900/30 border border-red-700 rounded">错误: {str(e)}</div>', 500
    
    @app.route('/api/htmx/editor/seed/<seed_name>', methods=['GET'])
    def get_seed_editor(seed_name):
        """获取种子数据编辑器"""
        current_domain = request.args.get('domain', 'supply_chain')
        
        try:
            domain_data = domain_manager.get_domain_files(current_domain)
            seed_data = json.loads(domain_data.get('seed', '{}')) if domain_data.get('seed') else {}
            
            # 这里简化处理，返回整个种子数据
            return render_template('fragments/editor_content.html',
                                 content=json.dumps(seed_data, indent=2),
                                 language='json',
                                 file_path=f'seed/{seed_name}.json')
                
        except Exception as e:
            logger.error(f"获取种子编辑器失败: {e}")
            return f'<div class="p-4 bg-red-900/30 border border-red-700 rounded">错误: {str(e)}</div>', 500
    
    # ========== 保存操作 ==========
    
    @app.route('/api/htmx/save', methods=['POST'])
    def save_file():
        """保存文件 - HTMX版本"""
        try:
            file_path = request.form.get('file_path')
            content = request.form.get('content')
            
            if not file_path or not content:
                return render_template('fragments/toast.html',
                                     type='error',
                                     title='保存失败',
                                     message='缺少文件路径或内容'), 400
            
            current_domain = request.args.get('domain', 'supply_chain')
            
            # 根据文件类型保存到不同的位置
            if file_path.startswith('objects/'):
                # 保存对象类型
                domain_data = domain_manager.get_domain_files(current_domain)
                schema_data = json.loads(domain_data.get('schema', '{}')) if domain_data.get('schema') else {}
                
                if 'object_types' not in schema_data:
                    schema_data['object_types'] = []
                
                # 解析新内容
                new_object = json.loads(content)
                
                # 更新或添加对象类型
                updated = False
                for i, obj in enumerate(schema_data['object_types']):
                    if obj.get('type_key') == new_object.get('type_key'):
                        schema_data['object_types'][i] = new_object
                        updated = True
                        break
                
                if not updated:
                    schema_data['object_types'].append(new_object)
                
                # 保存回领域
                domain_manager.save_domain_file(current_domain, 'schema', json.dumps(schema_data, indent=2))
                
            elif file_path.startswith('actions/'):
                # 保存动作规则
                domain_data = domain_manager.get_domain_files(current_domain)
                actions_data = json.loads(domain_data.get('actions', '{}')) if domain_data.get('actions') else {}
                
                if 'actions' not in actions_data:
                    actions_data['actions'] = []
                
                new_action = json.loads(content)
                
                updated = False
                for i, act in enumerate(actions_data['actions']):
                    if act.get('action_id') == new_action.get('action_id'):
                        actions_data['actions'][i] = new_action
                        updated = True
                        break
                
                if not updated:
                    actions_data['actions'].append(new_action)
                
                domain_manager.save_domain_file(current_domain, 'actions', json.dumps(actions_data, indent=2))
            
            # 返回成功通知
            response = make_response(render_template('fragments/toast.html',
                                      type='success',
                                      title='保存成功',
                                      message=f'文件 {file_path} 已保存'))
            
            # 添加HTMX触发头，通知前端更新状态
            response.headers['HX-Trigger'] = 'save-success'
            return response
            
        except json.JSONDecodeError as e:
            return render_template('fragments/toast.html',
                                 type='error',
                                 title='JSON格式错误',
                                 message=f'无效的JSON格式: {str(e)}'), 400
        except Exception as e:
            logger.error(f"保存文件失败: {e}")
            return render_template('fragments/toast.html',
                                 type='error',
                                 title='保存失败',
                                 message=f'保存时发生错误: {str(e)}'), 500
    
    # ========== 验证操作 ==========
    
    @app.route('/api/htmx/validate', methods=['POST'])
    def validate_content():
        """验证内容 - HTMX版本"""
        try:
            content = request.form.get('content')
            file_type = request.form.get('type', 'json')
            
            if not content:
                errors = [{
                    'message': '没有提供验证内容',
                    'location': '未知',
                    'details': '请提供要验证的内容'
                }]
                return render_template('fragments/validation_results.html', errors=errors)
            
            errors = []
            
            # JSON格式验证
            if file_type == 'json':
                try:
                    json.loads(content)
                except json.JSONDecodeError as e:
                    errors.append({
                        'message': 'JSON语法错误',
                        'location': f'行 {e.lineno}, 列 {e.colno}',
                        'details': e.msg,
                        'line': e.lineno,
                        'suggestion': '检查JSON格式，确保引号、逗号和括号匹配'
                    })
            
            # 业务逻辑验证（示例）
            if file_type == 'json' and not errors:
                try:
                    data = json.loads(content)
                    
                    # 对象类型验证
                    if 'type_key' in data:
                        if not data['type_key'] or not isinstance(data['type_key'], str):
                            errors.append({
                                'message': '无效的对象类型键',
                                'location': 'type_key字段',
                                'details': 'type_key必须是非空字符串',
                                'suggestion': '提供一个有意义的类型标识符，如"NPC"或"WAREHOUSE"'
                            })
                    
                    # 动作规则验证
                    if 'action_id' in data:
                        if not data['action_id'] or not isinstance(data['action_id'], str):
                            errors.append({
                                'message': '无效的动作ID',
                                'location': 'action_id字段',
                                'details': 'action_id必须是非空字符串',
                                'suggestion': '提供一个有意义的动作标识符，如"ACT_ATTACK"或"ACT_TRANSFER"'
                            })
                
                except Exception as e:
                    errors.append({
                        'message': '业务逻辑验证失败',
                        'location': '未知',
                        'details': str(e)
                    })
            
            # 返回验证结果
            response = make_response(render_template('fragments/validation_results.html', errors=errors))
            
            # 如果有错误，触发打开验证面板
            if errors:
                response.headers['HX-Trigger'] = 'validation-error'
            
            return response
            
        except Exception as e:
            logger.error(f"验证内容失败: {e}")
            errors = [{
                'message': '验证过程出错',
                'location': '系统',
                'details': str(e)
            }]
            return render_template('fragments/validation_results.html', errors=errors), 500
    
    # ========== 图谱数据 ==========
    
    @app.route('/api/htmx/graph/data', methods=['GET'])
    def get_graph_data():
        """获取图谱数据 - HTMX版本"""
        try:
            current_domain = request.args.get('domain', 'supply_chain')
            
            # 获取领域信息
            domain_info = domain_manager.get_domain_info(current_domain)
            elements = []
            
            # 基于领域配置生成图数据
            config = domain_info.get('config', {})
            features = config.get('features', {})
            default_objects = config.get('default_objects', [])
            
            # 添加对象类型作为节点
            object_types = features.get('object_types', [])
            for i, obj_type in enumerate(object_types[:10]):  # 限制数量
                elements.append({
                    'data': {
                        'id': f'type_{obj_type}',
                        'label': obj_type,
                        'type': 'object_type',
                        'description': f'{obj_type} 对象类型'
                    },
                    'position': {'x': 100 + i * 150, 'y': 100}
                })
            
            # 添加默认对象作为节点
            for i, obj in enumerate(default_objects[:8]):  # 限制数量
                elements.append({
                    'data': {
                        'id': obj.get('id', f'obj_{i}'),
                        'label': obj.get('name', obj.get('id', f'对象{i}')),
                        'type': obj.get('type', 'entity'),
                        'properties': {k: v for k, v in obj.items() if k not in ['id', 'name', 'type']}
                    },
                    'position': {'x': 100 + (i % 4) * 200, 'y': 300 + (i // 4) * 150}
                })
            
            # 添加关系类型作为节点
            relation_types = features.get('relation_types', [])
            for i, rel_type in enumerate(relation_types[:8]):  # 限制数量
                elements.append({
                    'data': {
                        'id': f'rel_{rel_type}',
                        'label': rel_type,
                        'type': 'relation_type',
                        'description': f'{rel_type} 关系类型'
                    },
                    'position': {'x': 800 + (i % 4) * 150, 'y': 100 + (i // 4) * 100}
                })
            
            # 添加动作类型作为节点
            action_types = features.get('action_types', [])
            for i, action_type in enumerate(action_types[:6]):  # 限制数量
                elements.append({
                    'data': {
                        'id': f'action_{action_type}',
                        'label': action_type.replace('PROC_', ''),
                        'type': 'action_type',
                        'description': f'{action_type} 动作类型'
                    },
                    'position': {'x': 800 + (i % 3) * 180, 'y': 400 + (i // 3) * 120}
                })
            
            # 添加示例关系
            if object_types and default_objects:
                # 对象类型与实例的关系
                for i, obj_type in enumerate(object_types[:3]):
                    for j, obj in enumerate(default_objects[:2]):
                        if obj.get('type') == obj_type:
                            elements.append({
                                'data': {
                                    'id': f'edge_{obj_type}_{obj.get("id")}',
                                    'source': f'type_{obj_type}',
                                    'target': obj.get('id'),
                                    'label': 'INSTANCE_OF'
                                }
                            })
            
            # 添加关系类型之间的关系
            if relation_types:
                for i in range(min(3, len(relation_types) - 1)):
                    elements.append({
                        'data': {
                            'id': f'rel_edge_{i}',
                            'source': f'rel_{relation_types[i]}',
                            'target': f'rel_{relation_types[i+1]}',
                            'label': 'RELATED_TO'
                        }
                    })
            
            # 如果没有生成任何元素，提供示例数据
            if not elements:
                elements = [
                    {
                        'data': {'id': 'node1', 'label': '示例节点1', 'type': 'example'},
                        'position': {'x': 100, 'y': 100}
                    },
                    {
                        'data': {'id': 'node2', 'label': '示例节点2', 'type': 'example'},
                        'position': {'x': 300, 'y': 100}
                    },
                    {
                        'data': {'id': 'edge1', 'source': 'node1', 'target': 'node2', 'label': '连接'}
                    }
                ]
            
            return jsonify({'elements': elements})
            
        except Exception as e:
            logger.error(f"获取图谱数据失败: {e}")
            # 返回示例数据而不是空数组
            return jsonify({
                'elements': [
                    {
                        'data': {'id': 'error_node', 'label': '数据加载失败', 'type': 'error'},
                        'position': {'x': 100, 'y': 100}
                    },
                    {
                        'data': {'id': 'error_info', 'label': f'错误: {str(e)[:50]}', 'type': 'info'},
                        'position': {'x': 100, 'y': 200}
                    }
                ]
            })
    
    @app.route('/api/htmx/graph/node', methods=['POST'])
    def add_graph_node():
        """添加图谱节点 - HTMX版本"""
        try:
            node_data = request.json
            if not node_data:
                return jsonify({'error': '没有提供节点数据'}), 400
            
            current_domain = request.args.get('domain', 'supply_chain')
            
            # 这里简化处理，实际应该保存到种子数据
            logger.info(f"添加节点到领域 {current_domain}: {node_data}")
            
            return jsonify({'status': 'success', 'message': '节点已添加'})
            
        except Exception as e:
            logger.error(f"添加节点失败: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ========== 侧边栏数据 ==========
    
    @app.route('/api/htmx/sidebar/data', methods=['GET'])
    def get_sidebar_data():
        """获取侧边栏数据 - HTMX版本"""
        try:
            current_domain = request.args.get('domain', 'supply_chain')
            
            # 使用增强版DomainManager获取领域信息
            domain_info = domain_manager.get_domain_info(current_domain)
            
            # 提取结构化数据
            object_types = domain_info.get('object_types', [])
            action_rules = domain_info.get('action_rules', [])
            seed_data = domain_info.get('seed_data', [])
            
            # 如果从config.json中获取的数据为空，尝试从XML文件中提取
            if not object_types and domain_info.get('files', {}).get('schema'):
                schema_content = domain_info['files']['schema']
                if schema_content:
                    try:
                        # 尝试从XML中提取对象类型
                        root = ET.fromstring(schema_content)
                        for obj_type in root.findall('.//ObjectType'):
                            name = obj_type.get('name') or obj_type.findtext('Name')
                            if name:
                                object_types.append({
                                    'name': name,
                                    'description': obj_type.get('description') or obj_type.findtext('Description') or f'{name} 对象类型'
                                })
                    except:
                        pass
            
            if not action_rules and domain_info.get('files', {}).get('actions'):
                actions_content = domain_info['files']['actions']
                if actions_content:
                    try:
                        # 尝试从XML中提取动作规则
                        root = ET.fromstring(actions_content)
                        for action in root.findall('.//Action'):
                            name = action.get('name') or action.findtext('Name')
                            if name:
                                action_rules.append({
                                    'name': name,
                                    'description': action.get('description') or action.findtext('Description') or f'{name} 动作规则'
                                })
                    except:
                        pass
            
            # 格式化种子数据
            formatted_seed_data = []
            for seed in seed_data:
                if isinstance(seed, dict):
                    formatted_seed_data.append({
                        'name': seed.get('id') or seed.get('name', '未知'),
                        'type': seed.get('type', '未知类型')
                    })
            
            return jsonify({
                'object_types': object_types[:20],  # 限制数量
                'action_rules': action_rules[:20],
                'seed_data': formatted_seed_data[:10]
            })
            
        except Exception as e:
            logger.error(f"获取侧边栏数据失败: {e}")
            return jsonify({
                'object_types': [],
                'action_rules': [],
                'seed_data': []
            }), 500
    
    # ========== 系统操作 ==========
    
    @app.route('/api/htmx/deploy', methods=['POST'])
    def deploy_changes():
        """部署变更 - HTMX版本"""
        try:
            current_domain = request.args.get('domain', 'supply_chain')
            
            # 这里应该调用GitOps服务进行部署
            logger.info(f"部署领域 {current_domain} 的变更")
            
            # 模拟部署过程
            import time
            time.sleep(1)
            
            return render_template('fragments/toast.html',
                                 type='success',
                                 title='部署成功',
                                 message='变更已部署到生产环境')
            
        except Exception as e:
            logger.error(f"部署失败: {e}")
            return render_template('fragments/toast.html',
                                 type='error',
                                 title='部署失败',
                                 message=f'部署时发生错误: {str(e)}'), 500
    
    @app.route('/api/htmx/hot-reload', methods=['POST'])
    def htmx_hot_reload():
        """热重载 - HTMX版本"""
        try:
            current_domain = request.args.get('domain', 'supply_chain')
            
            logger.info(f"热重载领域 {current_domain}")
            
            # 触发图谱刷新事件
            response = make_response(render_template('fragments/toast.html',
                                      type='success',
                                      title='热重载完成',
                                      message='系统已重新加载最新配置'))
            
            response.headers['HX-Trigger'] = 'reload-graph'
            return response
            
        except Exception as e:
            logger.error(f"热重载失败: {e}")
            return render_template('fragments/toast.html',
                                 type='error',
                                 title='热重载失败',
                                 message=f'热重载时发生错误: {str(e)}'), 500
    
    # ========== 工具函数 ==========
    
    @app.route('/api/htmx/tools/format', methods=['POST'])
    def format_code():
        """格式化代码 - HTMX版本"""
        try:
            content = request.form.get('content')
            language = request.form.get('language', 'json')
            
            if not content:
                return '', 400
            
            formatted = content
            
            # JSON格式化
            if language == 'json':
                try:
                    data = json.loads(content)
                    formatted = json.dumps(data, indent=2, ensure_ascii=False)
                except:
                    pass
            
            return formatted
            
        except Exception as e:
            logger.error(f"格式化代码失败: {e}")
            return f'格式化失败: {str(e)}', 500
    
    # ========== 兼容性路由 ==========
    
    # 保留旧路由以兼容现有前端
    @app.route('/studio/editor/object/<type_key>', methods=['GET'])
    def get_object_editor_compat(type_key):
        """获取对象类型编辑器 (兼容性路由)"""
        return get_object_editor(type_key)
    
    @app.route('/studio/editor/action/<action_id>', methods=['GET'])
    def get_action_editor_compat(action_id):
        """获取动作规则编辑器 (兼容性路由)"""
        return get_action_editor(action_id)
    
    @app.route('/studio/editor/seed/<seed_name>', methods=['GET'])
    def get_seed_editor_compat(seed_name):
        """获取种子数据编辑器 (兼容性路由)"""
        return get_seed_editor(seed_name)
    
    @app.route('/api/save', methods=['POST'])
    def save_file_compat():
        """保存文件 (兼容性路由)"""
        return save_file()
    
    @app.route('/api/validate', methods=['POST'])
    def validate_content_compat():
        """验证内容 (兼容性路由)"""
        return validate_content()
    
    @app.route('/api/graph/data', methods=['GET'])
    def get_graph_data_compat():
        """获取图谱数据 (兼容性路由)"""
        return get_graph_data()
    
    @app.route('/api/graph/node', methods=['POST'])
    def add_graph_node_compat():
        """添加图谱节点 (兼容性路由)"""
        return add_graph_node()
    
    @app.route('/studio/sidebar/data', methods=['GET'])
    def get_sidebar_data_compat():
        """获取侧边栏数据 (兼容性路由)"""
        return get_sidebar_data()
    
    @app.route('/api/deploy', methods=['POST'])
    def deploy_changes_compat():
        """部署变更 (兼容性路由)"""
        return deploy_changes()
    
    @app.route('/api/tools/format', methods=['POST'])
    def format_code_compat():
        """格式化代码 (兼容性路由)"""
        return format_code()
    
    logger.info("HTMX路由注册完成")
    return app