# Google News RSS 搜索技术

当 DuckDuckGo HTML、Google 网页搜索、Bing 等搜索引擎全部被 CAPTCHA/反爬拦截时，**Google News RSS** 是可靠的免墙搜索方案。

## 原理

Google News 提供 RSS feed 格式的搜索结果，通过 `news.google.com/rss/search` 端点返回标准 XML，不会被常规网页搜索的反爬机制拦截。RSS feed 返回的是结构化数据（标题、来源、摘要、链接），不需要 JS 渲染。

## 使用方式

### 基本搜索

```bash
curl -sL "https://news.google.com/rss/search?q={关键词}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans" -A "Mozilla/5.0"
```

参数说明：
- `hl=zh-CN` — 界面语言（中文）
- `gl=CN` — 地理位置（中国）
- `ceid=CN:zh-Hans` — 版本标识
- 搜索中文新闻建议全用 URL 编码的中文关键词

### 提取结果

返回的 RSS XML 中，每个 `<item>` 包含：
- `<title>` — 文章标题
- `<link>` — Google News 跳转链接（需要再重定向一次才能到原文）
- `<source>` — 来源媒体名
- `<description>` — 文章摘要（含原文链接）

Python 解析示例：

```python
import re, html
content = resp.read().decode('utf-8')
items = re.findall(r'<item>(.*?)</item>', content, re.DOTALL)
for item in items:
    title = re.search(r'<title>(.*?)</title>', item)
    source = re.search(r'<source[^>]*>(.*?)</source>', item)
    desc = re.search(r'<description>(.*?)</description>', item)
    if title:
        t = html.unescape(title.group(1))
        s = html.unescape(source.group(1)) if source else '?'
        print(f'[{s}] {t}')
```

### 获取原文 URL

Google News RSS 返回的 `link` 是 Google 的跳转链接，要获取真实的原文 URL：

```bash
# 跟踪重定向获取最终 URL
curl -sL -o /dev/null -w "%{url_effective}" "https://news.google.com/...跳转链接..." -A "Mozilla/5.0"
```

或者直接通过 `description` 字段中的 `<a href="...">` 提取。

## 与 Brave Search 的互补

| 场景 | 推荐方案 |
|------|---------|
| 搜中文新闻 | Google News RSS（中文覆盖率最高） |
| 搜英文/国际新闻 | Google News RSS（改 `hl=en-US&gl=US`） |
| 搜产品名/工具名 | Brave Search（技术内容更准） |
| 都失效 | domain probing（`references/content-fetching-tips.md`） |

## 已知限制

- 只返回新闻类结果，不返回普通网页/论坛/社交媒体
- 同一关键词短时间内频繁查询可能被限流（每小时约 20-30 次安全）
- 返回结果数有限（通常 10-20 条），不如 HTML 搜索全面
- 部分中文媒体的 RSS 摘要被截断严重
