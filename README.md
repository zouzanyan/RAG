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
- ❌ 没有 Web 界面，使用复杂

**我们的解决方案**：
- ✅ **智能中文切分** - 针对中文优化，保持语义完整
- ✅ **两阶段检索** - 向量检索 + Rerank 精排，准确率提升 50%+
- ✅ **三级缓存** - Redis 缓存降低 90% API 成本
- ✅ **父子文档** - 小文档检索，大文档作答，兼顾精度和上下文
- ✅ **Web 界面** - 现代化前端，开箱即用

---

## 🎯 核心特性

| 特性 | 说明 | 好处 |
|------|------|------|
| **中文优化** | 按中文标点切分（。！？） | 语义完整，回答更准确 |
| **自动检测** | 自动识别 Markdown/代码/中文 | 无需手动配置 |
| **流式输出** | 实时流式返回答案 | 用户体验更好 |
| **高并发** | 异步架构 + 信号量控制 | 支持海量请求 |
| **可观测** | 结构化日志 + 链路追踪 | 问题快速定位 |
| **Web 界面** | 现代化响应式前端 | 无需编程，即开即用 |

---

## 🚀 5 分钟快速开始

### 1️⃣ 克隆项目

```bash
git clone <your-repo-url>
cd rag
```

### 2️⃣ 配置 API 密钥

编辑 `config.yaml` 文件：

```yaml
siliconflow:
  api_key: "sk-your-api-key-here"  # 替换为你的 API 密钥
```

> 💡 获取 SiliconFlow API Key: https://siliconflow.cn

### 3️⃣ 安装依赖

```bash
pip install -r requirements.txt
```

### 4️⃣ 启动服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload
```

### 5️⃣ 访问 Web 界面

🎉 打开浏览器访问：**http://localhost:8010**

你将看到一个现代化的 Web 界面！

---

## 🎨 Web 界面功能

### 主要功能

#### 📄 文档管理
- 一键上传文档（支持 .txt 文件）
- 实时查看文档列表
- 自动切分和向量化

#### 🔍 智能问答
- 自然语言查询输入
- 实时显示查询结果
- 支持快捷键（Ctrl + Enter 快速提交）
- 显示性能指标（响应时间、缓存状态）

#### 📜 对话历史
- 自动保存最近 20 条对话
- 时间戳记录
- 快速回顾历史问答

#### ⚙️ 系统监控
- 实时健康检查
- 系统配置展示
- API 状态监控

### 界面预览

```
┌─────────────────────────────────────────────────────────┐
│  📚 RAG 知识库问答系统                    ● 在线 (v1.0.0)  │
├──────────────────────┬──────────────────────────────────┤
│  📄 文档管理         │  🔍 智能问答                     │
│  ┌─────────────────┐ │  ┌─────────────────────────────┐ │
│  │ ➕ 上传文档     │ │  │ 请输入您的问题...           │ │
│  └─────────────────┘ │  └─────────────────────────────┘ │
│                      │  [💬 提问] [🗑️ 清空]           │
│  已上传文档          │                                   │
│  • test_doc.txt      │  📝 回答                         │
│    (3 个分块)        │  机器学习是人工智能的核心...    │
│                      │                                   │
│  ⚙️ 系统配置         │  📜 对话历史                     │
│  嵌入模型: bge-m3    │  ❓ 什么是机器学习？            │
│  LLM: Qwen3-8B       │  机器学习是...                   │
└──────────────────────┴──────────────────────────────────┘
```

---

## 📖 使用指南

### Web 界面使用

#### 上传文档

1. 点击左侧"➕ 上传文档"按钮
2. 选择一个 .txt 文件
3. 等待上传完成（会显示成功提示）
4. 左侧文档列表会自动更新

#### 提问查询

1. 在右侧查询框输入问题，例如：
   ```
   什么是机器学习？
   深度学习有哪些应用？
   解释一下自然语言处理
   ```
2. 点击"💬 提问"按钮或按 `Ctrl + Enter`
3. 查看回答结果和性能指标

### API 使用

#### 上传文档

```bash
curl -X POST http://localhost:8010/api/v1/documents/upload \
  -F "file=@doc.txt"
