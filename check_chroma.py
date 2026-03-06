"""检查 ChromaDB 中的内容"""
import asyncio
from pathlib import Path
from app.services.rag_service import LocalKnowledgeEngine
from app.core.config import settings

async def main():
    print("=" * 60)
    print("ChromaDB 检查")
    print("=" * 60)

    print(f"\nChromaDB 路径: {settings.chroma_persist_dir}")

    # 初始化引擎
    engine = LocalKnowledgeEngine()

    print("\n尝试从持久化加载...")
    try:
        await engine.init_from_persist()
        print("加载成功")
    except Exception as e:
        print(f"加载失败: {e}")
        return

    # 检查 vectorstore
    print(f"\nVectorstore: {engine.vectorstore}")

    if engine.vectorstore:
        # 尝试获取所有 collection
        print("\n检查 collections...")
        try:
            # ChromaDB 的内部方法
            print(f"Collection: {engine.vectorstore._collection}")

            # 获取 collection 中的文档数量
            collection = engine.vectorstore._collection
            count = collection.count()
            print(f"Collection 中的文档数: {count}")

            if count > 0:
                # 获取一些文档
                results = collection.get(limit=5, include=['documents', 'metadatas'])
                print(f"\n前 {len(results['documents'])} 个文档:")
                for i, (doc, meta) in enumerate(zip(results['documents'], results['metadatas'])):
                    print(f"\n文档 {i+1}:")
                    print(f"  内容: {doc[:100]}...")
                    print(f"  元数据: {meta}")
            else:
                print("Collection 为空！")

        except Exception as e:
            print(f"检查 collection 失败: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
