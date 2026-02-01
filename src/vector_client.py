"""
Vector Client - 游戏的"右脑" (感性脑)

负责记忆、语义检索、长期对话历史。
使用 PostgreSQL + pgvector 存储向量嵌入。

与 Neo4j (左脑/逻辑脑) 形成双脑架构：
- Neo4j: 逻辑、关系、当前状态
- Postgres/pgvector: 记忆、语义、历史上下文
"""

import os
from typing import List, Dict, Optional
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()


class Memory(Base):
    """记忆表：存储对话历史和世界知识"""
    __tablename__ = 'memories'
    
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)              # 记忆文本内容
    embedding = Column(Vector(1536), nullable=False)    # OpenAI 向量 (text-embedding-3-small)
    metadata_ = Column("metadata", JSONB, default={})   # 元数据：{'source': 'dialogue', 'npc': '卫兵'}
    
    def __repr__(self):
        return f"<Memory(id={self.id}, content='{self.content[:30]}...')>"


class VectorClient:
    """
    向量数据库客户端 (右脑)
    
    职责：
    1. 存储记忆 (对话历史、世界知识)
    2. 语义检索 (基于向量相似度)
    3. 长期记忆管理
    """
    
    def __init__(self, db_url: Optional[str] = None):
        """
        初始化向量数据库连接
        
        Args:
            db_url: PostgreSQL 连接 URL
                   默认: postgresql://postgres:kimyitao@localhost:5432/smartcleankb
        """
        self.db_url = db_url or os.getenv(
            "PGVECTOR_URL", 
            "postgresql://postgres:kimyitao@localhost:5432/smartcleankb"
        )
        
        # 适配 SQLAlchemy 同步模式
        sync_db_url = self.db_url.replace("+asyncpg", "")
        
        self.engine = create_engine(sync_db_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
        
        # 延迟初始化 OpenAI 客户端 (避免在导入时出错)
        self._openai_client = None
        
        # 自动建表
        self._setup_database()
        
        logger.info("右脑 (VectorClient) 初始化完成")
    
    @property
    def openai_client(self):
        """延迟加载 OpenAI 客户端"""
        if self._openai_client is None:
            import openai
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("必须设置 OPENAI_API_KEY 环境变量")
            self._openai_client = openai.OpenAI(api_key=api_key)
        return self._openai_client
    
    def _setup_database(self):
        """设置数据库：建表 + 启用 pgvector 扩展"""
        try:
            # 启用 pgvector 扩展
            with self.engine.connect() as conn:
                conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector")
                conn.commit()
            
            # 自动建表
            Base.metadata.create_all(self.engine)
            logger.info("记忆表创建/验证完成")
            
        except Exception as e:
            logger.error(f"数据库设置失败: {e}")
            raise
    
    def _get_embedding(self, text: str) -> List[float]:
        """
        获取文本的向量嵌入
        
        Args:
            text: 输入文本
        
        Returns:
            1536维向量
        """
        # 清理文本
        text = text.replace("\n", " ").strip()
        
        try:
            response = self.openai_client.embeddings.create(
                input=[text],
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"生成嵌入失败: {e}")
            raise
    
    def add_memory(self, content: str, meta: Optional[Dict] = None) -> int:
        """
        写入一条新记忆
        
        Args:
            content: 记忆文本内容 (如对话记录)
            meta: 元数据字典 {'source': 'dialogue', 'npc': '卫兵', 'location': '王宫'}
        
        Returns:
            记忆ID
        """
        try:
            embedding = self._get_embedding(content)
            
            session = self.Session()
            memory = Memory(
                content=content,
                embedding=embedding,
                metadata_=meta or {}
            )
            session.add(memory)
            session.commit()
            memory_id = memory.id
            session.close()
            
            logger.info(f"记忆已存储 (id={memory_id}): {content[:50]}...")
            return memory_id
            
        except Exception as e:
            logger.error(f"存储记忆失败: {e}")
            raise
    
    def search_memory(self, query_text: str, limit: int = 3) -> List[str]:
        """
        语义检索：根据查询文本找到相关记忆
        
        Args:
            query_text: 查询文本 (如 "那个态度很差的卫兵")
            limit: 返回的记忆条数
        
        Returns:
            记忆内容列表
        """
        try:
            query_embedding = self._get_embedding(query_text)
            
            session = self.Session()
            
            # 使用 pgvector 的余弦距离进行相似度排序
            # cosine_distance: 0=完全相同, 2=完全相反
            results = session.query(Memory).order_by(
                Memory.embedding.cosine_distance(query_embedding)
            ).limit(limit).all()
            
            memories = [r.content for r in results]
            session.close()
            
            logger.info(f"记忆检索: '{query_text[:30]}...' -> 找到 {len(memories)} 条")
            return memories
            
        except Exception as e:
            logger.error(f"检索记忆失败: {e}")
            return []
    
    def search_memory_with_meta(self, query_text: str, limit: int = 3) -> List[Dict]:
        """
        语义检索（带元数据）
        
        Returns:
            [{'content': '...', 'metadata': {...}}, ...]
        """
        try:
            query_embedding = self._get_embedding(query_text)
            
            session = self.Session()
            results = session.query(Memory).order_by(
                Memory.embedding.cosine_distance(query_embedding)
            ).limit(limit).all()
            
            memories = [
                {'content': r.content, 'metadata': dict(r.metadata_)}
                for r in results
            ]
            session.close()
            
            return memories
            
        except Exception as e:
            logger.error(f"检索记忆失败: {e}")
            return []
    
    def get_recent_memories(self, limit: int = 5) -> List[str]:
        """
        获取最近的记忆（按时间倒序）
        
        Args:
            limit: 条数
        
        Returns:
            记忆内容列表
        """
        try:
            session = self.Session()
            results = session.query(Memory).order_by(
                Memory.id.desc()
            ).limit(limit).all()
            
            memories = [r.content for r in results]
            session.close()
            
            return memories
            
        except Exception as e:
            logger.error(f"获取最近记忆失败: {e}")
            return []
    
    def clear_all_memories(self):
        """清空所有记忆（慎用！）"""
        try:
            session = self.Session()
            session.query(Memory).delete()
            session.commit()
            session.close()
            logger.warning("所有记忆已清空！")
            
        except Exception as e:
            logger.error(f"清空记忆失败: {e}")
            raise
