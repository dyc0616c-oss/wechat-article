# 绕过反爬抓取中文科技媒体文章

部分中文科技/区块链媒体（如 techflowpost.com、深潮TechFlow）使用 Alibaba Cloud ESA / acw_tc cookie 挑战等强反爬保护，curl 无法直接获取正文内容。

## 方案一：web.archive.org（推荐）

Internet Archive 的快照通常完整保留了文章正文，且无反爬限制。

```bash
# 原始 URL
ORIGINAL_URL="https://www.techflowpost.com/zh-CN/article/31549"

# 直接用 web.archive.org 获取快照
curl -sL "https://web.archive.org/web/2026/${ORIGINAL_URL#https://}" | python3 -c "
import sys, re
html = sys.stdin.read()

# 提取标题
title = re.search(r'<title>(.*?)</title>', html)
if title: print('TITLE:', title.group(1))

# 提取 meta description
desc = re.search(r'<meta[^>]*name=[\"\\']description[\"\\'][^>]*content=[\"\\'](.*?)[\"\\']', html)
if desc: print('DESC:', desc.group(1))

# 提取长文本块（含中文的段落）
texts = re.findall(r'>([^<]{30,})<', html)
for t in texts:
    t = t.strip()
    if any('\\u4e00' <= c <= '\\u9fff' for c in t):
        print(t)
        print('---')
"
```

### 快速提取正文的管道命令

```bash
# 一步到位：取正文标题 + 所有含中文的段落
curl -sL "https://web.archive.org/web/2026/https://example.com/article" | \
  python3 -c "
import sys, re
html = sys.stdin.read()
# 标题
t = re.search(r'<title>(.*?)</title>', html)
if t: print('TITLE:', t.group(1))
# 所有长文本块中的中文段落
texts = re.findall(r'>([^<]{30,})<', html)
for t in texts:
    if any('\u4e00' <= c <= '\u9fff' for c in t):
        print(re.sub(r'<[^>]+>', '', t).strip())
"
```

## 方案二：搜索 Google/Bing 快照

```bash
curl -sL "https://webcache.googleusercontent.com/search?q=cache:${URL}"
```

成功率低于 web.archive.org，但偶尔有效。

## 方案三：利用 RSS 或 API

部分媒体提供 RSS 全文输出（如 techflowpost 有 `/api/client/common/rss.xml`），或 JSON API（如 `/api/article/{id}`）。

```bash
curl -sL "https://www.techflowpost.com/api/article/31549"
```

注意：即使 API 端点有反爬限制，返回的内容量（字节数）可用来判断是否命中反爬墙。

## 判断是否命中反爬

- 返回内容 < 5KB 且只有混淆 JS → 命中反爬
- 返回内容 > 10KB 且包含中文段落 → 正常内容
- 标题包含网站名 + 文章标题 → 正常内容

## 注意事项

- web.archive.org 的快照可能有延迟（数小时到数天），不保证有最新文章
- 快照可能只保存 HTML 骨架，JS 渲染的内容丢失
- 对于纯文本类页面（如 GitHub raw、JSON API），优先用 curl 直连
- 提取正文后，仍需遵守公众号写作规则：用自己的语言重写，不得直接复制
