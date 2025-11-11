# -*- coding: utf-8 -*-
"""资源管理器，统一管理文件资源。"""
import os
from typing import List, Set
from contextlib import contextmanager

from astrbot.api import logger


class ResourceManager:
    """资源管理器，统一管理文件资源。
    
    使用上下文管理器确保资源在退出时自动清理。
    支持临时文件和缓存文件的分类管理。
    """

    def __init__(self, logger_instance=None):
        """初始化资源管理器。

        Args:
            logger_instance: 日志记录器实例，如果为None则使用默认logger
        """
        self._temp_files: Set[str] = set()
        self._cache_files: Set[str] = set()
        self.logger = logger_instance or logger
        self._cleaned = False

    def register_temp_file(self, file_path: str):
        """注册临时文件。

        Args:
            file_path: 临时文件路径
        """
        if file_path:
            self._temp_files.add(file_path)

    def register_cache_file(self, file_path: str):
        """注册缓存文件。

        Args:
            file_path: 缓存文件路径
        """
        if file_path:
            self._cache_files.add(file_path)

    def register_files(self, file_paths: List[str], is_cache: bool = False):
        """批量注册文件。

        Args:
            file_paths: 文件路径列表
            is_cache: 是否为缓存文件，False为临时文件
        """
        if is_cache:
            for file_path in file_paths:
                self.register_cache_file(file_path)
        else:
            for file_path in file_paths:
                self.register_temp_file(file_path)

    def cleanup_temp_files(self) -> int:
        """清理所有临时文件。

        Returns:
            成功清理的文件数量
        """
        return self._cleanup_files(self._temp_files)

    def cleanup_cache_files(self) -> int:
        """清理所有缓存文件。

        Returns:
            成功清理的文件数量
        """
        return self._cleanup_files(self._cache_files)

    def cleanup_all(self) -> int:
        """清理所有资源。

        Returns:
            成功清理的文件总数
        """
        if self._cleaned:
            return 0
        
        self._cleaned = True
        temp_count = self.cleanup_temp_files()
        cache_count = self.cleanup_cache_files()
        return temp_count + cache_count

    def _cleanup_files(self, file_paths: Set[str]) -> int:
        """清理文件集合。

        Args:
            file_paths: 文件路径集合

        Returns:
            成功清理的文件数量
        """
        cleaned_count = 0
        for file_path in file_paths:
            if file_path and os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                    cleaned_count += 1
                except Exception as e:
                    self.logger.warning(
                        f"清理文件失败: {file_path}, 错误: {e}"
                    )
        file_paths.clear()
        return cleaned_count

    def get_stats(self) -> dict:
        """获取资源统计信息。

        Returns:
            包含临时文件和缓存文件数量的字典
        """
        return {
            'temp_files_count': len(self._temp_files),
            'cache_files_count': len(self._cache_files),
            'total_files_count': len(self._temp_files) + len(self._cache_files),
            'cleaned': self._cleaned
        }

    def __enter__(self):
        """上下文管理器入口。"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口，自动清理资源。"""
        self.cleanup_all()
        return False  # 不抑制异常

    @contextmanager
    def temp_file_context(self, file_path: str):
        """临时文件上下文管理器。

        Args:
            file_path: 临时文件路径

        Yields:
            文件路径
        """
        self.register_temp_file(file_path)
        try:
            yield file_path
        finally:
            if file_path in self._temp_files:
                self._cleanup_files({file_path})
                self._temp_files.discard(file_path)

    @contextmanager
    def cache_file_context(self, file_path: str):
        """缓存文件上下文管理器。

        Args:
            file_path: 缓存文件路径

        Yields:
            文件路径
        """
        self.register_cache_file(file_path)
        try:
            yield file_path
        finally:
            if file_path in self._cache_files:
                self._cleanup_files({file_path})
                self._cache_files.discard(file_path)


