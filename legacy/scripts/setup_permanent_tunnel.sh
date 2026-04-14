#!/bin/bash
#
# 设置永久 Cloudflare Tunnel
# 这会创建一个固定的 URL，不会变化
#

set -e

echo "========================================="
echo "  设置永久 Cloudflare Tunnel"
echo "========================================="
echo ""

CLOUDFLARED="/opt/homebrew/opt/cloudflared/bin/cloudflared"
CONFIG_DIR="$HOME/.cloudflared"
TUNNEL_NAME="apple-notes-mcp"

# 检查 cloudflared
if ! command -v $CLOUDFLARED &> /dev/null; then
    echo "❌ cloudflared 未安装"
    echo "   请运行: brew install cloudflared"
    exit 1
fi

echo "步骤 1/4: 登录 Cloudflare"
echo "浏览器会打开，请登录你的 Cloudflare 账号..."
echo ""
$CLOUDFLARED tunnel login

echo ""
echo "步骤 2/4: 创建隧道"
echo ""
$CLOUDFLARED tunnel create $TUNNEL_NAME

echo ""
echo "步骤 3/4: 获取隧道 ID"
TUNNEL_ID=$($CLOUDFLARED tunnel list | grep $TUNNEL_NAME | awk '{print $1}')
echo "隧道 ID: $TUNNEL_ID"

if [ -z "$TUNNEL_ID" ]; then
    echo "❌ 无法获取隧道 ID"
    exit 1
fi

echo ""
echo "步骤 4/4: 创建配置文件"
cat > $CONFIG_DIR/config.yml <<EOF
tunnel: $TUNNEL_ID
credentials-file: $CONFIG_DIR/$TUNNEL_ID.json

ingress:
  - service: http://localhost:8001
EOF

echo ""
echo "========================================="
echo "  ✅ 永久隧道设置完成！"
echo "========================================="
echo ""
echo "隧道名称: $TUNNEL_NAME"
echo "隧道 ID: $TUNNEL_ID"
echo ""
echo "下一步："
echo "1. 编辑 cloudflare-worker/wrangler.toml"
echo "2. 将 LOCAL_API_URL 设置为: https://$TUNNEL_ID.cfargotunnel.com"
echo "3. 重新部署: cd cloudflare-worker && npx wrangler deploy"
echo ""
echo "启动隧道："
echo "  $CLOUDFLARED tunnel run $TUNNEL_NAME"
echo ""
