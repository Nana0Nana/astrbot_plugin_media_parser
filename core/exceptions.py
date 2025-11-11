# -*- coding: utf-8 -*-
"""视频解析器异常定义。"""


class VideoParserError(Exception):
    """视频解析器基础异常类。
    
    所有视频解析器相关的异常都应继承此类。
    """
    
    def __init__(self, message: str, error_code: str = None, original_error: Exception = None):
        """初始化异常。

        Args:
            message: 错误消息
            error_code: 错误代码（可选）
            original_error: 原始异常（可选）
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.original_error = original_error


class ParseError(VideoParserError):
    """解析错误。
    
    当视频链接解析失败时抛出此异常。
    """
    
    def __init__(self, message: str, url: str = None, original_error: Exception = None):
        """初始化解析错误。

        Args:
            message: 错误消息
            url: 解析失败的URL（可选）
            original_error: 原始异常（可选）
        """
        super().__init__(message, error_code="PARSE_ERROR", original_error=original_error)
        self.url = url


class ResourceError(VideoParserError):
    """资源错误。
    
    当资源（文件、目录等）操作失败时抛出此异常。
    """
    
    def __init__(self, message: str, resource_path: str = None, original_error: Exception = None):
        """初始化资源错误。

        Args:
            message: 错误消息
            resource_path: 资源路径（可选）
            original_error: 原始异常（可选）
        """
        super().__init__(message, error_code="RESOURCE_ERROR", original_error=original_error)
        self.resource_path = resource_path


class ConfigurationError(VideoParserError):
    """配置错误。
    
    当配置无效或缺失时抛出此异常。
    """
    
    def __init__(self, message: str, config_key: str = None, original_error: Exception = None):
        """初始化配置错误。

        Args:
            message: 错误消息
            config_key: 配置键（可选）
            original_error: 原始异常（可选）
        """
        super().__init__(message, error_code="CONFIG_ERROR", original_error=original_error)
        self.config_key = config_key


class NetworkError(VideoParserError):
    """网络错误。
    
    当网络请求失败时抛出此异常。
    """
    
    def __init__(
        self,
        message: str,
        url: str = None,
        status_code: int = None,
        original_error: Exception = None
    ):
        """初始化网络错误。

        Args:
            message: 错误消息
            url: 请求的URL（可选）
            status_code: HTTP状态码（可选）
            original_error: 原始异常（可选）
        """
        super().__init__(message, error_code="NETWORK_ERROR", original_error=original_error)
        self.url = url
        self.status_code = status_code


