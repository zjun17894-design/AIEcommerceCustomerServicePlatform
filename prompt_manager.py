"""
提示词管理器

管理提示词模板的创建、版本、使用等。
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from loguru import logger

from app.models.prompt import PromptTemplate, PromptVersion, PromptUsage
from app.prompts.prompt_template import PromptTemplate as PromptTemplateClass, PromptVariable
from app.prompts.prompt_config import prompt_config


class PromptManager:
    """提示词管理器"""

    def __init__(self, db: AsyncSession):
        """
        初始化管理器

        Args:
            db: 数据库 Session
        """
        self.db = db
        self._templates: Dict[str, PromptTemplateClass] = {}

    async def get_template(
        self,
        name: str,
        version: Optional[str] = None
    ) -> Optional[PromptTemplateClass]:
        """
        获取提示词模板

        Args:
            name: 模板名称
            version: 版本号（None 表示最新）

        Returns:
            提示词模板或 None
        """
        # 先从缓存获取
        if name in self._templates:
            return self._templates[name]

        # 从数据库获取
        query = select(PromptTemplate).where(
            PromptTemplate.name == name,
            PromptTemplate.is_active == True
        )

        if version:
            query = query.where(PromptTemplate.version == version)
        else:
            query = query.order_by(desc(PromptTemplate.version)).limit(1)

        result = await self.db.execute(query)
        template = result.scalar_one_or_none()

        if not template:
            return None

        # 构建提示词模板对象
        variables = []
        if template.variables:
            variables = [
                PromptVariable(
                    name=k,
                    var_type=v.get("type", "string"),
                    description=v.get("description", ""),
                    default=v.get("default"),
                    required=v.get("required", True)
                )
                for k, v in template.variables.items()
            ]

        prompt_template = PromptTemplateClass(
            name=template.name,
            template=template.template,
            category=template.category,
            variables=variables,
            description=template.description,
            version=template.version
        )

        # 缓存
        self._templates[name] = prompt_template

        return prompt_template

    async def render_template(
        self,
        name: str,
        variables: Dict[str, Any],
        version: Optional[str] = None
    ) -> str:
        """
        渲染提示词模板

        Args:
            name: 模板名称
            variables: 变量值
            version: 版本号

        Returns:
            渲染后的提示词
        """
        template = await self.get_template(name, version)
        if not template:
            raise ValueError(f"模板不存在: {name}")

        return template.render(variables)

    async def save_template(
        self,
        name: str,
        template: str,
        category: str,
        variables: List[Dict[str, Any]] = None,
        description: str = "",
        version: str = "1.0.0"
    ) -> PromptTemplate:
        """
        保存提示词模板

        Args:
            name: 模板名称
            template: 模板内容
            category: 分类
            variables: 变量定义
            description: 描述
            version: 版本号

        Returns:
            保存的模板
        """
        # 检查是否已存在
        result = await self.db.execute(
            select(PromptTemplate).where(PromptTemplate.name == name)
        )
        existing = result.scalar_one_or_none()

        if existing:
            # 更新版本
            existing.version = version
            existing.template = template
            existing.description = description

            # 创建版本记录
            prompt_version = PromptVersion(
                template_id=existing.id,
                version=version,
                template=template,
                changelog=f"更新到版本 {version}"
            )
            self.db.add(prompt_version)

        else:
            # 创建新模板
            new_template = PromptTemplate(
                name=name,
                template=template,
                category=category,
                version=version,
                variables={v["name"]: v for v in variables} if variables else None,
                description=description
            )
            self.db.add(new_template)

        await self.db.commit()
        await self.db.refresh(existing or new_template)

        # 清除缓存
        if name in self._templates:
            del self._templates[name]

        logger.info(f"保存提示词模板: {name} v{version}")
        return existing or new_template

    async def record_usage(
        self,
        template_name: str,
        variables: Dict[str, Any],
        rendered_prompt: str,
        session_id: str,
        score: Optional[int] = None
    ):
        """
        记录提示词使用

        Args:
            template_name: 模板名称
            variables: 使用的变量
            rendered_prompt: 渲染后的提示词
            session_id: 会话ID
            score: 评分
        """
        # 获取模板
        template = await self.get_template(template_name)
        if not template:
            return

        # 记录使用
        usage = PromptUsage(
            template_id=template.id if hasattr(template, 'id') else None,  # 简化
            version=template.version,
            session_id=session_id,
            variables=variables,
            rendered_prompt=rendered_prompt,
            score=score
        )

        self.db.add(usage)

        # 更新使用次数和平均分
        # TODO: 实现更新逻辑

        await self.db.commit()
        logger.debug(f"记录提示词使用: {template_name}")

    async def list_templates(
        self,
        category: Optional[str] = None
    ) -> List[PromptTemplate]:
        """
        列出所有模板

        Args:
            category: 分类过滤

        Returns:
            模板列表
        """
        query = select(PromptTemplate).where(
            PromptTemplate.is_active == True
        )

        if category:
            query = query.where(PromptTemplate.category == category)

        query = query.order_by(PromptTemplate.name)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_version(
        self,
        name: str,
        new_version: str,
        changelog: str = "",
        new_template: Optional[str] = None
    ):
        """
        创建新版本

        Args:
            name: 模板名称
            new_version: 新版本号
            changelog: 变更日志
            new_template: 新模板内容（可选，不传则使用当前）
        """
        template = await self.get_template(name)
        if not template:
            raise ValueError(f"模板不存在: {name}")

        # 使用当前模板或新模板
        template_content = new_template or template.template

        # 更新模板
        await self.save_template(
            name=name,
            template=template_content,
            category=template.category,
            description=template.description,
            version=new_version
        )

        logger.info(f"创建新版本: {name} v{new_version}")