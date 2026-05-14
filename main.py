"""
FastAPI 应用入口

创建 FastAPI 应用实例，配置中间件，注册路由，管理应用生命周期。
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import config
from app.core.logging import logger
from app.core.database import init_db, close_db
from app.core.redis_client import init_redis, close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    yield 之前是启动逻辑，之后是关闭逻辑。
    """
    # ========== 启动时执行 ==========
    logger.info("=" * 60)
    logger.info(f"🚀 {config.app_name} v{config.app_version} 启动中...")
    logger.info(f"📝 环境: {'开发' if config.debug else '生产'}")
    logger.info(f"🌐 监听地址: http://{config.host}:{config.port}")
    logger.info(f"📚 API 文档: http://{config.host}:{config.port}/docs")

    # 初始化数据库
    try:
        await init_db()
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")

    # 初始化 Redis
    try:
        await init_redis()
    except Exception as e:
        logger.error(f"Redis 初始化失败: {e}")

    logger.info("=" * 60)

    yield

    # ========== 关闭时执行 ==========
    logger.info("🔌 正在关闭连接...")
    await close_db()
    await close_redis()
    logger.info(f"👋 {config.app_name} 关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title=config.app_name,
    version=config.app_version,
    description="企业级 AI 电商运营 Agent 平台",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ========== 配置 CORS 中间件 ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== 注册路由 ==========
# from app.api import health, auth, products, users, orders, agents, workflows
# app.include_router(health.router, tags=["健康检查"])
# app.include_router(auth.router, prefix="/api", tags=["认证授权"])
# app.include_router(products.router, prefix="/api", tags=["商品管理"])
# app.include_router(users.router, prefix="/api", tags=["用户管理"])
# app.include_router(orders.router, prefix="/api", tags=["订单管理"])
# app.include_router(agents.router, prefix="/api", tags=["AI Agent"])
# app.include_router(workflows.router, prefix="/api", tags=["工作流"])

# ========== 根路径 ==========
@app.get("/")
async def root():
    """根路径，返回欢迎信息"""
    return {
        "message": f"Welcome to {config.app_name} API",
        "version": config.app_version,
        "docs": "/docs",
        "redoc": "/redoc"
    }


# ========== 健康检查 ==========
@app.get("/health")
async def health():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": config.app_name,
        "version": config.app_version
    }


# ========== 开发服务器入口 ==========
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level="info"
    )