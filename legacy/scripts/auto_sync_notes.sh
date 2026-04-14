#!/bin/bash
#
# 自动同步 Apple Notes 索引
# 功能：定期导出笔记 → 增量更新索引
#

set -e

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$HOME/Documents/apple-notes-mcp/logs"
LOG_FILE="$LOG_DIR/auto_sync_$(date +%Y%m%d).log"
PYTHON="/opt/homebrew/bin/python3.12"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "========================================="
log "🔄 开始自动同步 Apple Notes 索引"
log "========================================="

# 1. 导出最新笔记
log "📤 步骤 1/2: 导出 Apple Notes..."
if $PYTHON "$SCRIPT_DIR/export_notes_fixed.py" >> "$LOG_FILE" 2>&1; then
    log "✅ 笔记导出成功"
else
    log "❌ 笔记导出失败，退出"
    exit 1
fi

# 2. 增量更新索引（无参数 = 增量索引）
log "🔍 步骤 2/2: 增量更新索引..."
if $PYTHON "$SCRIPT_DIR/indexer.py" >> "$LOG_FILE" 2>&1; then
    log "✅ 索引更新成功"
else
    log "❌ 索引更新失败"
    exit 1
fi

log "========================================="
log "🎉 自动同步完成！"
log "========================================="

# 清理旧日志（保留最近7天）
find "$LOG_DIR" -name "auto_sync_*.log" -mtime +7 -delete 2>/dev/null || true

exit 0
