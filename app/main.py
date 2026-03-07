"""FastAPI 应用主入口

企业级 RAG 系统的 FastAPI 应用。
"""
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.api.v1.endpoints import router, init_rag_engine
from app.utils.cache import get_cache
from app.utils.logger import logger, get_logger


app_logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    启动时初始化资源，关闭时清理资源。
    """
    # 启动时的操作
    app_logger.info("Starting RAG API server...")
    app_logger.info(f"Environment: {settings.log_level}")
    app_logger.info(f"Cache enabled: {settings.redis_enabled}")

    # 初始化缓存
    cache = await get_cache()
    if cache.is_enabled:
        app_logger.info("Redis cache connected")

    # 尝试初始化 RAG 引擎（如果存在持久化数据）
    try:
        await init_rag_engine()
        app_logger.info("RAG engine initialized")
    except Exception as e:
        app_logger.warning(f"RAG engine initialization deferred: {e}")

    yield

    # 关闭时的操作
    app_logger.info("Shutting down RAG API server...")

    # 关闭 RAG 引擎
    from app.api.v1.endpoints import _rag_engine
    if _rag_engine:
        await _rag_engine.close()

    # 关闭缓存
    if cache._redis:
        await cache.close()

    app_logger.info("RAG API server stopped")


# 创建 FastAPI 应用
app = FastAPI(
    title="RAG API",
    description="企业级 RAG (Retrieval-Augmented Generation) 知识库问答 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ==================== 中间件 ====================

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip 压缩中间件
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """
    请求中间件

    - 添加请求 ID
    - 记录请求日志
    - 记录响应时间
    """
    # 生成请求 ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # 记录请求开始
    start_time = time.time()

    # 添加请求 ID 到日志上下文
    logger.bind(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
    )

    app_logger.info(f"Request started: {request.method} {request.url.path}")

    # 处理请求
    try:
        response = await call_next(request)

        # 计算处理时间
        process_time = time.time() - start_time

        # 添加自定义响应头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)

        # 记录请求完成
        app_logger.info(
            f"Request completed: {request.method} {request.url.path} - "
            f"Status: {response.status_code} - Time: {process_time:.3f}s"
        )

        return response

    except Exception as e:
        process_time = time.time() - start_time
        app_logger.error(f"Request failed: {e}")
        raise


# ==================== 异常处理 ====================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    请求验证异常处理
    """
    app_logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "请求参数验证失败",
            "detail": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理
    """
    app_logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "服务器内部错误",
            "detail": str(exc) if settings.log_level == "DEBUG" else None,
        },
    )


# ==================== 路由 ====================

# 注册 API 路由
app.include_router(router)

# 挂载静态文件
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    app_logger.info(f"Static files mounted from: {static_dir}")
else:
    app_logger.warning(f"Static directory not found: {static_dir}")


# ==================== 根路径 ====================

@app.get("/", response_class=HTMLResponse)
async def root():
    """
    根路径

    返回前端页面。
    """
    index_file = static_dir / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding='utf-8'))
    return HTMLResponse(content="""
    <html>
        <head><title>RAG API</title></head>
        <body>
            <h1>RAG Knowledge Base Q&A System</h1>
            <p>API is running. Visit <a href="/docs">/docs</a> for API documentation.</p>
            <p>Frontend not found. Please ensure static files are built.</p>
        </body>
    </html>
    """)

@app.get("/api")
async def api_info():
    """
    API 信息端点

    返回 API 基本信息。
    """
    return {
        "name": "RAG API",
        "version": "1.0.0",
        "description": "Enterprise-grade RAG Knowledge Base Q&A API",
        "docs_url": "/docs",
        "health_check": "/health",
        "api_prefix": "/api/v1",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        workers=settings.workers,
        log_level=settings.log_level.lower(),
        reload=False,  # 生产环境禁用自动重载
    )
