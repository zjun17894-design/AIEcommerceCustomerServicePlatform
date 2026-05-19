"""
检索服务

提供向量检索功能。
"""
from typing import List, Optional, Dict, Any
from pymilvus import Collection
from loguru import logger

from app.core.milvus_client import milvus_client
from app.core.config import config
from app.rag.embedding_service import embedding_service
from app.rag.document_processor import DocumentChunk


class RetrievalResult:
    """检索结果"""

    def __init__(
        self,
        content: str,
        metadata: Dict[str, Any],
        score: float
    ):
        self.content = content
        self.metadata = metadata
        self.score = score

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "content": self.content,
            "metadata": self.metadata,
            "score": self.score
        }


class RetrievalService:
    """检索服务"""

    def __init__(self, collection_name: str = "default"):
        """
        初始化服务

        Args:
            collection_name: 集合名称
        """
        self.collection_name = collection_name
        self.collection: Optional[Collection] = None
        self.top_k = config.rag_top_k

    async def initialize(self):
        """初始化服务"""
        try:
            # 获取集合
            self.collection = milvus_client.get_collection(self.collection_name)
            logger.info(f"检索服务初始化完成: {self.collection_name}")
        except Exception as e:
            logger.error(f"检索服务初始化失败: {e}")
            # 尝试创建集合
            try:
                dimension = embedding_service.get_dimension()
                milvus_client.create_collection(
                    self.collection_name,
                    dimension=dimension
                )
                self.collection = milvus_client.get_collection(self.collection_name)
                logger.info(f"创建新集合: {self.collection_name}")
            except Exception as e2:
                logger.error(f"创建集合失败: {e2}")
                raise

    async def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """
        检索相关文档

        Args:
            query: 查询文本
            top_k: 返回数量
            filters: 过滤条件

        Returns:
            检索结果列表
        """
        if self.collection is None:
            await self.initialize()

        top_k = top_k or self.top_k

        try:
            # 向量化查询
            query_vector = await embedding_service.embed_query(query)

            # 构建搜索表达式
            expr = self._build_filter_expression(filters)

            # 执行检索
            results = self.collection.search(
                data=[query_vector],
                anns_field="vector",
                param={"metric_type": "COSINE", "params": {"nprobe": 10}},
                limit=top_k,
                expr=expr,
                output_fields=["content", "metadata"]
            )

            # 解析结果
            retrieval_results = []
            for hit in results[0]:
                retrieval_results.append(RetrievalResult(
                    content=hit.entity.get("content"),
                    metadata=hit.entity.get("metadata", {}),
                    score=hit.distance
                ))

            logger.info(f"检索完成: 查询='{query[:30]}...', 返回 {len(retrieval_results)} 条结果")
            return retrieval_results

        except Exception as e:
            logger.error(f"检索失败: {e}")
            raise

    async def hybrid_retrieve(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> List[RetrievalResult]:
        """
        混合检索（向量 + 关键词）

        Args:
            query: 查询文本
            top_k: 返回数量

        Returns:
            检索结果列表
        """
        # TODO: 实现混合检索
        # 当前简化为向量检索
        return await self.retrieve(query, top_k=top_k)

    async def add_documents(
        self,
        chunks: List[DocumentChunk]
    ) -> List[str]:
        """
        添加文档到向量库

        Args:
            chunks: 文档块列表

        Returns:
            文档 ID 列表
        """
        if self.collection is None:
            await self.initialize()

        try:
            # 批量向量化
            texts = [chunk.content for chunk in chunks]
            vectors = await embedding_service.embed_documents(texts)

            # 准备数据
            ids = []
            for i, chunk in enumerate(chunks):
                if chunk.id is None:
                    import uuid
                    chunk.id = str(uuid.uuid4())
                ids.append(chunk.id)

            # 插入数据
            data = [
                ids,
                texts,
                [chunk.metadata for chunk in chunks],
                vectors
            ]

            self.collection.insert(data)
            self.collection.flush()

            logger.info(f"添加 {len(chunks)} 个文档到向量库: {self.collection_name}")
            return ids

        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            raise

    async def delete_documents(self, doc_ids: List[str]) -> bool:
        """
        删除文档

        Args:
            doc_ids: 文档 ID 列表

        Returns:
            是否删除成功
        """
        if self.collection is None:
            await self.initialize()

        try:
            # 构建删除表达式
            ids_str = ", ".join([f"'{id}'" for id in doc_ids])
            expr = f"id in [{ids_str}]"

            self.collection.delete(expr)
            self.collection.flush()

            logger.info(f"删除 {len(doc_ids)} 个文档")
            return True

        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False

    def _build_filter_expression(self, filters: Optional[Dict[str, Any]]) -> str:
        """
        构建过滤表达式

        Args:
            filters: 过滤条件

        Returns:
            Milvus 过滤表达式
        """
        if not filters:
            return ""

        expressions = []

        for key, value in filters.items():
            # 字符串类型
            if isinstance(value, str):
                expressions.append(f'metadata["{key}"] == "{value}"')
            # 数字类型
            elif isinstance(value, (int, float)):
                expressions.append(f'metadata["{key}"] == {value}')
            # 布尔类型
            elif isinstance(value, bool):
                expressions.append(f'metadata["{key}"] == {str(value).lower()}')
            # 列表类型（in 查询）
            elif isinstance(value, list):
                value_str = ", ".join([f'"{v}"' if isinstance(v, str) else str(v) for v in value])
                expressions.append(f'metadata["{key}"] in [{value_str}]')

        return " and ".join(expressions) if expressions else ""


class RetrievalManager:
    """检索管理器（管理多个检索服务）"""

    def __init__(self):
        self.services: Dict[str, RetrievalService] = {}

    async def get_service(self, collection_name: str) -> RetrievalService:
        """
        获取或创建检索服务

        Args:
            collection_name: 集合名称

        Returns:
            检索服务
        """
        if collection_name not in self.services:
            service = RetrievalService(collection_name)
            await service.initialize()
            self.services[collection_name] = service

        return self.services[collection_name]


# 全局单例
retrieval_manager = RetrievalManager()