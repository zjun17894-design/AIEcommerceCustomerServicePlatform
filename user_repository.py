"""
用户仓库

处理用户相关的数据访问。
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.models.user import User, Role
from app.repositories.base_repository import BaseRepository
from app.schemas.user import UserCreate, UserUpdate


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """用户仓库"""

    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_username(self, username: str) -> Optional[User]:
        """
        根据用户名获取用户

        Args:
            username: 用户名

        Returns:
            用户实例或 None
        """
        result = await self.db.execute(
            select(User).where(User.username == username, User.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        根据邮箱获取用户

        Args:
            email: 邮箱

        Returns:
            用户实例或 None
        """
        result = await self.db.execute(
            select(User).where(User.email == email, User.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def get_by_username_or_email(self, identifier: str) -> Optional[User]:
        """
        根据用户名或邮箱获取用户

        Args:
            identifier: 用户名或邮箱

        Returns:
            用户实例或 None
        """
        result = await self.db.execute(
            select(User).where(
                or_(
                    User.username == identifier,
                    User.email == identifier
                ),
                User.is_deleted == False
            )
        )
        return result.scalar_one_or_none()

    async def get_with_roles(self, id: int) -> Optional[User]:
        """
        获取用户（含角色信息）

        Args:
            id: 用户 ID

        Returns:
            用户实例或 None
        """
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.roles))
            .where(User.id == id, User.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def search(
        self,
        keyword: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[User]:
        """
        搜索用户

        Args:
            keyword: 关键词
            is_active: 是否激活
            skip: 跳过数量
            limit: 限制数量

        Returns:
            用户列表
        """
        query = select(User).where(User.is_deleted == False)

        # 关键词搜索
        if keyword:
            search_pattern = f"%{keyword}%"
            query = query.where(
                or_(
                    User.username.ilike(search_pattern),
                    User.nickname.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    User.real_name.ilike(search_pattern)
                )
            )

        # 激活状态
        if is_active is not None:
            query = query.where(User.is_active == is_active)

        # 分页
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_password(self, user: User, new_password: str) -> User:
        """
        更新用户密码

        Args:
            user: 用户实例
            new_password: 新密码

        Returns:
            更新后的用户
        """
        from app.core.security import security_manager

        user.hashed_password = security_manager.hash_password(new_password)
        await self.db.commit()
        await self.db.refresh(user)

        return user


class RoleRepository(BaseRepository[Role, dict, dict]):
    """角色仓库"""

    def __init__(self, db: AsyncSession):
        super().__init__(Role, db)

    async def get_by_code(self, code: str) -> Optional[Role]:
        """
        根据编码获取角色

        Args:
            code: 角色编码

        Returns:
            角色实例或 None
        """
        result = await self.db.execute(
            select(Role).where(Role.code == code)
        )
        return result.scalar_one_or_none()