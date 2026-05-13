"""
配置管理模块

使用 Pydantic Settings 实现类型安全的配置管理，从 .env 文件读取配置。
"""
from typing import Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ========== 应用配置 ==========
    app_name: str = "EcommerceAgent"
    app_version: str = "0.1.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # ========== 数据库配置 ==========
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/ecommerce"

    # ========== Redis 配置 ==========
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0

    # ========== OpenAI 配置 ==========
    openai_api_key: str = ""
    openai_api_base: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4"

    # ========== DashScope 配置（阿里云） ==========
    dashscope_api_key: str = ""
    dashscope_api_base: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    dashscope_model: str = "qwen-max"
    dashscope_embedding_model: str = "text-embedding-v2"

    # ========== Milvus 配置 ==========
    milvus_host: str = "localhost"
    milvus_port: int = 19530

    # ========== JWT 配置 ==========
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # ========== RAG 配置 ==========
    rag_top_k: int = 3
    rag_model: str = "qwen-max"
    chunk_max_size: int = 800
    chunk_overlap: int = 100

    # ========== MCP 服务配置 ==========
    mcp_product_transport: str = "streamable-http"
    mcp_product_url: str = "http://localhost:8001/mcp"
    mcp_marketing_transport: str = "streamable-http"
    mcp_marketing_url: str = "http://localhost:8002/mcp"
    mcp_service_transport: str = "streamable-http"
    mcp_service_url: str = "http://localhost:8003/mcp"

    @property
    def mcp_servers(self) -> Dict[str, Dict[str, Any]]:
        """获取完整的 MCP 服务器配置"""
        return {
            "product": {
                "transport": self.mcp_product_transport,
                "url": self.mcp_product_url,
            },
            "marketing": {
                "transport": self.mcp_marketing_transport,
                "url": self.mcp_marketing_url,
            },
            "service": {
                "transport": self.mcp_service_transport,
                "url": self.mcp_service_url,
            }
        }

    @property
    def redis_url(self) -> str:
        """获取 Redis 连接 URL"""
        password_part = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{password_part}{self.redis_host}:{self.redis_port}/{self.redis_db}"


# 全局配置实例
config = Settings()