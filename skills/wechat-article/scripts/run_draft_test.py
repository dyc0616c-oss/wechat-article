#!/usr/bin/env python3
import argparse
import json
import os
import re
import urllib.parse
import urllib.request
import uuid
from pathlib import Path


def load_style(style_path: Path):
    text = style_path.read_text(encoding='utf-8')
    m = re.search(r'```yaml\n(.*?)\n```', text, re.S)
    if not m:
        raise SystemExit(f'Could not find YAML block in {style_path}')
    yaml_text = m.group(1)
    data = {}
    stack = [data]
    indent_stack = [0]

    for raw in yaml_text.splitlines():
        if not raw.strip() or raw.strip().startswith('#'):
            continue
        indent = len(raw) - len(raw.lstrip(' '))
        line = raw.strip()
        while len(indent_stack) > 1 and indent < indent_stack[-1]:
            indent_stack.pop()
            stack.pop()
        if ':' not in line:
            continue
        key, value = line.split(':', 1)
        key = key.strip()
        value = value.strip()
        current = stack[-1]
        if value == '':
            current[key] = {}
            stack.append(current[key])
            indent_stack.append(indent + 2)
        else:
            if value.lower() == 'true':
                current[key] = True
            elif value.lower() == 'false':
                current[key] = False
            else:
                current[key] = value
    return data


def fetch_json(url, *, method='GET', headers=None, data=None, timeout=60):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8', 'ignore'))


def get_wechat_access_token():
    appid = os.getenv('WECHAT_APP_ID') or os.getenv('DASHU_MP_APP_ID')
    secret = os.getenv('WECHAT_APP_SECRET') or os.getenv('DASHU_MP_APP_SECRET')
    if not appid or not secret:
        raise SystemExit('Missing WECHAT_APP_ID/WECHAT_APP_SECRET (or legacy envs)')
    url = 'https://api.weixin.qq.com/cgi-bin/token?' + urllib.parse.urlencode({
        'grant_type': 'client_credential',
        'appid': appid,
        'secret': secret,
    })
    obj = fetch_json(url, timeout=30)
    if 'access_token' not in obj:
        raise SystemExit(f'Failed to get access_token: {json.dumps(obj, ensure_ascii=False)}')
    return obj['access_token']


def multipart_upload(url: str, file_path: Path, field: str = 'media'):
    boundary = '----OpenClawBoundary' + uuid.uuid4().hex
    file_bytes = file_path.read_bytes()
    content_type = 'image/jpeg' if file_path.suffix.lower() in ['.jpg', '.jpeg'] else 'image/png'
    body = b''.join([
        f'--{boundary}\r\n'.encode(),
        f'Content-Disposition: form-data; name="{field}"; filename="{file_path.name}"\r\n'.encode(),
        f'Content-Type: {content_type}\r\n\r\n'.encode(),
        file_bytes,
        b'\r\n',
        f'--{boundary}--\r\n'.encode(),
    ])
    return fetch_json(url, method='POST', headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}, data=body, timeout=120)


def create_simple_cover(title: str, output: Path):
    import subprocess
    svg = output.with_suffix('.svg')
    safe_title = title[:18]
    svg.write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="500">
