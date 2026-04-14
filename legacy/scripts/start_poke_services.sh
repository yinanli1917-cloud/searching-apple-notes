#!/bin/bash
###############################################################################
# Apple Notes MCP + Poke AI 服务启动脚本
#
# 功能：
# 1. 启动 Python API 服务器 (localhost:8001)
# 2. 启动 Cloudflare Tunnel (公网访问)
# 3. 显示服务状态和访问 URL
#
# 使用：
#   ./start_poke_services.sh
#
# 停止服务：
#   按 Ctrl+C 停止所有服务
###############################################################################

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
API_PORT=8001
LOG_DIR="$SCRIPT_DIR/../logs"

# 创建日志目录
mkdir -p "$LOG_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Apple Notes MCP + Poke AI 服务启动  ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查 Python API 服务器
echo -e "${YELLOW}[1/3]${NC} 检查 Python 依赖..."
if ! /opt/homebrew/bin/python3.12 -c "import flask" 2>/dev/null; then
    echo -e "${RED}错误: Flask 未安装${NC}"
    echo "请运行: /opt/homebrew/bin/python3.12 -m pip install flask flask-cors --break-system-packages"
    exit 1
fi
echo -e "${GREEN}✓ Python 依赖已安装${NC}"

# 检查 Cloudflare Tunnel
echo -e "${YELLOW}[2/3]${NC} 检查 Cloudflare Tunnel..."
if ! command -v /opt/homebrew/opt/cloudflared/bin/cloudflared &> /dev/null; then
    echo -e "${RED}错误: cloudflared 未安装${NC}"
    echo "请运行: brew install cloudflared"
    exit 1
fi
echo -e "${GREEN}✓ Cloudflare Tunnel 已安装${NC}"

# 检查端口是否被占用
echo -e "${YELLOW}[3/3]${NC} 检查端口 $API_PORT..."
if lsof -Pi :$API_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠ 端口 $API_PORT 已被占用，尝试停止旧进程...${NC}"
    lsof -ti:$API_PORT | xargs kill -9 2>/dev/null || true
    sleep 1
fi
echo -e "${GREEN}✓ 端口 $API_PORT 可用${NC}"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  启动服务  ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 创建临时文件存储 Cloudflare Tunnel URL
TUNNEL_URL_FILE=$(mktemp)
trap "rm -f $TUNNEL_URL_FILE" EXIT

# 启动 Python API 服务器
echo -e "${GREEN}▶${NC} 启动 Python API 服务器 (端口 $API_PORT)..."
/opt/homebrew/bin/python3.12 "$SCRIPT_DIR/api_server.py" > "$LOG_DIR/api_server.log" 2>&1 &
API_PID=$!
echo -e "  ${BLUE}PID:${NC} $API_PID"
echo -e "  ${BLUE}日志:${NC} $LOG_DIR/api_server.log"

# 等待 API 服务器启动
sleep 3
if ! kill -0 $API_PID 2>/dev/null; then
    echo -e "${RED}✗ API 服务器启动失败${NC}"
    cat "$LOG_DIR/api_server.log"
    exit 1
fi
echo -e "${GREEN}✓ API 服务器运行中${NC}"
echo ""

# 启动 Cloudflare Tunnel
echo -e "${GREEN}▶${NC} 启动 Cloudflare Tunnel..."
/opt/homebrew/opt/cloudflared/bin/cloudflared tunnel --url http://localhost:$API_PORT > "$LOG_DIR/cloudflare_tunnel.log" 2>&1 &
TUNNEL_PID=$!
echo -e "  ${BLUE}PID:${NC} $TUNNEL_PID"
echo -e "  ${BLUE}日志:${NC} $LOG_DIR/cloudflare_tunnel.log"

# 等待 Tunnel 启动并获取 URL
echo -e "${YELLOW}等待 Cloudflare Tunnel 生成 URL...${NC}"
for i in {1..15}; do
    sleep 1
    if grep -q "https://.*\.trycloudflare\.com" "$LOG_DIR/cloudflare_tunnel.log"; then
        TUNNEL_URL=$(grep -o "https://[^[:space:]]*\.trycloudflare\.com" "$LOG_DIR/cloudflare_tunnel.log" | head -1)
        echo "$TUNNEL_URL" > "$TUNNEL_URL_FILE"
        break
    fi
done

if [ ! -f "$TUNNEL_URL_FILE" ] || [ ! -s "$TUNNEL_URL_FILE" ]; then
    echo -e "${RED}✗ 无法获取 Cloudflare Tunnel URL${NC}"
    echo "请查看日志: $LOG_DIR/cloudflare_tunnel.log"
    kill $API_PID $TUNNEL_PID 2>/dev/null
    exit 1
fi

TUNNEL_URL=$(cat "$TUNNEL_URL_FILE")
echo -e "${GREEN}✓ Cloudflare Tunnel 运行中${NC}"
echo ""

# 显示服务信息
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  ✅ 所有服务已启动  ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}本地 API 服务器:${NC}"
echo -e "  http://localhost:$API_PORT"
echo ""
echo -e "${GREEN}公网访问地址 (Cloudflare Tunnel):${NC}"
echo -e "  ${YELLOW}$TUNNEL_URL${NC}"
echo ""
echo -e "${GREEN}Poke AI 配置:${NC}"
echo -e "  MCP Server URL: ${YELLOW}https://apple-notes-mcp.yinanli1917.workers.dev/sse${NC}"
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  重要提示  ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}1. Cloudflare Tunnel URL 会在每次启动时改变${NC}"
echo -e "${YELLOW}2. 如果 URL 改变，需要更新 wrangler.toml 并重新部署:${NC}"
echo ""
echo -e "   ${BLUE}cd ~/Documents/apple-notes-mcp/cloudflare-worker${NC}"
echo -e "   ${BLUE}# 编辑 wrangler.toml，更新 LOCAL_API_URL 为上面的 URL${NC}"
echo -e "   ${BLUE}npx wrangler deploy${NC}"
echo ""
echo -e "${YELLOW}3. 按 Ctrl+C 停止所有服务${NC}"
echo ""
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}服务运行中... 日志实时输出:${NC}"
echo ""

# 清理函数
cleanup() {
    echo ""
    echo -e "${YELLOW}正在停止服务...${NC}"
    kill $API_PID $TUNNEL_PID 2>/dev/null || true
    echo -e "${GREEN}✓ 所有服务已停止${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# 实时显示日志
tail -f "$LOG_DIR/api_server.log" "$LOG_DIR/cloudflare_tunnel.log" &
TAIL_PID=$!

# 等待信号
wait $API_PID $TUNNEL_PID
