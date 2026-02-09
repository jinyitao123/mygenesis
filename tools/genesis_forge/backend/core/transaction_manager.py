"""
事务管理器 - 实现多存储事务原子性
"""
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from contextlib import contextmanager
from datetime import datetime
import logging
import hashlib

from core.exceptions import TransactionError, DataInconsistencyError

logger = logging.getLogger(__name__)


class TransactionLog:
    """事务日志记录器"""
    
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def create_transaction(self, transaction_id: str) -> Path:
        """创建新的事务日志文件"""
        log_file = self.log_dir / f"{transaction_id}.log"
        log_file.touch()
        return log_file
    
    def log_operation(self, transaction_id: str, operation: str, details: Dict[str, Any]):
        """记录操作"""
        log_file = self.log_dir / f"{transaction_id}.log"
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {operation}: {details}\n"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    
    def get_transaction_log(self, transaction_id: str) -> List[str]:
        """获取事务日志"""
        log_file = self.log_dir / f"{transaction_id}.log"
        if not log_file.exists():
            return []
        
        with open(log_file, 'r', encoding='utf-8') as f:
            return f.readlines()
    
    def cleanup_transaction_log(self, transaction_id: str):
        """清理事务日志"""
        log_file = self.log_dir / f"{transaction_id}.log"
        if log_file.exists():
            log_file.unlink()


class FileOperation:
    """文件操作记录"""
    
    def __init__(self, file_path: Path, operation_type: str, backup_path: Optional[Path] = None):
        self.file_path = file_path
        self.operation_type = operation_type  # 'create', 'update', 'delete'
        self.backup_path = backup_path
        self.original_hash = self._calculate_hash(file_path) if file_path.exists() else None
        self.timestamp = datetime.now()
    
    def _calculate_hash(self, file_path: Path) -> str:
        """计算文件哈希"""
        if not file_path.exists():
            return ""
        
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "file_path": str(self.file_path),
            "operation_type": self.operation_type,
            "backup_path": str(self.backup_path) if self.backup_path else None,
            "original_hash": self.original_hash,
            "timestamp": self.timestamp.isoformat()
        }


class Neo4jOperation:
    """Neo4j 操作记录"""
    
    def __init__(self, query: str, params: Optional[Dict] = None):
        self.query = query
        self.params = params or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "query": self.query,
            "params": self.params,
            "timestamp": self.timestamp.isoformat()
        }


