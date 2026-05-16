"""
工作流模型

定义工作流相关的数据模型。
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, Text, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class WorkflowDefinition(Base, TimestampMixin):
    """工作流定义"""
    __tablename__ = "workflow_definitions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="工作流名称")
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="工作流编码")
    description: Mapped[str | None] = mapped_column(Text, comment="工作流描述")
    definition: Mapped[Dict[str, Any]] = mapped_column(JSON, comment="工作流定义(JSON)")

    # 状态
    is_active: Mapped[bool] = mapped_column(default=True, comment="是否激活")
    version: Mapped[str] = mapped_column(String(20), comment="版本号")

    # 租户
    tenant_id: Mapped[int | None] = mapped_column(Integer, comment="租户ID")


class WorkflowExecution(Base, TimestampMixin):
    """工作流执行记录"""
    __tablename__ = "workflow_executions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workflow_id: Mapped[int] = mapped_column(Integer, comment="工作流定义ID")

    # 执行信息
    execution_id: Mapped[str] = mapped_column(String(50), unique=True, comment="执行ID")
    status: Mapped[str] = mapped_column(String(20), comment="执行状态")
    input_data: Mapped[Dict[str, Any]] = mapped_column(JSON, comment="输入数据")
    output_data: Mapped[Dict[str, Any] | None] = mapped_column(JSON, comment="输出数据")
    error_message: Mapped[str | None] = mapped_column(Text, comment="错误信息")

    # 时间
    started_at: Mapped[datetime | None] = mapped_column(comment="开始时间")
    completed_at: Mapped[datetime | None] = mapped_column(comment="完成时间")

    # 上下文
    context: Mapped[Dict[str, Any] | None] = mapped_column(JSON, comment="执行上下文")


class WorkflowNodeExecution(Base, TimestampMixin):
    """工作流节点执行记录"""
    __tablename__ = "workflow_node_executions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    execution_id: Mapped[str] = mapped_column(String(50), comment="执行ID")
    node_id: Mapped[str] = mapped_column(String(50), comment="节点ID")
    node_type: Mapped[str] = mapped_column(String(20), comment="节点类型")

    # 执行信息
    status: Mapped[str] = mapped_column(String(20), comment="执行状态")
    input_data: Mapped[Dict[str, Any] | None] = mapped_column(JSON, comment="输入数据")
    output_data: Mapped[Dict[str, Any] | None] = mapped_column(JSON, comment="输出数据")
    error_message: Mapped[str | None] = mapped_column(Text, comment="错误信息")

    # 时间
    started_at: Mapped[datetime | None] = mapped_column(comment="开始时间")
    completed_at: Mapped[datetime | None] = mapped_column(comment="完成时间")

    # 重试
    retry_count: Mapped[int] = mapped_column(default=0, comment="重试次数")