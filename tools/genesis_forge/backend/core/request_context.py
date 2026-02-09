"""
请求上下文管理器 - 解决并发环境下的状态管理问题
"""
from typing import Optional, Dict, Any
from flask import session, request
from werkzeug.local import LocalProxy


class RequestContext:
    """请求上下文管理器 - 每个请求拥有独立的领域上下文"""
    
    @staticmethod
    def get_current_domain() -> str:
        """
        获取当前请求的领域
        优先级：Session > 请求参数 > 请求体 > 默认值
        """
        if 'domain' in session and session['domain']:
            return session['domain']
        
        if request and request.args.get('domain'):
            domain = request.args.get('domain')
            if domain:
                return domain
        
        if request and request.is_json:
            try:
                json_data = request.get_json(silent=True)
                if json_data and json_data.get('domain'):
                    return json_data.get('domain')
            except:
                pass
        
        return "supply_chain"
    
    @staticmethod
    def set_current_domain(domain_name: str) -> None:
        """设置当前请求的领域（存储在 Session 中）"""
        session['domain'] = domain_name
    
    @staticmethod
    def get_user_context() -> Dict[str, Any]:
        """
        获取用户上下文信息
        TODO: 扩展以支持用户认证和权限管理
        """
        return {
            'domain': RequestContext.get_current_domain(),
            'session_id': session.get('session_id', None),
            'ip_address': request.remote_addr if request else None
        }
    
    @staticmethod
    def clear_domain() -> None:
        """清除当前领域设置"""
        session.pop('domain', None)


class DomainContextManager:
    """领域上下文管理器 - 提供线程安全的领域操作"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DomainContextManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialized = True
    
    @staticmethod
    def get_domain_context(domain_name: str) -> Dict[str, Any]:
        """
        获取领域的上下文信息
        
        Args:
            domain_name: 领域名称
            
        Returns:
            领域上下文字典
        """
        return {
            'domain_name': domain_name,
            'timestamp': None,
            'is_active': False
        }
    
    @staticmethod
    def validate_domain_access(domain_name: str, available_domains: list) -> bool:
        """
        验证是否可以访问指定领域
        
        Args:
            domain_name: 要访问的领域名称
            available_domains: 可用领域列表
            
        Returns:
            是否可以访问
        """
        return domain_name in available_domains


current_domain = LocalProxy(lambda: RequestContext.get_current_domain())
"""线程安全的当前领域代理对象"""
