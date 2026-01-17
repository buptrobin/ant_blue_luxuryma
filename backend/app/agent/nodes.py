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

    Supports multi-turn conversations:
    - Uses conversation_context to understand history
    - Detects if user is modifying existing intent
    - Adjusts intent based on previous state
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
    conversation_context = state.get("conversation_context", "")
    is_modification = state.get("is_modification", False)
    previous_intent = state.get("previous_intent")

    intent = None
    try:
        # Use context-aware prompt for multi-turn
        if conversation_context and is_modification and previous_intent:
            # User is modifying existing intent - use non-streaming for simplicity
            prompt_context = f"""你是一个营销专家。用户正在修改现有的营销策略。

{conversation_context}

请分析用户的新输入，并基于当前策略进行**增量调整**。返回调整后的完整策略。

用户的新输入：{user_input}

请返回一个JSON格式的结果，包含以下字段：
- kpi: 核心KPI目标 (conversion_rate/revenue/visit_rate)
- target_tiers: 目标会员等级 (VVIP/VIP/Member)
- behavior_filters: 行为筛选条件
  - browse_frequency: 浏览频次阈值 (0-100)
  - engagement_level: 参与度级别 (high/medium/low)
- size_preference: 人群规模偏好
  - min: 最小规模
  - max: 最大规模
- constraints: 额外约束条件列表

只返回JSON，不要其他内容。"""

            intent = await llm.analyze_intent(prompt_context)
            logger.info(f"Modified intent based on context: {intent}")

        else:
            # Fresh analysis - use streaming for faster first token
            logger.info("Using streaming LLM call for intent analysis")
            chunk_count = 0
            async for event in llm.analyze_intent_stream(user_input):
                if event["type"] == "chunk":
                    chunk_count += 1
                    if chunk_count == 1:
                        logger.info(f"✅ First token received! Streaming in progress...")
                    # Log every 20 chunks to show progress
                    if chunk_count % 20 == 0:
                        logger.info(f"  Received {chunk_count} tokens...")
                elif event["type"] == "complete":
                    intent = event["data"]
                    logger.info(f"Extracted fresh intent (received {chunk_count} tokens total)")
                    logger.info(f"[DEBUG] Intent content: {intent}")  # Debug log
                    break
                elif event["type"] == "error":
                    raise Exception(event["data"])

    except Exception as e:
        logger.error(f"Error analyzing intent: {e}")
        intent = None

    # Fallback to default or previous intent if needed
    if intent is None:
        if previous_intent:
            intent = previous_intent
        else:
            intent = {
                "kpi": "conversion_rate",
                "target_tiers": ["VVIP", "VIP"],
                "behavior_filters": {},
                "size_preference": {"min": 50, "max": 500},
                "constraints": []
            }

    # Mark step as completed with detailed description
    kpi = intent.get('kpi', 'N/A')
    target_tiers = intent.get('target_tiers', [])
    behavior_filters = intent.get('behavior_filters', {})
    size_pref = intent.get('size_preference', {})
    constraints = intent.get('constraints', [])

    # Build detailed natural language description
    description_parts = []

    # KPI目标
    kpi_map = {
        'conversion_rate': '转化率（CVR）',
        'revenue': '营收增长',
        'visit_rate': '到店率',
        'engagement': '互动参与度'
    }
    description_parts.append(f"**核心KPI目标**: {kpi_map.get(kpi, kpi)}")

    # 目标人群等级
    if target_tiers:
        # Filter out None values
        target_tiers_filtered = [t for t in target_tiers if t is not None]
        if target_tiers_filtered:
            tier_desc = "、".join(target_tiers_filtered)
            description_parts.append(f"**目标客户等级**: {tier_desc}")

    # 行为筛选条件
    if behavior_filters:
        behavior_desc = []
        browse_freq = behavior_filters.get('browse_frequency')
        if browse_freq is not None:
            behavior_desc.append(f"浏览频次≥{browse_freq}")

        engagement = behavior_filters.get('engagement_level')
        if engagement is not None:
            level_map = {'high': '高', 'medium': '中', 'low': '低'}
            level_val = level_map.get(engagement, engagement)
            behavior_desc.append(f"参与度{level_val}")

        # Filter out None values before joining
        behavior_desc = [b for b in behavior_desc if b is not None]
        if behavior_desc:
            description_parts.append(f"**行为要求**: {', '.join(behavior_desc)}")

    # 人群规模偏好
    if size_pref:
        min_size = size_pref.get('min', 0)
        max_size = size_pref.get('max', 0)
        if min_size or max_size:
            description_parts.append(f"**人群规模**: {min_size}-{max_size}人")

    # 额外约束
    if constraints:
        # Filter out None values
        constraints_filtered = [c for c in constraints if c is not None]
        if constraints_filtered:
            description_parts.append(f"**约束条件**: {', '.join(constraints_filtered)}")

    # 是否是修改意图
    if is_modification:
        description_parts.insert(0, "🔄 **检测到意图修改** - 基于上一轮结果进行增量调整")

    thinking_steps[0]["description"] = "\n".join(description_parts)
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

    features = None
    try:
        # Use streaming for faster first token
        logger.info("Using streaming LLM call for feature extraction")
        chunk_count = 0
        async for event in llm.extract_features_stream(intent):
            if event["type"] == "chunk":
                chunk_count += 1
                if chunk_count == 1:
                    logger.info(f"✅ First token received! Streaming in progress...")
                if chunk_count % 20 == 0:
                    logger.info(f"  Received {chunk_count} tokens...")
            elif event["type"] == "complete":
                features = event["data"]
                logger.info(f"Extracted features (received {chunk_count} tokens total)")
                break
            elif event["type"] == "error":
                raise Exception(event["data"])
    except Exception as e:
        logger.error(f"Error extracting features: {e}")
        features = None

    # Fallback if needed
    if features is None:
        features = {
            "feature_rules": [],
            "weights": {},
            "explanation": "基于会员等级和行为特征的多维筛选"
        }

    # Build detailed natural language description
    description_parts = []

    # 特征维度说明
    target_tiers = intent.get('target_tiers', [])
    if target_tiers:
        # Filter out None values
        target_tiers_filtered = [t for t in target_tiers if t is not None]
        if target_tiers_filtered:
            description_parts.append(f"**会员等级筛选**: 定位{', '.join(target_tiers_filtered)}客户群体")

    # 行为特征
    behavior_filters = intent.get('behavior_filters', {})
    if behavior_filters:
        behavior_features = []
        browse_freq = behavior_filters.get('browse_frequency')
        if browse_freq is not None:
            behavior_features.append(f"高频浏览用户（阈值{browse_freq}）")

        engagement = behavior_filters.get('engagement_level')
        if engagement is not None:
            level_desc = {'high': '高度活跃', 'medium': '中度活跃', 'low': '低活跃度'}
            desc = level_desc.get(engagement, f'{engagement}活跃度')
            behavior_features.append(desc)

        # Filter out None values before joining
        behavior_features = [f for f in behavior_features if f is not None]
        if behavior_features:
            description_parts.append(f"**行为特征**: {', '.join(behavior_features)}")

    # 消费力分析
    kpi = intent.get('kpi', '')
    if kpi == 'revenue':
        description_parts.append("**消费力**: 优先圈选高客单价、复购率高的用户")
    elif kpi == 'conversion_rate':
        description_parts.append("**转化倾向**: 优先圈选高意向、浏览深度高的用户")
    elif kpi == 'visit_rate':
        description_parts.append("**到店意愿**: 优先圈选近期活跃、地理位置匹配的用户")

    # 特征权重说明
    weights = features.get('weights', {})
    if weights:
        weight_items = []
        for key, val in weights.items():
            if key is not None and val is not None:
                weight_items.append(f"{key}({val})")
        if weight_items:
            description_parts.append(f"**特征权重**: {', '.join(weight_items)}")

    # LLM生成的说明
    explanation = features.get('explanation', '')
    if explanation:
        description_parts.append(f"**策略说明**: {explanation}")

    # Mark step as completed
    thinking_steps[-1]["description"] = "\n".join(description_parts) if description_parts else "已完成多维特征提取"
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

    # Build detailed natural language description
    description_parts = []

    # 圈选结果概览
    total_selected = len(selected_users)
    description_parts.append(f"✅ **圈选完成**: 从全量用户中筛选出 **{total_selected}人** 高潜人群")

    # 会员等级分布
    tier_distribution = {}
    for user in selected_users:
        tier = user.get("tier", "Member")
        tier_distribution[tier] = tier_distribution.get(tier, 0) + 1

    if tier_distribution:
        tier_desc = []
        tier_order = ["VVIP", "VIP", "Member"]
        for tier in tier_order:
            if tier in tier_distribution:
                count = tier_distribution[tier]
                percentage = (count / total_selected * 100) if total_selected > 0 else 0
                tier_desc.append(f"{tier} {count}人({percentage:.0f}%)")
        if tier_desc:
            description_parts.append(f"**会员分布**: {' | '.join(tier_desc)}")

    # 平均匹配度
    if selected_users:
        avg_match_score = sum(u.get("matchScore", 0) for u in selected_users) / len(selected_users)
        description_parts.append(f"**平均匹配度**: {avg_match_score:.1f}分")

    # Top 3用户预览
    if selected_users:
        top_3 = selected_users[:3]
        top_users_desc = []
        for i, user in enumerate(top_3, 1):
            name = user.get("name", "未知")
            tier = user.get("tier", "Member")
            score = user.get("score", 0)
            match_score = user.get("matchScore", 0)
            top_users_desc.append(f"{i}. {name}({tier}, 基础{score}分, 匹配{match_score:.1f}分)")

        description_parts.append(f"**Top 3用户**:\n" + "\n".join(top_users_desc))

    # 筛选策略说明
    target_tiers = intent.get('target_tiers', [])
    if target_tiers:
        # Filter out None values
        target_tiers_filtered = [t for t in target_tiers if t is not None]
        if target_tiers_filtered:
            description_parts.append(f"**筛选策略**: 定位{'/'.join(target_tiers_filtered)}等级，匹配度加权排序")

    # 数据质量评估
    if total_selected > 0:
        if total_selected < 10:
            description_parts.append("⚠️ **建议**: 当前人群规模较小，可考虑放宽筛选条件扩大覆盖")
        elif total_selected > 200:
            description_parts.append("💡 **建议**: 人群规模较大，可进一步提升筛选精准度")
        else:
            description_parts.append("✨ **评估**: 人群规模合理，匹配度良好")

    # Mark step as completed
    thinking_steps[-1]["description"] = "\n".join(description_parts) if description_parts else f"已圈选{total_selected}人"
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

    thinking_steps = state.get("thinking_steps", [])
    audience = state.get("audience", [])

    # Add fourth thinking step
    thinking_steps.append({
        "id": "4",
        "title": "效果预测与优化",
        "description": "正在计算转化率、ROI等核心指标...",
        "status": "active"
    })

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

    # Build detailed natural language description
    description_parts = []

    # 核心指标预测
    description_parts.append("📊 **核心指标预测**")

    # 转化率
    conversion_rate = metrics.get("conversion_rate", 0)
    description_parts.append(f"• **预估转化率**: {conversion_rate:.2%}")
    if conversion_rate > 0.10:
        description_parts.append("  ✨ 转化率表现优秀")
    elif conversion_rate > 0.05:
        description_parts.append("  ✓ 转化率表现良好")
    else:
        description_parts.append("  ⚠️ 转化率偏低，建议优化人群质量")

    # 预估收入
    estimated_revenue = metrics.get("estimated_revenue", 0)
    description_parts.append(f"• **预估收入**: ¥{estimated_revenue:,.0f}")

    # ROI
    roi = metrics.get("roi", 0)
    description_parts.append(f"• **投资回报率(ROI)**: {roi:.2f}倍")
    if roi > 5:
        description_parts.append("  🎯 ROI表现优异，建议立即执行")
    elif roi > 3:
        description_parts.append("  ✓ ROI达标，可以执行")
    else:
        description_parts.append("  ⚠️ ROI偏低，建议优化策略")

    # 触达率
    reach_rate = metrics.get("reach_rate", 0)
    description_parts.append(f"• **触达率**: {reach_rate:.1f}%")

    # 人群质量分
    quality_score = metrics.get("quality_score", 0)
    description_parts.append(f"• **人群质量分**: {quality_score:.1f}分")

    # 人群规模分析
    description_parts.append(f"\n📈 **人群规模分析**")
    description_parts.append(f"• 目标人群: {audience_size}人")

    # 各等级预估收入
    if tier_distribution:
        from app.data.mock_users import TIER_AVG_ORDER_VALUE
        tier_revenue_parts = []
        for tier in ["VVIP", "VIP", "Member"]:
            count = tier_distribution.get(tier, 0)
            if count > 0:
                avg_order = TIER_AVG_ORDER_VALUE.get(tier, 18000)
                tier_revenue = count * conversion_rate * avg_order
                tier_revenue_parts.append(f"  • {tier}: {count}人 × {conversion_rate:.1%} × ¥{avg_order:,} = ¥{tier_revenue:,.0f}")

        if tier_revenue_parts:
            description_parts.append("• 分层收入贡献:")
            description_parts.extend(tier_revenue_parts)

    # 优化建议
    description_parts.append(f"\n💡 **优化建议**")

    if audience_size < 50:
        description_parts.append("• 人群规模偏小，建议适当放宽筛选条件")

    if avg_score < 80:
        description_parts.append("• 平均匹配度偏低，建议提升特征权重")

    if tier_distribution.get("VVIP", 0) / audience_size > 0.7 if audience_size > 0 else False:
        description_parts.append("• VVIP占比高，建议增加个性化服务触点")

    if conversion_rate < 0.05:
        description_parts.append("• 转化率较低，建议优化营销文案和触达渠道")

    # Mark step as completed
    thinking_steps[-1]["description"] = "\n".join(description_parts)
    thinking_steps[-1]["status"] = "completed"

    return {
        "metrics": metrics,
        "thinking_steps": thinking_steps
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

    thinking_steps = state.get("thinking_steps", [])
    audience = state.get("audience", [])
    metrics = state.get("metrics", {})
    intent = state.get("intent", {})

    # Add fifth thinking step
    thinking_steps.append({
        "id": "5",
        "title": "策略总结与建议",
        "description": "正在生成营销策略总结...",
        "status": "active"
    })

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

    response = None
    try:
        # Use streaming for faster first token
        logger.info("Using streaming LLM call for response generation")
        chunk_count = 0
        async for event in llm.generate_response_stream(analysis_summary):
            if event["type"] == "chunk":
                chunk_count += 1
                if chunk_count == 1:
                    logger.info(f"✅ First token received! Streaming in progress...")
                if chunk_count % 20 == 0:
                    logger.info(f"  Received {chunk_count} tokens...")
            elif event["type"] == "complete":
                response = event["data"]
                logger.info(f"Generated response (received {chunk_count} tokens total)")
                break
            elif event["type"] == "error":
                raise Exception(event["data"])
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        response = None

    # Fallback if needed
    if response is None:
        response = f"已为您圈选{len(audience)}人高潜人群。预估转化率{metrics.get('conversion_rate', 0):.1%}，预估收入¥{metrics.get('estimated_revenue', 0):,.0f}。"

    # Update thinking step with summary
    thinking_steps[-1]["description"] = f"✅ 分析完成\n\n{response}"
    thinking_steps[-1]["status"] = "completed"

    return {
        "final_response": response,
        "thinking_steps": thinking_steps
    }


# Node registry for easy access
AGENT_NODES = {
    "intent_analysis": intent_analysis_node,
    "feature_extraction": feature_extraction_node,
    "audience_selection": audience_selection_node,
    "prediction_optimization": prediction_optimization_node,
    "response_generation": response_generation_node,
}
