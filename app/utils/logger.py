"""日志系统配置

使用 loguru 提供结构化日志，支持 JSON 格式输出和请求链路追踪。
"""
import sys
import json
from pathlib import Path
from typing import Any
from loguru import logger
from app.core.config import settings


def serialize_log(record: dict[str, Any]) -> str:
    """
    序列化日志记录为 JSON 格式

    Args:
        record: 日志记录字典

    Returns:
        JSON 格式的日志字符串
    """
    subset = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "logger": record["name"],
        "message": record["message"],
        "module": record["module"],
        "function": record["function"],
        "line": record["line"],
    }

    # 添加额外字段
    if "extra" in record:
        subset.update(record["extra"])

    return json.dumps(subset, ensure_ascii=False)


def setup_logger() -> None:
    """
    配置 loguru 日志系统

    - 控制台输出：格式化文本
    - 文件输出：JSON 格式，支持日志轮转
    """
    # 移除默认的处理器
    logger.remove()

    # 控制台输出 - 格式化文本
    logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # 文件输出 - JSON 格式（用于日志分析）
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logger.add(
        log_dir / "app_{time:YYYY-MM-DD}.log",
        format=serialize_log,
        level="DEBUG",
        rotation="00:00",  # 每天午夜轮转
        retention="30 days",  # 保留 30 天
        compression="zip",  # 压缩旧日志
        enqueue=True,  # 异步写入
        encoding="utf-8",
    )

    # 错误日志单独记录
    logger.add(
        log_dir / "error_{time:YYYY-MM-DD}.log",
        format=serialize_log,
        level="ERROR",
        rotation="00:00",
        retention="90 days",
        compression="zip",
        enqueue=True,
        encoding="utf-8",
    )


class LoggerMixin:
    """
    日志混入类

    为类添加日志功能，支持自动记录类名和方法名
    """

    @property
    def log(self) -> Any:
        """获取带有类名上下文的 logger"""
        return logger.bind(class_name=self.__class__.__name__)


def get_logger(name: str = None) -> Any:
    """
    获取 logger 实例

    Args:
        name: logger 名称，默认使用调用模块名

    Returns:
        logger 实例
    """
    if name:
        return logger.bind(name=name)
    return logger


# 初始化日志系统
setup_logger()

# 导出 logger
__all__ = ["logger", "get_logger", "LoggerMixin"]
