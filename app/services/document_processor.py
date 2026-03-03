"""中文优化的文档分块处理器

提供多种分块策略，针对中文场景优化。
"""
from typing import List, Optional, Literal
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.document_loaders import TextLoader

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SplitStrategy:
    """分块策略常量"""
    FIXED = "fixed"           # 固定字符切分
    CHINESE = "chinese"       # 中文优化切分
    MARKDOWN = "markdown"     # Markdown 结构化切分
    CODE = "code"            # 代码友好切分
    PARENT_CHILD = "parent_child"  # 父子文档切分


class ChineseTextSplitter(RecursiveCharacterTextSplitter):
    """中文优化的文本分割器"""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
        length_function: callable = len,
        keep_separator: bool = True,
    ):
        """
        初始化中文文本分割器

        Args:
            chunk_size: 块大小（字符数）
            chunk_overlap: 重叠大小
            length_function: 长度计算函数
            keep_separator: 是否保留分隔符
        """
        # 中文优先的分隔符列表
        separators = [
            "\n\n",          # 段落（最高优先级）
            "\n",            # 行
            "。",            # 中文句号
            "！",            # 中文感叹号
            "？",            # 中文问号
            "；",            # 中文分号
            "，",            # 中文逗号
            "、",            # 中文顿号
            " ",             # 空格
            "",              # 字符级（最后手段）
        ]

        super().__init__(
            separators=separators,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=length_function,
            keep_separator=keep_separator,
        )


class MarkdownStructuralSplitter:
    """Markdown 结构化分割器"""

    def __init__(
        self,
        chunk_size: int = 1500,
        chunk_overlap: int = 150,
    ):
        """
        初始化 Markdown 分割器

        Args:
            chunk_size: 块大小
            chunk_overlap: 重叠大小
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        切分 Markdown 文档

        Args:
            documents: 文档列表

        Returns:
            切分后的文档列表
        """
        from langchain_text_splitters import MarkdownHeaderTextSplitter

        # 先按 Markdown 结构切分
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "Header 1"),
                ("##", "Header 2"),
                ("###", "Header 3"),
                ("####", "Header 4"),
            ]
        )

        chunks = []
        for doc in documents:
            # 按标题切分
            md_chunks = markdown_splitter.split_text(doc.page_content)

            # 如果单个章节仍然太大，进一步切分
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=["\n\n", "\n", "。", "！", "？", " ", ""],
            )

            for md_chunk in md_chunks:
                if len(md_chunk.page_content) > self.chunk_size:
                    # 继续切分大块
                    sub_chunks = text_splitter.split_documents([md_chunk])
                    chunks.extend(sub_chunks)
                else:
                    chunks.append(md_chunk)

        return chunks


class CodeFriendlySplitter(RecursiveCharacterTextSplitter):
    """代码友好的文本分割器"""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ):
        """
        初始化代码友好分割器

        Args:
            chunk_size: 块大小（代码用较小值）
            chunk_overlap: 重叠大小
        """
        # 代码优先的分隔符
        separators = [
            "\n\n",          # 两个空行（函数/类之间）
            "\n```",         # 代码块边界
            "```\n",         # 代码块边界
            "\n```",         # 代码块开始
            "\ndef ",        # Python 函数定义
            "\nclass ",      # Python 类定义
            "\nfunction ",   # JS 函数定义
            "\n",            # 单个换行
            " ",             # 空格
            "",              # 字符级
        ]

        super().__init__(
            separators=separators,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )


