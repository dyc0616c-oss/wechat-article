# Verify Failure Patterns — Quick Reference

> A one-command self-check to run BEFORE the first verify, targeting the top 5 failure modes.

## Top 5 Failure Modes (90%+ of verify failures)

| # | Mode | How to avoid on first draft | Fix command |
|---|------|-----------------------------|-------------|
| 1 | **汉字数不足 600** | Target min 700 chars on first write; always err on the side of too much content | `python3 -c "import re; h=open('article.html').read(); print(f'{len(re.findall(r\"[\u4e00-\u9fff]\",h))} chars')"` |
| 2 | **标红不足 < 8** | Mark every key data point, model name, and core judgment with `class="hl"` as you write; aim for 10-12 then trim | `grep -c 'class="hl"' article.html` |
| 3 | **超长句 > 27字** | Split sentences at every `，` that results in >20 Chinese chars per clause; English names count as 3 letters = 1 hanzi | Built into verify script |
| 4 | **超过2句段落** | After writing, merge consecutive short single-sentence `<p>` blocks into multi-sentence `<p>` where they share a topic; aim for exactly 2 sentences per `<p>` | `grep -oP '<p>[^<]{10,80}</p>' article.html \| head -5` |
| 5 | **诗感 (3+ consecutive single-sentence paragraphs)** | Check the article visually: if you see 3+ `<p>` tags in a row each with only 1 sentence, merge the middle one with a neighbor | Built into verify script |

## Quick Pre-Verify Check (run before first verify)

```bash
# 1. Character count
python3 -c "import re; h=open('article.html').read(); print(f'汉字数: {len(re.findall(r\"[\u4e00-\u9fff]\",h))}')"
# 2. Highlight count  
grep -c 'class="hl"' article.html
# 3. Check for banned patterns
grep -oP '不是……而是|看着像……其实是|真正要命的是|真正关键的是|这波最值得' article.html && echo "⚠️ BANNED PATTERN FOUND" || echo "✅ No banned patterns"
```

## Other Common Fixes

| Symptom | Root cause | Fix |
|---------|-----------|-----|
| Sentence falsely flagged as >27 chars (has `DeepSeek V4 Pro` etc.) | English name inflates char count | Verify script `char_len()` already handles 3-letter=1-hanzi. Don't split; trust the script. |
| 连续3段单句段落 | Three `<p>`s each with one sentence, often in footer or near section breaks | Merge two of them into one `<p>` with a comma or period connection |
| Missing images | Wrote `<img src="图片/X.jpg">` but never downloaded X.jpg | `curl -sLO <url>` before final verify |
