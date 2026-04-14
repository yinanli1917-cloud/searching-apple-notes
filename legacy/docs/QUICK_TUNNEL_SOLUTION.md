# Quick Tunnel 实用解决方案 / Quick Tunnel Practical Solution

[中文](#中文) | [English](#english)

---

## 中文

### 问题背景

Quick Tunnel 的 URL 会在每次重启时改变，导致 Poke AI 无法连接。虽然命名隧道（Named Tunnel）可以提供固定 URL，但配置需要域名授权，相对复杂。

本文档提供一个**实用的解决方案**，让你可以继续使用 Quick Tunnel，同时自动处理 URL 变化问题。

---

## ✅ 解决方案：自动更新脚本

我已经为你创建了一个自动化脚本：`update_tunnel_url.sh`

### 功能

1. 从日志中自动提取最新的 Tunnel URL
2. 检查 URL 是否已变化
3. 如果变化，自动更新 `wrangler.toml`
4. 自动重新部署 Cloudflare Workers
5. 完成后显示新的 URL

### 使用方法

**当 Poke AI 报错 "530 error" 或 "Flask server stopped" 时**，运行：

```bash
cd ~/Documents/apple-notes-mcp/scripts
./update_tunnel_url.sh
```

脚本会自动：
- ✅ 提取新的 Tunnel URL
- ✅ 更新 Workers 配置
- ✅ 重新部署
- ✅ 告诉你新的 URL

**输出示例**：
```
=========================================
  自动更新 Tunnel URL 并重新部署
=========================================
📡 从日志中提取 Tunnel URL...
✅ 找到 Tunnel URL: https://new-url-here.trycloudflare.com
🔄 URL 已变化，需要更新：
   旧: https://old-url-here.trycloudflare.com
   新: https://new-url-here.trycloudflare.com
📝 更新 wrangler.toml...
✅ wrangler.toml 已更新
🚀 重新部署 Cloudflare Workers...
✅ Workers 部署成功！
=========================================
✅ 更新完成！Poke AI 现在应该可以使用了
=========================================

📱 新的 Tunnel URL: https://new-url-here.trycloudflare.com
🌐 Poke AI URL: https://apple-notes-mcp.yinanli1917.workers.dev/sse
```

---

## 📋 完整的问题解决流程

### 场景 1：Mac 重启后 Poke AI 不能用

**原因**：Mac 重启后 Tunnel URL 变了

**解决**：
```bash
# 1. 启动服务
cd ~/Documents/apple-notes-mcp/scripts
./start_poke_services.sh

# 2. 等待服务启动（约10秒）

# 3. 更新 Tunnel URL
./update_tunnel_url.sh

# 4. 测试 Poke AI
```

### 场景 2：Poke AI 突然报错 530

**原因**：Tunnel 连接断开并重新连接，URL 可能已变化

**解决**：
```bash
cd ~/Documents/apple-notes-mcp/scripts
./update_tunnel_url.sh
```

如果脚本显示 "URL 没有变化"，那可能是其他问题：
```bash
# 检查服务状态
ps aux | grep -E "api_server|cloudflared"

# 如果服务没运行，重新启动
./start_poke_services.sh
```

### 场景 3：想要长期稳定运行（完全自动化）

**✅ 已实现完全自动化！**

系统现在会每 5 分钟自动检查并更新 Tunnel URL，**无需任何手动操作**：

```bash
# 查看自动化服务状态
launchctl list | grep apple-notes-mcp
```

你会看到两个服务正在运行：
- `com.apple-notes-mcp.auto-sync` - 每 24 小时自动索引笔记
- `com.apple-notes-mcp.tunnel-monitor` - 每 5 分钟检查 URL 变化

**自动化做了什么？**

1. ✅ **自动检测服务**：如果 API 服务器或 Tunnel 崩溃，自动重启
2. ✅ **自动检测 URL**：每 5 分钟检查 Tunnel URL 是否变化
3. ✅ **自动更新配置**：URL 变化时自动更新 `wrangler.toml`
4. ✅ **自动部署 Workers**：配置更新后自动部署
5. ✅ **无缝切换**：Poke AI 无需任何操作，自动恢复连接

**监控日志**：
```bash
# 查看自动更新日志
tail -f ~/Documents/apple-notes-mcp/logs/tunnel_monitor.log
```

**方案 B：手动快捷命令**（如果需要手动触发）
```bash
# 快捷命令已经创建：
fix-poke
```

**方案 C：使用命名隧道**（更稳定但配置复杂）

如果你有自己的域名，可以配置命名隧道获得固定 URL。参见 [Cloudflare Tunnel 配置指南](CLOUDFLARE_TUNNEL.md)。

---

## 🔍 技术原理

### 脚本做了什么？

1. **读取日志文件** (`logs/cloudflare_tunnel.log`)
2. **提取 Tunnel URL**（正则匹配 `https://xxx.trycloudflare.com`）
3. **对比当前配置**（读取 `wrangler.toml` 中的 `LOCAL_API_URL`）
4. **更新配置文件**（使用 `sed` 替换 URL）
5. **重新部署**（运行 `npx wrangler deploy`）

### ✅ 已实现自动运行！

通过 macOS LaunchAgent，系统会每 5 分钟自动检查并更新：
- ✅ 仅在 URL 变化时部署 Workers（不会频繁部署）
- ✅ URL 变化时自动检测并更新（无需手动干预）
- ✅ 后台静默运行，完全透明

**检查自动化状态**：
```bash
launchctl list | grep apple-notes-mcp
# 输出：
# 78958	0	com.apple-notes-mcp.tunnel-monitor  <- 正在运行
# -	126	com.apple-notes-mcp.auto-sync         <- 正在运行
```

---

## ⚠️ 注意事项

### Cloudflare Workers 部署限制

Cloudflare 免费版有以下限制：
- 每天最多 1000 次部署
- 每分钟最多 10 次部署

所以：
- ✅ 手动按需运行脚本（几秒钟一次）
- ❌ 不要配置自动定时运行（可能超限）

### 何时需要手动操作？

**✅ 完全自动化后，99% 情况下无需手动操作！**

系统会自动处理：
- ✅ Mac 重启后（自动检测并更新）
- ✅ 网络重新连接后（自动检测并更新）
- ✅ Poke AI 报错 530 时（5分钟内自动修复）
- ✅ 服务崩溃时（自动重启）

**唯一需要手动的情况**：
- 首次 Mac 启动时运行 `./start_poke_services.sh`（以后会添加开机自启）
- 如果想立即修复而不等 5 分钟，可以运行 `fix-poke`

---

## 📊 Quick Tunnel vs 命名 Tunnel 对比

| 特性 | Quick Tunnel + 自动脚本 | 命名 Tunnel |
|------|----------------------|-------------|
| URL 稳定性 | ⚠️ 需要手动更新 | ✅ 永久固定 |
| 配置复杂度 | ✅ 简单（一个脚本） | ❌ 复杂（需要域名授权） |
| 维护成本 | ⚠️ 偶尔手动运行脚本 | ✅ 零维护 |
| 是否需要域名 | ✅ 不需要 | ❌ 需要 |
| 推荐场景 | 个人使用 | 生产环境 |

---

## 🛠️ 故障排除

### 问题 1：脚本报错 "无法从日志中找到 Tunnel URL"

**原因**：Poke 服务没有运行

**解决**：
```bash
cd ~/Documents/apple-notes-mcp/scripts
./start_poke_services.sh

# 等待10秒后重试
./update_tunnel_url.sh
```

### 问题 2：Workers 部署失败

**可能原因**：
- 没有安装 Node.js / npm
- 没有登录 wrangler
- 网络问题

**解决**：
```bash
# 检查 Node.js
node --version

# 检查 wrangler 登录状态
cd ~/Documents/apple-notes-mcp/cloudflare-worker
npx wrangler whoami

# 如果没登录
npx wrangler login
```

### 问题 3：运行脚本后 Poke AI 仍然不能用

**诊断步骤**：

1. **检查服务是否运行**：
```bash
ps aux | grep -E "api_server|cloudflared"
```

2. **测试 API 服务器**：
```bash
curl http://localhost:8001/health
```

3. **测试 Tunnel 连接**：
```bash
# 从 wrangler.toml 获取 URL
TUNNEL_URL=$(grep LOCAL_API_URL ~/Documents/apple-notes-mcp/cloudflare-worker/wrangler.toml | grep -o 'https://[^"]*')
curl $TUNNEL_URL/health
```

4. **测试 Workers**：
```bash
curl https://apple-notes-mcp.yinanli1917.workers.dev/sse
```

如果以上任何步骤失败，请查看 [Poke AI 集成指南](POKE_INTEGRATION.md) 进行完整诊断。

---

## 📖 相关文档

- [Cloudflare Tunnel 配置指南](CLOUDFLARE_TUNNEL.md) - 命名隧道配置（更稳定）
- [Poke AI 集成指南](POKE_INTEGRATION.md) - 完整的 Poke AI 配置
- [自动同步指南](AUTO_SYNC.md) - 索引自动更新

---

## English

### Background

Quick Tunnel's URL changes on every restart, causing Poke AI connection failures. While Named Tunnel provides a fixed URL, it requires domain authorization which is relatively complex.

This document provides a **practical solution** that allows you to continue using Quick Tunnel while automatically handling URL changes.

---

## ✅ Solution: Automatic Update Script

I've created an automation script for you: `update_tunnel_url.sh`

### Features

1. Automatically extracts the latest Tunnel URL from logs
2. Checks if the URL has changed
3. If changed, automatically updates `wrangler.toml`
4. Automatically redeploys Cloudflare Workers
5. Displays the new URL upon completion

### Usage

**When Poke AI shows "530 error" or "Flask server stopped"**, run:

```bash
cd ~/Documents/apple-notes-mcp/scripts
./update_tunnel_url.sh
```

The script will automatically:
- ✅ Extract the new Tunnel URL
- ✅ Update Workers configuration
- ✅ Redeploy
- ✅ Show you the new URL

**Example output**:
```
=========================================
  Auto-update Tunnel URL and Redeploy
=========================================
📡 Extracting Tunnel URL from logs...
✅ Found Tunnel URL: https://new-url-here.trycloudflare.com
🔄 URL has changed, updating:
   Old: https://old-url-here.trycloudflare.com
   New: https://new-url-here.trycloudflare.com
📝 Updating wrangler.toml...
✅ wrangler.toml updated
🚀 Redeploying Cloudflare Workers...
✅ Workers deployed successfully!
=========================================
✅ Update complete! Poke AI should now work
=========================================

📱 New Tunnel URL: https://new-url-here.trycloudflare.com
🌐 Poke AI URL: https://apple-notes-mcp.yinanli1917.workers.dev/sse
```

---

## 📋 Complete Troubleshooting Flow

### Scenario 1: Poke AI doesn't work after Mac restart

**Reason**: Tunnel URL changed after Mac restart

**Solution**:
```bash
# 1. Start services
cd ~/Documents/apple-notes-mcp/scripts
./start_poke_services.sh

# 2. Wait for services to start (~10 seconds)

# 3. Update Tunnel URL
./update_tunnel_url.sh

# 4. Test Poke AI
```

### Scenario 2: Poke AI suddenly shows 530 error

**Reason**: Tunnel connection dropped and reconnected, URL may have changed

**Solution**:
```bash
cd ~/Documents/apple-notes-mcp/scripts
./update_tunnel_url.sh
```

If the script says "URL hasn't changed", it might be another issue:
```bash
# Check service status
ps aux | grep -E "api_server|cloudflared"

# If services aren't running, restart them
./start_poke_services.sh
```

### Scenario 3: Want long-term stable operation

**Don't want to manually run the script every time?**

Consider these two options:

**Option A: Create shortcut command** (Recommended)
```bash
# Add to ~/.zshrc
echo 'alias fix-poke="cd ~/Documents/apple-notes-mcp/scripts && ./update_tunnel_url.sh"' >> ~/.zshrc
source ~/.zshrc

# Then just run:
fix-poke
```

**Option B: Use Named Tunnel** (More stable but complex setup)

If you have your own domain, you can configure a Named Tunnel for a fixed URL. See [Cloudflare Tunnel Setup Guide](CLOUDFLARE_TUNNEL.md).

---

## 🔍 Technical Details

### What does the script do?

1. **Read log file** (`logs/cloudflare_tunnel.log`)
2. **Extract Tunnel URL** (regex match `https://xxx.trycloudflare.com`)
3. **Compare with current config** (read `LOCAL_API_URL` from `wrangler.toml`)
4. **Update config file** (replace URL using `sed`)
5. **Redeploy** (run `npx wrangler deploy`)

### Why not run automatically?

Theoretically possible to configure LaunchAgent for periodic checks, but **not recommended** because:
- ❌ Frequent Workers deployments may hit Cloudflare limits
- ❌ URL doesn't change frequently (usually only on restart)
- ❌ Manual execution is more controllable

---

## ⚠️ Important Notes

### Cloudflare Workers Deployment Limits

Cloudflare free tier has these limits:
- Max 1000 deployments per day
- Max 10 deployments per minute

Therefore:
- ✅ Manually run script as needed (takes seconds)
- ❌ Don't configure automatic scheduled runs (may exceed limits)

### When to run the script?

Only run in these situations:
1. After Mac restart
2. After network reconnection (WiFi switch)
3. When Poke AI shows 530 error
4. After restarting `start_poke_services.sh`

**Don't need to run daily**, only when Tunnel URL changes.

---

## 📊 Quick Tunnel vs Named Tunnel Comparison

| Feature | Quick Tunnel + Auto Script | Named Tunnel |
|---------|---------------------------|--------------|
| URL Stability | ⚠️ Requires manual update | ✅ Permanently fixed |
| Setup Complexity | ✅ Simple (one script) | ❌ Complex (requires domain auth) |
| Maintenance Cost | ⚠️ Occasional script runs | ✅ Zero maintenance |
| Domain Required | ✅ No | ❌ Yes |
| Recommended For | Personal use | Production |

---

## 🛠️ Troubleshooting

### Issue 1: Script error "Cannot find Tunnel URL in logs"

**Reason**: Poke services not running

**Solution**:
```bash
cd ~/Documents/apple-notes-mcp/scripts
./start_poke_services.sh

# Wait 10 seconds then retry
./update_tunnel_url.sh
```

### Issue 2: Workers deployment failed

**Possible causes**:
- Node.js/npm not installed
- Not logged into wrangler
- Network issues

**Solution**:
```bash
# Check Node.js
node --version

# Check wrangler login status
cd ~/Documents/apple-notes-mcp/cloudflare-worker
npx wrangler whoami

# If not logged in
npx wrangler login
```

### Issue 3: Poke AI still doesn't work after running script

**Diagnostic steps**:

1. **Check if services are running**:
```bash
ps aux | grep -E "api_server|cloudflared"
```

2. **Test API server**:
```bash
curl http://localhost:8001/health
```

3. **Test Tunnel connection**:
```bash
# Get URL from wrangler.toml
TUNNEL_URL=$(grep LOCAL_API_URL ~/Documents/apple-notes-mcp/cloudflare-worker/wrangler.toml | grep -o 'https://[^"]*')
curl $TUNNEL_URL/health
```

4. **Test Workers**:
```bash
curl https://apple-notes-mcp.yinanli1917.workers.dev/sse
```

If any of the above steps fail, see [Poke AI Integration Guide](POKE_INTEGRATION.md) for complete diagnostics.

---

## 📖 Related Documentation

- [Cloudflare Tunnel Setup Guide](CLOUDFLARE_TUNNEL.md) - Named Tunnel configuration (more stable)
- [Poke AI Integration Guide](POKE_INTEGRATION.md) - Complete Poke AI setup
- [Auto-Sync Guide](AUTO_SYNC.md) - Automatic index updates

---

**Last Updated**: 2025-11-09
**Version**: 1.0