<rect width="100%" height="100%" fill="#f5f5f5"/>
<rect x="40" y="40" width="820" height="420" rx="24" fill="#ffffff" stroke="#111111" stroke-width="4"/>
<text x="80" y="180" font-size="54" font-family="PingFang SC, Microsoft YaHei, Arial" fill="#111111">测试稿封面</text>
<text x="80" y="260" font-size="42" font-family="PingFang SC, Microsoft YaHei, Arial" fill="#d0021b">{safe_title}</text>
</svg>''', encoding='utf-8')
    png_out = output.with_suffix('.png')
    subprocess.run(['qlmanage', '-t', '-s', '900', '-o', str(output.parent), str(svg)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    generated = output.parent / (svg.name + '.png')
    if generated.exists():
        generated.rename(png_out)
    subprocess.run(['sips', '-s', 'format', 'jpeg', str(png_out), '--out', str(output)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output


def render_test_article(style: dict, source: str):
    account_name = style.get('account_name', '未命名公众号')
    title = f'按{account_name}风格测试稿怎么落地更顺'
    digest = f'测试来源：{source[:18]}'
    tone = style.get('body', {}).get('tone', 'steady')
    sentence_mode = style.get('body', {}).get('sentence_mode', 'normal')
    cta_style = style.get('ending', {}).get('cta_style', 'none')
    qr = style.get('ending', {}).get('qr', 'none')
    body_lines = [
        f'这是一篇按 {account_name} 当前 style 自动渲染的测试稿',
        f'当前 tone={tone}，sentence_mode={sentence_mode}',
        '第一步先验证 style 是否真的能指导出稿，而不是只停留在配置文件里',
        '第二步再逐步接文生图、正文图、二维码和草稿发布',
        '如果这版风格不像，优先回头修 style spec，而不是先怪发布脚本',
    ]
    if cta_style != 'none':
        body_lines.append(f'当前结尾 CTA 风格：{cta_style}')
    if qr == 'bottom':
        body_lines.append('当前 style 要求二维码落在全文最下面')
    return {
        'account_name': account_name,
        'source': source,
        'title': title,
        'digest': digest,
        'body_lines': body_lines,
        'qr': qr,
    }


def build_html(article: dict):
    parts = []
    for line in article['body_lines']:
        parts.append(f'<p style="line-height:1.75;margin:0 0 18px 0;">{line}</p>')
    parts.append('<p style="color:#0052ff;font-size:15px;font-weight:bold;font-style:italic;line-height:1.6;margin:18px 0 12px 0;">测试完成后 请去草稿箱查看风格是否像你的号</p>')
    parts.append('<p style="color:#666666;font-size:13px;line-height:1.6;margin:12px 0 12px 0;">合规声明：本文为测试草稿，不构成任何投资建议</p>')
    return ''.join(parts)


def create_draft(title: str, digest: str, html_content: str, thumb_media_id: str, source_url: str):
    access_token = get_wechat_access_token()
    payload = {
        'articles': [{
            'title': title,
            'author': 'OpenClaw',
            'digest': digest,
            'content': html_content,
            'content_source_url': source_url,
            'thumb_media_id': thumb_media_id,
            'need_open_comment': 0,
            'only_fans_can_comment': 0,
        }]
    }
    return fetch_json(
        'https://api.weixin.qq.com/cgi-bin/draft/add?access_token=' + urllib.parse.quote(access_token),
        method='POST',
        headers={'Content-Type': 'application/json; charset=utf-8'},
        data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
        timeout=120,
    )


def main():
    parser = argparse.ArgumentParser(description='Run MVP draft test for wechat-style-publisher')
    parser.add_argument('--style-id', required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--with-images', action='store_true')
    parser.add_argument('--style-path', help='Optional explicit style path')
    parser.add_argument('--publish', action='store_true', help='Actually create a WeChat draft')
    parser.add_argument('--runtime-dir', default='skills/wechat-style-publisher/runtime/test-publish')
    args = parser.parse_args()

    style_path = Path(args.style_path) if args.style_path else Path(f'skills/wechat-style-publisher/references/styles/{args.style_id}.md')
    style = load_style(style_path)
    article = render_test_article(style, args.source)
    html_content = build_html(article)

    result = {
        'style_id': args.style_id,
        'style_path': str(style_path),
        'with_images': args.with_images,
        'article': article,
        'html_preview': html_content[:500],
    }

    if args.publish:
        runtime_dir = Path(args.runtime_dir)
        runtime_dir.mkdir(parents=True, exist_ok=True)
        cover_path = create_simple_cover(article['title'], runtime_dir / 'test-cover.jpg')
        access_token = get_wechat_access_token()
        upload_resp = multipart_upload('https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=' + urllib.parse.quote(access_token) + '&type=image', cover_path)
        thumb_media_id = upload_resp.get('media_id')
        if not thumb_media_id:
            raise SystemExit(f'Cover upload failed: {json.dumps(upload_resp, ensure_ascii=False)}')
        draft_resp = create_draft(article['title'], article['digest'], html_content, thumb_media_id, args.source)
        result['publish'] = {
            'cover_path': str(cover_path),
            'thumb_media_id': thumb_media_id,
            'draft_response': draft_resp,
        }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
