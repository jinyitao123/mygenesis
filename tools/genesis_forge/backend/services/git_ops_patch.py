"""
GitOpsManager补丁 - 添加缺失的API方法
"""
import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

def add_git_rollback_method():
    """为GitOpsManager添加回滚方法"""
    
    git_ops_file = r"E:\Documents\MyGame\tools\genesis_forge\backend\services\git_ops.py"
    
    if not os.path.exists(git_ops_file):
        print(f"找不到GitOps文件: {git_ops_file}")
        return False
    
    with open(git_ops_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找restore_ontology_snapshot方法的结束位置
    restore_end = content.find('def restore_ontology_snapshot(self,')
    if restore_end == -1:
        print("找不到restore_ontology_snapshot方法")
        return False
    
    # 找到方法结束位置（下一个def或文件结束）
    next_def = content.find('\n    def ', restore_end + 1)
    if next_def == -1:
        next_def = len(content)
    
    # 在restore_ontology_snapshot方法后添加rollback方法
    rollback_method = '''
    def rollback_to_commit(self, commit_id: str = "HEAD~1") -> Dict[str, Any]:
        """
        回滚到指定提交
        
        Args:
            commit_id: 提交ID或引用，默认为上一个提交
            
        Returns:
            回滚结果
        """
        result = {
            "success": False,
            "message": "",
            "commit_id": commit_id,
            "previous_head": "",
            "new_head": ""
        }
        
        try:
            # 获取当前HEAD
            success, output = self._run_git_command(["rev-parse", "HEAD"])
            if not success:
                result["message"] = f"获取当前HEAD失败: {output}"
                return result
            
            result["previous_head"] = output.strip()
            
            # 执行回滚
            success, output = self._run_git_command(["reset", "--hard", commit_id])
            if not success:
                result["message"] = f"回滚失败: {output}"
                return result
            
            # 获取新的HEAD
            success, output = self._run_git_command(["rev-parse", "HEAD"])
            if success:
                result["new_head"] = output.strip()
            
            result["success"] = True
            result["message"] = f"成功回滚到提交 {commit_id}"
            result["output"] = output
            
            logger.info(f"Git回滚完成: {commit_id}")
            
        except Exception as e:
            result["message"] = f"回滚过程出错: {str(e)}"
            logger.error(f"Git回滚失败: {e}")
        
        return result
    
    def get_branches(self) -> Dict[str, Any]:
        """
        获取所有分支
        
        Returns:
            分支列表
        """
        result = {
            "success": False,
            "message": "",
            "branches": [],
            "current": ""
        }
        
        try:
            # 获取所有分支
            success, output = self._run_git_command(["branch", "-a"])
            if not success:
                result["message"] = f"获取分支失败: {output}"
                return result
            
            # 解析分支输出
            branches = []
            for line in output.split('\\n'):
                line = line.strip()
                if line:
                    # 移除当前分支标记
                    if line.startswith('* '):
                        line = line[2:]
                        result["current"] = line
                    branches.append(line)
            
            result["success"] = True
            result["branches"] = branches
            result["message"] = f"找到 {len(branches)} 个分支"
            
        except Exception as e:
            result["message"] = f"获取分支过程出错: {str(e)}"
            logger.error(f"获取分支失败: {e}")
        
        return result
    
    def checkout_branch(self, branch_name: str) -> Dict[str, Any]:
        """
        切换到指定分支
        
        Args:
            branch_name: 分支名称
            
        Returns:
            切换结果
        """
        result = {
            "success": False,
            "message": "",
            "branch": branch_name,
            "previous_branch": ""
        }
        
        try:
            # 获取当前分支
            success, output = self._run_git_command(["branch", "--show-current"])
            if success:
                result["previous_branch"] = output.strip()
            
            # 切换到目标分支
            success, output = self._run_git_command(["checkout", branch_name])
            if not success:
                result["message"] = f"切换分支失败: {output}"
                return result
            
            result["success"] = True
            result["message"] = f"成功切换到分支 {branch_name}"
            
            logger.info(f"切换到分支: {branch_name}")
            
        except Exception as e:
            result["message"] = f"切换分支过程出错: {str(e)}"
            logger.error(f"切换分支失败: {e}")
        
        return result
'''
    
    # 插入新方法
    new_content = content[:next_def] + rollback_method + content[next_def:]
    
    with open(git_ops_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("已添加Git回滚和分支管理方法到GitOpsManager")
    return True

def add_git_api_endpoints():
    """在app_studio.py中添加Git API端点"""
    
    app_file = r"E:\Documents\MyGame\tools\genesis_forge\backend\api\app_studio.py"
    
    if not os.path.exists(app_file):
        print(f"找不到应用文件: {app_file}")
        return False
    
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找现有的Git路由
    git_routes_end = content.find('@app.route(\'/api/v1/git/hot-reload\'')
    if git_routes_end == -1:
        print("找不到现有的Git路由")
        return False
    
    # 找到hot-reload路由的结束位置
    route_end = content.find('def hot_reload():', git_routes_end)
    if route_end == -1:
        route_end = git_routes_end
    
    # 添加新的Git API端点
    new_routes = '''
@app.route('/api/v1/git/rollback', methods=['POST'])
def git_rollback():
    """回滚到指定提交"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "没有提供数据"}), 400
        
        commit_id = data.get('commit_id', 'HEAD~1')
        
        result = git_ops.rollback_to_commit(commit_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({"error": result['message']}), 500
            
    except Exception as e:
        logger.error(f"Git回滚失败: {e}")
        return jsonify({"error": f"Git回滚失败: {str(e)}"}), 500

@app.route('/api/v1/git/branches', methods=['GET'])
def git_branches():
    """获取所有分支"""
    try:
        result = git_ops.get_branches()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({"error": result['message']}), 500
            
    except Exception as e:
        logger.error(f"获取分支失败: {e}")
        return jsonify({"error": f"获取分支失败: {str(e)}"}), 500

@app.route('/api/v1/git/checkout', methods=['POST'])
def git_checkout():
    """切换到指定分支"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "没有提供数据"}), 400
        
        branch_name = data.get('branch_name', '')
        if not branch_name:
            return jsonify({"error": "没有提供分支名称"}), 400
        
        result = git_ops.checkout_branch(branch_name)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({"error": result['message']}), 500
            
    except Exception as e:
        logger.error(f"切换分支失败: {e}")
        return jsonify({"error": f"切换分支失败: {str(e)}"}), 500
'''
    
    # 插入新路由
    new_content = content[:route_end] + new_routes + content[route_end:]
    
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("已添加Git API端点到app_studio.py")
    return True

def main():
    """主函数"""
    print("Git API端点补丁工具")
    print("=" * 60)
    
    print("\n1. 添加GitOpsManager方法...")
    if add_git_rollback_method():
        print("   ✓ 成功添加GitOpsManager方法")
    else:
        print("   ✗ 添加GitOpsManager方法失败")
    
    print("\n2. 添加Git API端点...")
    if add_git_api_endpoints():
        print("   ✓ 成功添加Git API端点")
    else:
        print("   ✗ 添加Git API端点失败")
    
    print("\n" + "=" * 60)
    print("补丁应用完成!")
    print("\n需要重启Flask服务以使更改生效")
    print("新增的API端点:")
    print("  - POST /api/v1/git/rollback")
    print("  - GET  /api/v1/git/branches")
    print("  - POST /api/v1/git/checkout")

if __name__ == "__main__":
    main()