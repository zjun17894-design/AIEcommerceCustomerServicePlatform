"""
订单仓库

处理订单相关的数据访问。
"""
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem, OrderStatus
from app.repositories.base_repository import BaseRepository
from app.schemas.order import OrderCreate, OrderUpdate


class OrderRepository(BaseRepository[Order, OrderCreate, OrderUpdate]):
    """订单仓库"""

    def __init__(self, db: AsyncSession):
        super().__init__(Order, db)

    async def get_by_order_no(self, order_no: str) -> Optional[Order]:
        """
        根据订单编号获取订单

        Args:
            order_no: 订单编号

        Returns:
            订单实例或 None
        """
        result = await self.db.execute(
            select(Order).where(Order.order_no == order_no, Order.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def get_with_items(self, id: int) -> Optional[Order]:
        """
        获取订单（含订单项）

        Args:
            id: 订单 ID

        Returns:
            订单实例或 None
        """
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == id, Order.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def get_user_orders(
        self,
        user_id: int,
        status: Optional[OrderStatus] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Order]:
        """
        获取用户订单

        Args:
            user_id: 用户 ID
            status: 订单状态
            skip: 跳过数量
            limit: 限制数量

        Returns:
            订单列表
        """
        query = select(Order).where(
            Order.user_id == user_id,
            Order.is_deleted == False
        )

        # 状态过滤
        if status:
            query = query.where(Order.status == status)

        # 排序和分页
        query = query.order_by(Order.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_pending_payment_orders(self, minutes: int = 30) -> List[Order]:
        """
        获取待支付超时订单

        Args:
            minutes: 超时分钟数

        Returns:
            订单列表
        """
        timeout_time = datetime.now() - timedelta(minutes=minutes)

        result = await self.db.execute(
            select(Order).where(
                Order.status == OrderStatus.PENDING,
                Order.created_at < timeout_time,
                Order.is_deleted == False
            )
        )
        return result.scalars().all()


class OrderItemRepository(BaseRepository[OrderItem, dict, dict]):
    """订单项仓库"""

    def __init__(self, db: AsyncSession):
        super().__init__(OrderItem, db)

    async def create_batch(self, items: List[dict]) -> List[OrderItem]:
        """
        批量创建订单项

        Args:
            items: 订单项列表

        Returns:
            订单项列表
        """
        order_items = [OrderItem(**item) for item in items]
        self.db.add_all(order_items)
        await self.db.commit()

        for item in order_items:
            await self.db.refresh(item)

        return order_items