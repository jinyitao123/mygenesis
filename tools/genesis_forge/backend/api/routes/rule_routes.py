"""
规则引擎路由模块
统一管理所有规则引擎相关的API路由
"""

import logging
from flask import request, jsonify
from backend.services.rule_engine import Event, EventType

logger = logging.getLogger(__name__)

def register_rule_routes(app, rule_engine, validation_engine):
    """注册规则引擎路由"""
    
    # 1. 模拟运行动作
    @app.route('/api/v1/rules/simulate', methods=['POST'])
    def simulate_action():
        """模拟运行动作"""
        try:
            data = request.json
            if not data:
                return jsonify({"error": "没有提供数据"}), 400
            
            action_id = data.get('action_id', '')
            parameters = data.get('parameters', {})
            
            if not action_id:
                return jsonify({"error": "没有提供动作ID"}), 400
            
            # 创建模拟事件
            event = Event(
                event_type=EventType.USER_INTENT,
                source="simulation",
                data={
                    "action": action_id,
                    "parameters": parameters
                }
            )
            
            # 处理事件
            results = rule_engine.process_event(event, parameters)
            
            return jsonify({
                "status": "success",
                "results": results
            })
            
        except Exception as e:
            logger.error(f"动作模拟失败: {e}")
            return jsonify({"error": f"动作模拟失败: {str(e)}"}), 500
    
    # 2. 验证规则
    @app.route('/api/v1/rules/validate', methods=['POST'])
    def validate_rule():
        """验证规则"""
        try:
            data = request.json
            if not data:
                return jsonify({"error": "没有提供数据"}), 400
            
            cypher_query = data.get('cypher_query', '')
            
            if not cypher_query:
                return jsonify({"error": "没有提供Cypher查询"}), 400
            
            # 验证Cypher语法
            valid, errors = validation_engine.validate_cypher_query(cypher_query)
            
            if valid:
                return jsonify({
                    "status": "success",
                    "message": "Cypher语法验证通过"
                })
            else:
                return jsonify({
                    "status": "error",
                    "error_code": "ERR_CYPHER_02",
                    "errors": errors
                }), 400
                
        except Exception as e:
            logger.error(f"规则验证失败: {e}")
            return jsonify({"error": f"规则验证失败: {str(e)}"}), 500
    
    logger.info("规则引擎路由注册完成")
    return app