# 流式推理输出实现指南

## 📋 概述

本次实现为 LangGraph 工作流添加了**逐步推理流式输出**功能，使前端能够实时看到 LLM 的思考过程。

### 核心改进

1. **Chain-of-Thought (CoT) 推理** - LLM 在给出结果前先输出推理步骤
2. **实时流式传输** - 推理过程和结果通过 SSE 流式发送到前端
3. **节点级流式控制** - 关键节点支持流式输出，计算节点保持快速响应
4. **V2 流式 Endpoint** - 新的 `/api/v1/analysis/v2/stream` endpoint

---

## 🏗️ 架构设计

### 1. 流式节点 (Streaming Nodes)

新文件：`backend/app/agent/streaming_nodes.py`

包含4个支持流式推理的节点：

| 节点 | 功能 | 是否流式 | 推理内容 |
|-----|------|---------|---------|
| `intent_recognition_node_stream` | 意图识别 | ✅ 流式 | 分析业务目标、人群特征、约束条件 |
| `feature_matching_node_stream` | 特征匹配 | ✅ 流式 | 映射意图到数据库特征 |
| `strategy_generation_node_stream` | 策略生成 | ✅ 流式 | 组合特征的策略解释 |
| `final_analysis_node_stream` | 结果输出 | ✅ 流式 | 生成最终分析报告 |

**非流式节点**（快速计算，无需流式）：
- `ask_clarification_node` - 澄清问题生成
- `request_modification_node` - 修正建议生成
- `impact_prediction_node` - 效果预测（数据计算）

### 2. LLM 提示词改进

所有流式节点的提示词都加入了 **CoT 推理指导**：

```python
prompt = f"""你是一个营销专家...

请按照以下步骤分析：

1. **理解需求**：用户想要达到什么业务目标？
2. **识别人群**：用户想圈选哪类人群？
3. **提取约束**：有什么限制条件？
4. **判断清晰度**：用户的意图是否足够明确？

请先用自然语言逐步分析你的推理过程，然后在最后返回JSON格式的结果：

{{
  "reasoning": "这里写你的推理过程，逐步分析...",
  "business_goal": "...",
  ...
}}
"""
```

### 3. 流式工作流编排

新函数：`backend/app/agent/graph.py::run_agent_stream_v2()`

手动编排节点执行顺序，支持条件路由和流式输出：

```python
async def run_agent_stream_v2(user_input, conversation_history):
    # Step 1: Intent Recognition (流式)
    async for event in intent_recognition_node_stream(state):
        yield event
        if event["type"] == "node_complete":
            state.update(event["data"])

    # 条件路由
    if state.get("intent_status") == "ambiguous":
        # 返回澄清问题
        clarification_result = await ask_clarification_node(state)
        yield node_complete_event
        return  # 提前结束

    # Step 2: Feature Matching (流式)
    async for event in feature_matching_node_stream(state):
        yield event
        ...

    # Step 3-5: 继续执行...
```

### 4. SSE 流式 Endpoint

新 endpoint：`GET /api/v1/analysis/v2/stream`

**请求参数：**
- `prompt` (query string): 用户输入
- `session_id` (optional): Session ID for multi-turn

**SSE 事件类型：**

```typescript
// 1. 节点开始
{
  "type": "node_start",
  "node": "intent_recognition",
  "title": "意图识别"
}

// 2. 推理步骤（逐字流式）
{
  "type": "reasoning",
  "node": "intent_recognition",
  "data": "我首先分析用户的业务目标..."
}

// 3. 节点完成
{
  "type": "node_complete",
  "node": "intent_recognition",
  "data": {
    "user_intent": {...},
    "intent_status": "clear",
    "reasoning": "完整推理过程..."
  }
}

// 4. 工作流完成
{
  "type": "workflow_complete",
  "status": "success",
  "session_id": "abc123",
  "data": {
    "response": "最终报告...",
    "user_intent": {...},
    "matched_features": [...],
    "prediction_result": {...}
  }
}

// 5. 错误
{
  "type": "error",
  "data": "错误信息"
}
```

---

## 🚀 使用方法

