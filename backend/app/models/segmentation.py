"""
Segmentation proposal and result models.
"""

from typing import Any, Optional
from pydantic import BaseModel, Field


class FeatureRule(BaseModel):
    """特征规则定义"""
    key: str = Field(..., description="特征键名，如 R12M_Amount")
    operator: str = Field(..., description="操作符，如 >=, between, in")
    value: Any = Field(..., description="特征值")
    description: str = Field(..., description="用于展示的描述文案")


class TargetTrait(BaseModel):
    """目标特征分类"""
    category: str = Field(..., description="特征类别，如 消费门槛、品类兴趣")
    rules: list[FeatureRule] = Field(default_factory=list, description="该类别下的规则列表")


class SegmentationProposal(BaseModel):
    """圈人方案 - Agent产出的结构化数据"""
    marketing_goal: str = Field(..., description="营销目标")
    constraints: list[str] = Field(default_factory=list, description="约束条件列表")
    target_traits: list[TargetTrait] = Field(default_factory=list, description="具体的特征条件")
    kpi: str = Field(..., description="核心KPI")
    target_audience: dict[str, Any] = Field(default_factory=dict, description="目标人群描述")


class SegmentationResult(BaseModel):
    """圈选结果 - 后端返回的预测结果"""
    audience_count: int = Field(..., description="目标人群数量")
    est_conversion_rate: float = Field(..., description="预估转化率（小数）")
    est_revenue: float = Field(..., description="预估营收")
    roi: Optional[float] = Field(None, description="投资回报率")
    trait_breakdown: SegmentationProposal = Field(..., description="回传确认的圈选逻辑")
    audience: Optional[list[dict[str, Any]]] = Field(None, description="圈选的用户列表")
    tier_distribution: Optional[dict[str, int]] = Field(None, description="会员等级分布")
