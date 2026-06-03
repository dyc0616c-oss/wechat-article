# CDP 控制 Chrome 自动发布公众号草稿（2026-05-14 实战验证）

## 原理

通过 Chrome DevTools Protocol（CDP）直接操控已登录微信后台的 Chrome 浏览器实例，模拟人工操作：打开图文编辑器 → 填入标题/作者/正文 → 保存草稿。

**核心优势：** 不走微信 API，不依赖 IP 白名单，不走秀米第三方平台。原理与秀米 Chrome 插件相同——浏览器扩展直接操作 DOM。

## 前置条件

### Chrome 独立实例（2026-05-15 用户强制）

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-hermes-profile \
  --no-first-run \
  --no-default-browser-check &
```

**纪律：**
- ❌ 不得 kill 用户现有的 Chrome 进程（`killall "Google Chrome"` 绝对禁止）
- ✅ 始终使用 `--user-data-dir=/tmp/chrome-hermes-profile` 启动独立实例

### CDP 连接

通过 browser_cdp 工具直接调用，无需额外配置。端点默认为 `ws://127.0.0.1:9222`。

## 完整工作流

### Step 1 — 打开微信后台并登录

```javascript
// 创建新标签页并导航到微信公众平台
browser_cdp({
  method: "Target.createTarget",
  params: { url: "https://mp.weixin.qq.com" }
})

// 检查是否已登录
browser_cdp({
  method: "Runtime.evaluate",
  params: { expression: "window.location.href" },
  target_id: "TARGET_ID"
})
```

登录态判定：URL 中包含 `token=` 参数即已登录，否则为登录页。

### Step 2 — 进入图文编辑器

```javascript
// 直接跳转到新建图文页面
browser_cdp({
  method: "Page.navigate",
  params: { url: "https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit&action=edit&lang=zh_CN&token={TOKEN}&type=77&create=1" },
  target_id: "TARGET_ID"
})
```

### Step 3 — 填入标题

```javascript
browser_cdp({
  method: "Runtime.evaluate",
  params: {
    expression: `(function(){
      const ta = document.querySelector('textarea[placeholder*="标题"]');
      if(!ta) return 'Title input not found';
      const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
      setter.call(ta, '你的标题');
      ta.dispatchEvent(new Event('input', { bubbles: true }));
      return 'Title set OK';
    })()`
  },
  target_id: "TARGET_ID"
})
```

### Step 4 — 填入作者

```javascript
browser_cdp({
  method: "Runtime.evaluate",
  params: {
    expression: `(function(){
      const auth = document.querySelector('input[placeholder*="作者"]');
      if(!auth) return 'Author not found';
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      setter.call(auth, '作者名');
      auth.dispatchEvent(new Event('input', { bubbles: true }));
      auth.dispatchEvent(new Event('change', { bubbles: true }));
      return 'Author set: ' + auth.value;
    })()`
  },
  target_id: "TARGET_ID"
})
```

### Step 5 — 填入正文

微信编辑器使用 ProseMirror 富文本引擎。正文编辑器是第二个 `.ProseMirror` 元素。

```javascript
browser_cdp({
  method: "Runtime.evaluate",
  params: {
    expression: `(function(){
      const editors = document.querySelectorAll('.ProseMirror');
      const bodyEditor = editors[1]; // 第二个 ProseMirror 是正文编辑器
      if(!bodyEditor) return 'Editor not found';
      bodyEditor.innerHTML = '<p>你的正文HTML</p>';
      bodyEditor.dispatchEvent(new Event('input', { bubbles: true }));
      return 'Content set, length: ' + bodyEditor.innerHTML.length;
    })()`
  },
  target_id: "TARGET_ID"
})
```

**实战确认（2026-05-14）：** ProseMirror 收到 innerHTML 后，内容会以 `leaf=""` span 形式保留：
```
<p><span leaf="">内容</span></p>
```
不会丢失。可以放心批量注入内容，每次注入后 dispatch input 事件即可。

### Step 6 — 保存草稿

```javascript
browser_cdp({
  method: "Runtime.evaluate",
  params: {
    expression: `(function(){
      const btns = Array.from(document.querySelectorAll('a,button'))
        .filter(function(el){ return el.innerText.includes('保存为草稿') });
      if(btns.length > 0) { btns[0].click(); return 'Clicked save'; }
      return 'Save button not found';
    })()`
  },
  target_id: "TARGET_ID"
})
```

### Step 7 — 验证保存结果

检查页面内容中是否出现"保存成功"或操作时间记录。

## 注意事项与坑点

### Runtime.evaluate 偶发失效

现象：CDP 返回 `{'code': -32601, 'message': "'Runtime.evaluate' wasn't found"}`

原因：CDP 连接短暂不稳定。

修复：重试即可，不需要重启 Chrome。

### ProseMirror 内容覆盖

设置 innerHTML 后 ProseMirror 会在下一个渲染周期用自己的 node tree 重建 DOM。这个重建不影响内容——设置的内容会被保留，但标签结构可能会变（如 `<p>text</p>` 变成 `<p><span leaf="">text</span></p>`）。

**图片上传（当前限制）**

当前 CDP 方案不支持自动上传图片到微信素材库：
- 正文中的图片需要先手动上传到微信素材库，获取 URL 后再插入编辑器
- 或使用微信 API 上传后获取 URL
- 2026-05-14 实测：只做了文字草稿保存，图片部分未验证

**多标签页操作**

创建新标签页时使用 `Target.createTarget`，需要指定正确的 `browserContextId`。可通过 `Target.getTargets` 获取已有标签页的 context ID。

## Chrome 后端特有操作的兼容性

| 操作 | 方法 | 备注 |
|------|------|------|
| 截图 | `Page.captureScreenshot` | 返回 base64 PNG |
| 执行 JS | `Runtime.evaluate` | 需要 target_id |
| 点击元素 | `Runtime.evaluate` + `.click()` | 比 Input.dispatchMouseEvent 更稳 |
| 设置 input 值 | JS 原生 value setter + dispatchEvent | 微信前端框架监听 input 事件 |