### 1. 启动后端服务器

```bash
cd backend
uvicorn app.main:app --reload
```

### 2. 测试流式 Endpoint

**方法1：使用测试脚本**

```bash
cd backend
python test_streaming_v2.py
```

**方法2：使用 curl**

```bash
curl -N "http://localhost:8000/api/v1/analysis/v2/stream?prompt=我要为春季新款手袋上市做一次推广，目标是提升转化率。圈选VVIP和VIP客户。"
```

**方法3：使用 httpx (Python)**

```python
import httpx
import json

async with httpx.AsyncClient() as client:
    async with client.stream(
        "GET",
        "http://localhost:8000/api/v1/analysis/v2/stream",
        params={"prompt": "帮我圈选VIP客户"}
    ) as response:
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                event = json.loads(line[6:])
                print(event)
```

### 3. 前端集成示例

**使用 EventSource (浏览器原生 API)**

```javascript
const prompt = "我要为春季新款手袋上市做一次推广";
const url = `/api/v1/analysis/v2/stream?prompt=${encodeURIComponent(prompt)}`;

const eventSource = new EventSource(url);

// 所有事件都通过 'message' 监听
eventSource.addEventListener('message', (e) => {
  const event = JSON.parse(e.data);

  switch (event.type) {
    case 'node_start':
      console.log(`[节点开始] ${event.title}`);
      break;

    case 'reasoning':
      // 实时显示LLM推理过程
      appendReasoningText(event.node, event.data);
      break;

    case 'node_complete':
      console.log(`[节点完成] ${event.node}`);
      updateNodeStatus(event.node, 'completed', event.data);
      break;

    case 'workflow_complete':
      console.log(`[工作流完成] ${event.status}`);
      displayFinalResult(event.data);
      eventSource.close();
      break;

    case 'error':
      console.error(`[错误] ${event.data}`);
      eventSource.close();
      break;
  }
});

eventSource.onerror = (error) => {
  console.error('SSE Error:', error);
  eventSource.close();
};
```

**使用 fetch (更灵活的控制)**

```javascript
async function streamAnalysis(prompt) {
  const response = await fetch(
    `/api/v1/analysis/v2/stream?prompt=${encodeURIComponent(prompt)}`
  );

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const event = JSON.parse(line.slice(6));
        handleEvent(event);
      }
    }
  }
}
```

---

## 📊 工作流示例

### 场景1：明确意图 - 完整流程

**用户输入：**
> 我要为春季新款手袋上市做一次推广，目标是提升转化率。圈选VVIP和VIP客户，年龄在25-44岁。

**流式输出过程：**

```
🚀 【节点开始】 意图识别
--------------------------------------------------------------------------------
[推理] 我首先分析用户的业务目标。用户明确提到"春季新款手袋上市"和"提升转化率"，
这表明目标是针对特定产品的销售转化优化...

接下来识别目标人群。用户指定了"VVIP和VIP客户"，这是明确的会员等级筛选...

年龄范围"25-44岁"也很清晰，这是奢侈品手袋的核心消费群体...

综合判断：用户意图非常明确，包含业务目标、人群特征和约束条件。is_clear应为true。

✅ 【节点完成】 intent_recognition
  - 意图状态: clear
  - 业务目标: 提升春季新款手袋转化率
--------------------------------------------------------------------------------

🚀 【节点开始】 特征匹配
--------------------------------------------------------------------------------
[推理] 分析需求：用户需要筛选VVIP/VIP客户、年龄25-44岁...

匹配特征：
1. 会员等级 -> tier字段，使用in操作符，值为["VVIP", "VIP"]
2. 年龄段 -> age_group字段，使用in操作符，值为["25-34", "35-44"]
3. 手袋兴趣 -> handbag_browse_count字段，使用>操作符...

验证可行性：所有条件都能用现有特征满足，is_success=true。

✅ 【节点完成】 feature_matching
  - 匹配特征数: 4
    · 会员等级为VVIP或VIP
    · 年龄段在25-44岁
    · 浏览手袋品类超过5次
    · 近12个月消费额大于50000元
--------------------------------------------------------------------------------

🚀 【节点开始】 策略生成
--------------------------------------------------------------------------------
[推理] 根据您的需求，我们将采用以下圈选策略：

**目标人群定位**：锁定VVIP和VIP客户，年龄在25-44岁之间，这一群体是奢侈品手袋的
核心消费者，购买力强且品牌忠诚度高...

**行为筛选**：优先选择近期浏览手袋品类超过5次的用户，表明对新品有明确兴趣...

**预期效果**：这一策略能够精准触达高价值、高意向的潜在客户，预计转化率可提升30-50%...

✅ 【节点完成】 strategy_generation
  - 策略说明: 根据您的需求，我们将采用以下圈选策略...
--------------------------------------------------------------------------------

🚀 【节点开始】 效果预测
✅ 【节点完成】 impact_prediction
  - 圈选人数: 28
  - 预估转化率: 8.5%
  - 预估收入: ¥336,000
--------------------------------------------------------------------------------

🚀 【节点开始】 结果输出
--------------------------------------------------------------------------------
[推理] # 圈人分析报告

## 圈选结果概览
- **圈选人数**: 28人
- **会员分布**: VVIP 12人，VIP 16人
- **人群质量分**: 87.5/100

## 核心指标预测
...

✅ 【节点完成】 final_analysis
--------------------------------------------------------------------------------

🎉 【工作流完成】 状态: success
  最终预测结果:
  - 圈选人数: 28
  - 预估转化率: 8.50%
  - 预估收入: ¥336,000
  - ROI: 5.0倍
```

