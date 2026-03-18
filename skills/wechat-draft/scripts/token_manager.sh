#!/bin/bash
# Token 管理器 - 自动获取和刷新微信公众号 access_token

set -e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_FILE="$SKILL_DIR/config.json"
CACHE_DIR="$HOME/.openclaw/cache/wechat-draft"
mkdir -p "$CACHE_DIR"

# 获取指定账号的 token
get_token() {
    local account_name="${1:-default}"
    
    # 读取配置
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "Error: config.json not found. Please copy config.example.json to config.json and configure it." >&2
        exit 1
    fi
    
    # 如果是 default，获取默认账号名
    if [ "$account_name" = "default" ]; then
        account_name=$(jq -r '.default' "$CONFIG_FILE")
    fi
    
    local appid=$(jq -r ".accounts[\"$account_name\"].appid" "$CONFIG_FILE")
    local secret=$(jq -r ".accounts[\"$account_name\"].secret" "$CONFIG_FILE")
    
    if [ "$appid" = "null" ] || [ "$secret" = "null" ]; then
        echo "Error: Account '$account_name' not found in config.json" >&2
        exit 1
    fi
    
    local cache_file="$CACHE_DIR/${account_name}_token.json"
    
    # 检查缓存
    if [ -f "$cache_file" ]; then
        local expires_at=$(jq -r '.expires_at' "$cache_file" 2>/dev/null || echo "0")
        local now=$(date +%s)
        
        if [ "$expires_at" -gt "$now" ]; then
            jq -r '.access_token' "$cache_file"
            return 0
        fi
    fi
    
    # 获取新 token
    local response=$(curl -s "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=$appid&secret=$secret")
    local access_token=$(echo "$response" | jq -r '.access_token')
    local expires_in=$(echo "$response" | jq -r '.expires_in')
    
    if [ "$access_token" = "null" ]; then
        echo "Error: Failed to get token: $response" >&2
        exit 1
    fi
    
    # 缓存（提前5分钟过期）
    local expires_at=$(($(date +%s) + expires_in - 300))
    echo "{\"access_token\":\"$access_token\",\"expires_at\":$expires_at}" > "$cache_file"
    
    echo "$access_token"
}

get_token "$@"
