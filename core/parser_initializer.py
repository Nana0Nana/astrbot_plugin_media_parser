# -*- coding: utf-8 -*-
"""解析器初始化模块，用于注册所有内置解析器。"""
from .parser_registry import ParserRegistry
from ..parsers import (
    BilibiliParser,
    DouyinParser,
    KuaishouParser,
    XiaohongshuParser,
    TwitterParser
)


def register_builtin_parsers():
    """注册所有内置解析器。"""
    # 注册Bilibili解析器
    ParserRegistry.register(
        name='bilibili',
        parser_class=BilibiliParser,
        requires_proxy=False
    )
    
    # 注册Douyin解析器
    ParserRegistry.register(
        name='douyin',
        parser_class=DouyinParser,
        requires_proxy=False
    )
    
    # 注册Kuaishou解析器
    ParserRegistry.register(
        name='kuaishou',
        parser_class=KuaishouParser,
        requires_proxy=False
    )
    
    # 注册Xiaohongshu解析器
    ParserRegistry.register(
        name='xiaohongshu',
        parser_class=XiaohongshuParser,
        requires_proxy=False
    )
    
    # 注册Twitter解析器
    ParserRegistry.register(
        name='twitter',
        parser_class=TwitterParser,
        requires_proxy=True
    )


# 自动注册内置解析器
register_builtin_parsers()