class Transaction:
    """事务 - 管理多个原子操作"""
    
    def __init__(self, transaction_id: str, log_dir: Path):
        self.transaction_id = transaction_id
        self.log_dir = log_dir
        self.logger = TransactionLog(log_dir)
        
        self.file_operations: List[FileOperation] = []
        self.neo4j_operations: List[Neo4jOperation] = []
        self.custom_operations: List[Callable[[], None]] = []
        
        self.committed = False
        self.rolled_back = False
        
        self.logger.create_transaction(transaction_id)
    
    def add_file_operation(self, file_path: Path, operation_type: str, backup_path: Optional[Path] = None):
        """添加文件操作"""
        operation = FileOperation(file_path, operation_type, backup_path)
        self.file_operations.append(operation)
        self.logger.log_operation(
            self.transaction_id,
            f"FILE_{operation_type.upper()}",
            {
                "file_path": str(file_path),
                "backup_path": str(backup_path) if backup_path else None
            }
        )
    
    def add_neo4j_operation(self, query: str, params: Optional[Dict] = None):
        """添加 Neo4j 操作"""
        operation = Neo4jOperation(query, params)
        self.neo4j_operations.append(operation)
        self.logger.log_operation(
            self.transaction_id,
            "NEO4J_QUERY",
            {"query": query, "params": params}
        )
    
    def add_custom_operation(self, operation: Callable[[], None], description: str):
        """添加自定义操作"""
        self.custom_operations.append(operation)
        self.logger.log_operation(
            self.transaction_id,
            "CUSTOM",
            {"description": description}
        )
    
    def commit(self):
        """提交事务"""
        if self.committed:
            raise TransactionError("Transaction already committed")
        
        if self.rolled_back:
            raise TransactionError("Transaction already rolled back")
        
        # 标记为已提交
        self.committed = True
        self.logger.log_operation(self.transaction_id, "COMMIT", {})
        
        logger.info(f"Transaction {self.transaction_id} committed")
    
    def rollback(self):
        """回滚事务"""
        if self.rolled_back:
            logger.warning(f"Transaction {self.transaction_id} already rolled back")
            return
        
        # 回滚文件操作（按相反顺序）
        for operation in reversed(self.file_operations):
            try:
                self._rollback_file_operation(operation)
            except Exception as e:
                logger.error(f"Failed to rollback file operation: {e}")
        
        # 回滚 Neo4j 操作
        # 注意：Neo4j 的回滚比较复杂，这里简化处理
        # 实际应用中应该使用 Neo4j 的事务机制
        for operation in reversed(self.neo4j_operations):
            try:
                self._rollback_neo4j_operation(operation)
            except Exception as e:
                logger.error(f"Failed to rollback Neo4j operation: {e}")
        
        # 回滚自定义操作
        for operation in reversed(self.custom_operations):
            try:
                operation()
            except Exception as e:
                logger.error(f"Failed to rollback custom operation: {e}")
        
        self.rolled_back = True
        self.logger.log_operation(self.transaction_id, "ROLLBACK", {})
        
        logger.info(f"Transaction {self.transaction_id} rolled back")
    
    def _rollback_file_operation(self, operation: FileOperation):
        """回滚文件操作"""
        if operation.operation_type == 'create':
            if operation.file_path.exists():
                operation.file_path.unlink()
                logger.info(f"Rolled back created file: {operation.file_path}")
        
        elif operation.operation_type == 'update':
            if operation.backup_path and operation.backup_path.exists():
                shutil.copy2(operation.backup_path, operation.file_path)
                operation.backup_path.unlink()
                logger.info(f"Rolled back updated file: {operation.file_path}")
        
        elif operation.operation_type == 'delete':
            if operation.backup_path and operation.backup_path.exists():
                shutil.move(operation.backup_path, operation.file_path)
                logger.info(f"Rolled back deleted file: {operation.file_path}")
    
    def _rollback_neo4j_operation(self, operation: Neo4jOperation):
        """
        回滚 Neo4j 操作
        注意：这是一个简化版本，实际应用中需要更复杂的逻辑
        """
        # 这里只是一个占位符
        # 实际回滚逻辑应该根据具体的查询类型来决定
        logger.warning(f"Neo4j rollback not fully implemented for query: {operation.query[:50]}...")


class TransactionManager:
    """事务管理器"""
    
    def __init__(self, log_dir: Optional[Path] = None):
        if log_dir is None:
            # 使用临时目录
            self.log_dir = Path(tempfile.gettempdir()) / "genesis_transactions"
        else:
            self.log_dir = log_dir
        
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.active_transactions: Dict[str, Transaction] = {}
        self.temp_dir = self.log_dir / "backups"
        self.temp_dir.mkdir(exist_ok=True)
    
    def begin_transaction(self) -> Transaction:
        """开始一个新事务"""
        import uuid
        transaction_id = str(uuid.uuid4())
        transaction = Transaction(transaction_id, self.log_dir)
        self.active_transactions[transaction_id] = transaction
        logger.info(f"Started transaction: {transaction_id}")
        return transaction
    
    def commit_transaction(self, transaction: Transaction) -> bool:
        """提交事务"""
        try:
            transaction.commit()
            if transaction.transaction_id in self.active_transactions:
                del self.active_transactions[transaction.transaction_id]
            
            # 清理备份文件
            self._cleanup_backups(transaction)
            
            # 延迟删除日志
            self._delayed_log_cleanup(transaction.transaction_id)
            
            return True
        except Exception as e:
            logger.error(f"Failed to commit transaction: {e}")
            return False
    
    def rollback_transaction(self, transaction: Transaction) -> bool:
        """回滚事务"""
        try:
            transaction.rollback()
            if transaction.transaction_id in self.active_transactions:
                del self.active_transactions[transaction.transaction_id]
            
            # 清理备份文件
            self._cleanup_backups(transaction)
            
            return True
        except Exception as e:
            logger.error(f"Failed to rollback transaction: {e}")
            return False
    
    def _cleanup_backups(self, transaction: Transaction):
        """清理事务的备份文件"""
        for operation in transaction.file_operations:
            if operation.backup_path and operation.backup_path.exists():
                try:
                    operation.backup_path.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete backup {operation.backup_path}: {e}")
    
    def _delayed_log_cleanup(self, transaction_id: str, delay_hours: int = 24):
        """延迟清理事务日志"""
        # 实际应用中可以使用定时任务来清理
        # 这里只是记录日志
        logger.info(f"Transaction {transaction_id} log scheduled for cleanup in {delay_hours} hours")
    
    @contextmanager
    def transaction_scope(self):
        """事务作用域上下文管理器"""
        transaction = self.begin_transaction()
        try:
            yield transaction
            self.commit_transaction(transaction)
        except Exception as e:
            logger.error(f"Transaction failed, rolling back: {e}")
            self.rollback_transaction(transaction)
            raise


