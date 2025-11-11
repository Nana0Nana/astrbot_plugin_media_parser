# -*- coding: utf-8 -*-
"""解析器注册表，用于管理解析器的注册和发现。"""
from typing import Dict, Type, Optional, Callable, Any
from dataclasses import dataclass

from ..parsers.base_parser import BaseVideoParser


@dataclass
class ParserInfo:
    """解析器信息。"""
    name: str
    parser_class: Type[BaseVideoParser]
    requires_proxy: bool = False
    factory: Optional[Callable[[Dict[str, Any]], BaseVideoParser]] = None


class ParserRegistry:
    """解析器注册表。
    
    用于管理所有可用的解析器，支持动态注册和依赖注入。
    """
    
    _instance: Optional['ParserRegistry'] = None
    _registry: Dict[str, ParserInfo] = {}
    
    def __new__(cls):
        """单例模式。"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._registry = {}
        return cls._instance
    
    @classmethod
    def register(
        cls,
        name: str,
        parser_class: Type[BaseVideoParser],
        requires_proxy: bool = False,
        factory: Optional[Callable[[Dict[str, Any]], BaseVideoParser]] = None
    ):
        """注册解析器。
        
        Args:
            name: 解析器名称（如 'bilibili', 'douyin'）
            parser_class: 解析器类
            requires_proxy: 是否需要代理
            factory: 可选的工厂函数，用于创建解析器实例
                    如果提供，将使用此函数而不是直接实例化类
        """
        instance = cls()
        instance._registry[name] = ParserInfo(
            name=name,
            parser_class=parser_class,
            requires_proxy=requires_proxy,
            factory=factory
        )
    
    @classmethod
    def unregister(cls, name: str):
        """取消注册解析器。
        
        Args:
            name: 解析器名称
        """
        instance = cls()
        if name in instance._registry:
            del instance._registry[name]
    
    @classmethod
    def get(cls, name: str) -> Optional[ParserInfo]:
        """获取解析器信息。
        
        Args:
            name: 解析器名称
            
        Returns:
            解析器信息，如果不存在返回None
        """
        instance = cls()
        return instance._registry.get(name)
    
    @classmethod
    def get_all(cls) -> Dict[str, ParserInfo]:
        """获取所有已注册的解析器。
        
        Returns:
            解析器信息字典
        """
        instance = cls()
        return instance._registry.copy()
    
    @classmethod
    def is_registered(cls, name: str) -> bool:
        """检查解析器是否已注册。
        
        Args:
            name: 解析器名称
            
        Returns:
            如果已注册返回True，否则返回False
        """
        instance = cls()
        return name in instance._registry
    
    @classmethod
    def clear(cls):
        """清空注册表（主要用于测试）。"""
        instance = cls()
        instance._registry.clear()
    
    @classmethod
    def create_parser(
        cls,
        name: str,
        params: Dict[str, Any]
    ) -> Optional[BaseVideoParser]:
        """创建解析器实例。
        
        Args:
            name: 解析器名称
            params: 解析器初始化参数
            
        Returns:
            解析器实例，如果解析器未注册或创建失败返回None
        """
        parser_info = cls.get(name)
        if parser_info is None:
            return None
        
        try:
            if parser_info.factory:
                return parser_info.factory(params)
            else:
                return parser_info.parser_class(**params)
        except Exception:
            return None

