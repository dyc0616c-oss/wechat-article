# Style Example（风格模板 — 新人可效仿此格式创建自己的 style）

> 这是一个风格模板示例。把 `你的公众号名` 替换成你的号，按注释修改各字段即可。
> 更详细的字段定义见 `style-schema.md`。

```yaml
account_name: 你的公众号名
style_id: style-example
positioning: 你的账号定位，一句话说清（如：币圈避坑指南 / AI工具测评 / 财经热点解读）

core_goals:
  - 本风格的核心写作目标1（如：让读者看完能避开一个坑）
  - 本风格的核心写作目标2（如：用大白话翻译复杂概念）

title:
  length: 12-20字
  style:
    - 悬念 / 利益 / 观点 / 冲突 / 反转（选你号常用的类型）
    - 示例：「先抓人，再给信息点」
  preferred_patterns:
    - 可选：你常用的标题模式（如「别XX了」「XX的真相」）
  avoid:
    - 太像新闻标题
    - 没有信息增量的空标题

digest:
  length: 10-15字
  style:
    - 钩子型 / 信息差型 / 结论型
  avoid:
    - 复述标题（摘要是补信息，不是重复）

opening:
  goal: 首段要让读者知道「这是什么」并产生继续看的欲望
  preferred_methods:
    - 情绪切入 / 问题切入 / 判断切入 / 场景切入 / 故事切入
  preferred_patterns:
    - 示例：「说出来你可能不信……」
  avoid:
    - 「近日」「近年来」「随着……的发展」

body:
  paragraph_count: 4-6段
  sentence_mode: 每段1-2句（手机上扫读最舒服）
  tone:
    - 口语化 / 犀利 / 稳健 / 故事化 / 教程化
  pacing: 中等密度（medium）
  structure_templates:
    type_a:
      - 抛出一个具体事件/问题 → 怎么回事 → 为什么重要 → 收束判断
    type_b:
      - 抛出反常识事实 → 拆解原因 → 给行动建议 → 互动收尾

language:
  characteristics:
    - 口语化程度：像朋友聊天
    - 适当使用反问、轻吐槽
    - 专业术语必须翻译成人话（GMV→卖了多少钱）
  preferred_patterns:
    - 你常用的口头禅句式
  avoid:
    - 「首先其次最后」「综上所述」「值得注意的是」

narrative:
  goals:
    - 每条主线说清楚
    - 有故事推进，不纯堆信息
  required_features:
    - 至少一条主线贯穿全文
    - 中间有结构转折
  avoid:
    - 流水账、前后重复

reasoning:
  style:
    - 判断落在具体事件中，不空谈大道理
  preferred_output:
    - 观察点 / 风险点 / 可执行判断
  avoid:
    - 「这值得我们深思」

layout:
  paragraph_rule: 每段1-2句，重点句可独立成段
  section_titles:
    enabled: true
    style: 口语化「」胶囊式标签（如「账本摊开看看」「坑在哪」）
    avoid:
      - 一、二、三编号
      - 「首先/其次/最后」
  fixed_modules:
    - 可选：风险提示 / 二维码 / 官网链接
  reading_feel:
    - 高频分段
    - 扫读友好

highlight:
  sentence: 核心判断句标红
  keyword: 产品名/模型名/关键人名标红
  numbers: 金额/排名/分数标红

ending:
  article_close:
    - 正文收束为一句可截图传播的判断（20字内金句）
  hook: true — 必有评论区互动提问
  cta_style: 你想要的引流风格
  qr: 底部二维码（可选）
  preferred_patterns:
    - 示例：「你怎么看，……？」
  avoid:
    - 鸡汤式大结尾
    - 「下篇聊」等编辑预告口吻

images:
  cover:
    enabled: true
    mood: 简洁/有情绪/强对比
  inline:
    enabled: true
    ratio: 16:9
    placement: 每个小标题正上方一张图
  rules:
    - 图片必须与本节内容直接相关
    - 不用AI生图
    - 无水印/无媒体Logo

banned_patterns:
  - 该账号绝对不能出现的表达方式
  - 示例：禁用「赋能」「闭环」「抓手」等黑话

sample_learnings:
  - 从你以往文章中总结的关键规则
  - 示例：我的读者喜欢具体案例，不爱听空泛分析

acceptance_criteria:
  - 标题能不能让人一眼想点？→ 能才算过
  - 正文会不会被读者跳过？→ 会就重写
  - 结尾有没有互动钩子？→ 没有就补
```

## 如何使用

1. **复制** 这个文件，重命名为 `style-你的号名.md`
2. **填空**：把 `你的公众号名` 替换为实际账号名，按你的文风修改每个字段
3. **注册**：在 `account-style-map.json` 中添加你的账号→style 映射
4. **使用**：以后说「用我的号写一篇关于XXX的」，系统自动按你的 style 出稿

> 想自动学习风格？给 5-10 篇你的文章链接，让系统帮你分析生成 style 文件。
> 详见 `style-learning-workflow.md`。
