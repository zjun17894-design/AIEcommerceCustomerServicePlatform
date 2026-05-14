"""
应用包初始化

自动导入日志配置，确保应用启动时就配置好日志。
"""
from app.core.logging import logger  # noqa: F401