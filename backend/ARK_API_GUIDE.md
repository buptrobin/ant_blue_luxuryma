# 火山引擎 ARK API 集成指南

## 概述

后端已更新为使用火山引擎的 **ARK API**（OpenAI兼容接口），而不是旧的SDK方式。这使得集成更加简洁和灵活。

## 环境配置

在 `.env` 文件中配置以下变量（已提供）：

```env
# Volc Engine ARK API Configuration
ARK_API_KEY=d3b9b254-df0e-4afd-b18b-4362168f11f3
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3/
ARK_MODEL=doubao-seed-1-6-251015
```

## 配置说明

| 环境变量 | 说明 | 获取方式 |
|---------|------|---------|
| `ARK_API_KEY` | 火山引擎API密钥 | [火山引擎控制台](https://console.volcengine.com/) |
| `ARK_BASE_URL` | API基础URL | `https://ark.cn-beijing.volces.com/api/v3/` (中国北京) |
| `ARK_MODEL` | 使用的模型名称 | 例如 `doubao-seed-1-6-251015` (豆包系列模型) |

## LLM集成实现细节

### 核心类：`ArkChat`

位置: `backend/app/models/llm.py`

```python
class ArkChat(ChatModel):
    """Chat model using Volc Engine Ark API (OpenAI-compatible)."""

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model: str = "doubao-seed-1-6-251015"
    )
```

### 主要方法

#### 1. `call()` - 同步调用
```python
response = await llm.call(prompt)
```

**请求格式:**
- 使用 OpenAI 兼容的 `/chat/completions` 端点
- 支持 Bearer Token 认证
- 参数: `model`, `messages`, `temperature`, `max_tokens`

**响应格式:**
```json
{
    "choices": [
        {
            "message": {
                "content": "AI的响应内容"
            }
        }
    ]
}
```

#### 2. `stream()` - 流式调用
```python
async for chunk in llm.stream(prompt):
    print(chunk)
```

**流式格式:**
- 使用 Server-Sent Events (SSE)
- 每行以 `data: ` 开头，包含JSON数据
- 以 `data: [DONE]` 结尾

## 工作流

### 1. 意图分析（Intent Analysis）
```
用户输入 → LLM 分析 → 提取 JSON 结果
输出: {kpi, target_tiers, behavior_filters, size_preference, constraints}
```

### 2. 特征提取（Feature Extraction）
```
意图 → LLM 提取特征 → 生成筛选规则
输出: {feature_rules, weights, explanation}
```

### 3. 响应生成（Response Generation）
```
分析结果 → LLM 生成文案 → 自然语言总结
输出: 策略建议文本
```

## 错误处理与降级

### API 不可用时的处理

如果API连接失败或凭证缺失，系统会自动降级到 **Mock模式**：

```python
# 自动使用预定义的模拟响应
if not self.sdk_available:
    return self._get_mock_response(prompt)
```

这确保了即使没有真实API，系统也能继续工作用于开发和测试。

## 日志输出

启动时，你会看到以下日志信息：

```
INFO: Ark API initialized with model: doubao-seed-1-6-251015
```

如果配置不正确：

```
WARNING: Ark API credentials not fully configured. Please set ARK_API_KEY and ARK_BASE_URL.
WARNING: Ark API not available. Using mock response.
```

## 测试API连接

### 方法1：运行后端测试脚本

```bash
cd backend
python test_api.py
```

### 方法2：使用curl测试分析端点

```bash
curl -X POST http://localhost:8000/api/v1/analysis \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "我要为春季新款手袋上市做一次推广，目标是提升转化率，请帮我圈选高潜人群。",
    "stream": false
  }'
```

### 方法3：查看实时日志

```bash
# 设置调试日志级别
export LOG_LEVEL=DEBUG
python main.py
```

## 模型选择

### 推荐模型

| 模型ID | 说明 | 使用场景 |
|--------|------|---------|
| `doubao-seed-1-6-251015` | 豆包标准版，平衡性能和成本 | **推荐用于生产** |
| `doubao-pro-32k` | 豆包专业版，更强的推理能力 | 复杂分析任务 |
| `doubao-turbo-32k` | 豆包快速版，更低延迟 | 实时应用 |

## 成本优化

### 1. 提示工程优化

```python
# ✓ 好：清晰的指令
prompt = """分析用户的营销需求，返回JSON格式的结果。
用户需求：{user_input}"""

# ✗ 差：冗长的说明
prompt = """作为一个世界级的营销专家，你需要深入分析用户...
大约1000字的前置描述
最后才是真正的用户需求"""
```

### 2. Token计数

API 响应包含 `usage` 字段：

```json
{
    "usage": {
        "prompt_tokens": 128,
        "completion_tokens": 456,
        "total_tokens": 584
    }
}
```

### 3. 缓存策略

考虑对常见分析请求进行缓存：

```python
# backend/app/utils/cache.py
cache = {}
def cached_analysis(prompt):
    if prompt in cache:
        return cache[prompt]
    # 调用API
    result = await llm.call(prompt)
    cache[prompt] = result
    return result
```

## 故障排除

### 问题1：401 Unauthorized

**原因**: ARK_API_KEY 无效或过期

**解决**:
```bash
# 检查.env文件
cat backend/.env | grep ARK_API_KEY

# 从火山引擎控制台获取新的密钥
# https://console.volcengine.com/
```

### 问题2：404 Not Found

**原因**: ARK_BASE_URL 或 ARK_MODEL 不正确

**解决**:
```python
# 验证URL格式
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3/  # 注意末尾的/

# 查看日志中的实际请求URL
# POST {base_url}chat/completions
```

### 问题3：超时错误

**原因**: 网络问题或模型处理缓慢

**解决**:
```python
# 增加超时时间（在 llm.py 中）
self.timeout = 120  # 默认60秒

# 或在.env中配置
LLM_TIMEOUT=120
```

## 高级用法

### 自定义温度和Token限制

```python
response = await llm.call(
    prompt,
    temperature=0.3,  # 更确定性的输出
    max_tokens=1024   # 限制响应长度
)
```

### 使用流式处理大型响应

```python
collected = ""
async for chunk in llm.stream(prompt):
    collected += chunk
    print(chunk, end="", flush=True)
```

### 错误重试机制

```python
import asyncio

async def call_with_retry(llm, prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await llm.call(prompt)
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # 指数退避
            else:
                raise
```

## 监控与告警

### 建议的监控指标

1. **API可用性**: 成功率 > 99%
2. **响应时间**: p95 < 5秒
3. **Token成本**: 每个请求的平均Token数
4. **错误率**: 4xx和5xx错误比率

### 日志监控

```bash
# 实时查看错误
grep "Error calling Ark API" backend.log

# 统计API调用
grep "Ark API" backend.log | wc -l
```

## 生产部署检查清单

- [ ] ARK_API_KEY 已从安全的密钥管理系统加载
- [ ] ARK_BASE_URL 指向正确的区域端点
- [ ] 日志级别设置为 INFO 或 WARNING
- [ ] 实现了请求超时和重试逻辑
- [ ] 监控和告警已配置
- [ ] 容量规划完成（并发请求处理）
- [ ] 与前端的集成已测试

## 参考资源

- [火山引擎控制台](https://console.volcengine.com/)
- [ARK API 文档](https://www.volcengine.com/docs/)
- [豆包模型介绍](https://www.volcengine.com/product/ark)
- [OpenAI API 兼容性](https://platform.openai.com/docs/api-reference/chat)

## 支持

遇到问题？

1. 检查 `.env` 文件配置
2. 查看后端日志: `tail -f backend.log`
3. 运行 `python test_api.py` 进行诊断
4. 参考此文档的故障排除部分
