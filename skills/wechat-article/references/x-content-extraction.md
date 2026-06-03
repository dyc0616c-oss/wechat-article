# X/Twitter 素材提取方法

当用户提供的素材链接来自 X/Twitter（`x.com` 或 `twitter.com`），且浏览器 CDP 不可用时，使用以下方法提取推文内容：

## fxtwitter API（推荐，无需认证）

```bash
# 从 URL 中提取推文 ID
# URL: https://x.com/AYi_AInotes/status/2054256162330096067
# ID: 2054256162330096067

curl -sL 'https://api.fxtwitter.com/{username}/status/{tweet_id}'

# 示例
curl -sL 'https://api.fxtwitter.com/AYi_AInotes/status/2054256162330096067'
```

返回值 JSON 结构：
```json
{
  "tweet": {
    "text": "推文正文内容",
    "author": {"name": "显示名", "screen_name": "用户名"},
    "url": "推文链接",
    "media": {"photos": [{"url": "图片URL"}], "videos": [...]},
    "likes": "点赞数"
  }
}
```

提取纯文本：
```bash
curl -sL 'https://api.fxtwitter.com/{username}/status/{id}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['tweet']['text'])"
```

## vxtwitter 备选

```bash
curl -sL 'https://api.vxtwitter.com/{username}/status/{tweet_id}'
```

返回值 JSON 结构类似 fxtwitter，直接包含顶层 `text` 字段：
```bash
curl -sL 'https://api.vxtwitter.com/dotey/status/2054256272740864294' | python3 -c "import sys,json; print(json.load(sys.stdin)['text'])"
```

## 提取 X 长文（Article）完整内容

当推文只包含一个 `x.com/i/article/{id}` 链接（X 长文），且文章需要登录时，**fxtwitter API 可返回完整的文章正文内容**（含章节标题、加粗、引用、列表等富文本结构），无需任何认证。

### 提取方法

```bash
# fxtwitter 返回的 article.content.blocks 包含完整正文
curl -sL 'https://api.fxtwitter.com/{username}/status/{tweet_id}' | python3 << 'PYEOF'
import sys, json
d = json.load(sys.stdin)
art = d['tweet']['article']
print('标题:', art['title'])
print('预览:', art['preview_text'][:100])
print('配图:', art.get('cover_media', {}))
# 完整正文在 content.blocks 中
blocks = art['content']['blocks']
for b in blocks:
    t = b['type']
    text = b.get('text', '')
    styles = b.get('inlineStyleRanges', [])
    if t == 'header-one':
        print(f"\n## {text}")
    elif t == 'header-two':
        print(f"\n### {text}")
    elif t == 'blockquote':
        print(f"  > {text}")
    elif t == 'unordered-list-item':
        print(f"  - {text}")
    elif text.strip():
        # 处理加粗
        for s in styles:
            if s.get('style') == 'Bold':
                start, end = s['offset'], s['offset'] + s['length']
                text = text[:start] + '**' + text[start:end] + '**' + text[end:]
        print(text)
PYEOF
```

### blocks 字段结构

每个 block 包含：
- `type`：`unstyled`（正文）、`header-one`（一级标题）、`header-two`（二级标题）、`blockquote`（引用）、`unordered-list-item`（无序列表项）、`atomic`（分隔/空行）
- `text`：文本内容
- `inlineStyleRanges`：格式标记数组，每个元素有 `offset`（起始位置）、`length`（长度）、`style`（如 `"Bold"` 加粗）

### vxtwitter 备选（仅预览，无完整正文）

当 fxtwitter 不可用时，vxtwitter 的 `article` 字段可提取标题、预览片段和配图：

```bash
curl -sL 'https://api.vxtwitter.com/{username}/status/{tweet_id}'
```

vxtwitter 返回的 `article` 结构：
```json
{
  "article": {
    "title": "文章标题",
    "preview_text": "开头80-150字预览",
    "image": "配图URL（pbs.twimg.com）"
  }
}
```

### 注意事项

- **⚠️ 关键决策模型：推文正文是文章链接 → 必须用 fxtwitter，不是 vxtwitter**。当推文正文只包含一个 `x.com/i/article/{id}` 链接（X 长文）时，vxtwitter 的 `article` 字段只返回 `title` + `preview_text`（开头80-150字片段），并不返回完整正文。而 **fxtwitter 的 `article.content.blocks` 包含完整正文**。常见错误：先用 vxtwitter 发现只有预览，就以为整篇文章都需要登录才能获取 → 实际上 fxtwitter 可以直接返回全文。