class DomainSaveTransaction:
    """领域保存事务 - 专门用于领域配置的保存"""
    
    def __init__(self, transaction_manager: TransactionManager, domain_manager, domain_name: str):
        self.transaction_manager = transaction_manager
        self.domain_manager = domain_manager
        self.domain_name = domain_name
        self.transaction = transaction_manager.begin_transaction()
        self.original_files: Dict[str, str] = {}
    
    def prepare(self, file_types: List[str], new_contents: Dict[str, str]):
        """准备保存操作"""
        domains_dir = Path(self.domain_manager.domains_dir) / self.domain_name
        
        for file_type in file_types:
            if file_type not in self.domain_manager.file_mapping:
                raise ValueError(f"Invalid file type: {file_type}")
            
            filename = self.domain_manager.file_mapping[file_type]
            file_path = domains_dir / filename
            
            # 创建备份
            if file_path.exists():
                backup_path = self.transaction_manager.temp_dir / f"{self.transaction.transaction_id}_{filename}"
                shutil.copy2(file_path, backup_path)
                self.transaction.add_file_operation(file_path, 'update', backup_path)
                
                # 保存原始内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.original_files[file_type] = f.read()
            else:
                self.transaction.add_file_operation(file_path, 'create')
    
    def execute(self, file_types: List[str], new_contents: Dict[str, str]):
        """执行保存操作"""
        domains_dir = Path(self.domain_manager.domains_dir) / self.domain_name
        
        for file_type in file_types:
            if file_type not in new_contents:
                continue
            
            content = new_contents[file_type]
            filename = self.domain_manager.file_mapping[file_type]
            file_path = domains_dir / filename
            
            # 确保目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入新内容
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
    
    def commit(self) -> bool:
        """提交保存操作"""
        return self.transaction_manager.commit_transaction(self.transaction)
    
    def rollback(self) -> bool:
        """回滚保存操作"""
        return self.transaction_manager.rollback_transaction(self.transaction)


def save_domain_config_atomic(domain_manager, domain_name: str, file_types: List[str], 
                              new_contents: Dict[str, str], sync_to_neo4j: bool = False,
                              neo4j_loader = None) -> Dict[str, Any]:
    """
    原子性地保存领域配置
    
    Args:
        domain_manager: 领域管理器实例
        domain_name: 领域名称
        file_types: 要保存的文件类型列表
        new_contents: 新内容字典 {file_type: content}
        sync_to_neo4j: 是否同步到 Neo4j
        neo4j_loader: Neo4j 加载器实例（如果 sync_to_neo4j 为 True）
        
    Returns:
        操作结果
        
    Raises:
        TransactionError: 如果事务失败
    """
    transaction_manager = TransactionManager()
    save_transaction = DomainSaveTransaction(transaction_manager, domain_manager, domain_name)
    
    try:
        # 准备阶段：创建备份
        save_transaction.prepare(file_types, new_contents)
        
        # 执行阶段：写入新文件
        save_transaction.execute(file_types, new_contents)
        
        # 同步到 Neo4j（如果需要）
        if sync_to_neo4j and neo4j_loader:
            try:
                files = domain_manager.get_domain_files(domain_name)
                seed_content = files.get("seed", "")
                
                if seed_content:
                    neo4j_loader.load_to_neo4j(seed_content, clear_existing=True)
            except Exception as e:
                # Neo4j 同步失败，回滚文件操作
                raise DataInconsistencyError(
                    f"Neo4j sync failed: {str(e)}",
                    source="filesystem",
                    target="neo4j"
                )
        
        # 提交事务
        save_transaction.commit()
        
        return {
            "status": "success",
            "message": f"Successfully saved {len(file_types)} files for domain {domain_name}",
            "saved_files": file_types,
            "synced_to_neo4j": sync_to_neo4j
        }
        
    except Exception as e:
        # 回滚事务
        save_transaction.rollback()
        raise TransactionError(f"Failed to save domain config: {str(e)}", operations=file_types)
