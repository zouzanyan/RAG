"""测试中文优化分块策略

演示不同分块策略的效果。
"""
import asyncio
from app.services.document_processor import (
    ChineseTextSplitter,
    AdaptiveDocumentProcessor,
    SplitStrategy,
)
from langchain_core.documents import Document


def test_chinese_splitter():
    """测试中文文本分割器"""
    print("=" * 60)
    print("测试 1: 中文优化分块")
    print("=" * 60)

    # 示例文本（中文）
    chinese_text = """
    # 神经网络简介

    神经网络是一种受人脑神经元结构启发的计算模型。它由大量相互连接的节点（称为神经元）组成，这些节点分层组织，包括输入层、隐藏层和输出层。

    基本原理：神经元接收输入信号，通过权重进行加权求和，通过激活函数处理，产生输出。输出传递给下一层的神经元。

    前馈神经网络是最基础的类型，信号单向传播从输入层到输出层。每个连接都有一个权重参数，这些权重在训练过程中不断调整优化。

    训练神经网络通常使用反向传播算法，通过计算预测输出与真实标签之间的误差，从输出层向输入层反向传播梯度，更新网络权重。
    """

    # 创建中文分割器
    splitter = ChineseTextSplitter(
        chunk_size=200,
        chunk_overlap=30,
    )

    # 切分文档
    doc = Document(page_content=chinese_text.strip())
    chunks = splitter.split_documents([doc])

    print(f"\n原始文本长度: {len(chinese_text.strip())} 字符")
    print(f"切分后块数: {len(chunks)}")
    print(f"\n分块结果:")
    for i, chunk in enumerate(chunks, 1):
        print(f"\n--- 块 {i} ({len(chunk.page_content)} 字符) ---")
        print(chunk.page_content[:100] + "..." if len(chunk.page_content) > 100 else chunk.page_content)


def test_strategy_comparison():
    """对比不同分块策略"""
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

    strategies = [
        ("fixed (固定字符)", SplitStrategy.FIXED),
        ("chinese (中文优化)", SplitStrategy.CHINESE),
    ]

    for name, strategy in strategies:
        print(f"\n【{name}】")
        processor = AdaptiveDocumentProcessor(
            strategy=strategy,
            chunk_size=150,
            chunk_overlap=20,
        )
        chunks = processor.split_documents([doc])
        print(f"块数: {len(chunks)}")
        for i, chunk in enumerate(chunks, 1):
            preview = chunk.page_content[:50].replace("\n", " ")
            print(f"  块{i}: {preview}... ({len(chunk.page_content)}字符)")


def test_auto_detect():
    """测试自动内容类型检测"""
    print("\n" + "=" * 60)
    print("测试 3: 自动内容类型检测")
    print("=" * 60)

    # 不同类型的文本
    test_cases = [
        ("Markdown 文本", "# 标题\n\n这是一段 Markdown 文本"),
        ("代码文本", "def hello():\n    print('Hello World')"),
        ("中文文本", "这是一段中文文本。包含多个句子！这里还有问号？"),
        ("英文文本", "This is English text. It has multiple sentences."),
    ]

    for name, text in test_cases:
        content_type = AdaptiveDocumentProcessor.detect_content_type(text)
        print(f"\n{name}: 检测为 '{content_type}'")


def test_separators():
    """测试中文分隔符优先级"""
    print("\n" + "=" * 60)
    print("测试 4: 中文分隔符优先级")
    print("=" * 60)

    # 混合多种分隔符的文本
    text = """第一段内容。第二句！第三问？第四句，第五短语。这是第二个段落。另起一行。"""

    splitter = ChineseTextSplitter(chunk_size=50, chunk_overlap=10)
    doc = Document(page_content=text)
    chunks = splitter.split_documents([doc])

    print(f"原文: {text}")
    print(f"\n切分结果:")
    for i, chunk in enumerate(chunks, 1):
        print(f"块{i}: {chunk.page_content}")


if __name__ == "__main__":
    import sys
    import io
    # 设置标准输出为 UTF-8 编码
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("\n" + "=" * 60)
    print("中文优化分块策略测试")
    print("=" * 60)

    test_chinese_splitter()
    test_strategy_comparison()
    test_auto_detect()
    test_separators()

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
