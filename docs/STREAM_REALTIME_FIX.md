# 实时流式输出启动指南

## 问题描述

虽然后端日志显示各节点是逐步完成的，但前端是等所有节点都完成后才一起显示结果。这是因为：

1. **Python 输出缓冲**：即使设置了正确的 HTTP headers，Python 自身也可能缓冲输出
2. **操作系统缓冲**：特别是在 Windows 环境下

## ✅ 解决方案

### 1. 正确启动 Uvicorn（关键！）

**Windows (CMD):**
```cmd
cd backend
set PYTHONUNBUFFERED=1
uvicorn app.main:app --reload --log-level info
```

**Windows (PowerShell):**
```powershell
cd backend
$env:PYTHONUNBUFFERED=1
uvicorn app.main:app --reload --log-level info
```

**Windows (一行命令):**
```cmd
set PYTHONUNBUFFERED=1 && uvicorn app.main:app --reload --log-level info
```

**Linux/Mac:**
```bash
cd backend
PYTHONUNBUFFERED=1 uvicorn app.main:app --reload --log-level info
```

### 2. 验证实时性

运行测试脚本：

```bash
cd backend
python test_stream_realtime.py
```

**预期输出**（实时正常）：
```
[19:30:15.456] 🚀 步骤1 开始: 业务意图与约束解析 (首个事件, +0.12s)
[19:30:18.234] ✅ 步骤1 完成: 业务意图与约束解析 (+2.78s)
[19:30:18.567] 📋 节点摘要 [intent_recognition] (+0.33s)
    ✓ 意图识别完成您希望针对春季新品手袋上市...

[19:30:21.890] ✅ 步骤2 完成: 多维特征扫描 (+3.32s)
[19:30:22.123] 📋 节点摘要 [feature_matching] (+0.23s)
    ✓ 特征匹配完成已为您匹配4个关键特征...
```

**异常输出**（有缓冲问题）：
```
[19:30:45.123] 🚀 步骤1 开始: 业务意图与约束解析 (首个事件, +0.01s)
[19:30:45.125] ✅ 步骤1 完成: 业务意图与约束解析 (+0.002s)
[19:30:45.127] 📋 节点摘要 [intent_recognition] (+0.002s)
[19:30:45.129] ✅ 步骤2 完成: 多维特征扫描 (+0.002s)
[19:30:45.131] 📋 节点摘要 [feature_matching] (+0.002s)
（所有事件几乎同时到达 - 缓冲问题）
```

## 📋 完整修复清单

- [x] **后端修复**
  - [x] 更新 `nodes.py` - 添加 `feature_summary` 和 `strategy_summary` 字段
  - [x] 确认 `routes.py` - StreamingResponse headers 已正确设置

- [ ] **环境配置**（用户操作）
  - [ ] 设置 `PYTHONUNBUFFERED=1` 环境变量
  - [ ] 重启 uvicorn 服务器
  - [ ] 运行 `test_stream_realtime.py` 验证

- [ ] **前端配置**（可选）
  - [ ] 确认前端使用 EventSource 或 fetch Stream API
  - [ ] 在浏览器开发者工具 Network 面板确认事件逐个到达

## 🔧 如果仍有问题

### 检查 1: 确认服务器日志

启动服务器后，观察日志中的时间戳：

```
2026-01-17 22:46:32 - INFO - Intent recognition parsed: {...}
2026-01-17 22:47:33 - INFO - Feature matching result: {...}  # 约1分钟后
2026-01-17 22:47:58 - INFO - Strategy explanation: {...}      # 约25秒后
```

如果后端日志时间间隔明显（几秒到几十秒），说明后端是实时的，问题可能在前端。

### 检查 2: 浏览器开发者工具

1. 打开浏览器开发者工具 (F12)
2. 切换到 Network 面板
3. 找到 `/analysis/stream` 请求
4. 查看 EventStream 标签页
5. 观察事件是逐个到达还是批量到达

### 检查 3: 如果使用 Nginx

在 nginx 配置中添加：

```nginx
location /api/ {
    proxy_pass http://localhost:8000;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_buffering off;           # 关键
    proxy_cache off;
    proxy_read_timeout 300s;
}
```

## 📌 总结

**核心修复**：设置 `PYTHONUNBUFFERED=1` 环境变量后重启服务器

这是解决 Python 流式输出缓冲问题最有效的方法。
