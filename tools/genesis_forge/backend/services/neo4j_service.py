"""
Neo4j 服务抽象层 - 减少 genesis.kernel 依赖
"""
from typing import Optional, Dict, List, Any
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class INeo4jService(ABC):
    """Neo4j 服务接口 - 抽象层"""
    
    @abstractmethod
    def run_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        执行查询
        
        Args:
            query: Cypher 查询
            params: 查询参数
            
        Returns:
            查询结果列表
        """
        pass
    
    @abstractmethod
    def run_transaction(self, query: str, params: Optional[Dict] = None) -> bool:
        """
        执行事务
        
        Args:
            query: Cypher 查询
            params: 查询参数
            
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """检查是否已连接"""
        pass
    
    @abstractmethod
    def close(self):
        """关闭连接"""
        pass


class GenesisKernelNeo4jService(INeo4jService):
    """基于 genesis.kernel 的 Neo4j 服务实现"""
    
    def __init__(self):
        self.connector = None
        self._initialize_connector()
    
    def _initialize_connector(self):
        """初始化 Neo4j 连接器"""
        try:
            from genesis.kernel.connectors.neo4j_connector import Neo4jConnector
            from backend.core.config import settings
            
            # 使用新的配置系统
            neo4j_config = settings.get_neo4j_config()
            
            self.connector = Neo4jConnector(
                uri=neo4j_config["uri"],
                user=neo4j_config["user"],
                password=neo4j_config["password"]
            )
            logger.info(f"Neo4j service initialized (genesis.kernel backend) - URI: {neo4j_config['uri']}")
            
        except ImportError as e:
            logger.warning(f"Failed to import genesis.kernel: {e}")
            logger.info("Neo4j service will be disabled")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j connector: {e}")
    
    def run_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """执行查询"""
        if not self.is_connected():
            logger.warning("Neo4j not connected, returning empty result")
            return []
        
        try:
            if self.connector is None:
                logger.error("Neo4j connector is None")
                return []
            result = self.connector.run_query(query, params or {})
            return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return []
    
    def run_transaction(self, query: str, params: Optional[Dict] = None) -> bool:
        """执行事务"""
        if not self.is_connected():
            logger.warning("Neo4j not connected, transaction skipped")
            return False
        
        try:
            if self.connector is None:
                logger.error("Neo4j connector is None")
                return False
            self.connector.run_transaction(query, params or {})
            return True
        except Exception as e:
            logger.error(f"Transaction execution failed: {e}")
            return False
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.connector is not None
    
    def close(self):
        """关闭连接"""
        if self.connector:
            self.connector.close()
            self.connector = None


class MockNeo4jService(INeo4jService):
    """Mock Neo4j 服务 - 用于测试和开发"""
    
    def __init__(self):
        self.data = []
        self.connected = True
        logger.info("Mock Neo4j service initialized")
    
    def run_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """执行模拟查询"""
        # 返回模拟数据
        return []
    
    def run_transaction(self, query: str, params: Optional[Dict] = None) -> bool:
        """执行模拟事务"""
        return True
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.connected
    
    def close(self):
        """关闭连接"""
        self.connected = False


class Neo4jServiceFactory:
    """Neo4j 服务工厂"""
    
    @staticmethod
    def create_service(use_mock: bool = False) -> INeo4jService:
        """
        创建 Neo4j 服务实例
        
        Args:
            use_mock: 是否使用 Mock 服务
            
        Returns:
            Neo4j 服务实例
        """
        if use_mock:
            return MockNeo4jService()
        
        # 尝试使用 genesis.kernel
        try:
            return GenesisKernelNeo4jService()
        except Exception as e:
            logger.warning(f"Failed to create GenesisKernelNeo4jService: {e}")
            logger.info("Falling back to MockNeo4jService")
            return MockNeo4jService()
    
    @staticmethod
    def create_service_from_config(config: Dict[str, Any]) -> INeo4jService:
        """
        从配置创建 Neo4j 服务
        
        Args:
            config: 配置字典
            
        Returns:
            Neo4j 服务实例
        """
        use_mock = config.get('use_mock', False)
        return Neo4jServiceFactory.create_service(use_mock)


# 全局服务实例（使用工厂模式）
_neo4j_service: Optional[INeo4jService] = None


def get_neo4j_service() -> INeo4jService:
    """
    获取全局 Neo4j 服务实例（单例模式）
    
    Returns:
        Neo4j 服务实例
    """
    global _neo4j_service
    
    if _neo4j_service is None:
        from backend.core.config import settings
        
        # 根据环境决定是否使用 Mock 服务
        use_mock = settings.is_testing or (settings.is_development and settings.test_mode)
        
        _neo4j_service = Neo4jServiceFactory.create_service(
            use_mock=use_mock
        )
    
    return _neo4j_service


def reset_neo4j_service():
    """重置全局 Neo4j 服务实例（主要用于测试）"""
    global _neo4j_service
    
    if _neo4j_service:
        _neo4j_service.close()
        _neo4j_service = None
