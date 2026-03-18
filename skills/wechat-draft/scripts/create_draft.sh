#!/bin/bash
# 创建草稿到微信公众号

set -e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOKEN_SCRIPT="$SKILL_DIR/scripts/token_manager.sh"
UPLOAD_SCRIPT="$SKILL_DIR/scripts/upload_image.sh"

create_draft() {
    local title="$1"
    local content="$2"
    local account="${3:-default}"
    local author="${4:-}"
    local digest="${5:-}"
    local cover_image="${6:-}"
    
    local token=$("$TOKEN_SCRIPT" "$account")
    
    # 上传封面图
    local thumb_media_id=""
    if [ -n "$cover_image" ] && [ -f "$cover_image" ]; then
        thumb_media_id=$("$UPLOAD_SCRIPT" "$cover_image" "$account")
    else
        # 创建默认封面
        local default_cover="/tmp/wechat_default_cover_$$.jpg"
        convert -size 900x500 xc:white -pointsize 48 -fill black -gravity center \
            -annotate +0+0 "$(echo "$title" | head -c 20)" "$default_cover" 2>/dev/null || \
            convert -size 900x500 xc:white "$default_cover"
        thumb_media_id=$("$UPLOAD_SCRIPT" "$default_cover" "$account")
        rm -f "$default_cover"
    fi
    
    # 构建请求体
    local json=$(jq -n \
        --arg title "$title" \
        --arg author "$author" \
        --arg digest "$digest" \
        --arg content "$content" \
        --arg thumb "$thumb_media_id" \
        '{
            articles: [{
                title: $title,
                author: $author,
                digest: $digest,
                content: $content,
                thumb_media_id: $thumb,
                need_open_comment: 0,
                only_fans_can_comment: 0
            }]
        }')
    
    local response=$(curl -s -X POST \
        "https://api.weixin.qq.com/cgi-bin/draft/add?access_token=$token" \
        -H "Content-Type: application/json" \
        -d "$json")
    
    local media_id=$(echo "$response" | jq -r '.media_id')
    
    if [ "$media_id" = "null" ]; then
        echo "Error: $response" >&2
        exit 1
    fi
    
    echo "$media_id"
}

create_draft "$@"
