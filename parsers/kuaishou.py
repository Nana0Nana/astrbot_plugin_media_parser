# -*- coding: utf-8 -*-
import aiohttp
import asyncio
import re
import json
from urllib.parse import urlparse
from datetime import datetime
from typing import Optional, Dict, Any, List
from .base_parser import BaseVideoParser


MOBILE_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) '
                  'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}


class KuaishouParser(BaseVideoParser):
    """快手视频解析器"""
    
    def __init__(self, max_video_size_mb: float = 0.0):
        super().__init__("快手", max_video_size_mb)
        self.headers = MOBILE_HEADERS
        self.semaphore = asyncio.Semaphore(10)
    
    def can_parse(self, url: str) -> bool:
        """判断是否可以解析此URL"""
        if not url:
            return False
        url_lower = url.lower()
        if 'kuaishou.com' in url_lower or 'kspkg.com' in url_lower:
            return True
        return False
    
    def extract_links(self, text: str) -> List[str]:
        """从文本中提取快手链接"""
        result_links = []
        short_pattern = r'https?://v\.kuaishou\.com/[^\s]+'
        short_links = re.findall(short_pattern, text)
        result_links.extend(short_links)
        
        long_pattern = r'https?://(?:www\.)?kuaishou\.com/[^\s]+'
        long_links = re.findall(long_pattern, text)
        result_links.extend(long_links)
        
        return result_links
    
    def _min_mp4(self, url: str) -> str:
        """处理MP4 URL，提取最小格式"""
        pu = urlparse(url)
        domain = pu.netloc
        filename = pu.path.split('/')[-1].split('?')[0]
        path_wo_file = '/'.join(pu.path.split('/')[1:-1])
        return f"https://{domain}/{path_wo_file}/{filename}"
    
    def _extract_upload_time(self, url: str) -> Optional[str]:
        """从URL中提取上传时间"""
        try:
            match = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
            if match:
                year, month, day = match.groups()
                return f"{year}-{month}-{day}"
            match = re.search(r'_(\d{11,13})_', url)
            if match:
                timestamp = int(match.group(1))
                if len(match.group(1)) == 13:
                    timestamp = timestamp // 1000
                dt = datetime.fromtimestamp(timestamp)
                return dt.strftime('%Y-%m-%d')
        except Exception:
            pass
        return None
    
    def _extract_metadata(self, html: str) -> Dict[str, Optional[str]]:
        """提取用户名、UID、标题"""
        metadata = {'userName': None, 'userId': None, 'caption': None}
        
        json_match = re.search(r'window\.INIT_STATE\s*=\s*({.*?});', html, re.DOTALL)
        if not json_match:
            json_match = re.search(r'window\.__APOLLO_STATE__\s*=\s*({.*?});', html, re.DOTALL)
        
        if json_match:
            try:
                json_str = json_match.group(1)
                
                user_match = re.search(r'"userName"\s*:\s*"([^"]+)"', json_str)
                if user_match:
                    metadata['userName'] = user_match.group(1)
                
                uid_match = re.search(r'"userId"\s*:\s*["\']?(\d+)["\']?', json_str)
                if uid_match:
                    metadata['userId'] = uid_match.group(1)
                
                caption_match = re.search(r'"caption"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', json_str)
                if caption_match:
                    raw_caption = caption_match.group(1)
                    try:
                        test_json = f'{{"text":"{raw_caption}"}}'
                        parsed = json.loads(test_json)
                        metadata['caption'] = parsed['text']
                    except Exception:
                        metadata['caption'] = raw_caption
            except Exception:
                pass
        
        if not metadata['caption']:
            title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE)
            if title_match:
                metadata['caption'] = title_match.group(1).strip()
        
        return metadata
    
    def _extract_album_image_url(self, html: str) -> Optional[str]:
        """提取图集图片URL"""
        match = re.search(r'<img\s+class="image"\s+src="([^"]+)"', html)
        if match:
            return match.group(1).split('?')[0]
        match = re.search(r'src="(https?://[^"]*?/upic/[^"]*?\.jpg)', html)
        if match:
            return match.group(1)
        return None
    
    def _build_album(self, cdn: str, music_path: Optional[str], img_paths: List[str]) -> Dict[str, Any]:
        """构建图集数据"""
        cdn = re.sub(r'https?://', '', cdn)
        cleaned_paths = [p.strip('"') for p in img_paths if p.strip('"')]
        images = [f"https://{cdn}{p}" for p in cleaned_paths]
        seen = set()
        uniq = []
        for u in images:
            if u not in seen:
                uniq.append(u)
                seen.add(u)
        if music_path:
            cleaned_music = music_path.strip('"')
            bgm = f"https://{cdn}{cleaned_music}"
        else:
            bgm = None
        return {'type': 'album', 'bgm': bgm, 'images': uniq}
    
    def _parse_album(self, html: str) -> Optional[Dict[str, Any]]:
        """解析图集"""
        cdn_matches = re.findall(r'"cdnList"\s*:\s*\[.*?"cdn"\s*:\s*"([^"]+)"', html, re.DOTALL)
        if not cdn_matches:
            cdn_matches = re.findall(r'"cdn"\s*:\s*\["([^"]+)"', html)
        if not cdn_matches:
            cdn_matches = re.findall(r'"cdn"\s*:\s*"([^"]+)"', html)
        if not cdn_matches:
            return None
        cdn = cdn_matches[0]
        
        img_paths = re.findall(r'"/ufile/atlas/[^"]+?\.jpg"', html)
        if not img_paths:
            return None
        
        m = re.search(r'"music"\s*:\s*"(/ufile/atlas/[^"]+?\.m4a)"', html)
        music_path = m.group(1) if m else None
        
        return self._build_album(cdn, music_path, img_paths)
    
    def _parse_video(self, html: str) -> Optional[str]:
        """解析视频URL"""
        m = re.search(r'"(url|srcNoMark|photoUrl|videoUrl)"\s*:\s*"(https?://[^"]+?\.mp4[^"]*)"', html)
        if not m:
            m = re.search(r'"url"\s*:\s*"(https?://[^"]+?\.mp4[^"]*)"', html)
        if m:
            return self._min_mp4(m.group(2))
        return None
    
    async def parse(self, session: aiohttp.ClientSession, url: str) -> Optional[Dict[str, Any]]:
        """解析单个快手链接"""
        async with self.semaphore:
            try:
                is_short = 'v.kuaishou.com' in urlparse(url).netloc
                
                if is_short:
                    async with session.get(url, headers=self.headers, allow_redirects=False) as r1:
                        if r1.status != 302:
                            return None
                        loc = r1.headers.get('Location')
                        if not loc:
                            return None
                    async with session.get(loc, headers=self.headers) as r2:
                        if r2.status != 200:
                            return None
                        html = await r2.text()
                else:
                    async with session.get(url, headers=self.headers) as r:
                        if r.status != 200:
                            return None
                        html = await r.text()
                
                metadata = self._extract_metadata(html)
                
                userName = metadata.get('userName', '')
                userId = metadata.get('userId', '')
                
                if userName and userId:
                    author = f"{userName}(uid:{userId})"
                elif userName:
                    author = userName
                elif userId:
                    author = f"(uid:{userId})"
                else:
                    author = ""
                
                title = metadata.get('caption', '') or "快手视频"
                if len(title) > 100:
                    title = title[:100]
                
                video_url = self._parse_video(html)
                if video_url:
                    if not await self.check_video_size(video_url, session):
                        return None
                    upload_time = self._extract_upload_time(video_url)
                    return {
                        "video_url": url,
                        "title": title,
                        "author": author,
                        "timestamp": upload_time or "",
                        "direct_url": video_url
                    }
                
                album = self._parse_album(html)
                if album:
                    image_url = self._extract_album_image_url(html)
                    upload_time = self._extract_upload_time(image_url) if image_url else None
                    return {
                        "video_url": url,
                        "title": title or "快手图集",
                        "author": author,
                        "timestamp": upload_time or "",
                        "images": album['images'],
                        "is_gallery": True
                    }
                
                json_match = re.search(r'<script[^>]*>window\.rawData\s*=\s*({.*?});?</script>', html, re.DOTALL)
                if json_match:
                    try:
                        data = json.loads(json_match.group(1))
                        if 'video' in data:
                            vurl = data['video'].get('url') or data['video'].get('srcNoMark')
                            if vurl and '.mp4' in vurl:
                                video_url = self._min_mp4(vurl)
                                if not await self.check_video_size(video_url, session):
                                    return None
                                upload_time = self._extract_upload_time(video_url)
                                return {
                                    "video_url": url,
                                    "title": title,
                                    "author": author,
                                    "timestamp": upload_time or "",
                                    "direct_url": video_url
                                }
                        elif 'photo' in data and data.get('type') == 1:
                            cdn_raw = data['photo'].get('cdn', ['p3.a.yximgs.com'])
                            cdn = cdn_raw[0] if isinstance(cdn_raw, list) and len(cdn_raw) > 0 else (cdn_raw if isinstance(cdn_raw, str) else 'p3.a.yximgs.com')
                            music = data['photo'].get('music')
                            img_list = data['photo'].get('list', [])
                            album_data = self._build_album(cdn, music, img_list)
                            image_url = self._extract_album_image_url(html)
                            upload_time = self._extract_upload_time(image_url) if image_url else None
                            return {
                                "video_url": url,
                                "title": title or "快手图集",
                                "author": author,
                                "timestamp": upload_time or "",
                                "images": album_data['images'],
                                "is_gallery": True
                            }
                    except json.JSONDecodeError:
                        pass
                
                if metadata.get('userName') or metadata.get('userId') or metadata.get('caption'):
                    return {
                        "video_url": url,
                        "title": title,
                        "author": author,
                        "timestamp": "",
                        "direct_url": None
                    }
                
                return None
            except Exception:
                return None
