"""
RAG 引擎

提供统一的 RAG 查询接口。
"""
from typing import List, Optional, Dict, Any
from loguru import logger

from app.rag.retrieval_service import RetrievalService, RetrievalResult, retrieval_manager
from app.rag.rerank_service import rerank_service
from app.core.llm_factory import LLMFactory
from langchain_core.messages import SystemMessage, HumanMessage


class RAGEngine:
    """RAG 引擎"""

    def __init__(
        self,
        collection_name: str = "default",
        top_k: int = 3,
        use_rerank: bool = True
    ):
        """
        初始化引擎

        Args:
            collection_name: 集合名称
            top_k: 检索数量
            use_rerank: 是否使用重排
        """
        self.collection_name = collection_name
        self.top_k = top_k
        self.use_rerank = use_rerank
        self.retrieval_service: Optional[RetrievalService] = None

    async def initialize(self):
        """初始化引擎"""
        self.retrieval_service = await retrieval_manager.get_service(self.collection_name)
        logger.info(f"RAG 引擎初始化完成: {self.collection_name}")

    async def query(
        self,
        question: str,
        context_length: int = 2000
    ) -> Dict[str, Any]:
        """
        RAG 查询

        Args:
            question: 用户问题
            context_length: 上下文最大长度

        Returns:
            查询结果
        """
        if self.retrieval_service is None:
            await self.initialize()

        try:
            # 1. 检索相关文档
            results = await self.retrieval_service.retrieve(question, top_k=self.top_k)

            if not results:
                return {
                    "answer": "没有找到相关信息。",
                    "context": "",
                    "sources": []
                }

            # 2. 重排
            if self.use_rerank:
                results = await rerank_service.rerank(results, question, top_k=self.top_k)

            # 3. 构建上下文
            context = self._build_context(results, context_length)

            # 4. 生成回答（使用 LLM）
            answer = await self._generate_answer(question, context)

            # 5. 构建来源信息
            sources = [r.metadata for r in results]

            return {
                "answer": answer,
                "context": context,
                "sources": sources
            }

        except Exception as e:
            logger.error(f"RAG 查询失败: {e}")
            return {
                "answer": f"查询失败: {str(e)}",
                "context": "",
                "sources": []
            }

    async def query_with_sources(
        self,
        question: str
    ) -> Dict[str, Any]:
        """
        带来源的 RAG 查询

        Args:
            question: 用户问题

        Returns:
            查询结果（含来源）
        """
        result = await self.query(question)
        result["formatted_sources"] = self._format_sources(result["sources"])
        return result

    async def add_document(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        添加文档

        Args:
            content: 文档内容
            metadata: 元数据

        Returns:
            文档 ID 列表
        """
        if self.retrieval_service is None:
            await self.initialize()

        from app.rag.document_processor import DocumentProcessor, DocumentChunk

        processor = DocumentProcessor()
        chunks = await processor.process_text(content, metadata)

        doc_ids = await self.retrieval_service.add_documents(chunks)
        return doc_ids

    def _build_context(
        self,
        results: List[RetrievalResult],
        max_length: int
    ) -> str:
        """
        构建上下文

        Args:
            results: 检索结果
            max_length: 最大长度

        Returns:
            上下文文本
        """
        context_parts = []

        for i, result in enumerate(results, 1):
            context_parts.append(f"[资料 {i}] {result.content}")

        context = "\n\n".join(context_parts)

        # 截断到最大长度
        if len(context) > max_length:
            context = context[:max_length] + "..."

        return context

    async def _generate_answer(
        self,
        question: str,
        context: str
    ) -> str:
        """
        生成回答

        Args:
            question: 问题
            context: 上下文

        Returns:
            回答文本
        """
        try:
            # 获取 LLM
            llm = LLMFactory.create_chat_llm(provider="dashscope", streaming=False)

            # 构建提示词
            system_prompt = """你是一个专业的客服助手。请根据提供的参考资料回答用户的问题。

要求：
1. 基于参考资料回答，不要编造信息
2. 如果参考资料中没有相关信息，请诚实告知
3. 回答要简洁、准确、有帮助
4. 必要时可以引用参考资料的内容

参考资料：
{context}"""

            prompt = system_prompt.format(context=context)

            messages = [
                SystemMessage(content=prompt),
                HumanMessage(content=question)
            ]

            # 生成回答
            response = await llm.ainvoke(messages)
            return response.content

        except Exception as e:
            logger.error(f"生成回答失败: {e}")
            return f"生成回答失败: {str(e)}"

    def _format_sources(
        self,
        sources: List[Dict[str, Any]]
    ) -> str:
        """
        格式化来源

        Args:
            sources: 来源列表

        Returns:
            格式化文本
        """
        formatted = []
        for i, source in enumerate(sources, 1):
            formatted.append(f"{i}. {source.get('source', '未知来源')}")

        return "\n".join(formatted)


class RAGEngineManager:
    """RAG 引擎管理器"""

    def __init__(self):
        self.engines: Dict[str, RAGEngine] = {}

    async def get_engine(self, collection_name: str) -> RAGEngine:
        """
        获取或创建 RAG 引擎

        Args:
            collection_name: 集合名称

        Returns:
            RAG 引擎
        """
        if collection_name not in self.engines:
            engine = RAGEngine(collection_name=collection_name)
            await engine.initialize()
            self.engines[collection_name] = engine

        return self.engines[collection_name]


# 全局单例
rag_engine_manager = RAGEngineManager()