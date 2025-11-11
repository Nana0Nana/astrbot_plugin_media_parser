# -*- coding: utf-8 -*-
"""配置管理类，用于统一解析和管理配置。"""
from typing import Dict, Any

from .constants import (
    DEFAULT_CACHE_DIR,
    DEFAULT_MAX_CONCURRENT_DOWNLOADS,
    DEFAULT_LARGE_MEDIA_THRESHOLD_MB,
    DEFAULT_MAX_MEDIA_SIZE_MB,
    MAX_LARGE_MEDIA_THRESHOLD_MB
)
from .exceptions import ConfigurationError


class ConfigManager:
    """配置管理类。"""

    def __init__(self, config: Dict[str, Any], validate: bool = True):
        """初始化配置管理器。

        Args:
            config: 配置字典
            validate: 是否验证配置，默认为True

        Raises:
            ConfigurationError: 当配置验证失败时
        """
        self.config = config
        if validate:
            self._validate_config()
        self._parse_config()

    def _validate_config(self):
        """验证配置的有效性。

        Raises:
            ConfigurationError: 当配置无效时
        """
        # 验证媒体大小设置
        media_size_settings = self.config.get("media_size_settings", {})
        max_media_size_mb = media_size_settings.get(
            "max_media_size_mb",
            DEFAULT_MAX_MEDIA_SIZE_MB
        )
        if not isinstance(max_media_size_mb, (int, float)) or max_media_size_mb < 0:
            raise ConfigurationError(
                f"max_media_size_mb必须是非负数，当前值: {max_media_size_mb}",
                config_key="media_size_settings.max_media_size_mb"
            )
        
        large_media_threshold_mb = media_size_settings.get(
            "large_media_threshold_mb",
            DEFAULT_LARGE_MEDIA_THRESHOLD_MB
        )
        if not isinstance(large_media_threshold_mb, (int, float)) or large_media_threshold_mb < 0:
            raise ConfigurationError(
                f"large_media_threshold_mb必须是非负数，当前值: {large_media_threshold_mb}",
                config_key="media_size_settings.large_media_threshold_mb"
            )
        
        # 验证下载设置
        download_settings = self.config.get("download_settings", {})
        max_concurrent_downloads = download_settings.get(
            "max_concurrent_downloads",
            DEFAULT_MAX_CONCURRENT_DOWNLOADS
        )
        if not isinstance(max_concurrent_downloads, int) or max_concurrent_downloads < 1:
            raise ConfigurationError(
                f"max_concurrent_downloads必须是大于0的整数，当前值: {max_concurrent_downloads}",
                config_key="download_settings.max_concurrent_downloads"
            )
        
        # 验证Twitter代理设置
        twitter_proxy_settings = self.config.get("twitter_proxy_settings", {})
        proxy_url = twitter_proxy_settings.get("twitter_proxy_url", "")
        use_image_proxy = twitter_proxy_settings.get("twitter_use_image_proxy", False)
        use_video_proxy = twitter_proxy_settings.get("twitter_use_video_proxy", False)
        
        if (use_image_proxy or use_video_proxy) and not proxy_url:
            raise ConfigurationError(
                "启用Twitter代理时必须提供twitter_proxy_url",
                config_key="twitter_proxy_settings.twitter_proxy_url"
            )
        
        if proxy_url and not (
            proxy_url.startswith("http://") or 
            proxy_url.startswith("https://") or 
            proxy_url.startswith("socks5://")
        ):
            raise ConfigurationError(
                (
                    f"twitter_proxy_url格式无效，应为http://、https://或"
                    f"socks5://开头，当前值: {proxy_url}"
                ),
                config_key="twitter_proxy_settings.twitter_proxy_url"
            )

    def _parse_config(self):
        """解析配置。"""
        # 触发设置
        trigger_settings = self.config.get("trigger_settings", {})
        self.is_auto_parse = trigger_settings.get("is_auto_parse", True)
        self.trigger_keywords = trigger_settings.get(
            "trigger_keywords",
            ["视频解析", "解析视频"]
        )

        # 媒体大小设置
        media_size_settings = self.config.get("media_size_settings", {})
        self.max_media_size_mb = media_size_settings.get(
            "max_media_size_mb",
            DEFAULT_MAX_MEDIA_SIZE_MB
        )
        large_media_threshold_mb = media_size_settings.get(
            "large_media_threshold_mb",
            DEFAULT_LARGE_MEDIA_THRESHOLD_MB
        )
        # 先限制最大值，再判断是否启用
        large_media_threshold_mb = min(
            large_media_threshold_mb,
            MAX_LARGE_MEDIA_THRESHOLD_MB
        )
        if large_media_threshold_mb <= 0:
            large_media_threshold_mb = 0.0
        self.large_media_threshold_mb = large_media_threshold_mb

        # 下载设置
        download_settings = self.config.get("download_settings", {})
        self.cache_dir = download_settings.get(
            "cache_dir",
            DEFAULT_CACHE_DIR
        )
        self.pre_download_all_media = download_settings.get(
            "pre_download_all_media",
            False
        )
        self.max_concurrent_downloads = download_settings.get(
            "max_concurrent_downloads",
            DEFAULT_MAX_CONCURRENT_DOWNLOADS
        )

        # 其他设置
        self.is_auto_pack = self.config.get("is_auto_pack", True)
        
        # Twitter代理设置（用于解析器创建）
        twitter_proxy_settings = self.config.get("twitter_proxy_settings", {})
        self.twitter_use_image_proxy = twitter_proxy_settings.get(
            "twitter_use_image_proxy",
            False
        )
        self.twitter_use_video_proxy = twitter_proxy_settings.get(
            "twitter_use_video_proxy",
            False
        )
        self.twitter_proxy_url = twitter_proxy_settings.get(
            "twitter_proxy_url",
            ""
        )

    def get_parser_config(self) -> Dict[str, Any]:
        """获取解析器配置（用于工厂类）。

        Returns:
            解析器配置字典
        """
        return self.config
    
    def get_common_parser_params(self) -> Dict[str, Any]:
        """获取通用解析器参数。

        Returns:
            包含通用参数的字典
        """
        return {
            'max_media_size_mb': self.max_media_size_mb,
            'large_media_threshold_mb': self.large_media_threshold_mb,
            'cache_dir': self.cache_dir,
            'pre_download_all_media': self.pre_download_all_media,
            'max_concurrent_downloads': self.max_concurrent_downloads
        }
    
    def get_twitter_proxy_params(self) -> Dict[str, Any]:
        """获取Twitter代理参数。

        Returns:
            包含Twitter代理参数的字典
        """
        return {
            'use_image_proxy': self.twitter_use_image_proxy,
            'use_video_proxy': self.twitter_use_video_proxy,
            'proxy_url': self.twitter_proxy_url
        }
    
    def get_parser_enable_settings(self) -> Dict[str, bool]:
        """获取解析器启用设置。

        Returns:
            解析器启用设置字典
        """
        return self.config.get("parser_enable_settings", {})

