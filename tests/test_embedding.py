"""测试嵌入模型"""
import asyncio
from app.core.config import settings
from langchain_openai import OpenAIEmbeddings

async def test_embedding():
    print("=" * 60)
    print("测试嵌入模型")
    print("=" * 60)

    print(f"\n嵌入模型: {settings.embedding_model}")
    print(f"API Base: {settings.siliconflow_base_url}")

    # 初始化嵌入模型
    embeddings = OpenAIEmbeddings(
        base_url=settings.siliconflow_base_url,
        api_key=settings.siliconflow_api_key,
        model=settings.embedding_model,
    )

    # 测试中文和英文文本的嵌入
    texts = [
        "什么是机器学习？",
        "机器学习是人工智能的核心领域之一",
        "What is machine learning?",
        "This is a test document",
    ]

    print(f"\n生成嵌入向量...")
    try:
        vectors = await embeddings.aembed_documents(texts)
        print(f"成功生成 {len(vectors)} 个向量")
        print(f"向量维度: {len(vectors[0])}")

        # 计算相似度
        import numpy as np
        query_vec = np.array(vectors[0])  # "什么是机器学习？"

        print(f"\n相似度分析:")
        for i, (text, vec) in enumerate(zip(texts, vectors)):
            similarity = np.dot(query_vec, np.array(vec)) / (
                np.linalg.norm(query_vec) * np.linalg.norm(np.array(vec))
            )
            print(f"{i+1}. {text[:30]:30s} -> {similarity:.4f}")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test_embedding())
