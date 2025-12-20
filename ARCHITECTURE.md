# 架构文档

## 一、整体框架

### 1.1 系统概述

本项目是一个流媒体平台链接解析插件，主要功能是自动识别消息中的媒体链接，解析获取媒体元数据和直链，并转换为可发送的媒体消息。

### 1.2 核心模块架构

```
astrbot_plugin_media_parser/
├── main.py                          # 插件主入口
├── run_local.py                     # 本地测试工具脚本
├── core/
│   ├── config_manager.py            # 配置管理器
│   ├── constants.py                 # 常量定义
│   ├── file_cleaner.py              # 文件清理工具
│   ├── parser/                      # 解析器模块
│   │   ├── manager.py               # 解析器管理器
│   │   ├── router.py                # 链接路由分发器
│   │   ├── utils.py                 # 解析器工具函数
│   │   └── platform/                 # 各平台解析器实现
│   │       ├── base.py              # 解析器基类
│   │       ├── bilibili.py          # B站解析器
│   │       ├── douyin.py            # 抖音解析器
│   │       ├── kuaishou.py          # 快手解析器
│   │       ├── weibo.py             # 微博解析器
│   │       ├── xiaohongshu.py       # 小红书解析器
│   │       ├── xiaoheihe.py         # 小黑盒解析器
│   │       └── twitter.py           # 推特解析器
│   ├── downloader/                  # 下载器模块
│   │   ├── manager.py               # 下载管理器
│   │   ├── router.py                # 媒体下载路由
│   │   ├── utils.py                 # 下载器工具函数
│   │   ├── validator.py             # 媒体验证器
│   │   └── handler/                 # 各类型下载处理器
│   │       ├── base.py              # 下载器基类
│   │       ├── image.py             # 图片下载器
│   │       ├── normal_video.py      # 普通视频下载器
│   │       ├── range_video.py       # 分片视频下载器
│   │       └── m3u8.py              # M3U8流媒体下载器
│   └── message_adapter/             # 消息适配器模块
│       ├── manager.py                # 消息管理器
│       ├── node_builder.py          # 节点构建器
│       └── sender.py                # 消息发送器
```

### 1.3 模块职责

#### 1.3.1 主入口模块 (main.py)
- **VideoParserPlugin**: 插件主类
  - 初始化所有管理器
  - 监听消息事件
  - 协调各模块工作流程
  - 处理插件生命周期

#### 1.3.2 配置管理模块 (config_manager.py)
- **ConfigManager**: 配置管理器
  - 解析配置文件
  - 管理解析器启用状态
  - 管理下载配置（缓存目录、预下载模式等）
  - 管理代理配置
  - 创建解析器实例列表

#### 1.3.3 解析器模块 (parser/)
- **ParserManager**: 解析器管理器
  - 管理所有解析器实例
  - 协调链接提取和解析流程
  - 处理解析结果聚合

- **LinkRouter**: 链接路由分发器
  - 从文本中提取所有可解析链接
  - 为每个链接匹配对应的解析器
  - 过滤直播链接和重复链接

- **BaseVideoParser**: 解析器基类
  - 定义解析器接口规范
  - 各平台解析器继承此基类

- **平台解析器** (platform/)
  - 实现各平台特定的链接识别和解析逻辑
  - 提取媒体元数据（标题、作者、视频URL、图片URL等）
  - 处理平台特定的请求头和参数

#### 1.3.4 下载器模块 (downloader/)
- **DownloadManager**: 下载管理器
  - 管理媒体下载流程
  - 处理视频大小验证
  - 管理并发下载
  - 决定使用直链还是本地文件

- **Router**: 媒体下载路由
  - 检测媒体类型（图片/视频/M3U8）
  - 路由到对应的下载处理器

- **下载处理器** (handler/)
  - **Image Handler**: 图片下载器
  - **Normal Video Handler**: 普通视频下载器（完整下载）
  - **Range Video Handler**: 分片视频下载器（支持Range请求）
  - **M3U8 Handler**: M3U8流媒体下载器（支持FFmpeg转换）

