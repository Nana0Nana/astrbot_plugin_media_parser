# AstrBot 插件 | 视频链接直链解析器

自动识别聊天中的视频或图片链接，并解析为直链发送；支持多消息平台与多流媒体平台，开箱即用、稳定可靠。

> 适配 AstrBot 的插件，自动识别视频链接并转换为直链发送

---

## 目录

- 功能特性
- 支持平台
- 安装
  - 依赖库安装
  - 插件安装
- 使用
  - 自动解析
  - 手动解析
  - 自动打包
  - 批量解析
- 配置建议
- 使用建议
- 已知问题
- 鸣谢

---

## 功能特性

- 自动识别会话中的视频或图片链接，并解析成直链发送  
- 支持多平台并行解析与批量处理  
- 提供消息打包为集合的返回方式（可配置开关）  

---

## 支持平台

### 消息平台

<table border="1" cellpadding="5" cellspacing="0">
<thead>
<tr>
<th>消息平台</th>
<th>支持状态</th>
</tr>
</thead>
<tbody>
<tr>
<td>QQ</td>
<td>✅ 支持</td>
</tr>
<tr>
<td>微信</td>
<td>✅ 支持</td>
</tr>
</tbody>
</table>

### 流媒体平台

<table border="1" cellpadding="5" cellspacing="0">
<thead>
<tr>
<th>流媒体平台</th>
<th>可解析的媒体类型</th>
</tr>
</thead>
<tbody>
<tr>
<td>B站</td>
<td>视频（UGC/PGC）</td>
</tr>
<tr>
<td>抖音</td>
<td>视频、图片集</td>
</tr>
<tr>
<td>Twitter/X</td>
<td>视频、图片集</td>
</tr>
<tr>
<td>快手</td>
<td>视频</td>
</tr>
</tbody>
</table>

---

## 安装

### 依赖库安装（重要）

使用前请先安装依赖库：`aiohttp`

- 打开 “AstrBot WebUI” -> “控制台” -> “安装 Pip 库”  
- 在库名栏输入 `aiohttp` 并点击安装  

### 插件安装

1) 通过 插件市场 安装  
- 打开 “AstrBot WebUI” -> “插件市场” -> “右上角 Search”  
- 搜索与本项目相关的关键词，找到插件后点击安装  
- 推荐通过唯一标识符搜索：`astrbot_plugin_video_parser`  

2) 通过 GitHub 仓库链接 安装  
- 打开 “AstrBot WebUI” -> “插件市场” -> “右下角 ‘+’ 按钮”  
- 输入以下地址并点击安装：  
  https://github.com/drdon1234/astrbot_plugin_video_parser

---

## 使用

### 自动解析
- 当需要自动解析聊天中出现的视频链接时，开启自动解析功能  

### 手动解析
- 当自动解析关闭时，可通过自定义关键词手动触发（在 WebUI 的插件配置中设置）  

### 自动打包
- 开启时：所有解析结果将以一个“消息集合”的形式返回  
- 关闭时：解析结果将逐条依次返回  
- 在微信平台使用时需要禁用此项  

### 批量解析
- 机器人会依次解析所有识别到的链接  
- 支持同时解析多个平台的链接  
- 当自动打包功能开启时，超过“大视频阈值”的视频将单独发送，不包含在转发消息集合中  

---

## 配置建议

- 如需解析 Twitter 视频或处理超过阈值的大视频，请务必配置有效的“视频缓存目录”  
- 在墙内解析 Twitter 视频时，必须启用 Twitter 解析代理，并配置有效的代理地址  

---

## 使用建议

- 在 “AstrBot WebUI” 中开启 “回复时引用消息” 功能，便于溯源  
- 控制批量解析的链接数量，一次过多会导致消息集合在平台上的发送速度变慢  
- 如需在任何 wechat 平台使用，请在 “插件管理” 中禁用 “是否将解析结果打包为消息集合”  
- 建议将 `large_video_threshold_mb` 设置为 50MB 以下，以避免消息适配器的限制  
- 如果遇到 Twitter 解析失败，可尝试配置代理设置  

---

## 已知问题

- 微信无法正确推送视频消息（疑似消息平台问题）  

---

## 鸣谢

- 抖音解析方法参考自：CSDN 博客文章  
  https://blog.csdn.net/qq_53153535/article/details/141297614
- B站解析端点参考自：GitHub 项目 bilibili-API-collect  
  https://github.com/SocialSisterYi/bilibili-API-collect
- 推特解析使用免费第三方服务：fxtwitter（GitHub 项目 FxEmbed）  
  https://github.com/FxEmbed/FxEmbed
