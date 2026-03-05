"""配置管理模块

优先级：环境变量 > config.yaml > 默认值
"""
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional, Any
import yaml

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _substitute_env(value: str) -> str:
    """替换环境变量 ${VAR:default} 语法"""
    if not isinstance(value, str):
        return value

    pattern = r'\$\{([^:}]+)(?::([^}]*))?\}'

    def replace_var(match):
        var_name = match.group(1)
        default_val = match.group(2) if match.group(2) is not None else ""
        return os.getenv(var_name, default_val)

    return re.sub(pattern, replace_var, value)


def _load_config_yaml() -> dict:
    """加载 config.yaml 并替换环境变量"""
    config_path = Path("config.yaml")
    if not config_path.exists():
        return {}

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f) or {}

    # 递归替换环境变量
    def substitute_recursive(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: substitute_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [substitute_recursive(item) for item in obj]
        elif isinstance(obj, str):
            return _substitute_env(obj)
        return obj

    return substitute_recursive(config)


_yaml_config = _load_config_yaml()


class Settings(BaseSettings):
    """应用配置类"""

    # SiliconFlow API
    siliconflow_api_key: str = ""
    siliconflow_base_url: str = "https://api.siliconflow.cn/v1"

    # 模型配置
    embedding_model: str = "BAAI/bge-m3"
    reranker_model: str = "BAAI/bge-reranker-v2-m3"
    reranker_enabled: bool = True
    reranker_top_n: int = 3
    llm_model: str = "Qwen/Qwen3-8B"
    llm_temperature: float = 0.0

    # 向量数据库
    chroma_persist_dir: str = "./chroma_db"

    # 文档处理
    split_strategy: str = "recursive"
    separator_type: str = "auto"
    default_chunk_size: int = 1000
    default_chunk_overlap: int = 100
    auto_detect_content_type: bool = True

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0
    redis_enabled: bool = True
    cache_ttl_query: int = 3600
    cache_ttl_response: int = 86400

    # 应用
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    workers: int = 1
    log_level: str = "INFO"
    max_concurrent_requests: int = 50
    max_retries: int = 3
    retry_delay: float = 1.0

    @field_validator('*')
    @classmethod
    def validate_fields(cls, v):
        """字符串字段去除前后空格"""
        if isinstance(v, str):
            return v.strip()
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        """自定义配置优先级：环境变量 > YAML > 默认值"""
        return (
            init_settings,          # 初始化参数（最高优先级）
            env_settings,           # 环境变量
            dotenv_settings,        # .env 文件
            file_secret_settings,   # secrets 文件
        )


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    # 从 YAML 加载默认值
    yaml_defaults = {}

    def flatten_dict(d: dict, prefix: str = "") -> dict:
        """展平嵌套字典，使用下划线连接"""
        items = []
        for k, v in d.items():
            new_key = f"{prefix}_{k}" if prefix else k
            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)

    if _yaml_config:
        yaml_defaults = flatten_dict(_yaml_config)

    return Settings(**yaml_defaults)


# 导出配置实例
settings = get_settings()
