"""
仓库基类

定义通用的数据访问方法。
"""
from typing import Generic, TypeVar, Type, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import DeclarativeBase
from pydantic import BaseModel
from loguru import logger


ModelType = TypeVar("ModelType", bound=DeclarativeBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """仓库基类"""

    def __init__(self, model: Type[ModelType], db: AsyncSession):
        """
        初始化仓库

        Args:
            model: 模型类
            db: 数据库 Session
        """
        self.model = model
        self.db = db

    async def create(
        self,
        obj_in: CreateSchemaType,
        **kwargs
    ) -> ModelType:
        """
        创建记录

        Args:
            obj_in: 创建对象
            **kwargs: 额外字段

        Returns:
            创建的模型实例
        """
        obj_data = obj_in.model_dump() if hasattr(obj_in, 'model_dump') else obj_in
        obj_data.update(kwargs)

        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        logger.info(f"创建 {self.model.__name__}: {db_obj.id}")
        return db_obj

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        根据 ID 获取记录

        Args:
            id: 记录 ID

        Returns:
            模型实例或 None
        """
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[ModelType]:
        """
        获取所有记录

        Args:
            skip: 跳过数量
            limit: 限制数量
            **filters: 过滤条件

        Returns:
            模型实例列表
        """
        query = select(self.model)

        # 添加过滤条件
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update(
        self,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict,
        **kwargs
    ) -> ModelType:
        """
        更新记录

        Args:
            db_obj: 数据库对象
            obj_in: 更新对象或字典
            **kwargs: 额外字段

        Returns:
            更新后的模型实例
        """
        obj_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, 'model_dump') else obj_in
        obj_data.update(kwargs)

        for field, value in obj_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)

        logger.info(f"更新 {self.model.__name__}: {db_obj.id}")
        return db_obj

    async def delete(self, id: int) -> bool:
        """
        删除记录

        Args:
            id: 记录 ID

        Returns:
            是否删除成功
        """
        result = await self.db.execute(
            delete(self.model).where(self.model.id == id)
        )
        await self.db.commit()

        deleted = result.rowcount > 0
        if deleted:
            logger.info(f"删除 {self.model.__name__}: {id}")

        return deleted

    async def count(self, **filters) -> int:
        """
        统计记录数量

        Args:
            **filters: 过滤条件

        Returns:
            记录数量
        """
        query = select(func.count()).select_from(self.model)

        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)

        result = await self.db.execute(query)
        return result.scalar()