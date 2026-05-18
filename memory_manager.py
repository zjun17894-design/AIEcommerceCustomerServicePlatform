"""
记忆管理器

统一管理 Agent 的各种记忆类型。
"""
from typing import Optional, Dict, Any
from loguru import logger

from app.memory.conversation_memory import ConversationMemory
from app.memory.vector_memory import VectorMemory


class MemoryType:
    """记忆类型"""
    CONVERSATION = "conversation"  # 对话记忆
    VECTOR = "vector"              # 向量记忆
    EPISODIC = "episodic"          # 情景记忆（未来扩展）
    SEMANTIC = "semantic"          # 语义记忆（未来扩展）


class MemoryManager:
    """记忆管理器"""

    def __init__(self):
        self.memories: Dict[str, Any] = {}

    def get_memory_instance(self, memory_type: str, **kwargs) -> Any:
        """
        获取记忆实例

        Args:
            memory_type: 记忆类型
            **kwargs: 其他参数

        Returns:
            记忆实例
        """
        # 简单的缓存机制
        cache_key = f"{memory_type}_{kwargs.get('session_id', 'default')}"

        if cache_key in self.memories:
            return self.memories[cache_key]

        # 创建新实例
        if memory_type == MemoryType.CONVERSATION:
            memory = ConversationMemory(**kwargs)
        elif memory_type == MemoryType.VECTOR:
            memory = VectorMemory(**kwargs)
        else:
            raise ValueError(f"不支持的记忆类型: {memory_type}")

        self.memories[cache_key] = memory
        return memory

    async def save_memory(
        self,
        session_id: str,
        key: str,
        value: Any,
        memory_type: str = MemoryType.CONVERSATION
    ):
        """
        保存记忆

        Args:
            session_id: 会话 ID
            key: 键
            value: 值
            memory_type: 记忆类型
        """
        memory = self.get_memory_instance(memory_type, session_id=session_id)
        await memory.save(key, value)
        logger.debug(f"保存记忆: {session_id}/{key}")

    async def get_memory_value(
        self,
        session_id: str,
        key: str,
        memory_type: str = MemoryType.CONVERSATION
    ) -> Any:
        """
        获取记忆

        Args:
            session_id: 会话 ID
            key: 键
            memory_type: 记忆类型

        Returns:
            记忆值
        """
        memory = self.get_memory_instance(memory_type, session_id=session_id)
        return await memory.get(key)

    async def clear_session(self, session_id: str):
        """
        清除会话记忆

        Args:
            session_id: 会话 ID
        """
        # 清除所有类型的记忆
        for cache_key in list(self.memories.keys()):
            if cache_key.startswith(session_id):
                del self.memories[cache_key]

        logger.info(f"清除会话记忆: {session_id}")


# 全局单例
memory_manager = MemoryManager()