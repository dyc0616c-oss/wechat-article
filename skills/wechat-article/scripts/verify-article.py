#!/usr/bin/env python3
"""
verify-article.py — 公众号文章交付前全面自检

用法:
    python3 scripts/verify-article.py <HTML文件路径>

输出:
    - 汉字数 / 标红数 / 句长检查 / 段落数 / 诗感检测
    - 图片完整性验证
    - 摘要长度检查
    - 最终 pass/fail 状态

句长计数规则（与标题/摘要统一）：
    英文字母按 3字母=1汉字 折算。
    例如 "Claude Code" (10字母) ≈ 4字。
    避免逐字母计数导致的误报。

通过标准:
    - 汉字数 600-900 (或按style要求)
    - 标红数 ≥ 8
    - 无超27字的句子 (折算后)
    - 无超过2句的段落
    - 无连续3段以上单句段落 (诗感)
    - 所有引用的图片文件在本地存在
"""

import re
import os
import sys


def char_len(s):
    """返回字符串的「折算字数」: 中文字/数字各算1字, 英文字母3个算1字"""
    cn = len(re.findall(r'[\u4e00-\u9fff0-9]', s))
    en = len(re.findall(r'[a-zA-Z]', s))
    return cn + en // 3


def verify(path):
    with open(path, encoding='utf-8') as f:
        html = f.read()

    errors = []
    warnings = []
    checks = {}

    # ── 1. 汉字数 ──
    cn_chars = len(re.findall(r'[\u4e00-\u9fff]', html))
    checks['汉字数'] = cn_chars
    if cn_chars < 600:
        errors.append(f'汉字数不足: {cn_chars}/600')
    elif cn_chars > 900:
        errors.append(f'汉字数超限: {cn_chars}/900')

    # ── 2. 标红数 ──
    hl_count = len(re.findall(r'class="hl"', html))
    checks['标红数'] = hl_count
    if hl_count < 8:
        errors.append(f'标红不足: {hl_count}/8')

    # ── 3. 句长检查 ──
    ps = re.findall(r'<p>(.*?)</p>', html, re.DOTALL)
    long_sentences = []
    for i, p in enumerate(ps):
        text = re.sub(r'<[^>]+>', '', p).strip()
        if not text:
            continue
        sents = [s.strip() for s in re.split(r'[。？！]', text) if s.strip()]
        for s in sents:
            cnt = char_len(s)
            if cnt > 27:
                long_sentences.append(f'  p{i+1}: {cnt}字 → {s[:50]}')
    checks['超长句数'] = len(long_sentences)
    if long_sentences:
        errors.append(f'超长句 {len(long_sentences)} 处:')
        for ls in long_sentences:
            errors.append(ls)

    # ── 4. 段落句数检查 ──
    multi_sent_paras = []
    for i, p in enumerate(ps):
        text = re.sub(r'<[^>]+>', '', p).strip()
        if not text:
            continue
        sents = [s.strip() for s in re.split(r'[。？！]', text) if s.strip()]
        if len(sents) > 2:
            multi_sent_paras.append(f'  p{i+1}: {len(sents)}句 → {sents[0][:20]}...')
    checks['超句段落数'] = len(multi_sent_paras)
    if multi_sent_paras:
        errors.append(f'超过2句的段落 {len(multi_sent_paras)} 处:')
        for m in multi_sent_paras:
            errors.append(m)

    # ── 5. 诗感检测 ──
    consecutive = 0
    max_consecutive = 0
    for p in ps:
        text = re.sub(r'<[^>]+>', '', p).strip()
        has_period = '。' in text or '！' in text or '？' in text
        if not has_period:
            consecutive += 1
            max_consecutive = max(max_consecutive, consecutive)
        else:
            consecutive = 0
    if max_consecutive >= 3:
        errors.append(f'诗感: 连续{max_consecutive}段单句段落')

    # ── 6. 图片验证 ──
    base_dir = os.path.dirname(path) or '.'
    imgs = re.findall(r'src="(?:图片/)?([^"]+\.(?:png|webp|jpg|jpeg))"', html)
    missing_imgs = []
    for img in imgs:
        img_path = os.path.join(base_dir, '图片', img) if not img.startswith('图片/') else os.path.join(base_dir, img)
        if not os.path.exists(img_path):
            missing_imgs.append(img)
    checks['图片总数'] = len(imgs)
    checks['缺失图片'] = len(missing_imgs)
    if missing_imgs:
        errors.append(f'图片缺失 {len(missing_imgs)} 张: {", ".join(missing_imgs)}')

    # ── 7. 摘要长度 ──
    sub_match = re.search(r'class="subtitle">(.*?)</p>', html)
    if sub_match:
        sub_text = sub_match.group(1)
        sub_len = char_len(sub_text)
        checks['摘要长度'] = sub_len
        if sub_len < 10 or sub_len > 15:
            errors.append(f'摘要字数不合规: {sub_len}字 (需10-15字) → "{sub_text}"')

    # ── 8. 段落总数 ──
    checks['段落数'] = len(ps)
    if len(ps) < 12:
        warnings.append(f'段落偏少: {len(ps)}段（建议12-20段）')
    elif len(ps) > 25:
        warnings.append(f'段落偏多: {len(ps)}段（建议12-20段）')

    # ── 输出结果 ──
    print('=' * 50)
    print(f'📄 验证: {os.path.basename(path)}')
    print('=' * 50)
    for k, v in checks.items():
        print(f'  {k}: {v}')
    print()

    if warnings:
        print('⚠️  提醒:')
        for w in warnings:
            print(f'  {w}')
        print()

    if errors:
        print('❌ 失败:')
        for e in errors:
            print(f'  {e}')
        print()
        print('🚦 状态: ❌ 不可交付 — 请修正后重新验证')
        return False
    else:
        print('✅ 全部通过!')
        print('🚦 状态: ✅ 可交付')
        return True


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python3 verify-article.py <HTML文件>')
        sys.exit(1)
    success = verify(sys.argv[1])
    sys.exit(0 if success else 1)
