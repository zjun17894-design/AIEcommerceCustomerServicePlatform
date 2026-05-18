"""
对话记忆

管理 Agent 的对话历史。
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage


class ConversationMemory:
    """对话记忆"""

    def __init__(
        self,
        session_id: str,
        max_messages: int = 100,
        max_tokens: int = 4000
    ):
        """
        初始化对话记忆

        Args:
            session_id: 会话 ID
            max_messages: 最大消息数量
            max_tokens: 最大 token 数量
        """
        self.session_id = session_id
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        self.messages: List[BaseMessage] = []

    async def add_message(self, message: BaseMessage):
        """
        添加消息

        Args:
            message: 消息对象
        """
        self.messages.append(message)

        # 检查是否需要裁剪
        if len(self.messages) > self.max_messages:
            self._trim_messages()

        logger.debug(f"添加消息: {type(message).__name__}, 当前消息数: {len(self.messages)}")

    async def get_messages(self, last_n: Optional[int] = None) -> List[BaseMessage]:
        """
        获取消息

        Args:
            last_n: 获取最后 N 条消息

        Returns:
            消息列表
        """
        if last_n:
            return self.messages[-last_n:]
        return self.messages

    async def save(self, key: str, value: Any):
        """
        保存键值对

        Args:
            key: 键
            value: 值
        """
        # 简单实现：存储在内存
        if not hasattr(self, 'kv_store'):
            self.kv_store = {}
        self.kv_store[key] = value

    async def get(self, key: str) -> Any:
        """
        获取键值

        Args:
            key: 键

        Returns:
            值
        """
        if not hasattr(self, 'kv_store'):
            return None
        return self.kv_store.get(key)

    def clear(self):
        """清空所有消息"""
        self.messages = []
        if hasattr(self, 'kv_store'):
            self.kv_store.clear()
        logger.info(f"清空对话记忆: {self.session_id}")

    def _trim_messages(self):
        """裁剪消息"""
        # 保留系统消息（如果有的话）
        system_messages = [m for m in self.messages if isinstance(m, AIMessage)]
        other_messages = [m for m in self.messages if not isinstance(m, AIMessage)]

        # 保留最新的消息
        self.messages = system_messages + other_messages[-self.max_messages:]

    def to_langchain_messages(self) -> List[BaseMessage]:
        """
        转换为 LangChain 消息格式

        Returns:
            LangChain 消息列表
        """
        return self.messages

    def get_summary(self) -> Dict[str, Any]:
        """
        获取对话摘要

        Returns:
            摘要信息
        """
        human_count = sum(1 for m in self.messages if isinstance(m, HumanMessage))
        ai_count = sum(1 for m in self.messages if isinstance(m, AIMessage))

        return {
            "session_id": self.session_id,
            "message_count": len(self.messages),
            "human_count": human_count,
            "ai_count": ai_count,
            "created_at": datetime.now().isoformat()
        }