# -*- coding: utf-8 -*-
"""核心模块。"""
# 延迟导入以避免循环导入
# 这些模块在需要时才会被导入

__all__ = [
    'ParserManager',
    'ParserFactory',
    'ConfigManager',
    'ParserRegistry',
]


def __getattr__(name):
    """延迟导入模块以避免循环导入。"""
    if name == 'ParserManager':
        from .parser_manager import ParserManager
        return ParserManager
    elif name == 'ParserFactory':
        from .parser_factory import ParserFactory
        return ParserFactory
    elif name == 'ConfigManager':
        from .config_manager import ConfigManager
        return ConfigManager
    elif name == 'ParserRegistry':
        from .parser_registry import ParserRegistry
        return ParserRegistry
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

