"""配置管理模块

使用 pydantic-settings 管理所有配置，支持从环境变量读取。
"""
from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""

    # SiliconFlow API 配置
    siliconflow_api_key: str = Field(
        default="",
        description="SiliconFlow API 密钥"
    )
    siliconflow_base_url: str = Field(
        default="https://api.siliconflow.cn/v1",
        description="SiliconFlow API 基础 URL"
    )

    # 嵌入模型配置
    embedding_model: str = Field(
        default="BAAI/bge-m3",
        description="嵌入模型名称"
    )

    # Reranker 配置
    reranker_model: str = Field(
        default="BAAI/bge-reranker-v2-m3",
        description="Reranker 模型名称"
    )
    reranker_enabled: bool = Field(
        default=True,
        description="是否启用 Reranker"
    )
    reranker_top_n: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Reranker 返回的文档数量"
    )

    # LLM 配置
    llm_model: str = Field(
        default="Qwen/Qwen3-8B",
        description="LLM 模型名称"
    )
    llm_temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="LLM 温度参数"
    )

    # 向量数据库配置
    chroma_persist_dir: str = Field(
        default="./chroma_db",
        description="Chroma 向量库持久化目录"
    )

    # 文档处理配置
    split_strategy: str = Field(
        default="recursive",
        description="文档切分策略: recursive(递归), fixed(固定长度), parent_child(父子文档)"
    )
    default_chunk_size: int = Field(
        default=1000,
        ge=100,
        le=5000,
        description="文档切分块大小"
    )
    default_chunk_overlap: int = Field(
        default=100,
        ge=0,
        le=1000,
        description="文档切分重叠大小"
    )
    separator_type: str = Field(
        default="auto",
        description="分隔符类型(仅用于recursive策略): auto, chinese, markdown, code, english"
    )
    auto_detect_content_type: bool = Field(
        default=True,
        description="是否自动检测内容类型并选择分隔符"
    )

    # Redis 缓存配置
    redis_host: str = Field(
        default="localhost",
        description="Redis 主机地址"
    )
    redis_port: int = Field(
        default=6379,
        ge=1,
        le=65535,
        description="Redis 端口"
    )
    redis_password: Optional[str] = Field(
        default=None,
        description="Redis 密码"
    )
    redis_db: int = Field(
        default=0,
        ge=0,
        le=15,
        description="Redis 数据库编号"
    )
    redis_enabled: bool = Field(
        default=True,
        description="是否启用 Redis 缓存"
    )
    cache_ttl_query: int = Field(
        default=3600,
        ge=0,
        description="向量查询缓存 TTL (秒)"
    )
    cache_ttl_response: int = Field(
        default=86400,
        ge=0,
        description="LLM 响应缓存 TTL (秒)"
    )

    # 应用配置
    app_host: str = Field(
        default="0.0.0.0",
        description="应用监听地址"
    )
    app_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="应用监听端口"
    )
    workers: int = Field(
        default=1,
        ge=1,
        le=32,
        description="工作进程数"
    )
    log_level: str = Field(
        default="INFO",
        description="日志级别"
    )

    # 并发控制
    max_concurrent_requests: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="最大并发请求数"
    )

    # 重试配置
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="API 调用最大重试次数"
    )
    retry_delay: float = Field(
        default=1.0,
        ge=0.1,
        description="重试延迟基数 (秒)"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """
    获取配置单例

    使用 lru_cache 确保配置只加载一次
    """
    return Settings()


# 导出配置实例
settings = get_settings()
