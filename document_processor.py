"""
文档处理器

处理文档上传、解析、分块等操作。
"""
from typing import List, Optional, Dict, Any
from pathlib import Path
import aiofiles
import asyncio
from loguru import logger

from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentChunk:
    """文档块"""

    def __init__(
        self,
        content: str,
        metadata: Dict[str, Any] = None,
        id: Optional[str] = None
    ):
        self.content = content
        self.metadata = metadata or {}
        self.id = id

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata
        }


class DocumentProcessor:
    """文档处理器"""

    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 100,
        separators: Optional[List[str]] = None
    ):
        """
        初始化处理器

        Args:
            chunk_size: 块大小
            chunk_overlap: 块重叠大小
            separators: 分隔符
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # 初始化文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators or ["\n\n", "\n", "。", "！", "？", " ", ""]
        )

    async def process_file(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """
        处理文件

        Args:
            file_path: 文件路径
            metadata: 元数据

        Returns:
            文档块列表
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 读取文件
        content = await self._read_file(path)

        # 基础元数据
        file_metadata = {
            "source": str(path),
            "file_name": path.name,
            "file_type": path.suffix,
            "file_size": path.stat().st_size
        }
        if metadata:
            file_metadata.update(metadata)

        # 分块
        chunks = self.split_text(content, file_metadata)

        logger.info(f"处理文件完成: {path.name}, 生成 {len(chunks)} 个块")
        return chunks

    async def process_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """
        处理文本

        Args:
            text: 文本内容
            metadata: 元数据

        Returns:
            文档块列表
        """
        # 分块
        chunks = self.split_text(text, metadata or {})

        logger.info(f"处理文本完成, 生成 {len(chunks)} 个块")
        return chunks

    def split_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """
        分割文本

        Args:
            text: 文本内容
            metadata: 元数据

        Returns:
            文档块列表
        """
        # 使用 LangChain 分割器
        text_chunks = self.text_splitter.split_text(text)

        # 创建 DocumentChunk
        chunks = []
        for i, chunk in enumerate(text_chunks):
            chunk_metadata = (metadata or {}).copy()
            chunk_metadata["chunk_index"] = i
            chunk_metadata["chunk_count"] = len(text_chunks)

            chunk = DocumentChunk(
                content=chunk,
                metadata=chunk_metadata
            )
            chunks.append(chunk)

        return chunks

    async def _read_file(self, path: Path) -> str:
        """
        读取文件

        Args:
            path: 文件路径

        Returns:
            文件内容
        """
        # 简单文本文件
        if path.suffix in ['.txt', '.md', '.py', '.js', '.json', '.yaml', '.yml']:
            async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                return await f.read()

        # PDF 文件（需要安装相关库）
        if path.suffix == '.pdf':
            # TODO: 实现 PDF 读取
            raise NotImplementedError("PDF 暂不支持")

        # Word 文档
        if path.suffix in ['.doc', '.docx']:
            # TODO: 实现 Word 读取
            raise NotImplementedError("Word 暂不支持")

        raise ValueError(f"不支持的文件类型: {path.suffix}")

    def clean_text(self, text: str) -> str:
        """
        清理文本

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        # 移除多余空白
        text = " ".join(text.split())

        # 移除特殊字符
        import re
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)

        return text

    def extract_metadata(self, text: str) -> Dict[str, Any]:
        """
        从文本中提取元数据

        Args:
            text: 文本内容

        Returns:
            元数据字典
        """
        # 简单实现：提取标题、关键词等
        metadata = {}

        lines = text.split('\n')
        if lines:
            # 第一行可能是标题
            metadata['title'] = lines[0][:200]

        # 估算字符数
        metadata['length'] = len(text)

        return metadata