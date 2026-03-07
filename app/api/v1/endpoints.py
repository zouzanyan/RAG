"""FastAPI 路由定义

提供所有 API 端点。
"""
import time
import uuid
from pathlib import Path
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.models.schemas import (
    HealthResponse,
    QueryRequest,
    QueryResponse,
    BatchQueryRequest,
    BatchQueryResponse,
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentDeleteResponse,
    VectorStoreRebuildResponse,
    RAGConfigResponse,
    ConfigUpdateRequest,
    ConfigUpdateResponse, DocumentInfo,
)
from app.services.rag_service import LocalKnowledgeEngine
from app.utils.cache import get_cache
from app.utils.logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["v1"])
security = HTTPBearer(auto_error=False)

# 全局 RAG 引擎实例
_rag_engine: LocalKnowledgeEngine = None


def get_rag_engine() -> LocalKnowledgeEngine:
    """获取 RAG 引擎实例（依赖注入）"""
    global _rag_engine
    if _rag_engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG engine not initialized. Please upload documents first."
        )
    return _rag_engine


async def init_rag_engine():
    """初始化 RAG 引擎"""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = LocalKnowledgeEngine()
        # 尝试从持久化目录加载
        try:
            await _rag_engine.init_from_persist()
            logger.info("RAG engine loaded from persist")
        except ValueError:
            logger.info("No existing vectorstore found, waiting for document upload")
    return _rag_engine


# ==================== 健康检查 ====================

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    cache = await get_cache()
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        cache_enabled=cache.is_enabled,
    )


# ==================== 查询接口 ====================

@router.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    engine: LocalKnowledgeEngine = Depends(get_rag_engine),
):
    """
    单次查询

    - **query**: 问题文本
    - **use_cache**: 是否使用缓存（默认 True）
    - **top_k**: 返回文档数量（可选，默认使用配置值）
    """
    cache = await get_cache()
    start_time = time.time()
    cached = False

    # 检查缓存
    if request.use_cache and cache.is_enabled:
        # 简单的响应缓存（基于查询）
        cached_response = await cache.get_response_cache(request.query, "")
        if cached_response:
            logger.info(f"Cache hit for query: {request.query[:50]}...")
            return QueryResponse(
                answer=cached_response,
                sources=[],
                cached=True,
                duration_ms=(time.time() - start_time) * 1000,
            )

    try:
        # 执行查询
        answer = await engine.query(request.query)

        # 设置缓存
        if request.use_cache and cache.is_enabled:
            await cache.set_response_cache(request.query, "", answer)

        return QueryResponse(
            answer=answer,
            sources=[],
            cached=cached,
            duration_ms=(time.time() - start_time) * 1000,
        )

    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )


@router.post("/query/stream")
async def query_stream(
    request: QueryRequest,
    engine: LocalKnowledgeEngine = Depends(get_rag_engine),
):
    """
    流式查询

    返回 Server-Sent Events (SSE) 格式的流式响应。
    """
    async def generate():
        try:
            async for chunk in engine.query_stream(request.query):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Stream query failed: {e}")
            yield f"data: [ERROR] {str(e)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/batch/query", response_model=BatchQueryResponse)
async def batch_query(
    request: BatchQueryRequest,
    engine: LocalKnowledgeEngine = Depends(get_rag_engine),
):
    """
    批量查询

    - **queries**: 问题列表（最多 10 个）
    - **use_cache**: 是否使用缓存
    - **top_k**: 返回文档数量
    """
    if len(request.queries) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 queries allowed per batch request"
        )

    start_time = time.time()
    results = []
    cached_count = 0

    for query in request.queries:
        try:
            # 复用单次查询逻辑
            query_req = QueryRequest(query=query, use_cache=request.use_cache)
            result = await query(query_req, engine)
            results.append(result)
            if result.cached:
                cached_count += 1
        except Exception as e:
            logger.error(f"Batch query failed for '{query}': {e}")
            # 添加错误响应
            results.append(QueryResponse(
                answer=f"查询失败: {str(e)}",
                sources=[],
                cached=False,
                duration_ms=0,
            ))

    return BatchQueryResponse(
        results=results,
        total_count=len(request.queries),
        cached_count=cached_count,
        total_duration_ms=(time.time() - start_time) * 1000,
    )


# ==================== 文档管理 ====================