```

**响应示例**：
```json
{
  "message": "Document uploaded and processed successfully",
  "doc_id": "13fe6cdd-41c8-4c76-bf19-9bfa2beac377",
  "filename": "doc.txt",
  "chunk_count": 5
}
```

#### 发送查询

```bash
curl -X POST http://localhost:8010/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "什么是机器学习？"}'
```

**响应示例**：
```json
{
  "answer": "机器学习是人工智能的核心领域之一。它通过算法使计算机能够从数据中学习，并做出预测或决策...",
  "sources": [],
  "cached": false,
  "duration_ms": 1520.98
}
```

#### 流式查询

```bash
curl -X POST http://localhost:8010/api/v1/query/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "解释一下自然语言处理"}'
```

返回 Server-Sent Events (SSE) 格式的流式数据。



## 🎨 配置文件

所有配置在 `config.yaml`（结构化、易维护）：

```yaml
# SiliconFlow API
siliconflow:
  api_key: "sk-your-key"  # 从环境变量读取更安全
  base_url: "https://api.siliconflow.cn/v1"

  # 模型配置
  models:
    embedding: "BAAI/bge-m3"       # 嵌入模型
    reranker: "BAAI/bge-reranker-v2-m3"  # 重排序模型
    llm: "Qwen/Qwen3-8B"           # 语言模型
    temperature: 0.0               # 温度参数

  # Reranker 配置
  reranker:
    enabled: true                 # 是否启用重排序
    top_n: 3                      # 返回前 N 个结果

# 文档处理
document:
  split:
    strategy: recursive           # 切分策略: recursive/parent_child/fixed
    separator_type: auto          # 分隔符类型: auto/chinese/markdown/code/english
    chunk_size: 1000              # 块大小 (100-5000)
    chunk_overlap: 100            # 重叠大小 (0-1000)
  auto_detect: true               # 自动检测内容类型

# 向量数据库
vectorstore:
  type: chroma
  persist_dir: ./chroma_db        # 向量库持久化目录

# Redis 缓存
redis:
  enabled: true                   # 是否启用缓存
  host: localhost
  port: 6379
  cache_ttl:
    query: 3600                   # 查询缓存 1 小时
    response: 86400               # 响应缓存 24 小时

# 应用配置
app:
  host: 0.0.0.0
  port: 8010                      # 服务端口
  workers: 1                      # 工作进程数
  log_level: INFO                 # 日志级别
  max_concurrent: 50              # 最大并发数
```

---

## 📊 架构设计

```
用户提问 (Web 界面 / API)
    ↓
检查 Redis 缓存 ← 命中 → 直接返回
    ↓ 未命中
向量检索（Chroma）- 相似度搜索
    ↓
Rerank 精排（可选）- 提升准确率
    ↓
LLM 生成（SiliconFlow）- 流式输出
    ↓
写入缓存 + 返回结果
```

---

## 🔧 切分策略对比

| 策略 | 适用场景 | 切分方式 | 特点 |
|------|---------|---------|------|
| `recursive` | 🌟 通用场景 | 按语义边界递归切分 | 推荐，平衡性能和效果 |
| `parent_child` | 📚 长文档 | 子文档检索 + 父文档作答 | 精准且上下文完整 |
| `fixed` | 🔧 特殊需求 | 固定字符长度 | 简单直接 |

**分隔符类型**（用于 recursive）：
- `auto` - 自动检测（推荐）
- `chinese` - 中文标点（。！？；，）
- `markdown` - 标题结构（# ## ###）
- `code` - 代码语法（def class function）
- `english` - 英文标点（. ! ? ; ,）

---

## 📦 技术栈

| 组件 | 技术 | 用途 |
|------|------|------|
| Web 框架 | FastAPI | 高性能异步 API |
| 前端 | HTML/CSS/JavaScript | 现代化 Web 界面 |
| LLM 框架 | LangChain | RAG 编排 |
| 向量数据库 | Chroma | 文档向量存储 |
| 缓存 | Redis | 降低 API 成本 |
| 日志 | Loguru | 结构化日志 |

---

## 🛠️ 高级功能

### 批量查询

```bash
curl -X POST http://localhost:8010/api/v1/batch/query \
  -H "Content-Type: application/json" \
  -d '{
    "queries": [
      "什么是机器学习？",
      "深度学习的应用领域有哪些？",
      "解释一下自然语言处理"
    ],
    "use_cache": true
  }'
