# -*- coding: utf-8 -*-
import os

from astrbot.api import logger
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.core.star.filter.event_message_type import EventMessageType

from .core import ParserManager, ParserFactory, ConfigManager
from .utils import ResourceManager, MessageSender, ResultProcessor


@register(
    "astrbot_plugin_video_parser",
    "drdon1234",
    "聚合解析流媒体平台链接，转换为媒体直链发送",
    "1.1.0"
)
class VideoParserPlugin(Star):

    def __init__(self, context: Context, config: dict):
        """初始化插件。

        Args:
            context: 上下文对象
            config: 配置字典

        Raises:
            ValueError: 当没有启用任何解析器时
        """
        super().__init__(context)
        self.logger = logger
        
        # 使用配置管理器统一管理配置
        self.config_manager = ConfigManager(config)
        self.is_auto_pack = self.config_manager.is_auto_pack
        self.is_auto_parse = self.config_manager.is_auto_parse
        self.trigger_keywords = self.config_manager.trigger_keywords
        self.large_media_threshold_mb = self.config_manager.large_media_threshold_mb
        
        # 检查缓存目录
        cache_dir = self.config_manager.cache_dir
        self.cache_dir_available = self._check_cache_dir_available(cache_dir)
        if self.cache_dir_available:
            os.makedirs(cache_dir, exist_ok=True)
        
        # 使用工厂模式创建解析器（传入ConfigManager实例）
        parsers = ParserFactory.create_parsers(self.config_manager)
        self.parser_manager = ParserManager(parsers)
        
        # 创建消息发送器和结果处理器
        self.message_sender = MessageSender(
            self.logger,
            is_auto_pack=self.is_auto_pack,
            large_media_threshold_mb=self.large_media_threshold_mb
        )
        self.result_processor = ResultProcessor(
            self.logger,
            message_sender=self.message_sender,
            is_auto_pack=self.is_auto_pack
        )

    def _check_cache_dir_available(self, cache_dir: str) -> bool:
        """检查缓存目录是否可用（可写）。

        Args:
            cache_dir: 缓存目录路径

        Returns:
            如果目录可用返回True，否则返回False
        """
        if not cache_dir:
            return False
        try:
            os.makedirs(cache_dir, exist_ok=True)
            test_file = os.path.join(cache_dir, ".test_write")
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.unlink(test_file)
                return True
            except Exception as e:
                self.logger.error(f"检查缓存目录写入权限失败: {e}")
                return False
        except Exception as e:
            self.logger.error(f"检查缓存目录可用性失败: {e}")
            return False

    async def terminate(self):
        """插件终止时的清理工作。"""
        pass

    def _should_parse(self, message_str: str) -> bool:
        """判断是否应该解析消息。

        Args:
            message_str: 消息文本

        Returns:
            如果应该解析返回True，否则返回False
        """
        if self.is_auto_parse:
            return True
        for keyword in self.trigger_keywords:
            if keyword in message_str:
                return True
        return False

    def _cleanup_files(self, file_paths: list):
        """清理文件列表（兼容旧接口，建议使用ResourceManager）。

        Args:
            file_paths: 文件路径列表
        """
        resource_manager = ResourceManager(self.logger)
        resource_manager.register_files(file_paths, is_cache=False)
        resource_manager.cleanup_all()

    def _cleanup_all_files(self, temp_files: list, video_files: list):
        """清理所有临时文件和视频文件（兼容旧接口，建议使用ResourceManager）。

        Args:
            temp_files: 临时文件列表
            video_files: 视频文件列表
        """
        resource_manager = ResourceManager(self.logger)
        resource_manager.register_files(temp_files, is_cache=False)
        resource_manager.register_files(video_files, is_cache=True)
        resource_manager.cleanup_all()

    @filter.event_message_type(EventMessageType.ALL)
    async def auto_parse(self, event: AstrMessageEvent):
        """自动解析消息中的视频链接。

        Args:
            event: 消息事件对象
        """
        if not self._should_parse(event.message_str):
            return
        links_with_parser = self.parser_manager.extract_all_links(
            event.message_str
        )
        if not links_with_parser:
            return
        await event.send(event.plain_result("流媒体解析bot为您服务 ٩( 'ω' )و"))
        sender_name, sender_id = self.result_processor._get_sender_info(event)
        result = await self.parser_manager.build_nodes(
            event,
            self.is_auto_pack,
            sender_name,
            sender_id
        )
        
        # 使用ResourceManager统一管理资源
        with ResourceManager(self.logger) as resource_manager:
            try:
                await self.result_processor.process_and_send(
                    event,
                    result,
                    resource_manager
                )
            except Exception as e:
                self.logger.exception(f"auto_parse方法执行失败: {e}")
                raise
