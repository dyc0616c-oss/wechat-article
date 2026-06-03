# Style Learning via Direct DeepSeek API

当在 wechat-writing-assistant 等独立服务器中运行时，风格学习可以通过直接调用 DeepSeek API 完成，不走 Hermes Agent。

## 架构

```
前端 POST /api/accounts/learn-style { accountId, articleUrls }
  ↓
后端创建 status="direct" / kind="style-learn" 的 run
  ↓
前端 SSE → /api/runs/{run.id}/events
  ↓
后端：fetchArticleContent() x N → DeepSeek 流式 → SSE 推送
```

## fetchArticleContent() 模式

```javascript
async function fetchArticleContent(url) {
  // 跳过微信域名（100% 被反爬拦截）
  if (url.includes('mp.weixin.qq.com') || url.includes('weixin.qq.com')) return null;

  var body = '';
  // Phase 1: 直连 fetch（6-8s 超时）
  try { body = await fetch(url, { signal: AbortSignal.timeout(8000), headers: { 'User-Agent': '...' } }).then(r => r.ok ? r.text() : ''); } catch {}

  // Phase 2: archive.org 快照兜底
  if (!body || body.length < 200) {
    try { body = await fetch('https://web.archive.org/web/2026/' + url, { signal: AbortSignal.timeout(8000) }).then(r => r.ok ? r.text() : ''); } catch {}
  }

  // Phase 3: 提取中文句子（正则去 HTML 标签）
  if (body && body.length > 200) { /* 去掉 script/style/tag，提取中文句 */ }

  // Phase 4: og:description 备选
  if (!body || body.length < 100) { /* 只读 head 区间提取 og:description */ }

  return null;
}
```

## 9 维度风格分析 System Prompt

```text
你是一个专业的公众号写作风格分析专家。你的任务是根据用户提供的文章内容，
深入分析该公众号的写作风格，生成一套可执行的写作规则。

分析维度：
1. 标题风格：长度、句式结构、情绪强度、是否带数字/反问/悬念
2. 摘要风格：作用定位、语气倾向、是否补判断/抛观点
3. 首段切入方式：前3句锚点结构、场景带入方式
4. 正文结构：段落数量、句长分布、大块分隔方式、小标题风格
5. 语言风格：口语化程度、专业术语处理方式、网络用语边界
6. 叙事方式：故事推进 vs 信息罗列 vs 观点输出
7. 结尾形式：CTA类型、评论钩子、更新预告
8. 排版特征：重点句高亮、配图策略、HTML样式偏好
9. 禁用词/禁用句式：所有不能出现的表达

输出格式：用中文输出，每个维度写2-5条具体、可执行的规则。
最后汇总3-5条最核心的风格金律。
不要散文描述，每条规则必须是一句可直接执行的指令。
```

## User Prompt 模板

```text
请分析以下公众号「{accountName}」的文章写作风格。

共获取到 {N} 篇文章内容：

=== 文章 1 ===
{提取的中文正文内容}

=== 文章 2 ===
{提取的中文正文内容}

...

请根据以上文章内容，按要求的维度输出风格分析规则。
```

## 已知局限

- 微信域名（mp.weixin.qq.com）curl 100% 被拦截，直接跳过
- 部分使用 ESA/acw_tc 反爬的站点（如 techflowpost.com）archive.org 也不一定能拿到完整正文
- 少于 2 篇文章成功获取时，判定为不可分析并返回错误
- 模型设置为 `deepseek-chat`，`max_tokens: 4096`，`stream: true`
