# 流式推理输出 - 实现总结

## ✅ 已完成的工作

根据您的需求 "调用大模型的时候，让大模型同时返回一步步的推理过程，并把过程流式输出给前端"，已经完整实现了以下功能：

### 1. 新增文件

**核心实现：**
- `backend/app/agent/streaming_nodes.py` (410行)
  - 4个流式节点，支持 Chain-of-Thought 推理
  - 实时流式传输 LLM 的思考过程

**测试脚本：**
- `backend/test_streaming_v2.py` (209行)
  - 完整的流式 endpoint 测试
  - 实时打印 LLM 推理过程

**文档：**
- `STREAMING_GUIDE.md` (完整使用指南，包含示例和前端集成代码)
- `STREAMING_README.md` (本文档)

### 2. 修改的文件

**后端路由：**
- `backend/app/api/routes.py`
  - 新增 `GET /api/v1/analysis/v2/stream` endpoint (119行新增)
  - SSE 流式响应支持

**工作流编排：**
- `backend/app/agent/graph.py`
  - 新增 `run_agent_stream_v2()` 函数 (130行新增)
  - 手动编排流式节点执行

**文档更新：**
- `REFACTOR_GUIDE.md`
  - 添加流式推理功能说明

---

## 🎯 核心功能

### Chain-of-Thought (思维链) 推理

所有关键节点的 LLM 提示词都加入了逐步推理指导：

```python
prompt = f"""你是一个营销专家...

请按照以下步骤分析：
1. **理解需求**：用户想要达到什么业务目标？
2. **识别人群**：用户想圈选哪类人群？
3. **提取约束**：有什么限制条件？
4. **判断清晰度**：用户的意图是否足够明确？

请先用自然语言逐步分析你的推理过程，然后返回JSON结果...
"""
```

### 实时流式传输

LLM 的输出逐字传输到前端：

```
[用户] 我要为春季新款手袋上市做推广...

[推理流式输出]
我首先分析用户的业务目标。用户明确提到"春季新款手袋上市"和"提升转化率"，
这表明目标是针对特定产品的销售转化优化...

接下来识别目标人群。用户指定了"VVIP和VIP客户"，这是明确的会员等级筛选...

年龄范围"25-44岁"也很清晰，这是奢侈品手袋的核心消费群体...

综合判断：用户意图非常明确。is_clear=true。
```

### 节点级流式控制

- ✅ **意图识别** - 流式（显示推理）
- ✅ **特征匹配** - 流式（显示推理）
- ✅ **策略生成** - 流式（显示推理）
- ⚡ **效果预测** - 非流式（快速计算）
- ✅ **结果输出** - 流式（显示推理）

---

## 🚀 快速测试

### 方法1：运行测试脚本

```bash
# 终端1：启动后端服务器
cd backend
uvicorn app.main:app --reload

# 终端2：运行流式测试
cd backend
python test_streaming_v2.py
```

**预期输出：**
```
================================================================================
测试1: 明确意图 - 流式输出
================================================================================

用户输入: 我要为春季新款手袋上市做推广...

开始流式处理...

🚀 【节点开始】 意图识别 (intent_recognition)
--------------------------------------------------------------------------------
我首先分析用户的业务目标。用户明确提到"春季新款手袋上市"和"提升转化率"...
（实时流式输出 LLM 推理过程）

✅ 【节点完成】 intent_recognition
  - 意图状态: clear
  - 业务目标: 提升春季新款手袋转化率
--------------------------------------------------------------------------------

🚀 【节点开始】 特征匹配 (feature_matching)
--------------------------------------------------------------------------------
分析需求：用户需要筛选VVIP/VIP客户、年龄25-44岁...
（实时流式输出 LLM 推理过程）

✅ 【节点完成】 feature_matching
  - 匹配特征数: 4
    · 会员等级为VVIP或VIP
    · 年龄段在25-44岁
    ...
--------------------------------------------------------------------------------

（后续节点继续流式输出...）

🎉 【工作流完成】
  - 状态: success
  最终预测结果:
  - 圈选人数: 28
  - 预估转化率: 8.50%
  - 预估收入: ¥336,000
  - ROI: 5.0倍
```

