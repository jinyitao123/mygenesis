"""
请求中间件

提供请求追踪、请求ID生成、性能监控等中间件功能。
"""

import uuid
import time
from typing import Callable
from functools import wraps

from flask import request, g, jsonify
from .logger import get_performance_logger, get_audit_logger


class RequestMiddleware:
    """请求中间件"""
    
    @staticmethod
    def request_id_middleware():
        """请求ID中间件"""
        @wraps
        def middleware(next_handler: Callable):
            def wrapper(*args, **kwargs):
                # 生成请求ID
                request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
                
                # 存储到全局上下文
                g.request_id = request_id
                
                # 添加请求ID到响应头
                response = next_handler(*args, **kwargs)
                if hasattr(response, 'headers'):
                    response.headers['X-Request-ID'] = request_id
                
                return response
            
            return wrapper
        
        return middleware
    
    @staticmethod
    def performance_middleware():
        """性能监控中间件"""
        performance_logger = get_performance_logger()
        
        @wraps
        def middleware(next_handler: Callable):
            def wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                
                try:
                    response = next_handler(*args, **kwargs)
                    elapsed_time = time.perf_counter() - start_time
                    
                    # 记录请求性能
                    performance_logger.logger.info(
                        f"Request completed: {request.method} {request.path}",
                        extra={
                            "request_method": request.method,
                            "request_path": request.path,
                            "duration_ms": round(elapsed_time * 1000, 2),
                            "status_code": response.status_code if hasattr(response, 'status_code') else 200,
                            "request_id": getattr(g, 'request_id', None),
                        }
                    )
                    
                    return response
                except Exception as e:
                    elapsed_time = time.perf_counter() - start_time
                    
                    # 记录错误请求性能
                    performance_logger.logger.error(
                        f"Request failed: {request.method} {request.path}",
                        extra={
                            "request_method": request.method,
                            "request_path": request.path,
                            "duration_ms": round(elapsed_time * 1000, 2),
                            "error": str(e),
                            "error_type": e.__class__.__name__,
                            "request_id": getattr(g, 'request_id', None),
                        },
                        exc_info=True
                    )
                    
                    raise
            
            return wrapper
        
        return middleware
    
    @staticmethod
    def audit_middleware():
        """审计中间件"""
        audit_logger = get_audit_logger()
        
        @wraps
        def middleware(next_handler: Callable):
            def wrapper(*args, **kwargs):
                # 记录请求开始
                audit_logger.log_action(
                    action="request_start",
                    resource=request.path,
                    status="started",
                    details={
                        "method": request.method,
                        "remote_addr": request.remote_addr,
                        "user_agent": request.headers.get('User-Agent'),
                    }
                )
                
                try:
                    response = next_handler(*args, **kwargs)
                    
                    # 记录请求完成
                    audit_logger.log_action(
                        action="request_complete",
                        resource=request.path,
                        status="completed",
                        details={
                            "method": request.method,
                            "status_code": response.status_code if hasattr(response, 'status_code') else 200,
                            "content_type": response.headers.get('Content-Type') if hasattr(response, 'headers') else None,
                        }
                    )
                    
                    return response
                except Exception as e:
                    # 记录请求失败
                    audit_logger.log_action(
                        action="request_failed",
                        resource=request.path,
                        status="failed",
                        details={
                            "method": request.method,
                            "error": str(e),
                            "error_type": e.__class__.__name__,
                        }
                    )
                    
                    raise
            
            return wrapper
        
        return middleware
    
    @staticmethod
    def register_middlewares(app):
        """注册所有中间件到Flask应用"""
        
        @app.before_request
        def before_request():
            """请求前处理"""
            # 生成请求ID
            request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
            g.request_id = request_id
            
            # 记录请求开始时间
            g.request_start_time = time.perf_counter()
            
            # 记录请求开始
            logger = get_performance_logger().logger
            logger.debug(
                f"Request started: {request.method} {request.path}",
                extra={
                    "request_method": request.method,
                    "request_path": request.path,
                    "remote_addr": request.remote_addr,
                    "user_agent": request.headers.get('User-Agent'),
                    "request_id": request_id,
                }
            )
        
        @app.after_request
        def after_request(response):
            """请求后处理"""
            # 计算请求耗时
            if hasattr(g, 'request_start_time'):
                elapsed_time = time.perf_counter() - g.request_start_time
                
                # 添加请求ID到响应头
                response.headers['X-Request-ID'] = g.request_id
                
                # 添加性能头
                response.headers['X-Request-Duration'] = f"{round(elapsed_time * 1000, 2)}ms"
                
                # 记录请求完成
                logger = get_performance_logger().logger
                logger.info(
                    f"Request completed: {request.method} {request.path}",
                    extra={
                        "request_method": request.method,
                        "request_path": request.path,
                        "duration_ms": round(elapsed_time * 1000, 2),
                        "status_code": response.status_code,
                        "request_id": g.request_id,
                    }
                )
            
            return response
        
        @app.teardown_request
        def teardown_request(exception=None):
            """请求清理"""
            if exception:
                logger = get_performance_logger().logger
                logger.error(
                    f"Request teardown with exception: {request.method} {request.path}",
                    extra={
                        "request_method": request.method,
                        "request_path": request.path,
                        "exception": str(exception) if exception else None,
                        "exception_type": exception.__class__.__name__ if exception else None,
                        "request_id": getattr(g, 'request_id', None),
                    },
                    exc_info=bool(exception)
                )
        
        # 记录中间件注册
        from .logger import get_logger
        get_logger(__name__).info("Request middlewares registered")


# 导出
__all__ = ["RequestMiddleware"]