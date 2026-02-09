"""
异步任务管理器 - 处理长时间运行的任务
"""
import threading
import queue
import time
import uuid
from typing import Dict, Any, Optional, Callable
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task:
    """异步任务"""
    
    def __init__(self, task_id: str, func: Callable, *args, **kwargs):
        self.task_id = task_id
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.progress = 0
        self.progress_message = ""
        self.thread = None
    
    def run(self):
        """执行任务"""
        try:
            self.status = TaskStatus.RUNNING
            self.started_at = datetime.now()
            logger.info(f"Task {self.task_id} started")
            
            # 执行任务函数
            if hasattr(self.func, '__self__'):
                # 如果是方法，使用实例
                result = self.func(*self.args, **self.kwargs)
            else:
                result = self.func(*self.args, **self.kwargs)
            
            self.result = result
            self.status = TaskStatus.SUCCESS
            self.completed_at = datetime.now()
            self.progress = 100
            self.progress_message = "Completed"
            logger.info(f"Task {self.task_id} completed successfully")
            
        except Exception as e:
            self.error = str(e)
            self.status = TaskStatus.FAILED
            self.completed_at = datetime.now()
            logger.error(f"Task {self.task_id} failed: {e}")
    
    def cancel(self):
        """取消任务"""
        if self.status == TaskStatus.RUNNING:
            self.status = TaskStatus.CANCELLED
            logger.info(f"Task {self.task_id} cancelled")
    
    def update_progress(self, progress: int, message: str = ""):
        """更新任务进度"""
        self.progress = progress
        self.progress_message = message
        logger.debug(f"Task {self.task_id} progress: {progress}% - {message}")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "progress": self.progress,
            "progress_message": self.progress_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result if self.status == TaskStatus.SUCCESS else None,
            "error": self.error if self.status == TaskStatus.FAILED else None
        }


