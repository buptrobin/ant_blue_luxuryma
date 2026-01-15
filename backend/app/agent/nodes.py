"""LangGraph nodes for the marketing agent."""
import logging
from typing import Any

from app.agent.state import AgentState, ThinkingStep
from app.models.llm import get_llm_manager
from app.data.selectors import select_audience
from app.data.mock_users import MOCK_USERS
from app.utils.metrics import get_calculator

logger = logging.getLogger(__name__)


async def intent_analysis_node(state: AgentState) -> dict[str, Any]:
    """
    Node 1: Analyze user intent and extract marketing goals.

    Parses the user's input to identify:
    - Primary KPI (conversion rate, revenue, etc.)
    - Target audience tiers
    - Behavioral criteria
    - Constraints and preferences
    """
    logger.info("Executing intent_analysis_node")

    # Update thinking steps
    thinking_steps = state.get("thinking_steps", [])
    thinking_steps = [
        {
            "id": "1",
            "title": "业务意图与约束解析",
            "description": "正在分析营销目标和核心KPI...",
            "status": "active"
        }
    ]

    # Get LLM manager and analyze intent
    llm = get_llm_manager()
    user_input = state["user_input"]

    try:
        intent = await llm.analyze_intent(user_input)
        logger.info(f"Extracted intent: {intent}")
    except Exception as e:
        logger.error(f"Error analyzing intent: {e}")
        # Fallback to default intent
        intent = {
            "kpi": "conversion_rate",
            "target_tiers": ["VVIP", "VIP"],
            "behavior_filters": {},
            "size_preference": {"min": 50, "max": 500},
            "constraints": []
        }

    # Mark step as completed
    thinking_steps[0]["status"] = "completed"

    return {
        "intent": intent,
        "thinking_steps": thinking_steps
    }


async def feature_extraction_node(state: AgentState) -> dict[str, Any]:
    """
    Node 2: Extract multi-dimensional features for audience segmentation.

    Based on the identified intent, generates:
    - Filtering rules for different user dimensions
    - Feature weights and importance
    - Business logic explanations
    """
    logger.info("Executing feature_extraction_node")

    thinking_steps = state.get("thinking_steps", [])
    intent = state.get("intent", {})

    # Add second thinking step
    thinking_steps.append({
        "id": "2",
        "title": "多维特征扫描",
        "description": "正在提取人群的消费力、兴趣、活跃度等特征...",
        "status": "active"
    })

    llm = get_llm_manager()

    try:
        features = await llm.extract_features(intent)
        logger.info(f"Extracted features: {features}")
    except Exception as e:
        logger.error(f"Error extracting features: {e}")
        features = {
            "feature_rules": [],
            "weights": {},
            "explanation": "基于会员等级和行为特征的多维筛选"
        }

    # Mark step as completed
    thinking_steps[-1]["status"] = "completed"

    return {
        "features": features,
        "thinking_steps": thinking_steps
    }


async def audience_selection_node(state: AgentState) -> dict[str, Any]:
    """
    Node 3: Select audience based on intent and features.

    Applies filtering rules to the user pool:
    - Filters by membership tier
    - Applies behavior criteria
    - Calculates match scores
    - Returns ranked audience list
    """
    logger.info("Executing audience_selection_node")

    thinking_steps = state.get("thinking_steps", [])
    intent = state.get("intent", {})

    # Add third thinking step
    thinking_steps.append({
        "id": "3",
        "title": "人群策略组合计算",
        "description": "正在应用筛选规则并计算人群策略...",
        "status": "active"
    })

    try:
        # Select audience based on intent
        selected_users, metadata = select_audience(intent, MOCK_USERS)
        logger.info(f"Selected {len(selected_users)} users. Metadata: {metadata}")
    except Exception as e:
        logger.error(f"Error selecting audience: {e}")
        selected_users = []
        metadata = {}

    # Mark step as completed
    thinking_steps[-1]["status"] = "completed"

    return {
        "audience": selected_users,
        "thinking_steps": thinking_steps
    }


async def prediction_optimization_node(state: AgentState) -> dict[str, Any]:
    """
    Node 4: Predict campaign performance and optimize.

    Calculates key metrics:
    - Conversion rate based on audience size and quality
    - Estimated revenue
    - ROI
    - Audience quality score
    """
    logger.info("Executing prediction_optimization_node")

    audience = state.get("audience", [])

    # Calculate metrics
    calculator = get_calculator()
    audience_size = len(audience)
    avg_score = sum(u.get("matchScore", 0) for u in audience) / audience_size if audience else 0

    # Count tier distribution
    tier_distribution = {"VVIP": 0, "VIP": 0, "Member": 0}
    for user in audience:
        tier = user.get("tier", "Member")
        if tier in tier_distribution:
            tier_distribution[tier] += 1

    try:
        metrics = calculator.estimate_metrics(
            audience_size=audience_size,
            avg_user_score=avg_score,
            audience_tier_distribution=tier_distribution
        )
        logger.info(f"Calculated metrics: {metrics}")
    except Exception as e:
        logger.error(f"Error calculating metrics: {e}")
        metrics = {
            "audience_size": audience_size,
            "conversion_rate": 0,
            "estimated_revenue": 0,
            "roi": 0,
            "reach_rate": 0,
            "quality_score": 0
        }

    return {
        "metrics": metrics
    }


async def response_generation_node(state: AgentState) -> dict[str, Any]:
    """
    Node 5: Generate natural language response.

    Creates a human-readable summary of:
    - Selected audience insights
    - Key metrics and KPIs
    - Strategic recommendations
    """
    logger.info("Executing response_generation_node")

    audience = state.get("audience", [])
    metrics = state.get("metrics", {})
    intent = state.get("intent", {})

    # Prepare analysis summary
    analysis_summary = {
        "audience_size": len(audience),
        "avg_score": sum(u.get("matchScore", 0) for u in audience) / len(audience) if audience else 0,
        "conversion_rate": metrics.get("conversion_rate", 0),
        "estimated_revenue": metrics.get("estimated_revenue", 0),
        "roi": metrics.get("roi", 0),
        "reach_rate": metrics.get("reach_rate", 0),
        "quality_score": metrics.get("quality_score", 0),
        "kpi": intent.get("kpi", "")
    }

    llm = get_llm_manager()

    try:
        response = await llm.generate_response(analysis_summary)
        logger.info(f"Generated response: {response}")
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        response = f"已为您圈选{len(audience)}人高潜人群。预估转化率{metrics.get('conversion_rate', 0):.1%}，预估收入¥{metrics.get('estimated_revenue', 0):,.0f}。"

    return {
        "final_response": response
    }


# Node registry for easy access
AGENT_NODES = {
    "intent_analysis": intent_analysis_node,
    "feature_extraction": feature_extraction_node,
    "audience_selection": audience_selection_node,
    "prediction_optimization": prediction_optimization_node,
    "response_generation": response_generation_node,
}
