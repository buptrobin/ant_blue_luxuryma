# Marketing Agent Backend

AI-powered marketing audience segmentation agent built with FastAPI, LangGraph, and Volc Engine LLM.

## Features

- 🤖 **Multi-step Agent Reasoning**: 5-step workflow using LangGraph
  - Intent Analysis & Constraint Parsing
  - Multi-dimensional Feature Extraction
  - Audience Selection & Scoring
  - Performance Prediction & Optimization
  - Natural Language Response Generation

- 🎯 **Intelligent Audience Segmentation**: Smart user selection based on marketing goals
- 📊 **Real-time Metrics Prediction**: ROI, conversion rate, revenue forecasting
- 🚀 **Server-Sent Events (SSE)**: Stream thinking steps in real-time
- 📱 **CORS Enabled**: Ready for frontend integration

## Architecture

### Tech Stack

- **Framework**: FastAPI
- **Agent Framework**: LangGraph
- **LLM**: Volc Engine (ByteDance) - with fallback to mock mode for development
- **Data**: In-memory mock users (easily swappable with real database)
- **Language**: Python 3.11+

### Project Structure

```
backend/
├── main.py                    # FastAPI entry point
├── pyproject.toml            # Dependencies
├── .env                      # Environment config
├── test_api.py               # API test script
└── app/
    ├── api/
    │   ├── routes.py        # REST endpoints
    │   └── schemas.py       # Pydantic models
    ├── agent/
    │   ├── graph.py         # LangGraph workflow
    │   ├── nodes.py         # 5 agent nodes
    │   └── state.py         # Agent state definition
    ├── models/
    │   └── llm.py           # LLM integration
    ├── data/
    │   ├── mock_users.py    # Sample users
    │   └── selectors.py     # Audience filtering logic
    └── utils/
        └── metrics.py       # KPI calculations
```

## Installation

### Prerequisites

- Python 3.11+
- pip

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Or using pyproject.toml
pip install -e .

# Copy and configure environment
cp .env.example .env
# Edit .env with your Volc Engine API credentials (or leave as is for mock mode)
```

## Running the Server

### Development Mode (with auto-reload)

```bash
python main.py
```

The server will start on `http://0.0.0.0:8000`

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### 1. Health Check
```http
GET /api/v1/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-15T14:00:00"
}
```

### 2. Analyze Marketing Goal

**Non-streaming**:
```http
POST /api/v1/analysis
Content-Type: application/json

{
  "prompt": "我要为春季新款手袋上市做一次推广，目标是提升转化率，请帮我圈选高潜人群。",
  "stream": false
}
```

**Streaming (SSE)**:
```http
POST /api/v1/analysis/stream
Content-Type: application/json

{
  "prompt": "我要为春季新款手袋上市做一次推广，目标是提升转化率，请帮我圈选高潜人群。"
}
```

Response:
```json
{
  "audience": [
    {
      "id": "1",
      "name": "王女士",
      "tier": "VVIP",
      "score": 98,
      "recentStore": "上海恒隆广场店",
      "lastVisit": "3天前",
      "reason": "上月到访上海恒隆店3次 + 点击新品邮件",
      "matchScore": 95.5
    }
  ],
  "metrics": {
    "audienceSize": 8,
    "conversionRate": 0.09,
    "estimatedRevenue": 12960,
    "roi": 295.36,
    "reachRate": 0.8,
    "qualityScore": 85.5
  },
  "response": "已为您圈选高潜人群...",
  "thinkingSteps": [
    {
      "id": "1",
      "title": "业务意图与约束解析",
      "description": "...",
      "status": "completed"
    }
  ],
  "timestamp": "2026-01-15T14:00:00"
}
```

### 3. Get High-Potential Users

```http
GET /api/v1/users/high-potential?limit=50
```

### 4. Predict Metrics

```http
POST /api/v1/prediction/metrics

{
  "audienceSize": 100,
  "constraints": {}
}
```

