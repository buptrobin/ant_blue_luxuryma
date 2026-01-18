# 多轮对话记忆增强 - 修改说明

## 修改内容

已将多轮对话的记忆轮次从 **3轮** 增加到 **10轮**。

## 修改的文件

### backend/app/core/session.py

#### 1. Session.get_history_summary() 方法（第84行）
**修改前**:
```python
def get_history_summary(self, max_turns: int = 3) -> str:
```

**修改后**:
```python
def get_history_summary(self, max_turns: int = 10) -> str:
```

#### 2. MemoryManager.build_context_for_llm() 方法（第183行）
**修改前**:
```python
history = session.get_history_summary(max_turns=3)
```

**修改后**:
```python
history = session.get_history_summary(max_turns=10)
```

#### 3. MemoryManager.__init__() 方法（第162行）
**修改前**:
```python
self.max_history_tokens = 2000  # Approximate token limit for context
```

**修改后**:
```python
self.max_history_tokens = 5000  # Approximate token limit for context (increased for 10-turn memory)
```

**原因**: 增加token限制以容纳更长的对话历史（10轮约需4000-5000 tokens）

## 影响范围

### 1. 对话历史传递
- Agent在分析用户新输入时，可以看到最近10轮的对话历史
- 之前只能看到最近3轮

### 2. 上下文构建
```
第1轮: 提升VIP客户转化率
第2轮: 不要最近购买过的
第3轮: 只要女性客户
第4轮: 年龄在25-34岁
第5轮: 排除退货率高的
第6轮: 扩大到500人
第7轮: 增加手袋品类偏好
第8轮: 近30天活跃用户
第9轮: 消费额大于5万
第10轮: 去掉年龄限制
```

现在Agent可以看到并融合所有10轮的约束条件，而不仅仅是最后3轮。

### 3. 约束条件累积
`build_context_for_llm()` 会收集所有历史轮次的约束条件：
```python
# 收集所有历史的约束条件
all_constraints = []
for turn in session.turns:  # 遍历所有轮次（不限于10轮）
    constraints = turn.intent.get("constraints", [])
    all_constraints.extend(constraints)
```

注意：虽然显示的历史摘要限制为10轮，但**约束条件的累积是全部历史**，不受10轮限制。

## 使用场景

### 适合长对话的场景
```
用户: 提升VIP客户转化率
Agent: 已分析...

用户: 不要最近购买过的
Agent: 已更新约束...

用户: 只要女性客户
Agent: 已添加性别限制...

用户: 年龄25-34岁
Agent: 已添加年龄限制...

用户: 排除退货率高的
Agent: 已添加排除规则...

用户: 增加手袋品类偏好
Agent: 已添加品类兴趣...

用户: 近30天活跃
Agent: 已添加活跃度要求...

用户: 消费额>5万
Agent: 已添加消费门槛...

用户: 只要VVIP
Agent: 已修改会员等级...

用户: 扩大到1000人
Agent: 已调整人群规模...
```

现在所有10轮的信息都会被Agent考虑，确保最终方案融合了所有需求。

## 注意事项

### Token消耗
- 更长的历史会增加LLM的token消耗
- 每次调用intent_recognition时会传递更多上下文
- 预计每次调用增加约1000-2000 tokens

### 性能影响
- 响应时间可能略有增加（因为上下文更长）
- 建议监控LLM调用的token使用量

### 成本影响
- Token消耗增加约50-100%（取决于对话轮次）
- 如果成本是考虑因素，可以适当减少到5-7轮

## 测试建议

### 测试场景1: 10轮连续对话
1. 进行10轮连续对话，每轮添加不同的约束
2. 在第10轮时点击"应用"
3. 验证生成的方案包含所有10轮的约束条件

### 测试场景2: 验证历史摘要
1. 进行5轮对话后，查看后端日志中的对话历史摘要
2. 应该能看到所有5轮的详细信息
3. 继续到10轮，验证所有10轮都被显示

### 测试场景3: 超过10轮
1. 进行15轮对话
2. 验证历史摘要只显示最近10轮
3. 验证约束条件仍然包含所有15轮的累积

## 回退方案

如果需要回退到3轮记忆：

```python
# backend/app/core/session.py

# 第84行
def get_history_summary(self, max_turns: int = 3) -> str:

# 第183行
history = session.get_history_summary(max_turns=3)

# 第162行
self.max_history_tokens = 2000  # Approximate token limit for context
```

## 验证修改

```bash
cd backend
python -m py_compile app/core/session.py
# 无输出表示语法正确

# 重启后端
python main.py
```

查看日志确认修改生效：
```
INFO: Build context for LLM with history (max 10 turns)
```
