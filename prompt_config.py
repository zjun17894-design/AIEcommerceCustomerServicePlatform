"""
提示词配置

管理提示词的配置信息。
"""
from typing import Dict, Any, Optional
from pathlib import Path
import yaml
import json
from loguru import logger


class PromptConfig:
    """提示词配置"""

    def __init__(self, config_path: str = "prompts/config.yaml"):
        """
        初始化配置

        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        if not self.config_path.exists():
            logger.warning(f"配置文件不存在: {self.config_path}")
            return {}

        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')

        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_template_path(self, name: str) -> Optional[Path]:
        """
        获取模板文件路径

        Args:
            name: 模板名称

        Returns:
            文件路径或 None
        """
        template_dir = self.get('template_dir', 'prompts/templates')
        template_path = Path(template_dir) / f"{name}.yaml"

        if template_path.exists():
            return template_path

        # 尝试 .md 文件
        template_path = Path(template_dir) / f"{name}.md"
        if template_path.exists():
            return template_path

        return None

    def get_global_variables(self) -> Dict[str, Any]:
        """获取全局变量"""
        return self.get('global_variables', {})


# 全局单例
prompt_config = PromptConfig()