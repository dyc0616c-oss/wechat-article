# WeChat Skills 使用说明

这个仓库包含两套分开的 OpenClaw Skill：

- `wechat-article`：负责公众号内容生产
- `wechat-draft`：负责通过微信公众号开发者平台 API 自动保存到草稿箱

最简单理解：

- `wechat-article` = **写稿**
- `wechat-draft` = **存稿**

---

# 一、仓库地址

- GitHub：<https://github.com/dyc0616c-oss/wechat-article>

仓库里已经包含：

- `wechat-article.skill`
- `wechat-draft.skill`
- `skills/wechat-article/` 源文件
- `skills/wechat-draft/` 源文件

---

# 二、两个 Skill 的作用

## 1）wechat-article

用于公众号内容创作和改写，主要负责：

- 写公众号文章
- 做二创改写
- 生成标题、摘要、正文
- 输出公众号排版版
- 按不同账号风格生成内容

适合场景：

- “帮我写一篇公众号文章”
- “按老韭风格改写这篇”
- “给我出标题、摘要、正文”
- “按某个账号的语气发一版”

---

## 2）wechat-draft

用于接微信公众号开发者平台 API，主要负责：

- 自动获取 / 刷新 `access_token`
- 上传封面图
- 自动保存文章到公众号草稿箱

适合场景：

- “把这篇文章自动保存到公众号草稿箱”
- “接微信公众号开发者平台 API 自动存稿”
- “一键写稿后自动保存草稿”

---

# 三、典型工作流

如果你想实现“AI 写完文章后自动保存到公众号草稿箱”，常见流程是：

1. 用 `wechat-article` 生成文章
2. 用 `wechat-draft` 调微信 API 保存到草稿箱

也就是：

- **内容生成** → `wechat-article`
- **草稿入库** → `wechat-draft`

---

# 四、如何安装

## 方式 1：直接使用打包好的 `.skill`

仓库里已经有两个打包文件：

- `wechat-article.skill`
- `wechat-draft.skill`

适合：
- 想直接拿来用
- 不打算自己改源码

## 方式 2：下载源文件自己修改

如果你想自己修改规则、风格、映射表，可以直接下载源码目录：

- `skills/wechat-article/`
- `skills/wechat-draft/`

适合：
- 有多个公众号账号
- 想自定义风格
- 想重新打包 skill
- 想用“公众号A / B / C”这种匿名方式做对外展示

---

# 五、wechat-draft 想实现“自动保存草稿”需要准备什么

这个是重点。

`wechat-draft` 虽然可以直接下载，但如果要真正调用微信公众号开发者平台 API 自动保存草稿，至少需要这 3 样：

1. **AppID**
2. **AppSecret**
3. **API IP 白名单**

也就是：

**AppID + AppSecret + IP 白名单**

缺一个都不行。

## 具体说明

### 1. AppID
现在从**微信开发者平台**获取。

### 2. AppSecret
现在从**微信开发者平台**获取并管理。

### 3. API IP 白名单
需要把运行这套 skill 的机器出口 IP 加到**微信开发者平台**的 API IP 白名单里，否则会报错：

- `invalid ip not in whitelist`

> 也就是说，这几个关键信息现在不要再按旧教程去公众号后台找，统一按微信开发者平台的入口处理。

---

# 六、wechat-draft 的基本配置方法

仓库里只提供示例配置：

- `skills/wechat-draft/config.example.json`

你需要复制出自己的：

- `skills/wechat-draft/config.json`

示例结构如下：

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

说明：

- `accounts`：你的公众号账号配置
- `default`：默认使用哪个账号
- `style`：是写作偏好字段，不影响 API 鉴权本身

> 注意：真实 `config.json` 不要提交到 GitHub。

---

# 七、映射表怎么用

`wechat-article` 支持“账号名 → 风格文件”的映射。

映射表文件位置：

- `skills/wechat-article/references/account-style-map.json`

它的作用是：

> 你只需要告诉系统“按哪个公众号发”，系统就会自动读取这个账号对应的 style 文件来写。

## 例子

```json
{
  "default": "style-a",
  "accounts": {
    "公众号A": "style-a",
    "公众号B": "style-b",
    "公众号C": "style-c",
    "公众号D": "style-d"
  }
}
```

意思就是：

- 说“按公众号A发” → 用 `style-a`
- 说“按公众号B发” → 用 `style-b`
- 说“按公众号C发” → 用 `style-c`

