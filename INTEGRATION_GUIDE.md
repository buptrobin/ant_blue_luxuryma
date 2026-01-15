# LuxuryMA Agent 集成指南

## 项目概述

**LuxuryMA**是一个AI驱动的奢侈品营销人群圈选平台，由以下部分组成：

- **前端**: React + TypeScript + Ant Design（UI原型已完成）
- **后端**: FastAPI + LangGraph + 火山引擎大模型API（已实现）
- **Agent**: 5步骤的LangGraph推理流程

## 快速开始

### 前置要求

- Python 3.11+
- Node.js 18+ & npm
- 火山引擎API密钥（可选，有mock模式可用）

### 安装与运行

#### 步骤1：启动后端

```bash
cd backend

# 安装依赖
pip install fastapi uvicorn[standard] langgraph langchain langchain-community pydantic python-dotenv

# 配置环境变量（可选）
# 编辑 .env 文件，添加火山引擎API密钥
# VOLC_ACCESS_KEY=your_key
# VOLC_SECRET_KEY=your_secret
# VOLC_ENDPOINT_ID=your_endpoint_id

# 启动服务（默认运行在 http://localhost:8000）
python main.py
```

输出应该看起来像：
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### 步骤2：启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器（默认运行在 http://localhost:3000 或 5173）
npm run dev
```

#### 步骤3：打开浏览器

访问 `http://localhost:3000` 或 `http://localhost:5173`，开始使用！

## 功能演示

### 用户流程

1. **输入营销需求** - 在左侧聊天框输入您的营销目标
2. **Agent分析** - 后端Agent开始多步骤推理：
   - 解析营销意图和KPI
   - 提取多维人群特征
   - 应用筛选规则圈选用户
   - 预估转化效果
   - 生成策略建议
3. **实时反馈** - 思考步骤通过SSE流式实时显示
4. **查看结果** - 右侧仪表板显示：
   - 圈选的高潜用户列表
   - 转化率、收入等预估指标
   - 人群特征分布
   - 策略配置详情

### 示例输入

```
我要为春季新款手袋上市做一次推广，目标是提升转化率，请帮我圈选高潜人群。
```

### 示例输出

**圈选人群数**: 8人
**转化率预估**: 9.00%
**收入预估**: ¥12,960
**人群特征**:
- 会员等级: VVIP, VIP
- 活跃度: 高
- 消费力: 高

## API文档

### 核心端点

| 方法 | 端点 | 描述 |
|------|------|------|
| `POST` | `/api/v1/analysis` | 进行营销分析（同步） |
| `POST` | `/api/v1/analysis/stream` | 进行营销分析（SSE流式） |
| `GET` | `/api/v1/users/high-potential` | 获取高潜用户列表 |
| `POST` | `/api/v1/prediction/metrics` | 预估营销指标 |
| `GET` | `/api/v1/health` | 健康检查 |

### 完整API文档

启动后端后，访问: `http://localhost:8000/docs` (Swagger UI)

## 架构概览

### 后端架构

```
frontend (React)
    ↓ HTTP/SSE
FastAPI Server (8000)
    ↓
LangGraph Agent
    ├── Node 1: IntentAnalysis (意图分析)
    ├── Node 2: FeatureExtraction (特征提取)
    ├── Node 3: AudienceSelection (人群圈选)
    ├── Node 4: PredictionOptimization (效果预估)
    └── Node 5: ResponseGeneration (响应生成)
        ↓
    LLM (火山引擎/Mock)
```

### 前端架构

```
ChatInterface (聊天界面)
    ├── 用户输入处理
    ├── API调用 (services/api.ts)
    └── SSE流式监听
        ↓
Dashboard (结果展示)
    ├── UserList (用户列表)
    ├── PredictionWidget (指标预估)
    ├── StrategyConstraints (策略配置)
    └── InsightCard (洞察卡片)
```

## 开发指南

### 修改Agent逻辑

编辑 `backend/app/agent/nodes.py`:

```python
async def custom_node(state: AgentState) -> dict[str, Any]:
    """Custom agent node."""
    # 你的逻辑
    return {"key": "value"}
```

然后在 `backend/app/agent/graph.py` 中添加到图：

