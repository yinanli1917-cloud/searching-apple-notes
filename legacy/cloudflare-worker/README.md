# Apple Notes MCP Server - Cloudflare Workers 版本

> 使用官方 MCP SDK 的 TypeScript 实现，完全兼容 Poke AI

## 特点

- ✅ 使用官方 `@modelcontextprotocol/sdk`
- ✅ Cloudflare Workers 部署（免费额度大）
- ✅ 完全兼容 Poke AI
- ✅ SSE (Server-Sent Events) 传输
- ✅ 全球边缘网络，低延迟

## 快速开始

### 1. 安装依赖

```bash
cd cloudflare-worker
npm install
```

### 2. 本地测试

```bash
npm run dev
```

服务器将运行在: `http://localhost:8787`

测试端点:
- 健康检查: `http://localhost:8787/health`
- SSE 端点: `http://localhost:8787/sse`

### 3. 测试 SSE 连接

```bash
# 测试 SSE 端点
curl -v http://localhost:8787/sse

# 测试健康检查
curl http://localhost:8787/health
```

### 4. 与 Poke AI 集成

在 Poke AI 中配置：

| 字段 | 值 |
|------|-----|
| **Name** | `Apple Notes Search` |
| **Server URL** | `http://localhost:8787/sse` |
| **API Key** | *(留空)* |

## 项目结构

```
cloudflare-worker/
├── src/
│   └── index.ts          # MCP 服务器主文件
├── package.json          # 依赖配置
├── tsconfig.json         # TypeScript 配置
├── wrangler.toml         # Cloudflare Workers 配置
└── README.md            # 本文档
```

## 可用工具

### 1. search_notes

搜索 Apple Notes（语义搜索）

**参数**:
- `query` (string, 必需): 搜索关键词
- `limit` (number, 可选): 返回结果数（默认 5）

**示例**:
```json
{
  "tool": "search_notes",
  "arguments": {
    "query": "幽默搞笑的内容",
    "limit": 5
  }
}
```

### 2. get_stats

查看统计信息

**示例**:
```json
{
  "tool": "get_stats",
  "arguments": {}
}
```

## 开发状态

### ✅ 已完成

- [x] 项目结构搭建
- [x] 官方 MCP SDK 集成
- [x] SSE 传输实现
- [x] 基本工具注册
- [x] 健康检查端点

### 🚧 进行中

- [ ] Cloudflare Workers AI 嵌入向量生成
- [ ] R2 存储笔记数据
- [ ] 完整的语义搜索实现
- [ ] 向量相似度计算

### 📋 计划中

- [ ] 部署到 Cloudflare Workers
- [ ] Poke AI 集成测试
- [ ] 性能优化
- [ ] 错误处理改进

## 技术栈

- **语言**: TypeScript
- **运行环境**: Cloudflare Workers
- **MCP SDK**: `@modelcontextprotocol/sdk` v1.17.1
- **AI 模型**: Cloudflare Workers AI (计划使用 BGE embeddings)
- **存储**: R2 Object Storage (计划)

## 与 Python 版本对比

| 特性 | Python 版本 | TypeScript/Workers 版本 |
|------|-------------|------------------------|
| MCP SDK | FastMCP (第三方) | 官方 SDK |
| 部署 | 本地/Railway/Fly.io | Cloudflare Workers |
| Poke AI 兼容性 | ⚠️ 未知 | ✅ 预期兼容 |
| 嵌入模型 | BGE-M3 (本地) | Workers AI |
| 免费额度 | ❌ | ✅ 100k 请求/天 |
| 冷启动 | ~10秒 | <10ms |

## 下一步

1. **测试本地 SSE 连接**: 确保 MCP 协议正常工作
2. **Poke AI 集成测试**: 验证与 Poke AI 的兼容性
3. **实现完整搜索**: 添加 Workers AI + R2 存储
4. **部署到云端**: 使用 `npm run deploy`

## 故障排除

### 问题: wrangler dev 启动失败

**解决**:
```bash
# 确保 Node.js 已安装
node --version

# 重新安装依赖
rm -rf node_modules package-lock.json
npm install
```

### 问题: SSE 连接被拒绝

**检查**:
1. 确认服务器正在运行: `npm run dev`
2. 访问健康检查: `curl http://localhost:8787/health`
3. 查看控制台日志

## 参考资源

- [MCP 官方文档](https://modelcontextprotocol.io/)
- [Cloudflare Workers 文档](https://developers.cloudflare.com/workers/)
- [poke-mcp 参考实现](https://github.com/kaishin/poke-mcp)

## 许可证

MIT License © 2025 Yinan Li
