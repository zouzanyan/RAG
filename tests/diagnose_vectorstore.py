"""诊断向量库问题"""
import asyncio
from pathlib import Path
from app.services.rag_service import LocalKnowledgeEngine
from app.core.config import settings

async def main():
    print("=" * 60)
    print("向量库诊断")
    print("=" * 60)

    print(f"\n1. 配置信息:")
    print(f"   Chroma persist dir: {settings.chroma_persist_dir}")
    print(f"   目录是否存在: {Path(settings.chroma_persist_dir).exists()}")

    print(f"\n2. 检查 test_doc.txt:")
    test_doc = Path("../test_doc.txt")
    print(f"   文件存在: {test_doc.exists()}")
    if test_doc.exists():
        content = test_doc.read_text(encoding='utf-8')
        print(f"   文件内容长度: {len(content)} 字符")
        print(f"   前100字符: {content[:100]}")

    print(f"\n3. 初始化 RAG 引擎:")
    engine = LocalKnowledgeEngine()

    print(f"\n4. 加载文档:")
    try:
        doc_count = await engine.load_documents(["test_doc.txt"])
        print(f"   加载的文档数: {doc_count}")
        print(f"   docs长度: {len(engine.docs)}")
        if engine.docs:
            print(f"   第一个文档内容: {engine.docs[0].page_content[:100]}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return

    print(f"\n5. 切分和向量化:")
    try:
        chunk_count = await engine.split_and_embed()
        print(f"   ✓ 创建的chunk数: {chunk_count}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return

    print(f"\n6. 检查向量库:")
    print(f"   向量库存在: {engine.vectorstore is not None}")
    print(f"   RAG chain存在: {engine.rag_chain is not None}")

    print(f"\n7. 测试查询:")
    try:
        answer = await engine.query("什么是机器学习？")
        print(f"   ✓ 查询成功")
        print(f"   回答长度: {len(answer)} 字符")
        print(f"   回答: {answer[:200]}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n8. 检查持久化目录:")
    chroma_path = Path(settings.chroma_persist_dir)
    if chroma_path.exists():
        print(f"   ✓ ChromaDB目录存在")
        files = list(chroma_path.rglob("*"))
        print(f"   文件数量: {len(files)}")
    else:
        print(f"   ❌ ChromaDB目录不存在")

    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
