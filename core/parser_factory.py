# -*- coding: utf-8 -*-
"""解析器工厂类，用于统一创建和管理解析器实例。"""
from typing import List

from ..parsers.base_parser import BaseVideoParser
from .config_manager import ConfigManager
from .parser_registry import ParserRegistry


class ParserFactory:
    """解析器工厂类。"""

    _parsers_initialized = False

    @classmethod
    def _ensure_parsers_initialized(cls):
        """确保解析器已注册（延迟导入以避免循环导入）。"""
        if not cls._parsers_initialized:
            # 延迟导入解析器初始化器
            from . import parser_initializer  # noqa: F401
            cls._parsers_initialized = True

    @classmethod
    def create_parsers(
        cls,
        config_manager: ConfigManager
    ) -> List[BaseVideoParser]:
        """根据配置管理器创建解析器列表。

        Args:
            config_manager: ConfigManager实例

        Returns:
            解析器实例列表

        Raises:
            ValueError: 当没有启用任何解析器时
        """
        # 确保解析器已注册
        cls._ensure_parsers_initialized()
        
        # 从配置管理器获取参数
        common_params = config_manager.get_common_parser_params()
        twitter_proxy_params = config_manager.get_twitter_proxy_params()
        parser_enable_settings = config_manager.get_parser_enable_settings()

        parsers = []
        
        # 从注册表获取所有已注册的解析器
        registered_parsers = ParserRegistry.get_all()
        
        # 遍历所有已注册的解析器
        for parser_name, parser_info in registered_parsers.items():
            enable_key = f"enable_{parser_name}"
            is_enabled = parser_enable_settings.get(enable_key, True)
            
            if not is_enabled:
                continue
            
            # 构建参数
            parser_params = common_params.copy()
            
            # Twitter解析器需要额外的代理参数
            if parser_name == 'twitter' and parser_info.requires_proxy:
                parser_params.update(twitter_proxy_params)
            
            # 使用注册表创建解析器实例
            parser = ParserRegistry.create_parser(parser_name, parser_params)
            if parser is not None:
                parsers.append(parser)

        if not parsers:
            raise ValueError(
                "至少需要启用一个视频解析器。"
                "请检查配置中的 parser_enable_settings 设置。"
            )

        return parsers

