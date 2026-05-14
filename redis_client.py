"""
Redis 客户端模块

提供 Redis 连接管理和常用操作封装。
"""
from redis.asyncio import Redis, ConnectionPool
from loguru import logger

from app.core.config import config


# 创建 Redis 连接池
pool = ConnectionPool.from_url(
    config.redis_url,
    encoding="utf-8",
    decode_responses=True,
)

# 创建 Redis 客户端
redis_client = Redis(connection_pool=pool)


async def init_redis():
    """初始化 Redis 连接"""
    try:
        await redis_client.ping()
        logger.info(f"Redis 连接成功: {config.redis_host}:{config.redis_port}")
    except Exception as e:
        logger.error(f"Redis 连接失败: {e}")
        raise


async def close_redis():
    """关闭 Redis 连接"""
    await redis_client.close()
    logger.info("Redis 连接已关闭")


class RedisManager:
    """Redis 管理器，提供常用操作"""

    @staticmethod
    async def get(key: str) -> str | None:
        """获取值"""
        return await redis_client.get(key)

    @staticmethod
    async def set(key: str, value: str, ex: int | None = None) -> bool:
        """设置值"""
        return await redis_client.set(key, value, ex=ex)

    @staticmethod
    async def delete(key: str) -> int:
        """删除键"""
        return await redis_client.delete(key)

    @staticmethod
    async def exists(key: str) -> int:
        """检查键是否存在"""
        return await redis_client.exists(key)

    @staticmethod
    async def expire(key: str, seconds: int) -> bool:
        """设置过期时间"""
        return await redis_client.expire(key, seconds)

    @staticmethod
    async def hget(name: str, key: str) -> str | None:
        """获取哈希字段"""
        return await redis_client.hget(name, key)

    @staticmethod
    async def hset(name: str, key: str, value: str) -> bool:
        """设置哈希字段"""
        return await redis_client.hset(name, key, value)

    @staticmethod
    async def hgetall(name: str) -> dict:
        """获取所有哈希字段"""
        return await redis_client.hgetall(name)


# 导出管理器
redis_manager = RedisManager()