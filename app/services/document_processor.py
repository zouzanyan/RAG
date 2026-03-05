"""文档分块处理器

简洁设计：
- 策略：recursive（递归切分）、fixed（固定长度）、parent_child（父子文档）
- 分隔符：auto、chinese、markdown、code、english（仅用于 recursive 策略）
"""
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from app.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentSplitter:
    """文档切分器（统一的切分接口）"""

    def __init__(
        self,
        strategy: str = "recursive",
        separator_type: str = "auto",
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
    ):
        """
        初始化切分器

        Args:
            strategy: 切分策略 (recursive/fixed/parent_child)
            separator_type: 分隔符类型 (auto/chinese/markdown/code/english) - 仅用于 recursive
            chunk_size: 块大小
            chunk_overlap: 重叠大小
        """
        self.strategy = strategy
        self.separator_type = separator_type
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        if strategy == "recursive":
            self.splitter = RecursiveCharacterTextSplitter(
                separators=self._get_separators(separator_type),
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        elif strategy == "fixed":
            self.splitter = RecursiveCharacterTextSplitter(
                separators=[""],  # 字符级切分
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        elif strategy == "parent_child":
            # 父子文档：小文档检索，大文档作为上下文
            self.child_splitter = RecursiveCharacterTextSplitter(
                separators=self._get_separators(separator_type),
                chunk_size=chunk_size // 5,  # 子文档较小
                chunk_overlap=chunk_overlap // 5,
            )
            self.parent_splitter = RecursiveCharacterTextSplitter(
                separators=self._get_separators(separator_type),
                chunk_size=chunk_size,  # 父文档较大
                chunk_overlap=chunk_overlap,
            )
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        logger.info(f"Splitter initialized: strategy={strategy}, separator={separator_type}")

    def _get_separators(self, separator_type: str) -> List[str]:
        """获取分隔符列表"""
        if separator_type == "chinese":
            return ["\n\n", "\n", "。", "！", "？", "；", "，", "、", " ", ""]
        elif separator_type == "markdown":
            return ["\n\n", "\n#", "\n```", "\n-", "\n", " ", ""]
        elif separator_type == "code":
            return ["\n\n", "\n```", "```\n", "\ndef ", "\nclass ", "\nfunction ", "\n", " ", ""]
        elif separator_type == "english":
            return ["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""]
        else:  # auto - 混合中英文
            return ["\n\n", "\n", "。", "！", "？", "；", ". ", "! ", "? ", "，", ", ", "、", " ", ""]

    def split(self, documents: List[Document]) -> List[Document]:
        """切分文档"""
        if self.strategy == "parent_child":
            # 父子文档特殊处理
            all_child_docs = []
            for doc in documents:
                parent_docs = self.parent_splitter.split_documents([doc])
                for parent_doc in parent_docs:
                    child_docs = self.child_splitter.split_documents([parent_doc])
                    for child_doc in child_docs:
                        child_doc.metadata["parent_content"] = parent_doc.page_content
                        all_child_docs.append(child_doc)
            return all_child_docs
        else:
            return self.splitter.split_documents(documents)

    @staticmethod
    def detect_content_type(content: str) -> str:
        """自动检测内容类型"""
        if content.startswith("#") or "```" in content:
            return "markdown"
        if any(indicator in content for indicator in ["def ", "class ", "function(", "import "]):
            return "code"
        if len(content) > 0 and sum(1 for c in content if '\u4e00' <= c <= '\u9fff') / len(content) > 0.3:
            return "chinese"
        return "english"

    @classmethod
    def auto_detect_and_split(
        cls,
        documents: List[Document],
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
    ) -> List[Document]:
        """自动检测内容类型并切分"""
        all_chunks = []
        for doc in documents:
            content_type = cls.detect_content_type(doc.page_content)
            splitter = cls(strategy="recursive", separator_type=content_type, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            chunks = splitter.split([doc])
            all_chunks.extend(chunks)
            logger.info(f"Content type '{content_type}': {len(doc.page_content)} chars -> {len(chunks)} chunks")
        return all_chunks
