"""工具模块

包含日志、缓存、重试等工具函数。
"""
from app.utils.logger import logger, get_logger, LoggerMixin

# 延迟导入缓存模块（需要 Redis）
try:
    from app.utils.cache import RedisCache, get_cache, CacheKey
    _cache_available = True
except ImportError:
    _cache_available = False

__all__ = [
    "logger",
    "get_logger",
    "LoggerMixin",
]

if _cache_available:
    __all__.extend(["RedisCache", "get_cache", "CacheKey"])
