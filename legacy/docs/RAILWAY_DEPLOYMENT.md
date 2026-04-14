# Railway 部署指南

将 Apple Notes MCP 服务器部署到 Railway，实现远程访问和 Poke AI 集成。

## 前置要求

- ✅ GitHub 账号（已有：yinanli1917@gmail.com）
- ✅ Railway 账号（通过 GitHub 登录）
- ✅ 本地已有 `notes.db`（包含你的笔记数据）

---

## 部署步骤

### 步骤 1: 推送代码到 GitHub

```bash
cd ~/Documents/apple-notes-mcp

# 添加所有新文件
git add .

# 创建 commit
git commit -m "添加 Railway 部署支持和 API Key 认证

- 新增 server_cloud.py（云端服务器，支持 API Key）
- 新增 build_index_cloud.py（云端索引构建）
- 新增 Dockerfile 和 requirements.txt
- 更新 .gitignore（排除敏感数据）
"

# 推送到 GitHub
git push origin main
```

### 步骤 2: 在 Railway 创建项目

1. 访问 https://railway.app
2. 点击 "New Project"
3. 选择 "Deploy from GitHub repo"
4. 选择 `yinanli1917-cloud/apple-notes-mcp`
5. Railway 会自动检测 Dockerfile 并开始构建

### 步骤 3: 配置环境变量

在 Railway 项目的 "Variables" 标签页，添加：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `API_KEY` | `your-secret-key-here` | **必需**，自己生成一个强密码 |
| `PORT` | `8000` | 可选，Railway 会自动设置 |

**生成 API Key**：
```bash
# 生成一个随机的 32 字符密钥
openssl rand -base64 32
```

复制生成的密钥，填入 Railway 的 `API_KEY` 变量。

**重要**: 保存这个 API Key，稍后在 Poke AI 中需要用到！

### 步骤 4: 上传 notes.db

Railway 构建完成后，需要上传你的笔记数据：

#### 方法 1: 使用 Railway CLI（推荐）

```bash
# 安装 Railway CLI
npm install -g @railway/cli

# 登录
railway login

# 链接到你的项目
railway link

# 上传 notes.db
railway run python3 -c "import sys; sys.exit(0)"  # 测试连接
railway shell  # 进入 Railway shell

# 在 Railway shell 中：
exit  # 先退出，因为需要用另一种方式
```

#### 方法 2: 通过构建脚本自动下载（如果你有云存储）

如果你的 `notes.db` 在云存储（如 Google Drive、Dropbox）：

1. 获取 `notes.db` 的公开下载链接
2. 在 Railway 的 Variables 添加：
   - `NOTES_DB_URL`: `https://...`（你的 notes.db 下载链接）

3. 修改 Dockerfile，添加下载步骤（我可以帮你改）

#### 方法 3: 使用 Railway Volume（持久化存储）

1. 在 Railway 项目中添加 Volume
2. 挂载到 `/app/data`
3. 手动上传 `notes.db` 到 Volume

**我的建议**: 先使用方法 1（Railway CLI），最简单。

### 步骤 5: 构建向量索引

上传 `notes.db` 后，在 Railway 中运行索引构建：

```bash
# 方法 1: 通过 Railway Web Terminal
# 在 Railway 项目页面，点击 "Shell" 按钮

python3 scripts/build_index_cloud.py
```

这个过程大约需要 3-5 分钟（920 条笔记）。

### 步骤 6: 获取服务器 URL

构建完成后，Railway 会分配一个 URL，类似：

```
https://apple-notes-mcp-production-xxxx.up.railway.app
```

你的 MCP 服务器地址是：

```
https://apple-notes-mcp-production-xxxx.up.railway.app/sse
```

### 步骤 7: 在 Poke AI 中配置

在 Poke AI 的 "New Integration" 页面填写：

| 字段 | 值 |
|------|-----|
| **Name** | `Apple Notes Search` |
| **Server URL** | `https://your-app.up.railway.app/sse` |
| **API Key** | `your-secret-key-here`（步骤 3 中生成的） |

点击 "Create Integration"。

### 步骤 8: 测试

在 iMessage 中向 Poke AI 发送：

```
搜索幽默搞笑的内容
```

如果配置正确，Poke 会返回相关笔记！

---

## 故障排除

### 问题 1: Railway 构建失败

