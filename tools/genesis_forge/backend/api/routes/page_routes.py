"""
页面路由模块
统一管理所有页面相关的路由
"""

import json
import logging
from flask import request, render_template, jsonify, send_from_directory
from datetime import datetime
from backend.core.request_context import RequestContext

logger = logging.getLogger(__name__)

def register_page_routes(app, domain_manager, DOMAIN_PACKS):
    """注册页面路由"""
    
    # 1. 启动页 - 领域选择器
    @app.route('/')
    def index():
        """启动页 - 领域选择器"""
        available_domains = domain_manager.list_domains()
        
        domains_info = []
        for domain_id in available_domains:
            if domain_id in DOMAIN_PACKS:
                domains_info.append({
                    "id": domain_id,
                    **DOMAIN_PACKS[domain_id]
                })
        
        current_domain = RequestContext.get_current_domain()
        
        return render_template('launcher.html', 
                             domains=domains_info,
                             current_domain=current_domain)
    
    # 2. Genesis Studio主界面
    @app.route('/studio')
    def studio():
        """Genesis Studio主界面"""
        # 从 Session 获取当前领域
        current_domain = RequestContext.get_current_domain()
        
        # 验证领域是否存在
        if current_domain not in DOMAIN_PACKS:
            current_domain = "supply_chain"
            RequestContext.set_current_domain(current_domain)
        
        # 获取当前领域配置
        files_content = domain_manager.get_domain_files(current_domain)
        
        current_domain_info = DOMAIN_PACKS.get(current_domain, {})
        
        # 解析侧边栏数据
        object_types = []
        action_rules = []
        seed_data = []
        
        try:
            # 解析对象类型
            if files_content.get('schema'):
                schema_data = json.loads(files_content['schema'])
                if 'object_types' in schema_data:
                    object_types = schema_data['object_types']
            
            # 解析动作规则
            if files_content.get('actions'):
                actions_data = json.loads(files_content['actions'])
                if 'actions' in actions_data:
                    action_rules = actions_data['actions']
            
            # 解析种子数据
            if files_content.get('seed'):
                seed_json = json.loads(files_content['seed'])
                if 'entities' in seed_json:
                    seed_data = [{'name': e.get('id', '未知')} for e in seed_json['entities'][:10]]
        except Exception as e:
            logger.warning(f"解析侧边栏数据失败: {e}")
        
        return render_template('studio.html',
                             current_domain=current_domain,
                             current_domain_name=current_domain_info.get("name", "未知领域"),
                             domain_color=current_domain_info.get("color", "#6b7280"),
                             domain_icon=current_domain_info.get("icon", "cube"),
                             object_types=object_types,
                             action_rules=action_rules,
                             seed_data=seed_data,
                             graph_elements=[])  # 图谱数据将通过HTMX加载
    
    # 3. 编辑器页面 - 本体编辑器 IDE (兼容性路由)
    @app.route('/editor')
    def editor():
        """编辑器页面 - 本体编辑器 IDE (兼容性路由)"""
        # 从 Session 获取当前领域
        current_domain = RequestContext.get_current_domain()
        
        # 验证领域是否存在
        if current_domain not in DOMAIN_PACKS:
            current_domain = "supply_chain"
            RequestContext.set_current_domain(current_domain)
        
        # 获取当前领域配置
        files_content = domain_manager.get_domain_files(current_domain)
        
        current_domain_info = DOMAIN_PACKS.get(current_domain, {})
        
        # 解析侧边栏数据
        object_types = []
        action_rules = []
        seed_data = []
        
        try:
            # 解析对象类型
            if files_content.get('schema'):
                schema_data = json.loads(files_content['schema'])
                if 'object_types' in schema_data:
                    object_types = schema_data['object_types']
            
            # 解析动作规则
            if files_content.get('actions'):
                actions_data = json.loads(files_content['actions'])
                if 'actions' in actions_data:
                    action_rules = actions_data['actions']
            
            # 解析种子数据
            if files_content.get('seed'):
                seed_json = json.loads(files_content['seed'])
                if 'entities' in seed_json:
                    seed_data = [{'name': e.get('id', '未知')} for e in seed_json['entities'][:10]]
        except Exception as e:
            logger.warning(f"解析侧边栏数据失败: {e}")
        
        return render_template('studio.html',
                             current_domain=current_domain,
                             current_domain_name=current_domain_info.get("name", "未知领域"),
                             domain_color=current_domain_info.get("color", "#6b7280"),
                             domain_icon=current_domain_info.get("icon", "cube"),
                             object_types=object_types,
                             action_rules=action_rules,
                             seed_data=seed_data,
                             graph_elements=[])  # 图谱数据将通过HTMX加载
    
    # 4. 测试页面
    @app.route('/test')
    def test_page():
        """测试页面"""
        return render_template('test.html')
    
    @app.route('/simple-test')
    def simple_test():
        """简单测试页面"""
        return render_template('simple_test.html')
    
    @app.route('/editor-simple')
    def editor_simple():
        """简化编辑器页面"""
        return render_template('editor_simple.html')
    
    # 5. 测试API
    @app.route('/api/test')
    def api_test():
        """测试API"""
        return "<div class='p-4 bg-green-100 rounded'>HTMX 请求成功！时间: " + datetime.now().strftime("%H:%M:%S") + "</div>"
    
    # 6. 静态文件服务
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        """提供静态文件"""
        from pathlib import Path
        BASE_DIR = Path(__file__).parent.parent.parent  # backend目录
        return send_from_directory(BASE_DIR / 'static', filename)
    
    # 7. 性能监控端点
    @app.route('/api/performance/metrics', methods=['POST'])
    def receive_performance_metrics():
        """接收前端性能指标数据"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "没有提供数据"}), 400
            
            # 记录性能数据
            logger.info(f"性能指标接收: {data.get('url', '未知URL')}")
            
            # 提取关键指标
            metrics = data.get('metrics', {})
            page_load = metrics.get('pageLoad', {})
            
            if page_load:
                logger.info(f"页面加载时间: {page_load.get('total', 0)}ms")
                
                # 检查是否超过阈值
                if page_load.get('total', 0) > 3000:  # 3秒阈值
                    logger.warning(f"页面加载时间超过阈值: {page_load.get('total', 0)}ms")
            
            # 记录慢速资源
            slow_resources = metrics.get('resourceTiming', [])
            slow_resources = [r for r in slow_resources if r.get('duration', 0) > 1000]
            
            if slow_resources:
                logger.warning(f"发现 {len(slow_resources)} 个慢速资源")
                for resource in slow_resources[:3]:  # 只记录前3个
                    logger.warning(f"  慢速资源: {resource.get('name', '未知')} - {resource.get('duration', 0)}ms")
            
            return jsonify({"status": "success", "message": "性能数据已接收"})
            
        except Exception as e:
            logger.error(f"性能数据接收失败: {e}")
            return jsonify({"error": f"性能数据接收失败: {str(e)}"}), 500
    
    logger.info("页面路由注册完成")
    return app