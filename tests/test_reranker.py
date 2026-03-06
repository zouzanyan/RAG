"""测试 Reranker API 调用"""
import asyncio
import aiohttp
from app.core.config import settings

async def test_reranker():
    """测试 reranker API"""
    api_key = settings.siliconflow_api_key
    base_url = settings.siliconflow_base_url.rstrip("/")
    model = settings.reranker_model

    url = f"{base_url}/rerank"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # 测试数据
    data = {
        "model": model,
        "query": "什么是机器学习",
        "documents": [
            "机器学习是人工智能的核心领域之一",
            "深度学习使用多层神经网络",
            "自然语言处理是AI的重要应用"
        ],
        "top_n": 3,
    }

    print("=" * 60)
    print("测试 Reranker API")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"Model: {model}")
    print(f"Request data: {data}")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            print(f"Status: {response.status}")
            print(f"Response: {await response.text()}")

if __name__ == "__main__":
    asyncio.run(test_reranker())
