#!/usr/bin/env python3
import argparse
import json
import re
from collections import Counter
from pathlib import Path

TITLE_PATTERNS = {
    'question': r'[？?]',
    'exclaim': r'[！!]',
    'number': r'\d',
    'contrast': r'(不是|而是|却|但|其实|真相|反而)',
    'benefit': r'(赚钱|避坑|机会|方法|指南|增长|搞懂)',
    'conflict': r'(暴跌|崩盘|翻车|送命|收割|陷阱|骗局|割)',
}

TONE_WORDS = {
    'sharp': ['家人们', '老韭', '送命', '割', '坑', '上头', '接刀', '别碰', '吐槽', '荒诞'],
    'steady': ['建议', '可以', '需要', '风险', '关注', '观察', '判断'],
    'story': ['那天', '后来', '当时', '结果', '故事', '一个人'],
    'tutorial': ['第一', '第二', '步骤', '具体', '操作', '教程'],
}

CTA_WORDS = ['扫码', '进群', '关注', '点击', '获取更多', '继续聊', '欢迎', '交流']
QR_WORDS = ['二维码', '扫码', '进群']


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8') if path.exists() else ''


def split_nonempty_lines(text: str):
    return [line.strip() for line in text.splitlines() if line.strip()]


def detect_title(lines):
    if not lines:
        return ''
    first = lines[0]
    return first.lstrip('#').strip()


def detect_digest(lines, title):
    candidates = []
    for idx, line in enumerate(lines[1:8], start=1):
        if not line or line.startswith('##'):
            continue
        score = 0
        length = len(line)
        if 6 <= length <= 28:
            score += 3
        if idx <= 3:
            score += 2
        if not line.startswith('!!'):
            score += 1
        if any(x in line for x in ['摘要', '导语', '速看', '核心', '结论']):
            score += 2
        if length > 40:
            score -= 2
        candidates.append((score, line.strip()))
    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]
    return title[:18]


def line_is_highlight(line: str) -> bool:
    return any([
        'ff0000' in line.lower(),
        'color:#d0021b' in line.lower(),
        'red-bold-italic' in line.lower(),
        line.startswith('!!'),
        '🔴✨' in line,
    ])


def classify_tone(text: str):
    scores = {k: 0 for k in TONE_WORDS}
    for tone, words in TONE_WORDS.items():
        for w in words:
            scores[tone] += text.count(w)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else 'steady', scores


def estimate_sentence_mode(lines):
    short_lines = [ln for ln in lines if 6 <= len(ln) <= 40]
    if not lines:
        return 'normal'
    ratio = len(short_lines) / max(len(lines), 1)
    return 'one-sentence-per-paragraph' if ratio >= 0.65 else 'normal'


def estimate_paragraph_count(lines):
    body = lines[1:]
    if not body:
        return 1
    # 一句一段号：短句行数量更能代表真实段落数
    short_lines = [ln for ln in body if 6 <= len(ln) <= 42 and not ln.startswith('## ')]
    heading_lines = [ln for ln in body if ln.startswith('## ')]
    if len(short_lines) >= max(4, len(body) * 0.6):
        # 合并相邻 highlight / CTA 尾部，避免虚高
        tail_trim = sum(1 for ln in body[-4:] if any(w in ln for w in CTA_WORDS))
        return max(1, len(short_lines) - tail_trim)
    if heading_lines:
        return max(1, len(heading_lines))
    return max(1, round(len(body) / 4))


def detect_title_style(titles):
    counts = Counter()
    for title in titles:
        for name, pat in TITLE_PATTERNS.items():
            if re.search(pat, title):
                counts[name] += 1
    ordered = [k for k, _ in counts.most_common()]
    return ordered[:3] or ['statement']


def detect_cta(lines):
    tail = '\n'.join(lines[-8:])
    return any(w in tail for w in CTA_WORDS)


def detect_qr(lines):
    tail = '\n'.join(lines[-10:])
    return 'bottom' if any(w in tail for w in QR_WORDS) else 'none'