### 场景2：模糊意图 - 早期退出

**用户输入：**
> 帮我圈选一些用户

**流式输出过程：**

```
🚀 【节点开始】 意图识别
--------------------------------------------------------------------------------
[推理] 我首先分析用户的业务目标。用户只提到"圈选一些用户"，没有说明具体的营销目标...

接下来识别目标人群。用户没有提供任何人群特征，比如会员等级、年龄、消费力等...

综合判断：用户意图非常模糊，缺少关键信息。is_clear应为false。

✅ 【节点完成】 intent_recognition
  - 意图状态: ambiguous
--------------------------------------------------------------------------------

🚀 【节点开始】 澄清问题
✅ 【节点完成】 ask_clarification

澄清问题:
我理解您想进行人群圈选。为了更精准地帮您，能否告诉我：
1. 您的核心目标是什么？（提升转化率、增加营收、促进到店？）
2. 您希望圈选哪类客户？（VIP客户、年轻客户、高消费客户？）
3. 有什么约束条件吗？（人群规模、预算、排除条件？）
--------------------------------------------------------------------------------

🎉 【工作流完成】 状态: clarification_needed

最终响应:
我理解您想进行人群圈选。为了更精准地帮您，能否告诉我：...
```

---

## 🔧 技术细节

### 1. 流式推理实现原理

```python
async def stream_llm_with_reasoning(prompt: str, max_tokens: int):
    """核心流式推理函数"""
    llm = get_llm_manager()
    full_response = ""

    # 流式获取LLM输出
    async for chunk in llm.model.stream(prompt, max_tokens=max_tokens):
        full_response += chunk
        # 立即发送推理片段
        yield {"type": "reasoning", "data": chunk}

    # 解析最终JSON结果
    json_match = re.search(r'\{.*\}', full_response, re.DOTALL)
    if json_match:
        result = json.loads(json_match.group())
        yield {"type": "result", "data": result}
```

**关键点：**
- 使用 `llm.model.stream()` 获取 token-level 流式输出
- 每个 chunk 立即通过 `yield` 发送到前端
- 最终解析完整响应提取JSON结果

### 2. 节点流式包装

```python
async def intent_recognition_node_stream(state):
    """流式节点模板"""
    # 1. 发送节点开始事件
    yield {"type": "node_start", "node": "intent_recognition", "title": "意图识别"}

    # 2. 构建带CoT的prompt
    prompt = f"""..."""

    # 3. 流式调用LLM
    async for event in stream_llm_with_reasoning(prompt):
        if event["type"] == "reasoning":
            # 转发推理步骤
            yield {"type": "reasoning", "node": "intent_recognition", "data": event["data"]}

        elif event["type"] == "result":
            # 解析结果并发送节点完成事件
            result = event["data"]
            yield {
                "type": "node_complete",
                "node": "intent_recognition",
                "data": {...parsed result...}
            }
```

