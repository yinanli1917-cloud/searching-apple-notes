# Cloudflare Workers 部署指南

> **推荐方案**: 相比 Railway/Fly.io，Cloudflare Workers 提供更好的免费额度和全球边缘网络

## 为什么选择 Cloudflare Workers？

| 对比项 | Cloudflare Workers | Railway | Fly.io |
|--------|-------------------|---------|--------|
| **免费额度** | 100,000 请求/天 | ❌ 需付费 | 有限免费 |
| **费用** | 免费或 $5/月 | ~$5/月 | ~$2-3/月 |
| **全球分发** | ✅ 边缘网络 | ❌ 单区域 | ✅ 多区域 |
| **冷启动** | <10ms | ~1-2秒 | ~500ms |
| **适用场景** | Poke AI 远程访问 | 长时间运行 | 通用部署 |

## 快速开始

### 1. 安装 Wrangler (Cloudflare CLI)

```bash
npm install -g wrangler

# 登录 Cloudflare 账户
wrangler login
```

### 2. 创建 Workers 项目

```bash
# 方式一：使用模板创建
npm create cloudflare@latest apple-notes-mcp-worker

# 选择：
# - Framework: None (bare worker)
# - TypeScript: Yes
# - Git: Yes

cd apple-notes-mcp-worker
```

### 3. 项目结构

```
apple-notes-mcp-worker/
├── src/
│   └── index.ts          # MCP 服务器主文件
├── wrangler.toml         # Cloudflare 配置
├── package.json
└── tsconfig.json
```

### 4. 配置 wrangler.toml

```toml
name = "apple-notes-mcp"
main = "src/index.ts"
compatibility_date = "2024-11-01"

# R2 存储配置（用于存储笔记数据和索引）
[[r2_buckets]]
binding = "NOTES_BUCKET"
bucket_name = "apple-notes-data"
preview_bucket_name = "apple-notes-data-preview"

# KV 存储配置（用于快速查询）
[[kv_namespaces]]
binding = "NOTES_KV"
id = "your_kv_namespace_id"
preview_id = "your_preview_kv_namespace_id"

# 环境变量
[vars]
ENVIRONMENT = "production"
```

### 5. 实现 MCP 服务器 (src/index.ts)

参考 poke-mcp 的实现：

```typescript
import { FastMCP } from "fastmcp";

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // SSE 端点（Poke AI 使用）
    if (url.pathname === "/sse") {
      return handleSSE(request, env);
    }

    return new Response("Apple Notes MCP Server", { status: 200 });
  }
};

async function handleSSE(request: Request, env: Env): Promise<Response> {
  // 实现 SSE 流
  // TODO: 参考 poke-mcp 的 SSE 实现
  const { readable, writable } = new TransformStream();

  return new Response(readable, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      "Connection": "keep-alive",
    },
  });
}
```

### 6. 部署

```bash
# 本地测试
npm run dev
# 访问: http://localhost:8787/sse

# 部署到 Cloudflare
wrangler deploy

# 获取部署 URL
# 示例: https://apple-notes-mcp.your-username.workers.dev/sse
```

## 数据存储方案

由于 Cloudflare Workers 是无服务器环境，需要使用外部存储：

### 方案 1: R2 对象存储（推荐）

- **用途**: 存储笔记数据库和 ChromaDB 索引
- **费用**: 10GB 免费存储，之后 $0.015/GB/月
- **优势**: 完全兼容 S3 API

```bash
# 创建 R2 存储桶
wrangler r2 bucket create apple-notes-data
```

### 方案 2: D1 数据库

- **用途**: 存储笔记元数据和搜索索引
- **费用**: 免费额度 5GB
- **限制**: SQLite，不支持向量搜索

```bash
# 创建 D1 数据库
wrangler d1 create apple-notes-db
```

### 方案 3: KV 存储

- **用途**: 缓存热门查询结果
- **费用**: 免费额度 100,000 读取/天
- **优势**: 极快的读取速度

```bash
# 创建 KV 命名空间
wrangler kv:namespace create NOTES_KV
```

## 完整部署流程

### Step 1: 导出笔记数据

```bash
cd /Users/yinanli/Documents/apple-notes-mcp/scripts
python3 export_notes_fixed.py
```

### Step 2: 构建搜索索引

```bash
python3 indexer.py
```

