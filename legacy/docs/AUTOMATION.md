# 完全自动化方案 / Full Automation Solution

[中文](#中文) | [English](#english)

---

## 中文

### ✅ 已实现完全自动化！

你的 Apple Notes MCP 服务器现在是**完全自动化、一劳永逸**的！

---

## 🎯 自动化功能

### 1. 开机自动启动

Mac 启动后，所有服务自动运行，无需手动操作：

```bash
# 查看自动化服务状态
launchctl list | grep apple-notes-mcp
```

你会看到三个服务：
- ✅ `com.apple-notes-mcp.poke-services` - Poke AI 服务（API + Tunnel）
- ✅ `com.apple-notes-mcp.auto-sync` - 自动索引笔记
- ✅ `com.apple-notes-mcp.tunnel-monitor` - 自动监控 URL 变化

### 2. 崩溃自动重启

如果任何服务崩溃，系统会自动重启，无需人工干预。

### 3. 自动索引更新

每 24 小时自动导出并索引新增/修改的笔记：
- 📅 运行时间：每天自动
- 📝 索引方式：增量索引（仅处理变化）
- 📊 当前状态：929 条笔记已索引

### 4. 自动 URL 监控和更新

每 5 分钟检查 Cloudflare Tunnel URL 是否变化：
- 🔍 检测 URL 变化
- 📝 自动更新 `wrangler.toml`
- 🚀 自动重新部署 Cloudflare Workers
- ✅ Poke AI 无缝恢复连接

---

## 📋 你需要做什么？

### 答案：**什么都不用做！**

系统会自动处理：
- ✅ Mac 重启后自动启动服务
- ✅ 服务崩溃后自动重启
- ✅ 笔记每天自动索引
- ✅ Tunnel URL 变化自动更新
- ✅ Poke AI 无需重新配置

### 唯一例外

如果你想**立即**修复 Tunnel URL 而不等 5 分钟，可以手动运行：

```bash
fix-poke
```

---

## 🔍 监控和日志

### 查看服务状态

```bash
# 查看所有服务
launchctl list | grep apple-notes-mcp

# 查看进程
ps aux | grep -E "api_server|cloudflared"
```

### 查看日志

```bash
# Poke 服务日志
tail -f ~/Documents/apple-notes-mcp/logs/poke_services_out.log

# 自动索引日志
tail -f ~/Documents/apple-notes-mcp/logs/auto_sync.log

# Tunnel 监控日志
tail -f ~/Documents/apple-notes-mcp/logs/tunnel_monitor.log

# Cloudflare Tunnel 日志
tail -f ~/Documents/apple-notes-mcp/logs/cloudflare_tunnel.log
```

---

## 🛠️ 管理命令

### 启动服务

服务会自动启动，但如果需要手动启动：

```bash
# 启动 Poke 服务（一般不需要）
launchctl start com.apple-notes-mcp.poke-services

# 或者手动运行脚本
cd ~/Documents/apple-notes-mcp/scripts
./start_poke_services.sh
```

### 停止服务

```bash
# 停止 Poke 服务
launchctl stop com.apple-notes-mcp.poke-services

# 停止自动索引
launchctl stop com.apple-notes-mcp.auto-sync

# 停止 Tunnel 监控
launchctl stop com.apple-notes-mcp.tunnel-monitor
```

### 卸载自动化

如果不想要自动化，可以卸载 LaunchAgents：

```bash
# 卸载 Poke 服务
launchctl unload ~/Library/LaunchAgents/com.apple-notes-mcp.poke-services.plist

# 卸载自动索引
launchctl unload ~/Library/LaunchAgents/com.apple-notes-mcp.auto-sync.plist

# 卸载 Tunnel 监控
launchctl unload ~/Library/LaunchAgents/com.apple-notes-mcp.tunnel-monitor.plist
```

---

## 📊 自动化架构

```
Mac 启动
  ↓
[LaunchAgent] com.apple-notes-mcp.poke-services
  ↓
启动 API 服务器 (localhost:8001)
  ↓
启动 Cloudflare Tunnel
  ↓
获得临时 URL (https://xxx.trycloudflare.com)
  ↓
[LaunchAgent] com.apple-notes-mcp.tunnel-monitor (每5分钟)
  ↓
检测 URL 是否变化
  ↓ (如果变化)
更新 wrangler.toml → 重新部署 Workers
  ↓
Poke AI 自动恢复连接
```

---

## 🎉 使用体验

### Mac 重启后

1. **你**：什么都不做，喝杯咖啡 ☕
2. **系统**：自动启动所有服务
3. **结果**：Poke AI 可以直接使用

### Tunnel URL 变化时

1. **你**：什么都不做，继续工作 💼
2. **系统**：5 分钟内自动检测并更新
3. **结果**：Poke AI 自动恢复连接

### 添加新笔记后

1. **你**：在备忘录中写笔记 ✍️
2. **系统**：24 小时内自动索引
3. **结果**：Poke AI 可以搜索到新笔记

---

## ⚠️ 注意事项

### Cloudflare Workers 部署限制

Cloudflare 免费版限制：
- 每天最多 1000 次部署
- 每分钟最多 10 次部署

**我们的方案不会超限**：
- ✅ 仅在 URL **真正变化**时部署
- ✅ 每 5 分钟检查一次（每天最多 288 次）
- ✅ 实际部署次数：每天 0-3 次（仅在 Mac 重启或网络切换时）

### Mac Sleep 影响

**短时间 Sleep（<1 小时）**：
- URL 通常不变
- 服务保持运行
- 无需任何操作

**长时间 Sleep（>1 小时）**：
- URL 可能变化
- 5 分钟内自动修复
- 无需手动操作

---

## 🆚 对比：自动化前 vs 自动化后

| 场景 | 自动化前 | 自动化后 |
|------|---------|---------|
| Mac 重启 | ❌ 手动运行脚本 | ✅ 自动启动 |
| 服务崩溃 | ❌ 手动重启 | ✅ 自动重启 |
| URL 变化 | ❌ 手动运行 `fix-poke` | ✅ 5分钟内自动修复 |
| 索引更新 | ❌ 手动运行索引脚本 | ✅ 每天自动更新 |
| Poke AI 配置 | ❌ 需要重新配置 | ✅ 永远不需要 |
| 日常维护 | ❌ 经常需要操作 | ✅ 完全无需操作 |

---

## 🔗 相关文档

- [Quick Tunnel 解决方案](QUICK_TUNNEL_SOLUTION.md) - URL 自动更新原理
- [Poke AI 集成指南](POKE_INTEGRATION.md) - Poke AI 配置
- [自动同步指南](AUTO_SYNC.md) - 自动索引配置
- [Cloudflare Tunnel 指南](CLOUDFLARE_TUNNEL.md) - Tunnel 详细配置

---

## English

### ✅ Full Automation Achieved!

Your Apple Notes MCP server is now **fully automated and maintenance-free**!

---

## 🎯 Automated Features

### 1. Auto-start on Boot

All services start automatically after Mac boot, no manual action needed:

```bash
# Check automation service status
launchctl list | grep apple-notes-mcp
```

You'll see three services:
- ✅ `com.apple-notes-mcp.poke-services` - Poke AI services (API + Tunnel)
- ✅ `com.apple-notes-mcp.auto-sync` - Auto-index notes
- ✅ `com.apple-notes-mcp.tunnel-monitor` - Auto-monitor URL changes

### 2. Auto-restart on Crash

If any service crashes, the system automatically restarts it.

### 3. Auto-index Updates

Automatically exports and indexes new/modified notes every 24 hours:
- 📅 Schedule: Daily
- 📝 Mode: Incremental (only processes changes)
- 📊 Current: 929 notes indexed

### 4. Auto URL Monitoring and Updates

Checks Cloudflare Tunnel URL every 5 minutes:
- 🔍 Detects URL changes
- 📝 Auto-updates `wrangler.toml`
- 🚀 Auto-redeploys Cloudflare Workers
- ✅ Poke AI seamlessly reconnects

---

## 📋 What Do You Need to Do?

### Answer: **Nothing!**

The system handles:
- ✅ Auto-start services after Mac restart
- ✅ Auto-restart after service crashes
- ✅ Auto-index notes daily
- ✅ Auto-update Tunnel URL changes
- ✅ Poke AI never needs reconfiguration

### Only Exception

If you want **immediate** Tunnel URL fix instead of waiting 5 minutes:

```bash
fix-poke
```

---

## 🔍 Monitoring and Logs

### Check Service Status

```bash
# View all services
launchctl list | grep apple-notes-mcp

# View processes
ps aux | grep -E "api_server|cloudflared"
```

### View Logs

```bash
# Poke services log
tail -f ~/Documents/apple-notes-mcp/logs/poke_services_out.log

# Auto-sync log
tail -f ~/Documents/apple-notes-mcp/logs/auto_sync.log

# Tunnel monitor log
tail -f ~/Documents/apple-notes-mcp/logs/tunnel_monitor.log

# Cloudflare Tunnel log
tail -f ~/Documents/apple-notes-mcp/logs/cloudflare_tunnel.log
```

---

## 🛠️ Management Commands

### Start Services

Services start automatically, but if needed:

```bash
# Start Poke services (usually not needed)
launchctl start com.apple-notes-mcp.poke-services

# Or run script manually
cd ~/Documents/apple-notes-mcp/scripts
./start_poke_services.sh
```

### Stop Services

```bash
# Stop Poke services
launchctl stop com.apple-notes-mcp.poke-services

# Stop auto-sync
launchctl stop com.apple-notes-mcp.auto-sync

# Stop tunnel monitor
launchctl stop com.apple-notes-mcp.tunnel-monitor
```

### Uninstall Automation

To disable automation:

```bash
# Unload Poke services
launchctl unload ~/Library/LaunchAgents/com.apple-notes-mcp.poke-services.plist

# Unload auto-sync
launchctl unload ~/Library/LaunchAgents/com.apple-notes-mcp.auto-sync.plist

# Unload tunnel monitor
launchctl unload ~/Library/LaunchAgents/com.apple-notes-mcp.tunnel-monitor.plist
```

---

## 📊 Automation Architecture

```
Mac Boot
  ↓
[LaunchAgent] com.apple-notes-mcp.poke-services
  ↓
Start API Server (localhost:8001)
  ↓
Start Cloudflare Tunnel
  ↓
Get Temporary URL (https://xxx.trycloudflare.com)
  ↓
[LaunchAgent] com.apple-notes-mcp.tunnel-monitor (every 5 min)
  ↓
Check if URL changed
  ↓ (if changed)
Update wrangler.toml → Redeploy Workers
  ↓
Poke AI auto-reconnects
```

---

## 🎉 User Experience

### After Mac Restart

1. **You**: Do nothing, grab a coffee ☕
2. **System**: Auto-starts all services
3. **Result**: Poke AI works immediately

### When Tunnel URL Changes

1. **You**: Do nothing, keep working 💼
2. **System**: Auto-detects and updates within 5 minutes
3. **Result**: Poke AI auto-reconnects

### After Adding New Notes

1. **You**: Write notes in Notes app ✍️
2. **System**: Auto-indexes within 24 hours
3. **Result**: Poke AI can search new notes

---

## ⚠️ Important Notes

### Cloudflare Workers Deployment Limits

Cloudflare free tier limits:
- Max 1000 deployments/day
- Max 10 deployments/minute

**Our solution stays within limits**:
- ✅ Deploys only when URL **actually changes**
- ✅ Checks every 5 minutes (max 288/day)
- ✅ Actual deployments: 0-3/day (only on Mac restart or network switch)

### Mac Sleep Impact

**Short Sleep (<1 hour)**:
- URL usually unchanged
- Services keep running
- No action needed

**Long Sleep (>1 hour)**:
- URL may change
- Auto-fixed within 5 minutes
- No manual action needed

---

## 🆚 Comparison: Before vs After Automation

| Scenario | Before | After |
|----------|--------|-------|
| Mac restart | ❌ Manual script run | ✅ Auto-start |
| Service crash | ❌ Manual restart | ✅ Auto-restart |
| URL change | ❌ Manual `fix-poke` | ✅ Auto-fix in 5 min |
| Index update | ❌ Manual indexing | ✅ Auto-update daily |
| Poke AI config | ❌ Re-configure | ✅ Never needed |
| Daily maintenance | ❌ Frequent action | ✅ Zero action |

---

## 🔗 Related Documentation

- [Quick Tunnel Solution](QUICK_TUNNEL_SOLUTION.md) - Auto URL update mechanism
- [Poke AI Integration Guide](POKE_INTEGRATION.md) - Poke AI setup
- [Auto-Sync Guide](AUTO_SYNC.md) - Auto-indexing setup
- [Cloudflare Tunnel Guide](CLOUDFLARE_TUNNEL.md) - Detailed Tunnel config

---

**最后更新 / Last Updated**: 2025-11-09
**版本 / Version**: 1.0