def detect_ending_style(lines):
    tail_lines = lines[-6:]
    tail_text = '\n'.join(tail_lines)
    if any('扫码' in ln or '进群' in ln for ln in tail_lines):
        return 'traffic-hook-group-cta'
    if any('关注' in ln or '点击' in ln for ln in tail_lines):
        return 'follow-or-click-cta'
    return 'none'


def infer_images(text, lines):
    cover_enabled = True
    inline_enabled = any(x in text for x in ['配图', '插图', '图片', '<img', 'img src', '文生图'])
    mood = 'abstract-humorous' if any(x in text for x in ['幽默', '搞笑', '讽刺']) else ('serious-clean' if any(x in text for x in ['数据', '分析', '复盘']) else '待学习')
    placement = 'before-next-section-highlight' if ('下一大段' in text or '重点句上方' in text) else ('paragraph-end' if inline_enabled else 'none')
    qr = 'bottom' if detect_qr(lines) == 'bottom' else 'none'
    return {
        'cover': {
            'enabled': cover_enabled,
            'text': 'light',
            'mood': mood,
        },
        'inline': {
            'enabled': inline_enabled,
            'ratio': '16:9',
            'text': 'none',
            'placement': placement,
            'variety': 'required' if inline_enabled else 'optional',
        },
        'qr': qr,
    }


def build_style_spec(account_name: str, sample_infos):
    titles = [s['title'] for s in sample_infos if s['title']]
    digests = [s['digest'] for s in sample_infos if s['digest']]
    all_lines = []
    all_text = []
    highlight_count = 0
    total_lines = 0
    para_counts = []

    for s in sample_infos:
        lines = s['lines']
        all_lines.extend(lines[1:])
        all_text.append(s['text'])
        total_lines += max(len(lines) - 1, 0)
        highlight_count += sum(1 for ln in lines if line_is_highlight(ln))
        para_counts.append(s['paragraph_count'])

    merged_text = '\n'.join(all_text)
    tone, tone_scores = classify_tone(merged_text)
    title_styles = detect_title_style(titles)
    avg_title_len = round(sum(len(t) for t in titles) / max(len(titles), 1))
    avg_digest_len = round(sum(len(d) for d in digests) / max(len(digests), 1)) if digests else 12
    sentence_mode = estimate_sentence_mode(all_lines)
    avg_para = round(sum(para_counts) / max(len(para_counts), 1))
    highlight_ratio = highlight_count / max(total_lines, 1)
    cta = detect_cta(all_lines)
    qr = detect_qr(all_lines)
    images = infer_images(merged_text, all_lines)
    ending_style = detect_ending_style(all_lines)

    spec = {
        'account_name': account_name,
        'style_id': 'style-a',
        'positioning': tone,
        'title': {
            'length': f'{max(8, avg_title_len-2)}-{avg_title_len+2}',
            'style': ' / '.join(title_styles),
        },
        'digest': {
            'length': f'{max(6, avg_digest_len-2)}-{avg_digest_len+2}',
            'style': 'hook / info-gap' if avg_digest_len <= 18 else 'summary',
        },
        'body': {
            'paragraph_count': f'{min(max(1, avg_para-1), avg_para+1)}-{max(max(1, avg_para-1), avg_para+1)}',
            'sentence_mode': sentence_mode,
            'tone': tone,
            'pacing': 'dense' if sentence_mode == 'one-sentence-per-paragraph' else 'medium',
        },
        'highlight': {
            'sentence': 'red-bold-italic' if highlight_ratio > 0.08 else 'none',
            'keyword': 'red-bold-italic' if highlight_ratio > 0.08 else 'none',
            'numbers': 'red-bold-italic' if any(re.search(r'\d', t) for t in titles + digests + all_lines) else 'none',
        },
        'ending': {
            'hook': cta,
            'cta_style': ending_style if cta else 'none',
            'qr': qr,
        },
        'images': images,
        'wechat': {
            'requires_appid_secret': True,
            'whitelist_required': True,
        },
        'tuzi': {
            'required': True,
        },
        'analysis': {
            'sample_count': len(sample_infos),
            'avg_title_length': avg_title_len,
            'avg_digest_length': avg_digest_len,
            'tone_scores': tone_scores,
            'highlight_ratio': round(highlight_ratio, 3),
        }
    }
    return spec