- **Validator**: 媒体验证器
  - 验证媒体URL可访问性
  - 获取媒体大小信息
  - 检测访问权限问题

#### 1.3.5 消息适配器模块 (message_adapter/)
- **MessageManager**: 消息管理器
  - 协调节点构建和消息发送
  - 获取发送者信息

- **NodeBuilder**: 节点构建器
  - 构建文本节点（标题、作者、描述等）
  - 构建媒体节点（图片、视频）
  - 处理打包逻辑（大视频单独发送）

- **MessageSender**: 消息发送器
  - 打包模式发送（使用Nodes）
  - 非打包模式发送（独立发送）
  - 处理大媒体单独发送逻辑

#### 1.3.6 工具模块
- **FileCleaner**: 文件清理工具
  - 清理临时文件
  - 清理缓存目录

- **Constants**: 常量定义
  - 超时时间
  - 大小限制
  - 默认配置值

#### 1.3.7 本地测试工具 (run_local.py)
- **run_local.py**: 本地测试工具脚本
  - 提供交互式命令行界面
  - 支持输入链接并解析
  - 支持用户确认后下载媒体
  - 显示解析和下载统计信息
  - 用于本地开发和调试

## 二、程序执行链

### 2.1 完整处理流程

```
消息接收
  ↓
判断是否需要解析 (ConfigManager)
  ├─ 自动解析模式 → 直接解析
  └─ 关键词触发模式 → 检查关键词
  ↓
提取链接 (LinkRouter)
  ├─ 遍历所有解析器
  ├─ 提取匹配的链接
  ├─ 过滤直播链接
  └─ 去重处理
  ↓
解析链接 (ParserManager)
  ├─ 并发调用各平台解析器
  ├─ 获取媒体元数据
  └─ 聚合解析结果
  ↓
处理元数据 (DownloadManager)
  ├─ 检查视频大小限制
  ├─ 验证媒体可访问性
  ├─ 决定下载策略
  │   ├─ 预下载模式 → 批量下载所有媒体
  │   └─ 直链模式 → 图片下载到临时目录，视频使用直链
  └─ 处理强制下载标志
  ↓
构建消息节点 (NodeBuilder)
  ├─ 构建文本节点（元数据信息）
  ├─ 构建媒体节点（图片/视频）
  ├─ 判断大媒体（超过阈值）
  └─ 处理打包逻辑
  ↓
发送消息 (MessageSender)
  ├─ 打包模式
  │   ├─ 普通媒体 → Nodes打包发送
  │   └─ 大媒体 → 单独发送
  └─ 非打包模式 → 逐个独立发送
  ↓
清理临时文件 (FileCleaner)
```

### 2.2 详细程序链

#### 2.2.1 消息接收与判断阶段

```
main.py::VideoParserPlugin.auto_parse()
  ↓
提取消息文本
  ├─ 普通消息 → 直接使用 message_str
  └─ QQ小程序卡片 → 提取 qqdocurl 或 jumpUrl
  ↓
main.py::VideoParserPlugin._should_parse()
  ├─ is_auto_parse = True → 返回 True
  └─ 检查 trigger_keywords → 匹配则返回 True
```

#### 2.2.2 链接提取阶段

```
main.py::VideoParserPlugin.auto_parse()
  ↓
parser::manager::ParserManager.extract_all_links()
  ↓
parser::router::LinkRouter.extract_links_with_parser()
  ├─ 检查 "原始链接：" 标记 → 跳过解析
  ├─ 遍历所有解析器
  │   └─ parser::platform::BaseVideoParser.extract_links()
  ├─ 过滤直播链接 (utils::is_live_url)
  ├─ 按位置排序
  └─ 去重处理
  ↓
返回 (链接, 解析器) 元组列表
```

#### 2.2.3 链接解析阶段

