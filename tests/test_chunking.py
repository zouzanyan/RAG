"""测试文档分块策略

演示不同切分策略的效果。
"""
from app.services.document_processor import DocumentSplitter
from langchain_core.documents import Document


def test_recursive_chinese():
    """测试递归切分 + 中文分隔符"""
    print("=" * 60)
    print("测试 1: 递归切分 + 中文分隔符")
    print("=" * 60)

    chinese_text = """
    神经网络是一种受人脑神经元结构启发的计算模型。它由大量相互连接的节点组成，这些节点分层组织，包括输入层、隐藏层和输出层。

    基本原理：神经元接收输入信号，通过权重进行加权求和，通过激活函数处理，产生输出。输出传递给下一层的神经元。

    前馈神经网络是最基础的类型，信号单向传播从输入层到输出层。每个连接都有一个权重参数，这些权重在训练过程中不断调整优化。

    训练神经网络通常使用反向传播算法，通过计算预测输出与真实标签之间的误差，从输出层向输入层反向传播梯度，更新网络权重。
    """

    splitter = DocumentSplitter(
        strategy="recursive",
        separator_type="chinese",
        chunk_size=200,
        chunk_overlap=30,
    )

    doc = Document(page_content=chinese_text.strip())
    chunks = splitter.split([doc])

    print(f"\n原始文本长度: {len(chinese_text.strip())} 字符")
    print(f"切分后块数: {len(chunks)}")
    print(f"\n分块结果:")
    for i, chunk in enumerate(chunks, 1):
        print(f"\n--- 块 {i} ({len(chunk.page_content)} 字符) ---")
        print(chunk.page_content[:100] + "..." if len(chunk.page_content) > 100 else chunk.page_content)


def test_strategy_comparison():
    """对比不同切分策略"""
    print("\n" + "=" * 60)
    print("测试 2: 不同策略对比")
    print("=" * 60)

    test_text = """
    ## 深度学习与神经网络应用

    深度学习是神经网络技术的重要发展，指的是具有多个隐藏层的神经网络。深度神经网络能够自动学习数据的多层次抽象表示。

    常见的神经网络架构：
    1. 卷积神经网络（CNN）：特别适合处理图像数据
    2. 循环神经网络（RNN）：适合处理序列数据
    3. Transformer：基于自注意力机制的架构

    神经网络训练需要大量数据和计算资源。
    """

    doc = Document(page_content=test_text.strip())

    # 测试不同策略
    strategies = [
        ("fixed (固定长度)", "fixed", "auto"),
        ("recursive + chinese", "recursive", "chinese"),
    ]

    for name, strategy, sep_type in strategies:
        print(f"\n【{name}】")
        splitter = DocumentSplitter(
            strategy=strategy,
            separator_type=sep_type,
            chunk_size=150,
            chunk_overlap=20,
        )
        chunks = splitter.split([doc])
        print(f"块数: {len(chunks)}")
        for i, chunk in enumerate(chunks, 1):
            preview = chunk.page_content[:50].replace("\n", " ")
            print(f"  块{i}: {preview}... ({len(chunk.page_content)}字符)")


def test_auto_detect():
    """测试自动内容类型检测"""
    print("\n" + "=" * 60)
    print("测试 3: 自动内容类型检测")
    print("=" * 60)

    test_cases = [
        ("Markdown 文本", "# 标题\n\n这是一段 Markdown 文本"),
        ("代码文本", "def hello():\n    print('Hello World')"),
        ("中文文本", "这是一段中文文本。包含多个句子！这里还有问号？"),
        ("英文文本", "This is English text. It has multiple sentences."),
    ]

    for name, text in test_cases:
        content_type = DocumentSplitter.detect_content_type(text)
        print(f"\n{name}: 检测为 '{content_type}'")


def test_parent_child():
    """测试父子文档切分"""
    print("\n" + "=" * 60)
    print("测试 4: 父子文档切分")
    print("=" * 60)

    text = "第一段内容。第二句！第三问？\n\n这是第二个段落。\n\n这是第三个段落，内容更长一些，用于测试父子切分功能。"

    splitter = DocumentSplitter(
        strategy="parent_child",
        separator_type="chinese",
        chunk_size=200,  # 父文档大小
        chunk_overlap=20,
    )

    doc = Document(page_content=text)
    chunks = splitter.split([doc])

    print(f"原文: {text}")
    print(f"\n切分结果:")
    for i, chunk in enumerate(chunks, 1):
        parent = chunk.metadata.get("parent_content", "")
        print(f"\n子文档 {i}:")
        print(f"  内容: {chunk.page_content}")
        print(f"  父文档长度: {len(parent)} 字符")


if __name__ == "__main__":
    test_recursive_chinese()
    test_strategy_comparison()
    test_auto_detect()
    test_parent_child()

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