Response:
```json
{
  "audienceSize": 100,
  "conversionRate": 0.075,
  "estimatedRevenue": 135000,
  "roi": 1250,
  "reachRate": 10.0,
  "qualityScore": 85.0
}
```

## Testing

Run the included test script:

```bash
python test_api.py
```

This will test all endpoints and display results.

## LangGraph Workflow

The agent executes a 5-step workflow:

```
Input: User's marketing prompt
   ↓
[1] Intent Analysis Node
   - Parse user input
   - Extract KPIs, target tiers, constraints
   ↓
[2] Feature Extraction Node
   - Generate filtering rules based on intent
   - Extract multi-dimensional features
   ↓
[3] Audience Selection Node
   - Apply filters to mock users
   - Calculate match scores
   - Rank and select top users
   ↓
[4] Prediction Optimization Node
   - Calculate conversion rates
   - Estimate revenue and ROI
   - Compute quality metrics
   ↓
[5] Response Generation Node
   - Generate natural language summary
   ↓
Output: Complete analysis with audience, metrics, and strategic recommendations
```

Each step is tracked as a "thinking step" for frontend visualization.

## Mock Mode

When Volc Engine credentials are not configured, the agent runs in **mock mode**:

- LLM calls return pre-defined responses for development
- All audience selection logic works with mock users
- Metrics calculations are fully functional
- Perfect for local development and testing

## Connecting to Volc Engine

To use real Volc Engine API:

1. Get credentials from Volc Engine console
2. Set environment variables:
   ```bash
   export VOLC_ACCESS_KEY=your_key
   export VOLC_SECRET_KEY=your_secret
   export VOLC_ENDPOINT_ID=your_endpoint_id
   ```

3. The SDK will automatically switch from mock to real API calls

## Frontend Integration

The frontend (Next.js/React) connects via:

```javascript
// Streaming analysis
const eventSource = new EventSource('/api/v1/analysis/stream');
eventSource.addEventListener('thinking_step', (e) => {
  const step = JSON.parse(e.data);
  // Update UI with step
});

// Final result
eventSource.addEventListener('analysis_complete', (e) => {
  const result = JSON.parse(e.data);
  // Display audience and metrics
});
```

## Customization

### Add New Agent Nodes

1. Create node function in `app/agent/nodes.py`
2. Add to state in `app/agent/state.py`
3. Connect in `app/agent/graph.py`

### Modify Audience Selection Rules

Edit `app/data/selectors.py`:
- `filter_by_tier()`: Membership tier filtering
- `filter_by_behavior()`: Behavior-based criteria
- `calculate_match_score()`: Custom scoring logic

### Update Metrics Calculation

Edit `app/utils/metrics.py` to change:
- Base conversion rate
- Revenue calculation formula
- Quality scoring formula

## Performance Considerations

- **Agent execution**: ~1-2 seconds with mock LLM (depends on real LLM latency)
- **User pool**: Currently 15 mock users, easily scales to millions with DB
- **Concurrent requests**: Uvicorn handles multiple concurrent analysis requests
- **Memory**: ~100MB for base app + cache

## Future Enhancements

- [ ] Real database integration (PostgreSQL)
- [ ] User session management
- [ ] A/B testing simulation
- [ ] Custom audience rule builder
- [ ] Campaign performance tracking
- [ ] Multi-language support
- [ ] Docker containerization
- [ ] OpenAPI schema documentation

## Troubleshooting

### Port 8000 already in use
```bash
# Kill existing process
lsof -ti:8000 | xargs kill -9

# Or use different port
ENVIRONMENT=development python main.py  # Update API_PORT in .env
```

### Import errors
```bash
# Reinstall dependencies
pip install --upgrade --force-reinstall -e .
```

### Volc Engine connection issues
- Check credentials in `.env`
- Agent will automatically fall back to mock mode
- Check logs for detailed error messages

## License

MIT

## Support

For issues and questions:
1. Check the API documentation at `http://localhost:8000/docs`
2. Review test cases in `test_api.py`
3. Check logs for error details
