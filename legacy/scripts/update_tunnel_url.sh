#!/bin/bash
#
# 自动更新 Cloudflare Workers 的 Tunnel URL
# 使用场景：Quick Tunnel URL 变化后，自动更新 wrangler.toml 并重新部署
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WORKER_DIR="$PROJECT_ROOT/cloudflare-worker"
WRANGLER_TOML="$WORKER_DIR/wrangler.toml"
LOG_FILE="$PROJECT_ROOT/logs/cloudflare_tunnel.log"

echo "========================================="
echo "  自动更新 Tunnel URL 并重新部署"
echo "========================================="

# 1. 从日志中提取最新的 Tunnel URL
echo "📡 从日志中提取 Tunnel URL..."

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ 日志文件不存在: $LOG_FILE"
    exit 1
fi

# 提取最新的 trycloudflare.com URL
TUNNEL_URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$LOG_FILE" | tail -1)

if [ -z "$TUNNEL_URL" ]; then
    echo "❌ 无法从日志中找到 Tunnel URL"
    echo "提示：请确保 Poke 服务正在运行"
    exit 1
fi

echo "✅ 找到 Tunnel URL: $TUNNEL_URL"

# 2. 检查是否需要更新
CURRENT_URL=$(grep "LOCAL_API_URL" "$WRANGLER_TOML" | grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' || echo "")

if [ "$CURRENT_URL" == "$TUNNEL_URL" ]; then
    echo "✅ URL 没有变化，无需更新"
    exit 0
fi

echo "🔄 URL 已变化，需要更新："
echo "   旧: $CURRENT_URL"
echo "   新: $TUNNEL_URL"

# 3. 更新 wrangler.toml
echo "📝 更新 wrangler.toml..."

# 使用 sed 替换 LOCAL_API_URL
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s|LOCAL_API_URL = \".*\"|LOCAL_API_URL = \"$TUNNEL_URL\"|" "$WRANGLER_TOML"
else
    # Linux
    sed -i "s|LOCAL_API_URL = \".*\"|LOCAL_API_URL = \"$TUNNEL_URL\"|" "$WRANGLER_TOML"
fi

echo "✅ wrangler.toml 已更新"

# 4. 重新部署 Cloudflare Workers
echo "🚀 重新部署 Cloudflare Workers..."

cd "$WORKER_DIR"
if npx wrangler deploy > /dev/null 2>&1; then
    echo "✅ Workers 部署成功！"
else
    echo "❌ Workers 部署失败"
    exit 1
fi

echo "========================================="
echo "✅ 更新完成！Poke AI 现在应该可以使用了"
echo "========================================="
echo ""
echo "📱 新的 Tunnel URL: $TUNNEL_URL"
echo "🌐 Poke AI URL: https://apple-notes-mcp.yinanli1917.workers.dev/sse"
echo ""

exit 0
