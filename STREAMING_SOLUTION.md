# 思维链流式输出实现方案

## 问题分析

当前的 `/api/v1/analysis/stream` 虽然使用了 SSE，但实际是**伪流式**：
```python
# 当前实现 (routes.py:224)
final_state = await graph.ainvoke(initial_state)  # ❌ 等待全部执行完

# 然后才发送 (routes.py:226-236)
for step in thinking_steps:
    yield f"event: thinking_step\n..."
```

这导致用户需要等待 30-60 秒才能看到第一个字符。

---

## 解决方案

### 方案 1：使用 LangGraph astream() - 节点级流式输出（推荐）

**优点：**
- ✅ 每个节点完成后立即流式发送
- ✅ 首字符响应快（1-3秒）
- ✅ 实现简单，不需要修改节点代码
- ✅ 用户可以实时看到各个节点的进度

**代码修改：**

#### 1. 修改 `app/api/routes.py` 的流式端点

```python
@router.get("/analysis/stream")
async def analyze_marketing_goal_stream(
    prompt: str,
    session_id: str = None
):
    """使用 LangGraph astream() 实现真正的流式输出"""
    logger.info(f"Received streaming analysis request: {prompt}")

    async def event_generator() -> AsyncIterator[str]:
        try:
            # 会话管理
            session_manager = get_session_manager()
            session = session_manager.get_or_create_session(session_id)
            memory_manager = session_manager.memory_manager
            llm_context = memory_manager.build_context_for_llm(session, prompt)
            is_modification = memory_manager.should_modify_intent(session, prompt)

            # 初始状态
            initial_state = {
                "user_input": prompt,
                "thinking_steps": [],
                "conversation_context": llm_context,
                "is_modification": is_modification,
                "previous_intent": session.current_context.get("latest_intent") if session.turns else None
            }

            # 🔥 关键改动：使用 astream() 代替 ainvoke()
            graph = get_agent_graph()
            final_state = None

            async for output in graph.astream(initial_state):
                # output 格式: {node_name: node_output}
                for node_name, node_output in output.items():
                    logger.info(f"Node {node_name} completed")

                    # 实时发送当前节点的 thinking_steps
                    thinking_steps = node_output.get("thinking_steps", [])
                    if thinking_steps:
                        # 找到最新添加的 step（通常是最后一个）
                        latest_step = thinking_steps[-1]
                        step_event = {
                            "stepId": latest_step["id"],
                            "title": latest_step["title"],
                            "description": latest_step["description"],
                            "status": latest_step["status"]
                        }
                        yield f"event: thinking_step\n"
                        yield f"data: {json.dumps(step_event, ensure_ascii=False)}\n\n"

                    # 保存最终状态
                    final_state = node_output

            # 发送最终结果
            if final_state:
                audience_list = final_state.get("audience", [])
                metrics_data = final_state.get("metrics", {})
                response_text = final_state.get("final_response", "")
                intent = final_state.get("intent", {})

                # 转换为响应格式
                audience = [
                    {
                        "id": u["id"],
                        "name": u["name"],
                        "tier": u["tier"],
                        "score": u["score"],
                        "recentStore": u["recentStore"],
                        "lastVisit": u["lastVisit"],
                        "reason": u["reason"],
                        "matchScore": u.get("matchScore")
                    }
                    for u in audience_list
                ]

                metrics = {
                    "audienceSize": metrics_data.get("audience_size", 0),
                    "conversionRate": metrics_data.get("conversion_rate", 0),
                    "estimatedRevenue": metrics_data.get("estimated_revenue", 0),
                    "roi": metrics_data.get("roi", 0),
                    "reachRate": metrics_data.get("reach_rate", 0),
                    "qualityScore": metrics_data.get("quality_score", 0)
                }

                # 保存会话
                turn = ConversationTurn(
                    user_input=prompt,
                    intent=intent,
                    audience=audience_list,
                    metrics=metrics_data,
                    response=response_text
                )
                session.add_turn(turn)

                # 发送完成事件
                result = {
                    "session_id": session.session_id,
                    "audience": audience,
                    "metrics": metrics,
                    "response": response_text,
                    "timestamp": datetime.now().isoformat()
                }
                yield f"event: analysis_complete\n"
                yield f"data: {json.dumps(result, ensure_ascii=False)}\n\n"

                logger.info(f"Streaming completed for session {session.session_id}")

        except Exception as e:
            logger.error(f"Error during streaming: {e}", exc_info=True)
            error_event = {"error": str(e)}
            yield f"event: error\n"
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
```

**效果：**
- 第一个节点（intent_analysis）完成后 ~3秒 → 用户看到第一个 thinking step
- 第二个节点（feature_extraction）完成后 ~6秒 → 用户看到第二个 step
- 依此类推，用户能实时看到进度

---

### 方案 2：LLM 级别的流式输出 - 字符级流式（可选）

如果你想看到 LLM "打字"的效果（像 ChatGPT 那样），需要更深度的改动。

**优点：**
- ✅ 极致的首字符响应（< 1秒）
- ✅ 用户能看到 AI "思考"的过程
- ✅ 体验最接近 ChatGPT

**缺点：**
- ❌ 需要修改所有节点的 LLM 调用
- ❌ 需要实时解析 JSON 流
- ❌ 实现复杂度较高

#### 实现步骤

##### 1. 修改 LLMManager 添加流式方法

