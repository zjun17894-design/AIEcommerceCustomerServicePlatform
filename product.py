"""
商品模型

定义商品、分类、库存相关的数据模型。
"""
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, Numeric, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.order import OrderItem


# ========== 商品分类模型 ==========
class ProductCategory(Base, TimestampMixin, SoftDeleteMixin):
    """商品分类模型"""
    __tablename__ = "product_categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="分类名称")
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="分类编码")
    parent_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("product_categories.id"),
        comment="父分类ID"
    )
    level: Mapped[int] = mapped_column(Integer, default=1, comment="分类层级")
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    description: Mapped[str | None] = mapped_column(String(200), comment="分类描述")

    # 关系
    parent: Mapped["ProductCategory | None"] = relationship(
        "ProductCategory",
        remote_side="ProductCategory.id",
        backref="children"
    )
    products: Mapped[list["Product"]] = relationship("Product", back_populates="category")


# ========== 商品模型 ==========
class Product(Base, TimestampMixin, SoftDeleteMixin):
    """商品模型"""
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 基本信息
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="商品名称")
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="商品编码")
    description: Mapped[str | None] = mapped_column(Text, comment="商品描述")

    # 分类
    category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("product_categories.id"),
        nullable=False,
        comment="分类ID"
    )

    # 价格
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="售价"
    )
    cost_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        comment="成本价"
    )
    original_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        comment="原价"
    )

    # 库存
    stock: Mapped[int] = mapped_column(Integer, default=0, comment="库存数量")
    min_stock: Mapped[int] = mapped_column(Integer, default=0, comment="最小库存预警")
    sales: Mapped[int] = mapped_column(Integer, default=0, comment="销量")

    # 状态
    is_on_sale: Mapped[bool] = mapped_column(default=True, comment="是否上架")
    is_featured: Mapped[bool] = mapped_column(default=False, comment="是否推荐")

    # 图片
    image_url: Mapped[str | None] = mapped_column(String(500), comment="主图URL")
    images: Mapped[str | None] = mapped_column(Text, comment="图片列表(JSON)")

    # 标签
    tags: Mapped[str | None] = mapped_column(String(200), comment="标签(逗号分隔)")
    keywords: Mapped[str | None] = mapped_column(Text, comment="SEO关键词")

    # 操作人
    creator_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        comment="创建人ID"
    )

    # 租户
    tenant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tenants.id"),
        comment="租户ID"
    )

    # 关系
    category: Mapped["ProductCategory"] = relationship("ProductCategory", back_populates="products")
    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[creator_id],
        backref="created_products"
    )
    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="product")

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name={self.name}, price={self.price})>"


# ========== 商品规格模型 ==========
class ProductSku(Base, TimestampMixin):
    """商品SKU模型"""
    __tablename__ = "product_skus"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        comment="商品ID"
    )
    sku_code: Mapped[str] = mapped_column(String(50), nullable=False, comment="SKU编码")
    sku_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="SKU名称")
    specs: Mapped[str] = mapped_column(Text, comment="规格(JSON)")
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, comment="SKU价格")
    stock: Mapped[int] = mapped_column(Integer, default=0, comment="SKU库存")

    # 关系
    product: Mapped["Product"] = relationship("Product", backref="skus")