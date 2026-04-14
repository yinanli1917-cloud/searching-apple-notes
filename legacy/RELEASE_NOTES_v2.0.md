# Release Notes v2.0 - Poke AI Integration

**发布日期 / Release Date**: 2025-11-07

---

## 🎉 重大更新 / Major Updates

### ✅ Poke AI 集成成功 / Poke AI Integration

现在可以通过 iMessage 搜索你的 Apple Notes！

**新增功能**:
- 📱 通过 Poke AI (iMessage) 搜索备忘录
- ☁️ Cloudflare Workers 部署（全球边缘网络）
- 🔒 Cloudflare Tunnel 安全桥接
- 🚀 一键启动脚本
- 📚 完整的双语文档

---

## 🏗️ 技术架构 / Architecture

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
```

---

## 📦 新增文件 / New Files

### 核心实现 / Core Implementation
- `cloudflare-worker/` - Cloudflare Workers MCP 服务器（TypeScript）
  - `src/index.ts` - 主服务器实现
  - `package.json` - 依赖配置
  - `wrangler.toml` - Workers 配置
  - `tsconfig.json` - TypeScript 配置

- `scripts/api_server.py` - Python Flask API 服务器
  - 提供 `/health`, `/search`, `/stats` 端点
  - BGE-M3 模型集成
  - ChromaDB 向量搜索

- `scripts/start_poke_services.sh` - 一键启动脚本
  - 自动启动 API 服务器
  - 自动启动 Cloudflare Tunnel
  - URL 提取和部署指导

### 文档 / Documentation
- `docs/POKE_INTEGRATION.md` - Poke AI 完整集成指南
- `docs/CLOUDFLARE_TUNNEL.md` - Cloudflare Tunnel 使用指南
- `STATUS.md` - 项目状态和路线图

---

## 🚀 快速开始 / Quick Start

### Claude Desktop (本地)
保持原有配置，无需更改。

### Poke AI (iMessage)

1. **启动服务**:
   ```bash
   cd ~/Documents/apple-notes-mcp/scripts
   ./start_poke_services.sh
   ```

2. **配置 Poke AI**:
   - Server URL: `https://apple-notes-mcp.yinanli1917.workers.dev/sse`

3. **开始搜索**:
   - "搜索我的笔记里关于幽默搞笑的内容"

👉 [完整配置指南](docs/POKE_INTEGRATION.md)

---

## 📊 性能指标 / Performance

- **搜索准确率**: 87%（中文优化）
- **首次查询**: 10-15 秒（模型加载）+ 200-500ms
- **后续查询**: 100-200ms
- **端到端延迟**（Poke AI）: 200-500ms
- **索引容量**: 920 条笔记

---

## 🔧 技术栈 / Tech Stack

**核心搜索**:
- BGE-M3 (1024-dim vectors)
- ChromaDB
- Python 3.12

**新增集成**:
- Cloudflare Workers
- TypeScript 5.7.2
- @modelcontextprotocol/sdk 1.17.1
- Cloudflare Agents SDK (agents 0.2.21)
- Cloudflare Tunnel (cloudflared)
- Flask + Flask-CORS

---

## 📝 重要说明 / Important Notes

### Cloudflare Tunnel URL 会变化
每次重启 Tunnel，URL 都会改变。需要：
1. 更新 `wrangler.toml` 中的 `LOCAL_API_URL`
2. 重新部署 Cloudflare Workers

启动脚本会自动显示更新指导。

### 需要 Mac 保持运行
Poke AI 搜索需要本地服务保持运行：
- Python API Server (localhost:8001)
- Cloudflare Tunnel

建议使用 tmux 或后台运行。

---

## 🗑️ 弃用 / Deprecated

以下文件已移至 `archive/` 目录：
- ❌ `Dockerfile` - Railway 部署方案
- ❌ `fly.toml` - Fly.io 部署方案
- ❌ `start_poke_server.sh` - 旧启动脚本

**当前推荐部署**:
- ✅ Cloudflare Workers (Poke AI)
- ✅ 本地运行 (Claude Desktop)

---

## 🐛 已知问题 / Known Issues

1. **Cloudflare Tunnel URL 不固定**
   - 临时方案：使用 Quick Tunnel
   - 长期方案：配置命名 Tunnel（需要域名）

2. **无身份验证**
   - 当前无 API Key 验证
   - 仅适用个人使用
   - 计划在未来版本添加

3. **FastMCP 与 Poke AI 不兼容**
   - Python FastMCP SSE 实现与 Poke AI 不兼容
   - 已通过 Cloudflare Workers 方案解决

---

## 📖 完整文档 / Full Documentation

- [README.md](README.md) - 项目概览
- [Poke AI Integration Guide](docs/POKE_INTEGRATION.md)
- [Cloudflare Tunnel Setup](docs/CLOUDFLARE_TUNNEL.md)
- [Project Status](STATUS.md)
- [Technical Log](docs/PROJECT_LOG.md)

---

## 🙏 致谢 / Acknowledgments

**参考项目**:
- [poke-mcp](https://github.com/kaishin/poke-mcp) - Poke AI MCP 集成参考实现

**使用的开源项目**:
- [Cloudflare Workers](https://workers.cloudflare.com/)
- [@modelcontextprotocol/sdk](https://github.com/modelcontextprotocol/sdk)
- [BGE-M3](https://github.com/FlagOpen/FlagEmbedding)
- [ChromaDB](https://www.trychroma.com/)
- [Flask](https://flask.palletsprojects.com/)

---

## 📜 版本历史 / Version History

### v2.0 (2025-11-07) - Poke AI Integration
- ✅ Poke AI (iMessage) 集成
- ✅ Cloudflare Workers 部署
- ✅ Cloudflare Tunnel 桥接
- ✅ Python Flask API 服务器
- ✅ 一键启动脚本
- ✅ 完整双语文档

### v1.0 (2024-03-15) - Initial Release
- ✅ Claude Desktop 集成
- ✅ BGE-M3 语义搜索
- ✅ ChromaDB 向量数据库
- ✅ Python FastMCP 服务器

---

**项目地址**: https://github.com/yinanli1917-cloud/apple-notes-mcp-Chinese-Optimized

**开源协议**: MIT License © 2025 Yinan Li

**Made with ❤️ by [Yinan Li](https://github.com/yinanli1917-cloud) & [Claude Code](https://claude.ai/claude-code)**
