"""
世界仿真路由模块
统一管理所有世界仿真相关的API路由
"""

import logging
from flask import request, jsonify
from backend.core.request_context import RequestContext, DomainContextManager
from backend.core.exceptions import DomainNotFoundError, Neo4jError
from backend.services.neo4j_loader import Neo4jLoader

logger = logging.getLogger(__name__)

def register_world_routes(app, domain_manager):
    """注册世界仿真路由"""
    
    # 1. 预览世界图谱
    @app.route('/api/v1/world/preview', methods=['GET'])
    def preview_world():
        """预览世界图谱"""
        try:
            node_type = request.args.get('type', None)
            limit = int(request.args.get('limit', 100))
            domain = request.args.get('domain', RequestContext.get_current_domain())
            
            loader = Neo4jLoader()
            graph_data = loader.query_graph(node_type=node_type, limit=limit, domain=domain)
            
            return jsonify({
                "status": "success",
                "data": graph_data
            })
            
        except Neo4jError as e:
            logger.error(f"世界预览失败: {e.message}")
            return jsonify(e.to_dict()), 500
        except Exception as e:
            logger.error(f"世界预览失败: {e}")
            return jsonify({"error": f"世界预览失败: {str(e)}"}), 500
    
    # 2. 验证图谱连通性
    @app.route('/api/v1/world/validate-connectivity', methods=['GET'])
    def validate_connectivity():
        """验证图谱连通性"""
        try:
            loader = Neo4jLoader()
            
            if loader.neo4j is None:
                return jsonify({
                    "status": "warning",
                    "message": "Neo4j 未连接，无法检查连通性"
                })
            
            result = loader.query_graph(limit=10)
            isolated_nodes = [
                {"id": node.get("id"), "node_type": node.get("type")}
                for node in result.get("nodes", [])
                if not any(
                    link["source"] == node.get("id") or link["target"] == node.get("id")
                    for link in result.get("links", [])
                )
            ]
            
            if isolated_nodes:
                return jsonify({
                    "status": "warning",
                    "message": f"发现 {len(isolated_nodes)} 个孤岛节点",
                    "isolated_nodes": isolated_nodes
                })
            else:
                return jsonify({
                    "status": "success",
                    "message": "图谱连通性良好"
                })
                
        except Exception as e:
            logger.error(f"连通性验证失败: {e}")
            return jsonify({"error": f"连通性验证失败: {str(e)}"}), 500
    
    # 3. 重置世界
    @app.route('/api/v1/world/reset', methods=['POST'])
    def reset_world():
        """重置世界到初始状态"""
        try:
            data = request.json or {}
            domain = data.get('domain', RequestContext.get_current_domain())
            
            # 验证领域访问权限
            if not DomainContextManager.validate_domain_access(domain, domain_manager.list_domains()):
                raise DomainNotFoundError(domain)
            
            # 获取指定领域的seed数据
            files_content = domain_manager.get_domain_files(domain)
            seed_content = files_content.get("seed", "")
            
            if not seed_content:
                return jsonify({
                    "status": "error",
                    "message": "没有初始世界数据"
                }), 400
            
            # 清空Neo4j并重新加载
            loader = Neo4jLoader()
            loader.delete_all_nodes()
            
            # 重新加载seed数据
            stats = loader.load_to_neo4j(seed_content, clear_existing=False)
            
            return jsonify({
                "status": "success",
                "message": "世界重置成功",
                "stats": stats
            })
            
        except DomainNotFoundError as e:
            logger.error(f"领域不存在: {e.domain_name}")
            return jsonify(e.to_dict()), 404
        except Neo4jError as e:
            logger.error(f"世界重置失败: {e.message}")
            return jsonify(e.to_dict()), 500
        except Exception as e:
            logger.error(f"世界重置失败: {e}")
            return jsonify({"error": f"世界重置失败: {str(e)}"}), 500
    
    # 4. 启动仿真
    @app.route('/api/v1/world/launch', methods=['POST'])
    def launch_simulation():
        """启动领域仿真"""
        try:
            data = request.json or {}
            domain_name = data.get('domain', RequestContext.get_current_domain())
            
            # 验证领域访问权限
            if not DomainContextManager.validate_domain_access(domain_name, domain_manager.list_domains()):
                raise DomainNotFoundError(domain_name)
            
            # 获取当前领域配置
            files_content = domain_manager.get_domain_files(domain_name)
            
            logger.info(f"Launch simulation for domain: {domain_name}")
            logger.info(f"Files content keys: {list(files_content.keys())}")
            
            # 检查是否有文件内容
            has_content = False
            for file_type, content in files_content.items():
                if content and content.strip():
                    has_content = True
                    logger.info(f"{file_type}: {len(content)} chars")
                    break
            
            if not has_content:
                logger.info(f"No content found for domain: {domain_name}")
            
            # 这里可以添加仿真启动逻辑
            # 例如：启动独立的仿真进程、初始化仿真环境等
            
            return jsonify({
                "status": "success",
                "message": f"仿真启动成功",
                "domain_name": domain_name,
                "has_files": has_content
            })
            
        except DomainNotFoundError as e:
            logger.error(f"领域不存在: {e.domain_name}")
            return jsonify(e.to_dict()), 404
        except Exception as e:
            logger.error(f"仿真启动失败: {e}")
            return jsonify({
                "status": "error",
                "error": f"仿真启动失败: {str(e)}"
            }), 500
    
    # 5. 兼容性路由
    @app.route('/api/launch_simulation', methods=['POST'])
    def launch_simulation_compat():
        """启动领域仿真 (兼容性路由)"""
        return launch_simulation()
    
    # 6. 图谱数据服务 (保留原有API兼容性)
    @app.route('/api/graph', methods=['GET'])
    def get_graph():
        """获取图谱数据 (兼容性路由)"""
        try:
            node_type = request.args.get('type', None)
            limit = int(request.args.get('limit', 100))
            
            loader = Neo4jLoader()
            graph_data = loader.query_graph(node_type=node_type, limit=limit)
            
            return jsonify(graph_data)
            
        except Exception as e:
            logger.error(f"获取图谱失败: {e}")
            return jsonify({
                "status": "error",
                "message": str(e),
                "nodes": [],
                "links": []
            }), 500
    
    @app.route('/api/graph/stats', methods=['GET'])
    def get_graph_stats():
        """获取图谱统计 (兼容性路由)"""
        try:
            loader = Neo4jLoader()
            stats = loader.get_graph_stats()
            return jsonify(stats)
        except Exception as e:
            logger.error(f"获取图谱统计失败: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    
    logger.info("世界仿真路由注册完成")
    return app