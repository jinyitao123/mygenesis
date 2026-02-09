"""
Genesis Kernel Connectors - 多模态存储连接器

提供对多种存储后端的统一访问：
- Neo4jConnector: L1 状态层 (图数据库)
- PostgresConnector: L2/L3 层 (审计 + 语义记忆)
- TelemetryConnector: L4 遥测层 (时序数据) - 未来扩展

使用示例：
    from genesis.kernel.connectors import Neo4jConnector, PostgresConnector
    
    neo4j = Neo4jConnector("bolt://localhost:7687", "neo4j", "password")
    postgres = PostgresConnector("postgresql://user:pass@localhost/db")
"""

from .neo4j_connector import Neo4jConnector
from .postgres_connector import PostgresConnector

__all__ = [
    'Neo4jConnector',
    'PostgresConnector',
]