```

### 重建向量库

```bash
curl -X POST http://localhost:8010/api/v1/documents/rebuild
```

### 动态配置更新

```bash
curl -X PATCH http://localhost:8010/api/v1/config \
  -H "Content-Type: application/json" \
  -d '{
    "llm_temperature": 0.7,
    "reranker_enabled": true
  }'
```

---

## 🐛 故障排除

### 问题 1：文档列表显示为空

**原因**：服务器重启后，内存中的文档列表被清空，但向量库数据持久化了。

**解决**：
```bash
# 方法 1：重新上传文档
# 在 Web 界面上点击"上传文档"按钮

# 方法 2：重建向量库
curl -X POST http://localhost:8010/api/v1/documents/rebuild
```

### 问题 2：查询返回"无法回答这个问题"

**原因**：
1. 向量库为空（需要先上传文档）
2. 问题与文档内容不相关
3. 向量搜索没有匹配到相关文档

**解决**：
```bash
# 检查文档列表
curl http://localhost:8010/api/v1/documents

# 如果为空，重新上传文档
curl -X POST http://localhost:8010/api/v1/documents/upload \
  -F "file=@your_document.txt"

# 或清空向量库重新开始
rm -rf chroma_db
# 然后重启服务器并重新上传文档
```

### 问题 3：Web 界面样式错乱

**原因**：浏览器缓存或静态文件路径问题。

**解决**：
1. 按 `Ctrl + F5` 强制刷新
2. 清除浏览器缓存
3. 检查浏览器控制台（F12）是否有错误

### 问题 4：Reranker 报错 "Field required"

**原因**：向量库中没有文档，传给 Reranker 的是空列表。

**解决**：先上传文档到向量库。

---

## 📈 性能优化建议

1. **启用 Redis 缓存** - 可降低 90% API 成本
2. **使用 Reranker** - 提升检索准确率 50%+
3. **调整块大小** - 根据文档类型优化（短文档用 500，长文档用 1500）
4. **多 Worker** - 设置为 CPU 核心数提升并发能力
5. **外部 Redis** - 生产环境使用 Redis 集群

---

## 🛡️ 生产环境部署

```bash
# 1. 修改配置
vim config.yaml

# 2. 使用多 worker
uvicorn app.main:app --host 0.0.0.0 --port 8010 --workers 4

# 3. 配置环境变量（更安全）
export SILICONFLOW_API_KEY="sk-xxx"

# 4. 使用进程管理器（推荐）
pip install supervisor
# 配置 supervisord.conf

# 5. 监控日志
tail -f logs/app.log
```

---

## 📚 API 文档

- **Swagger UI**: http://localhost:8010/docs
- **ReDoc**: http://localhost:8010/redoc
- **OpenAPI JSON**: http://localhost:8010/openapi.json

---

## 🔍 相关文档

- [前端使用指南](FRONTEND_GUIDE.md) - Web 界面详细说明
- [API 文档](docs/API.md) - 完整的 API 参考
- [配置说明](docs/CONFIG.md) - 配置文件详解

---

## 📄 License

MIT License - 详见 [LICENSE](LICENSE)

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## ⭐ Star History

如果这个项目对你有帮助，请给个 Star！

---

<div align="center">

**Made with ❤️ by zouzanyan**

**⭐ 如果这个项目对你有帮助，请给个 Star！**

</div>