**检查**:
1. 查看 Railway 的 Build Logs
2. 确认 `requirements.txt` 格式正确
3. 确认 Dockerfile 没有语法错误

**解决**:
```bash
# 本地测试 Docker 构建
cd ~/Documents/apple-notes-mcp
docker build -t apple-notes-mcp-test .
```

### 问题 2: 服务器启动失败 "未设置 API_KEY"

**原因**: 忘记在 Railway 设置 `API_KEY` 环境变量

**解决**:
1. 进入 Railway 项目 → Variables
2. 添加 `API_KEY` 变量
3. 重新部署（点击 "Redeploy"）

### 问题 3: Poke AI 报错 "认证失败"

**检查**:
1. 确认 Poke AI 中填写的 API Key 与 Railway 中的一致
2. API Key 没有多余的空格或换行

**解决**:
- 重新复制 API Key，确保完全一致

### 问题 4: 搜索报错 "向量数据库不存在"

**原因**: 未运行 `build_index_cloud.py`

**解决**:
```bash
# 在 Railway Shell 中运行
python3 scripts/build_index_cloud.py
```

### 问题 5: notes.db 上传失败

**临时方案**: 在 Railway 中通过脚本重新导出（如果你愿意在云端运行 export 脚本）

**注意**: 这需要 Railway 能访问你的 Apple Notes，可能需要额外配置。

**更简单的方案**: 使用 Railway Volume 手动上传

---

## 成本说明

**Railway 免费额度**:
- 每月 500 小时运行时间
- 100GB 出站流量
- 对个人使用完全够用

**超出免费额度**:
- 按使用量付费
- 对于你的使用场景（920条笔记，偶尔搜索），每月费用预计 < $5

---

## 安全性

### 当前配置

✅ **已实现**:
- API Key 认证（所有工具调用都需要验证）
- HTTPS 加密（Railway 自动提供）
- notes.db 不在 Git 仓库中（.gitignore 已排除）

⚠️ **注意事项**:
- API Key 存储在 Railway 环境变量中（相对安全）
- notes.db 包含敏感信息，确保只上传到你的 Railway 私有实例
- 不要在公开的地方分享你的 Railway URL 和 API Key

### 进一步增强（可选）

如果你想更安全：

1. **IP 白名单**: 限制只有特定 IP 可以访问
2. **请求频率限制**: 防止滥用
3. **加密 notes.db**: 在上传前加密数据库

我可以帮你实现这些功能，如果需要的话。

---

## 更新部署

当你添加新笔记后，需要更新云端索引：

### 方法 1: 手动更新

```bash
# 1. 本地导出新笔记
cd ~/Documents/apple-notes-mcp/scripts
python3 export_notes_fixed.py

# 2. 上传新的 notes.db 到 Railway
railway shell
# （然后上传 notes.db）

# 3. 重建索引
python3 scripts/build_index_cloud.py
```

### 方法 2: 自动化（未来改进）

可以添加一个 webhook，当你本地更新笔记后自动同步到 Railway。

---

## 开源部署说明

如果其他人想 fork 你的仓库并部署自己的实例：

### 他们需要做的

1. **Fork 仓库**: `https://github.com/yinanli1917-cloud/apple-notes-mcp`
2. **导出自己的笔记**: 在本地运行 `python3 scripts/export_notes_fixed.py`
3. **部署到 Railway**: 按本文档的步骤操作
4. **设置自己的 API Key**: 在 Railway 环境变量中
5. **上传自己的 notes.db**: 使用 Railway CLI 或 Volume
6. **构建索引**: 运行 `build_index_cloud.py`

### 他们会得到

- ✅ 自己的私有 Apple Notes 搜索实例
- ✅ 可以通过 Poke AI（或其他 MCP 客户端）访问
- ✅ 数据完全私有，不与他人共享

---

## 下一步

部署完成后，你可以：

1. **在 README.md 中添加部署徽章**:
   ```markdown
   [![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/...)
   ```

2. **编写 CONTRIBUTING.md**: 让其他人知道如何贡献代码

3. **创建 GitHub Releases**: 标记稳定版本

---

**需要帮助？**

如果在部署过程中遇到任何问题，随时问我！

**预计部署时间**: 20-30 分钟（首次）

**难度**: ⭐⭐⚪⚪⚪ (中等，但我会一步步指导你)
