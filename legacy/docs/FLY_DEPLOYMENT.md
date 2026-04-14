# Fly.io 部署指南

> 如果 Railway 免费额度不够用，使用 Fly.io 作为替代方案

## Fly.io 免费额度

- ✅ 3个共享 CPU 虚拟机（足够运行 MCP 服务器）
- ✅ 160GB 出站流量/月
- ✅ 3GB 持久化存储
- ✅ 完全够个人使用

## 部署步骤

### 1. 安装 Fly.io CLI

```bash
# macOS
brew install flyctl

# 或使用安装脚本
curl -L https://fly.io/install.sh | sh
```

### 2. 注册并登录

```bash
# 注册账号
fly auth signup

# 或登录现有账号
fly auth login
```

### 3. 创建应用

```bash
cd ~/Documents/apple-notes-mcp

# 创建应用（自动检测 fly.toml）
fly launch --no-deploy
```

**重要**: 选择 `--no-deploy` 是因为我们需要先上传数据。

按提示操作：
- App name: 使用默认或自定义（如 `your-name-apple-notes`）
- Region: 选择 `sjc` (San Jose) 或 `nrt` (Tokyo)
- 不要创建 PostgreSQL 数据库

### 4. 设置环境变量

生成 API Key：
```bash
openssl rand -base64 32
```

设置到 Fly.io：
```bash
fly secrets set API_KEY="your-generated-key-here"
```

**保存这个 API Key**，稍后在 Poke AI 中需要用到！

### 5. 创建持久化存储（用于 notes.db）

```bash
fly volumes create apple_notes_data --size 3
```

### 6. 部署应用

```bash
fly deploy
```

这会：
- 构建 Docker 镜像
- 部署到 Fly.io
- 启动服务器

预计时间：5-8 分钟

### 7. 上传 notes.db

部署完成后，需要上传你的笔记数据：

```bash
# 方法 1: 使用 fly ssh（推荐）
fly ssh console

# 进入 shell 后
cd /app

# 退出
exit
```

使用 `fly ssh sftp` 上传文件：

```bash
# 上传 notes.db
fly ssh sftp shell

# 在 sftp> 提示符下：
put /Users/yinanli/notes.db /app/notes.db
quit
```

### 8. 构建向量索引

上传 notes.db 后，在 Fly.io 上运行索引构建：

```bash
fly ssh console

# 在远程 shell 中
cd /app
python3 scripts/build_index_cloud.py
exit
```

这个过程大约需要 3-5 分钟。

### 9. 获取服务器 URL

```bash
fly status
```

你的应用 URL 类似：
```
https://your-app-name.fly.dev
```

你的 Poke AI 服务器地址：
```
https://your-app-name.fly.dev/sse
```

### 10. 配置 Poke AI

在 Poke AI 的 "New Integration" 页面填写：

| 字段 | 值 |
|------|-----|
| **Name** | `Apple Notes Search` |
| **Server URL** | `https://your-app-name.fly.dev/sse` |
| **API Key** | 你在步骤 4 生成的密钥 |

### 11. 测试

在 iMessage 中向 Poke 发送：

```
搜索幽默搞笑的内容
```

成功！🎉

---

## 日常管理

### 查看日志

```bash
fly logs
```

### 查看应用状态

```bash
fly status
```

### 更新部署

当你修改代码后：

```bash
git push origin main
fly deploy
```

### 更新笔记索引

当你添加新笔记后：

```bash
# 1. 本地导出新笔记
cd ~/Documents/apple-notes-mcp/scripts
python3 export_notes_fixed.py

# 2. 上传到 Fly.io
fly ssh sftp shell
put /Users/yinanli/notes.db /app/notes.db
quit

# 3. 重建索引
fly ssh console
python3 scripts/build_index_cloud.py
exit
```

### 停止应用（省钱）

如果暂时不用：

```bash
fly scale count 0
```

重新启动：

```bash
fly scale count 1
```

---

## 成本对比

### Fly.io 免费额度

| 资源 | 免费额度 | 你的使用 | 状态 |
|------|---------|---------|------|
| VM | 3个共享CPU | 1个 | ✅ |
| 内存 | 256MB/VM | 1GB（需付费） | ⚠️ |
| 存储 | 3GB | < 500MB | ✅ |
| 流量 | 160GB/月 | < 1GB/月 | ✅ |

**注意**: BGE-M3 模型加载需要约 1GB 内存，超出免费额度的 256MB。

**预计费用**: 约 $2-3/月（仅内存费用）

### Railway vs Fly.io

| 项目 | Railway Hobby | Fly.io |
|------|--------------|--------|
| 最低费用 | $5/月 | $2-3/月 |
| 部署便捷性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 文档质量 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 免费额度 | 受限 | 更慷慨 |

---

## 故障排除

### 问题 1: 部署失败 "out of memory"

**原因**: BGE-M3 模型较大

**解决**:
```bash
# 增加内存到 2GB
fly scale memory 2048
fly deploy
```

### 问题 2: 上传 notes.db 失败

**替代方案**: 使用 fly secrets 传递 notes.db URL

如果你的 notes.db 在云存储（Dropbox、Google Drive）：

```bash
# 获取公开下载链接
NOTES_DB_URL="https://..."

# 设置环境变量
fly secrets set NOTES_DB_URL="$NOTES_DB_URL"
```

然后修改 `build_index_cloud.py` 添加下载逻辑（我可以帮你改）。

### 问题 3: Poke AI 连接失败

**检查**:
1. 确认服务器运行中：`fly status`
2. 查看日志：`fly logs`
3. 测试健康检查：`curl https://your-app.fly.dev/sse`

---

## 安全性

### 当前配置

✅ **已实现**:
- HTTPS 加密（Fly.io 自动提供）
- API Key 认证
- notes.db 在 Volume 中，不在镜像里

### 进一步加密（可选）

如果你想加密 notes.db：

```bash
# 在上传前加密
openssl enc -aes-256-cbc -salt -in ~/notes.db -out ~/notes.db.enc -k "your-password"

# 上传加密文件
fly ssh sftp shell
put ~/notes.db.enc /app/notes.db.enc

# 在 Fly.io 上解密
fly ssh console
openssl enc -aes-256-cbc -d -in /app/notes.db.enc -out /app/notes.db -k "your-password"
```

---

## 总结

**推荐方案**: 使用 Fly.io

**优势**:
- ✅ 更慷慨的免费额度
- ✅ 更低的最低费用（$2-3/月 vs $5/月）
- ✅ 同样支持 Dockerfile 部署
- ✅ 持久化存储支持

**劣势**:
- ⚠️ 配置稍复杂（但我会指导你）
- ⚠️ 需要手动上传 notes.db

---

准备好开始部署到 Fly.io 了吗？
