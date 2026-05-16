"""
订单模型

定义订单、订单项、收货地址相关的数据模型。
"""
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from enum import Enum
from sqlalchemy import String, Integer, Numeric, Text, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.product import Product


# ========== 订单状态枚举 ==========
class OrderStatus(str, Enum):
    """订单状态"""
    PENDING = "pending"          # 待支付
    PAID = "paid"                # 已支付
    SHIPPED = "shipped"          # 已发货
    COMPLETED = "completed"      # 已完成
    CANCELLED = "cancelled"      # 已取消
    REFUNDING = "refunding"      # 退款中
    REFUNDED = "refunded"        # 已退款


# ========== 订单模型 ==========
class Order(Base, TimestampMixin, SoftDeleteMixin):
    """订单模型"""
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 订单信息
    order_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="订单编号")

    # 用户
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        comment="用户ID"
    )

    # 金额
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="订单总额"
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        comment="优惠金额"
    )
    actual_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="实付金额"
    )
    shipping_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        comment="运费"
    )

    # 状态
    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus),
        default=OrderStatus.PENDING,
        comment="订单状态"
    )

    # 收货信息
    receiver_name: Mapped[str] = mapped_column(String(50), comment="收货人")
    receiver_phone: Mapped[str] = mapped_column(String(20), comment="收货电话")
    receiver_address: Mapped[str] = mapped_column(Text, comment="收货地址")

    # 备注
    remark: Mapped[str | None] = mapped_column(Text, comment="订单备注")

    # 支付信息
    payment_method: Mapped[str | None] = mapped_column(String(20), comment="支付方式")
    payment_time: Mapped[datetime | None] = mapped_column(comment="支付时间")

    # 发货信息
    shipping_time: Mapped[datetime | None] = mapped_column(comment="发货时间")
    shipping_no: Mapped[str | None] = mapped_column(String(50), comment="物流单号")
    shipping_company: Mapped[str | None] = mapped_column(String(50), comment="物流公司")

    # 完成时间
    completed_time: Mapped[datetime | None] = mapped_column(comment="完成时间")

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


# ========== 订单项模型 ==========
class OrderItem(Base, TimestampMixin):
    """订单项模型"""
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 关联
    order_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        comment="订单ID"
    )
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id"),
        nullable=False,
        comment="商品ID"
    )
    sku_id: Mapped[int | None] = mapped_column(Integer, comment="SKU ID")

    # 商品信息（快照）
    product_name: Mapped[str] = mapped_column(String(200), comment="商品名称")
    product_code: Mapped[str] = mapped_column(String(50), comment="商品编码")
    product_image: Mapped[str | None] = mapped_column(String(500), comment="商品图片")
    sku_specs: Mapped[str | None] = mapped_column(Text, comment="SKU规格")

    # 价格和数量
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, comment="单价")
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, comment="数量")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, comment="小计")

    # 关系
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped["Product"] = relationship("Product", back_populates="order_items")


# ========== 收货地址模型 ==========
class ShippingAddress(Base, TimestampMixin, SoftDeleteMixin):
    """收货地址模型"""
    __tablename__ = "shipping_addresses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 用户
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        comment="用户ID"
    )

    # 地址信息
    receiver_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="收货人")
    receiver_phone: Mapped[str] = mapped_column(String(20), nullable=False, comment="收货电话")
    province: Mapped[str] = mapped_column(String(50), comment="省份")
    city: Mapped[str] = mapped_column(String(50), comment="城市")
    district: Mapped[str] = mapped_column(String(50), comment="区县")
    detail_address: Mapped[str] = mapped_column(Text, nullable=False, comment="详细地址")
    postal_code: Mapped[str | None] = mapped_column(String(10), comment="邮编")

    # 默认
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否默认地址")

    # 关系
    user: Mapped["User"] = relationship("User", backref="addresses")