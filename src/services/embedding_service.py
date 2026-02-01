"""
本地 Ollama 嵌入服务
使用本地 Ollama API 生成文本嵌入，避免依赖 OpenAI
"""

import os
import requests
import json
from typing import List
import logging

logger = logging.getLogger(__name__)


class OllamaEmbeddingService:
    """Ollama 嵌入服务"""
    
    def __init__(
        self, 
        base_url: str = None,
        model: str = None,
        api_key: str = None
    ):
        """初始化 Ollama 嵌入服务"""
        self.base_url = base_url or os.getenv("CHAT_API_BASE", "http://127.0.0.1:11434")
        self.model = model or os.getenv("EMBEDDING_MODEL", "nomic-embed-text-v2-moe")
        self.api_key = api_key or os.getenv("CHAT_API_KEY", "ollama")
        
        # 清理 URL
        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]
            
        logger.info(f"Ollama 嵌入服务初始化: {self.base_url}, 模型: {self.model}")
    
    def get_embedding(self, text: str) -> List[float]:
        """
        获取文本的向量嵌入
        
        Args:
            text: 输入文本
            
        Returns:
            向量嵌入列表
        """
        # 清理文本
        text = text.replace("\n", " ").strip()
        
        if not text:
            logger.warning("输入文本为空，返回零向量")
            return [0.0] * 768  # nomic-embed-text 默认维度
        
        try:
            # Ollama API 端点 (使用 /api/embeddings 而不是 /v1/embeddings)
            url = f"{self.base_url}/api/embeddings"
            
            headers = {
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "input": text
            }
            
            logger.debug(f"请求 Ollama 嵌入: {text[:50]}...")
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if "data" in data and len(data["data"]) > 0:
                embedding = data["data"][0]["embedding"]
                if len(embedding) == 0:
                    logger.warning("Ollama 返回空嵌入向量，使用备用嵌入")
                    return self._generate_fallback_embedding(text)
                logger.debug(f"嵌入生成成功，维度: {len(embedding)}")
                return embedding
            elif "embedding" in data:
                embedding = data["embedding"]
                if len(embedding) == 0:
                    logger.warning("Ollama 返回空嵌入向量，使用备用嵌入")
                    return self._generate_fallback_embedding(text)
                logger.debug(f"嵌入生成成功，维度: {len(embedding)}")
                return embedding
            else:
                logger.error(f"Ollama 响应格式异常: {data}")
                raise ValueError("无法从响应中提取嵌入向量")
                
        except requests.exceptions.ConnectionError:
            logger.error("无法连接到 Ollama API，请确保 Ollama 正在运行")
            return self._generate_fallback_embedding(text)
        except requests.exceptions.Timeout:
            logger.error("Ollama API 请求超时")
            return self._generate_fallback_embedding(text)
        except Exception as e:
            logger.error(f"生成嵌入失败: {e}")
            return self._generate_fallback_embedding(text)
    
    def _generate_fallback_embedding(self, text: str) -> List[float]:
        """生成备用嵌入（基于文本哈希的确定性向量）"""
        import hashlib
        import struct
        
        # 使用文本哈希生成确定性向量
        hash_obj = hashlib.sha256(text.encode('utf-8'))
        hash_bytes = hash_obj.digest()
        
        # 生成 768 维向量（模拟）
        embedding = []
        for i in range(0, min(len(hash_bytes) - 3, 1024), 4):
            # 每4个字节生成一个32位浮点数
            value_bytes = hash_bytes[i:i+4]
            if len(value_bytes) == 4:
                # 转换为 0-1 之间的浮点数
                value_int = int.from_bytes(value_bytes, byteorder='big')
                normalized = (value_int % 10000) / 10000.0
                embedding.append(float(normalized))
        
        # 如果向量长度不足，用0填充
        target_dim = 768
        while len(embedding) < target_dim:
            embedding.append(0.0)
        
        # 截断到目标维度
        embedding = embedding[:target_dim]
        
        logger.warning(f"使用备用嵌入生成，维度: {len(embedding)}")
        return embedding
    
    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量获取嵌入向量
        
        Args:
            texts: 文本列表
            
        Returns:
            嵌入向量列表
        """
        embeddings = []
        for text in texts:
            embedding = self.get_embedding(text)
            embeddings.append(embedding)
        
        logger.info(f"批量嵌入生成完成: {len(texts)} 个文本")
        return embeddings
    
    def get_embedding_dimensions(self) -> int:
        """
        获取嵌入向量的维度
        
        Returns:
            向量维度
        """
        # 测试获取一个简单文本的嵌入
        test_embedding = self.get_embedding("test")
        return len(test_embedding)


def create_embedding_service() -> OllamaEmbeddingService:
    """创建嵌入服务实例"""
    return OllamaEmbeddingService()


# 全局实例（可选）
_global_embedding_service = None

def get_embedding_service() -> OllamaEmbeddingService:
    """获取全局嵌入服务实例（单例模式）"""
    global _global_embedding_service
    if _global_embedding_service is None:
        _global_embedding_service = create_embedding_service()
    return _global_embedding_service