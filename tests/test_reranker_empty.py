"""测试 Reranker API 边界情况"""
import asyncio
import aiohttp
from app.core.config import settings

async def test_reranker_with_empty_docs():
    """测试空文档列表"""
    api_key = settings.siliconflow_api_key
    base_url = settings.siliconflow_base_url.rstrip("/")
    model = settings.reranker_model

    url = f"{base_url}/rerank"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # 测试 1: 空文档列表
    print("\n[TEST 1] 空文档列表")
    data = {
        "model": model,
        "query": "测试查询",
        "documents": [],
        "top_n": 3,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            print(f"Status: {response.status}")
            print(f"Response: {await response.text()}")

    # 测试 2: top_n 为 None
    print("\n[TEST 2] top_n 为 None")
    data = {
        "model": model,
        "query": "测试查询",
        "documents": ["文档1", "文档2"],
        "top_n": None,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            print(f"Status: {response.status}")
            print(f"Response: {await response.text()}")

    # 测试 3: 不传 top_n
    print("\n[TEST 3] 不传 top_n")
    data = {
        "model": model,
        "query": "测试查询",
        "documents": ["文档1", "文档2"],
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            print(f"Status: {response.status}")
            print(f"Response: {await response.text()}")

    # 测试 4: top_n 为 0
    print("\n[TEST 4] top_n 为 0")
    data = {
        "model": model,
        "query": "测试查询",
        "documents": ["文档1", "文档2"],
        "top_n": 0,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            print(f"Status: {response.status}")
            print(f"Response: {await response.text()}")

if __name__ == "__main__":
    asyncio.run(test_reranker_with_empty_docs())
