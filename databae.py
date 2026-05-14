"""
数据库连接模块

使用 SQLAlchemy AsyncSession 实现异步数据库操作。
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from loguru import logger

from app.core.config import config


class Base(DeclarativeBase):
    """SQLAlchemy 基类"""
    pass


# 创建异步引擎
engine = create_async_engine(
    config.database_url,
    echo=config.debug,  # 开发环境打印 SQL
    pool_size=10,       # 连接池大小
    max_overflow=20,    # 最大溢出连接数
    pool_pre_ping=True, # 连接前 ping 检测
)

# 创建异步 Session 工厂
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """
    获取数据库 Session（依赖注入）

    用于 FastAPI 的依赖注入系统，在请求结束后自动关闭 Session。

    Returns:
        AsyncSession: 数据库 Session 实例
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"数据库操作异常: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    初始化数据库

    创建所有表（开发环境使用，生产环境应使用 Alembic 迁移）
    """
    async with engine.begin() as conn:
        # 导入所有模型以确保它们被注册
        from app.models import product, user, order  # 后续创建
        await conn.run_sync(Base.metadata.create_all)
    logger.info("数据库表初始化完成")


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()
    logger.info("数据库连接已关闭")