class AsyncTaskManager:
    """异步任务管理器 - 简化版（单进程多线程）"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AsyncTaskManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, max_workers: int = 5):
        if not self._initialized:
            self.tasks: Dict[str, Task] = {}
            self.max_workers = max_workers
            self._initialized = True
            logger.info(f"AsyncTaskManager initialized with {max_workers} workers")
    
    def submit_task(self, func: Callable, *args, **kwargs) -> str:
        """
        提交异步任务
        
        Args:
            func: 要执行的函数
            *args, **kwargs: 函数参数
            
        Returns:
            任务 ID
        """
        task_id = str(uuid.uuid4())
        task = Task(task_id, func, *args, **kwargs)
        self.tasks[task_id] = task
        
        # 在新线程中执行任务
        thread = threading.Thread(target=task.run, daemon=True)
        task.thread = thread
        thread.start()
        
        logger.info(f"Task {task_id} submitted")
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态
        
        Args:
            task_id: 任务 ID
            
        Returns:
            任务状态字典，如果任务不存在则返回 None
        """
        task = self.tasks.get(task_id)
        if task:
            return task.to_dict()
        return None
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务 ID
            
        Returns:
            是否成功取消
        """
        task = self.tasks.get(task_id)
        if task and task.status == TaskStatus.RUNNING:
            task.cancel()
            return True
        return False
    
    def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """
        清理已完成的任务
        
        Args:
            max_age_hours: 最大保留时间（小时）
        """
        now = datetime.now()
        to_remove = []
        
        for task_id, task in self.tasks.items():
            if task.status in [TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                if task.completed_at:
                    age = (now - task.completed_at).total_seconds() / 3600
                    if age > max_age_hours:
                        to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.tasks[task_id]
            logger.info(f"Cleaned up task {task_id}")
    
    def get_active_tasks(self) -> Dict[str, Dict[str, Any]]:
        """获取所有活动的任务"""
        return {
            task_id: task.to_dict()
            for task_id, task in self.tasks.items()
            if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]
        }


# Neo4j 同步任务的专用包装器
class Neo4jSyncTask:
    """Neo4j 同步任务"""
    
    def __init__(self, neo4j_loader, domain_manager, domain_name: str):
        self.neo4j_loader = neo4j_loader
        self.domain_manager = domain_manager
        self.domain_name = domain_name
        self.progress_callback = None
    
    def set_progress_callback(self, callback: Callable[[int, str], None]):
        """设置进度回调函数"""
        self.progress_callback = callback
    
    def run(self):
        """执行同步任务"""
        try:
            if self.progress_callback:
                self.progress_callback(10, "开始加载数据...")
            
            # 获取领域数据
            files = self.domain_manager.get_domain_files(self.domain_name)
            seed_content = files.get("seed", "")
            
            if not seed_content:
                raise ValueError(f"Domain {self.domain_name} has no seed data")
            
            if self.progress_callback:
                self.progress_callback(30, "解析 XML 数据...")
            
            # 解析 XML
            nodes, links = self.neo4j_loader.parse_seed_xml(seed_content)
            
            if self.progress_callback:
                self.progress_callback(50, f"开始同步 {len(nodes)} 个节点...")
            
            # 加载到 Neo4j
            stats = self.neo4j_loader.load_to_neo4j(seed_content, clear_existing=True)
            
            if self.progress_callback:
                self.progress_callback(90, "完成同步...")
            
            if self.progress_callback:
                self.progress_callback(100, "同步完成")
            
            return {
                "status": "success",
                "stats": stats,
                "message": f"成功同步 {stats['nodes']} 个节点和 {stats['links']} 个关系"
            }
            
        except Exception as e:
            if self.progress_callback:
                self.progress_callback(100, f"同步失败: {str(e)}")
            raise


# 文件导入任务的专用包装器
class FileImportTask:
    """文件导入任务"""
    
    def __init__(self, domain_manager, domain_name: str, file_type: str, content: str):
        self.domain_manager = domain_manager
        self.domain_name = domain_name
        self.file_type = file_type
        self.content = content
        self.progress_callback = None
    
    def set_progress_callback(self, callback: Callable[[int, str], None]):
        """设置进度回调函数"""
        self.progress_callback = callback
    
    def run(self):
        """执行导入任务"""
        try:
            if self.progress_callback:
                self.progress_callback(20, f"验证 {self.file_type} 文件...")
            
            # 验证文件类型
            valid_types = ["schema", "seed", "actions", "patterns"]
            if self.file_type not in valid_types:
                raise ValueError(f"Invalid file type: {self.file_type}")
            
            if self.progress_callback:
                self.progress_callback(50, "保存文件...")
            
            # 保存文件
            success = self.domain_manager.save_domain_file(
                self.domain_name,
                self.file_type,
                self.content
            )
            
            if not success:
                raise Exception(f"Failed to save {self.file_type} file")
            
            if self.progress_callback:
                self.progress_callback(100, "导入完成")
            
            return {
                "status": "success",
                "file_type": self.file_type,
                "domain": self.domain_name,
                "message": f"{self.file_type} 文件导入成功"
            }
            
        except Exception as e:
            if self.progress_callback:
                self.progress_callback(100, f"导入失败: {str(e)}")
            raise


def submit_neo4j_sync_task(neo4j_loader, domain_manager, domain_name: str) -> str:
    """
    提交 Neo4j 同步任务
    
    Args:
        neo4j_loader: Neo4j 加载器实例
        domain_manager: 领域管理器实例
        domain_name: 领域名称
        
    Returns:
        任务 ID
    """
    manager = AsyncTaskManager()
    task = Neo4jSyncTask(neo4j_loader, domain_manager, domain_name)
    return manager.submit_task(task.run)


def submit_file_import_task(domain_manager, domain_name: str, file_type: str, content: str) -> str:
    """
    提交文件导入任务
    
    Args:
        domain_manager: 领域管理器实例
        domain_name: 领域名称
        file_type: 文件类型
        content: 文件内容
        
    Returns:
        任务 ID
    """
    manager = AsyncTaskManager()
    task = FileImportTask(domain_manager, domain_name, file_type, content)
    return manager.submit_task(task.run)