---

# 八、怎么制作自己的公众号风格

最推荐的方法是：

## 第一步：先准备你自己的样稿

建议收集你过去写得最像自己的 **5-10 篇公众号文章**。

重点观察这些东西：

- 你通常写什么类型的选题
- 开头怎么切入
- 语气是口语化还是专业化
- 标题偏悬念、观点还是利益
- 每篇大概写几段
- 会不会用固定口头禅
- 结尾是总结、提问、还是 CTA

---

## 第二步：新建一个 style 文件

放在这里：

- `skills/wechat-article/references/`

例如：

- `style-f.md`

---

## 第三步：在 style 文件里写清楚这几类规则

建议至少包括：

### 1. 账号定位
例如：
- 资讯号 / 观点号 / 教程号 / 吃瓜号
- 面向新手 / 从业者 / 泛用户

### 2. 语气
例如：
- 口语化还是专业化
- 是否允许犀利表达
- 是否允许反问句
- 有没有固定口头禅

### 3. 结构
例如：
- 首段先抛结论还是先讲故事
- 正文几大段
- 是否固定使用小标题
- 结尾怎么收口

### 4. 标题规则
例如：
- 偏悬念型 / 观点型 / 利益型
- 标题控制几字
- 摘要控制几字

### 5. 风险边界
例如：
- 不编造事实
- 不做无依据指控
- 不做绝对化收益承诺
- 信息不确定时标“待确认”

### 6. 开头 / 结尾习惯
例如：
- 有没有固定开头提示
- 有没有固定 CTA
- 是否引导关注 / 进群 / 私信

---

## 第四步：把你的账号绑定到映射表

修改：

- `skills/wechat-article/references/account-style-map.json`

例如：

```json
{
  "default": "style-a",
  "accounts": {
    "我的公众号": "style-f",
    "主号": "style-f",
    "测试号": "style-e"
  }
}
```

这样以后你只要说：

- “按我的公众号发”
- “按主号风格改一下”

系统就会自动去读取 `style-f.md`。

---

# 九、推荐的 style 文件写法

建议一个 style 文件至少包含这些模块：

- 账号定位
- 人设语气
- 开场规则
- 内容结构
- 标题与摘要规则
- 数据与证据规则
- 风险边界
- 开头 / CTA / 文末
- 示例段落

这样 AI 更容易稳定复现这个账号的文风。

---

# 十、常见问题

## 1. 直接下载仓库，别人就能自动存稿吗？
不一定。

`wechat-article` 下载后可以看规则、改风格、用于写稿。

但 `wechat-draft` 要真正自动保存草稿，仍然需要对方自己配置：

- AppID
- AppSecret
- API IP 白名单
- `config.json`

---

## 2. 只给 AppSecret 行不行？
不行。

必须要：
- AppID
- AppSecret
- API IP 白名单

---

## 3. 可以一套 skill 同时支持多个公众号吗？
可以。

`wechat-draft` 可以在 `config.json` 里配多个账号。  
`wechat-article` 可以通过映射表给多个账号绑定不同风格。

---

## 4. 为什么要把“写稿”和“存稿”拆开？
因为这两个任务本质不同：

- 写稿是内容生成问题
- 存稿是 API 接入问题

拆开后更容易：
- 单独维护
- 单独升级
- 单独复用
- 避免把写作规则和发布逻辑搅成一锅粥

---

# 十一、适合谁用

适合这些人：

- 做公众号矩阵的人
- 有多个账号、多个文风的人
- 想让 AI 按号稳定出稿的人
- 想把“写稿 + 自动存草稿”流程打通的人
- 愿意自己配置微信开发者平台的人

---

# 十二、安全提醒

请不要把下面这些东西提交到公开仓库：

- 真实 `config.json`
- 真实 AppSecret
- 真实 access_token
- 任何含账号密钥的缓存文件

对外公开时，建议只保留：

- `SKILL.md`
- `config.example.json`
- `scripts/`
- `.skill` 打包产物

---

如果你是第一次接触这套方案，可以先按这个顺序上手：

1. 先用 `wechat-article` 跑通“写稿”
2. 再配 `wechat-draft` 跑通“自动存草稿”
3. 最后再补自己的 style 文件和映射表

这样最稳，不容易一上来就把流程打成毛线球。