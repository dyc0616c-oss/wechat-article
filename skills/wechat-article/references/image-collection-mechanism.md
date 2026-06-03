# 配图获取机制说明（2026-05-15 用户询问后整理）

## 完整优先级链路

按顺序执行，不得跳过任意一级：

### 第-1优先级：X/Twitter 推文视频截帧

当 X/Twitter 源素材只有视频（无配图）时，优先从视频中提取一帧作为封面图：

```bash
# 先下载视频
curl -sL 'VIDEO_URL' -o /tmp/temp_video.mp4 --max-time 30
# 提取第3秒一帧
ffmpeg -i /tmp/temp_video.mp4 -ss 00:00:03 -vframes 1 -q:v 2 图片/封面_主题.jpg -y 2>/dev/null
```

视频 URL 可通过 vxtwitter API 的 `mediaURLs[0]` 获取（通常是 `.mp4` 链接）。  
提取前用 `ls` 确认视频下载成功（>100KB），提取后用 `ls` 确认图片生成成功。  
视频帧通常是 16:9 横屏，用作公众号封面图比例合适，可配合上下留白。

### 第0优先级：X/Twitter 推文媒体附件
用户素材为 X/Twitter 链接时，通过 vxtwitter API 提取 `mediaURLs` 直接下载。
```bash
curl -s 'https://api.vxtwitter.com/{user}/status/{id}' | python3 -c "import json,sys;d=json.load(sys.stdin);[print(m['url']) for m in d.get('media_extended',[])]"
```
推文配图与内容直接相关、无水印，是最佳来源。

### 第1优先级：原文页面直接提取
- 公众号文章：curl 提取 `data-src` / `data-croporisrc`
- 新闻页面：curl 提取 `og:image` 
- 降级：browser_navigate 打开页面 → browser_console 执行 `document.querySelectorAll(...)`

### 第2优先级：archive.org 缓存提取
`curl -sL 'https://web.archive.org/web/2026/https://目标URL'`
多数中文站点的反爬无法拦截 archive.org，缓存页面中通常保留原文配图 CDN URL。

### 第3优先级：Unsplash/Pexels 免费图库
当以上均无合适图片时：
```bash
curl -sL 'https://images.unsplash.com/photo-{ID}?auto=format&fit=crop&w=1200&q=80' -o 图片/{name}.jpg
```
优先选与文章场景直接相关的图片，不用无关氛围图。

### 第4优先级：PIL 裁剪复用（所有外部来源均失败时的最后手段）

当所有外部图片源均无法获取足够图片时——CDN 超时、站点不可达、仅 1-2 张图片可用——使用 Python PIL 将一张大图裁剪为多张视觉上独立的子图：

```python
from PIL import Image
img = Image.open('大图.jpg')
w, h = img.size
top = img.crop((0, 0, w, h//2)).save('sec1.jpg', quality=85)
bottom = img.crop((0, h//2, w, h)).save('sec2.jpg', quality=85)
```

条件：源图 ≥1200px 宽/高，裁剪后各子图仍有足够分辨率且视觉内容明显不同。
裁剪后文件名不同，满足「每张图URL/文件名不同」的规则。
此方案是最后手段，不得主动优先使用。

### 禁止行为
- ❌ 使用 AI 生成图片
- ❌ 引用外链图片（必须下载到本地 图片/ 文件夹）
- ❌ 图片带有来源媒体 logo/水印
- ❌ 封面图与首节配图使用同一张图

## 配图数量规则

- 全篇 = 封面图1张 + 每节1张（小标题数）
- 封面图放在标题摘要下方、正文首段上方
- 每节图放在小标题正上方（图 → 小标题 → 正文）
- 缺图时不插入占位符，跳过即可