### 方法2：直接调用 API

```bash
curl -N "http://localhost:8000/api/v1/analysis/v2/stream?prompt=我要为春季新款手袋上市做推广，目标是提升转化率。圈选VVIP和VIP客户。"
```

---

## 📡 SSE 事件类型

新的流式 endpoint 发送5种事件类型：

### 1. node_start - 节点开始
```json
{
  "type": "node_start",
  "node": "intent_recognition",
  "title": "意图识别"
}
```

### 2. reasoning - 推理步骤（逐字流式）
```json
{
  "type": "reasoning",
  "node": "intent_recognition",
  "data": "我首先分析用户的业务目标..."
}
```

### 3. node_complete - 节点完成
```json
{
  "type": "node_complete",
  "node": "intent_recognition",
  "data": {
    "user_intent": {...},
    "intent_status": "clear",
    "reasoning": "完整推理过程摘要"
  }
}
```

### 4. workflow_complete - 工作流完成
```json
{
  "type": "workflow_complete",
  "status": "success",
  "session_id": "abc123",
  "data": {
    "response": "最终分析报告...",
    "user_intent": {...},
    "matched_features": [...],
    "prediction_result": {...}
  }
}
```

### 5. error - 错误
```json
{
  "type": "error",
  "data": "错误信息"
}
```

---

## 💻 前端集成示例

### 使用 EventSource (浏览器原生)

```javascript
const prompt = "我要为春季新款手袋上市做推广";
const url = `/api/v1/analysis/v2/stream?prompt=${encodeURIComponent(prompt)}`;

const eventSource = new EventSource(url);

eventSource.addEventListener('message', (e) => {
  const event = JSON.parse(e.data);

  switch (event.type) {
    case 'node_start':
      console.log(`[开始] ${event.title}`);
      showNodeStatus(event.node, 'running');
      break;

    case 'reasoning':
      // 实时显示 LLM 推理过程（打字机效果）
      appendReasoningText(event.node, event.data);
      break;

    case 'node_complete':
      console.log(`[完成] ${event.node}`);
      showNodeStatus(event.node, 'completed');
      updateNodeResult(event.node, event.data);
      break;

    case 'workflow_complete':
      console.log(`[工作流完成] ${event.status}`);
      displayFinalResult(event.data);
      eventSource.close();
      break;

    case 'error':
      console.error(`[错误] ${event.data}`);
      showError(event.data);
      eventSource.close();
      break;
  }
});

eventSource.onerror = (error) => {
  console.error('连接错误:', error);
  eventSource.close();
};
```

### React 组件示例

```typescript
import { useEffect, useState } from 'react';

function StreamingAnalysis({ prompt }: { prompt: string }) {
  const [reasoning, setReasoning] = useState<Record<string, string>>({});
  const [currentNode, setCurrentNode] = useState<string>('');
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    const url = `/api/v1/analysis/v2/stream?prompt=${encodeURIComponent(prompt)}`;
    const eventSource = new EventSource(url);

    eventSource.addEventListener('message', (e) => {
      const event = JSON.parse(e.data);

      switch (event.type) {
        case 'node_start':
          setCurrentNode(event.node);
          setReasoning(prev => ({ ...prev, [event.node]: '' }));
          break;

        case 'reasoning':
          setReasoning(prev => ({
            ...prev,
            [event.node]: (prev[event.node] || '') + event.data
          }));
          break;

        case 'workflow_complete':
          setResult(event.data);
          eventSource.close();
          break;
      }
    });

    return () => eventSource.close();
  }, [prompt]);

  return (
    <div>
      <h2>推理过程：</h2>
      {Object.entries(reasoning).map(([node, text]) => (
        <div key={node} className={node === currentNode ? 'active' : ''}>
          <h3>{node}</h3>
          <pre>{text}</pre>
        </div>
      ))}

      {result && (
        <div>
          <h2>分析结果：</h2>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
```

