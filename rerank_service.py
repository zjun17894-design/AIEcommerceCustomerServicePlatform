"""
重排服务

对检索结果进行重新排序，提高相关性。
"""
from typing import List, Optional
from loguru import logger

from app.rag.retrieval_service import RetrievalResult


class RerankService:
    """重排服务"""

    def __init__(self):
        pass

    async def rerank(
        self,
        results: List[RetrievalResult],
        query: str,
        top_k: Optional[int] = None
    ) -> List[RetrievalResult]:
        """
        重新排序检索结果

        Args:
            results: 检索结果
            query: 原始查询
            top_k: 返回数量

        Returns:
            重排后的结果
        """
        if not results:
            return results

        try:
            # TODO: 实现真实的重排算法
            # 可以使用：
            # 1. Cross-encoder 重排序
            # 2. LLM 评分重排序
            # 3. 多样性重排序

            # 当前简化版：保持原排序
            reranked = results[:top_k] if top_k else results

            logger.debug(f"重排完成: 返回 {len(reranked)} 条结果")
            return reranked

        except Exception as e:
            logger.error(f"重排失败: {e}")
            # 返回原始结果
            return results[:top_k] if top_k else results

    def calculate_diversity_score(
        self,
        results: List[RetrievalResult]
    ) -> float:
        """
        计算多样性分数

        Args:
            results: 检索结果

        Returns:
            多样性分数
        """
        if len(results) <= 1:
            return 1.0

        # 简单多样性计算：基于元数据差异
        metadata_keys = set()
        for result in results:
            metadata_keys.update(result.metadata.keys())

        diversity = len(metadata_keys) / max(len(results), 1)
        return min(diversity, 1.0)

    def deduplicate(
        self,
        results: List[RetrievalResult],
        threshold: float = 0.95
    ) -> List[RetrievalResult]:
        """
        去重

        Args:
            results: 检索结果
            threshold: 相似度阈值

        Returns:
            去重后的结果
        """
        if not results:
            return results

        # 简单去重：基于内容
        seen_contents = set()
        unique_results = []

        for result in results:
            content_hash = hash(result.content)
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                unique_results.append(result)

        logger.debug(f"去重: {len(results)} -> {len(unique_results)}")
        return unique_results


# 全局单例
rerank_service = RerankService()