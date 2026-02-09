"""
Git-Ops 开发流程支持

基于PRP文档的流程模型架构：
Draft (UI) -> Validate (Schema) -> Commit (Git) -> Hot Reload (Engine)

核心流程：
1. 本体开发流程 (Ontology Dev Flow)
2. 实时调试流程 (Live Ops Flow)
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import subprocess
import shutil

from backend.core.models import OntologyModel
from backend.core.validation_engine import ValidationEngine

logger = logging.getLogger(__name__)


class GitOpsError(Exception):
    """Git-Ops错误异常"""
    pass


class GitOpsManager:
    """Git-Ops流程管理器"""
    
    def __init__(self, project_root: str, validation_engine: ValidationEngine):
        self.project_root = Path(project_root)
        self.validation_engine = validation_engine
        self.repo_path = self.project_root
        self.domains_dir = self.project_root / "domains"
        
        # 确保Git仓库初始化
        self._ensure_git_repo()
    
    def _ensure_git_repo(self):
        """确保Git仓库已初始化"""
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            logger.info("初始化Git仓库...")
            self._run_git_command(["init"])
            
            # 创建.gitignore
            gitignore_content = """# Genesis Studio Git Ignore

# 临时文件
*.tmp
*.temp
*.log
*.pid

# 开发环境
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# 运行时数据
*.db
*.db-journal
*.sqlite
*.sqlite3

# 备份文件
*.bak
*.backup
*.old

# IDE文件
.vscode/
.idea/
*.swp
*.swo

# 操作系统文件
.DS_Store
Thumbs.db

# 依赖目录
node_modules/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# 测试覆盖率
.coverage
htmlcov/

