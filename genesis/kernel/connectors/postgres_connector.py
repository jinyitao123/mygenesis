"""
PostgreSQL Connector - PostgreSQL 连接器 (L2 审计层 + L3 认知层)

职责：
- L2: Event Ledger (append-only 事件记录)
- L3: Semantic Memory (向量存储的语义记忆)
- 支持 pgvector 扩展

设计原则：
- Event Ledger 只追加，不可变
- Semantic Memory 支持向量相似度检索
- 使用 SQLAlchemy + psycopg2
"""

from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import create_engine, text, Column, String, DateTime, Float, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()


class EventLedger(Base):
    """L2: 事件账本表"""
    __tablename__ = 'event_ledger'
    
    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    action_type = Column(String(64), nullable=False)
    action_id = Column(String(64), nullable=False)
    initiator_id = Column(String(64), nullable=False)
    initiator_name = Column(String(128))
    target_id = Column(String(64))
    target_name = Column(String(128))
    summary = Column(String(500))
    context = Column(JSONB)
    changes = Column(JSONB)


class SemanticMemory(Base):
    """L3: 语义记忆表"""
    __tablename__ = 'semantic_memory'
    
    memory_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(String(64))
    memory_type = Column(String(32), nullable=False)  # 'dialogue', 'lore', 'event'
    content = Column(String(2000), nullable=False)
    embedding = Column(String)  # 存储为字符串，实际使用时转换
    importance = Column(Float, default=1.0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class PostgresConnector:
    """PostgreSQL 连接器 - L2/L3 层"""
    
    def __init__(self, connection_url: str):
        """
        初始化 PostgreSQL 连接器
        
        Args:
            connection_url: PostgreSQL 连接 URL
                例如: postgresql://user:password@localhost:5432/dbname
        """
        self.connection_url = connection_url
        self.engine = create_engine(connection_url, pool_pre_ping=True)
        self.Session = sessionmaker(bind=self.engine)
        
        # 验证连接
        self._verify_connection()
        
        # 确保表存在
        self._init_schema()
        
        logger.info(f"[PostgresConnector] Connected to PostgreSQL")
    
    @property
    def available(self) -> bool:
        """检查连接是否可用"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                return True
        except Exception:
            return False
    
    def _verify_connection(self):
        """验证数据库连接"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.scalar()
                if version:
                    logger.info(f"[PostgresConnector] PostgreSQL version: {str(version)[:50]}...")
        except Exception as e:
            logger.error(f"[PostgresConnector] Connection failed: {e}")
            raise
    
    def _init_schema(self):
        """初始化数据库 Schema"""
        try:
            # 创建 pgvector 扩展
            with self.engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
            
            # 创建表
            Base.metadata.create_all(self.engine)
            logger.info("[PostgresConnector] Schema initialized")
        except Exception as e:
            logger.error(f"[PostgresConnector] Schema init failed: {e}")
            raise
    
    # ============== L2: Event Ledger 方法 ==============
    
    def log_event(self, event_data: Dict[str, Any]) -> str:
        """
        记录事件到 Event Ledger
        
        Args:
            event_data: 事件数据
                - action_type: 动作类型
                - action_id: 动作ID
                - initiator_id: 发起者ID
                - initiator_name: 发起者名称
                - target_id: 目标ID (可选)
                - target_name: 目标名称 (可选)
                - summary: 事件摘要
                - context: 上下文 (JSON)
                - changes: 变更 (JSON)
                
        Returns:
            event_id: 事件UUID
        """
        session = self.Session()
        try:
            event = EventLedger(
                event_id=uuid.uuid4(),
                action_type=event_data.get('action_type', 'UNKNOWN'),
                action_id=event_data.get('action_id', ''),
                initiator_id=event_data.get('initiator_id', ''),
                initiator_name=event_data.get('initiator_name'),
                target_id=event_data.get('target_id'),
                target_name=event_data.get('target_name'),
                summary=event_data.get('summary', ''),
                context=event_data.get('context', {}),
                changes=event_data.get('changes', {})
            )
            session.add(event)
            session.commit()
            event_id = str(event.event_id)
            logger.debug(f"[PostgresConnector] Event logged: {event_id}")
            return event_id
        except Exception as e:
            session.rollback()
            logger.error(f"[PostgresConnector] Failed to log event: {e}")
            raise
        finally:
            session.close()
    
    def get_history(self, entity_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        查询实体的历史事件
        
        Args:
            entity_id: 实体ID
            limit: 返回条数限制
            
        Returns:
            事件列表
        """
        session = self.Session()
        try:
            events = session.query(EventLedger).filter(
                (EventLedger.initiator_id == entity_id) | 
                (EventLedger.target_id == entity_id)
            ).order_by(EventLedger.timestamp.desc()).limit(limit).all()
            
            return [
                {
                    'event_id': str(e.event_id),
                    'timestamp': e.timestamp.isoformat() if e.timestamp is not None else None,
                    'action_type': e.action_type,
                    'summary': e.summary,
                    'initiator_name': e.initiator_name,
                    'target_name': e.target_name
                }
                for e in events
            ]
        finally:
            session.close()
    
    # ============== L3: Semantic Memory 方法 ==============
    
    def memorize(self, content: str, embedding: Optional[List[float]] = None,
                 entity_id: Optional[str] = None, memory_type: str = 'observation') -> str:
        """
        存储语义记忆
        
        Args:
            content: 记忆内容
            embedding: 向量嵌入 (可选)
            entity_id: 关联实体ID (可选)
            memory_type: 记忆类型 ('dialogue', 'lore', 'event', 'observation')
            
        Returns:
            memory_id: 记忆UUID
        """
        session = self.Session()
        try:
            # 将 embedding 转换为字符串存储
            embedding_str = str(embedding) if embedding else None
            
            memory = SemanticMemory(
                memory_id=uuid.uuid4(),
                entity_id=entity_id,
                memory_type=memory_type,
                content=content,
                embedding=embedding_str,
                importance=1.0
            )
            session.add(memory)
            session.commit()
            memory_id = str(memory.memory_id)
            logger.debug(f"[PostgresConnector] Memory stored: {memory_id}")
            return memory_id
        except Exception as e:
            session.rollback()
            logger.error(f"[PostgresConnector] Failed to store memory: {e}")
            raise
        finally:
            session.close()
    
    def search_memory(self, query_embedding: List[float], entity_id: Optional[str] = None,
                     limit: int = 5) -> List[Dict[str, Any]]:
        """
        向量相似度检索语义记忆
        
        注意: 这是一个简化实现，没有真正的向量检索。
        生产环境应该使用 pgvector 的向量操作符。
        
        Args:
            query_embedding: 查询向量
            entity_id: 限制特定实体的记忆 (可选)
            limit: 返回条数
            
        Returns:
            记忆列表
        """
        session = self.Session()
        try:
            query = session.query(SemanticMemory)
            
            if entity_id:
                query = query.filter(SemanticMemory.entity_id == entity_id)
            
            # 简化: 按时间倒序返回最近的记忆
            # 生产环境应该使用向量相似度计算
            memories = query.order_by(SemanticMemory.created_at.desc()).limit(limit).all()
            
            return [
                {
                    'memory_id': str(m.memory_id),
                    'entity_id': m.entity_id,
                    'memory_type': m.memory_type,
                    'content': m.content,
                    'created_at': m.created_at.isoformat() if m.created_at is not None else None,
                    'importance': m.importance
                }
                for m in memories
            ]
        finally:
            session.close()
    
    def clear_memories(self, entity_id: Optional[str] = None):
        """清空记忆（危险操作！）"""
        session = self.Session()
        try:
            if entity_id:
                session.query(SemanticMemory).filter(
                    SemanticMemory.entity_id == entity_id
                ).delete()
            else:
                session.query(SemanticMemory).delete()
            session.commit()
            logger.warning(f"[PostgresConnector] Memories cleared for entity: {entity_id}")
        finally:
            session.close()
    
    def close(self):
        """关闭连接"""
        self.engine.dispose()
        logger.info("[PostgresConnector] Connection closed")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()
