"""
Git操作路由模块
统一管理所有Git相关的API路由
"""

import logging
from flask import request, jsonify
from backend.core.request_context import RequestContext, DomainContextManager
from backend.core.exceptions import DomainNotFoundError

logger = logging.getLogger(__name__)

def register_git_routes(app, git_ops, domain_manager):
    """注册Git操作路由"""
    
    # 1. 获取Git状态
    @app.route('/api/v1/git/status', methods=['GET'])
    def git_status():
        """获取Git状态"""
        try:
            status = git_ops.get_git_status()
            
            return jsonify({
                "status": "success",
                "data": status
            })
            
        except Exception as e:
            logger.error(f"获取Git状态失败: {e}")
            return jsonify({"error": f"获取Git状态失败: {str(e)}"}), 500
    
    # 2. 创建Git提交
    @app.route('/api/v1/git/commit', methods=['POST'])
    def git_commit():
        """创建Git提交"""
        try:
            data = request.json
            if not data:
                return jsonify({"error": "没有提供数据"}), 400
            
            message = data.get('message', '')
            files = data.get('files', None)
            skip_validation = data.get('skip_validation', False)
            
            if not message:
                return jsonify({"error": "没有提供提交消息"}), 400
            
            result = git_ops.create_commit(message, files, skip_validation)
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"创建提交失败: {e}")
            return jsonify({"error": f"创建提交失败: {str(e)}"}), 500
    
    # 3. 触发热重载
    @app.route('/api/v1/git/hot-reload', methods=['POST'])
    def hot_reload():
        """触发热重载"""
        try:
            data = request.json or {}
            domain_name = data.get('domain', RequestContext.get_current_domain())
            
            # 验证领域访问权限
            if not DomainContextManager.validate_domain_access(domain_name, domain_manager.list_domains()):
                raise DomainNotFoundError(domain_name)
            
            result = git_ops.trigger_hot_reload(domain_name)
            
            return jsonify(result)
            
        except DomainNotFoundError as e:
            logger.error(f"领域不存在: {e.domain_name}")
            return jsonify(e.to_dict()), 404
        except Exception as e:
            logger.error(f"热重载失败: {e}")
            return jsonify({"error": f"热重载失败: {str(e)}"}), 500
    
    # 4. 回滚到指定提交
    @app.route('/api/v1/git/rollback', methods=['POST'])
    def git_rollback():
        """回滚到指定提交"""
        try:
            data = request.json
            if not data:
                return jsonify({"error": "没有提供数据"}), 400
            
            commit_id = data.get('commit_id', 'HEAD~1')
            
            # 执行Git回滚
            success, output = git_ops._run_git_command(['reset', '--hard', commit_id])
            
            if success:
                return jsonify({
                    "success": True,
                    "message": f"已回滚到提交 {commit_id}",
                    "output": output
                })
            else:
                return jsonify({"error": f"回滚失败: {output}"}), 500
                
        except Exception as e:
            logger.error(f"Git回滚失败: {e}")
            return jsonify({"error": f"Git回滚失败: {str(e)}"}), 500
    
    # 5. 获取所有分支
    @app.route('/api/v1/git/branches', methods=['GET'])
    def git_branches():
        """获取所有分支"""
        try:
            success, output = git_ops._run_git_command(['branch', '-a'])
            if success:
                branches = [b.strip() for b in output.split('\n') if b.strip()]
                return jsonify({
                    "success": True,
                    "branches": branches
                })
            else:
                return jsonify({"error": f"获取分支失败: {output}"}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    # 6. 获取文件差异
    @app.route('/api/v1/git/diff', methods=['GET'])
    def git_diff():
        """获取文件差异"""
        try:
            # 获取特定文件的差异或所有文件的差异
            file_path = request.args.get('file', '')
            
            if file_path:
                success, output = git_ops._run_git_command(['diff', 'HEAD', '--', file_path])
            else:
                success, output = git_ops._run_git_command(['diff', 'HEAD'])
            
            if success:
                return jsonify({
                    "success": True,
                    "diff": output
                })
            else:
                return jsonify({"error": f"获取差异失败: {output}"}), 500
        except Exception as e:
            logger.error(f"Git差异获取失败: {e}")
            return jsonify({"error": f"Git差异获取失败: {str(e)}"}), 500
    
    # 7. 撤销更改
    @app.route('/api/v1/git/revert', methods=['POST'])
    def git_revert():
        """撤销更改"""
        try:
            data = request.json
            if not data:
                return jsonify({"error": "没有提供数据"}), 400
            
            file_path = data.get('file_path', '')
            
            if not file_path:
                return jsonify({"error": "需要提供文件路径"}), 400
            
            # 执行Git撤销
            success, output = git_ops._run_git_command(['checkout', '--', file_path])
            
            if success:
                return jsonify({
                    "success": True,
                    "message": f"已撤销文件 {file_path} 的更改",
                    "output": output
                })
            else:
                return jsonify({"error": f"撤销失败: {output}"}), 500
                
        except Exception as e:
            logger.error(f"Git撤销失败: {e}")
            return jsonify({"error": f"Git撤销失败: {str(e)}"}), 500
    
    logger.info("Git操作路由注册完成")
    return app