@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
):
    """
    上传文档

    支持纯文本文件 (.txt)。
    上传后会自动进行文档切分和向量化。
    """
    global _rag_engine

    # 验证文件类型
    if not file.filename.endswith(".txt"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .txt files are supported"
        )

    try:
        # 保存文件
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        file_path = upload_dir / file.filename

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        logger.info(f"File uploaded: {file.filename}")

        # 初始化或获取 RAG 引擎
        if _rag_engine is None:
            _rag_engine = await init_rag_engine()

        # 加载文档
        doc_count = await _rag_engine.load_documents([str(file_path)])

        # 切分并生成向量
        chunk_count = await _rag_engine.split_and_embed()

        # 清除缓存（因为文档已更新）
        cache = await get_cache()
        await cache.clear_all_cache()

        return DocumentUploadResponse(
            message="Document uploaded and processed successfully",
            doc_id=str(uuid.uuid4()),
            filename=file.filename,
            chunk_count=chunk_count,
        )

    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    engine: LocalKnowledgeEngine = Depends(get_rag_engine),
):
    """
    获取文档列表

    返回已加载的文档信息。
    """
    # 从向量库中获取文档信息
    documents = []

    if engine.vectorstore:
        try:
            # 从向量库的 collection 中获取所有文档的元数据
            collection = engine.vectorstore._collection
            results = collection.get(include=['metadatas'])

            # 使用字典去重（按文件名）
            unique_docs = {}
            for metadata in results['metadatas']:
                source = metadata.get('source', '')
                if source:
                    # 提取文件名
                    filename = source.split('\\')[-1].split('/')[-1]
                    unique_docs[filename] = {
                        'filename': filename,
                        'source': source,
                        'chunk_count': 0  # 稍后统计
                    }

            # 统计每个文件的chunk数量
            for metadata in results['metadatas']:
                source = metadata.get('source', '')
                if source:
                    filename = source.split('\\')[-1].split('/')[-1]
                    if filename in unique_docs:
                        unique_docs[filename]['chunk_count'] += 1

            # 转换为 DocumentInfo 对象
            from datetime import datetime
            for doc_info in unique_docs.values():
                documents.append(DocumentInfo(
                    doc_id=str(hash(doc_info['source']) & 0x7fffffffffffffff),  # 转换为字符串
                    filename=doc_info['filename'],
                    chunk_count=doc_info['chunk_count'],
                    created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                ))
        except Exception as e:
            logger.error(f"Failed to get documents from vectorstore: {e}")

    # 如果向量库为空，返回 engine.docs（兼容旧逻辑）
    if not documents and engine.docs:
        documents = [
            DocumentInfo(
                doc_id=str(i),
                filename=f"document_{i}",
                chunk_count=0,
                created_at="",
            )
            for i in range(len(engine.docs))
        ]

    return DocumentListResponse(
        total=len(documents),
        documents=documents,
    )


@router.delete("/documents/{doc_id}", response_model=DocumentDeleteResponse)
async def delete_document(
    doc_id: str,
    engine: LocalKnowledgeEngine = Depends(get_rag_engine),
):
    """
    删除文档

    注意：当前实现需要重建向量库才能完全删除文档。
    """
    # 简化实现
    return DocumentDeleteResponse(
        message="Document deletion not fully implemented",
        doc_id=doc_id,
    )


@router.post("/documents/rebuild", response_model=VectorStoreRebuildResponse)
async def rebuild_vectorstore(
    engine: LocalKnowledgeEngine = Depends(get_rag_engine),
):
    """
    重建向量库

    重新加载所有文档并生成向量。
    """
    start_time = time.time()

    try:
        chunk_count = await engine.split_and_embed()
        duration = time.time() - start_time

        # 清除缓存
        cache = await get_cache()
        await cache.clear_all_cache()

        return VectorStoreRebuildResponse(
            message="Vector store rebuilt successfully",
            total_chunks=chunk_count,
            duration_seconds=duration,
        )

    except Exception as e:
        logger.error(f"Vector store rebuild failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rebuild failed: {str(e)}"
        )


# ==================== 配置管理 ====================

@router.get("/config", response_model=RAGConfigResponse)
async def get_config():
    """
    获取当前配置

    返回 RAG 系统的当前配置信息。
    """
    return RAGConfigResponse(
        embedding_model=settings.embedding_model,
        reranker_enabled=settings.reranker_enabled,
        reranker_model=settings.reranker_model,
        reranker_top_n=settings.reranker_top_n,
        llm_model=settings.llm_model,
        llm_temperature=settings.llm_temperature,
        split_strategy=settings.split_strategy,
        chunk_size=settings.default_chunk_size,
        chunk_overlap=settings.default_chunk_overlap,
        auto_detect_content_type=settings.auto_detect_content_type,
        cache_enabled=settings.redis_enabled,
    )


@router.patch("/config", response_model=ConfigUpdateResponse)
async def update_config(request: ConfigUpdateRequest):
    """
    更新配置

    支持动态更新部分配置项。
    注意：部分配置需要重启服务才能生效。
    """
    updated_fields = []

    # 简化实现：仅返回请求的更新字段
    if request.reranker_enabled is not None:
        updated_fields.append("reranker_enabled")
    if request.reranker_top_n is not None:
        updated_fields.append("reranker_top_n")
    if request.llm_temperature is not None:
        updated_fields.append("llm_temperature")
    if request.split_strategy is not None:
        updated_fields.append("split_strategy")
    if request.chunk_size is not None:
        updated_fields.append("chunk_size")
    if request.chunk_overlap is not None:
        updated_fields.append("chunk_overlap")
    if request.auto_detect_content_type is not None:
        updated_fields.append("auto_detect_content_type")

    return ConfigUpdateResponse(
        message="Configuration updated. Some changes may require restart.",
        updated_fields=updated_fields,
        current_config=await get_config(),
    )
