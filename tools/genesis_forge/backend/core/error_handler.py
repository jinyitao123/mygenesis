"""
统一错误处理中间件

提供一致的错误处理机制，包括：
1. 异常捕获和转换
2. 错误响应格式化
3. 错误日志记录
4. HTTP状态码映射
"""

import logging
import traceback
from typing import Dict, Any, Optional, Callable
from functools import wraps

from flask import jsonify, request, g
from .exceptions import GenesisError

logger = logging.getLogger(__name__)


class ErrorHandler:
    """错误处理器"""
    
    # 错误类型到HTTP状态码的映射
    ERROR_STATUS_MAP = {
        "DOMAIN_NOT_FOUND": 404,
        "SCHEMA_VALIDATION_ERROR": 400,
        "SECURITY_ERROR": 403,
        "CYPHER_INJECTION_ERROR": 400,
        "PATH_TRAVERSAL_ERROR": 400,
        "NEO4J_ERROR": 503,
        "TRANSACTION_ERROR": 500,
        "VALIDATION_ERROR": 400,
        "NOT_FOUND_ERROR": 404,
        "UNAUTHORIZED_ERROR": 401,
        "FORBIDDEN_ERROR": 403,
        "CONFLICT_ERROR": 409,
        "RATE_LIMIT_ERROR": 429,
        "SERVICE_UNAVAILABLE": 503,
    }
    
    # 默认HTTP状态码
    DEFAULT_STATUS = 500
    
    @classmethod
    def handle_exception(cls, error: Exception) -> tuple:
        """
        处理异常并返回标准化的错误响应
        
        Args:
            error: 捕获的异常
            
        Returns:
            (response, status_code) 元组
        """
        # 记录错误
        cls._log_error(error)
        
        # 处理自定义异常
        if isinstance(error, GenesisError):
            return cls._handle_genesis_error(error)
        
        # 处理其他异常
        return cls._handle_generic_error(error)
    
    @classmethod
    def _handle_genesis_error(cls, error: GenesisError) -> tuple:
        """处理Genesis自定义异常"""
        status_code = cls.ERROR_STATUS_MAP.get(error.error_code, cls.DEFAULT_STATUS)
        
        response = {
            "success": False,
            "error": {
                "code": error.error_code,
                "message": error.message,
                "details": error.details,
                "type": error.__class__.__name__,
            },
            "timestamp": cls._get_timestamp(),
            "request_id": cls._get_request_id(),
        }
        
        return jsonify(response), status_code
    
    @classmethod
    def _handle_generic_error(cls, error: Exception) -> tuple:
        """处理通用异常"""
        error_name = error.__class__.__name__
        
        # 生产环境隐藏详细错误信息
        if cls._is_production():
            message = "An internal server error occurred"
            details = {}
        else:
            message = str(error) or f"{error_name} occurred"
            details = {
                "traceback": traceback.format_exc(),
                "exception_type": error_name,
            }
        
        response = {
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": message,
                "details": details,
                "type": error_name,
            },
            "timestamp": cls._get_timestamp(),
            "request_id": cls._get_request_id(),
        }
        
        return jsonify(response), 500
    
    @classmethod
    def _log_error(cls, error: Exception):
        """记录错误日志"""
        error_name = error.__class__.__name__
        
        if isinstance(error, GenesisError):
            # 业务逻辑错误，记录为警告
            logger.warning(
                f"Business error: {error.error_code} - {error.message}",
                extra={
                    "error_code": error.error_code,
                    "details": error.details,
                    "request_path": request.path if request else None,
                }
            )
        else:
            # 系统错误，记录为错误
            logger.error(
                f"System error: {error_name} - {str(error)}",
                extra={
                    "traceback": traceback.format_exc(),
                    "request_path": request.path if request else None,
                },
                exc_info=True
            )
    
    @classmethod
    def _get_timestamp(cls) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
    
    @classmethod
    def _get_request_id(cls) -> Optional[str]:
        """获取请求ID"""
        from flask import g
        if hasattr(g, 'request_id'):
            return g.request_id
        return None
    
    @classmethod
    def _is_production(cls) -> bool:
        """检查是否为生产环境"""
        from .config import settings
        return settings.is_production
    
    @classmethod
    def error_handler(cls, func: Callable) -> Callable:
        """
        错误处理装饰器
        
        用法:
            @ErrorHandler.error_handler
            def my_endpoint():
                # 你的代码
                pass
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return cls.handle_exception(e)
        
        return wrapper
    
    @classmethod
    def register_error_handlers(cls, app):
        """
        注册错误处理器到Flask应用
        
        Args:
            app: Flask应用实例
        """
        # 注册通用错误处理器
        @app.errorhandler(Exception)
        def handle_all_errors(error):
            return cls.handle_exception(error)
        
        # 注册404错误处理器
        @app.errorhandler(404)
        def handle_not_found(error):
            response = {
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "The requested resource was not found",
                    "details": {
                        "path": request.path,
                        "method": request.method,
                    },
                    "type": "NotFound",
                },
                "timestamp": cls._get_timestamp(),
                "request_id": cls._get_request_id(),
            }
            return jsonify(response), 404
        
        # 注册405错误处理器
        @app.errorhandler(405)
        def handle_method_not_allowed(error):
            response = {
                "success": False,
                "error": {
                    "code": "METHOD_NOT_ALLOWED",
                    "message": "The method is not allowed for the requested URL",
                    "details": {
                        "path": request.path,
                        "method": request.method,
                        "allowed_methods": error.valid_methods if hasattr(error, 'valid_methods') else [],
                    },
                    "type": "MethodNotAllowed",
                },
                "timestamp": cls._get_timestamp(),
                "request_id": cls._get_request_id(),
            }
            return jsonify(response), 405
        
        logger.info("Error handlers registered")


# 导出
__all__ = ["ErrorHandler"]