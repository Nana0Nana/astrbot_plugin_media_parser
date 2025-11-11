# -*- coding: utf-8 -*-
"""结果处理器，负责处理解析结果并组织消息节点。"""
from typing import Any, Optional, Tuple

from astrbot.api.event import AstrMessageEvent

from .message_sender import MessageSender
from .resource_manager import ResourceManager


class ResultProcessor:
    """结果处理器类。
    
    负责处理解析结果，组织消息节点，并协调消息发送和资源清理。
    """
    
    def __init__(
        self,
        logger,
        message_sender: MessageSender,
        is_auto_pack: bool = True
    ):
        """初始化结果处理器。
        
        Args:
            logger: 日志记录器
            message_sender: 消息发送器实例
            is_auto_pack: 是否自动打包
        """
        self.logger = logger
        self.message_sender = message_sender
        self.is_auto_pack = is_auto_pack
    
    def _get_sender_info(self, event: AstrMessageEvent) -> Tuple[str, Any]:
        """获取发送者信息。
        
        Args:
            event: 消息事件对象
            
        Returns:
            包含发送者名称和ID的元组 (sender_name, sender_id)
        """
        sender_name = "视频解析bot"
        platform = event.get_platform_name()
        sender_id = event.get_self_id()
        if platform not in ("wechatpadpro", "webchat", "gewechat"):
            try:
                sender_id = int(sender_id)
            except (ValueError, TypeError):
                sender_id = 10000
        return sender_name, sender_id
    
    async def process_and_send(
        self,
        event: AstrMessageEvent,
        parse_result: Optional[Tuple],
        resource_manager: Optional[ResourceManager] = None
    ):
        """处理解析结果并发送消息。
        
        Args:
            event: 消息事件对象
            parse_result: 解析结果元组，格式为：
                (all_link_nodes, link_metadata, temp_files, video_files, normal_link_count)
                如果为None，则不发送任何消息
            resource_manager: 资源管理器（可选）
        """
        if parse_result is None:
            return
        
        all_link_nodes, link_metadata, temp_files, video_files, \
            normal_link_count = parse_result
        
        # 注册资源
        if resource_manager:
            resource_manager.register_files(temp_files, is_cache=False)
            resource_manager.register_files(video_files, is_cache=True)
        
        try:
            sender_name, sender_id = self._get_sender_info(event)
            
            if self.is_auto_pack:
                await self.message_sender.send_packed_results(
                    event,
                    link_metadata,
                    sender_name,
                    sender_id,
                    resource_manager
                )
            else:
                await self.message_sender.send_unpacked_results(
                    event,
                    all_link_nodes,
                    link_metadata,
                    resource_manager
                )
        except Exception as e:
            self.logger.exception(f"处理并发送结果失败: {e}")
            raise

