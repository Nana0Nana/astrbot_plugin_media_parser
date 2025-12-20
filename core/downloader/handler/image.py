import os
import tempfile
from typing import Optional

import aiohttp

try:
    from astrbot.api import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from ..utils import generate_cache_file_path, get_image_suffix
from .base import download_media_from_url


async def download_image_to_cache(
    session: aiohttp.ClientSession,
    image_url: str,
    cache_dir: str,
    media_id: str,
    index: int = 0,
    headers: dict = None,
    proxy: str = None
) -> Optional[str]:
    """下载图片到缓存目录或临时文件

    Args:
        session: aiohttp会话
        image_url: 图片URL
        cache_dir: 缓存目录（如果提供则下载到缓存目录，否则下载到临时文件）
        media_id: 媒体ID（用于生成缓存文件名）
        index: 图片索引
        headers: 请求头字典
        proxy: 代理地址（可选）

    Returns:
        文件路径，失败时为None
    """
    if cache_dir and media_id:
        def file_path_generator(content_type: str, url: str) -> str:
            """生成缓存文件路径"""
            return generate_cache_file_path(
                cache_dir=cache_dir,
                media_id=media_id,
                media_type='image',
                index=index,
                content_type=content_type,
                url=url
            )
        
        file_path, _ = await download_media_from_url(
            session=session,
            media_url=image_url,
            file_path_generator=file_path_generator,
            is_video=False,
            headers=headers,
            proxy=proxy
        )
    else:
        def generate_temp_file_path(content_type: str, url: str) -> str:
            """生成临时文件路径"""
            suffix = get_image_suffix(content_type, url)
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix
            ) as temp_file:
                return os.path.normpath(temp_file.name)
        
        file_path, _ = await download_media_from_url(
            session=session,
            media_url=image_url,
            file_path_generator=generate_temp_file_path,
            is_video=False,
            headers=headers,
            proxy=proxy
        )
    
    return file_path

