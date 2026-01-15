"""API request/response schemas."""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class User(BaseModel):
    """User data model."""
    id: str
    name: str
    tier: str  # 'VVIP', 'VIP', 'Member'
    score: int
    recentStore: str
    lastVisit: str
    reason: str
    matchScore: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "1",
                "name": "王女士",
                "tier": "VVIP",
                "score": 98,
                "recentStore": "上海恒隆广场店",
                "lastVisit": "3天前",
                "reason": "上月到访上海恒隆店3次 + 点击新品邮件",
                "matchScore": 95.5
            }
        }


class ThinkingStep(BaseModel):
    """A step in the agent's thinking process."""
    id: str = Field(..., description="Step ID")
    title: str = Field(..., description="Step title")
    description: str = Field(..., description="Step description")
    status: str = Field(..., description="Step status: pending, active, completed")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "1",
                "title": "业务意图与约束解析",
                "description": "核心目标：提升转化率 (CVR)...",
                "status": "completed"
            }
        }


class PredictionMetrics(BaseModel):
    """Prediction metrics model."""
    audienceSize: int = Field(..., description="Number of selected users")
    conversionRate: float = Field(..., description="Estimated conversion rate (0-1)")
    estimatedRevenue: float = Field(..., description="Estimated revenue in CNY")
    roi: Optional[float] = None
    reachRate: Optional[float] = None
    qualityScore: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "audienceSize": 100,
                "conversionRate": 0.08,
                "estimatedRevenue": 144000,
                "roi": 1340,
                "reachRate": 10.0,
                "qualityScore": 85.5
            }
        }


class AnalysisRequest(BaseModel):
    """Request body for analysis endpoint."""
    prompt: str = Field(..., description="User's marketing goal/prompt")
    stream: Optional[bool] = Field(default=False, description="Whether to stream thinking steps")

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "我要为春季新款手袋上市做一次推广，目标是提升转化率，请帮我圈选高潜人群。",
                "stream": False
            }
        }


class AnalysisResponse(BaseModel):
    """Response body for analysis endpoint."""
    audience: list[User] = Field(..., description="Selected audience")
    metrics: PredictionMetrics = Field(..., description="Predicted metrics")
    response: str = Field(..., description="Agent's natural language response")
    thinkingSteps: list[ThinkingStep] = Field(..., description="Agent's thinking process")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")

    class Config:
        json_schema_extra = {
            "example": {
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
                    "audienceSize": 100,
                    "conversionRate": 0.08,
                    "estimatedRevenue": 144000,
                    "roi": 1340,
                    "reachRate": 10.0,
                    "qualityScore": 85.5
                },
                "response": "已为您圈选100人高潜人群...",
                "thinkingSteps": [
                    {
                        "id": "1",
                        "title": "业务意图与约束解析",
                        "description": "...",
                        "status": "completed"
                    }
                ],
                "timestamp": "2024-01-15T10:00:00"
            }
        }


class UserListResponse(BaseModel):
    """Response for user list endpoint."""
    users: list[User]
    total: int

    class Config:
        json_schema_extra = {
            "example": {
                "users": [],
                "total": 0
            }
        }


class PredictionRequest(BaseModel):
    """Request body for prediction endpoint."""
    audienceSize: int = Field(..., description="Size of the audience")
    constraints: Optional[dict] = Field(default=None, description="Additional constraints")

    class Config:
        json_schema_extra = {
            "example": {
                "audienceSize": 100,
                "constraints": {}
            }
        }


class MetricsEventData(BaseModel):
    """SSE event data for streaming metrics."""
    stepId: str = Field(..., description="Thinking step ID")
    title: str = Field(..., description="Step title")
    description: str = Field(..., description="Step description")
    status: str = Field(..., description="Step status")
