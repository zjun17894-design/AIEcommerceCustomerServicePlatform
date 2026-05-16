"""
提示词模型

定义提示词相关的数据模型。
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, Text, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class PromptTemplate(Base, TimestampMixin):
    """提示词模板"""
    __tablename__ = "prompt_templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, comment="模板名称")
    category: Mapped[str] = mapped_column(String(50), nullable=False, comment="分类")
    template: Mapped[str] = mapped_column(Text, nullable=False, comment="模板内容")
    version: Mapped[str] = mapped_column(String(20), default="1.0.0", comment="版本号")
    is_active: Mapped[bool] = mapped_column(default=True, comment="是否激活")
    variables: Mapped[Dict[str, Any]] = mapped_column(JSON, comment="变量定义")
    description: Mapped[str | None] = mapped_column(Text, comment="描述")

    # 统计
    usage_count: Mapped[int] = mapped_column(default=0, comment="使用次数")
    avg_score: Mapped[float | None] = mapped_column(comment="平均评分")


class PromptVersion(Base, TimestampMixin):
    """提示词版本"""
    __tablename__ = "prompt_versions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(Integer, comment="模板ID")
    version: Mapped[str] = mapped_column(String(20), comment="版本号")
    template: Mapped[str] = mapped_column(Text, comment="模板内容")
    changelog: Mapped[str | None] = mapped_column(Text, comment="变更日志")

    # 创建人
    created_by: Mapped[int] = mapped_column(Integer, comment="创建人ID")


class PromptUsage(Base, TimestampMixin):
    """提示词使用记录"""
    __tablename__ = "prompt_usage"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(Integer, comment="模板ID")
    version: Mapped[str] = mapped_column(String(20), comment="版本号")

    # 使用信息
    session_id: Mapped[str] = mapped_column(String(100), comment="会话ID")
    variables: Mapped[Dict[str, Any]] = mapped_column(JSON, comment="使用的变量")
    rendered_prompt: Mapped[str] = mapped_column(Text, comment="渲染后的提示词")

    # 评估
    score: Mapped[int | None] = mapped_column(Integer, comment="评分(1-5)")
    feedback: Mapped[str | None] = mapped_column(Text, comment="反馈")