### 3. SSE 响应格式

所有事件都使用标准 SSE 格式：

```
data: {"type": "node_start", "node": "intent_recognition", "title": "意图识别"}\n\n
data: {"type": "reasoning", "node": "intent_recognition", "data": "我首先..."}\n\n
data: {"type": "node_complete", "node": "intent_recognition", "data": {...}}\n\n
```

**注意：**
- 每个事件以 `data: ` 开头
- JSON 格式的事件数据
- 事件以双换行符 `\n\n` 结尾

---

## 📝 配置说明

### LLM Token 限制

为了控制推理过程的长度，所有流式节点都设置了 `max_tokens` 限制：

```python
# backend/app/agent/streaming_nodes.py
async for event in stream_llm_with_reasoning(prompt, max_tokens=600):
    ...
```

**推荐值：**
- `intent_recognition`: 600 tokens
- `feature_matching`: 700 tokens
- `strategy_generation`: 600 tokens
- `final_analysis`: 800 tokens

### API 超时设置

流式请求需要更长的超时时间：

```python
# Client-side
async with httpx.AsyncClient(timeout=120.0) as client:
    ...
```

---

## ⚠️ 注意事项

### 1. LLM 依赖

- 所有流式节点都依赖 LLM 的流式输出能力
- 确保 `app.models.llm.ArkChat.stream()` 正常工作
- 如果 LLM 不可用，会fallback到mock响应

### 2. 性能考虑

- 流式输出增加了 API 响应时间（因为需要等待 LLM 逐字生成）
- 建议只在需要查看推理过程时使用流式 endpoint
- 如果只需要最终结果，使用非流式 `/analysis/v2` endpoint

### 3. 错误处理

- 每个流式节点都有 try-except 包装
- 错误会通过 SSE 事件发送：`{"type": "error", "data": "..."}`
- 前端应正确处理错误事件并关闭连接

### 4. Session 管理

- V2 流式 endpoint 支持多轮对话
- 通过 `session_id` 参数传递 session
- 对话历史会影响LLM的推理过程

---

## 🧪 测试清单

- [x] 明确意图 - 完整流程
- [x] 模糊意图 - 澄清问题
- [x] 特征匹配失败 - 修正建议
- [x] 推理内容实时流式传输
- [x] 节点状态正确更新
- [x] 工作流完成事件
- [x] 错误处理和错误事件
- [ ] 前端集成测试
- [ ] 多轮对话流式处理
- [ ] 长时间运行稳定性测试

---

## 📚 相关文件

### 新增文件
- `backend/app/agent/streaming_nodes.py` - 流式节点实现
- `backend/test_streaming_v2.py` - 流式endpoint测试脚本
- `STREAMING_GUIDE.md` - 本文档

### 修改文件
- `backend/app/agent/graph.py` - 添加 `run_agent_stream_v2()` 函数
- `backend/app/api/routes.py` - 添加 `/analysis/v2/stream` endpoint

### 相关文件
- `backend/app/models/llm.py` - LLM 流式调用实现
- `backend/app/agent/nodes.py` - 非流式节点实现
- `backend/app/agent/state.py` - State schema定义

---

## 🔜 后续优化建议

1. **流式节点性能优化**
   - 减少 LLM prompt 长度
   - 优化 token 使用效率
   - 缓存重复的特征元数据

2. **前端用户体验**
   - 打字机效果显示推理过程
   - 可折叠的推理过程面板
   - 进度条显示节点执行状态

3. **推理质量提升**
   - Few-shot examples in prompts
   - 更精细的 CoT 步骤划分
   - 推理过程的质量评估

4. **监控和调试**
   - 记录推理过程到日志
   - 推理质量分析工具
   - A/B测试不同prompt策略

---

**实现完成时间:** 2026-01-17
**版本:** V2.1 - Streaming with Chain-of-Thought
