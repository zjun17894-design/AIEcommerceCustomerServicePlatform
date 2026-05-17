"""
提示词模板

提供提示词模板的定义和渲染功能。
"""
from typing import Dict, Any, Optional, List
from string import Template
import jinja2
from loguru import logger


class PromptVariable:
    """提示词变量"""

    def __init__(
        self,
        name: str,
        var_type: str = "string",
        description: str = "",
        default: Any = None,
        required: bool = True
    ):
        self.name = name
        self.type = var_type
        self.description = description
        self.default = default
        self.required = required

    def validate(self, value: Any) -> bool:
        """验证值"""
        if value is None:
            return not self.required

        if self.type == "string":
            return isinstance(value, str)
        elif self.type == "integer":
            return isinstance(value, int)
        elif self.type == "float":
            return isinstance(value, (int, float))
        elif self.type == "boolean":
            return isinstance(value, bool)
        elif self.type == "list":
            return isinstance(value, list)
        elif self.type == "dict":
            return isinstance(value, dict)

        return True


class PromptTemplate:
    """提示词模板"""

    def __init__(
        self,
        name: str,
        template: str,
        category: str = "default",
        variables: List[PromptVariable] = None,
        description: str = "",
        version: str = "1.0.0"
    ):
        """
        初始化提示词模板

        Args:
            name: 模板名称
            template: 模板内容
            category: 分类
            variables: 变量列表
            description: 描述
            version: 版本号
        """
        self.name = name
        self.template = template
        self.category = category
        self.variables = variables or []
        self.description = description
        self.version = version

    def render(
        self,
        variables: Dict[str, Any],
        engine: str = "jinja2"
    ) -> str:
        """
        渲染提示词

        Args:
            variables: 变量值
            engine: 渲染引擎（string.Template 或 jinja2）

        Returns:
            渲染后的提示词
        """
        try:
            # 验证变量
            self._validate_variables(variables)

            # 渲染
            if engine == "jinja2":
                return self._render_jinja2(variables)
            else:
                return self._render_string(variables)

        except Exception as e:
            logger.error(f"渲染提示词失败: {self.name}, {e}")
            raise

    def _render_jinja2(self, variables: Dict[str, Any]) -> str:
        """使用 Jinja2 渲染"""
        env = jinja2.Environment(
            loader=jinja2.BaseLoader(),
            autoescape=False
        )

        template = env.from_string(self.template)
        return template.render(**variables)

    def _render_string(self, variables: Dict[str, Any]) -> str:
        """使用 string.Template 渲染"""
        # 设置默认值
        for var in self.variables:
            if var.name not in variables and var.default is not None:
                variables[var.name] = var.default

        template = Template(self.template)
        return template.substitute(**variables)

    def _validate_variables(self, variables: Dict[str, Any]):
        """验证变量"""
        required_vars = [v for v in self.variables if v.required]
        provided_vars = set(variables.keys())
        required_vars_names = {v.name for v in required_vars}

        missing_vars = required_vars_names - provided_vars
        if missing_vars:
            raise ValueError(f"缺少必需的变量: {', '.join(missing_vars)}")

        # 验证每个变量
        for var in self.variables:
            if var.name in variables:
                if not var.validate(variables[var.name]):
                    raise ValueError(f"变量 {var.name} 值类型错误: {var.type}")

    def get_variables_schema(self) -> Dict[str, Any]:
        """获取变量 Schema"""
        return {
            var.name: {
                "type": var.type,
                "description": var.description,
                "default": var.default,
                "required": var.required
            }
            for var in self.variables
        }

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "template": self.template,
            "category": self.category,
            "variables": self.get_variables_schema(),
            "description": self.description,
            "version": self.version
        }