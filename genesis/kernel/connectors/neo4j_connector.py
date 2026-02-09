"""
Neo4j Connector - Neo4j 连接器 (L1 状态层)

职责：
- 连接 Neo4j 图数据库
- 执行 Cypher 查询和事务
- 管理数据库连接生命周期
"""

from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase, Driver
import logging

logger = logging.getLogger(__name__)


class Neo4jConnector:
    """Neo4j 连接器 - L1 状态层"""
    
    def __init__(self, uri: str, user: str, password: str):
        """初始化 Neo4j 连接器"""
        self.uri = uri
        self.user = user
        self.password = password
        self._driver: Optional[Driver] = None
        self._connect()
    
    def _connect(self):
        """建立数据库连接"""
        try:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # 验证连接
            with self._driver.session() as session:
                result = session.run("RETURN 1 as connected")
                record = result.single()
                if record and record.get("connected") == 1:
                    logger.info(f"[Neo4jConnector] Connected to {self.uri}")
        except Exception as e:
            logger.error(f"[Neo4jConnector] Connection failed: {e}")
            raise
    
    @property
    def driver(self) -> Driver:
        """获取驱动实例"""
        if self._driver is None:
            self._connect()
        return self._driver  # type: ignore
    
    def run_query(self, cypher_query: Any, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """执行只读查询"""
        params = params or {}
        
        with self.driver.session() as session:
            result = session.run(cypher_query, params)
            return [record.data() for record in result]
    
    def run_transaction(self, cypher_query: Any, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """执行写入事务"""
        params = params or {}
        
        def _tx_func(tx, query: Any, parameters: Dict[str, Any]):
            result = tx.run(query, parameters)
            return [record.data() for record in result]
        
        with self.driver.session() as session:
            return session.execute_write(_tx_func, cypher_query, params)
    
    def execute_write(self, cypher_query: Any, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """执行写入操作（别名）"""
        return self.run_transaction(cypher_query, params)
    
    def clear_database(self):
        """清空整个数据库（危险操作！）"""
        logger.warning("[Neo4jConnector] Clearing database...")
        self.run_transaction("MATCH (n) DETACH DELETE n")
        logger.info("[Neo4jConnector] Database cleared")
    
    def verify_connectivity(self) -> bool:
        """验证连接是否正常"""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as connected")
                record = result.single()
                return record is not None and record.get("connected") == 1
        except Exception:
            return False
    
    def close(self):
        """关闭连接"""
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("[Neo4jConnector] Connection closed")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()