---

## 📊 工作流程图

```
用户输入
  ↓
🚀 意图识别 (流式)
  ├─ [推理] 分析业务目标...
  ├─ [推理] 识别目标人群...
  └─ [结果] intent_status: clear/ambiguous
  ↓
[条件路由]
  ├─ ambiguous → 🚀 澄清问题 → END
  └─ clear → 继续
  ↓
🚀 特征匹配 (流式)
  ├─ [推理] 分析需求维度...
  ├─ [推理] 匹配数据库特征...
  └─ [结果] match_status: success/needs_refinement
  ↓
[条件路由]
  ├─ needs_refinement → 🚀 请求修正 → END
  └─ success → 继续
  ↓
🚀 策略生成 (流式)
  ├─ [推理] 组合策略...
  └─ [结果] strategy_explanation
  ↓
⚡ 效果预测 (快速计算)
  └─ [结果] prediction_result
  ↓
🚀 结果输出 (流式)
  ├─ [推理] 生成分析报告...
  └─ [结果] final_response
  ↓
🎉 工作流完成
```

---

## 📂 文件清单

### 新增文件
```
backend/app/agent/streaming_nodes.py     # 流式节点实现 (410行)
backend/test_streaming_v2.py              # 测试脚本 (209行)
STREAMING_GUIDE.md                        # 完整使用指南
STREAMING_README.md                       # 本文档
```

### 修改文件
```
backend/app/agent/graph.py                # +130行 (run_agent_stream_v2)
backend/app/api/routes.py                 # +119行 (v2/stream endpoint)
REFACTOR_GUIDE.md                         # 更新说明
```

---

## ✅ 功能验证清单

- [x] Chain-of-Thought 推理提示词设计
- [x] LLM 流式输出实现
- [x] 4个流式节点实现
- [x] 工作流编排函数
- [x] SSE 流式 endpoint
- [x] 测试脚本
- [x] 完整文档
- [x] 明确意图流式测试
- [x] 模糊意图流式测试
- [x] 错误处理
- [x] Session 支持

---

## 🎯 核心技术点

### 1. Chain-of-Thought Prompting

通过在 prompt 中加入推理步骤指导，让 LLM 先思考再回答：

```python
prompt = f"""
请按照以下步骤分析：
1. 理解需求
2. 识别人群
3. 提取约束
4. 判断清晰度

请先用自然语言逐步分析推理过程，然后返回JSON结果。
"""
```

### 2. 流式传输实现

```python
async def stream_llm_with_reasoning(prompt, max_tokens):
    llm = get_llm_manager()
    full_response = ""

    # 逐字流式获取 LLM 输出
    async for chunk in llm.model.stream(prompt, max_tokens=max_tokens):
        full_response += chunk
        # 立即发送给前端
        yield {"type": "reasoning", "data": chunk}

    # 解析最终 JSON 结果
    result = json.loads(full_response)
    yield {"type": "result", "data": result}
```

### 3. SSE 响应格式

所有事件使用标准 SSE 格式：

```
data: {"type": "reasoning", "node": "intent_recognition", "data": "我首先..."}\n\n
data: {"type": "node_complete", "node": "intent_recognition", "data": {...}}\n\n
```

---

## 🔍 下一步工作建议

### 前端集成
1. 实现打字机效果显示推理过程
2. 添加可折叠的推理过程面板
3. 节点执行进度可视化

### 性能优化
1. 调整各节点的 max_tokens 参数
2. 优化 prompt 长度
3. 添加推理过程缓存

### 用户体验
1. 允许用户选择是否查看推理过程
2. 推理过程摘要显示
3. 推理质量评分

---

## 📞 支持

如有问题，请查看：
- 完整使用指南：`STREAMING_GUIDE.md`
- 测试脚本：`backend/test_streaming_v2.py`
- API 文档：`http://localhost:8000/docs`

---

**实现时间**: 2026-01-17
**版本**: V2.1 - Streaming with Chain-of-Thought Reasoning
**状态**: ✅ 完成并可用
