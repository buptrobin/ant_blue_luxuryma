"""LangGraph state definition for the marketing agent - Refactored for multi-turn dialogue."""
from typing import TypedDict, Any, Literal
from langgraph.graph import MessagesState


class UserIntent(TypedDict, total=False):
    """结构化的用户意图."""
    business_goal: str  # 业务目标 (如 "提升转化率", "扩大客户群")
    target_audience: dict[str, Any]  # 目标人群描述 (如 {"tier": ["VVIP", "VIP"], "age": "25-34"})
    constraints: list[str]  # 约束条件 (如 ["排除近期已购买用户", "预算限制"])
    kpi: str  # 核心KPI (如 "conversion_rate", "revenue", "visit_rate")
    size_preference: dict[str, int]  # 人群规模偏好 (如 {"min": 50, "max": 500})


class MatchedFeature(TypedDict):
    """匹配到的特征."""
    feature_name: str  # 特征名称 (如 "r12m_spending", "gender")
    feature_type: str  # 特征类型 (如 "numeric", "categorical", "boolean")
    operator: str  # 操作符 (如 ">", "==", "in")
    value: Any  # 特征值 (如 100000, "F", ["VVIP", "VIP"])
    description: str  # 自然语言描述 (如 "近12个月消费额大于10万")


class PredictionResult(TypedDict, total=False):
    """预测结果."""
    audience_size: int  # 圈选人数
    conversion_rate: float  # 预估转化率
    estimated_revenue: float  # 预估收入
    roi: float  # 投资回报率
    quality_score: float  # 人群质量分
    top_users: list[dict[str, Any]]  # Top用户列表
    tier_distribution: dict[str, int]  # 会员等级分布


class AgentState(MessagesState, total=False):
    """
    State for the marketing agent - Multi-turn dialogue workflow.

    继承自 MessagesState，自动包含 messages 字段用于聊天历史。
    """
    # ========== 用户输入 ==========
    user_input: str  # 当前用户输入

    # ========== 意图识别 ==========
    user_intent: UserIntent  # 结构化的用户意图
    intent_status: Literal["ambiguous", "clear"]  # 意图识别状态
    intent_summary: str  # 意图识别的自然语言摘要 (新增)

    # ========== 特征匹配 ==========
    matched_features: list[MatchedFeature]  # 匹配到的特征列表
    match_status: Literal["success", "needs_refinement"]  # 特征匹配状态
    feature_summary: str  # 特征匹配的自然语言摘要 (新增)

    # ========== 策略生成 ==========
    strategy_explanation: str  # 策略解释（自然语言）
    strategy_summary: str  # 策略摘要 (新增)

    # ========== 效果预测 ==========
    prediction_result: PredictionResult  # 预测/分析数据

    # ========== 最终输出 ==========
    final_response: str  # 最终回复
    segmentation_proposal: dict[str, Any]  # 结构化的圈人方案 (新增)

    # ========== 中间状态 ==========
    clarification_question: str  # 澄清问题（用于反问用户）
    modification_request: str  # 修正请求（用于引导用户修改意图）

    # ========== 多轮对话支持 ==========
    conversation_context: str  # 对话上下文（文本摘要）
    previous_intent: UserIntent  # 上一轮的用户意图（用于融合）
    is_modification: bool  # 是否是修改现有需求
