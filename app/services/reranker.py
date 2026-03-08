"""通用 Rerank 模型客户端（异步版本）

支持任何兼容 OpenAI Rerank API 格式的服务（OpenAI/Azure/SiliconFlow/其他）。
使用 aiohttp 实现异步 HTTP 请求，支持高并发场景。
"""
import asyncio
from typing import List, Optional
import aiohttp
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class APIError(Exception):
    """API 调用异常"""
    pass


class SiliconFlowReranker:
    """通用 Reranker 客户端（异步版本）

    支持任何兼容 OpenAI Rerank API 格式的服务。

    注意：类名保留 SiliconFlowReranker 以保持 API 兼容性。
    实际上这是一个通用的 reranker 客户端，不限于硅基流动。
    """

    def __init__(
        self,
        api_key: str,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        初始化 Reranker

        Args:
            api_key: API 密钥
            model: 模型名称，默认使用配置中的模型
            base_url: API 基础 URL，默认使用配置中的 URL
        """
        self.api_key = api_key
        self.model = model or settings.reranker_model
        self.base_url = (base_url or settings.llm_base_url).rstrip("/")
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """
        获取或创建 aiohttp 会话

        Returns:
            aiohttp.ClientSession 实例
        """
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            connector = aiohttp.TCPConnector(limit=100)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
            )
        return self._session

    @retry(
        stop=stop_after_attempt(settings.max_retries),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
    )
    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_n: Optional[int] = None
    ) -> List[dict]:
        """
        对文档进行重排序（异步）

        Args:
            query: 查询文本
            documents: 文档列表
            top_n: 返回前 N 个结果

        Returns:
            排序后的文档列表，包含索引和相关性分数

        Raises:
            APIError: API 调用失败
        """
        # 如果文档列表为空，直接返回空结果
        if not documents:
            logger.warning("Empty document list provided to reranker, returning empty results")
            return []

        url = f"{self.base_url}/rerank"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.model,
            "query": query,
            "documents": documents,
            "top_n": top_n if top_n else len(documents),
        }

        session = await self._get_session()

        try:
            logger.info(f"Calling rerank API: {url}", extra={
                "model": self.model,
                "query": query[:50],
                "doc_count": len(documents),
                "top_n": top_n,
            })

            async with session.post(url, headers=headers, json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Rerank API error: {response.status} - {error_text}")
                    raise APIError(f"API returned status {response.status}: {error_text}")

                result = await response.json()
                rerank_results = result.get("results", [])

                logger.debug(f"Rerank completed", extra={
                    "result_count": len(rerank_results),
                })

                return rerank_results

        except aiohttp.ClientError as e:
            logger.error(f"Rerank request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in rerank: {e}")
            raise APIError(f"Rerank failed: {str(e)}")

    async def rerank_documents(
        self,
        query: str,
        documents: List,  # LangChain Document 对象
        top_n: Optional[int] = None
    ) -> List:
        """
        对 LangChain Document 对象进行重排序（异步）

        Args:
            query: 查询文本
            documents: LangChain Document 对象列表
            top_n: 返回前 N 个结果

        Returns:
            排序后的 Document 对象列表
        """
        # 如果文档列表为空，直接返回空结果
        if not documents:
            logger.warning("Empty document list provided to rerank_documents, returning empty results")
            return []

        doc_texts = [doc.page_content for doc in documents]
        rerank_results = await self.rerank(query, doc_texts, top_n)

        # 根据 rerank 结果重新排序文档
        reranked_docs = []
        for item in rerank_results:
            idx = item["index"]
            score = item.get("relevance_score", 0)
            doc = documents[idx]

            # 创建新的 Document 副本，避免修改原始数据
            from langchain_core.documents import Document
            new_doc = Document(
                page_content=doc.page_content,
                metadata={**doc.metadata, "rerank_score": score}
            )
            reranked_docs.append(new_doc)

        return reranked_docs

    async def close(self):
        """关闭 HTTP 会话"""
        if self._session and not self._session.closed:
            await self._session.close()
            # 等待所有连接关闭
            await asyncio.sleep(0.25)

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        """异步上下文管理器出口"""
        await self.close()
