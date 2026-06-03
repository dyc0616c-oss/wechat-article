# CDP 操控 Chrome 保存公众号草稿

## 适用场景

当 Hermes 的 WeChat API 不可用（未配置 AppID/AppSecret、IP 不在白名单），或需要快速测试时，可以用 **Chrome DevTools Protocol (CDP)** 直接操控已登录微信后台的 Chrome 浏览器来保存草稿。

## 前提

1. Chrome 已通过 `--remote-debugging-port=9222` 启动
2. 浏览器已登录 `mp.weixin.qq.com`（二维码扫码登录）
3. 使用 `browser_cdp` 工具连接

## 完整工作流

### Step 1: 检查并连接 CDP

```javascript
// 获取所有标签页
await browser_cdp({method: "Target.getTargets", params: {}})
```

### Step 2: 打开新标签页到微信后台

```javascript
// 先创建目标
const tab = await browser_cdp({
  method: "Target.createTarget",
  params: { url: "https://mp.weixin.qq.com" }
})
```

### Step 3: 检查登录状态

```javascript
await browser_cdp({
  target_id: tab.targetId,
  method: "Runtime.evaluate",
  params: { expression: "document.body.innerText.substring(0,500)" }
})
```

未登录时会显示登录页（含二维码），已登录会直接进后台。

### Step 4: 导航到图文编辑器

```javascript
// 获取当前 token
const url = await browser_cdp({
  target_id: tab.targetId,
  method: "Runtime.evaluate",
  params: { expression: "window.location.href" }
})
// 从 URL 中提取 token，然后打开编辑器
await browser_cdp({
  target_id: tab.targetId,
  method: "Page.navigate",
  params: { url: `https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit&action=edit&lang=zh_CN&token=${TOKEN}&type=77&create=1` }
})
```

### Step 5: 填写标题

```javascript
await browser_cdp({
  target_id: tab.targetId,
  method: "Runtime.evaluate",
  params: {
    expression: `
      (function(){
        const ta = document.querySelector('textarea[placeholder*="标题"]');
        if(ta) {
          const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
          setter.call(ta, 'YOUR_TITLE');
          ta.dispatchEvent(new Event('input', { bubbles: true }));
          return 'Title set OK';
        }
        return 'Title input not found';
      })()
    `
  }
})
```

### Step 6: 填写作者

```javascript
await browser_cdp({
  target_id: tab.targetId,
  method: "Runtime.evaluate",
  params: {
    expression: `
      (function(){
        const auth = document.querySelector('input[placeholder*="作者"]');
        if(auth) {
          const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
          setter.call(auth, 'YOUR_AUTHOR');
          auth.dispatchEvent(new Event('input', { bubbles: true }));
          auth.dispatchEvent(new Event('change', { bubbles: true }));
          return 'Author set OK';
        }
        return 'Author input not found';
      })()
    `
  }
})
```

### Step 7: 填写正文

微信编辑器使用 ProseMirror 框架。可以通过设置 `innerHTML` 插入内容：

```javascript
await browser_cdp({
  target_id: tab.targetId,
  method: "Runtime.evaluate",
  params: {
    expression: `
      (function(){
        const e = document.querySelectorAll('.ProseMirror')[1];
        if(!e) return 'Editor not found';
        e.innerHTML = '<p>YOUR_HTML_CONTENT</p>';
        e.dispatchEvent(new Event('input', {bubbles: true}));
        return 'Content set OK: ' + e.innerHTML.length;
      })()
    `
  }
})
```

**注意：**
- ProseMirror 接受 HTML 格式的 innerHTML，但会用自己的节点树重新渲染
- 内容需分多次追加（每次追加 `e.innerHTML = e.innerHTML + '<p>new content</p>'`）
- 特殊字符（中文、emoji）需要转义为 unicode 或直接使用原文字符串
- 如果 ProseMirror 重新渲染覆盖了 innerHTML，尝试减少每次设置的内容量

### Step 8: 保存草稿

```javascript
await browser_cdp({
  target_id: tab.targetId,
  method: "Runtime.evaluate",
  params: {
    expression: `
      (function(){
        const btns = Array.from(document.querySelectorAll('a,button'))
          .filter(function(el){return el.innerText.includes('保存为草稿')});
        if(btns.length>0){btns[0].click(); return 'Clicked save'}
        return 'Save button not found'
      })()
    `
  }
})
```

### Step 9: 验证保存成功

检查页面中是否出现「保存成功」字样或手动保存记录：

```javascript
await browser_cdp({
  target_id: tab.targetId,
  method: "Runtime.evaluate",
  params: { expression: "document.body.innerText.includes('保存成功') || document.body.innerText.includes('手动保存')" }
})
```

## 已知坑点

### 1. ProseMirror 内容覆盖
ProseMirror 收到 innerHTML 后可能会用自己的节点树重新渲染，覆盖你设置的内容。如果注入后内容丢失，尝试以下方法：
- 减少每次注入的内容量（2-3个段落一次）
- 注入后立即 dispatch input 事件
- 等待编辑器完全加载后再写入（用 setTimeout 或轮询）

### 2. Runtime.evaluate 间歇性失败
偶尔 CDP 返回 `'Runtime.evaluate' wasn't found` 错误。重试即可恢复。

### 3. 图片上传尚未自动化
目前 CDP 方案只支持文字内容。图片需要先上传到微信素材库，再插入编辑器。暂时需要手动操作或在代码中添加图片上传流程。

### 4. 页面元素选择器变化
微信后台的 DOM 结构随时可能更新。如果选择器失效，用以下方法检查：
```javascript
// 查找所有 textarea / input
Array.from(document.querySelectorAll('textarea,input'))
  .map(e => (e.placeholder||e.id||e.name) + ' type=' + (e.type||e.tagName))

// 查找所有 ProseMirror 编辑器
document.querySelectorAll('.ProseMirror')

// 查找保存按钮
Array.from(document.querySelectorAll('a,button'))
  .filter(el => el.innerText.includes('保存'))
```

## 与微信 API 方案的对比

| 维度 | CDP 方案 | 微信 API 方案 |
|------|---------|-------------|
| 需要 AppID/Secret | ❌ 不需要 | ✅ 必须配置 |
| 需要 IP 白名单 | ❌ 不需要 | ✅ 需要 |
| 登录方式 | 扫码登录 | 接口调用凭据 |
| 速度 | 较慢（5-15秒） | 快（1-3秒） |
| 图片上传 | ❌ 需额外实现 | ✅ 原生支持 |
| 稳定性 | 依赖页面 DOM | 稳定 API |
| 微信检测风险 | 无（像真人操作） | 无 |

## 推荐使用场景

- 测试 / 快速验证阶段：用 CDP 方案，无需配置 API 凭据
- 生产 / 批量发布阶段：用微信 API 方案
- 两者也可并行：CDP 做测试，API 做正式发布
