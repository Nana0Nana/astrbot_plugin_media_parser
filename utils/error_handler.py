# -*- coding: utf-8 -*-
"""错误处理工具。"""
import asyncio
import functools
from typing import Callable, Any

from astrbot.api import logger
from ..core.exceptions import (
    VideoParserError,
    ParseError,
    ResourceError
)


def handle_parse_errors(func: Callable) -> Callable:
    """解析错误处理装饰器。
    
    自动捕获异常并转换为统一的错误格式。
    
    Args:
        func: 要装饰的函数
    
    Returns:
        装饰后的函数
    """
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ParseError:
            raise
        except ResourceError:
            raise
        except VideoParserError:
            raise
        except Exception as e:
            logger.exception(f"{func.__name__}执行失败: {e}")
            raise ParseError(
                f"解析失败：{str(e)}",
                original_error=e
            )
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ParseError:
            raise
        except ResourceError:
            raise
        except VideoParserError:
            raise
        except Exception as e:
            logger.exception(f"{func.__name__}执行失败: {e}")
            raise ParseError(
                f"解析失败：{str(e)}",
                original_error=e
            )
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def normalize_error_message(error: Exception) -> str:
    """规范化错误消息。
    
    Args:
        error: 异常对象
    
    Returns:
        规范化后的错误消息
    """
    if isinstance(error, VideoParserError):
        return error.message
    
    error_msg = str(error)
    
    # 规范化常见错误消息
    if "本地缓存路径无效" in error_msg or "cache_dir" in error_msg.lower():
        return "本地缓存路径无效"
    
    if error_msg.startswith("解析失败："):
        return error_msg.replace("解析失败：", "", 1)
    
    return error_msg or "未知错误"


def format_parse_error(url: str, error: Exception) -> str:
    """格式化解析错误消息。
    
    Args:
        url: 解析失败的URL
        error: 异常对象
    
    Returns:
        格式化后的错误消息
    """
    failure_reason = normalize_error_message(error)
    return f"解析失败：{failure_reason}\n原始链接：{url}"