- **操作流程（强制）**：拿到 X 推文后，先检查 `text` 字段是否指向 `x.com/i/article/`。如果是，直接上 fxtwitter 并读取 `article.content.blocks`，不要走 vxtwitter 路径，也不要先试 browser_navigate（X 文章页面有登录墙）。

- **优先使用 fxtwitter**：只有 fxtwitter 能返回完整正文内容（`article.content.blocks`），vxtwitter 仅返回预览片段

### 降级方案：当 fxtwitter 也无法返回完整正文时

在极少数情况下，fxtwitter 的 `article` 字段也只包含 `title` + `preview_text`（无 `content.blocks`），说明该文章在 API 层面也是登录受限的。此时：

**操作流程：**
1. 告知用户 X 文章需要登录才能获取完整内容
2. 以 `background=true` 启动一个 **有界面（visible）** Chrome 窗口（必须去掉 `--headless`，否则用户看不到窗口）
3. 用户在可见的 Chrome 窗口中登录 X
4. 登录后，用 browser_navigate 打开文章 URL 读取内容

**启动有界面 Chrome 的命令（必须在 background 中启动）：**
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-x-profile \
  --no-first-run \
  --no-default-browser-check \
  --new-window "https://x.com/..." &
```

**关键点：**
- 必须在 background 中启动（terminal with background=true），不能用 foreground + &
- 杀掉已有的 headless Chrome 实例后再启动可见版（否则端口冲突）
- 用户登录后，直接用 browser_navigate 访问文章 URL，可正常读取
- 登录后的 session 在同一 user-data-dir 中持续有效，后续多个 X 页面都不需要重新登录

**常见错误：** 用户说"我给你登陆"时，Chrome 以 headless 模式运行 → 用户看不到窗口 → 无法登录 → 陷入死循环。正确做法：杀掉 headless 实例，重新用可见模式启动。
- 提取到的文章正文可以直接作为写作素材使用，但**正文中不得暴露"原帖说""某篇文章里讲到"等素材痕迹**
- 文章配图可通过 `art['cover_media']` 获取，通常是 `pbs.twimg.com` 的图片 URL
- 文章的长文 ID 可从推文 JSON 中获取：`d['tweet']['article']['id']`
- 首次调用 fxtwitter 时可能返回非 JSON（浏览器页面），重试一次即可。不要因此放弃使用 fxtwitter 转而去用 vxtwitter

## 安全调研 / 链小智专用：币圈安全事件数据源

当撰写钱包安全/黑客攻击/资产损失类文章（常见于 链小智 style-a）时，以下 X 账号的 vxtwitter 数据可直接作为可信素材来源：

| 账号 | 用途 | 示例数据 |
|------|------|---------|
| @WuBlockchain | 行业黑客事件月度/季度汇总 | 1月16起攻击，损失$8600万 |
| @BSCNews | Web3 行业损失报告转载 | Q1 2026 $4.64亿损失 |
| @mementoresearch | DeFi/协议级黑客分析 | 4月单月$6.23亿被黑 |
| @TrustWallet | 钱包安全事件官方通报 | v2.68扩展被黑$700万，全额赔付 |
| @k1rallik | 大型安全事故故事性报道 | 少年电话骗$2.63亿，FBI起诉 |

**获取方式：** 用 `execute_code` 批量获取上述账号的最新推文，30秒完成素材搜集：
```python
import subprocess, json
accounts = [
    "WuBlockchain/status/2017959711501406586",
    # ... 替换为具体推文ID
]
for a in accounts:
    r = subprocess.run(['curl','-sL',f'https://api.vxtwitter.com/{a}'], capture_output=True, text=True, timeout=8)
    data = json.loads(r.stdout)
    print(f'{data[\"user_name\"]}: {data.get(\"text\",\"\")[:200]}')
```

## 媒体附件直链提取（syndication API，视频专用）

当推文包含视频且需要**直接下载源文件**用于配图或素材分析时，使用 Twitter 官方的 syndication API。它比 fxtwitter/vxtwitter 更强的地方在于返回**视频的完整 mp4 直链**（多个分辨率可选），且完全无需认证。

```bash
curl -sL "https://cdn.syndication.twimg.com/tweet-result?id={tweet_id}&lang=en&token=2" \
  -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
```

返回值 JSON 中的媒体字段结构：

| 字段 | 内容 |
|------|------|
| `mediaDetails[].type` | `photo`（图片）或 `video`（视频） |
| `mediaDetails[].media_url_https` | 图片/视频封面 URL（`pbs.twimg.com`） |
| `mediaDetails[].video_info.variants[]` | 视频源文件数组，包含 `bitrate` 和 `url` |

### 提取视频 mp4 直链

```python
import json, subprocess
r = subprocess.run(['curl', '-sL',
    'https://cdn.syndication.twimg.com/tweet-result?id=2058521536869650539&lang=en&token=2',
    '-H', 'User-Agent: Mozilla/5.0'], capture_output=True, text=True, timeout=10)
