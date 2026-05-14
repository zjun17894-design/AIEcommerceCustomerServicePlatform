"""
LLM 工厂模块

统一管理多种 LLM 模型，支持 OpenAI 和 DashScope。
"""
from typing import Literal
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import DashScopeEmbeddings
from loguru import logger

from app.core.config import config


class LLMProvider:
    """LLM 提供商类型"""
    OPENAI = "openai"
    DASHSCOPE = "dashscope"


class LLMFactory:
    """LLM 工厂类"""

    @staticmethod
    def create_chat_llm(
        provider: Literal["openai", "dashscope"] = "openai",
        model: str | None = None,
        temperature: float = 0.7,
        streaming: bool = True,
    ) -> ChatOpenAI:
        """
        创建聊天 LLM 实例

        Args:
            provider: 提供商类型
            model: 模型名称，默认使用配置中的模型
            temperature: 温度参数
            streaming: 是否启用流式输出

        Returns:
            ChatOpenAI: LLM 实例
        """
        if provider == LLMProvider.OPENAI:
            if not config.openai_api_key:
                raise ValueError("OpenAI API Key 未配置")

            model = model or config.openai_model
            logger.info(f"创建 OpenAI LLM: {model}")

            return ChatOpenAI(
                model=model,
                api_key=config.openai_api_key,
                base_url=config.openai_api_base,
                temperature=temperature,
                streaming=streaming,
            )

        elif provider == LLMProvider.DASHSCOPE:
            if not config.dashscope_api_key:
                raise ValueError("DashScope API Key 未配置")

            model = model or config.dashscope_model
            logger.info(f"创建 DashScope LLM: {model}")

            # DashScope 兼容 OpenAI API
            return ChatOpenAI(
                model=model,
                api_key=config.dashscope_api_key,
                base_url=config.dashscope_api_base,
                temperature=temperature,
                streaming=streaming,
            )

        else:
            raise ValueError(f"不支持的 LLM 提供商: {provider}")

    @staticmethod
    def create_embedding_llm(
        provider: Literal["openai", "dashscope"] = "dashscope",
    ):
        """
        创建 Embedding LLM 实例

        Args:
            provider: 提供商类型

        Returns:
            Embedding 实例
        """
        if provider == LLMProvider.OPENAI:
            if not config.openai_api_key:
                raise ValueError("OpenAI API Key 未配置")

            logger.info("创建 OpenAI Embedding")
            return OpenAIEmbeddings(
                api_key=config.openai_api_key,
                base_url=config.openai_api_base,
            )

        elif provider == LLMProvider.DASHSCOPE:
            if not config.dashscope_api_key:
                raise ValueError("DashScope API Key 未配置")

            logger.info(f"创建 DashScope Embedding: {config.dashscope_embedding_model}")
            return DashScopeEmbeddings(
                model=config.dashscope_embedding_model,
                dashscope_api_key=config.dashscope_api_key,
            )

        else:
            raise ValueError(f"不支持的 Embedding 提供商: {provider}")


# 创建全局实例
def get_chat_llm(provider: str = "openai") -> ChatOpenAI:
    """获取聊天 LLM（从环境读取默认提供商）"""
    # 优先使用 DashScope，如果未配置则回退到 OpenAI
    if config.dashscope_api_key:
        return LLMFactory.create_chat_llm(provider="dashscope")
    return LLMFactory.create_chat_llm(provider="openai")


def get_embedding_llm():
    """获取 Embedding LLM"""
    if config.dashscope_api_key:
        return LLMFactory.create_embedding_llm(provider="dashscope")
    return LLMFactory.create_embedding_llm(provider="openai")