def format_style_markdown(spec):
    return f"""# {spec['style_id']}

```yaml
account_name: {spec['account_name']}
style_id: {spec['style_id']}
positioning: {spec['positioning']}

title:
  length: {spec['title']['length']}
  style: {spec['title']['style']}

digest:
  length: {spec['digest']['length']}
  style: {spec['digest']['style']}

body:
  paragraph_count: {spec['body']['paragraph_count']}
  sentence_mode: {spec['body']['sentence_mode']}
  tone: {spec['body']['tone']}
  pacing: {spec['body']['pacing']}

highlight:
  sentence: {spec['highlight']['sentence']}
  keyword: {spec['highlight']['keyword']}
  numbers: {spec['highlight']['numbers']}

ending:
  hook: {str(spec['ending']['hook']).lower()}
  cta_style: {spec['ending']['cta_style']}
  qr: {spec['ending']['qr']}

images:
  cover:
    enabled: {str(spec['images']['cover']['enabled']).lower()}
    text: {spec['images']['cover']['text']}
    mood: {spec['images']['cover']['mood']}
  inline:
    enabled: {str(spec['images']['inline']['enabled']).lower()}
    ratio: {spec['images']['inline']['ratio']}
    text: {spec['images']['inline']['text']}
    placement: {spec['images']['inline']['placement']}
    variety: {spec['images']['inline']['variety']}

wechat:
  requires_appid_secret: true
  whitelist_required: true

tuzi:
  required: true
```
"""


def update_account_style_map(map_path: Path, account_name: str, style_id: str):
    data = {"default": "style-a", "accounts": {}}
    if map_path.exists():
        try:
            data = json.loads(map_path.read_text(encoding='utf-8'))
        except Exception:
            pass
    if 'accounts' not in data or not isinstance(data['accounts'], dict):
        data['accounts'] = {}
    data['accounts'][account_name] = style_id
    map_path.parent.mkdir(parents=True, exist_ok=True)
    map_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    return data


def main():
    parser = argparse.ArgumentParser(description='Learn style from 5-10 WeChat article samples')
    parser.add_argument('--account-name', required=True)
    parser.add_argument('--inputs', nargs='+', required=True, help='Paths to article sample files')
    parser.add_argument('--style-id', default='style-a')
    parser.add_argument('--output', help='Optional output style markdown path')
    parser.add_argument('--map-path', default='skills/wechat-style-publisher/references/styles/account-style-map.json')
    parser.add_argument('--write-map', action='store_true')
    args = parser.parse_args()

    sample_infos = []
    for path in args.inputs:
        p = Path(path)
        text = read_text(p)
        lines = split_nonempty_lines(text)
        title = detect_title(lines)
        digest = detect_digest(lines, title)
        sample_infos.append({
            'path': str(p),
            'chars': len(text),
            'text': text,
            'lines': lines,
            'title': title,
            'digest': digest,
            'paragraph_count': estimate_paragraph_count(lines),
        })

    spec = build_style_spec(args.account_name, sample_infos)
    spec['style_id'] = args.style_id
    spec['analysis']['sample_count'] = len(sample_infos)
    style_markdown = format_style_markdown(spec)

    result = {
        'account_name': args.account_name,
        'style_id': args.style_id,
        'sample_count': len(sample_infos),
        'samples': [{'path': s['path'], 'chars': s['chars'], 'title': s['title']} for s in sample_infos],
        'spec': spec,
        'style_markdown': style_markdown,
    }

    output_path = args.output or f'skills/wechat-style-publisher/references/styles/{args.style_id}.md'
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(style_markdown, encoding='utf-8')
    result['output'] = str(out)

    if args.write_map:
        updated_map = update_account_style_map(Path(args.map_path), args.account_name, args.style_id)
        result['account_style_map'] = updated_map

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
