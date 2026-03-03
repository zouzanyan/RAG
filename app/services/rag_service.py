"""RAG 服务核心模块（异步版本）

提供文档处理、向量化、检索和问答等功能。
"""
import asyncio
import os
from pathlib import Path
from typing import List, Optional, AsyncIterator
from pydantic import SecretStr

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.documents import Document
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.services.reranker import SiliconFlowReranker
from app.services.document_processor import (
    AdaptiveDocumentProcessor,
    create_document_processor,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LocalKnowledgeEngine:
    """本地知识库 RAG 引擎（异步版本）"""

    def __init__(
            self,
            embedding_model=None,
            use_rerank: bool = None,
            rerank_top_n: int = None,
    ):
        """
        初始化 RAG 引擎

        Args:
            embedding_model: 自定义嵌入模型
            use_rerank: 是否启用 Reranker
            rerank_top_n: Reranker 返回的文档数量
        """
        # 初始化嵌入模型
        if embedding_model is None:
            self.embedding_model = OpenAIEmbeddings(
                base_url=settings.siliconflow_base_url,
                api_key=SecretStr(settings.siliconflow_api_key),
                model=settings.embedding_model,
            )
        else:
            self.embedding_model = embedding_model

        # 初始化 Reranker
        self.use_rerank = use_rerank if use_rerank is not None else settings.reranker_enabled
        self.rerank_top_n = rerank_top_n if rerank_top_n is not None else settings.reranker_top_n

        if self.use_rerank:
            self.reranker = SiliconFlowReranker(
                api_key=settings.siliconflow_api_key,
            )
        else:
            self.reranker = None

        # 状态变量
        self.vectorstore: Optional[Chroma] = None
        self.docs: List[Document] = []
        self.rag_chain = None
        self._semaphore = asyncio.Semaphore(settings.max_concurrent_requests)

        logger.info("RAG engine initialized", extra={
            "use_rerank": self.use_rerank,
            "rerank_top_n": self.rerank_top_n,
        })

    async def load_documents(self, file_paths: List[str]) -> int:
        """
        加载文档（异步）

        Args:
            file_paths: 文件路径列表

        Returns:
            加载的文档数量
        """
        loop = asyncio.get_event_loop()
        total_docs = 0

        async def load_single_file(path: str) -> List[Document]:
            """加载单个文件"""

            def _load():
                loader = TextLoader(path, encoding="utf-8")
                return loader.load()

            docs = await loop.run_in_executor(None, _load)
            return docs

        # 并发加载所有文件
        tasks = [load_single_file(path) for path in file_paths]
        all_docs = await asyncio.gather(*tasks)

        for docs in all_docs:
            self.docs.extend(docs)
            total_docs += len(docs)

        logger.info(f"Loaded {total_docs} documents from {len(file_paths)} files")
        return total_docs

    async def split_and_embed(
            self,
            chunk_size: int = None,
            chunk_overlap: int = None,
            persist_directory: str = None,
            split_strategy: str = None,
    ) -> int:
        """
        切分文档并生成向量（异步）

        Args:
            chunk_size: 切分块大小
            chunk_overlap: 切分重叠大小
            persist_directory: 向量库持久化目录
            split_strategy: 分块策略 (可选，默认使用配置)

        Returns:
            生成的 chunk 数量
        """
        chunk_size = chunk_size or settings.default_chunk_size
        chunk_overlap = chunk_overlap or settings.default_chunk_overlap
        persist_directory = persist_directory or settings.chroma_persist_dir
        split_strategy = split_strategy or settings.split_strategy

        loop = asyncio.get_event_loop()

        # 使用新的文档处理器
        def _split():
            # 如果启用自动检测
            if settings.auto_detect_content_type:
                logger.info("Using auto-detect content type strategy")
                return AdaptiveDocumentProcessor.auto_detect_and_split(
                    self.docs,
                    default_chunk_size=chunk_size,
                    default_overlap=chunk_overlap,
                )
            else:
                # 使用指定策略
                processor = create_document_processor(
                    strategy=split_strategy,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                )
                return processor.split_documents(self.docs)

        chunks = await loop.run_in_executor(None, _split)

        logger.info(
            f"Split {len(self.docs)} documents into {len(chunks)} chunks "
            f"(strategy: {split_strategy}, auto_detect: {settings.auto_detect_content_type})"
        )

        # 生成向量库
        def _create_vectorstore():
            return Chroma.from_documents(
                documents=chunks,
                embedding=self.embedding_model,
                persist_directory=persist_directory,
            )

        self.vectorstore = await loop.run_in_executor(None, _create_vectorstore)

        await self._build_rag_chain()

        return len(chunks)

    async def init_from_persist(self, persist_directory: str = None) -> bool:
        """
        从已持久化的向量库加载（异步）

        Args:
            persist_directory: 向量库持久化目录

        Returns:
            是否成功加载

        Raises:
            ValueError: 持久化目录不存在
        """
        persist_directory = persist_directory or settings.chroma_persist_dir

        if not os.path.exists(persist_directory):
            raise ValueError(
                f"持久化目录不存在: {persist_directory}，请先运行 split_and_embed"
            )

        loop = asyncio.get_event_loop()

        def _load_vectorstore():
            return Chroma(
                persist_directory=persist_directory,
                embedding_function=self.embedding_model,
            )

        self.vectorstore = await loop.run_in_executor(None, _load_vectorstore)

        await self._build_rag_chain()

        logger.info(f"Loaded vectorstore from {persist_directory}")
        return True

    async def _build_rag_chain(self):
        """构建 RAG 链（异步）"""
        # 初始化 LLM
        llm = ChatOpenAI(
            base_url=f"{settings.siliconflow_base_url}/",
            api_key=SecretStr(settings.siliconflow_api_key),
            model=settings.llm_model,
            temperature=settings.llm_temperature,
        )

        # 提示模板
        template = """请根据以下上下文信息回答问题。如果上下文中没有相关信息，请说"根据提供的文档，我无法回答这个问题"。

上下文:
{context}

问题: {question}

回答:
"""
        prompt = ChatPromptTemplate.from_template(template)

        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        async def retrieve_and_rerank(question: str) -> List[Document]:
            """检索并可选地进行 rerank"""
            async with self._semaphore:
                # 检索文档
                retrieve_k = self.rerank_top_n * 3 if self.use_rerank else self.rerank_top_n

                loop = asyncio.get_event_loop()

                def _search():
                    return self.vectorstore.similarity_search(question, k=retrieve_k)

                docs = await loop.run_in_executor(None, _search)

                # Rerank
                if self.use_rerank and self.reranker:
                    docs = await self.reranker.rerank_documents(
                        question, docs, self.rerank_top_n
                    )

                return docs

        # 构建 RAG 链
        self.rag_chain = (
                {
                    "context": RunnableLambda(retrieve_and_rerank) | format_docs,
                    "question": RunnablePassthrough(),
                }
                | prompt
                | llm
        )

        logger.info("RAG chain built successfully")

    @retry(
        stop=stop_after_attempt(settings.max_retries),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def query(self, question: str) -> str:
        """
        查询问答（异步）

        Args:
            question: 问题文本

        Returns:
            回答文本

        Raises:
            ValueError: RAG chain 未初始化
        """
        if not self.rag_chain:
            raise ValueError("RAG chain not initialized. Run split_and_embed first.")

        logger.debug(f"Querying: {question[:50]}...")

        result = await self.rag_chain.ainvoke(question)
        answer = result.content

        logger.info(f"Query completed", extra={
            "question_length": len(question),
            "answer_length": len(answer),
        })

        return answer

    async def query_stream(self, question: str) -> AsyncIterator[str]:
        """
        流式查询（异步）

        Args:
            question: 问题文本

        Yields:
            回答文本片段

        Raises:
            ValueError: RAG chain 未初始化
        """
        if not self.rag_chain:
            raise ValueError("RAG chain not initialized. Run split_and_embed first.")

        logger.debug(f"Streaming query: {question[:50]}...")

        async for chunk in self.rag_chain.astream_log(question):
            if chunk.name == "ChatOpenAI":
                for token in chunk.generations[0][:]:
                    yield token.text

    async def close(self):
        """关闭资源"""
        if self.reranker:
            await self.reranker.close()

        logger.info("RAG engine closed")
