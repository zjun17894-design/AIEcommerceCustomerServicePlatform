"""
商品仓库

处理商品相关的数据访问。
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.models.product import Product, ProductCategory
from app.repositories.base_repository import BaseRepository
from app.schemas.product import ProductCreate, ProductUpdate


class ProductRepository(BaseRepository[Product, ProductCreate, ProductUpdate]):
    """商品仓库"""

    def __init__(self, db: AsyncSession):
        super().__init__(Product, db)

    async def get_by_code(self, code: str) -> Optional[Product]:
        """
        根据编码获取商品

        Args:
            code: 商品编码

        Returns:
            商品实例或 None
        """
        result = await self.db.execute(
            select(Product).where(Product.code == code, Product.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def get_with_category(self, id: int) -> Optional[Product]:
        """
        获取商品（含分类信息）

        Args:
            id: 商品 ID

        Returns:
            商品实例或 None
        """
        result = await self.db.execute(
            select(Product)
            .options(selectinload(Product.category))
            .where(Product.id == id, Product.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def search(
        self,
        keyword: Optional[str] = None,
        category_id: Optional[int] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        is_on_sale: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Product]:
        """
        搜索商品

        Args:
            keyword: 关键词
            category_id: 分类 ID
            min_price: 最低价格
            max_price: 最高价格
            is_on_sale: 是否上架
            skip: 跳过数量
            limit: 限制数量

        Returns:
            商品列表
        """
        query = select(Product).where(Product.is_deleted == False)

        # 关键词搜索
        if keyword:
            search_pattern = f"%{keyword}%"
            query = query.where(
                or_(
                    Product.name.ilike(search_pattern),
                    Product.description.ilike(search_pattern),
                    Product.tags.ilike(search_pattern),
                    Product.code.ilike(search_pattern)
                )
            )

        # 分类过滤
        if category_id:
            query = query.where(Product.category_id == category_id)

        # 价格范围
        if min_price is not None:
            query = query.where(Product.price >= min_price)
        if max_price is not None:
            query = query.where(Product.price <= max_price)

        # 上架状态
        if is_on_sale is not None:
            query = query.where(Product.is_on_sale == is_on_sale)

        # 分页
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_featured_products(self, limit: int = 10) -> List[Product]:
        """
        获取推荐商品

        Args:
            limit: 数量

        Returns:
            商品列表
        """
        result = await self.db.execute(
            select(Product)
            .where(Product.is_featured == True, Product.is_on_sale == True, Product.is_deleted == False)
            .order_by(Product.sales.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_hot_products(self, limit: int = 10) -> List[Product]:
        """
        获取热销商品

        Args:
            limit: 数量

        Returns:
            商品列表
        """
        result = await self.db.execute(
            select(Product)
            .where(Product.is_on_sale == True, Product.is_deleted == False)
            .order_by(Product.sales.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def decrease_stock(self, id: int, quantity: int) -> bool:
        """
        减少库存

        Args:
            id: 商品 ID
            quantity: 数量

        Returns:
            是否成功
        """
        result = await self.db.execute(
            select(Product).where(
                Product.id == id,
                Product.is_deleted == False,
                Product.stock >= quantity
            )
        )
        product = result.scalar_one_or_none()

        if not product:
            return False

        product.stock -= quantity
        product.sales += quantity
        await self.db.commit()

        return True


class ProductCategoryRepository(BaseRepository[ProductCategory, dict, dict]):
    """商品分类仓库"""

    def __init__(self, db: AsyncSession):
        super().__init__(ProductCategory, db)

    async def get_by_code(self, code: str) -> Optional[ProductCategory]:
        """
        根据编码获取分类

        Args:
            code: 分类编码

        Returns:
            分类实例或 None
        """
        result = await self.db.execute(
            select(ProductCategory).where(
                ProductCategory.code == code,
                ProductCategory.is_deleted == False
            )
        )
        return result.scalar_one_or_none()

    async def get_children(self, parent_id: Optional[int] = None) -> List[ProductCategory]:
        """
        获取子分类

        Args:
            parent_id: 父分类 ID

        Returns:
            分类列表
        """
        query = select(ProductCategory).where(
            ProductCategory.is_deleted == False
        )

        if parent_id is None:
            query = query.where(ProductCategory.parent_id.is_(None))
        else:
            query = query.where(ProductCategory.parent_id == parent_id)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_tree(self) -> List[dict]:
        """
        获取分类树

        Returns:
            分类树列表
        """
        result = await self.db.execute(
            select(ProductCategory)
            .where(ProductCategory.is_deleted == False)
            .order_by(ProductCategory.sort)
        )
        all_categories = result.scalars().all()

        # 构建树形结构
        category_map = {c.id: c for c in all_categories}
        tree = []

        for category in all_categories:
            if category.parent_id is None:
                tree.append(self._build_category_tree(category, category_map))

        return tree

    def _build_category_tree(self, category, category_map) -> dict:
        """
        构建分类树

        Args:
            category: 当前分类
            category_map: 分类映射

        Returns:
            分类树节点
        """
        node = {
            "id": category.id,
            "name": category.name,
            "code": category.code,
            "level": category.level,
            "children": []
        }

        # 查找子分类
        for child in category_map.values():
            if child.parent_id == category.id:
                node["children"].append(self._build_category_tree(child, category_map))

        return node