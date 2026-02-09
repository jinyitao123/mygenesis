"""
AI Copilot路由模块
统一管理所有AI Copilot相关的API路由
"""

import logging
from datetime import datetime
from flask import request, jsonify, Response, stream_with_context
from backend.core.request_context import RequestContext, DomainContextManager
from backend.core.exceptions import DomainNotFoundError

logger = logging.getLogger(__name__)

def register_copilot_routes(app, ai_copilot, domain_manager):
    """注册AI Copilot路由"""
    
    # 1. AI生成内容
    @app.route('/api/v1/copilot/generate', methods=['POST'])
    def copilot_generate():
        """AI Copilot生成内容"""
        try:
            data = request.json
            if not data:
                return jsonify({"error": "没有提供数据"}), 400
            
            prompt = data.get('prompt', '')
            content_type = data.get('type', 'object_type')
            context = data.get('context', {})
            
            if not prompt:
                return jsonify({"error": "没有提供提示词"}), 400
            
            # 调用AI Copilot
            result = ai_copilot.generate_content(prompt, content_type, context)
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"AI生成失败: {e}")
            return jsonify({
                "status": "error",
                "error": f"AI生成失败: {str(e)}"
            }), 500
    
    # 2. 文本转Cypher
    @app.route('/api/v1/copilot/text-to-cypher', methods=['POST'])
    def text_to_cypher():
        """自然语言转Cypher"""
        try:
            data = request.json
            if not data:
                return jsonify({"error": "没有提供数据"}), 400
            
            natural_language = data.get('text', '')
            context = data.get('context', {})
            
            if not natural_language:
                return jsonify({"error": "没有提供文本"}), 400
            
            result = ai_copilot.text_to_cypher(natural_language, context)
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"文本转Cypher失败: {e}")
            return jsonify({"error": f"文本转Cypher失败: {str(e)}"}), 500
    
    # 3. 建议动作
    @app.route('/api/v1/copilot/suggest-actions', methods=['POST'])
    def suggest_actions():
        """为对象类型推荐动作"""
        try:
            data = request.json
            if not data:
                return jsonify({"error": "没有提供数据"}), 400
            
            object_type = data.get('object_type', '')
            context = data.get('context', {})
            
            if not object_type:
                return jsonify({"error": "没有提供对象类型"}), 400
            
            suggestions = ai_copilot.suggest_actions(object_type, context)
            
            return jsonify({
                "status": "success",
                "suggestions": suggestions
            })
            
        except Exception as e:
            logger.error(f"动作推荐失败: {e}")
            return jsonify({"error": f"动作推荐失败: {str(e)}"}), 500
    
    # 4. AI聊天 (HTMX版本)
    @app.route('/api/v1/copilot/chat', methods=['POST'])
    def copilot_chat():
        """AI Copilot聊天"""
        try:
            data = request.json
            if not data or 'message' not in data:
                return jsonify({'error': '没有提供消息'}), 400
            
            message = data['message']
            context = data.get('context', {})
            
            # 这里调用AI Copilot服务
            logger.info(f"Copilot消息: {message}, 上下文: {context}")
            
            # 模拟响应
            response_text = f"我收到了您的消息: '{message}'。这是一个模拟响应。在实际实现中，我会调用AI模型来生成有意义的回答。"
            
            # 如果是关于代码的请求，生成示例代码
            if 'cypher' in message.lower() or '查询' in message:
                response_text += "\n\n示例Cypher查询：\n```cypher\nMATCH (n) RETURN n LIMIT 10\n```"
            
            return jsonify({
                'response': response_text,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Copilot聊天失败: {e}")
            return jsonify({'error': str(e)}), 500
    
    # 5. AI流式响应
    @app.route('/api/v1/copilot/stream')
    def copilot_stream():
        """AI Copilot流式响应 - Server-Sent Events"""
        def generate():
            # 模拟流式响应
            messages = [
                "正在思考您的问题...",
                "分析上下文信息...",
                "生成回答...",
                "这是我对您问题的回答。"
            ]
            
            import json
            import time
            
            for msg in messages:
                yield f"data: {json.dumps({'type': 'chunk', 'content': msg})}\n\n"
                time.sleep(0.5)
            
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"
        
        return Response(stream_with_context(generate()), 
                       mimetype='text/event-stream',
                       headers={
                           'Cache-Control': 'no-cache',
                           'Connection': 'keep-alive',
                           'X-Accel-Buffering': 'no'
                       })
    
    # 6. 简化的AI生成路由
    @app.route('/api/v1/copilot/simple-generate', methods=['POST'])
    def ai_generate_simple():
        """AI生成内容 (简化路由)"""
        try:
            data = request.json
            if not data:
                return jsonify({"error": "没有提供数据"}), 400
            
            prompt = data.get('prompt', '')
            content_type = data.get('type', 'object_type')
            domain = data.get('domain', RequestContext.get_current_domain())
            
            if not prompt:
                return jsonify({"error": "没有提供提示词"}), 400
            
            # 验证领域访问权限
            if not DomainContextManager.validate_domain_access(domain, domain_manager.list_domains()):
                raise DomainNotFoundError(domain)
            
            # 构建上下文
            context = {
                'domain': domain,
                'schema': domain_manager.get_domain_files(domain).get('schema', ''),
                'seed': domain_manager.get_domain_files(domain).get('seed', '')
            }
            
            try:
                # 调用AI Copilot
                result = ai_copilot.generate_content(prompt, content_type, context)
                
                content = result.get("content", result.get("result", ""))
                
                if content:
                    return jsonify({
                        "status": "success",
                        "result": content,
                        "type": content_type,
                        "domain": domain
                    })
            except Exception as ai_error:
                logger.warning(f"AI服务调用失败，使用模拟结果: {ai_error}")
            
            # AI服务失败时返回模拟结果
            mock_result = generate_mock_result(prompt, content_type)
            return jsonify({
                "status": "success",
                "result": mock_result,
                "type": content_type,
                "domain": domain,
                "mock": True
            })
            
        except DomainNotFoundError as e:
            logger.error(f"领域不存在: {e.domain_name}")
            return jsonify(e.to_dict()), 404
        except Exception as e:
            logger.error(f"AI生成失败: {e}")
            return jsonify({
                "status": "error",
                "error": f"AI生成失败: {str(e)}"
            }), 500
    
    # 7. CSV导入生成领域文件
    @app.route('/api/v1/copilot/csv-to-domain', methods=['POST'])
    def csv_to_domain():
        """将CSV数据转换为完整的领域文件"""
        try:
            data = request.json
            if not data:
                return jsonify({"error": "没有提供数据"}), 400
            
            csv_content = data.get('csv_content', '')
            domain_name = data.get('domain_name', 'CSV导入领域')
            domain_id = data.get('domain_id', '')
            
            if not csv_content:
                return jsonify({"error": "没有提供CSV内容"}), 400
            
            if not domain_id:
                # 自动生成领域ID
                import re
                domain_id = re.sub(r'[^a-z0-9_]', '_', domain_name.lower())
                domain_id = re.sub(r'_+', '_', domain_id).strip('_')
                if not domain_id:
                    domain_id = 'csv_imported_domain'
            
            # 构建详细的提示词
            prompt = f"""请基于以下CSV数据生成完整的领域本体文件：

领域信息:
- 领域名称: {domain_name}
- 领域ID: {domain_id}

CSV内容:
{csv_content[:3000]}

请生成以下完整的XML/JSON文件：

1. config.json - 领域配置文件
   - 包含name, description, ui_config等
   - 根据CSV内容选择合适的颜色和图标

2. object_types.xml - 对象类型定义
   - 分析CSV中的实体类型（如product, supplier, customer等）
   - 为每种实体类型定义属性和约束
   - 包含合适的图标和颜色

3. action_types.xml - 动作类型定义
   - 基于CSV中的业务逻辑推断可能的动作
   - 包含preconditions和effects

4. seed_data.xml - 种子数据
   - 将CSV数据转换为XML格式的种子数据
   - 保持数据完整性和一致性

5. synapser_patterns.xml - 同步模式定义（可选）
   - 定义数据同步和转换规则

请确保：
1. 所有XML文件格式正确，有完整的XML声明
2. JSON文件格式正确
3. 文件内容符合业务逻辑
4. 使用中文注释说明重要部分

请为每个文件生成完整的内容，用```xml和```json代码块包裹。"""

            # 调用AI Copilot
            result = ai_copilot.generate_content(prompt, "object_type", {
                "data_type": "csv_to_domain",
                "domain_name": domain_name,
                "domain_id": domain_id,
                "csv_sample": csv_content[:500]
            })
            
            content = result.get("content", result.get("result", ""))
            
            return jsonify({
                "status": "success",
                "domain_name": domain_name,
                "domain_id": domain_id,
                "generated_content": content,
                "files": [
                    "config.json",
                    "object_types.xml", 
                    "action_types.xml",
                    "seed_data.xml",
                    "synapser_patterns.xml"
                ]
            })
            
        except Exception as e:
            logger.error(f"CSV转领域失败: {e}")
            return jsonify({
                "status": "error",
                "error": f"CSV转领域失败: {str(e)}"
            }), 500
    
    # 8. 兼容性路由
    @app.route('/api/copilot/generate', methods=['POST'])
    def copilot_generate_compat():
        """AI Copilot生成内容 (兼容性路由)"""
        return copilot_generate()
    
    @app.route('/api/copilot/chat', methods=['POST'])
    def copilot_chat_compat():
        """AI Copilot聊天 (兼容性路由)"""
        return copilot_chat()
    
    @app.route('/api/copilot/stream')
    def copilot_stream_compat():
        """AI Copilot流式响应 (兼容性路由)"""
        return copilot_stream()
    
    @app.route('/api/ai_generate', methods=['POST'])
    def ai_generate_compat():
        """AI生成内容 (兼容性路由)"""
        return ai_generate_simple()
    
    @app.route('/api/copilot/csv-to-domain', methods=['POST'])
    def csv_to_domain_compat():
        """CSV转领域 (兼容性路由)"""
        return csv_to_domain()
    
    logger.info("AI Copilot路由注册完成")
    return app

def generate_mock_result(prompt, content_type):
    """生成模拟的AI结果"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if content_type == 'object_type':
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<ObjectType name="NewEntity{timestamp.replace('-', '').replace(':', '').replace(' ', '')}" 
           icon="cube" color="#3b82f6" primary_key="id" description="AI生成的实体类型">
    <Property name="id" type="string" required="true" description="唯一标识符"/>
    <Property name="name" type="string" required="true" description="名称"/>
    <Property name="description" type="string" required="false" description="描述"/>
    <Property name="created_at" type="datetime" required="false" default="now()" description="创建时间"/>
</ObjectType>'''
    
    elif content_type == 'relationship':
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<LinkType name="HAS_RELATIONSHIP{timestamp.replace('-', '').replace(':', '').replace(' ', '')}" 
         source="EntityA" target="EntityB" color="#10b981" description="AI生成的关系类型">
    <Property name="strength" type="integer" required="false" default="1" description="关系强度"/>
    <Property name="created_at" type="datetime" required="false" default="now()" description="创建时间"/>
</LinkType>'''
    
    elif content_type == 'action':
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<ActionType name="AI_Generated_Action" description="AI生成的动作类型">
    <Trigger type="condition" expression="always_true"/>
    <Effect type="log" message="执行AI生成的动作：{prompt}"/>
    <Effect type="update" target="current" property="last_action" value="AI_Generated_Action"/>
</ActionType>'''
    
    elif content_type == 'cypher':
        return f'''// AI生成的Cypher查询
// 提示词: {prompt}
// 生成时间: {timestamp}

MATCH (n:Entity)
WHERE n.description CONTAINS '{prompt[:20]}...'
RETURN n
LIMIT 10'''
    
    elif content_type == 'description':
        return f"""AI生成的描述（基于提示词："{prompt}"）：

这是一个由AI自动生成的描述内容。内容涉及{prompt}相关的内容，由Genesis Studio AI Copilot在{timestamp}生成。

特点：
- 智能分析用户需求
- 自动生成相关内容
- 支持多种内容类型
- 可直接应用到项目中"""
    
    else:
        return f"""AI生成的结果（类型: {content_type}）

提示词: {prompt}
生成时间: {timestamp}

这是一个模拟的AI生成结果。在实际部署中，此内容将由AI服务根据您的需求生成。"""