```python
workflow.add_node("custom", custom_node)
workflow.add_edge("previous_node", "custom")
```

### 修改用户筛选规则

编辑 `backend/app/data/selectors.py`:

```python
def custom_filter(users: list[User]) -> list[User]:
    """Custom user filtering."""
    return [u for u in users if custom_condition(u)]
```

### 修改指标计算

编辑 `backend/app/utils/metrics.py`:

```python
def calculate_custom_metric(audience_size: int) -> float:
    """Calculate custom metric."""
    return custom_formula(audience_size)
```

### 修改前端UI

所有React组件位于 `frontend/components/`:

- `ChatInterface.tsx` - 聊天界面
- `Dashboard.tsx` - 结果展示台
- `UserList.tsx` - 用户列表
- 等等

## 故障排除

### 后端不能启动

**症状**: `ModuleNotFoundError: No module named 'xxx'`

**解决方案**:
```bash
pip install --upgrade -r requirements.txt
# 或手动安装缺少的包
pip install fastapi uvicorn langgraph langchain
```

### 前端无法连接后端

**症状**: 显示 "后端API不可用"

**解决方案**:
1. 确保后端已启动: `python main.py` 输出包含 `Uvicorn running on`
2. 检查后端端口: 默认是 `8000`
3. 检查CORS配置: `backend/main.py` 中的 `origins` 列表

### 分析返回空结果

**症状**: 没有圈选任何用户

**解决方案**:
1. 检查模拟数据是否正确加载: `backend/app/data/mock_users.py`
2. 查看后端日志了解筛选细节
3. 验证Intent解析: 在 `backend/app/models/llm.py` 添加日志

### SSE连接断开

**症状**: 思考步骤显示不完整

**解决方案**:
1. 检查浏览器网络连接
2. 增加请求超时时间
3. 查看浏览器控制台 Console 标签的错误信息

## 生产部署

### Docker化

创建 `Dockerfile` (后端):

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e .
CMD ["python", "main.py"]
```

构建和运行:
```bash
docker build -t luxuryma-backend .
docker run -p 8000:8000 -e VOLC_ACCESS_KEY=xxx luxuryma-backend
```

### Nginx反向代理

```nginx
server {
    listen 80;
    server_name api.luxuryma.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # SSE特定配置
    location /api/v1/analysis/stream {
        proxy_pass http://localhost:8000;
        proxy_buffering off;
        proxy_set_header Cache-Control no-cache;
    }
}
```

## 数据库集成（未来）

当前使用模拟数据。要集成真实数据库：

1. 安装ORM: `pip install sqlalchemy`
2. 创建数据库模型
3. 修改 `backend/app/data/selectors.py` 从数据库查询
4. 更新API路由以持久化结果

## 性能优化

### 后端优化

- 增加 uvicorn workers: `--workers 4`
- 使用缓存: 实现Redis缓存层
- 异步数据库: 使用 `asyncpg` 而不是 `psycopg2`

### 前端优化

- 代码分割: 动态导入组件
- 图片优化: 使用WebP格式
- 缓存: 使用Service Worker缓存API响应

## 监控与日志

### 后端日志

设置日志级别:
```bash
export LOG_LEVEL=DEBUG  # 或 INFO, WARNING, ERROR
python main.py
```

### 指标收集

集成Prometheus:
```python
from prometheus_client import Counter, Histogram

request_count = Counter('requests_total', 'Total requests')
request_duration = Histogram('request_duration_seconds', 'Request duration')
```

## 常见问题

**Q: 如何自定义Agent的思考步骤？**
A: 在 `backend/app/agent/nodes.py` 的每个节点中修改 `thinking_steps`。

**Q: 如何添加新的数据源？**
A: 在 `backend/app/data/` 下创建新模块，实现数据查询接口。

**Q: 能否离线运行？**
A: 是的，使用mock LLM模式（不需要API密钥）。

**Q: 如何扩展到多语言？**
A: 在前端使用 `i18next`，在后端处理多语言Prompt。

## 许可证

MIT

## 支持与贡献

- 问题报告: 创建GitHub Issue
- 功能建议: 讨论区
- 代码贡献: 提交Pull Request

---

**最后更新**: 2026-01-15
**当前版本**: 1.0.0
