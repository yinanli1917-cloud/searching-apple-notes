# Apple Notes AI Search

> Use AI to search and index your Apple Notes with natural language | 用 AI 自然语言检索你的苹果备忘录

[English](#english) | [中文](#中文)

---

## English

### What is this?

Turn your Apple Notes into a searchable knowledge base powered by AI. Instead of remembering exact titles, just describe what you're looking for.

![Search Demo in Claude Desktop.png](https://github.com/yinanli1917-cloud/apple-notes-mcp/blob/7dcb7766ec1c2d099339fc4c0818665d555a263b/images/Search%20Demo%20in%20Claude%20Desktop.png)

### Features

- **Claude Code Skill** *(recommended)*: Drop-in skill that lets Claude Code search and write your Apple Notes from any conversation, with built-in search strategy and dialogue-to-note workflow
- **Semantic Search**: Understands meaning, not just keywords
- **Chinese Optimized**: BGE-M3 embedding model handles Chinese-English mixed content natively
- **Multi-language**: Supports 100+ languages
- **Privacy First**: All data stays local — no API keys, no third-party servers
- **MCP Server** *(alternative)*: For Claude Desktop and Poke AI users who don't use Claude Code

### Two ways to use this

**1. As a Claude Code Skill — recommended.** This is the primary path. The skill teaches Claude Code *when* to search, *how* to phrase queries, *how* to interpret results, and *when* to save new insights back into Apple Notes. You install it once, then talk to Claude normally — no commands, no tool calls, no search box.

→ **[Read the skill docs and install instructions](skills/searching-apple-notes/README.md)**

**2. As an MCP server — for non-Claude-Code users.** If you use Claude Desktop, Cursor, or Poke AI on iMessage, the MCP server in `scripts/server.py` exposes the same search functionality as MCP tools. The MCP path is no longer my primary use case — I still accept PRs and bug reports, but new development happens in the Skill. See the Claude Desktop and Poke AI sections below for MCP setup.

### Quick Start

**Requirements:**
- macOS
- Python 3.10+
- Basic terminal knowledge (or ask AI like Claude to help!)

**Installation (5 minutes):**

```bash
# Clone the repo
git clone https://github.com/yinanli1917-cloud/apple-notes-mcp.git
cd apple-notes-mcp

# Install dependencies
pip3 install -r requirements.txt

# Export your notes
cd scripts && python3 export_notes_fixed.py

# Build search index (takes 3-5 minutes first time)
python3 indexer.py
```

**Use with Claude Desktop:**

1. Edit Claude's config file:
   ```bash
   open ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. Add this configuration (update the path):
   ```json
   {
     "mcpServers": {
       "apple-notes": {
         "command": "python3",
         "args": ["/Users/YOUR_USERNAME/Documents/apple-notes-mcp/scripts/server.py"]
       }
     }
   }
   ```

3. Restart Claude Desktop

4. Try searching: `Search for "funny content" in my notes`

👉 [Learn more about configuring MCP servers](https://modelcontextprotocol.io/quickstart/user)

**Use with Poke AI (iMessage):**

Search your notes directly from iMessage using Poke AI!

1. Install [Poke AI](https://poke.com) on your iPhone
2. Start the services on your Mac:
   ```bash
   cd ~/Documents/apple-notes-mcp/scripts
   ./start_poke_services.sh
   ```
3. Configure Poke AI with the MCP server URL:
   ```
   https://apple-notes-mcp.yinanli1917.workers.dev/sse
   ```
4. Search via iMessage: "Search my notes for funny jokes"

👉 [Full Poke AI Setup Guide](docs/POKE_INTEGRATION.md)

### Cost

**Local (Free):**
- All data stays on your Mac
- Complete privacy
- No internet required (except downloading models)

**Cloud Deploy (Optional):**
- Cloudflare: Free plan is enough
- Fly.io: ~$2-3/month
- Railway: ~$5/month
- Access from anywhere with your phone

### Tech Stack

**Core Search:**
- **BGE-M3**: Chinese-optimized embedding model (1024-dim)
- **ChromaDB**: Vector database
- **Python 3.12**

**Integrations:**
- **FastMCP**: MCP protocol framework (Claude Desktop)
- **Cloudflare Workers**: Serverless platform (Poke AI)
- **Cloudflare Tunnel**: Secure local-to-cloud bridge

### Documentation

- [Poke AI Integration Guide](docs/POKE_INTEGRATION.md) - Search via iMessage
- [Auto-Sync Guide](docs/AUTO_SYNC.md) - Keep your index up-to-date automatically
- [Cloudflare Tunnel Setup](docs/CLOUDFLARE_TUNNEL.md) - Local-to-cloud bridge
- [Cloud Deployment Guide](docs/DEPLOY.md) - Deploy to Fly.io/Railway
- [Project Status](STATUS.md) - Current features and roadmap
- [Technical Details](docs/PROJECT_LOG.md) - Development log

### Contributing

Contributions welcome! Feel free to:
- Report bugs
- Suggest features
- Improve documentation
- Submit pull requests

### License

MIT License © 2025 [Yinan Li](https://github.com/yinanli1917-cloud)

**Made with ❤️ by [Yinan Li](https://github.com/yinanli1917-cloud) & [Claude Code](https://claude.ai/claude-code)**

---

## 中文

### 这是什么？

用 AI 把你的苹果备忘录变成可搜索的知识库。不需要记住笔记标题，只要描述你想找什么就行。

![在 Claude Desktop 里的搜索演示](https://github.com/yinanli1917-cloud/apple-notes-mcp/blob/7dcb7766ec1c2d099339fc4c0818665d555a263b/images/Search%20Demo%20in%20Claude%20Desktop.png)

### 特性

- **Claude Code 技能包** *（推荐）*：开箱即用的技能包，让 Claude Code 在任何对话中都能搜索和写入你的 Apple Notes，内置搜索策略和"对话→笔记"工作流
- **语义搜索**：理解含义，而不仅仅是关键词匹配
- **中文优化**：BGE-M3 嵌入模型原生支持中英文混合内容
- **多语言支持**：支持 100+ 种语言
- **隐私优先**：数据全部保存在本地——不需要 API key，不依赖任何第三方服务器
- **MCP 服务器** *（备选）*：给那些不用 Claude Code、而是用 Claude Desktop 或 Poke AI 的用户

### 两种使用方式

**1. 作为 Claude Code 技能包——推荐方案。** 这是主要的使用路径。技能包教 Claude Code **什么时候**该搜、**怎么**写查询、**怎么**理解返回结果、**什么时候**该把新洞察写回 Apple Notes。装一次，之后就正常跟 Claude 对话——不用命令，不用工具调用，不用搜索框。

→ **[查看技能包文档和安装说明](skills/searching-apple-notes/README.md)**

**2. 作为 MCP 服务器——给不用 Claude Code 的用户。** 如果你用的是 Claude Desktop、Cursor 或者 iMessage 上的 Poke AI，`scripts/server.py` 里的 MCP 服务器把同样的搜索功能暴露成 MCP 工具。MCP 这条路径已经不是我目前的主要使用场景——我仍然接受 PR 和 bug 报告，但新功能开发都在技能包那边进行。MCP 的配置见下面的 Claude Desktop 和 Poke AI 章节。

### 快速开始

**前置要求：**
- macOS 电脑
- Python 3.10+
- 基础的终端使用（或者让 AI 比如 Claude 帮你！）

**安装步骤（5 分钟）：**

```bash
# 克隆项目
git clone https://github.com/yinanli1917-cloud/apple-notes-mcp.git
cd apple-notes-mcp

# 安装依赖
pip3 install -r requirements.txt

# 导出备忘录
cd scripts && python3 export_notes_fixed.py

# 建立搜索索引（首次需要 3-5 分钟）
python3 indexer.py
```

**在 Claude Desktop 中使用：**

1. 编辑 Claude 配置文件：
   ```bash
   open ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. 添加以下配置（修改路径为你的实际路径）：
   ```json
   {
     "mcpServers": {
       "apple-notes": {
         "command": "python3",
         "args": ["/Users/你的用户名/Documents/apple-notes-mcp/scripts/server.py"]
       }
     }
   }
   ```

3. 重启 Claude Desktop

4. 试试搜索：`搜索我笔记里的"幽默搞笑"内容`

👉 [了解更多关于配置 MCP 服务器](https://modelcontextprotocol.io/quickstart/user)

**在 Poke AI（iMessage）中使用：**

直接通过 iMessage 搜索你的备忘录！

1. 在 iPhone 上安装 [Poke AI](https://poke.com)
2. 在 Mac 上启动服务：
   ```bash
   cd ~/Documents/apple-notes-mcp/scripts
   ./start_poke_services.sh
   ```
3. 在 Poke AI 中配置 MCP 服务器 URL：
   ```
   https://apple-notes-mcp.yinanli1917.workers.dev/sse
   ```
4. 通过 iMessage 搜索："搜索我的笔记里关于幽默搞笑的内容"

👉 [完整 Poke AI 配置指南](docs/POKE_INTEGRATION.md)

### 费用

**本地使用（免费）：**
- 所有数据保存在你的 Mac 上
- 完全隐私保护
- 无需联网（除了下载模型）

**云端部署（可选）：**
- Cloudflare: 免费版已经足够消费者使用了
- Fly.io：约 $2-3/月
- Railway：约 $5/月
- 可以在任何地方用手机访问

### 技术栈

**核心搜索：**
- **BGE-M3**：中文优化的嵌入模型（1024 维向量）
- **ChromaDB**：向量数据库
- **Python 3.12**

**集成方式：**
- **FastMCP**：MCP 协议框架（Claude Desktop）
- **Cloudflare Workers**：无服务器平台（Poke AI）
- **Cloudflare Tunnel**：安全的本地到云端桥接

### 文档

- [Poke AI 集成指南](docs/POKE_INTEGRATION.md) - 通过 iMessage 搜索
- [自动同步指南](docs/AUTO_SYNC.md) - 自动保持索引最新
- [Cloudflare Tunnel 配置](docs/CLOUDFLARE_TUNNEL.md) - 本地到云端桥接
- [云端部署指南](docs/DEPLOY.md) - 部署到 Fly.io/Railway
- [项目状态](STATUS.md) - 当前功能和路线图
- [技术文档](docs/PROJECT_LOG.md) - 开发日志

### 参与贡献

欢迎贡献！你可以：
- 报告 Bug
- 提出功能建议
- 改进文档
- 提交 Pull Request

### 常见问题

**Q: 我不会用命令行怎么办？**

A: 可以让 AI 助手（比如 Claude、ChatGPT）帮你！复制命令给它们，让它们一步步指导你。

**Q: 支持其他笔记应用吗？**

A: 目前只支持 Apple Notes。Notion、Evernote 等可以先导出成文本后使用。

**Q: 能在手机上用吗？**

A: 当然可以！任何支持MCP的AI都可以✨

### 致谢

**灵感来源**：[ima (腾讯出品)](https://ima.qq.com/download?webFrom=10000075) - 优秀的 在线RAG个人知识库 应用

**使用的开源项目**：
- [FastMCP](https://github.com/jlowin/fastmcp)
- [BGE-M3](https://github.com/FlagOpen/FlagEmbedding)
- [ChromaDB](https://www.trychroma.com/)

### 开源协议

MIT License © 2025 [Yinan Li](https://github.com/yinanli1917-cloud)

**Made with ❤️ by [Yinan Li](https://github.com/yinanli1917-cloud) & [Claude Code](https://claude.ai/claude-code)**

如果觉得有用，请给我们一个 ⭐！
