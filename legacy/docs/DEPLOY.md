# 部署你自己的 Apple Notes MCP 服务器

> 将你的 Apple Notes 变成可以远程搜索的语义数据库

## 🎯 这个项目能做什么？

- ✅ 从 Apple Notes 导出所有笔记
- ✅ 使用 BGE-M3 模型构建语义索引（支持中英文）
- ✅ 通过 MCP 协议提供搜索服务
- ✅ 可以接入 Claude Desktop、Poke AI 等 MCP 客户端
- ✅ 支持本地和云端部署

## 📋 前置要求

- macOS（用于导出 Apple Notes）
- Python 3.10+
- GitHub 账号（如果要部署到 Railway）
- Railway 账号（免费，可选）

---

## 🚀 快速开始（本地部署）

### 1. 克隆仓库

```bash
git clone https://github.com/yinanli1917-cloud/apple-notes-mcp.git
cd apple-notes-mcp
```

### 2. 安装依赖

```bash
# 推荐使用 Python 3.12
pip install -r requirements.txt
```

### 3. 导出 Apple Notes

```bash
cd scripts
python3 export_notes_fixed.py
```

这会在 `~/notes.db` 创建一个 SQLite 数据库，包含你的所有笔记。

### 4. 构建语义索引

```bash
python3 indexer.py
```

首次运行会下载 BGE-M3 模型（约 560MB），然后索引你的笔记。
预计耗时：3-5 分钟（取决于笔记数量）。

### 5. 启动服务器

#### 选项 A: Claude Desktop（本地）

配置 `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "apple-notes": {
      "command": "python3",
      "args": [
        "/path/to/apple-notes-mcp/scripts/server.py"
      ]
    }
  }
}
```

重启 Claude Desktop，即可在对话中搜索笔记！

#### 选项 B: HTTP 服务器（本地网络）

```bash
python3 server_http.py
```

服务器地址：`http://127.0.0.1:8000/sse`

---

## ☁️ 云端部署（Railway）

如果你想通过 iPhone（流量）访问，需要部署到云端。

### 快速部署按钮

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/apple-notes-mcp)

### 手动部署步骤

详细步骤见 [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)

**简要流程**：

1. Fork 这个仓库
2. 在 Railway 创建项目（连接 GitHub）
3. 设置环境变量 `API_KEY`（生成一个强密码）
4. 上传你的 `notes.db`
5. 运行 `python3 scripts/build_index_cloud.py`
6. 获取 Railway 提供的 HTTPS URL

**你的服务器地址**：`https://your-app.up.railway.app/sse`

---

## 🔌 接入 MCP 客户端

### Poke AI（iMessage）

1. 打开 Poke AI → Settings → Integrations → New Integration
2. 填写：
   - **Name**: `Apple Notes Search`
   - **Server URL**: `https://your-app.up.railway.app/sse`（云端）或 `http://127.0.0.1:8000/sse`（本地）
   - **API Key**: 你在 Railway 设置的密钥（本地部署留空）

3. 在 iMessage 中测试：
   ```
   搜索关于 AI 的笔记
   ```

### Claude Desktop

见上文"选项 A"。

### 其他 MCP 客户端

任何支持 MCP SSE 传输的客户端都可以连接。

---

## 🛠️ 可用工具

### 1. `search_notes`
语义搜索笔记

**参数**：
- `query`（必需）：搜索关键词
- `limit`（可选）：返回结果数（默认 5，最多 20）
- `api_key`（云端部署必需）：API 密钥

**示例**：
```
搜索"幽默搞笑的内容"
```

### 2. `refine_search`
带时间过滤的精细搜索

**参数**：
- `query`（必需）：搜索关键词
- `date_after`（可选）：只搜索此日期之后（YYYY-MM-DD）
- `date_before`（可选）：只搜索此日期之前（YYYY-MM-DD）
- `limit`（可选）：返回结果数
- `api_key`（云端部署必需）：API 密钥

### 3. `get_stats`
查看统计信息