class ParentChildSplitter:
    """父子文档分割器"""

    def __init__(
        self,
        child_chunk_size: int = 200,
        child_overlap: int = 20,
        parent_chunk_size: int = 1500,
        parent_overlap: int = 100,
    ):
        """
        初始化父子文档分割器

        Args:
            child_chunk_size: 子文档大小（用于检索）
            child_overlap: 子文档重叠
            parent_chunk_size: 父文档大小（用于上下文）
            parent_overlap: 父文档重叠
        """
        self.child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=child_chunk_size,
            chunk_overlap=child_overlap,
            separators=["\n\n", "\n", "。", "！", "？", " ", ""],
            length_function=len,
        )

        self.parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=parent_chunk_size,
            chunk_overlap=parent_overlap,
            separators=["\n\n", "\n", "。", "！", "？", " ", ""],
            length_function=len,
        )

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        切分文档为父子结构

        子文档用于向量检索（精确匹配）
        父文档作为 LLM 上下文（丰富信息）

        Args:
            documents: 文档列表

        Returns:
            切分后的子文档列表（带父文档引用）
        """
        all_child_docs = []

        for doc in documents:
            # 先生成父文档
            parent_docs = self.parent_splitter.split_documents([doc])

            # 为每个父文档生成子文档
            for parent_doc in parent_docs:
                child_docs = self.child_splitter.split_documents([parent_doc])

                # 在子文档元数据中存储父文档引用
                for child_doc in child_docs:
                    child_doc.metadata["parent_doc_id"] = id(parent_doc)
                    child_doc.metadata["parent_content"] = parent_doc.page_content
                    all_child_docs.append(child_doc)

        return all_child_docs


class AdaptiveDocumentProcessor:
    """自适应文档处理器

    根据内容类型自动选择最优的分块策略。
    """

    def __init__(
        self,
        strategy: Literal[
            "fixed", "chinese", "markdown", "code", "parent_child"
        ] = "chinese",
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ):
        """
        初始化文档处理器

        Args:
            strategy: 分块策略
            chunk_size: 块大小（可选，覆盖默认值）
            chunk_overlap: 重叠大小（可选）
        """
        self.strategy = strategy
        self.chunk_size = chunk_size or 1000  # 中文默认 1000
        self.chunk_overlap = chunk_overlap or 100

        # 根据策略选择分割器
        if strategy == SplitStrategy.FIXED:
            self.splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
            )
        elif strategy == SplitStrategy.CHINESE:
            self.splitter = ChineseTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
            )
        elif strategy == SplitStrategy.MARKDOWN:
            self.splitter = MarkdownStructuralSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
            )
        elif strategy == SplitStrategy.CODE:
            self.splitter = CodeFriendlySplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
            )
        elif strategy == SplitStrategy.PARENT_CHILD:
            self.splitter = ParentChildSplitter()
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        logger.info(f"Document processor initialized with strategy: {strategy}")

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        切分文档

        Args:
            documents: 文档列表

        Returns:
            切分后的文档列表
        """
        logger.info(f"Splitting {len(documents)} documents with strategy: {self.strategy}")

        if self.strategy == SplitStrategy.MARKDOWN or self.strategy == SplitStrategy.PARENT_CHILD:
            # 这两种策略有特殊处理
            chunks = self.splitter.split_documents(documents)
        else:
            chunks = self.splitter.split_documents(documents)

        logger.info(f"Split into {len(chunks)} chunks")

        # 打印统计信息
        if chunks:
            sizes = [len(chunk.page_content) for chunk in chunks]
            logger.info(f"Chunk size stats - min: {min(sizes)}, max: {max(sizes)}, avg: {sum(sizes)/len(sizes):.0f}")

        return chunks

    @staticmethod
    def detect_content_type(content: str) -> str:
        """
        自动检测内容类型

        Args:
            content: 文本内容

        Returns:
            内容类型: "markdown", "code", "chinese", "general"
        """
        # 检测 Markdown
        if content.startswith("#") or "```" in content:
            return "markdown"

        # 检测代码
        code_indicators = ["def ", "class ", "function(", "import ", "const ", "let "]
        if any(indicator in content for indicator in code_indicators):
            return "code"

        # 检测中文
        chinese_chars = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
        if chinese_chars / len(content) > 0.3:  # 中文占比 > 30%
            return "chinese"

        return "general"

    @classmethod
    def auto_detect_and_split(
        cls,
        documents: List[Document],
        default_chunk_size: int = 1000,
        default_overlap: int = 100,
    ) -> List[Document]:
        """
        自动检测内容类型并选择最优策略

        Args:
            documents: 文档列表
            default_chunk_size: 默认块大小
            default_overlap: 默认重叠

        Returns:
            切分后的文档列表
        """
        all_chunks = []

        for doc in documents:
            content_type = cls.detect_content_type(doc.page_content)

            # 根据内容类型选择策略
            if content_type == "markdown":
                processor = cls(
                    strategy=SplitStrategy.MARKDOWN,
                    chunk_size=default_chunk_size,
                    chunk_overlap=default_overlap,
                )
            elif content_type == "code":
                processor = cls(
                    strategy=SplitStrategy.CODE,
                    chunk_size=500,  # 代码用更小的块
                    chunk_overlap=50,
                )
            elif content_type == "chinese":
                processor = cls(
                    strategy=SplitStrategy.CHINESE,
                    chunk_size=default_chunk_size,
                    chunk_overlap=default_overlap,
                )
            else:
                processor = cls(
                    strategy=SplitStrategy.CHINESE,  # 默认也用中文优化
                    chunk_size=default_chunk_size,
                    chunk_overlap=default_overlap,
                )

            chunks = processor.split_documents([doc])
            all_chunks.extend(chunks)

            logger.info(f"Content type '{content_type}': {len(doc.page_content)} chars -> {len(chunks)} chunks")

        return all_chunks


def create_document_processor(
    strategy: str = "chinese",
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> AdaptiveDocumentProcessor:
    """
    创建文档处理器工厂函数

    Args:
        strategy: 分块策略
        chunk_size: 块大小
        chunk_overlap: 重叠大小

    Returns:
        文档处理器实例
    """
    return AdaptiveDocumentProcessor(
        strategy=strategy,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
