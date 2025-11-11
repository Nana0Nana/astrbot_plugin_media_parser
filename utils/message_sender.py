# -*- coding: utf-8 -*-
"""消息发送器，负责发送解析结果。"""
import os
from typing import List, Any, Optional

from astrbot.api.event import AstrMessageEvent
from astrbot.api.message_components import Nodes, Plain, Image, Video, Node

from ..core.constants import LINK_SEPARATOR
from .resource_manager import ResourceManager


class MessageSender:
    """消息发送器类。
    
    负责将解析结果发送到消息平台，包括打包和非打包两种模式。
    """
    
    def __init__(
        self,
        logger,
        is_auto_pack: bool = True,
        large_media_threshold_mb: float = 0.0
    ):
        """初始化消息发送器。
        
        Args:
            logger: 日志记录器
            is_auto_pack: 是否自动打包
            large_media_threshold_mb: 大媒体阈值（MB）
        """
        self.logger = logger
        self.is_auto_pack = is_auto_pack
        self.large_media_threshold_mb = large_media_threshold_mb
    
    def _is_pure_image_gallery(self, nodes: List) -> bool:
        """判断节点列表是否是纯图片图集。
        
        Args:
            nodes: 节点列表
            
        Returns:
            如果是纯图片图集返回True，否则返回False
        """
        has_video = False
        has_image = False
        for node in nodes:
            if isinstance(node, Video):
                has_video = True
                break
            elif isinstance(node, Image):
                has_image = True
        return has_image and not has_video
    
    async def send_packed_results(
        self,
        event: AstrMessageEvent,
        link_metadata: List[dict],
        sender_name: str,
        sender_id: Any,
        resource_manager: Optional[ResourceManager] = None
    ):
        """发送打包的结果（使用Nodes）。
        
        Args:
            event: 消息事件对象
            link_metadata: 链接元数据列表
            sender_name: 发送者名称
            sender_id: 发送者ID
            resource_manager: 资源管理器（可选）
        """
        normal_metadata = [
            meta for meta in link_metadata if meta.get('is_normal', False)
        ]
        large_video_metadata = [
            meta for meta in link_metadata if meta.get('is_large_video', False)
        ]
        normal_link_nodes = [
            meta.get('link_nodes', []) for meta in normal_metadata
        ]
        large_video_link_nodes = [
            meta.get('link_nodes', []) for meta in large_video_metadata
        ]
        separator = LINK_SEPARATOR

        if normal_link_nodes:
            flat_nodes = []
            normal_video_files_to_cleanup = []
            for link_idx, link_nodes in enumerate(normal_link_nodes):
                if link_idx < len(normal_metadata):
                    link_video_files = normal_metadata[link_idx].get(
                        'video_files',
                        []
                    )
                    if link_video_files:
                        normal_video_files_to_cleanup.extend(
                            link_video_files
                        )
                if self._is_pure_image_gallery(link_nodes):
                    texts = [
                        node for node in link_nodes
                        if isinstance(node, Plain)
                    ]
                    images = [
                        node for node in link_nodes
                        if isinstance(node, Image)
                    ]
                    for text in texts:
                        flat_nodes.append(Node(
                            name=sender_name,
                            uin=sender_id,
                            content=[text]
                        ))
                    if images:
                        flat_nodes.append(Node(
                            name=sender_name,
                            uin=sender_id,
                            content=images
                        ))
                else:
                    for node in link_nodes:
                        if node is not None:
                            flat_nodes.append(Node(
                                name=sender_name,
                                uin=sender_id,
                                content=[node]
                            ))
                if link_idx < len(normal_link_nodes) - 1:
                    flat_nodes.append(Node(
                        name=sender_name,
                        uin=sender_id,
                        content=[Plain(separator)]
                    ))
            if flat_nodes:
                try:
                    await event.send(event.chain_result([Nodes(flat_nodes)]))
                finally:
                    # 立即清理已发送的视频文件
                    if normal_video_files_to_cleanup and resource_manager:
                        resource_manager.register_files(
                            normal_video_files_to_cleanup,
                            is_cache=True
                        )
                        resource_manager.cleanup_cache_files()
                    elif normal_video_files_to_cleanup:
                        # 如果没有资源管理器，使用简单清理
                        self._simple_cleanup(normal_video_files_to_cleanup)

        if large_video_link_nodes:
            await self.send_large_media_results(
                event,
                large_video_metadata,
                large_video_link_nodes,
                sender_name,
                sender_id,
                resource_manager
            )
    
    async def send_large_media_results(
        self,
        event: AstrMessageEvent,
        metadata: List[dict],
        link_nodes_list: List[List],
        sender_name: str,
        sender_id: Any,
        resource_manager: Optional[ResourceManager] = None
    ):
        """发送大媒体结果（单独发送）。
        
        Args:
            event: 消息事件对象
            metadata: 元数据列表
            link_nodes_list: 链接节点列表
            sender_name: 发送者名称
            sender_id: 发送者ID
            resource_manager: 资源管理器（可选）
        """
        separator = LINK_SEPARATOR
        threshold_mb = (
            int(self.large_media_threshold_mb)
            if self.large_media_threshold_mb > 0
            else 50
        )
        notice_text = (
            f"⚠️ 链接中包含超过{threshold_mb}MB的媒体时"
            f"将单独发送所有媒体"
        )
        await event.send(event.plain_result(notice_text))
        for link_idx, link_nodes in enumerate(link_nodes_list):
            link_video_files = []
            if link_idx < len(metadata):
                link_video_files = metadata[link_idx].get('video_files', [])
            try:
                for node in link_nodes:
                    if node is not None:
                        try:
                            await event.send(event.chain_result([node]))
                        except Exception as e:
                            self.logger.warning(f"发送大媒体节点失败: {e}")
            finally:
                # 立即清理已发送的视频文件
                if link_video_files and resource_manager:
                    resource_manager.register_files(
                        link_video_files,
                        is_cache=True
                    )
                    resource_manager.cleanup_cache_files()
                elif link_video_files:
                    self._simple_cleanup(link_video_files)
            if link_idx < len(link_nodes_list) - 1:
                await event.send(event.plain_result(separator))
    
    async def send_unpacked_results(
        self,
        event: AstrMessageEvent,
        all_link_nodes: List[List],
        link_metadata: List[dict],
        resource_manager: Optional[ResourceManager] = None
    ):
        """发送非打包的结果（独立发送）。
        
        Args:
            event: 消息事件对象
            all_link_nodes: 所有链接节点列表
            link_metadata: 链接元数据列表
            resource_manager: 资源管理器（可选）
        """
        separator = LINK_SEPARATOR
        for link_idx, (link_nodes, metadata) in enumerate(
            zip(all_link_nodes, link_metadata)
        ):
            link_video_files = metadata.get('video_files', [])
            try:
                if self._is_pure_image_gallery(link_nodes):
                    texts = [
                        node for node in link_nodes
                        if isinstance(node, Plain)
                    ]
                    images = [
                        node for node in link_nodes
                        if isinstance(node, Image)
                    ]
                    for text in texts:
                        await event.send(event.chain_result([text]))
                    if images:
                        await event.send(event.chain_result(images))
                else:
                    for node in link_nodes:
                        if node is not None:
                            try:
                                await event.send(event.chain_result([node]))
                            except Exception as e:
                                self.logger.warning(f"发送节点失败: {e}")
            finally:
                # 立即清理已发送的视频文件
                if link_video_files and resource_manager:
                    resource_manager.register_files(
                        link_video_files,
                        is_cache=True
                    )
                    resource_manager.cleanup_cache_files()
                elif link_video_files:
                    self._simple_cleanup(link_video_files)
            if link_idx < len(all_link_nodes) - 1:
                await event.send(event.plain_result(separator))
    
    def _simple_cleanup(self, file_paths: List[str]):
        """简单清理文件列表（不使用ResourceManager时）。
        
        Args:
            file_paths: 文件路径列表
        """
        for file_path in file_paths:
            if file_path and os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                except Exception:
                    pass

