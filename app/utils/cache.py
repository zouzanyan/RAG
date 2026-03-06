"""Redis 缓存层

提供三级缓存：向量查询缓存、LLM 响应缓存、文档嵌入缓存。
"""
import hashlib
import json
from typing import Optional, Any
import redis.asyncio as redis
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CacheKey:
    """缓存键生成器"""

    @staticmethod
    def query_cache(query: str) -> str:
        """生成向量查询缓存键"""
        content = f"query:{query}"
        return f"rag:query:{hashlib.sha256(content.encode()).hexdigest()}"

    @staticmethod
    def response_cache(query: str, context: str) -> str:
        """生成 LLM 响应缓存键"""
        content = f"response:{query}:{context[:100]}"
        return f"rag:response:{hashlib.sha256(content.encode()).hexdigest()}"

    @staticmethod
    def document_cache(doc_id: str) -> str:
        """生成文档嵌入缓存键"""
        return f"rag:doc:{doc_id}"


class RedisCache:
    """Redis 缓存客户端"""

    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        self._enabled = settings.redis_enabled

    async def connect(self):
        """连接 Redis"""
        if not self._enabled:
            logger.info("Redis cache is disabled")
            return

        try:
            self._redis = await redis.from_url(
                f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}",
                password=settings.redis_password,
                encoding="utf-8",
                decode_responses=True,
            )
            # 测试连接
            await self._redis.ping()
            logger.info(f"Redis cache connected: {settings.redis_host}:{settings.redis_port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._enabled = False
            self._redis = None

    async def close(self):
        """关闭连接"""
        if self._redis:
            await self._redis.close()
            logger.info("Redis cache connection closed")

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self._enabled or not self._redis:
            return None

        try:
            value = await self._redis.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        return None

    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """设置缓存"""
        if not self._enabled or not self._redis:
            return False

        try:
            serialized = json.dumps(value, ensure_ascii=False)
            await self._redis.set(key, serialized, ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self._enabled or not self._redis:
            return False

        try:
            await self._redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的所有缓存"""
        if not self._enabled or not self._redis:
            return 0

        try:
            keys = []
            async for key in self._redis.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                await self._redis.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries with pattern: {pattern}")
                return len(keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error: {e}")
            return 0

    async def get_query_cache(self, query: str) -> Optional[Any]:
        """获取向量查询缓存"""
        key = CacheKey.query_cache(query)
        return await self.get(key)

    async def set_query_cache(self, query: str, docs: Any) -> bool:
        """设置向量查询缓存"""
        key = CacheKey.query_cache(query)
        return await self.set(key, docs, ttl=settings.cache_ttl_query)

    async def get_response_cache(self, query: str, context: str) -> Optional[str]:
        """获取 LLM 响应缓存"""
        key = CacheKey.response_cache(query, context)
        result = await self.get(key)
        return result.get("response") if result else None

    async def set_response_cache(self, query: str, context: str, response: str) -> bool:
        """设置 LLM 响应缓存"""
        key = CacheKey.response_cache(query, context)
        return await self.set(
            key,
            {"response": response},
            ttl=settings.cache_ttl_response
        )

    async def clear_document_cache(self, doc_id: str = None) -> int:
        """清除文档缓存"""
        if doc_id:
            key = CacheKey.document_cache(doc_id)
            await self.delete(key)
            return 1
        else:
            return await self.clear_pattern("rag:doc:*")

    async def clear_all_cache(self) -> int:
        """清除所有 RAG 缓存"""
        return await self.clear_pattern("rag:*")

    @property
    def is_enabled(self) -> bool:
        """检查缓存是否启用"""
        return self._enabled and self._redis is not None


# 全局缓存实例
_cache_instance: Optional[RedisCache] = None


async def get_cache() -> RedisCache:
    """获取缓存实例（单例）"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCache()
        await _cache_instance.connect()
    return _cache_instance
