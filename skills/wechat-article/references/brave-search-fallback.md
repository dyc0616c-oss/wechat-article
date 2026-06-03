# Brave Search Fallback（2026-05-18 实战验证）

当所有主流搜索引擎（DuckDuckGo、Google、Bing、Baidu、X）均被反爬/CAPTCHA/登录墙拦截时，**Brave Search 的 curl 直连**可以作为最后的搜索备选方案。

## 实战背景

2026-05-18 搜索 Anthropic 补贴政策变化相关素材时：

| 引擎 | 结果 |
|------|------|
| DuckDuckGo HTML 版 | CAPTCHA「选鸭子」拦截 |
| Google | sorry 页面（反爬） |
| Bing | Cloudflare 安全质询 |
| Baidu | 百度安全验证 |
| X 搜索 | 登录墙 |

全部失败后，**Brave Search 的 curl 请求可以正常返回搜索结果**，含文章标题和摘要片段。

## 用法

```bash
curl -sL "https://search.brave.com/search?q=关键词关键词" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
```

## 提取搜索结果

Brave 的 HTML 返回结果比较特殊——不包含常规的 `<a href>` 搜索结果链接标签，而是把摘要信息放在纯文本片段中。

**最佳提取方式：用 Python 正则扫描长文本片段**

```python
import re, sys
html = sys.stdin.read()

# 提取所有相关长文本段落（Brave 把搜索结果信息放在纯文本中）
texts = re.findall(r'>([^<]{60,})<', html)
for t in texts:
    t = t.strip()
    if any(x in t.lower() for x in ['anthropic', 'claude', 'gpu', 'spacex', 'subsidy', 'quota']):
        print(t[:300])
```

**提取文章链接（Brave 不直接展示链接文本）**

Brave 搜索结果页的结构与传统搜索引擎不同——搜索结果以 `<a>` 标签形式呈现，但并非所有链接都直接可见于 snapshot。需要从 HTML 中扫描特定模式：

```bash
curl -sL "https://search.brave.com/search?q=关键词" -H "User-Agent: Mozilla/5.0" \
  | python3 -c "
import sys, re
html = sys.stdin.read()
links = re.findall(r'<a[^>]*href=\"(https?://[^\"\\s]+)\"[^>]*>([^<]+)</a>', html)
for url, text in links:
    text = text.strip()
    if len(text) > 5 and 'brave' not in url and 'search.brave' not in url:
        print(f'{text} --> {url}')
"
```

注意：Brave 返回的链接数量少于传统搜索引擎（通常 5-15 条），但相关性较高。

## 优劣势

**优势：**
- 无 CAPTCHA 拦截（已验证），不需要 CDP/browser
- 速度快（curl 直连，0.5-3s）
- 对长尾英文关键词效果好
- 不需要 API Key 或注册

**劣势：**
- 对中文关键词效果一般（不如 Google）
- HTML 结构与传统搜索引擎不同，提取信息需要特殊处理
- 返回结果数量有限
- **有频率限制：连续 3-5 次搜索后会触发 CAPTCHA 拦截**（2026-05-18 发现）。触发后，后续所有 Brave Search 请求均返回 captcha 页面，短时间（15-30分钟）不可恢复。策略：把 Brave Search 当"有限次急诊"用——只用在其他方法全部失败时，且一次性用完配额。触发 CAPTCHA 后标注「当前为单源稿」

## 在搜索优先级中的位置

按 wechat-article skill 定义的搜索优先级：

1. **browser_navigate DuckDuckGo HTML 版**（首选，需 CDP 就绪）
2. **vxtwitter/fxtwitter API**（素材为 X 链接时）
3. **Brave Search via curl**（当 1 和 2 均失败时的备选）
4. **Google via browser**（如果 CDP 就绪）
5. **archive.org 快照**（针对特定已知 URL）
6. 标注「当前为单源稿」