**参数**：
- `api_key`（云端部署必需）：API 密钥

### 4. `health_check`
健康检查（无需 API Key）

---

## 🔒 安全性

### 本地部署
- ✅ 数据完全在你的设备上
- ✅ 无需 API Key
- ✅ 仅本地访问

### 云端部署
- ✅ HTTPS 加密（Railway 自动提供）
- ✅ API Key 认证保护
- ✅ notes.db 不在 Git 仓库中（.gitignore 已排除）
- ⚠️ **注意**：你的笔记数据会上传到 Railway（但只有你能访问）

**重要**：
- 不要在公开的地方分享你的 Railway URL 和 API Key
- 定期更换 API Key
- 如果笔记包含高度敏感信息，建议仅本地部署

---

## 🔄 更新笔记索引

当你添加新笔记后：

### 本地部署

```bash
cd ~/Documents/apple-notes-mcp/scripts

# 1. 重新导出
python3 export_notes_fixed.py

# 2. 增量索引（只索引新笔记）
python3 indexer.py
```

### 云端部署

```bash
# 1. 本地导出
python3 scripts/export_notes_fixed.py

# 2. 上传到 Railway
railway shell
# 上传 notes.db

# 3. 重建索引
python3 scripts/build_index_cloud.py
```

---

## 📊 性能指标

基于测试（920 条笔记）：

- **索引时间**：约 3 分钟
- **搜索准确率**：87%
- **搜索响应时间**：100-200ms
- **向量维度**：1024（BGE-M3）
- **支持语言**：中英文混合 + 100+ 其他语言

---

## 🐛 故障排除

### 导出笔记失败

**可能原因**：权限问题

**解决**：
1. 系统偏好设置 → 安全性与隐私 → 完全磁盘访问
2. 添加 Terminal.app 或 iTerm.app

### 索引构建失败

**可能原因**：模型下载失败

**解决**：
```bash
# 手动下载模型
python3 -c "from FlagEmbedding import FlagModel; FlagModel('BAAI/bge-m3')"
```

### 搜索返回乱码

**可能原因**：使用了旧的导出脚本

**解决**：
```bash
python3 scripts/export_notes_fixed.py  # 使用修复版
python3 scripts/indexer.py full        # 完全重建索引
```

### Railway 部署失败

**查看**：Railway Build Logs

**常见问题**：
- `API_KEY` 环境变量未设置
- `notes.db` 未上传
- 内存不足（920 条笔记应该没问题，如果你有 10000+ 条笔记可能需要升级）

---

## 💡 进阶配置

### 自定义搜索返回数量

编辑 `server_cloud.py` 或 `server_http.py`，修改：

```python
limit = min(limit, 20)  # 改为你想要的最大值
```

### 使用 GPU 加速

在 M 系列 Mac 上：

编辑 `indexer.py`，将：
```python
use_fp16=True
```

改为：
```python
use_fp16=True,
device="mps"  # 使用 Metal Performance Shaders
```

### 添加更多过滤条件

你可以扩展 `refine_search` 工具，添加：
- 按文件夹过滤
- 按标签过滤
- 按笔记长度过滤

---

## 🤝 贡献

欢迎 Pull Requests！

**改进建议**：
- 支持其他笔记应用（Notion、Evernote 等）
- 添加自动同步功能
- 改进搜索质量（混合检索、重排序）
- 添加更多 MCP 客户端示例

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

## 🙏 致谢

- [FastMCP](https://github.com/jlowin/fastmcp) - MCP 框架
- [BGE-M3](https://github.com/FlagOpen/FlagEmbedding) - 嵌入模型
- [ChromaDB](https://www.trychroma.com/) - 向量数据库

---

## 📞 支持

- **Issues**: https://github.com/yinanli1917-cloud/apple-notes-mcp/issues
- **Discussions**: https://github.com/yinanli1917-cloud/apple-notes-mcp/discussions

---

**Star ⭐ 这个项目如果觉得有用！**

**Made with ❤️ by Yinan Li**
