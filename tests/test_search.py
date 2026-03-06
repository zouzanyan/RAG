"""测试向量搜索和完整查询"""
import asyncio
from app.services.rag_service import LocalKnowledgeEngine

async def main():
    print("初始化引擎...")
    engine = LocalKnowledgeEngine()
    await engine.init_from_persist()

    query = "什么是机器学习？"

    print(f"\n1. 向量搜索 (k=5):")
    docs = engine.vectorstore.similarity_search(query, k=5)
    print(f"找到 {len(docs)} 个文档")

    for i, doc in enumerate(docs):
        print(f"\n文档 {i+1}:")
        print(f"  来源: {doc.metadata.get('source', 'unknown')}")
        print(f"  内容: {doc.page_content[:80]}...")

    print(f"\n2. 完整 RAG 查询:")
    try:
        answer = await engine.query(query)
        print(f"回答: {answer}")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
