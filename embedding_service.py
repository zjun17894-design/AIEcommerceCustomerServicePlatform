"""
向量化服务

提供文本向量化功能。
"""
from typing import List
from loguru import logger

from langchain_community.embeddings import DashScopeEmbeddings
from langchain_openai import OpenAIEmbeddings

from app.core.config import config
from app.core.llm_factory import LLMProvider


class EmbeddingService:
    """向量化服务"""

    def __init__(self, provider: str = "dashscope"):
        """
        初始化服务

        Args:
            provider: 提供商
        """
        self.provider = provider
        self.embedding = self._create_embedding()
        logger.info(f"Embedding 服务初始化完成: {provider}")

    def _create_embedding(self):
        """创建 Embedding 实例"""
        if self.provider == LLMProvider.DASHSCOPE:
            if not config.dashscope_api_key:
                raise ValueError("DashScope API Key 未配置")

            return DashScopeEmbeddings(
                model=config.dashscope_embedding_model,
                dashscope_api_key=config.dashscope_api_key,
            )

        elif self.provider == LLMProvider.OPENAI:
            if not config.openai_api_key:
                raise ValueError("OpenAI API Key 未配置")

            return OpenAIEmbeddings(
                api_key=config.openai_api_key,
                base_url=config.openai_api_base,
            )

        else:
            raise ValueError(f"不支持的 Embedding 提供商: {self.provider}")

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        批量向量化文档

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        try:
            # Embedding API 是同步的，需要在异步环境中包装
            def embed():
                return self.embedding.embed_documents(texts)

            # 在线程池中执行
            loop = asyncio.get_event_loop()
            vectors = await loop.run_in_executor(None, embed)

            logger.debug(f"向量化 {len(texts)} 个文档")
            return vectors

        except Exception as e:
            logger.error(f"文档向量化失败: {e}")
            raise

    async def embed_query(self, text: str) -> List[float]:
        """
        向量化查询

        Args:
            text: 查询文本

        Returns:
            向量
        """
        try:
            def embed():
                return self.embedding.embed_query(text)

            loop = asyncio.get_event_loop()
            vector = await loop.run_in_executor(None, embed)

            logger.debug(f"向量化查询: {text[:50]}...")
            return vector

        except Exception as e:
            logger.error(f"查询向量化失败: {e}")
            raise

    async def embed_text(self, text: str) -> List[float]:
        """
        向量化单条文本（别名）

        Args:
            text: 文本

        Returns:
            向量
        """
        return await self.embed_query(text)

    def get_dimension(self) -> int:
        """
        获取向量维度

        Returns:
            向量维度
        """
        # 测试向量化获取维度
        test_vector = self.embedding.embed_query("test")
        return len(test_vector)


# 全局单例
embedding_service = EmbeddingService(provider="dashscope")