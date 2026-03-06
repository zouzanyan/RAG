"""日志系统配置

使用 loguru 提供结构化日志。
"""
import sys
from pathlib import Path
from typing import Any
from loguru import logger
from app.core.config import settings


def setup_logger() -> None:
    """
    配置 loguru 日志系统

    - 控制台输出：格式化文本
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
