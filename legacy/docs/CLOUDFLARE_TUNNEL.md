# Cloudflare Tunnel 使用指南 / Cloudflare Tunnel Guide

[中文](#中文) | [English](#english)

---

## 中文

### 什么是 Cloudflare Tunnel？

Cloudflare Tunnel 是一个安全的方式将本地服务暴露到公网，无需打开防火墙端口或配置路由器。

**在 Apple Notes MCP 项目中的作用**:
- 将本地 Python API 服务器（`localhost:8001`）暴露到公网
- 提供 HTTPS 加密连接
- 允许 Cloudflare Workers 访问本地 BGE-M3 模型和 ChromaDB

### 架构图

```
┌─────────────────┐
│   Poke AI       │ (iPhone/iMessage)
│   (手机端)      │
└────────┬────────┘
         │ HTTPS
         ↓
┌─────────────────────────────┐
│  Cloudflare Workers         │ (全球边缘网络)
│  apple-notes-mcp            │
│  .yinanli1917.workers.dev   │
└────────┬────────────────────┘
         │ HTTPS
         ↓
┌─────────────────────────────┐
│  Cloudflare Tunnel          │ (公网隧道)
│  https://xxx.trycloudflare  │
│  .com                       │
└────────┬────────────────────┘
         │ HTTP (本地网络)
         ↓
┌─────────────────────────────┐
│  Python API Server          │ (Mac Studio 本地)
│  localhost:8001             │
│  ├─ Flask API               │
│  ├─ BGE-M3 Model            │
│  └─ ChromaDB                │
└─────────────────────────────┘
```

---

### 安装

Cloudflare Tunnel 已通过 Homebrew 安装在你的系统上：

```bash
brew install cloudflared
```

验证安装：
```bash
/opt/homebrew/opt/cloudflared/bin/cloudflared --version
```

---

### 使用方法

#### 方法 1: 使用启动脚本（推荐）

最简单的方式是使用提供的启动脚本，它会自动启动所有服务：

```bash
cd ~/Documents/apple-notes-mcp/scripts
./start_poke_services.sh
```

脚本会：
1. ✅ 检查依赖
2. ✅ 启动 Python API 服务器（端口 8001）
3. ✅ 启动 Cloudflare Tunnel
4. ✅ 自动提取并显示公网 URL
5. ✅ 提供部署指导

#### 方法 2: 手动启动（适合调试）

**1. 启动 Python API 服务器**:
```bash
cd ~/Documents/apple-notes-mcp/scripts
/opt/homebrew/bin/python3.12 api_server.py
```

**2. 在另一个终端窗口启动 Cloudflare Tunnel**:
```bash
/opt/homebrew/opt/cloudflared/bin/cloudflared tunnel --url http://localhost:8001
```

**3. 查看输出，找到公网 URL**:
```
2024-11-07T10:30:45Z INF +--------------------------------------------------------------------------------------------+
2024-11-07T10:30:45Z INF |  Your quick Tunnel has been created! Visit it at (it may take some time to be reachable):  |
2024-11-07T10:30:45Z INF |  https://secret-rolls-stories-substances.trycloudflare.com                                 |
2024-11-07T10:30:45Z INF +--------------------------------------------------------------------------------------------+
```

**4. 更新 Cloudflare Workers 配置**:

编辑 [cloudflare-worker/wrangler.toml](../cloudflare-worker/wrangler.toml):
```toml
[vars]
ENVIRONMENT = "production"
LOCAL_API_URL = "https://secret-rolls-stories-substances.trycloudflare.com"
```

**5. 重新部署 Cloudflare Workers**:
```bash
cd ~/Documents/apple-notes-mcp/cloudflare-worker
npx wrangler deploy
```

---

### 重要提示

#### ⚠️ Tunnel URL 会变化

**问题**: 每次重启 Cloudflare Tunnel，公网 URL 都会改变
- ❌ 旧 URL: `https://secret-rolls-stories-substances.trycloudflare.com`
- ✅ 新 URL: `https://different-words-example.trycloudflare.com`

**影响**:
- Cloudflare Workers 配置中的 `LOCAL_API_URL` 需要更新
- 必须重新部署 Cloudflare Workers

**解决方案**:
1. **使用启动脚本**: 脚本会显示当前 URL 和更新指导
2. **固定 Tunnel**: 配置命名 Tunnel（见下文"高级用法"）

#### 🔒 安全性

**当前配置（Quick Tunnel）**:
- ✅ HTTPS 加密
- ✅ 只暴露 API 端口（8001），不暴露整个系统
- ⚠️ URL 可被任何知道的人访问（无认证）
- ⚠️ URL 是临时的（重启后失效）

**适用场景**:
- ✅ 个人使用
- ✅ 开发和测试
- ✅ 家庭网络

**不适用场景**:
- ❌ 生产环境
- ❌ 多用户共享
- ❌ 需要持久 URL

---

### 高级用法：永久命名 Tunnel（推荐用于长期稳定运行）

#### 为什么需要命名 Tunnel？

**Quick Tunnel 的问题**:
- ❌ 每次重启 URL 都变化
- ❌ 连接不稳定，可能随时断开
- ❌ 需要频繁更新 `wrangler.toml` 并重新部署 Workers

**命名 Tunnel 的优势**:
- ✅ **URL 永久固定**，永远不会改变
- ✅ **自动重连机制**，网络中断后自动恢复
- ✅ **免费使用**，无需付费
- ✅ **一次配置**，长期稳定运行

#### 使用自动化脚本配置（推荐）

我已经为你准备了自动化配置脚本：

```bash
cd ~/Documents/apple-notes-mcp/scripts
./setup_permanent_tunnel.sh
```

脚本会引导你完成：
1. 登录 Cloudflare 账户（在浏览器中授权，仅需一次）
2. 创建命名隧道 `apple-notes-mcp`
3. 自动生成固定 URL（格式：`https://<tunnel-id>.cfargotunnel.com`）
4. 保存配置文件到 `~/.cloudflared/config.yml`

**完成后**，你会看到：
```
✅ 永久隧道设置完成！
隧道 ID: abc123def456
固定 URL: https://abc123def456.cfargotunnel.com

📋 接下来的步骤:
1. 更新 cloudflare-worker/wrangler.toml 中的 LOCAL_API_URL
2. 重新部署 Cloudflare Workers: npx wrangler deploy
3. 启动永久隧道: cloudflared tunnel run apple-notes-mcp
```

**这个 URL 永远不会改变！** 只需在 `wrangler.toml` 中配置一次。

#### 手动配置（如果脚本失败）

如果自动化脚本不工作，可以手动配置：

**1. 登录 Cloudflare**:
```bash
/opt/homebrew/opt/cloudflared/bin/cloudflared tunnel login
```

**2. 创建 Tunnel**:
```bash
/opt/homebrew/opt/cloudflared/bin/cloudflared tunnel create apple-notes-mcp
```

记下输出的 Tunnel ID（例如：`abc123def456`）

**3. 创建配置文件**:

创建 `~/.cloudflared/config.yml`：
```yaml
tunnel: abc123def456
credentials-file: ~/.cloudflared/abc123def456.json

ingress:
  - service: http://localhost:8001
```

**4. 获取固定 URL**:

你的固定 URL 是：`https://abc123def456.cfargotunnel.com`

**5. 更新 Workers 配置**:

编辑 `cloudflare-worker/wrangler.toml`：
```toml
[vars]
ENVIRONMENT = "production"
LOCAL_API_URL = "https://abc123def456.cfargotunnel.com"
```

**6. 重新部署 Workers（仅需一次）**:
```bash
cd ~/Documents/apple-notes-mcp/cloudflare-worker
npx wrangler deploy
```

**7. 启动永久隧道**:
```bash
/opt/homebrew/opt/cloudflared/bin/cloudflared tunnel run apple-notes-mcp
```

#### 作为后台服务运行

配置 macOS 启动时自动运行 Tunnel（可选）：

```bash
# 安装为系统服务
sudo /opt/homebrew/opt/cloudflared/bin/cloudflared service install

# 启动服务
sudo launchctl start com.cloudflare.cloudflared
```

#### 对比：Quick Tunnel vs 命名 Tunnel

| 特性 | Quick Tunnel | 命名 Tunnel |
|------|-------------|-------------|
| URL 稳定性 | ❌ 每次重启都变 | ✅ 永久固定 |
| 连接稳定性 | ⚠️ 可能断开 | ✅ 自动重连 |
| 配置复杂度 | ✅ 无需配置 | ⚠️ 一次配置 |
| 需要账号 | ✅ 不需要 | ⚠️ 需要（免费） |
| 维护成本 | ❌ 频繁更新 URL | ✅ 一劳永逸 |
| 推荐场景 | 临时测试 | **长期使用** |

**结论**: 如果你计划长期使用 Poke AI 集成，**强烈建议**配置命名 Tunnel。

---

### 监控和日志

#### 查看 Tunnel 日志

启动脚本会将日志保存到：
```bash
~/Documents/apple-notes-mcp/logs/cloudflare_tunnel.log
```

查看实时日志：
```bash
tail -f ~/Documents/apple-notes-mcp/logs/cloudflare_tunnel.log
```

#### 检查 Tunnel 状态

测试 Tunnel 是否正常工作：
```bash
# 替换为你的 Tunnel URL
curl https://secret-rolls-stories-substances.trycloudflare.com/health
```

应该返回：
```json
{
  "status": "running",
  "service": "Apple Notes Search API",
  "version": "1.0.0"
}
```

---

### 故障排除

#### 问题 1: Tunnel 无法启动

**错误**: "cloudflared: command not found"

**解决**:
```bash
brew install cloudflared
```

#### 问题 2: Tunnel 启动后无法访问

**检查清单**:
1. 确认 Python API 服务器正在运行：
   ```bash
   curl http://localhost:8001/health
   ```

2. 确认 Tunnel 日志中显示连接成功：
   ```bash
   tail -20 ~/Documents/apple-notes-mcp/logs/cloudflare_tunnel.log
   ```

3. 等待几秒钟让 Tunnel 建立连接（通常需要 5-10 秒）

#### 问题 3: Cloudflare Workers 报错 "403 Forbidden"

**原因**: Tunnel URL 已过期或改变

**解决**:
1. 重启启动脚本获取新 URL
2. 更新 `wrangler.toml`
3. 重新部署 Workers

#### 问题 4: Tunnel 频繁断开

**原因**: 网络不稳定或 Mac 休眠

**解决**:
1. 禁用 Mac 自动休眠（系统设置 → 节能）
2. 使用有线网络（而非 WiFi）
3. 配置命名 Tunnel 并使用 `keepalive` 设置

---

### 性能考虑

**延迟**:
- 本地 API 调用: ~10-50ms
- 通过 Tunnel: ~50-150ms（取决于地理位置）
- Cloudflare Workers 到 Tunnel: ~20-100ms

**总延迟（端到端）**:
- Poke AI → Cloudflare Workers → Tunnel → API → 响应: ~200-500ms

**带宽限制**:
- Cloudflare Tunnel 免费版: 无硬性限制
- 但建议合理使用（个人使用完全足够）

---

### 替代方案

如果 Cloudflare Tunnel 不适合你，可以考虑：

#### 1. ngrok
```bash
brew install ngrok
ngrok http 8001
```

**优点**: 简单易用
**缺点**: 免费版需要账号认证，URL 会变化

#### 2. Tailscale
**优点**: 点对点连接，更安全
**缺点**: 需要在 Cloudflare Workers 中配置（较复杂）

#### 3. 自建 VPS
**优点**: 完全控制
**缺点**: 需要服务器和维护

---

### 停止服务

#### 如果使用启动脚本

按 `Ctrl+C`，脚本会自动清理所有进程。

#### 如果手动启动

1. 找到 Tunnel 进程：
   ```bash
   ps aux | grep cloudflared
   ```

2. 停止进程：
   ```bash
   kill <PID>
   ```

---

## English

### What is Cloudflare Tunnel?

Cloudflare Tunnel is a secure way to expose local services to the internet without opening firewall ports or configuring routers.

**Purpose in Apple Notes MCP Project**:
- Exposes local Python API server (`localhost:8001`) to the internet
- Provides HTTPS encrypted connection
- Allows Cloudflare Workers to access local BGE-M3 model and ChromaDB

### Architecture

```
┌─────────────────┐
│   Poke AI       │ (iPhone/iMessage)
└────────┬────────┘
         │ HTTPS
         ↓
┌─────────────────────────────┐
│  Cloudflare Workers         │ (Global Edge Network)
│  apple-notes-mcp            │
│  .yinanli1917.workers.dev   │
└────────┬────────────────────┘
         │ HTTPS
         ↓
┌─────────────────────────────┐
│  Cloudflare Tunnel          │ (Public Tunnel)
│  https://xxx.trycloudflare  │
│  .com                       │
└────────┬────────────────────┘
         │ HTTP (Local Network)
         ↓
┌─────────────────────────────┐
│  Python API Server          │ (Mac Studio Local)
│  localhost:8001             │
│  ├─ Flask API               │
│  ├─ BGE-M3 Model            │
│  └─ ChromaDB                │
└─────────────────────────────┘
```

---

### Installation

Cloudflare Tunnel is already installed on your system via Homebrew:

```bash
brew install cloudflared
```

Verify installation:
```bash
/opt/homebrew/opt/cloudflared/bin/cloudflared --version
```

---

### Usage

#### Method 1: Using Startup Script (Recommended)

The easiest way is to use the provided startup script:

```bash
cd ~/Documents/apple-notes-mcp/scripts
./start_poke_services.sh
```

The script will:
1. ✅ Check dependencies
2. ✅ Start Python API server (port 8001)
3. ✅ Start Cloudflare Tunnel
4. ✅ Extract and display public URL
5. ✅ Provide deployment instructions

#### Method 2: Manual Start (For Debugging)

**1. Start Python API server**:
```bash
cd ~/Documents/apple-notes-mcp/scripts
/opt/homebrew/bin/python3.12 api_server.py
```

**2. Start Cloudflare Tunnel in another terminal**:
```bash
/opt/homebrew/opt/cloudflared/bin/cloudflared tunnel --url http://localhost:8001
```

**3. Find the public URL in the output**:
```
2024-11-07T10:30:45Z INF +--------------------------------------------------------------------------------------------+
2024-11-07T10:30:45Z INF |  Your quick Tunnel has been created! Visit it at (it may take some time to be reachable):  |
2024-11-07T10:30:45Z INF |  https://secret-rolls-stories-substances.trycloudflare.com                                 |
2024-11-07T10:30:45Z INF +--------------------------------------------------------------------------------------------+
```

**4. Update Cloudflare Workers configuration**:

Edit [cloudflare-worker/wrangler.toml](../cloudflare-worker/wrangler.toml):
```toml
[vars]
ENVIRONMENT = "production"
LOCAL_API_URL = "https://secret-rolls-stories-substances.trycloudflare.com"
```

**5. Redeploy Cloudflare Workers**:
```bash
cd ~/Documents/apple-notes-mcp/cloudflare-worker
npx wrangler deploy
```

---

### Important Notes

#### ⚠️ Tunnel URL Changes

**Issue**: Every time you restart Cloudflare Tunnel, the public URL changes
- ❌ Old URL: `https://secret-rolls-stories-substances.trycloudflare.com`
- ✅ New URL: `https://different-words-example.trycloudflare.com`

**Impact**:
- `LOCAL_API_URL` in Cloudflare Workers config needs updating
- Must redeploy Cloudflare Workers

**Solutions**:
1. **Use startup script**: Shows current URL and update instructions
2. **Configure named Tunnel**: See "Advanced Usage" below for permanent URL

#### 🔒 Security

**Current Configuration (Quick Tunnel)**:
- ✅ HTTPS encryption
- ✅ Only exposes API port (8001), not entire system
- ⚠️ URL accessible to anyone who knows it (no authentication)
- ⚠️ URL is temporary (expires after restart)

**Suitable For**:
- ✅ Personal use
- ✅ Development and testing
- ✅ Home network

**Not Suitable For**:
- ❌ Production environments
- ❌ Multi-user sharing
- ❌ Requires persistent URL

---

### Advanced Usage

#### Configure Named Tunnel (Fixed URL)

For a permanent URL:

**1. Login to Cloudflare**:
```bash
/opt/homebrew/opt/cloudflared/bin/cloudflared tunnel login
```

**2. Create Tunnel**:
```bash
/opt/homebrew/opt/cloudflared/bin/cloudflared tunnel create apple-notes-mcp
```

**3. Configure routing**:

Create config file `~/.cloudflared/config.yml`:
```yaml
tunnel: apple-notes-mcp
credentials-file: ~/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: apple-notes-api.yourdomain.com
    service: http://localhost:8001
  - service: http_status:404
```

**4. Create DNS record**:
```bash
/opt/homebrew/opt/cloudflared/bin/cloudflared tunnel route dns apple-notes-mcp apple-notes-api.yourdomain.com
```

**5. Run Tunnel**:
```bash
/opt/homebrew/opt/cloudflared/bin/cloudflared tunnel run apple-notes-mcp
```

**Pros**:
- ✅ Permanent URL
- ✅ Custom domain
- ✅ Supports multiple services

**Cons**:
- ❌ Requires owning a domain
- ❌ Requires Cloudflare account
- ❌ More complex configuration

---

### Monitoring and Logs

#### View Tunnel Logs

The startup script saves logs to:
```bash
~/Documents/apple-notes-mcp/logs/cloudflare_tunnel.log
```

View real-time logs:
```bash
tail -f ~/Documents/apple-notes-mcp/logs/cloudflare_tunnel.log
```

#### Check Tunnel Status

Test if Tunnel is working:
```bash
# Replace with your Tunnel URL
curl https://secret-rolls-stories-substances.trycloudflare.com/health
```

Should return:
```json
{
  "status": "running",
  "service": "Apple Notes Search API",
  "version": "1.0.0"
}
```

---

### Troubleshooting

#### Issue 1: Tunnel fails to start

**Error**: "cloudflared: command not found"

**Solution**:
```bash
brew install cloudflared
```

#### Issue 2: Tunnel starts but cannot access

**Checklist**:
1. Confirm Python API server is running:
   ```bash
   curl http://localhost:8001/health
   ```

2. Check Tunnel logs show successful connection:
   ```bash
   tail -20 ~/Documents/apple-notes-mcp/logs/cloudflare_tunnel.log
   ```

3. Wait a few seconds for Tunnel to establish (usually 5-10 seconds)

#### Issue 3: Cloudflare Workers returns "403 Forbidden"

**Cause**: Tunnel URL expired or changed

**Solution**:
1. Restart startup script to get new URL
2. Update `wrangler.toml`
3. Redeploy Workers

---

### Performance Considerations

**Latency**:
- Local API call: ~10-50ms
- Through Tunnel: ~50-150ms (depends on location)
- Cloudflare Workers to Tunnel: ~20-100ms

**Total Latency (End-to-End)**:
- Poke AI → Workers → Tunnel → API → Response: ~200-500ms

**Bandwidth**:
- Cloudflare Tunnel free tier: No hard limits
- Recommended for personal use only

---

### Alternatives

If Cloudflare Tunnel doesn't work for you:

#### 1. ngrok
```bash
brew install ngrok
ngrok http 8001
```

**Pros**: Simple to use
**Cons**: Free tier requires account, URL changes

#### 2. Tailscale
**Pros**: Peer-to-peer, more secure
**Cons**: Complex to configure with Cloudflare Workers

#### 3. Self-hosted VPS
**Pros**: Full control
**Cons**: Requires server and maintenance

---

### Stopping Services

#### If using startup script

Press `Ctrl+C`, the script will automatically clean up all processes.

#### If manually started

1. Find Tunnel process:
   ```bash
   ps aux | grep cloudflared
   ```

2. Stop process:
   ```bash
   kill <PID>
   ```

---

**最后更新 / Last Updated**: 2025-11-07
**版本 / Version**: 1.0