```python
# app/models/llm.py

class LLMManager:
    """现有代码已经有 stream() 方法，需要添加高级封装"""

    async def analyze_intent_stream(self, prompt: str) -> AsyncIterator[dict]:
        """流式分析意图，实时返回 JSON 片段"""
        full_response = ""
        async for chunk in self.chat_model.stream(prompt):
            full_response += chunk
            # 尝试解析部分 JSON
            try:
                # 如果能解析就 yield
                partial_result = json.loads(full_response)
                yield {"type": "partial", "data": partial_result}
            except json.JSONDecodeError:
                # 还没完整就 yield 文本
                yield {"type": "text", "data": chunk}

        # 最终完整结果
        try:
            final_result = json.loads(full_response)
            yield {"type": "complete", "data": final_result}
        except json.JSONDecodeError:
            yield {"type": "error", "data": "Failed to parse JSON"}
```

##### 2. 修改节点支持流式输出

```python
# app/agent/nodes.py

async def intent_analysis_node_stream(state: AgentState, emit_callback):
    """支持流式输出的意图分析节点"""
    llm = get_llm_manager()
    user_input = state["user_input"]

    # 先发送 "正在思考" 的状态
    await emit_callback({
        "type": "thinking_step_update",
        "data": {
            "id": "1",
            "title": "业务意图与约束解析",
            "description": "正在分析营销目标...",
            "status": "active"
        }
    })

    # 流式调用 LLM
    full_intent = None
    async for chunk in llm.analyze_intent_stream(user_input):
        if chunk["type"] == "text":
            # 实时更新描述
            await emit_callback({
                "type": "thinking_step_text",
                "data": {
                    "id": "1",
                    "text": chunk["data"]
                }
            })
        elif chunk["type"] == "complete":
            full_intent = chunk["data"]

    # 完成后发送完整 step
    await emit_callback({
        "type": "thinking_step_complete",
        "data": {
            "id": "1",
            "title": "业务意图与约束解析",
            "description": f"核心KPI：{full_intent['kpi']}...",
            "status": "completed"
        }
    })

    return {"intent": full_intent, "thinking_steps": [...]}
```

##### 3. 使用 LangGraph astream_events()

```python
# app/api/routes.py

@router.get("/analysis/stream/llm")  # 新端点
async def analyze_with_llm_streaming(prompt: str, session_id: str = None):
    """LLM 级别的流式输出"""

    async def event_generator() -> AsyncIterator[str]:
        try:
            # ... 会话管理 ...

            graph = get_agent_graph()

            # 🔥 使用 astream_events() 获取所有事件
            async for event in graph.astream_events(initial_state):
                event_type = event["event"]

                # 捕获自定义事件
                if event_type == "on_custom_event":
                    custom_type = event["data"]["type"]

                    if custom_type == "thinking_step_text":
                        # 流式发送 LLM 输出的文本
                        yield f"event: llm_chunk\n"
                        yield f"data: {json.dumps(event['data'], ensure_ascii=False)}\n\n"

                    elif custom_type == "thinking_step_complete":
                        # 发送完整的 step
                        yield f"event: thinking_step\n"
                        yield f"data: {json.dumps(event['data']['data'], ensure_ascii=False)}\n\n"

            # ... 发送最终结果 ...

        except Exception as e:
            # ... 错误处理 ...

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

---

## 推荐实施路径

### 阶段 1：快速改进（1-2小时）
实施**方案 1**：使用 `astream()` 实现节点级流式输出
- 修改 `routes.py` 的 `/analysis/stream` 端点
- 测试确保每个节点完成后能实时发送
- 前端调整：接收并展示实时的 thinking steps

**预期效果：**
- 首字符响应从 30-60秒 → 3-5秒
- 用户能看到 5 个节点依次完成的进度

### 阶段 2：极致体验（可选，1-2天）
实施**方案 2**：LLM 级别的流式输出
- 修改所有节点支持 LLM 流式调用
- 使用 `astream_events()` 捕获所有事件
- 前端支持字符级的打字效果

**预期效果：**
- 首字符响应 < 1秒
- 用户能看到 LLM "思考"的实时过程
- 体验类似 ChatGPT

---

## 前端调整建议

无论使用哪个方案，前端都需要调整事件处理：

```javascript
// 方案 1 的前端代码
const eventSource = new EventSource(`/api/v1/analysis/stream?prompt=${prompt}&session_id=${sessionId}`);

eventSource.addEventListener('thinking_step', (event) => {
  const step = JSON.parse(event.data);
  // 立即在 UI 上显示新的 thinking step
  addThinkingStep(step);
});

eventSource.addEventListener('analysis_complete', (event) => {
  const result = JSON.parse(event.data);
  // 显示最终结果
  displayFinalResult(result);
  eventSource.close();
});

// 方案 2 的前端代码（额外支持）
eventSource.addEventListener('llm_chunk', (event) => {
  const chunk = JSON.parse(event.data);
  // 实时追加 LLM 输出的文字
  appendTextToCurrentStep(chunk.id, chunk.text);
});
```

---

## 总结

| 方案 | 首字符响应 | 实现难度 | 用户体验 | 推荐度 |
|------|------------|----------|----------|--------|
| **当前** | 30-60秒 | - | ⭐⭐ | - |
| **方案 1** | 3-5秒 | 低 | ⭐⭐⭐⭐ | ✅ **推荐** |
| **方案 2** | < 1秒 | 高 | ⭐⭐⭐⭐⭐ | 可选 |

**建议：**
1. 先实施方案 1，快速提升体验
2. 如果用户反馈好，再考虑方案 2 的极致优化
3. 保持当前的 `/api/v1/analysis` 同步端点不变，作为备选
