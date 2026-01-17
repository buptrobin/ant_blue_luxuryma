# 实时流式输出配置指南

## 🎯 问题描述

用户期望：每个节点完成后立即将结果输出到前端
实际表现：所有节点都完成后才一起输出

这是一个典型的**流式响应缓冲问题**。

---

## ✅ 已完成的修复

### 1. 更新 StreamingResponse Headers

**文件**: `backend/app/api/routes.py`

```python
return StreamingResponse(
    event_generator(),
    media_type="text/event-stream",
    headers={
        "Cache-Control": "no-cache, no-transform",  # 禁用缓存和转换
        "Connection": "keep-alive",                  # 保持连接
        "X-Accel-Buffering": "no",                  # 禁用 nginx 缓冲
        "Content-Encoding": "none",                  # 禁用压缩
    }
)
```

### 2. 添加事件发送日志

每个事件发送时都会记录日志：

```python
if event_type == "node_complete":
    logger.info(f"[V2 Stream] Sent node_complete event for {event.get('node')}")
elif event_type == "node_start":
    logger.info(f"[V2 Stream] Sent node_start event for {event.get('node')}")
```

---

## 🔧 确保实时输出的配置

### 1. Uvicorn 启动配置

**推荐启动命令**（禁用缓冲）：

```bash
cd backend
uvicorn app.main:app --reload --log-level info --timeout-keep-alive 120
```

**参数说明：**
- `--log-level info` - 显示详细日志，可以看到事件何时发送
- `--timeout-keep-alive 120` - 保持连接 120 秒

### 2. 如果使用 Nginx 反向代理

在 nginx 配置中添加：

```nginx
location /api/v1/analysis/v2/stream {
    proxy_pass http://localhost:8000;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_buffering off;           # 关键：禁用缓冲
    proxy_cache off;               # 禁用缓存
    proxy_read_timeout 300s;       # 增加超时时间
}
```

### 3. 前端配置（浏览器）

**使用 EventSource（推荐）：**

```javascript
const eventSource = new EventSource(
  `/api/v1/analysis/v2/stream?prompt=${encodeURIComponent(prompt)}`
);

eventSource.addEventListener('message', (e) => {
  const event = JSON.parse(e.data);
  console.log(`[${new Date().toLocaleTimeString()}] 收到事件:`, event.type);

  // 立即处理事件
  if (event.type === 'node_complete') {
    updateUI(event.node, event.data);  // 立即更新UI
  }
});
```

**使用 fetch + ReadableStream：**

```javascript
const response = await fetch(
  `/api/v1/analysis/v2/stream?prompt=${encodeURIComponent(prompt)}`
);

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value, { stream: true });
  console.log(`[${new Date().toLocaleTimeString()}] 收到数据块`);

  // 立即处理每个 chunk
  const lines = chunk.split('\n');
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const event = JSON.parse(line.slice(6));
      updateUI(event);  // 立即更新UI
    }
  }
}
```

---

## 🧪 测试实时性

### 方法1：使用测试脚本

```bash
cd backend
python test_realtime_streaming.py
```

**预期输出：**
```
================================================================================
实时流式输出测试
================================================================================

用户输入: 我要为春季新款手袋上市做推广，圈选VVIP和VIP客户

开始时间: 19:30:15.123

--------------------------------------------------------------------------------

[19:30:15.456] (首个事件) 🚀 节点开始: 意图识别
[19:30:15.789] 💭 推理中...
[19:30:18.234] (+2.78s) ✅ 节点完成: intent_recognition
    └─ 输出: ✓ 意图识别完成您希望针对春季新品手袋上市...

[19:30:18.567] (+0.33s) 🚀 节点开始: 特征匹配
[19:30:21.890] (+3.32s) ✅ 节点完成: feature_matching
    └─ 输出: ✓ 特征匹配完成已为您匹配4个关键特征...

（后续节点...）

================================================================================
时间分析
================================================================================

总耗时: 25.67秒
事件总数: 156

节点完成时间间隔：
  intent_recognition → feature_matching: 3.32秒
  feature_matching → strategy_generation: 4.12秒
  strategy_generation → impact_prediction: 0.15秒
  impact_prediction → final_analysis: 3.89秒

================================================================================
✅ 判断：流式输出是实时的
   各节点之间有明显的时间间隔（最大间隔 4.12秒）
================================================================================
```

**关键指标：**
- ✅ **节点之间有明显间隔**（几秒钟）→ 实时输出正常
- ❌ **所有事件几乎同时到达**（间隔都 <0.1秒）→ 存在缓冲问题

### 方法2：查看服务器日志

启动服务器时观察日志：

```bash
uvicorn app.main:app --reload --log-level info
```