```
main.py::VideoParserPlugin.auto_parse()
  ↓
创建 aiohttp.ClientSession
  ↓
parser::manager::ParserManager.parse_text()
  ├─ 提取唯一链接（去重）
  ├─ 并发调用各解析器
  │   └─ parser::platform::BaseVideoParser.parse()
  │       ├─ 请求平台API
  │       ├─ 解析响应数据
  │       └─ 提取元数据
  └─ 聚合解析结果
  ↓
返回元数据列表
  ├─ url: 原始链接
  ├─ title: 标题
  ├─ author: 作者
  ├─ video_urls: 视频URL列表（二维列表）
  ├─ image_urls: 图片URL列表（二维列表）
  ├─ video_headers: 视频请求头
  ├─ image_headers: 图片请求头
  └─ video_force_download: 是否强制下载
```

#### 2.2.4 元数据处理阶段

```
main.py::VideoParserPlugin.auto_parse()
  ↓
并发处理每个元数据
  ↓
downloader::manager::DownloadManager.process_metadata()
  ├─ 检查视频大小限制
  │   └─ validator::get_video_size()
  │       └─ 如果超过限制 → 返回错误元数据
  │
  ├─ 预下载模式 (effective_pre_download = True)
  │   ├─ 构建媒体项列表
  │   ├─ 批量下载所有媒体
  │   │   └─ downloader::router::download_media()
  │   │       ├─ 检测媒体类型
  │   │       └─ 路由到对应下载器
  │   │           ├─ image → handler::image
  │   │           ├─ video → handler::normal_video
  │   │           ├─ range: → handler::range_video
  │   │           └─ m3u8: → handler::m3u8
  │   ├─ 处理下载结果
  │   └─ 更新元数据（file_paths, video_sizes等）
  │
  └─ 直链模式 (effective_pre_download = False)
      ├─ 处理 video_force_download 标志
      │   └─ 如果为True且未启用预下载 → 跳过视频
      ├─ 检查视频可访问性
      │   └─ validator::get_video_size()
      └─ 下载图片到临时目录
          └─ downloader::manager::DownloadManager._download_images()
  ↓
返回处理后的元数据
```

#### 2.2.5 节点构建阶段

```
main.py::VideoParserPlugin.auto_parse()
  ↓
message_adapter::manager::MessageManager.build_nodes()
  ↓
message_adapter::node_builder::build_all_nodes()
  ├─ 遍历所有元数据
  │   └─ message_adapter::node_builder::build_nodes_for_link()
  │       ├─ 构建文本节点
  │       │   └─ message_adapter::node_builder::build_text_node()
  │       │       ├─ 标题、作者、描述
  │       │       ├─ 视频大小信息
  │       │       ├─ 错误信息
  │       │       └─ 原始链接
  │       │
  │       └─ 构建媒体节点
  │           └─ message_adapter::node_builder::build_media_nodes()
  │               ├─ 判断是否使用本地文件
  │               ├─ 构建视频节点
  │               │   ├─ 本地文件 → Video.fromFileSystem()
  │               │   └─ 直链 → Video.fromURL()
  │               └─ 构建图片节点
  │                   ├─ 本地文件 → Image.fromFileSystem()
  │                   └─ 直链 → Image.fromURL()
  │
  ├─ 判断大媒体（超过 large_video_threshold_mb）
  └─ 分类文件路径（临时文件、视频文件）
  ↓
返回 (all_link_nodes, link_metadata, temp_files, video_files)
```

#### 2.2.6 消息发送阶段

```
main.py::VideoParserPlugin.auto_parse()
  ↓
message_adapter::manager::MessageManager.send_results()
  ↓
判断发送模式
  ├─ 打包模式 (is_auto_pack = True)
  │   └─ message_adapter::sender::MessageSender.send_packed_results()
  │       ├─ 分离普通媒体和大媒体
  │       ├─ 普通媒体打包发送
  │       │   ├─ 纯图片图集 → 文本和图片分组
  │       │   ├─ 混合内容 → 每个节点单独打包
  │       │   └─ 使用 Nodes 发送
  │       └─ 大媒体单独发送
  │           └─ message_adapter::sender::MessageSender.send_large_media_results()
  │               ├─ 发送提示信息
  │               └─ 逐个发送节点
  │
  └─ 非打包模式 (is_auto_pack = False)
      └─ message_adapter::sender::MessageSender.send_unpacked_results()
          ├─ 遍历所有链接节点
          ├─ 纯图片图集 → 文本和图片分组发送
          └─ 其他内容 → 逐个节点独立发送
  ↓
发送完成
```

