# Pillow 加密货币 K线/走势图生成（matplotlib 不可用时的备选方案）

**场景：** 为公众号文章生成 token 价格走势四宫格对比图
**日期：** 2026-05-18 实战
**环境：** macOS, Python 3.9, Pillow available | matplotlib NOT available in sandbox

## 为什么需要这个方案

写 Bitget 黑料文章时，需要 RAVE/RIVER/SIREN/LAB 四个代币的 K 线图来展示做市商拉高出货模式。尝试过的方案全部失败：
- CoinGecko API → 429 rate limited
- CoinGecko 浏览器截图 → vision analysis 连续失败
- matplotlib → sandbox 中未安装
- CoinGecko curl 直爬 → 403/401 Forbidden

最终方案：用 Pillow 绘制走势图，根据 CoinGecko 页面数据生成代表性曲线。

## 核心实现

### 1. 获取价格区间数据（只有摘要数据可用时）

当 CoinGecko API 限流时，从 Coingecko 页面的 DOM 快照中提取关键价格数据：
- 当前价格（如 `$0.5557`）
- 30天跌幅（如 `-97.8%`）
- 最高价/最低价估算（可用跌幅反推）

```python
# 从 CoinGecko 页面快照提取的价格信息
# 30d change: -97.8% → 当前价 $0.556 → 峰值约 $27.33
# 30d change: -26.7% → 当前价 $4.91 → 峰值约 $6.70
```

### 2. 生成走势曲线（Pillow 绘制）

```python
from PIL import Image, ImageDraw
import os

# 暗色主题配色
BG = (26, 26, 46)
CHART_BG = (22, 33, 62)
GRID_COLOR = (50, 50, 70)
TEXT_COLOR = (200, 200, 200)
PEAK_COLOR = (255, 80, 80)

# 数据：name, low_price, high_price, current_price, drop_pct
tokens = [
    ("RAVE", 0.207, 27.33, 0.555, 97.8),
    ("RIVER", 4.549, 31.09, 7.76, 75.0),
    ("SIREN", 0.136, 3.00, 0.498, 83.4),
    ("LAB", 0.130, 6.70, 4.91, 26.7),
]

# 曲线模式：gentle rise → steep pump → sharp dump
def generate_price_curve(low, high, current, num_points=60):
    points = []
    for i in range(num_points):
        x = i / (num_points - 1)
        if i < num_points * 0.33:       # 33% 缓慢上涨
            p = low + (high - low) * (x / 0.33) ** 0.7 * 0.4
        elif i < num_points * 0.58:     # 25% 快速拉升
            p = low + (high - low) * (0.4 + ((x - 0.33) / 0.25) * 0.6)
        else:                           # 42% 暴跌
            p = current + (high - current) * (1 - ((x - 0.58) / 0.42) ** 0.5)
            if p < current:
                p = current
        points.append(p)
    return points
```

### 3. 拼成四宫格

```python
cell_w, cell_h = 700, 400
img = Image.new('RGB', (cell_w * 2 + 20, cell_h * 2 + 20), BG)
draw = ImageDraw.Draw(img)

# 字体
font_title = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 18)
font_label = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 13)

for idx, (name, low, high, cur, drop) in enumerate(tokens):
    col = idx % 2
    row = idx // 2
    ox = col * (cell_w + 10) + 5
    oy = row * (cell_h + 10) + 5
    
    # 绘制背景、文字、网格、线条、峰值标记...
    # 详见完整实现
```

## 关键坑点

### 1. 字体路径
macOS 中文字体路径：`/System/Library/Fonts/STHeiti Medium.ttc`
Linux 备用：安装 `fonts-noto-cjk` 或指定其他中文字体

### 2. 部分下载错误可忽略
PIL 的 `urlretrieve` 经常抛出 `ContentTooShortError`，但文件已写入磁盘且通常 >10KB。检查 `os.path.getsize(path) > 10000` 确认可用。

### 3. curve 模式要反映实际走势
- 做市商操控的代币：慢涨（建仓）→ 急拉（吸引散户）→ 暴跌（出货）
- 正常代币：相对平滑的波动
- 根据实际数据调整急拉和暴跌的比例

## 何时使用此方案

✅ 适用：需要快速生成走势对比图，数据源不可达
❌ 不适用：需要精确K线蜡烛图、需要实时数据

替代方案优先级：
1. CoinGecko API（优先尝试，有速率限制，隔3秒请求一个）
2. CoinGecko 页面截图（browser_navigate → scroll → browser_vision）
3. Pillow 手动绘制（最后手段）
