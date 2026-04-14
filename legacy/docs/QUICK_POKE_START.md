# Poke AI 快速开始 - 30 秒配置指南

## 第一步：启动服务器（10 秒）

打开终端，运行：

```bash
cd ~/Documents/apple-notes-mcp
./start_poke_server.sh
```

看到这个界面表示成功：

```
╭────────────────────────────────────────╮
│  🔗 Server URL:  http://127.0.0.1:8000/sse  │
╰────────────────────────────────────────╯
```

**保持这个终端窗口打开！**

---

## 第二步：配置 Poke AI（10 秒）

在 Poke AI 的 "New Integration" 页面：

| 填写项 | 内容 |
|--------|------|
| Name | `Apple Notes Search` |
| Server URL | `http://127.0.0.1:8000/sse` |
| API Key | 留空 |

点击 "Create Integration"

---

## 第三步：开始使用（10 秒）

在 iMessage 中向 Poke 发送：

```
搜索幽默搞笑的内容
```

你应该会收到相关笔记列表！

---

## 常用命令

**在 iMessage 中说**：

- "搜索 [关键词]"
- "找一找关于 [主题] 的笔记"
- "查看备忘录统计"
- "刷新备忘录索引"（添加新笔记后）

---

## 故障排除

### Poke AI 无法连接

1. 确认终端中的服务器还在运行
2. 确认 Server URL 是：`http://127.0.0.1:8000/sse`（末尾有 `/sse`）
3. 重启服务器（Ctrl+C 停止，然后重新运行 `./start_poke_server.sh`）

### 搜索返回错误

可能是向量数据库问题，重建索引：

```bash
cd ~/Documents/apple-notes-mcp/scripts
python3 export_notes_fixed.py
python3 indexer.py full
```

---

## 后台运行（可选）

如果你不想保持终端打开，使用 tmux：

```bash
# 安装 tmux（首次）
brew install tmux

# 在 tmux 中运行服务器
tmux new -s poke-server
cd ~/Documents/apple-notes-mcp
./start_poke_server.sh

# 按 Ctrl+B 然后 D 退出（服务器继续运行）

# 重新连接
tmux attach -t poke-server
```

---

**完整文档**: [POKE_INTEGRATION.md](POKE_INTEGRATION.md)

**需要帮助？** 查看主文档 [README.md](README.md)
