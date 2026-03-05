# 🚀 RAG 知识库问答系统

> 企业级 RAG 系统，让 AI 准确回答你的文档问题

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-0.1+-blue?logo=python)](https://python.langchain.com)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## ✨ 为什么选择这个系统？

**传统 RAG 痛点**：
- ❌ 文档切分不合理，丢失上下文
- ❌ 检索不准确，答非所问
- ❌ 中文支持差，切分碎片化
- ❌ 每次都调用 API，成本高昂

**我们的解决方案**：
- ✅ **智能中文切分** - 针对中文优化，保持语义完整
- ✅ **两阶段检索** - 向量检索 + Rerank 精排，准确率提升 50%+
- ✅ **三级缓存** - Redis 缓存降低 90% API 成本
- ✅ **父子文档** - 小文档检索，大文档作答，兼顾精度和上下文

---

## 🎯 核心特性

| 特性 | 说明 | 好处 |
|------|------|------|
| **中文优化** | 按中文标点切分（。！？） | 语义完整，回答更准确 |
| **自动检测** | 自动识别 Markdown/代码/中文 | 无需手动配置 |
| **流式输出** | 实时流式返回答案 | 用户体验更好 |
| **高并发** | 异步架构 + 信号量控制 | 支持海量请求 |
| **可观测** | 结构化日志 + 链路追踪 | 问题快速定位 |

---

## 🚀 5 分钟快速开始

### 1️⃣ 配置 API 密钥

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env，填入你的 API 密钥
echo "SILICONFLOW_API_KEY=sk-xxx" > .env
```

> 💡 获取 SiliconFlow API Key: https://siliconflow.cn

### 2️⃣ 启动服务

```bash
# Docker 启动（推荐）
docker-compose up -d

# 或本地启动
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 3️⃣ 上传文档并提问

```bash
# 上传文档
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@doc.txt"

# 提问
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "什么是神经网络？"}'
```

### 4️⃣ 查看效果

🎉 打开浏览器访问：
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

---

## 📖 使用示例

### 场景 1：技术文档问答

```yaml
# config.yaml
document:
  split:
    strategy: recursive
    separator_type: markdown  # Markdown 结构化切分
```

```bash
# 上传 Markdown 技术文档
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@api_docs.md"

# 提问 API 使用方法
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "如何使用用户认证接口？"}'
```

### 场景 2：长文档精准问答

```yaml
# config.yaml
document:
  split:
    strategy: parent_child  # 父子文档模式
```

```bash
# 子文档（200字）用于精准检索
# 父文档（1000字）提供完整上下文
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "第三章讲了什么？"}'
```

---

## 🎨 配置文件

所有配置在 `config.yaml`（结构化、易维护）：

```yaml
# 文档切分配置
document:
  split:
    strategy: recursive     # 切分策略
    separator_type: auto    # 自动检测内容类型
    chunk_size: 1000        # 块大小
  auto_detect: true

# Redis 缓存
redis:
  enabled: true
  cache_ttl:
    query: 3600      # 查询缓存 1 小时
    response: 86400  # 响应缓存 24 小时

# 并发控制
app:
  workers: 4              # 工作进程数
  max_concurrent: 50      # 最大并发数
```

---

## 📊 架构设计

```
用户提问
    ↓
检查 Redis 缓存 ← 命中 → 直接返回
    ↓ 未命中
向量检索（Chroma）
    ↓
Rerank 精排（可选）
    ↓
LLM 生成（SiliconFlow）
    ↓
写入缓存 + 返回结果
```

---

## 🔧 切分策略对比

| 策略 | 适用场景 | 切分方式 |
|------|---------|---------|
| `recursive` | 🌟 通用场景 | 按语义边界递归切分 |
| `parent_child` | 📚 长文档 | 子文档检索 + 父文档作答 |
| `fixed` | 🔧 特殊需求 | 固定字符长度 |

**分隔符类型**（用于 recursive）：
- `auto` - 自动检测（推荐）
- `chinese` - 中文标点
- `markdown` - 标题结构
- `code` - 代码语法
- `english` - 英文标点

---

## 📦 技术栈

| 组件 | 技术 | 用途 |
|------|------|------|
| Web 框架 | FastAPI | 高性能异步 API |
| LLM 框架 | LangChain | RAG 编排 |
| 向量数据库 | Chroma | 文档向量存储 |
| 缓存 | Redis | 降低 API 成本 |
| 日志 | Loguru | 结构化日志 |

---

## 🛠️ 生产环境部署

```bash
# 1. 修改配置
vim config.yaml  # 调整 workers、并发数等

# 2. 使用多 worker
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# 3. 配置 Nginx 反向代理
docker-compose --profile with-nginx up -d

# 4. 监控日志
tail -f logs/app.log
```

---

## 📈 性能优化建议

1. **启用缓存** - 可降低 90% API 成本
2. **多 Worker** - 设置为 CPU 核心数
3. **调整块大小** - 根据文档类型优化
4. **外部 Redis** - 生产环境使用 Redis 集群

---

## 📄 License

MIT License - 详见 [LICENSE](LICENSE)

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给个 Star！**

Made with ❤️ by zouzanyan

</div>
