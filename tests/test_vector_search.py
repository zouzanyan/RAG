"""测试向量检索"""
import asyncio
from app.services.rag_service import LocalKnowledgeEngine

async def test_search():
    print("初始化引擎...")
    engine = LocalKnowledgeEngine()

    print("从持久化加载...")
    try:
        await engine.init_from_persist()
        print("加载成功")
    except Exception as e:
        print(f"加载失败: {e}")
        print("重新创建向量库...")
        await engine.load_documents(["test_doc.txt"])
        await engine.split_and_embed()

    print("\n测试向量检索:")
    query = "什么是机器学习？"

    # 直接测试向量搜索
    docs = engine.vectorstore.similarity_search(query, k=3)
    print(f"找到 {len(docs)} 个文档")

    for i, doc in enumerate(docs):
        print(f"\n文档 {i+1}:")
        print(f"内容: {doc.page_content[:100]}")
        print(f"元数据: {doc.metadata}")

    print("\n测试完整查询:")
    try:
        answer = await engine.query(query)
        print(f"回答: {answer}")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_search())