**正常的日志输出（实时）：**
```
INFO:     2026-01-17 19:30:15 - [V2 Stream] Sent node_start event for intent_recognition
INFO:     2026-01-17 19:30:18 - [V2 Stream] Sent node_complete event for intent_recognition
INFO:     2026-01-17 19:30:18 - [V2 Stream] Sent node_start event for feature_matching
INFO:     2026-01-17 19:30:21 - [V2 Stream] Sent node_complete event for feature_matching
...
```

**有缓冲问题的日志（所有日志几乎同时出现）：**
```
INFO:     2026-01-17 19:30:45 - [V2 Stream] Sent node_start event for intent_recognition
INFO:     2026-01-17 19:30:45 - [V2 Stream] Sent node_complete event for intent_recognition
INFO:     2026-01-17 19:30:45 - [V2 Stream] Sent node_start event for feature_matching
INFO:     2026-01-17 19:30:45 - [V2 Stream] Sent node_complete event for feature_matching
...
```

### 方法3：使用 curl 测试

```bash
curl -N "http://localhost:8000/api/v1/analysis/v2/stream?prompt=帮我圈选VIP客户" \
  --no-buffer
```

**参数说明：**
- `-N, --no-buffer` - 禁用缓冲
- 应该能看到事件逐个出现，而不是一次性全部输出

---

## 🔍 常见缓冲问题和解决方案

### 问题1: Python 输出缓冲

**症状：** 日志显示事件已发送，但前端收不到

**解决方案：** 启动 uvicorn 时设置环境变量

```bash
# Linux/Mac
PYTHONUNBUFFERED=1 uvicorn app.main:app --reload

# Windows (PowerShell)
$env:PYTHONUNBUFFERED=1; uvicorn app.main:app --reload

# Windows (CMD)
set PYTHONUNBUFFERED=1 && uvicorn app.main:app --reload
```

### 问题2: Nginx 缓冲

**症状：** 本地测试正常，但通过 Nginx 访问有延迟

**解决方案：** 配置 nginx.conf

```nginx
# 在 http 块或 location 块中添加
proxy_buffering off;
proxy_cache off;
proxy_http_version 1.1;
```

### 问题3: 浏览器缓冲

**症状：** 使用 EventSource，但事件接收有延迟

**解决方案：** 检查浏览器网络面板

1. 打开浏览器开发者工具
2. 查看 Network 面板
3. 找到 SSE 请求
4. 查看 "Messages" 或 "EventStream" 标签
5. 确认事件是逐个到达还是批量到达

### 问题4: LLM API 延迟

**症状：** 节点之间有很长时间没有任何输出

**解决方案：** 这是正常的！LLM 生成需要时间

- `intent_recognition`: 通常 2-5 秒
- `feature_matching`: 通常 3-6 秒
- `strategy_generation`: 通常 3-5 秒
- `final_analysis`: 通常 4-8 秒

只要在节点执行过程中能看到 `reasoning` 事件（推理过程），就说明是实时的。

---

## 📊 实时性对比

### 缓冲输出（问题）

```
时间线：
|-------------------------- 所有处理 --------------------------|
0s                                                           25s
                                                              ↓
                                                [所有事件一起到达]
```

### 实时输出（正确）

```
时间线：
|-- 意图识别 --|-- 特征匹配 --|-- 策略生成 --|-- 预测 --|-- 分析 --|
0s           3s            7s           11s       12s      16s    25s
 ↓            ↓             ↓            ↓         ↓        ↓
[事件1]      [事件2]       [事件3]      [事件4]   [事件5]  [事件6]
```

---

## ✅ 验证清单

在前端集成前，请确认：

- [ ] 运行 `test_realtime_streaming.py`，看到各节点有明显时间间隔
- [ ] 查看服务器日志，事件发送时间有间隔
- [ ] 使用 `curl -N` 测试，看到事件逐个出现
- [ ] 如果使用 Nginx，已配置 `proxy_buffering off`
- [ ] 浏览器开发者工具中，SSE 消息逐个到达

---

## 🐛 如果仍然有问题

### 收集诊断信息

1. **服务器日志**
   ```bash
   uvicorn app.main:app --reload --log-level debug 2>&1 | tee server.log
   ```

2. **测试脚本输出**
   ```bash
   python test_realtime_streaming.py 2>&1 | tee test.log
   ```

3. **网络抓包**（高级）
   ```bash
   curl -N "http://localhost:8000/api/v1/analysis/v2/stream?prompt=测试" -v
   ```

4. **浏览器 HAR 文件**
   - 打开开发者工具 → Network
   - 右键请求 → "Save all as HAR with content"

---

## 📚 相关文档

- **实现代码**: `backend/app/api/routes.py` (第801-918行)
- **测试脚本**: `backend/test_realtime_streaming.py`
- **本文档**: `REALTIME_STREAMING_CONFIG.md`

---

**更新时间**: 2026-01-17
**版本**: V2.2
**状态**: ✅ 已修复并提供测试工具
