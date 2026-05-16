"""
用户模型

定义用户、角色、权限相关的数据模型。
"""
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, Integer, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.product import Product


# ========== 用户-角色关联表 ==========
user_role = Table(
    "user_role",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


# ========== 角色模型 ==========
class Role(Base, TimestampMixin):
    """角色模型"""
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="角色名称")
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="角色编码")
    description: Mapped[str | None] = mapped_column(String(200), comment="角色描述")

    # 关系
    users: Mapped[list["User"]] = relationship(
        "User",
        secondary=user_role,
        back_populates="roles"
    )


# ========== 用户模型 ==========
class User(Base, TimestampMixin, SoftDeleteMixin):
    """用户模型"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="用户名")
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, comment="邮箱")
    phone: Mapped[str | None] = mapped_column(String(20), comment="手机号")
    hashed_password: Mapped[str] = mapped_column(String(200), nullable=False, comment="加密密码")

    # 用户信息
    nickname: Mapped[str | None] = mapped_column(String(50), comment="昵称")
    avatar: Mapped[str | None] = mapped_column(String(500), comment="头像URL")
    real_name: Mapped[str | None] = mapped_column(String(50), comment="真实姓名")

    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否激活")
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否超级管理员")

    # 租户（多租户支持）
    tenant_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("tenants.id", ondelete="SET NULL"),
        index=True,
        comment="租户ID"
    )

    # 关系
    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary=user_role,
        back_populates="users"
    )
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="user")
    created_products: Mapped[list["Product"]] = relationship(
        "Product",
        back_populates="creator",
        foreign_keys="Product.creator_id"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"


# ========== 租户模型 ==========
class Tenant(Base, TimestampMixin):
    """租户模型"""
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, comment="租户名称")
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="租户编码")
    description: Mapped[str | None] = mapped_column(String(200), comment="租户描述")

    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否激活")

    # 关系
    users: Mapped[list["User"]] = relationship("User", backref="tenant")