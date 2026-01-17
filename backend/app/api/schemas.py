"""API request/response schemas."""
from typing import Optional, Any, Literal
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
    session_id: Optional[str] = Field(default=None, description="Session ID for multi-turn conversation")
    stream: Optional[bool] = Field(default=False, description="Whether to stream thinking steps")

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "我要为春季新款手袋上市做一次推广，目标是提升转化率，请帮我圈选高潜人群。",
                "session_id": None,
                "stream": False
            }
        }


class AnalysisResponse(BaseModel):
    """Response body for analysis endpoint."""
    session_id: str = Field(..., description="Session ID for this conversation")
    audience: list[User] = Field(..., description="Selected audience")
    metrics: PredictionMetrics = Field(..., description="Predicted metrics")
    response: str = Field(..., description="Agent's natural language response")
    thinkingSteps: list[ThinkingStep] = Field(..., description="Agent's thinking process")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc123-def456-ghi789",
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


class SessionResponse(BaseModel):
    """Response for session operations."""
    session_id: str = Field(..., description="Session ID")
    message: str = Field(..., description="Status message")
    created_at: Optional[str] = Field(default=None, description="Session creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc123-def456-ghi789",
                "message": "Session cleared. New session started.",
                "created_at": "2024-01-15T10:00:00"
            }
        }


class CampaignApplicationRequest(BaseModel):
    """Request body for campaign application endpoint."""
    session_id: str = Field(..., description="Session ID to apply")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc123-def456-ghi789"
            }
        }


class CampaignApplicationResponse(BaseModel):
    """Response body for campaign application endpoint."""
    status: str = Field(..., description="Application status")
    message: str = Field(..., description="Result message")
    campaign_summary: dict = Field(..., description="Summary of the applied campaign")
    mock_payload: dict = Field(..., description="Mock payload sent to marketing engine")
    timestamp: datetime = Field(default_factory=datetime.now, description="Application timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Campaign successfully applied to marketing engine",
                "campaign_summary": {
                    "target_audience_size": 100,
                    "estimated_revenue": 144000,
                    "target_tiers": ["VVIP", "VIP"]
                },
                "mock_payload": {
                    "campaign_id": "camp_123456",
                    "audience_ids": ["1", "2", "3"],
                    "kpi_target": "conversion_rate"
                },
                "timestamp": "2024-01-15T10:00:00"
            }
        }


# =====================================================
# New schemas for refactored workflow
# =====================================================

class MatchedFeature(BaseModel):
    """匹配到的特征."""
    feature_name: str = Field(..., description="特征名称")
    feature_type: str = Field(..., description="特征类型")
    operator: str = Field(..., description="操作符")
    value: Any = Field(..., description="特征值")
    description: str = Field(..., description="自然语言描述")

    class Config:
        json_schema_extra = {
            "example": {
                "feature_name": "r12m_spending",
                "feature_type": "numeric",
                "operator": ">",
                "value": 100000,
                "description": "近12个月消费额大于10万"
            }
        }


class UserIntent(BaseModel):
    """用户意图."""
    business_goal: str = Field(..., description="业务目标")
    target_audience: dict[str, Any] = Field(..., description="目标人群描述")
    constraints: list[str] = Field(..., description="约束条件")
    kpi: str = Field(..., description="核心KPI")
    size_preference: dict[str, int] = Field(..., description="人群规模偏好")

    class Config:
        json_schema_extra = {
            "example": {
                "business_goal": "提升春季新品转化率",
                "target_audience": {
                    "tier": ["VVIP", "VIP"],
                    "age_group": "25-44"
                },
                "constraints": ["排除近7天已购买用户"],
                "kpi": "conversion_rate",
                "size_preference": {"min": 100, "max": 500}
            }
        }


class TopUser(BaseModel):
    """Top用户信息."""
    name: str
    tier: str
    score: int
    r12m_spending: int

    class Config:
        json_schema_extra = {
            "example": {
                "name": "王女士",
                "tier": "VVIP",
                "score": 98,
                "r12m_spending": 1800000
            }
        }


class PredictionResult(BaseModel):
    """预测结果."""
    audience_size: int = Field(..., description="圈选人数")
    conversion_rate: float = Field(..., description="预估转化率")
    estimated_revenue: float = Field(..., description="预估收入")
    roi: float = Field(..., description="投资回报率")
    quality_score: float = Field(..., description="人群质量分")
    tier_distribution: dict[str, int] = Field(..., description="会员等级分布")
    top_users: list[TopUser] = Field(..., description="Top用户列表")

    class Config:
        json_schema_extra = {
            "example": {
                "audience_size": 100,
                "conversion_rate": 0.08,
                "estimated_revenue": 144000,
                "roi": 5.0,
                "quality_score": 85.5,
                "tier_distribution": {"VVIP": 30, "VIP": 50, "Member": 20},
                "top_users": []
            }
        }


class AnalysisResponseV2(BaseModel):
    """
    Response body for analysis endpoint - V2 (refactored workflow).

    支持多轮对话的响应格式。
    """
    session_id: str = Field(..., description="Session ID for this conversation")

    # 对话状态
    status: Literal["clarification_needed", "modification_needed", "success"] = Field(
        ..., description="响应状态"
    )

    # 返回的消息（可能是澄清问题、修正建议或最终结果）
    response: str = Field(..., description="Agent's response")

    # 当 status == "success" 时，以下字段有值
    user_intent: Optional[UserIntent] = Field(None, description="识别的用户意图")
    matched_features: Optional[list[MatchedFeature]] = Field(None, description="匹配的特征")
    strategy_explanation: Optional[str] = Field(None, description="策略解释")
    prediction_result: Optional[PredictionResult] = Field(None, description="预测结果")

    # 元数据
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc123-def456-ghi789",
                "status": "success",
                "response": "已为您圈选100人高潜人群...",
                "user_intent": {
                    "business_goal": "提升转化率",
                    "target_audience": {"tier": ["VVIP", "VIP"]},
                    "constraints": [],
                    "kpi": "conversion_rate",
                    "size_preference": {"min": 50, "max": 500}
                },
                "matched_features": [],
                "strategy_explanation": "根据您的需求...",
                "prediction_result": {
                    "audience_size": 100,
                    "conversion_rate": 0.08,
                    "estimated_revenue": 144000,
                    "roi": 5.0,
                    "quality_score": 85.5,
                    "tier_distribution": {},
                    "top_users": []
                },
                "timestamp": "2024-01-15T10:00:00"
            }
        }

