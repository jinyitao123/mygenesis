"""
增强的日志系统

提供结构化日志、请求追踪、性能监控等功能。
"""

import logging
import logging.handlers
import json
import time
import uuid
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from pathlib import Path
from functools import wraps

from flask import request, g

from .config import settings


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""
    
    def __init__(self):
        super().__init__()
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        # 基础日志信息
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加额外字段 - 通过__dict__获取extra信息
        extra_data = {}
        for key, value in record.__dict__.items():
            if key not in ['args', 'asctime', 'created', 'exc_info', 'exc_text', 
                          'filename', 'funcName', 'levelname', 'levelno', 'lineno',
                          'module', 'msecs', 'message', 'msg', 'name', 'pathname',
                          'process', 'processName', 'relativeCreated', 'stack_info',
                          'thread', 'threadName']:
                extra_data[key] = value
        
        if extra_data:
            log_data.update(extra_data)
        
        # 添加请求上下文
        
        # 添加请求上下文
        try:
            if hasattr(g, "request_id"):
                log_data["request_id"] = g.request_id
            
            if request and hasattr(request, "path"):
                log_data.update({
                    "request_path": request.path,
                    "request_method": request.method,
                    "remote_addr": request.remote_addr,
                })
        except RuntimeError:
            # 在没有应用上下文时跳过
            pass
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class RequestContextFilter(logging.Filter):
    """请求上下文过滤器"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """添加请求上下文到日志记录"""
        try:
            # 添加请求ID
            if hasattr(g, "request_id"):
                if not hasattr(record, "request_id"):
                    record.request_id = g.request_id
            
            # 添加用户信息（如果有）
            if hasattr(g, "user_id"):
                if not hasattr(record, "user_id"):
                    record.user_id = g.user_id
            
            # 添加领域信息（如果有）
            if hasattr(g, "domain"):
                if not hasattr(record, "domain"):
                    record.domain = g.domain
        except RuntimeError:
            # 在没有应用上下文时跳过
            pass
        
        return True
class PerformanceLogger:
    """性能日志记录器"""
    
    def __init__(self, logger_name: str = "performance"):
        self.logger = logging.getLogger(logger_name)
    
    def time_it(self, operation_name: str):
        """
        计时装饰器
        
        用法:
            @performance_logger.time_it("database_query")
            def query_database():
                # 你的代码
                pass
        """
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    elapsed_time = time.perf_counter() - start_time
                    
                    # 记录性能日志
                    self.logger.info(
                        f"Operation '{operation_name}' completed",
                        extra={
                            "operation": operation_name,
                            "duration_ms": round(elapsed_time * 1000, 2),
                            "success": True,
                        }
                    )
                    
                    return result
                except Exception as e:
                    elapsed_time = time.perf_counter() - start_time
                    
                    # 记录错误性能日志
                    self.logger.error(
                        f"Operation '{operation_name}' failed",
                        extra={
                            "operation": operation_name,
                            "duration_ms": round(elapsed_time * 1000, 2),
                            "success": False,
                            "error": str(e),
                            "error_type": e.__class__.__name__,
                        },
                        exc_info=True
                    )
                    
                    raise
            
            return wrapper
        
        return decorator
    
    def log_metric(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """记录指标"""
        extra = {
            "metric": metric_name,
            "value": value,
            "type": "metric",
        }
        
        if tags:
            extra["tags"] = tags
        
        self.logger.info(f"Metric: {metric_name} = {value}", extra=extra)


class AuditLogger:
    """审计日志记录器"""
    
    def __init__(self, logger_name: str = "audit"):
        self.logger = logging.getLogger(logger_name)
    
    def log_action(self, 
                   action: str, 
                   resource: str, 
                   user_id: Optional[str] = None,
                   status: str = "success",
                   details: Optional[Dict[str, Any]] = None):
        """
        记录审计日志
        
        Args:
            action: 执行的操作（如：create, update, delete, read）
            resource: 操作的资源（如：user, domain, ontology）
            user_id: 执行操作的用户ID
            status: 操作状态（success, failure）
            details: 额外详情
        """
        audit_data: Dict[str, Any] = {
            "action": action,
            "resource": resource,
            "status": status,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "type": "audit",
        }
        
        # 添加用户信息
        if user_id:
            audit_data["user_id"] = user_id
        elif hasattr(g, 'user_id'):
            audit_data["user_id"] = g.user_id
        
        # 添加请求信息
        if request:
            request_info = {
                "request_path": str(request.path),
                "request_method": str(request.method),
                "remote_addr": str(request.remote_addr) if request.remote_addr else "",
            }
            # 手动更新字典以避免类型检查问题
            for key, value in request_info.items():
                audit_data[key] = value
        
        # 添加请求ID
        if hasattr(g, 'request_id'):
            audit_data["request_id"] = g.request_id
        
        # 添加额外详情
        if details:
            audit_data["details"] = details
        
        # 记录审计日志
        message = f"Audit: {action} {resource} - {status}"
        if user_id:
            message += f" by {user_id}"
        
        self.logger.info(message, extra=audit_data)


def setup_logging():
    """设置日志系统"""
    # 创建日志目录
    log_dir = settings.log_dir
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level.value)
    
    # 清除现有的处理器
    root_logger.handlers.clear()
    
    # 创建文件处理器（JSON格式）
    log_file = settings.project_root / settings.log_file
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(StructuredFormatter())
    file_handler.addFilter(RequestContextFilter())
    
    # 创建控制台处理器（人类可读格式）
    console_handler = logging.StreamHandler()
    if settings.is_development:
        # 开发环境使用简单格式
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    else:
        # 生产环境也使用JSON格式
        console_format = StructuredFormatter()
    
    console_handler.setFormatter(console_format)
    console_handler.addFilter(RequestContextFilter())
    
    # 添加处理器
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # 创建专门的日志记录器
    performance_logger = logging.getLogger("performance")
    performance_logger.setLevel(logging.INFO)
    performance_logger.propagate = False
    
    audit_logger = logging.getLogger("audit")
    audit_logger.setLevel(logging.INFO)
    audit_logger.propagate = False
    
    # 记录日志系统初始化
    logging.getLogger(__name__).info(
        "Logging system initialized",
        extra={
            "log_level": settings.log_level.value,
            "log_file": str(log_file),
            "environment": settings.app_env.value,
        }
    )


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器（快捷方式）"""
    return logging.getLogger(name)


def get_performance_logger() -> PerformanceLogger:
    """获取性能日志记录器"""
    return PerformanceLogger()


def get_audit_logger() -> AuditLogger:
    """获取审计日志记录器"""
    return AuditLogger()


# 导出
__all__ = [
    "setup_logging",
    "get_logger",
    "get_performance_logger",
    "get_audit_logger",
    "StructuredFormatter",
    "RequestContextFilter",
    "PerformanceLogger",
    "AuditLogger",
]