#### 2.2.7 文件清理阶段

```
main.py::VideoParserPlugin.auto_parse()
  ↓
finally 块
  ↓
file_cleaner::cleanup_files()
  ├─ 清理临时文件（图片）
  └─ 清理视频文件
  ↓
清理完成
```

### 2.3 异常处理链

```
解析阶段异常
  ├─ SkipParse → 跳过该链接
  ├─ 其他异常 → 记录错误，返回错误元数据
  └─ 继续处理其他链接
  ↓
下载阶段异常
  ├─ 单个媒体下载失败 → 记录警告，继续其他媒体
  ├─ 全部媒体下载失败 → 标记 has_valid_media = False
  └─ 继续构建节点（可能只有文本节点）
  ↓
发送阶段异常
  ├─ 单个节点发送失败 → 记录警告，继续发送其他节点
  └─ 确保文件清理执行
```

### 2.4 并发处理链

```
链接解析并发
  ├─ asyncio.gather() 并发调用所有解析器
  └─ 每个解析器独立处理，互不影响
  ↓
元数据处理并发
  ├─ asyncio.gather() 并发处理所有元数据
  └─ 每个元数据独立处理
  ↓
媒体下载并发
  ├─ Semaphore 控制最大并发数
  ├─ 批量下载时并发下载所有媒体项
  └─ 单个媒体失败不影响其他媒体
```

## 三、关键设计模式

### 3.1 管理器模式
- **ParserManager**: 统一管理所有解析器
- **DownloadManager**: 统一管理下载流程
- **MessageManager**: 统一管理消息构建和发送

### 3.2 路由模式
- **LinkRouter**: 根据URL特征路由到对应解析器
- **Download Router**: 根据媒体类型路由到对应下载器

### 3.3 策略模式
- **下载策略**: 预下载模式 vs 直链模式
- **发送策略**: 打包模式 vs 非打包模式

### 3.4 模板方法模式
- **BaseVideoParser**: 定义解析器接口，各平台实现具体逻辑
- **Base Download Handler**: 定义下载器接口，各类型实现具体逻辑

## 四、数据流

### 4.1 元数据流转

```
原始消息文本
  ↓
链接提取 → (链接, 解析器) 列表
  ↓
解析结果 → 元数据字典
  ├─ url
  ├─ title, author, desc
  ├─ video_urls: List[List[str]]
  ├─ image_urls: List[List[str]]
  ├─ video_headers, image_headers
  └─ video_force_download
  ↓
下载处理 → 增强元数据
  ├─ file_paths: List[str]
  ├─ video_sizes: List[float]
  ├─ max_video_size_mb
  ├─ has_valid_media
  ├─ use_local_files
  └─ failed_video_count, failed_image_count
  ↓
节点构建 → 节点列表
  ├─ Plain 节点（文本信息）
  ├─ Image 节点（图片）
  └─ Video 节点（视频）
  ↓
消息发送 → 最终消息
```

### 4.2 文件流转

```
媒体URL
  ↓
下载处理
  ├─ 预下载模式 → 缓存目录
  │   └─ {platform}_{hash}_{timestamp}/media_{index}.{ext}
  └─ 直链模式（仅图片）→ 临时目录
      └─ temp_image_{index}.{ext}
  ↓
节点构建
  ├─ 本地文件 → fromFileSystem()
  └─ 直链 → fromURL()
  ↓
消息发送
  ↓
文件清理 → 删除临时文件
```
