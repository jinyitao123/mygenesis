"""
服务层模块
包含各种外部服务集成
"""

from .embedding_service import OllamaEmbeddingService, create_embedding_service, get_embedding_service
from .vector_client import VectorClient, Memory

__all__ = [
    'OllamaEmbeddingService',
    'create_embedding_service',
    'get_embedding_service',
    'VectorClient',
    'Memory'
]