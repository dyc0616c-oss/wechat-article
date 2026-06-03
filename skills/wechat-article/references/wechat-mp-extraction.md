# 微信公众号文章抓取

抓取微信公众号文章内容的标准两步法。

## 为什么需要两步

微信公众号文章正文是 JS 动态渲染的，单纯 `curl` 只能拿到一堆 `<script>` 标签和元数据，拿不到正文。

## 第一步：curl 拿元数据（快，不需要浏览器）

```bash
curl -sL \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  "https://mp.weixin.qq.com/s/ARTICLE_ID" \
  | grep -E '(var msg_title|var msg_desc|var nickname|var msg_cdn_url|var msg_link)'
```

能拿到：
- `var nickname` → 公众号名称
- `var msg_title` → 文章标题
- `var msg_desc` → 文章简介
- `var msg_cdn_url` → 封面图 CDN 地址
- `var msg_link` → 文章永久链接

> 如果只需要标题和公众号名做映射匹配，第一步就够了，不用上浏览器。

## 第二步：browser_navigate 拿正文（需要浏览器）

```json
{
  "url": "https://mp.weixin.qq.com/s/ARTICLE_ID"
}
```

浏览器渲染后返回无障碍树快照，结构化的标题、段落、链接全部拆好。

## 实用技巧

- **只做元数据匹配**：如果只是想确认"这篇文章是哪个号发的"，curl 就够了
- **需要正文时**：直接上 browser_navigate，不需要先 curl
- **批量抓取**：先用 curl 批量拿元数据，再对目标文章精准上浏览器

## 第三步：浏览器不可用时的 curl 正文提取（备选方案）

当 browser 工具不可用（CDP 连接失败等）时，仍然可以从 curl 拿到的原始 HTML 中提取文章正文。

### 方法

```bash
# 1. 先保存原始 HTML
curl -sL -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  "https://mp.weixin.qq.com/s/ARTICLE_ID" -o /tmp/wechat_article.html

# 2. 用 Python 提取 js_content 中的文本内容
python3 -c "
import re
with open('/tmp/wechat_article.html','r',encoding='utf-8',errors='ignore') as f:
    html = f.read()

# 提取元数据
title_m = re.search(r\"msg_title\s*=\s*'(.+?)'\.html\", html)
desc_m = re.search(r\"msg_desc\s*=\s*'(.+?)'\.html\", html)
nickname_m = re.search(r\"nickname\s*=\s*'(.+?)'\.html\", html)

if title_m: print('标题:', title_m.group(1))
if desc_m: print('摘要:', desc_m.group(1))
if nickname_m: print('公众号:', nickname_m.group(1))

# 提取正文（从 js_content div 中提取）
content_m = re.search(r'id=\"js_content\"[^>]*>(.*?)</div>\s*<script', html, re.DOTALL)
if not content_m:
    content_m = re.search(r'rich_media_content[^>]*>(.*?)</div>\s*<', html, re.DOTALL)

if content_m:
    raw = content_m.group(1)
    raw = re.sub(r'<script[^>]*>.*?</script>', '', raw, flags=re.DOTALL)
    raw = re.sub(r'<style[^>]*>.*?</style>', '', raw, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '\n', raw)
    text = re.sub(r'&nbsp;|&lt;|&gt;|&amp;|&quot;', ' ', text)
    
    lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 8]
    for l in lines[:30]:
        print(l)
else:
    print('[内容未提取到 - 页面结构可能已变化]')
"
```

### 原理
微信文章的正文内容由 JS 动态渲染后才可见，但原始 HTML 中 `id="js_content"` 的 div 里已经包含了带 HTML 标签的正文文本（被隐藏）。直接从 raw HTML 提取并去除标签后，可以获得可读的正文内容。

### 注意事项
- 这个方法拿到的文本会保留 HTML 实体和部分残留标签，需要正则清理
- 正文结构（分段、换行）需要二次整理
- 图片 `data-src` 属性无法通过此方法提取（JS 渲染后才赋值）
- 正文完整性取决于微信的页面版本，部分文章可能因 JS 加载而不可见
- 这仍是备选方案：能覆盖大部分情况，但不如 browser 渲染准确

## 从正文内容识别账号风格

拿到正文后，可以用于：
- 判断文章风格类型（犀利/稳健/故事/教程）
- 提取高频词汇和句式
- 作为风格学习样本
- 匹配现有 style 映射表中的账号
