# Style Schema（统一风格结构）

每个 style 文件建议统一包含以下字段：

```yaml
account_name: 公众号名称
style_id: style-a
positioning: 账号定位

core_goals:
  - 本风格的核心写作目标1
  - 本风格的核心写作目标2

title:
  length: 10-15 或 15-20 或 16-24
  style:
    - 悬念 / 利益 / 观点 / 冲突 / 反转
    - 可补充“先抓人，再给信息点”之类规则
  preferred_patterns:
    - 可选，列常见标题模式
  avoid:
    - 可选，列标题禁区

digest:
  length: 6-12 或 12-18 或 12-24
  style:
    - 钩子 / 信息差 / 结论型
  avoid:
    - 可选，列摘要禁区

opening:
  goal: 首段承担什么任务
  preferred_methods:
    - 情绪切入 / 问题切入 / 判断切入 / 场景切入
  preferred_patterns:
    - 先说结论……
    - 这瓜保熟吗？
  avoid:
    - 近日……
    - 随着……

body:
  paragraph_count: 4-5 / 10-18
  sentence_mode: one-sentence-per-paragraph / short-paragraph / normal
  tone:
    - sharp / steady / story / tutorial
    - 可同时写“口语化 / 真人化 / 判断型”等复合特征
  pacing: dense / medium / loose / medium-dense
  structure_templates:
    type_a:
      - 结构步骤1
      - 结构步骤2
    type_b:
      - 结构步骤1
      - 结构步骤2

language:
  characteristics:
    - 口语化程度
    - 是否允许反问/吐槽/转折句
    - 是否需要“翻译成人话”
  preferred_patterns:
    - 常见带路句/口头句式
  avoid:
    - 书面汇报腔
    - 机械教学腔
    - AI套话

narrative:
  goals:
    - 是否强调故事推进
    - 是否强调流程感
  required_features:
    - 至少一条主线
    - 中间有结构转折
    - 结尾有收束判断
  avoid:
    - 流水账
    - 前后重复
    - 发散跳跃

reasoning:
  style:
    - 判断如何嵌入事件
    - 是否强调具体变量/风险点/观察点
  preferred_output:
    - 观察点
    - 风险点
    - 判断框架
  avoid:
    - 大道理泛滥
    - 空泛正确话术

layout:
  paragraph_rule:
    - 1-2句一段 / 正常段落
    - 重点句是否单独成段
  section_titles:
    enabled: true/false
    style: 口语化带路句 / 正式标题 / 无小标题
    examples:
      - 示例1
      - 示例2
    avoid:
      - 首先/其次/最后
  fixed_modules:
    - 风险提示前置 / 正文主体 / 二维码 / 官网链接
  reading_feel:
    - 高频分段 / 强节奏 / 扫读友好

highlight:
  sentence: red-bold-italic / none / structure-first
  keyword: red-bold-italic / none / optional
  numbers: red-bold-italic / none / optional
  note:
    - 是否更依赖结构型重点而非视觉型重点

ending:
  article_close:
    - 正文收束方式1
    - 正文收束方式2
  hook: true/false
  cta_style: style-specific description / none
  qr: bottom / none
  website_link: required / optional / none
  preferred_patterns:
    - 可选，列结尾常用引流句式
  avoid:
    - 鸡汤式大结尾
    - 结论和广告混在一起

images:
  cover:
    enabled: true/false
    text: none / light
    mood: abstract-humorous / serious / clean / data-like / clean-hot-topic
  inline:
    enabled: true/false
    ratio: 16:9
    text: none
    placement: before-next-section-highlight / paragraph-end / section-transition / none
    variety: required / optional
  rules:
    - 图片承担什么作用（节奏切换/解释辅助/装饰）

banned_patterns:
  - 禁用句式1
  - 禁用句式2

sample_learnings:
  - 从样本中学到的关键规则1
  - 从样本中学到的关键规则2

acceptance_criteria:
  - 什么叫写得像
  - 什么叫排版对
  - 什么叫节奏自然

wechat:
  requires_appid_secret: true
  whitelist_required: true

tuzi:
  required: true/false
```

## 原则
- schema 要可执行，不要只写“更像真人”“更有感觉”这种虚词
- 每个字段都要能指导后续渲染或发布脚本
- style 不仅描述“长什么样”，还要描述“怎么写、怎么推进、什么不能写”
- 优先把“首段、人味、故事性、流程感、禁用AI腔”写成明确规则
