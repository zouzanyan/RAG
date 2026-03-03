"""API 数据模型

定义所有 API 请求和响应的 Pydantic 模型。
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ==================== 基础响应模型 ====================

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(description="服务状态")
    version: str = Field(description="版本号")
    cache_enabled: bool = Field(description="缓存是否启用")


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str = Field(description="错误类型")
    message: str = Field(description="错误消息")
    detail: Optional[str] = Field(None, description="详细信息")


# ==================== 文档模型 ====================

class DocumentInfo(BaseModel):
    """文档信息"""
    doc_id: str = Field(description="文档 ID")
    filename: str = Field(description="文件名")
    chunk_count: int = Field(description="文档分块数量")
    created_at: str = Field(description="创建时间")


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    message: str = Field(description="响应消息")
    doc_id: str = Field(description="文档 ID")
    filename: str = Field(description="文件名")
    chunk_count: int = Field(description="生成的文档块数量")


class DocumentListResponse(BaseModel):
    """文档列表响应"""
    total: int = Field(description="文档总数")
    documents: List[DocumentInfo] = Field(description="文档列表")


class DocumentDeleteResponse(BaseModel):
    """文档删除响应"""
    message: str = Field(description="响应消息")
    doc_id: str = Field(description="文档 ID")


class VectorStoreRebuildResponse(BaseModel):
    """向量库重建响应"""
    message: str = Field(description="响应消息")
    total_chunks: int = Field(description="总文档块数量")
    duration_seconds: float = Field(description="耗时（秒）")


# ==================== 查询模型 ====================

class QueryRequest(BaseModel):
    """查询请求"""
    query: str = Field(..., description="问题文本", min_length=1)
    use_cache: bool = Field(True, description="是否使用缓存")
    top_k: Optional[int] = Field(None, description="返回文档数量")


class QueryResponse(BaseModel):
    """查询响应"""
    answer: str = Field(description="回答文本")
    sources: List[Dict[str, Any]] = Field(description="来源文档信息")
    cached: bool = Field(description="是否来自缓存")
    duration_ms: float = Field(description="响应时间（毫秒）")


class BatchQueryRequest(BaseModel):
    """批量查询请求"""
    queries: List[str] = Field(..., description="问题列表", min_length=1, max_length=10)
    use_cache: bool = Field(True, description="是否使用缓存")
    top_k: Optional[int] = Field(None, description="返回文档数量")


class BatchQueryResponse(BaseModel):
    """批量查询响应"""
    results: List[QueryResponse] = Field(description="查询结果列表")
    total_count: int = Field(description="总查询数量")
    cached_count: int = Field(description="缓存命中数量")
    total_duration_ms: float = Field(description="总响应时间（毫秒）")


# ==================== 配置模型 ====================

class RAGConfigResponse(BaseModel):
    """RAG 配置响应"""
    embedding_model: str = Field(description="嵌入模型")
    reranker_enabled: bool = Field(description="是否启用 Reranker")
    reranker_model: str = Field(description="Reranker 模型")
    reranker_top_n: int = Field(description="Reranker 返回数量")
    llm_model: str = Field(description="LLM 模型")
    llm_temperature: float = Field(description="LLM 温度")
    split_strategy: str = Field(description="分块策略")
    chunk_size: int = Field(description="文档块大小")
    chunk_overlap: int = Field(description="文档块重叠")
    auto_detect_content_type: bool = Field(description="是否自动检测内容类型")
    cache_enabled: bool = Field(description="缓存是否启用")


class ConfigUpdateRequest(BaseModel):
    """配置更新请求"""
    reranker_enabled: Optional[bool] = Field(None, description="是否启用 Reranker")
    reranker_top_n: Optional[int] = Field(None, ge=1, le=10, description="Reranker 返回数量")
    llm_temperature: Optional[float] = Field(None, ge=0, le=2, description="LLM 温度")
    split_strategy: Optional[str] = Field(
        None,
        description="分块策略: fixed, chinese, markdown, code, parent_child"
    )
    chunk_size: Optional[int] = Field(None, ge=100, le=5000, description="文档块大小")
    chunk_overlap: Optional[int] = Field(None, ge=0, le=1000, description="文档块重叠")
    auto_detect_content_type: Optional[bool] = Field(None, description="是否自动检测内容类型")


class ConfigUpdateResponse(BaseModel):
    """配置更新响应"""
    message: str = Field(description="响应消息")
    updated_fields: List[str] = Field(description="更新的字段列表")
    current_config: RAGConfigResponse = Field(description="当前配置")