# 构建产物
dist/
build/
*.egg-info/
"""
            
            gitignore_path = self.repo_path / ".gitignore"
            gitignore_path.write_text(gitignore_content, encoding='utf-8')
            
            # 初始提交
            self._run_git_command(["add", "."])
            self._run_git_command(["commit", "-m", "Initial commit: Genesis Studio project"])
            
            logger.info("Git仓库初始化完成")
    
    def _run_git_command(self, args: List[str], workdir: Optional[Path] = None) -> Tuple[bool, str]:
        """
        运行Git命令
        
        Args:
            args: Git命令参数
            workdir: 工作目录
            
        Returns:
            (是否成功, 输出信息)
        """
        try:
            cmd = ["git"] + args
            workdir = workdir or self.repo_path
            
            result = subprocess.run(
                cmd,
                cwd=str(workdir),
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                logger.error(f"Git命令失败: {' '.join(cmd)} - {error_msg}")
                return False, error_msg
                
        except Exception as e:
            logger.error(f"执行Git命令异常: {e}")
            return False, str(e)
    
    def get_git_status(self) -> Dict[str, Any]:
        """获取Git状态"""
        status = {
            "branch": "",
            "clean": True,
            "changes": {
                "staged": [],
                "unstaged": [],
                "untracked": []
            },
            "remote": {
                "connected": False,
                "ahead": 0,
                "behind": 0
            }
        }
        
        # 获取当前分支
        success, output = self._run_git_command(["branch", "--show-current"])
        if success:
            status["branch"] = output
        
        # 获取状态摘要
        success, output = self._run_git_command(["status", "--porcelain"])
        if success:
            lines = output.split('\n') if output else []
            
            for line in lines:
                if line:
                    # 解析状态代码
                    # XY: X=暂存区状态, Y=工作区状态
                    status_code = line[:2]
                    file_path = line[3:]
                    
                    if status_code == '??':
                        status["changes"]["untracked"].append(file_path)
                    elif status_code[0] != ' ':
                        status["changes"]["staged"].append(file_path)
                    elif status_code[1] != ' ':
                        status["changes"]["unstaged"].append(file_path)
            
            status["clean"] = len(status["changes"]["staged"]) == 0 and \
                             len(status["changes"]["unstaged"]) == 0 and \
                             len(status["changes"]["untracked"]) == 0
        
        # 检查远程状态
        success, output = self._run_git_command(["remote", "-v"])
        if success and output:
            status["remote"]["connected"] = True
            
            # 检查与远程的差异
            success, output = self._run_git_command(["rev-list", "--count", "HEAD..@{u}"])
            if success:
                status["remote"]["behind"] = int(output) if output else 0
            
            success, output = self._run_git_command(["rev-list", "--count", "@{u}..HEAD"])
            if success:
                status["remote"]["ahead"] = int(output) if output else 0
        
        return status
    
    def get_commit_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取提交历史"""
        commits = []
        
        # 使用自定义格式获取提交信息
        format_str = "%H|%an|%ae|%ad|%s"
        success, output = self._run_git_command([
            "log",
            f"--pretty=format:{format_str}",
            f"--max-count={limit}",
            "--date=iso"
        ])
        
        if success and output:
            for line in output.split('\n'):
                if line:
                    parts = line.split('|', 4)
                    if len(parts) == 5:
                        commit = {
                            "hash": parts[0],
                            "author_name": parts[1],
                            "author_email": parts[2],
                            "date": parts[3],
                            "message": parts[4],
                            "short_hash": parts[0][:7]
                        }
                        commits.append(commit)
        
        return commits
    
    def create_commit(self, 
                     message: str,
                     files: Optional[List[str]] = None,
                     skip_validation: bool = False) -> Dict[str, Any]:
        """
        创建提交
        
        Args:
            message: 提交消息
            files: 要提交的文件列表（None表示所有更改）
            skip_validation: 是否跳过验证
            
        Returns:
            提交结果
        """
        result = {
            "success": False,
            "commit_id": None,
            "message": "",
            "validation_errors": []
        }
        
        try:
            # 1. 验证更改（如果不跳过）
            if not skip_validation:
                validation_errors = self._validate_changes(files)
                if validation_errors:
                    result["validation_errors"] = validation_errors
                    result["message"] = "验证失败，无法提交"
                    return result
            
            # 2. 添加文件到暂存区
            if files:
                for file_path in files:
                    success, output = self._run_git_command(["add", file_path])
                    if not success:
                        result["message"] = f"添加文件失败: {file_path} - {output}"
                        return result
            else:
                success, output = self._run_git_command(["add", "."])
                if not success:
                    result["message"] = f"添加所有文件失败: {output}"
                    return result
            
            # 3. 创建提交
            success, output = self._run_git_command(["commit", "-m", message])
            if not success:
                result["message"] = f"提交失败: {output}"
                return result
            
            # 4. 获取提交ID
            success, output = self._run_git_command(["rev-parse", "HEAD"])
            if success:
                result["commit_id"] = output.strip()
            
            result["success"] = True
            result["message"] = "提交成功"
            
            logger.info(f"创建提交: {message} ({result['commit_id']})")
            
        except Exception as e:
            result["message"] = f"提交过程异常: {str(e)}"
            logger.error(f"创建提交失败: {e}")
        
        return result
    
    def _validate_changes(self, files: Optional[List[str]] = None) -> List[str]:
        """验证更改"""
        errors = []
        
        # 获取状态以确定哪些文件有更改
        status = self.get_git_status()
        
        # 确定要验证的文件
        files_to_validate = []
        if files:
            files_to_validate = files
        else:
            # 验证所有更改的文件
            files_to_validate = (
                status["changes"]["staged"] +
                status["changes"]["unstaged"] +
                status["changes"]["untracked"]
            )
        
        # 过滤出本体文件进行验证
        ontology_files = []
        for file_path in files_to_validate:
            path = Path(file_path)
            if path.suffix in ['.json', '.xml'] and 'domains/' in str(path):
                ontology_files.append(file_path)
        
        # 验证每个本体文件
        for file_path in ontology_files:
            full_path = self.repo_path / file_path
            
            # 确定文件类型
            file_type = self._infer_file_type(file_path)
            
            if file_type:
                valid, file_errors = self.validation_engine.validate_ontology_file(full_path, file_type)
                if not valid:
                    errors.extend([f"{file_path}: {err}" for err in file_errors])
        
        return errors
    
    def _infer_file_type(self, file_path: str) -> Optional[str]:
        """推断文件类型"""
        path = Path(file_path)
        
        # 检查是否在domains目录下
        if 'domains/' not in str(path):
            return None
        
        # 根据文件名推断类型
        filename = path.name
        if filename == 'schema.json':
            return 'schema'
        elif filename == 'seed.json':
            return 'seed'
        elif filename == 'actions.json':
            return 'actions'
        elif filename == 'patterns.json':
            return 'patterns'
        elif filename == 'config.json':
            return 'config'
        
        return None
    
    def create_branch(self, branch_name: str, from_branch: str = "main") -> Dict[str, Any]:
        """创建分支"""
        result = {
            "success": False,
            "message": "",
            "branch_name": branch_name
        }
        
        try:
            # 检查分支是否存在
            success, output = self._run_git_command(["branch", "--list", branch_name])
            if success and output.strip():
                result["message"] = f"分支已存在: {branch_name}"
                return result
            
            # 创建分支
            success, output = self._run_git_command(["checkout", "-b", branch_name, from_branch])
            if success:
                result["success"] = True
                result["message"] = f"分支创建成功: {branch_name}"
                logger.info(f"创建分支: {branch_name} from {from_branch}")
            else:
                result["message"] = f"分支创建失败: {output}"
                
        except Exception as e:
            result["message"] = f"创建分支异常: {str(e)}"
            logger.error(f"创建分支失败: {e}")
        
        return result
    
    def switch_branch(self, branch_name: str) -> Dict[str, Any]:
        """切换分支"""
        result = {
            "success": False,
            "message": "",
            "branch_name": branch_name
        }
        
        try:
            # 检查分支是否存在
            success, output = self._run_git_command(["branch", "--list", branch_name])
            if not success or not output.strip():
                result["message"] = f"分支不存在: {branch_name}"
                return result
            
            # 切换分支
            success, output = self._run_git_command(["checkout", branch_name])
            if success:
                result["success"] = True
                result["message"] = f"切换到分支: {branch_name}"
                logger.info(f"切换分支: {branch_name}")
            else:
                result["message"] = f"切换分支失败: {output}"
                
        except Exception as e:
            result["message"] = f"切换分支异常: {str(e)}"
            logger.error(f"切换分支失败: {e}")
        
        return result
    
    def merge_branch(self, source_branch: str, target_branch: str = "main") -> Dict[str, Any]:
        """合并分支"""
        result = {
            "success": False,
            "message": "",
            "conflicts": []
        }
        
        try:
            # 保存当前分支
            success, current_branch = self._run_git_command(["branch", "--show-current"])
            if not success:
                result["message"] = "无法确定当前分支"
                return result
            
            # 切换到目标分支
            switch_result = self.switch_branch(target_branch)
            if not switch_result["success"]:
                return switch_result
            
            # 合并源分支
            success, output = self._run_git_command(["merge", source_branch])
            
            if success:
                result["success"] = True
                result["message"] = f"合并成功: {source_branch} -> {target_branch}"
                logger.info(f"合并分支: {source_branch} -> {target_branch}")
            else:
                # 检查是否有冲突
                if "CONFLICT" in output:
                    # 获取冲突文件
                    success, conflict_output = self._run_git_command(["diff", "--name-only", "--diff-filter=U"])
                    if success and conflict_output:
                        conflicts = conflict_output.strip().split('\n')
                        result["conflicts"] = conflicts
                        result["message"] = f"合并冲突: {len(conflicts)} 个文件"
                    else:
                        result["message"] = "合并冲突"
                else:
                    result["message"] = f"合并失败: {output}"
            
            # 切换回原分支
            if current_branch.strip():
                self.switch_branch(current_branch.strip())
                
        except Exception as e:
            result["message"] = f"合并分支异常: {str(e)}"
            logger.error(f"合并分支失败: {e}")
        
        return result
    
    def push_to_remote(self, remote: str = "origin", branch: Optional[str] = None) -> Dict[str, Any]:
        """推送到远程仓库"""
        result = {
            "success": False,
            "message": ""
        }
        
        try:
            # 获取当前分支
            if not branch:
                success, current_branch = self._run_git_command(["branch", "--show-current"])
                if success:
                    branch = current_branch.strip()
            
            if not branch:
                result["message"] = "无法确定当前分支"
                return result
            
            # 推送到远程
            success, output = self._run_git_command(["push", remote, branch])
            
            if success:
                result["success"] = True
                result["message"] = f"推送成功: {branch} -> {remote}/{branch}"
                logger.info(f"推送到远程: {branch} -> {remote}")
            else:
                result["message"] = f"推送失败: {output}"
                
        except Exception as e:
            result["message"] = f"推送异常: {str(e)}"
            logger.error(f"推送到远程失败: {e}")
        
        return result
    
    def pull_from_remote(self, remote: str = "origin", branch: Optional[str] = None) -> Dict[str, Any]:
        """从远程拉取"""
        result = {
            "success": False,
            "message": "",
            "conflicts": []
        }
        
        try:
            # 获取当前分支
            if not branch:
                success, current_branch = self._run_git_command(["branch", "--show-current"])
                if success:
                    branch = current_branch.strip()
            
            if not branch:
                result["message"] = "无法确定当前分支"
                return result
            
            # 从远程拉取
            success, output = self._run_git_command(["pull", remote, branch])
            
            if success:
                result["success"] = True
                result["message"] = f"拉取成功: {remote}/{branch} -> {branch}"
                logger.info(f"从远程拉取: {remote}/{branch}")
            else:
                # 检查是否有冲突
                if "CONFLICT" in output:
                    # 获取冲突文件
                    success, conflict_output = self._run_git_command(["diff", "--name-only", "--diff-filter=U"])
                    if success and conflict_output:
                        conflicts = conflict_output.strip().split('\n')
                        result["conflicts"] = conflicts
                        result["message"] = f"拉取冲突: {len(conflicts)} 个文件"
                    else:
                        result["message"] = "拉取冲突"
                else:
                    result["message"] = f"拉取失败: {output}"
                
        except Exception as e:
            result["message"] = f"拉取异常: {str(e)}"
            logger.error(f"从远程拉取失败: {e}")
        
        return result
    
    def create_pull_request(self, 
                           title: str,
                           body: str,
                           source_branch: str,
                           target_branch: str = "main") -> Dict[str, Any]:
        """
        创建Pull Request（模拟）
        
        注意：实际PR创建需要GitHub CLI或API
        """
        result = {
            "success": False,
            "message": "",
            "pr_info": {}
        }
        
        try:
            # 检查源分支是否存在
            success, output = self._run_git_command(["branch", "--list", source_branch])
            if not success or not output.strip():
                result["message"] = f"源分支不存在: {source_branch}"
                return result
            
            # 检查目标分支是否存在
            success, output = self._run_git_command(["branch", "--list", target_branch])
            if not success or not output.strip():
                result["message"] = f"目标分支不存在: {target_branch}"
                return result
            
            # 获取差异
            success, diff_output = self._run_git_command(["diff", "--stat", f"{target_branch}...{source_branch}"])
            
            if success:
                # 模拟PR信息
                pr_info = {
                    "title": title,
                    "body": body,
                    "source_branch": source_branch,
                    "target_branch": target_branch,
                    "diff_stat": diff_output.strip() if diff_output else "",
                    "created_at": datetime.now().isoformat(),
                    "status": "draft"
                }
                
                result["success"] = True
                result["message"] = f"Pull Request 创建成功（模拟）: {source_branch} -> {target_branch}"
                result["pr_info"] = pr_info
                
                logger.info(f"创建Pull Request: {title}")
            else:
                result["message"] = f"无法获取分支差异: {diff_output}"
                
        except Exception as e:
            result["message"] = f"创建Pull Request异常: {str(e)}"
            logger.error(f"创建Pull Request失败: {e}")
        
        return result
    
    def trigger_hot_reload(self, domain_name: str) -> Dict[str, Any]:
        """
        触发热重载
        
        Args:
            domain_name: 领域名称
            
        Returns:
            热重载结果
        """
        result = {
            "success": False,
            "message": "",
            "reloaded_files": []
        }
        
        try:
            domain_path = self.domains_dir / domain_name
            if not domain_path.exists():
                result["message"] = f"领域不存在: {domain_name}"
                return result
            
            # 查找需要重载的文件
            reloaded_files = []
            for file_type in ["schema.json", "seed.json", "actions.json", "patterns.json"]:
                file_path = domain_path / file_type
                if file_path.exists():
                    reloaded_files.append(file_type)
            
            if not reloaded_files:
                result["message"] = f"领域 {domain_name} 没有可重载的文件"
                return result
            
            # 模拟热重载过程
            # 实际实现需要与游戏引擎通信
            logger.info(f"触发热重载: {domain_name} - 文件: {', '.join(reloaded_files)}")
            
            result["success"] = True
            result["message"] = f"热重载触发成功: {len(reloaded_files)} 个文件"
            result["reloaded_files"] = reloaded_files
            
        except Exception as e:
            result["message"] = f"热重载异常: {str(e)}"
            logger.error(f"触发热重载失败: {e}")
        
        return result
    
    def export_ontology_snapshot(self, 
                                domain_name: str,
                                snapshot_name: Optional[str] = None) -> Dict[str, Any]:
        """
        导出本体快照
        
        Args:
            domain_name: 领域名称
            snapshot_name: 快照名称
            
        Returns:
            快照信息
        """
        result = {
            "success": False,
            "message": "",
            "snapshot_path": ""
        }
        
        try:
            domain_path = self.domains_dir / domain_name
            if not domain_path.exists():
                result["message"] = f"领域不存在: {domain_name}"
                return result
            
            # 创建快照目录
            snapshots_dir = domain_path / "snapshots"
            snapshots_dir.mkdir(exist_ok=True)
            
            # 生成快照名称
            if not snapshot_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                snapshot_name = f"snapshot_{timestamp}"
            
            # 创建快照
            snapshot_path = snapshots_dir / f"{snapshot_name}.tar.gz"
            
            # 打包领域文件
            import tarfile
            with tarfile.open(snapshot_path, "w:gz") as tar:
                for file_type in ["schema.json", "seed.json", "actions.json", "patterns.json", "config.json"]:
                    file_path = domain_path / file_type
                    if file_path.exists():
                        tar.add(file_path, arcname=file_type)
            
            result["success"] = True
            result["message"] = f"快照创建成功: {snapshot_name}"
            result["snapshot_path"] = str(snapshot_path.relative_to(self.project_root))
            
            logger.info(f"导出本体快照: {domain_name} -> {snapshot_name}")
            
        except Exception as e:
            result["message"] = f"导出快照异常: {str(e)}"
            logger.error(f"导出本体快照失败: {e}")
        
        return result
    
    def restore_ontology_snapshot(self, 
                                 domain_name: str,
                                 snapshot_path: str) -> Dict[str, Any]:
        """
        恢复本体快照
        
        Args:
            domain_name: 领域名称
            snapshot_path: 快照路径
            
        Returns:
            恢复结果
        """
        result = {
            "success": False,
            "message": "",
            "restored_files": []
        }
        
        try:
            domain_path = self.domains_dir / domain_name
            if not domain_path.exists():
                result["message"] = f"领域不存在: {domain_name}"
                return result
            
            full_snapshot_path = self.project_root / snapshot_path
            if not full_snapshot_path.exists():
                result["message"] = f"快照文件不存在: {snapshot_path}"
                return result
            
            # 解压快照
            import tarfile
            restored_files = []
            
            with tarfile.open(full_snapshot_path, "r:gz") as tar:
                # 备份现有文件
                backup_dir = domain_path / "backup"
                backup_dir.mkdir(exist_ok=True)
                backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                for file_type in ["schema.json", "seed.json", "actions.json", "patterns.json", "config.json"]:
                    file_path = domain_path / file_type
                    if file_path.exists():
                        backup_path = backup_dir / f"{file_type}.{backup_timestamp}.bak"
                        shutil.copy2(file_path, backup_path)
                
                # 提取文件
                tar.extractall(path=domain_path)
                
                # 记录恢复的文件
                for member in tar.getmembers():
                    if member.isfile():
                        restored_files.append(member.name)
            
            result["success"] = True
            result["message"] = f"快照恢复成功: {len(restored_files)} 个文件"
            result["restored_files"] = restored_files
            
            logger.info(f"恢复本体快照: {domain_name} <- {snapshot_path}")
            
        except Exception as e:
            result["message"] = f"恢复快照异常: {str(e)}"
            logger.error(f"恢复本体快照失败: {e}")
        
        return result