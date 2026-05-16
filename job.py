"""
任务模型

定义调度任务相关的数据模型。
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, Text, Integer, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ScheduledJob(Base, TimestampMixin):
    """计划任务"""
    __tablename__ = "scheduled_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, comment="任务名称")
    job_type: Mapped[str] = mapped_column(String(50), comment="任务类型")
    trigger_type: Mapped[str] = mapped_column(String(20), comment="触发器类型")
    trigger_config: Mapped[Dict[str, Any]] = mapped_column(JSON, comment="触发器配置")
    job_params: Mapped[Dict[str, Any]] = mapped_column(JSON, comment="任务参数")

    # 状态
    is_active: Mapped[bool] = mapped_column(default=True, comment="是否激活")
    next_run_time: Mapped[datetime | None] = mapped_column(comment="下次运行时间")
    last_run_time: Mapped[datetime | None] = mapped_column(comment="上次运行时间")

    # 统计
    run_count: Mapped[int] = mapped_column(default=0, comment="运行次数")
    success_count: Mapped[int] = mapped_column(default=0, comment="成功次数")
    fail_count: Mapped[int] = mapped_column(default=0, comment="失败次数")

    # 租户
    tenant_id: Mapped[int | None] = mapped_column(Integer, comment="租户ID")


class JobExecution(Base, TimestampMixin):
    """任务执行记录"""
    __tablename__ = "job_executions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(Integer, comment="任务ID")

    # 执行信息
    execution_id: Mapped[str] = mapped_column(String(50), unique=True, comment="执行ID")
    status: Mapped[str] = mapped_column(String(20), comment="执行状态")
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), comment="开始时间")
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="结束时间")
    duration: Mapped[int | None] = mapped_column(Integer, comment="持续时间(秒)")

    # 结果
    result: Mapped[Dict[str, Any] | None] = mapped_column(JSON, comment="执行结果")
    error_message: Mapped[str | None] = mapped_column(Text, comment="错误信息")

    # 参数
    job_params: Mapped[Dict[str, Any]] = mapped_column(JSON, comment="任务参数")