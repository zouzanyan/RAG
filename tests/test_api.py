import sys
import os
sys.path.insert(0, '..')

# 在 FastAPI 服务启动前测试
print("=== 环境变量检查 ===")
print(f"SILICONFLOW_API_KEY exists: {bool(os.getenv('SILICONFLOW_API_KEY'))}")
print(f"API Key length: {len(os.getenv('SILICONFLOW_API_KEY', ''))}")

from app.core.config import settings
print(f"Settings API Key: {settings.siliconflow_api_key[:20]}...")

# 测试嵌入
from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr

embeddings = OpenAIEmbeddings(
    base_url=settings.siliconflow_base_url,
    api_key=SecretStr(settings.siliconflow_api_key),
    model=settings.embedding_model,
)

result = embeddings.embed_query('test')
print(f"嵌入测试成功: {len(result)} 维")
