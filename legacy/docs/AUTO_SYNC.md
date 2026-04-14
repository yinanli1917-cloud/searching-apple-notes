# 自动索引更新指南 / Auto Sync Guide

[中文](#中文) | [English](#english)

---

## 中文

### 问题：索引不会自动更新

当你在 Apple Notes 中添加新笔记后，MCP 搜索不到新内容，因为：
1. 笔记需要先导出到 SQLite 数据库
2. 然后从数据库生成向量索引
3. 这两步都需要手动运行

### 解决方案：自动定期更新

我提供了 3 种方案，你可以根据需求选择：

---

## 方案 1️⃣: 定时自动更新（推荐）

**特点**：
- ✅ 每 24 小时自动更新一次
- ✅ Mac 启动时立即更新
- ✅ 完全后台运行，无需手动操作
- ✅ 有日志记录，方便查看

**成本**：
- CPU: 每次约 2-3 分钟（增量更新）
- 内存: 峰值 ~3GB（模型加载期间）
- 磁盘 I/O: 轻微

### 启动定时任务

```bash
# 加载定时任务
launchctl load ~/Library/LaunchAgents/com.apple-notes-mcp.auto-sync.plist

# 立即运行一次（测试）
launchctl start com.apple-notes-mcp.auto-sync

# 查看状态
launchctl list | grep apple-notes-mcp
```

### 查看日志

```bash
# 查看最新日志
tail -f ~/Documents/apple-notes-mcp/logs/auto_sync_$(date +%Y%m%d).log

# 查看所有日志
ls -lh ~/Documents/apple-notes-mcp/logs/
```

### 停止定时任务

```bash
# 停止并卸载
launchctl unload ~/Library/LaunchAgents/com.apple-notes-mcp.auto-sync.plist

# 删除配置文件（可选）
rm ~/Library/LaunchAgents/com.apple-notes-mcp.auto-sync.plist
```

### 修改更新频率

编辑 `~/Library/LaunchAgents/com.apple-notes-mcp.auto-sync.plist`：

```xml
<!-- 每24小时 = 86400秒 -->
<key>StartInterval</key>
<integer>86400</integer>
```

**常用频率**：
- 每 12 小时: `43200`
- 每 6 小时: `21600`
- 每 1 小时: `3600`

修改后重新加载：
```bash
launchctl unload ~/Library/LaunchAgents/com.apple-notes-mcp.auto-sync.plist
launchctl load ~/Library/LaunchAgents/com.apple-notes-mcp.auto-sync.plist
```

---

## 方案 2️⃣: 手动快速更新

**特点**：
- ✅ 你控制何时更新
- ✅ 只需一个命令
- ✅ 增量更新，速度快（<1分钟）

**成本**：
- 需要记得运行

### 使用方法

```bash
# 进入脚本目录
cd ~/Documents/apple-notes-mcp/scripts

# 运行自动同步脚本
./auto_sync_notes.sh
```

你会看到：
```
[2025-11-07 16:30:45] =========================================
[2025-11-07 16:30:45] 🔄 开始自动同步 Apple Notes 索引
[2025-11-07 16:30:45] =========================================
[2025-11-07 16:30:45] 📤 步骤 1/2: 导出 Apple Notes...
[2025-11-07 16:30:52] ✅ 笔记导出成功
[2025-11-07 16:30:52] 🔍 步骤 2/2: 增量更新索引...
[2025-11-07 16:31:45] ✅ 索引更新成功
[2025-11-07 16:31:45] =========================================
[2025-11-07 16:31:45] 🎉 自动同步完成！
[2025-11-07 16:31:45] =========================================
```

**创建快捷命令**（可选）：

添加到 `~/.zshrc`:
```bash
alias sync-notes='~/Documents/apple-notes-mcp/scripts/auto_sync_notes.sh'
```

然后：
```bash
source ~/.zshrc
sync-notes  # 直接运行
```

---

## 方案 3️⃣: 实时监控（高级，不推荐）

**特点**：
- ✅ Apple Notes 一改动立即更新
- ❌ 持续占用资源
- ❌ 配置复杂

**成本**：
- CPU: 持续监控 + 频繁索引
- 内存: 持续占用 ~3GB
- 电量: 影响续航

### 为什么不推荐实时监控？

1. **Apple Notes 数据库频繁变化**
   - 每次打字都会触发数据库写入
   - 会导致索引频繁重建（非常耗资源）

2. **BGE-M3 模型加载慢**
   - 每次索引需要加载 2.3GB 模型
   - 需要 ~10秒启动时间

3. **收益不明显**
   - 大多数情况下，24小时延迟完全可接受
   - 你不会在写完笔记后立即去搜索它

### 如果你仍想实现

需要安装 `fswatch`:
```bash
brew install fswatch
```

创建监控脚本（仅供参考，不推荐使用）：
```bash
#!/bin/bash
# 监控 Apple Notes 数据库变化
fswatch -o ~/notes.db | while read f; do
    echo "检测到笔记变化，等待5分钟后更新..."
    sleep 300  # 等待5分钟避免频繁更新
    ~/Documents/apple-notes-mcp/scripts/auto_sync_notes.sh
done
```

---

## 📊 性能对比

| 方案 | 延迟 | CPU占用 | 内存占用 | 推荐度 |
|------|------|---------|----------|--------|
| 定时更新（24h） | 最多24小时 | 低（每天2-3分钟） | 低（运行时~3GB） | ⭐⭐⭐⭐⭐ |
| 手动更新 | 0（立即） | 低（按需） | 低（按需） | ⭐⭐⭐⭐ |
| 实时监控 | <5分钟 | 高（持续） | 高（持续~3GB） | ⭐ |

---

## 🔧 更新频次的代价

### 更新一次的成本

**时间**：
- 导出笔记: ~5-10秒（920条笔记）
- 增量索引: ~30-60秒（假设新增10条笔记）
- 总计: ~1分钟

**资源**：
- CPU: 100%（单核，索引期间）
- 内存: ~2.5-3GB（BGE-M3模型加载）
- 磁盘 I/O: 读取笔记数据库 + 写入ChromaDB

### 不同频率的影响

**每 24 小时（推荐）**：
- ✅ 每天仅消耗 ~2-3 分钟
- ✅ 对系统影响极小
- ✅ 延迟可接受（大多数人不会立即搜索新笔记）

**每 6 小时**：
- ⚠️ 每天消耗 ~8-12 分钟
- ⚠️ 如果在使用时更新，可能感觉卡顿
- ⚠️ 电池影响略增加

**每 1 小时**：
- ❌ 每天消耗 ~24-48 分钟
- ❌ 频繁加载模型影响续航
- ❌ 收益极小（延迟从24h降到1h，但你真的需要吗？）

**实时监控**：
- ❌❌❌ 持续占用 ~3GB 内存
- ❌❌❌ 每次修改都触发，资源浪费
- ❌❌❌ 电池续航显著下降

---

## 💡 最佳实践建议

### 普通用户

使用 **方案1（定时24小时）**：
```bash
launchctl load ~/Library/LaunchAgents/com.apple-notes-mcp.auto-sync.plist
```

**理由**：
- 完全自动，无需记忆
- 资源消耗极低
- 24小时延迟对日常使用无影响

### 重度笔记用户

使用 **方案1（定时12小时）** + **方案2（手动更新）**：

1. 定时任务设为12小时：
   ```xml
   <key>StartInterval</key>
   <integer>43200</integer>
   ```

2. 需要立即更新时手动运行：
   ```bash
   sync-notes  # 使用快捷命令
   ```

### 开发者/测试

使用 **方案2（纯手动）**：
```bash
# 创建别名
alias sync-notes='~/Documents/apple-notes-mcp/scripts/auto_sync_notes.sh'
```

**理由**：
- 完全控制何时更新
- 不会在开发时突然占用资源
- 需要时立即更新

---

## 🐛 故障排除

### 问题 1: 定时任务没有运行

**检查任务状态**：
```bash
launchctl list | grep apple-notes-mcp
```

如果没有输出，说明任务没有加载：
```bash
launchctl load ~/Library/LaunchAgents/com.apple-notes-mcp.auto-sync.plist
```

**查看错误日志**：
```bash
cat ~/Documents/apple-notes-mcp/logs/launchd_sync_err.log
```

### 问题 2: 权限错误

如果看到 "Permission denied"：
```bash
chmod +x ~/Documents/apple-notes-mcp/scripts/auto_sync_notes.sh
chmod +x ~/Documents/apple-notes-mcp/scripts/export_notes_fixed.py
chmod +x ~/Documents/apple-notes-mcp/scripts/indexer.py
```

### 问题 3: Python 路径错误

编辑 `auto_sync_notes.sh`，确认 Python 路径：
```bash
which python3.12
# 输出: /opt/homebrew/bin/python3.12

# 如果路径不同，修改脚本中的 PYTHON 变量
```

### 问题 4: 更新后搜索仍然找不到新笔记

可能是 API 服务器缓存问题，重启服务：
```bash
# 如果在运行 Poke AI 服务
cd ~/Documents/apple-notes-mcp/scripts
# 按 Ctrl+C 停止，然后重新启动
./start_poke_services.sh
```

---

## 📖 相关文档

- [Poke AI 集成指南](POKE_INTEGRATION.md)
- [项目状态](../STATUS.md)
- [技术文档](PROJECT_LOG.md)

---

## English

### Problem: Index doesn't auto-update

When you add new notes in Apple Notes, MCP search can't find them because:
1. Notes need to be exported to SQLite database first
2. Then vector index needs to be generated from database
3. Both steps require manual execution

### Solution: Automatic periodic updates

I provide 3 solutions, choose based on your needs:

---

## Option 1️⃣: Scheduled Auto-update (Recommended)

**Features**:
- ✅ Auto-update every 24 hours
- ✅ Immediate update on Mac startup
- ✅ Runs completely in background
- ✅ Logged for monitoring

**Cost**:
- CPU: ~2-3 minutes per update (incremental)
- Memory: Peak ~3GB (during model loading)
- Disk I/O: Minimal

### Start scheduled task

```bash
# Load the task
launchctl load ~/Library/LaunchAgents/com.apple-notes-mcp.auto-sync.plist

# Run once immediately (test)
launchctl start com.apple-notes-mcp.auto-sync

# Check status
launchctl list | grep apple-notes-mcp
```

### View logs

```bash
# View latest log
tail -f ~/Documents/apple-notes-mcp/logs/auto_sync_$(date +%Y%m%d).log

# List all logs
ls -lh ~/Documents/apple-notes-mcp/logs/
```

### Stop scheduled task

```bash
# Stop and unload
launchctl unload ~/Library/LaunchAgents/com.apple-notes-mcp.auto-sync.plist
```

### Change update frequency

Edit `~/Library/LaunchAgents/com.apple-notes-mcp.auto-sync.plist`:

```xml
<!-- Every 24 hours = 86400 seconds -->
<key>StartInterval</key>
<integer>86400</integer>
```

**Common frequencies**:
- Every 12 hours: `43200`
- Every 6 hours: `21600`
- Every 1 hour: `3600`

After editing, reload:
```bash
launchctl unload ~/Library/LaunchAgents/com.apple-notes-mcp.auto-sync.plist
launchctl load ~/Library/LaunchAgents/com.apple-notes-mcp.auto-sync.plist
```

---

## Option 2️⃣: Manual quick update

**Features**:
- ✅ You control when to update
- ✅ Just one command
- ✅ Incremental update, fast (<1 minute)

**Cost**:
- Need to remember to run

### Usage

```bash
cd ~/Documents/apple-notes-mcp/scripts
./auto_sync_notes.sh
```

**Create shortcut** (optional):

Add to `~/.zshrc`:
```bash
alias sync-notes='~/Documents/apple-notes-mcp/scripts/auto_sync_notes.sh'
```

Then:
```bash
source ~/.zshrc
sync-notes  # Run directly
```

---

## Option 3️⃣: Real-time monitoring (Advanced, NOT recommended)

**Features**:
- ✅ Updates immediately when Apple Notes changes
- ❌ Constant resource usage
- ❌ Complex setup

**Cost**:
- CPU: Continuous monitoring + frequent indexing
- Memory: Constant ~3GB
- Battery: Significant impact

### Why NOT recommended?

1. **Apple Notes database changes frequently**
   - Every keystroke triggers database writes
   - Would cause frequent index rebuilds (very resource-intensive)

2. **BGE-M3 model loads slowly**
   - Each indexing requires loading 2.3GB model
   - ~10 seconds startup time

3. **Minimal benefit**
   - 24-hour delay is acceptable for most use cases
   - You rarely search for a note immediately after writing it

---

## 📊 Performance Comparison

| Option | Latency | CPU Usage | Memory Usage | Rating |
|--------|---------|-----------|--------------|--------|
| Scheduled (24h) | Up to 24h | Low (2-3 min/day) | Low (~3GB when running) | ⭐⭐⭐⭐⭐ |
| Manual | 0 (immediate) | Low (on-demand) | Low (on-demand) | ⭐⭐⭐⭐ |
| Real-time | <5 min | High (constant) | High (constant ~3GB) | ⭐ |

---

## 🔧 Cost of Update Frequency

### Cost per update

**Time**:
- Export notes: ~5-10s (920 notes)
- Incremental index: ~30-60s (assuming 10 new notes)
- Total: ~1 minute

**Resources**:
- CPU: 100% (single core, during indexing)
- Memory: ~2.5-3GB (BGE-M3 model loading)
- Disk I/O: Read notes DB + Write ChromaDB

### Impact of different frequencies

**Every 24 hours (Recommended)**:
- ✅ Only ~2-3 minutes per day
- ✅ Minimal system impact
- ✅ Acceptable latency

**Every 6 hours**:
- ⚠️ ~8-12 minutes per day
- ⚠️ May feel sluggish if updating during use
- ⚠️ Slight battery impact

**Every 1 hour**:
- ❌ ~24-48 minutes per day
- ❌ Frequent model loading affects battery
- ❌ Minimal benefit

**Real-time**:
- ❌❌❌ Constant ~3GB memory
- ❌❌❌ Triggers on every change, wasteful
- ❌❌❌ Significant battery drain

---

## 💡 Best Practices

### Regular users

Use **Option 1 (Scheduled 24h)**:
```bash
launchctl load ~/Library/LaunchAgents/com.apple-notes-mcp.auto-sync.plist
```

### Heavy note-takers

Use **Option 1 (Scheduled 12h)** + **Option 2 (Manual)**:

1. Set scheduled task to 12 hours
2. Manually update when needed:
   ```bash
   sync-notes
   ```

### Developers/Testers

Use **Option 2 (Manual only)**:
```bash
alias sync-notes='~/Documents/apple-notes-mcp/scripts/auto_sync_notes.sh'
```

---

**Last Updated**: 2025-11-07
**Version**: 1.0
