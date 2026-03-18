---
name: wechat-draft
description: 微信公众号草稿箱自动保存技能。用于通过微信开发者平台相关 API 自动获取 access_token、上传封面图、创建草稿到草稿箱。适用于“把文章自动保存到公众号草稿箱”“接微信公众号开发者平台 API”“一键写稿后存草稿”“多账号公众号草稿管理”等场景。要求预先提供从微信开发者平台获取的 AppID、AppSecret，并将运行机器出口 IP 加入 API IP 白名单。
---

# WeChat Draft Skill

按下面流程执行“自动保存到公众号草稿箱”任务。

## 1. 必要准备（缺一不可）

在真正调用微信 API 前，先确认：

1. 已从**微信开发者平台**拿到 `AppID`
2. 已从**微信开发者平台**拿到 `AppSecret`
3. API IP 白名单已在**微信开发者平台**加入运行此 skill 的机器出口 IP
4. 已配置 `config.json`（可由 `config.example.json` 复制而来）

最小可用条件：
- **必须有 AppID + AppSecret + API IP 白名单**
- 只给 AppSecret 不够，少了 AppID 无法换 token
- 本教程中的这些配置项，统一按微信开发者平台入口处理

## 2. 配置文件

参考 `config.example.json` 创建 `config.json`：

```json
{
  "accounts": {
    "主号": {
      "appid": "wxXXXXXX",
      "secret": "XXXXXX",
      "name": "我的公众号",
      "style": {
        "tone": "专业、客观",
        "target": "目标读者群体",
        "length": "建议字数范围",
        "keywords": ["关键词1", "关键词2"]
      }
    }
  },
  "default": "主号"
}
```

- `accounts`：多账号配置
- `default`：默认账号名
- `style`：可选，仅用于写作偏好，不影响 API 调用

## 3. 工作流程

1. 读取账号配置
2. 自动获取/刷新 `access_token`
3. 如有封面图，上传素材拿 `media_id`
4. 保留传入 HTML 中的排版样式（例如 `<p style="line-height:3;">`）
5. 调用微信草稿接口 `draft/add`
6. 返回草稿 `media_id` 或错误信息

## 4. 关键脚本

- `scripts/token_manager.sh`：获取并缓存 token（默认缓存 2 小时，提前 5 分钟失效）
- `scripts/upload_image.sh`：上传封面图到微信素材库
- `scripts/create_draft.sh`：创建公众号草稿

## 5. 常见触发方式

- “把这篇文章自动保存到公众号草稿箱”
- “用微信开发者平台 API 存草稿”
- “接上公众号 AppID / AppSecret，自动保存草稿”
- “用测试号保存这篇文章到草稿箱”

## 6. 故障排查

### `invalid ip not in whitelist`
- 原因：运行机器出口 IP 不在微信 API 白名单里
- 处理：先确认当前出口 IP，再到微信开发者平台加白

### `invalid appid` / `invalid credential`
- 原因：AppID / AppSecret 填错，或账号映射错误
- 处理：核对 `config.json`

### `access_token expired`
- 正常情况下脚本会自动刷新
- 若持续异常，检查缓存目录：`~/.openclaw/cache/wechat-draft`

### `invalid media_id`
- 原因：封面图上传失败，或图片格式不合规
- 处理：优先使用 jpg/png，并重新上传

## 7. 安全要求

- 不要把真实 `config.json`、真实 AppSecret、真实 token 提交到 GitHub
- 对外分享时只分享：
  - `SKILL.md`
  - `config.example.json`
  - `scripts/`

## 8. 对外说明口径

这个 skill 的职责是：
- **负责把已经写好的内容，通过微信公众号开发者 API 自动保存到草稿箱**
- **不负责公众号风格写作本身**；写作与改写请交给 `wechat-article`
