# Poke AI 集成指南 / Poke AI Integration Guide

[中文](#中文) | [English](#english)

---

## 中文

### 系统概览

**Apple Notes MCP 系统**:
- 920 条笔记已索引
- BGE-M3 模型（1024 维向量）
- 87% 搜索准确率
- 支持中英文混合语义搜索

**技术架构**:
```
Poke AI (iMessage/iPhone)
    ↓ HTTPS
Cloudflare Workers (全球边缘网络)
    ↓ HTTPS
Cloudflare Tunnel (公网隧道)
    ↓ HTTP
Python API Server (本地 Mac)
    ↓
BGE-M3 Model + ChromaDB (语义搜索)
    ↓
Apple Notes 数据库
```

### 快速开始

#### 步骤 1: 启动服务

使用提供的启动脚本一键启动所有服务：

```bash
cd ~/Documents/apple-notes-mcp/scripts
./start_poke_services.sh
```

**脚本会自动**:
1. 检查依赖（Python Flask、Cloudflare Tunnel）
2. 启动 Python API 服务器（端口 8001）
3. 启动 Cloudflare Tunnel（生成公网 URL）
4. 显示所有服务状态和 URL

**输出示例**:
```
========================================
  ✅ 所有服务已启动
========================================

本地 API 服务器:
  http://localhost:8001

公网访问地址 (Cloudflare Tunnel):
  https://secret-rolls-stories-substances.trycloudflare.com

Poke AI 配置:
  MCP Server URL: https://apple-notes-mcp.yinanli1917.workers.dev/sse

========================================
  重要提示
========================================

1. Cloudflare Tunnel URL 会在每次启动时改变
2. 如果 URL 改变，需要更新 wrangler.toml 并重新部署:

   cd ~/Documents/apple-notes-mcp/cloudflare-worker
   # 编辑 wrangler.toml，更新 LOCAL_API_URL 为上面的 URL
   npx wrangler deploy

3. 按 Ctrl+C 停止所有服务
```

#### 步骤 2: 更新 Cloudflare Workers（如果 Tunnel URL 变化）

如果 Cloudflare Tunnel URL 改变了（每次重启都会改变），需要：

1. 编辑 [cloudflare-worker/wrangler.toml](../cloudflare-worker/wrangler.toml)：
   ```toml
   [vars]
   ENVIRONMENT = "production"
   LOCAL_API_URL = "https://新的-tunnel-url.trycloudflare.com"
   ```

2. 重新部署：
   ```bash
   cd ~/Documents/apple-notes-mcp/cloudflare-worker
   npx wrangler deploy
   ```

#### 步骤 3: 在 Poke AI 中配置

1. 打开 Poke AI 应用（iPhone/iMessage）
2. 进入 Settings → Connections → Integrations → New Integration
3. 填写信息：
   - **Name**: `Apple Notes Search`
   - **Server URL**: `https://apple-notes-mcp.yinanli1917.workers.dev/sse`
   - **API Key**: *(留空)*
4. 点击 "Create Integration"

#### 步骤 4: 开始使用

**示例对话**:

```
你: 搜索幽默搞笑的内容
Poke: 🔍 搜索: "幽默搞笑的内容"

找到 5 个相关结果：

1. **笑话** (95% 匹配)
   📅 2024-03-15
   这里是一些有趣的笑话内容...

2. **笑大家** (87% 匹配)
   📅 2024-02-20
   更多搞笑段子...

💡 提示：可以在 Mac 的备忘录应用中查看完整内容

你: 查看统计信息
Poke: 📊 Apple Notes 统计信息

✅ 已索引笔记: 920 条
✅ 嵌入模型: BGE-M3
✅ 向量维度: 1024
✅ 状态: 就绪

🎯 系统信息:
- MCP 协议: 官方 SDK
- 传输方式: SSE (Server-Sent Events)
- 部署平台: Cloudflare Workers
- 本地搜索: 局域网 API (BGE-M3)
```

---

### 可用工具

Poke AI 可以调用以下 2 个 MCP 工具：

#### 1. search_notes
**功能**: 使用 AI 语义搜索备忘录

**参数**:
- `query` (必需): 搜索关键词（支持自然语言，如 "funny jokes"、"工作笔记"、"食谱"）
- `limit` (可选): 返回结果数（默认 5，最多 20）

**示例**:
- "搜索幽默"
- "找一找关于美国政治的笔记"
- "AI 相关的内容，返回 10 条"

#### 2. get_stats
**功能**: 查看系统统计信息

**返回信息**:
- 已索引笔记数
- 嵌入模型信息
- 向量维度
- 系统状态

**示例**:
- "查看备忘录统计"
- "有多少条笔记"

---

### 技术细节

#### 为什么需要 Cloudflare Tunnel？

**问题**: Cloudflare Workers 运行在云端，无法直接访问本地 IP 地址（如 `10.0.0.189:8001`）

**解决方案**:
1. **Cloudflare Tunnel** 将本地 API 服务器暴露到公网（HTTPS）
2. **Cloudflare Workers** 通过公网 URL 访问本地 API
3. **Python API** 调用本地的 BGE-M3 模型和 ChromaDB 进行搜索

#### 为什么不直接在 Cloudflare Workers 中运行 BGE-M3？

- BGE-M3 模型大小: ~2.3GB（包含词表）
- Cloudflare Workers 内存限制: 128MB
- Cloudflare Workers AI 嵌入模型维度较低，中文效果不如 BGE-M3

#### 架构优势

✅ **最佳性能**: 使用本地 BGE-M3 模型，搜索质量高（87% 准确率）
✅ **全球访问**: Cloudflare Workers 全球边缘网络，低延迟
✅ **免费使用**: Cloudflare 免费额度足够个人使用（100,000 请求/天）
✅ **隐私保护**: 笔记数据保留在本地，仅搜索结果通过网络传输

---

### 故障排除

#### 问题 1: Poke AI 报错 "无法连接到 MCP 服务器"

**检查清单**:
1. 确认服务启动脚本正在运行（不要关闭终端窗口）
2. 确认 Cloudflare Workers 已部署：
   ```bash
   curl https://apple-notes-mcp.yinanli1917.workers.dev/health
   ```
   应该返回 JSON 格式的健康检查信息

#### 问题 2: 搜索返回 "❌ 搜索失败: API returned 403"

**原因**: Cloudflare Tunnel URL 已过期或改变

**解决**:
1. 重启启动脚本，获取新的 Tunnel URL
2. 更新 `wrangler.toml` 中的 `LOCAL_API_URL`
3. 重新部署 Cloudflare Workers

#### 问题 3: 服务器启动慢

**原因**: BGE-M3 模型加载需要时间（首次启动约 10-15 秒）

**建议**:
- 让服务保持运行（不要频繁重启）
- 使用 tmux 或 nohup 后台运行

---

### 性能说明

**首次查询**:
- 模型加载时间: ~10 秒
- 查询时间: ~200-500ms

**后续查询**:
- 查询时间: ~100-200ms

**索引刷新**:
- 920 条笔记: ~3 分钟

---

### 安全说明

**当前配置**:
- ✅ Python API 只监听 `localhost:8001`（仅本地访问）
- ✅ Cloudflare Tunnel 使用 HTTPS 加密
- ✅ Cloudflare Workers 使用官方 SDK
- ⚠️ 无 API 密钥验证（信任所有请求）

**适用场景**:
- ✅ 个人使用
- ✅ 家庭局域网

**不适用场景**:
- ❌ 多用户公开访问

---

### 更新索引

当你在 Apple Notes 中添加新笔记后，需要重新索引：

```bash
cd ~/Documents/apple-notes-mcp/scripts

# 导出最新笔记
python3 export_notes_fixed.py

# 增量更新索引（只处理新笔记）
python3 indexer.py incremental

# 或者完全重建索引（耗时更长但更彻底）
python3 indexer.py full
```

索引更新后无需重启服务，下次搜索自动使用新数据。

---

## English

### System Overview

**Apple Notes MCP System**:
- 920 notes indexed
- BGE-M3 model (1024-dimensional vectors)
- 87% search accuracy
- Supports bilingual (Chinese/English) semantic search

**Technical Architecture**:
```
Poke AI (iMessage/iPhone)
    ↓ HTTPS
Cloudflare Workers (Global Edge Network)
    ↓ HTTPS
Cloudflare Tunnel (Public Tunnel)
    ↓ HTTP
Python API Server (Local Mac)
    ↓
BGE-M3 Model + ChromaDB (Semantic Search)
    ↓
Apple Notes Database
```

### Quick Start

#### Step 1: Start Services

Use the provided startup script to launch all services with one command:

```bash
cd ~/Documents/apple-notes-mcp/scripts
./start_poke_services.sh
```

**The script automatically**:
1. Checks dependencies (Python Flask, Cloudflare Tunnel)
2. Starts Python API server (port 8001)
3. Starts Cloudflare Tunnel (generates public URL)
4. Displays all service statuses and URLs

#### Step 2: Update Cloudflare Workers (if Tunnel URL changes)

If the Cloudflare Tunnel URL changes (it changes every restart):

1. Edit [cloudflare-worker/wrangler.toml](../cloudflare-worker/wrangler.toml):
   ```toml
   [vars]
   ENVIRONMENT = "production"
   LOCAL_API_URL = "https://new-tunnel-url.trycloudflare.com"
   ```

2. Redeploy:
   ```bash
   cd ~/Documents/apple-notes-mcp/cloudflare-worker
   npx wrangler deploy
   ```

#### Step 3: Configure in Poke AI

1. Open Poke AI app (iPhone/iMessage)
2. Go to Settings → Connections → Integrations → New Integration
3. Fill in:
   - **Name**: `Apple Notes Search`
   - **Server URL**: `https://apple-notes-mcp.yinanli1917.workers.dev/sse`
   - **API Key**: *(leave empty)*
4. Click "Create Integration"

#### Step 4: Start Using

**Example Conversation**:

```
You: Search for funny content
Poke: 🔍 Search: "funny content"

Found 5 relevant results:

1. **Jokes** (95% match)
   📅 2024-03-15
   Here are some funny jokes...

2. **Humor** (87% match)
   📅 2024-02-20
   More funny stuff...

💡 Tip: You can view the full content in the Notes app on your Mac
```

---

### Available Tools

#### 1. search_notes
**Function**: Search notes using AI semantic search

**Parameters**:
- `query` (required): Search query (supports natural language)
- `limit` (optional): Maximum results (default 5, max 20)

#### 2. get_stats
**Function**: View system statistics

**Returns**:
- Indexed notes count
- Embedding model info
- Vector dimensions
- System status

---

### Technical Details

#### Why Cloudflare Tunnel?

**Problem**: Cloudflare Workers runs in the cloud and cannot access local IP addresses (e.g., `10.0.0.189:8001`)

**Solution**:
1. **Cloudflare Tunnel** exposes local API server to the internet (HTTPS)
2. **Cloudflare Workers** accesses local API via public URL
3. **Python API** calls local BGE-M3 model and ChromaDB for search

#### Architecture Benefits

✅ **Best Performance**: Uses local BGE-M3 model with high accuracy (87%)
✅ **Global Access**: Cloudflare Workers edge network, low latency
✅ **Free to Use**: Cloudflare free tier sufficient for personal use (100,000 requests/day)
✅ **Privacy**: Notes data stays local, only search results transmitted

---

### Troubleshooting

#### Issue 1: Poke AI cannot connect to MCP server

**Checklist**:
1. Confirm startup script is running (don't close the terminal)
2. Confirm Cloudflare Workers is deployed:
   ```bash
   curl https://apple-notes-mcp.yinanli1917.workers.dev/health
   ```

#### Issue 2: Search returns "❌ Search failed: API returned 403"

**Cause**: Cloudflare Tunnel URL expired or changed

**Solution**:
1. Restart startup script to get new Tunnel URL
2. Update `LOCAL_API_URL` in `wrangler.toml`
3. Redeploy Cloudflare Workers

---

### Performance

**First Query**:
- Model loading: ~10 seconds
- Query time: ~200-500ms

**Subsequent Queries**:
- Query time: ~100-200ms

---

### Updating the Index

When you add new notes in Apple Notes, reindex:

```bash
cd ~/Documents/apple-notes-mcp/scripts

# Export latest notes
python3 export_notes_fixed.py

# Incremental update (faster, only new notes)
python3 indexer.py incremental

# Full rebuild (slower but thorough)
python3 indexer.py full
```

No need to restart services after updating the index.

---

**最后更新 / Last Updated**: 2025-11-07
**版本 / Version**: 2.0
**状态 / Status**: ✅ 已成功集成 / Successfully Integrated
