#!/bin/bash
# 上传图片到微信素材库

set -e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOKEN_SCRIPT="$SKILL_DIR/scripts/token_manager.sh"

upload_image() {
    local image_path="$1"
    local account="${2:-default}"
    
    if [ ! -f "$image_path" ]; then
        echo "Error: Image file not found: $image_path" >&2
        exit 1
    fi
    
    local token=$("$TOKEN_SCRIPT" "$account")
    
    local response=$(curl -s -X POST \
        "https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=$token&type=image" \
        -F "media=@$image_path")
    
    local media_id=$(echo "$response" | jq -r '.media_id')
    
    if [ "$media_id" = "null" ]; then
        echo "Error: Upload failed: $response" >&2
        exit 1
    fi
    
    echo "$media_id"
}

upload_image "$@"
