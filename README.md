# 企业级 RAG 知识库问答系统

基于 FastAPI、LangChain、Chroma 和 SiliconFlow 的企业级 RAG (Retrieval-Augmented Generation) 系统。

## 特性

- ✅ **异步架构** - 支持高并发请求
- ✅ **REST API** - 标准的 HTTP API 接口
- ✅ **Redis 缓存** - 三级缓存，降低 API 成本
- ✅ **两阶段检索** - 向量检索 + Rerank 精排
- ✅ **配置管理** - 环境变量配置，支持多环境
- ✅ **日志系统** - 结构化日志，支持链路追踪
- ✅ **Docker 部署** - 容器化部署，支持水平扩展
- ✅ **健康检查** - 完善的监控和健康检查

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
cd rag

# 复制环境变量文件
cp .env.example .env

# 编辑 .env 文件，填入你的 SiliconFlow API 密钥
# SILICONFLOW_API_KEY=your_api_key_here
```

### 2. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 启动服务

#### 方式一：本地运行

```bash
# 启动 FastAPI 服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 方式二：Docker 运行

```bash
# 启动所有服务（包括 Redis）
docker-compose up -d

# 查看日志
docker-compose logs -f rag-api
```

### 4. 访问 API

- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health
- ReDoc 文档: http://localhost:8000/redoc

## API 使用示例

### 上传文档

```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@doc1.txt"
```

### 查询问答

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "什么是神经网络？"}'
```

### 批量查询

```bash
curl -X POST http://localhost:8000/api/v1/batch/query \
  -H "Content-Type: application/json" \
  -d '{"queries": ["问题1", "问题2"]}'
```

### 流式查询

```bash
curl -X POST http://localhost:8000/api/v1/query/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "什么是神经网络？"}'
```

## 项目结构

```
rag/
├── app/
│   ├── api/              # API 路由
│   │   └── v1/
│   │       └── endpoints.py
│   ├── core/             # 核心配置
│   │   ├── config.py
│   │   └── security.py
│   ├── models/           # 数据模型
│   │   └── schemas.py
│   ├── services/         # 业务逻辑
│   │   ├── rag_service.py
│   │   └── reranker.py
│   ├── utils/            # 工具函数
│   │   ├── logger.py
│   │   └── cache.py
│   └── main.py           # FastAPI 应用入口
├── chroma_db/            # 向量数据库（持久化）
├── logs/                 # 日志文件
├── uploads/              # 上传文件
├── .env                  # 环境变量（需创建）
├── .env.example          # 环境变量模板
├── docker-compose.yml    # Docker 编排
├── Dockerfile            # Docker 镜像
└── requirements.txt      # Python 依赖
```

## 配置说明

主要环境变量（详见 `.env.example`）：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `SILICONFLOW_API_KEY` | SiliconFlow API 密钥 | *必需* |
| `SPLIT_STRATEGY` | 分块策略 | chinese |
| `DEFAULT_CHUNK_SIZE` | 文档块大小 | 1000 |
| `DEFAULT_CHUNK_OVERLAP` | 文档块重叠 | 100 |
| `AUTO_DETECT_CONTENT_TYPE` | 自动检测内容类型 | true |
| `REDIS_ENABLED` | 是否启用 Redis 缓存 | true |
| `RERANKER_ENABLED` | 是否启用 Reranker | true |
| `RERANKER_TOP_N` | Reranker 返回文档数 | 3 |
| `LLM_MODEL` | LLM 模型名称 | Qwen/Qwen3-8B |
| `WORKERS` | 工作进程数 | 1 |

### 分块策略说明

系统支持多种分块策略，针对不同场景优化：

| 策略 | 说明 | 中文友好 | 适用场景 |
|------|------|---------|---------|
| `chinese` | 中文优化切分（推荐） | ⭐⭐⭐⭐⭐ | 中文文档 |
| `fixed` | 固定字符切分 | ⭐⭐⭐ | 通用文本 |
| `markdown` | Markdown 结构化切分 | ⭐⭐⭐⭐ | 技术文档 |
| `code` | 代码友好切分 | ⭐⭐⭐⭐ | 代码文件 |
| `parent_child` | 父子文档切分 | ⭐⭐⭐⭐ | 长文档问答 |

**中文优化策略特点**：
- 按中文标点符号优先切分（。！？；，）
- 默认 1000 字符（约 500-700 汉字）
- 10% 重叠保持上下文连贯
- 自动识别段落和句子边界

## 性能优化建议

### 生产环境配置

1. **设置多工作进程**
   ```bash
   WORKERS=4  # 设置为 CPU 核心数
   ```

2. **启用 Nginx 反向代理**
   ```bash
   docker-compose --profile with-nginx up -d
   ```

3. **Redis 持久化**
   - 已配置 AOF 持久化
   - 建议生产环境使用外部 Redis 集群

### 缓存策略

- 向量查询缓存: 1 小时
- LLM 响应缓存: 24 小时
- 可根据实际业务调整 TTL

## 监控和日志

- 日志位置: `logs/` 目录
- 健康检查端点: `/health`
- 请求链路追踪: 响应头 `X-Request-ID`

## 常见问题

### 1. Redis 连接失败

如果 Redis 不可用，系统会自动降级，禁用缓存功能。

### 2. 向量库已存在

如果 `chroma_db/` 目录存在，系统会自动加载已有数据。

### 3. 文档上传失败

确保上传的是 `.txt` 格式的纯文本文件。

## 技术栈

- **Web 框架**: FastAPI + Uvicorn
- **LLM 框架**: LangChain
- **向量数据库**: Chroma
- **缓存**: Redis
- **日志**: Loguru
- **部署**: Docker + docker-compose

## License

MIT

## 支持

如有问题，请查看 API 文档或提交 Issue。
