"""
领域管理路由模块
统一管理所有领域相关的API路由
"""

import json
import logging
from flask import request, jsonify
from backend.core.request_context import RequestContext
from backend.core.exceptions import DomainNotFoundError, PathTraversalError
from backend.core.transaction_manager import save_domain_config_atomic
from backend.services.domain_manager_enhanced import EnhancedDomainManager

logger = logging.getLogger(__name__)

def register_domain_routes(app, domain_manager: EnhancedDomainManager, DOMAIN_PACKS):
    """注册领域管理路由"""
    
    # 1. 获取所有领域
    @app.route('/api/v1/domains', methods=['GET'])
    def list_domains_api():
        """获取所有领域"""
        try:
            available_domains = domain_manager.list_domains()
            
            domains = []
            for domain_id in available_domains:
                if domain_id in DOMAIN_PACKS:
                    domain_info = DOMAIN_PACKS[domain_id]
                    domains.append({
                        "id": domain_id,
                        "name": domain_info["name"],
                        "description": domain_info["description"],
                        "color": domain_info["color"],
                        "icon": domain_info["icon"]
                    })
            
            return jsonify({
                "status": "success",
                "domains": domains,
                "current_domain": RequestContext.get_current_domain()
            })
            
        except Exception as e:
            logger.error(f"获取领域列表失败: {e}")
            return jsonify({"error": f"获取领域列表失败: {str(e)}"}), 500
    
    # 2. 切换领域
    @app.route('/api/v1/domains/<domain_name>/switch', methods=['POST'])
    def switch_domain_api(domain_name):
        """切换领域"""
        try:
            if domain_name not in DOMAIN_PACKS:
                return jsonify({"error": f"未知领域: {domain_name}"}), 404
            
            success = domain_manager.activate_domain(domain_name)
            
            if success:
                RequestContext.set_current_domain(domain_name)
                
                return jsonify({
                    "status": "success",
                    "message": f"已切换到 {DOMAIN_PACKS[domain_name]['name']}",
                    "domain": domain_name
                })
            else:
                return jsonify({"error": f"切换领域失败: {domain_name}"}), 500
                
        except Exception as e:
            logger.error(f"切换领域失败: {e}")
            return jsonify({"error": f"切换领域失败: {str(e)}"}), 500
    
    # 3. 获取领域配置
    @app.route('/api/v1/domains/<domain_name>/config', methods=['GET'])
    def get_domain_config_api(domain_name):
        """获取领域配置"""
        try:
            # 路径遍历防护
            if domain_name not in DOMAIN_PACKS:
                raise PathTraversalError(domain_name, "Domain not in allowed list")
            
            files_content = domain_manager.get_domain_files(domain_name)
            return jsonify({
                "status": "success",
                "config": files_content
            })
            
        except PathTraversalError as e:
            logger.error(f"路径遍历检测: {e.details.get('path')}")
            return jsonify(e.to_dict()), 403
        except Exception as e:
            logger.error(f"获取领域配置失败: {e}")
            return jsonify({"error": f"获取领域配置失败: {str(e)}"}), 500
    
    # 4. 保存领域配置
    @app.route('/api/v1/domains/<domain_name>/save', methods=['POST'])
    def save_domain_config_api(domain_name):
        """保存领域配置 - 原子性保存"""
        try:
            # 路径遍历防护
            if domain_name not in DOMAIN_PACKS:
                raise PathTraversalError(domain_name, "Domain not in allowed list")
            
            data = request.json
            if not data:
                return jsonify({"error": "没有提供数据"}), 400
            
            # 提取要保存的文件
            file_types = []
            new_contents = {}
            
            # 导入XML转换器
            try:
                from backend.core.xml_converter import XMLConverter
            except ImportError:
                logger.error("XML转换器导入失败")
                return jsonify({"error": "XML转换器不可用"}), 500
            
            for file_type in ["schema", "seed", "actions", "patterns"]:
                content = data.get(file_type, "")
                if content:
                    try:
                        # 尝试解析JSON内容
                        json_data = json.loads(content)
                        
                        # 根据文件类型转换为XML
                        if file_type == "schema":
                            # 本体数据转换为object_types.xml
                            xml_content = XMLConverter.convert_ontology_to_xml(json_data, domain_name)
                        elif file_type == "seed":
                            # 种子数据转换为seed_data.xml
                            xml_content = XMLConverter.convert_seed_data_to_xml(json_data, domain_name)
                        else:
                            # 其他文件类型保持原样
                            xml_content = content
                        
                        file_types.append(file_type)
                        new_contents[file_type] = xml_content
                        
                    except json.JSONDecodeError:
                        # 如果不是JSON，保持原样
                        file_types.append(file_type)
                        new_contents[file_type] = content
                    except Exception as e:
                        logger.error(f"处理{file_type}文件失败: {e}")
                        return jsonify({"error": f"处理{file_type}文件失败: {str(e)}"}), 500
            
            if not file_types:
                return jsonify({"error": "没有要保存的文件内容"}), 400
            
            # 判断是否需要同步到 Neo4j
            sync_to_neo4j = data.get('sync_to_neo4j', False)
            from backend.services.neo4j_loader import Neo4jLoader
            neo4j_loader_instance = Neo4jLoader() if sync_to_neo4j else None
            
            # 使用原子性保存
            result = save_domain_config_atomic(
                domain_manager=domain_manager,
                domain_name=domain_name,
                file_types=file_types,
                new_contents=new_contents,
                sync_to_neo4j=sync_to_neo4j,
                neo4j_loader=neo4j_loader_instance
            )
            
            return jsonify(result)
            
        except PathTraversalError as e:
            logger.error(f"路径遍历检测: {e.details.get('path')}")
            return jsonify(e.to_dict()), 403
        except Exception as e:
            logger.error(f"保存领域配置失败: {e}")
            return jsonify({"error": f"保存领域配置失败: {str(e)}"}), 500
    
    # 5. 兼容性路由 - 支持旧版本前端
    @app.route('/api/domains', methods=['GET'])
    def list_domains_compat():
        """获取所有可用领域模组 (兼容性路由)"""
        try:
            available_domains = domain_manager.list_domains()
            
            domains = []
            for domain_id in available_domains:
                if domain_id in DOMAIN_PACKS:
                    domain_info = DOMAIN_PACKS[domain_id]
                    domains.append({
                        "id": domain_id,
                        "name": domain_info["name"],
                        "description": domain_info["description"],
                        "color": domain_info["color"],
                        "icon": domain_info["icon"],
                        "exists": True
                    })
            
            return jsonify({
                "status": "success",
                "domains": domains,
                "current_domain": RequestContext.get_current_domain()
            })
            
        except Exception as e:
            logger.error(f"获取领域列表失败: {e}")
            return jsonify({"error": f"获取领域列表失败: {str(e)}"}), 500
    
    @app.route('/api/domains/<domain_name>', methods=['POST'])
    def switch_domain_compat(domain_name):
        """切换领域模组 (兼容性路由)"""
        try:
            if domain_name not in DOMAIN_PACKS:
                return jsonify({"error": f"未知领域: {domain_name}"}), 404
            
            success = domain_manager.activate_domain(domain_name)
            
            if success:
                RequestContext.set_current_domain(domain_name)
                
                return jsonify({
                    "status": "success",
                    "message": f"已切换到 {DOMAIN_PACKS[domain_name]['name']}",
                    "domain": domain_name,
                    "domain_info": DOMAIN_PACKS[domain_name]
                })
            else:
                return jsonify({"error": f"切换领域失败: {domain_name}"}), 500
                
        except Exception as e:
            logger.error(f"切换领域失败: {e}")
            return jsonify({"error": f"切换领域失败: {str(e)}"}), 500
    
    @app.route('/api/domains/<domain_name>/config', methods=['GET'])
    def get_domain_config_compat(domain_name):
        """获取领域模组配置 (兼容性路由)"""
        try:
            # 路径遍历防护
            if domain_name not in DOMAIN_PACKS:
                raise PathTraversalError(domain_name, "Domain not in allowed list")
            
            files_content = domain_manager.get_domain_files(domain_name)
            return jsonify({
                "status": "success",
                "config": files_content
            })
            
        except PathTraversalError as e:
            logger.error(f"路径遍历检测: {e.details.get('path')}")
            return jsonify(e.to_dict()), 403
        except Exception as e:
            logger.error(f"获取领域配置失败: {e}")
            return jsonify({"error": f"获取领域配置失败: {str(e)}"}), 500
    
    @app.route('/api/domains/<domain_name>/save', methods=['POST'])
    def save_domain_config_compat(domain_name):
        """保存领域模组配置 (兼容性路由)"""
        return save_domain_config_api(domain_name)
    
    logger.info("领域管理路由注册完成")
    return app