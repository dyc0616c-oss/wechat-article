# ⚠️ DEPRECATED — 独立服务器 Web 搜索引擎（2026-05-14 已移除）

> **本方案已于 2026-05-14 被移除。** 保留本文件仅作参考，不应在新的会话中重新实现。
>
> 移除原因：三阶段搜索（curl 用户素材 → DuckDuckGo → 搜狗微信）在面向中文站点时**100% 超时或返回空结果**。主流中文媒体/科技站（新华网、知乎、36kr、CSDN、techflowpost）均使用 ESA/acw_tc 等反爬机制，curl 和 DuckDuckGo 均无法突破。用户确认：搜索补充素材这一步无法工作，直接删掉，写稿时不再搜索。
>
> **当前方案**：直接调用 DeepSeek API（streaming），不使用任何搜索。基于用户提供的素材直接生成，prompt 中标记"当前仅基于已有素材写稿"。

# 旧方案存档

当通过 Node.js 等独立服务器调用 LLM API（而非 Hermes Agent）时，需要自行实现 web 搜索能力。本文件记录一个已被生产验证的三阶段搜索方案。

---

## 架构概览

```
用户素材链接 + 标题
    │
    ├─ Phase 1: curl 用户提供的 URL 提取正文
    ├─ Phase 2: DuckDuckGo HTML 搜索补充来源
    └─ Phase 3: 搜狗微信搜索公众号文章
    │
    ▼
补充素材摘要 → 拼入 LLM Prompt → 生成
```

## 三阶段搜索实现

### Phase 1：提取用户素材正文

```javascript
const resp = await fetch(m.url, {
  signal: AbortSignal.timeout(8000),
  headers: { 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36' }
});
if (resp.ok) {
  const text = await resp.text();
  // 提取中文段落（20字以上的句子）
  const matches = text.match(/[^。！？\n]{20,}[。！？]/g);
  // 清洗 HTML 标签，去重，拼成摘要
}
```

**注意**：大多数中文科技站（新华网、知乎、36kr、CSDN）会拦截 curl。这是预期的——打不开不报错，继续 Phase 2。

### Phase 2：DuckDuckGo HTML 搜索

DuckDuckGo 提供 `/html/` 端点，返回纯 HTML 搜索结果（无需 API Key）：

```javascript
const url = 'https://html.duckduckgo.com/html/?q=' + encodeURIComponent(keyword);
const resp = await fetch(url, {
  signal: AbortSignal.timeout(10000),
  headers: { 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36' }
});
const html = await resp.text();
// 提取标题和摘要
const linkRegex = /<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/g;
const snippetRegex = /<a[^>]*class="result__snippet"[^>]*>([\s\S]*?)<\/a>/g;
```

**已知问题**：DDG 对中文长尾查询经常返回空结果。这是 Phase 2 的降级点。

### Phase 3：搜狗微信搜索（中文公众号文章专项）

```javascript
const url = 'https://weixin.sogou.com/weixin?type=2&query=' + encodeURIComponent(keyword);
const resp = await fetch(url, {
  signal: AbortSignal.timeout(8000),
  headers: { 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36' }
});
// 提取文章标题
const titleRegex = /<h3[^>]*>[\s\S]*?<a[^>]*>([\s\S]*?)<\/a>[\s\S]*?<\/h3>/g;
```

返回 10 条左右公众号文章标题，足够判断来源类型和切入角度。

### 判断是否找到有效补充

```javascript
// 如果找到的来源 <= 用户提供的素材数，说明没搜到真正的补充
if (found.length <= materials.length) return null;
return found.join('\n\n');
```

## 搜索失败的交互式恢复（SSE 轮询 + 决策文件模式）

### 问题

LLM API 调用是长连接 SSE。搜索失败时不能直接报错关闭连接——应该给用户选择重试或跳过的机会。

### 方案：决策文件轮询

```
SSE 流:
  → search.failed { error, hasMaterials }
  → 轮询 ${runId}.decision.json (每1秒)
  ← 用户在前端点"重试"或"跳过"
  → POST /api/runs/${runId}/search-decision { choice: "retry" | "skip" }
  → 写入 ${runId}.decision.json
  → SSE 读到决策后继续
```

### 后端实现

**SSE 处理函数中：**

```javascript
// 搜索失败
send("search.failed", { error: errMsg, hasMaterials: true });

// 轮询决策文件，最多 60 秒
const decisionFile = join(RUNS_DIR, runId + '.decision.json');
for (let poll = 0; poll < 60; poll++) {
  await new Promise(r => setTimeout(r, 1000));
  try {
    const raw = await readFile(decisionFile, 'utf8');
    const d = JSON.parse(raw);
    if (d.choice === 'retry') {
      // 重试搜索逻辑...
    } else if (d.choice === 'skip') {
      // 跳过搜索，直接进入 LLM 调用
      break;
    }
  } catch { /* 文件未就绪，继续轮询 */ }
}
// 超时未决策 → 默认跳过
```

**决策端点：**

```javascript
POST /api/runs/${runId}/search-decision
Body: { choice: "retry" | "skip" }
→ 写入 decisionFile
→ 返回 { ok: true }
```

### 前端实现

```javascript
// SSE 事件监听
source.addEventListener("search.failed", (event) => {
  const data = JSON.parse(event.data);
  setSearchError(data.error);
  setSearchRunId(run.id);
});

// 重试
await fetch(`/api/runs/${searchRunId}/search-decision`, {
  method: "POST",
  body: JSON.stringify({ choice: "retry" })
});

// 跳过
await fetch(`/api/runs/${searchRunId}/search-decision`, {
  method: "POST",
  body: JSON.stringify({ choice: "skip" })
});
```

## 加载到 Prompt 的方式

```javascript
let userPrompt = '已有素材：\n' + selectedMaterialsText(materials);

if (searchResult) {
  userPrompt += '\n\n【搜索获取的补充材料】\n' + searchResult;
} else {
  userPrompt += '\n\n⚠️ 注意：搜索补充素材失败，当前为单源稿。请在输出中标注此风险。';
}
```

Node.js `fetch` 可用（Node 21+ 稳定），`AbortSignal.timeout()` 用于超时控制。