data = json.loads(r.stdout)
for m in data['mediaDetails']:
    if m['type'] == 'video':
        for v in m['video_info']['variants']:
            if v['content_type'] == 'video/mp4':
                print(f"{v['bitrate']}bps → {v['url']}")
```

### 下载视频 + 提取帧作为配图

当推文视频是唯一素材，且文章配图不足时，可用此工作流将视频帧转为文章配图：

```bash
# 1. 下载最高画质的 mp4（2176000bps = 720p）
curl -sL "https://video.twimg.com/amplify_video/{id}/vid/avc1/1280x720/{hash}.mp4" \
  -o /tmp/tweet_video.mp4

# 2. 提取帧（不同时间戳获取不同画面）
ffmpeg -y -ss 5 -i /tmp/tweet_video.mp4 -vf "scale=800:-1" -vframes 1 -update 1 图片/section1.jpg
ffmpeg -y -ss 20 -i /tmp/tweet_video.mp4 -vf "scale=800:-1" -vframes 1 -update 1 图片/section2.jpg
ffmpeg -y -ss 40 -i /tmp/tweet_video.mp4 -vf "scale=800:-1" -vframes 1 -update 1 图片/section3.jpg
```

**注意事项：**
- ℹ️ 视频封面图（`mediaDetails[].media_url_https`）本质是视频某一帧的截图，不要把它当图片用——同一画面出现在封面和正文会让读者觉得重复
- ℹ️ 提取的帧因压缩可能导致画面不够清晰，但作为配图（800px宽）足够使用
- 📍 优先用作小标题正上方的配图，封面图建议找其他来源的独立图（如产品官网图、Unsplash 相关场景图）

## 方法对比

| 方法 | 认证要求 | 可靠性 | 媒体类型 | 备注 |
|------|---------|--------|---------|------|
| fxtwitter | 无 | 高 | 图片 | 推荐首选，返回结构化 JSON |
| vxtwitter | 无 | 高 | 图片 | 备选，格式略有不同 |
| **syndication API** | **无** | **高** | **图片+视频mp4直链** | **唯一能获取视频源文件的免认证途径** |
| xurl CLI | OAuth 2.0 | 高 | 图片+视频 | 需要先安装配置 |
| x-cli | API Key 5件套 | 中 | 图片+视频 | 配置繁琐，依赖付费 API 额度 |
| browser | CDP | 中 | 图片+视频 | 需要本地 Chrome 运行 |

## 注意事项

- 推文内容提取后，**正文中不得暴露"原帖说""某条推文里讲到"等素材痕迹**（遵守 style 通用规则）
- 提取到的数据（点赞数、转发数等）可作为文章佐证使用，但不要编造数字
- 如果推文有图片/视频，可从 `media.photos` 或 `media.videos` 中提取 URL 作为配图来源（注意检查是否含水印）
- fxtwitter API 无速率限制记录，但建议单次任务不超过 10 次请求

## 常见坑点（2026-05-22 实战教训）

### 忽略 article.title 导致文章类型判断错误

**错误模式：** 推文链接了一篇标题为"DeepSeek V4 + Claude Code新手配置教程"的 X 长文（`article.title`），但只看推文中附带的预览文本提到了评测数据（`preview_text`），就写了篇分析稿而非教程。

**根因：** vxtwitter/fxtwitter 返回的 `article` 对象包含 `title`、`preview_text`、`image` 三个字段。`preview_text` 是文章开头摘要，不反映全文类型。**只有 `title` 字段才能准确判断内容类型。**

**修复规则（强制）：**
- 当 vxtwitter/fxtwitter 返回的 JSON 中包含 `article` 对象时，**先读取 `article.title`** 判断内容类型（教程/分析/新闻/观点）
- 标题含"教程/tutorial/指南/guide/setup/配置/入门/How to"等词 → 按**教程/How-to型**结构写稿，引子1-2段后直接进步骤
- 标题含"评测/测评/对比/analysis/benchmark"等词 → 按**测评对比型**结构写稿，数据表+分析为主
- 标题为纯新闻标题 → 按**热点事件型**结构写稿
- 不要仅凭 `preview_text`（开头摘要）判断文章类型。评测数据出现在教程开头非常正常，不代表全文是分析稿

**检查流程：**
```bash
# 提取推文后，先打印 article.title
curl -sL 'https://api.vxtwitter.com/{user}/status/{id}' | python3 -c "
import sys,json; d=json.load(sys.stdin)
art = d.get('article')
if art: print('TITLE:', art.get('title'))
"