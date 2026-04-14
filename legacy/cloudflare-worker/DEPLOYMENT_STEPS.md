# Cloudflare Workers 部署步骤

## 当前状态

✅ 代码已完成
✅ 已登录 Cloudflare 账户
⚠️ 需要创建 workers.dev 子域名

## 下一步操作

### 步骤 1: 创建 workers.dev 子域名

1. 打开浏览器访问: https://dash.cloudflare.com
2. 登录你的 Cloudflare 账户
3. 在左侧菜单点击 "Workers & Pages"
4. 第一次打开会自动创建一个 workers.dev 子域名（如 `your-username.workers.dev`）
5. 记下你的子域名

### 步骤 2: 部署

在终端运行：

```bash
cd ~/Documents/apple-notes-mcp/cloudflare-worker
npx wrangler deploy
```

部署成功后，你会看到类似以下的输出：

```
✨ Deployed apple-notes-mcp successfully!
🌍 https://apple-notes-mcp.your-username.workers.dev
```

### 步骤 3: 测试部署

```bash
# 健康检查
curl https://apple-notes-mcp.your-username.workers.dev/health

# 测试 SSE 端点
curl https://apple-notes-mcp.your-username.workers.dev/sse
```

### 步骤 4: 在 Poke AI 中配置

1. 打开 iPhone 的 Poke AI
2. 进入 Settings → Connections → Integrations → New
3. 填写：
   - **Name**: `Apple Notes Search`
   - **Server URL**: `https://apple-notes-mcp.your-username.workers.dev/sse`
   - **API Key**: (留空)
4. 保存并测试

## 预期行为

如果集成成功，你应该能在 Poke AI 中：

1. 看到 "Apple Notes Search" 集成显示为已连接
2. 可以调用 `search_notes` 工具
3. 可以调用 `get_stats` 工具

测试命令：
- "search for funny content in my notes"
- "get stats about my notes"

## 故障排除

### 问题: workers.dev 子域名已被占用

如果你之前创建过 Cloudflare Workers，子域名可能已经存在。直接进行步骤 2。

### 问题: 部署失败 - Durable Objects 相关

确保 wrangler.toml 包含：

```toml
[[migrations]]
tag = "v1"
new_sqlite_classes = ["AppleNotesMcpAgent"]
```

### 问题: Poke AI 连接失败

1. 检查 URL 是否正确（必须是 `/sse` 结尾）
2. 确认服务器已部署并运行
3. 测试健康检查端点

## 成本

- **免费额度**: 100,000 请求/天
- **Durable Objects**: 免费层包含每天一定数量的请求
- **预计费用**: 对于个人使用，应该完全免费

## 下一步开发

部署成功后，可以添加：
- ✅ 完整的语义搜索功能
- ✅ Cloudflare Workers AI 嵌入向量
- ✅ R2 存储笔记数据
- ✅ 性能优化和错误处理

---

**当前进度**: 等待创建 workers.dev 子域名并部署
