"""
自定义异常类 - 用于精细化错误处理
"""
from typing import Optional, Dict, Any


class GenesisError(Exception):
    """基础异常类"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }


class DomainError(GenesisError):
    """领域相关异常"""
    
    def __init__(self, message: str, domain_name: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DOMAIN_ERROR", details)
        self.domain_name = domain_name


class DomainNotFoundError(DomainError):
    """领域不存在异常"""
    
    def __init__(self, domain_name: str):
        super().__init__(f"Domain not found: {domain_name}", domain_name)
        self.error_code = "DOMAIN_NOT_FOUND"


class SchemaValidationError(GenesisError):
    """Schema 验证异常"""
    
    def __init__(self, message: str, validation_errors: Optional[list] = None):
        details = {"validation_errors": validation_errors} if validation_errors else {}
        super().__init__(message, "SCHEMA_VALIDATION_ERROR", details)


class DataInconsistencyError(GenesisError):
    """数据不一致异常"""
    
    def __init__(self, message: str, source: Optional[str] = None, target: Optional[str] = None):
        details = {}
        if source:
            details["source"] = source
        if target:
            details["target"] = target
        super().__init__(message, "DATA_INCONSISTENCY_ERROR", details)


class SecurityError(GenesisError):
    """安全异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "SECURITY_ERROR", details)


class CypherInjectionError(SecurityError):
    """Cypher 注入异常"""
    
    def __init__(self, query: str, reason: Optional[str] = None):
        details = {"query": query}
        if reason:
            details["reason"] = reason
        super().__init__(f"Potential Cypher injection detected", details)
        self.error_code = "CYPHER_INJECTION"


class PathTraversalError(SecurityError):
    """路径遍历异常"""
    
    def __init__(self, path: str, reason: Optional[str] = None):
        details = {"path": path}
        if reason:
            details["reason"] = reason
        super().__init__(f"Path traversal detected", details)
        self.error_code = "PATH_TRAVERSAL"


class TransactionError(GenesisError):
    """事务异常"""
    
    def __init__(self, message: str, operations: Optional[list] = None):
        details = {"failed_operations": operations} if operations else {}
        super().__init__(message, "TRANSACTION_ERROR", details)


class Neo4jError(GenesisError):
    """Neo4j 相关异常"""
    
    def __init__(self, message: str, query: Optional[str] = None):
        details = {"query": query} if query else {}
        super().__init__(message, "NEO4J_ERROR", details)