### Step 3: 上传数据到 R2

```bash
# 上传笔记数据库
wrangler r2 object put apple-notes-data/notes.db --file=notes.db

# 上传 ChromaDB 索引（需要先打包）
cd chroma_db
tar -czf chroma_index.tar.gz .
wrangler r2 object put apple-notes-data/chroma_index.tar.gz --file=chroma_index.tar.gz
```

### Step 4: 部署 Workers 代码

```bash
wrangler deploy
```

### Step 5: 在 Poke AI 中配置

1. 打开 Poke AI 设置
2. 添加新的 MCP 集成
3. 输入：
   - **Name**: Apple Notes Search
   - **Server URL**: `https://apple-notes-mcp.your-username.workers.dev/sse`
   - **API Key**: (可选，用于认证)

## 技术挑战与解决方案

### 挑战 1: BGE-M3 模型在 Workers 中运行

**问题**: Workers 有 CPU 时间限制（10ms-50ms）

**解决方案**:
1. 使用 Cloudflare AI (Workers AI) 的嵌入模型
2. 或：预计算所有嵌入向量，只在 Workers 中做向量匹配

```typescript
// 使用 Cloudflare AI
const embeddings = await env.AI.run('@cf/baai/bge-base-en-v1.5', {
  text: query
});
```

### 挑战 2: ChromaDB 在无服务器环境运行

**问题**: ChromaDB 需要持久化存储

**解决方案**:
1. 使用简化的向量搜索（如 FAISS 的 JS 实现）
2. 或：将向量索引转换为 JSON，使用余弦相似度搜索

```typescript
// 简化的向量搜索
function cosineSimilarity(a: number[], b: number[]): number {
  const dotProduct = a.reduce((sum, val, i) => sum + val * b[i], 0);
  const magnitudeA = Math.sqrt(a.reduce((sum, val) => sum + val * val, 0));
  const magnitudeB = Math.sqrt(b.reduce((sum, val) => sum + val * val, 0));
  return dotProduct / (magnitudeA * magnitudeB);
}
```

### 挑战 3: SSE 流的正确格式

**问题**: Poke AI 期望特定的 SSE 消息格式

**解决方案**: 参考 poke-mcp 的实现，确保：
- 使用 `data:` 前缀
- 每条消息后发送双换行符 `\n\n`
- 发送心跳包保持连接

```typescript
async function sendSSEMessage(writer: WritableStreamDefaultWriter, data: any) {
  const message = `data: ${JSON.stringify(data)}\n\n`;
  await writer.write(new TextEncoder().encode(message));
}
```

## 参考资源

- **poke-mcp 项目**: https://github.com/kaishin/poke-mcp
- **Cloudflare Workers 文档**: https://developers.cloudflare.com/workers/
- **Workers AI 文档**: https://developers.cloudflare.com/workers-ai/
- **R2 存储文档**: https://developers.cloudflare.com/r2/

## 与现有部署方案对比

| 功能 | Cloudflare Workers | Railway/Fly.io (当前方案) |
|------|-------------------|--------------------------|
| 免费使用 | ✅ 100k 请求/天 | ❌ 需付费 |
| 全球访问 | ✅ 边缘网络 | ⚠️ 单区域 |
| 冷启动 | ✅ <10ms | ⚠️ 1-2秒 |
| BGE-M3 支持 | ⚠️ 需要替代方案 | ✅ 完全支持 |
| ChromaDB 支持 | ⚠️ 需要改造 | ✅ 完全支持 |
| 配置复杂度 | ⚠️ 中等 | ✅ 简单 |
| **适用场景** | Poke AI 快速响应 | 完整功能、复杂查询 |

## 建议

**短期方案**（测试 Poke AI 集成）:
- 使用当前的 Railway/Fly.io 方案
- 先解决 Poke AI 连接问题（SSE 格式）

**长期方案**（优化成本和性能）:
- 迁移到 Cloudflare Workers
- 使用 Workers AI 替代 BGE-M3
- 简化向量搜索算法

## 下一步

1. ✅ 了解 Cloudflare Workers 部署流程
2. ⏳ 研究 poke-mcp 的 SSE 实现细节
3. ⏳ 修复当前 server_http.py 的 SSE 格式
4. ⏳ 测试 Poke AI 连接
5. ⏳ 评估是否迁移到 Cloudflare Workers
