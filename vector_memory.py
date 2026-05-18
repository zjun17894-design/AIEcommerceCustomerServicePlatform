"""
向量记忆

基于向量数据库的长期记忆。
"""
from typing import List, Optional, Dict, Any
from loguru import logger

from app.rag.embedding_service import embedding_service
from app.rag.retrieval_service import RetrievalService, retrieval_manager


class VectorMemory:
    """向量记忆"""

    def __init__(
        self,
        session_id: str,
        collection_name: str = "agent_memory"
    ):
        """
        初始化向量记忆

        Args:
            session_id: 会话 ID
            collection_name: 集合名称
        """
        self.session_id = session_id
        self.collection_name = collection_name
        self.retrieval_service: Optional[RetrievalService] = None

    async def initialize(self):
        """初始化"""
        self.retrieval_service = await retrieval_manager.get_service(self.collection_name)

    async def save(self, key: str, value: Any):
        """
        保存记忆

        Args:
            key: 键
            value: 值
        """
        if self.retrieval_service is None:
            await self.initialize()

        from app.rag.document_processor import DocumentChunk

        # 将值转换为文本
        text = self._value_to_text(value)

        # 创建文档块
        chunk = DocumentChunk(
            content=text,
            metadata={
                "key": key,
                "session_id": self.session_id,
                "type": "memory"
            }
        )

        # 添加到向量库
        await self.retrieval_service.add_documents([chunk])

        logger.debug(f"保存向量记忆: {self.session_id}/{key}")

    async def get(self, key: str) -> Optional[Any]:
        """
        获取记忆

        Args:
            key: 键

        Returns:
            值
        """
        if self.retrieval_service is None:
            await self.initialize()

        # 通过 key 检索
        results = await self.retrieval_service.retrieve(
            query=key,
            top_k=1,
            filters={"key": key, "session_id": self.session_id}
        )

        if results:
            return results[0].content

        return None

    async def search(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        搜索相关记忆

        Args:
            query: 查询
            top_k: 返回数量

        Returns:
            相关记忆列表
        """
        if self.retrieval_service is None:
            await self.initialize()

        results = await self.retrieval_service.retrieve(
            query=query,
            top_k=top_k,
            filters={"session_id": self.session_id}
        )

        return [
            {
                "content": r.content,
                "metadata": r.metadata,
                "score": r.score
            }
            for r in results
        ]

    def _value_to_text(self, value: Any) -> str:
        """
        将值转换为文本

        Args:
            value: 值

        Returns:
            文本
        """
        if isinstance(value, str):
            return value
        elif isinstance(value, dict):
            import json
            return json.dumps(value, ensure_ascii=False)
        elif isinstance(value, (list, tuple)):
            import json
            return json.dumps(value, ensure_ascii=False)
        else:
            return str(value)