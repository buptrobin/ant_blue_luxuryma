"""Streaming nodes with step-by-step reasoning for the marketing agent."""
import logging
import json
import re
from typing import Any, AsyncIterator

from app.agent.state import AgentState, UserIntent, MatchedFeature, PredictionResult
from app.models.llm import get_llm_manager
from app.data.feature_metadata import FEATURE_METADATA
from app.data.mock_users import MOCK_USERS_WITH_FEATURES, TIER_AVG_ORDER_VALUE

logger = logging.getLogger(__name__)


# =====================================================
# Helper Functions for Streaming with Reasoning
# =====================================================
async def stream_llm_with_reasoning(
    prompt: str,
    max_tokens: int = 800
) -> AsyncIterator[dict[str, Any]]:
    """
    Stream LLM response with step-by-step reasoning.

    Yields:
        Dict with 'type' and 'data':
        - {"type": "reasoning", "data": str} - Reasoning step text
        - {"type": "result", "data": dict} - Final parsed result
        - {"type": "error", "data": str} - Error message
    """
    llm = get_llm_manager()
    full_response = ""

    try:
        async for chunk in llm.model.stream(prompt, max_tokens=max_tokens):
            full_response += chunk
            # Stream raw chunks as reasoning steps
            yield {"type": "reasoning", "data": chunk}

        # Try to parse final result
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', full_response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                yield {"type": "result", "data": result}
            else:
                # No JSON found, return full text as result
                yield {"type": "result", "data": {"text": full_response}}
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON from: {full_response[:200]}...")
            yield {"type": "result", "data": {"text": full_response}}

    except Exception as e:
        logger.error(f"Error in stream_llm_with_reasoning: {e}")
        yield {"type": "error", "data": str(e)}


# =====================================================
# Node A: intent_recognition (streaming version)
# =====================================================
async def intent_recognition_node_stream(state: AgentState) -> AsyncIterator[dict[str, Any]]:
    """
    Node A: 意图识别 (流式版本)

    分析用户输入并流式返回推理过程。

    Yields:
        - {"type": "node_start", "node": "intent_recognition"}
        - {"type": "reasoning", "data": str} - 推理步骤
        - {"type": "node_complete", "data": {...}} - 节点结果
    """
    logger.info("Executing intent_recognition_node_stream")

    yield {"type": "node_start", "node": "intent_recognition", "title": "意图识别"}

    user_input = state.get("user_input", "")

    # 构建带推理的提示词
    prompt = f"""你是一个营销专家，负责分析用户的圈人需求。

用户输入：{user_input}

请按照以下步骤分析：

1. **理解需求**：用户想要达到什么业务目标？
2. **识别人群**：用户想圈选哪类人群？（会员等级、年龄、消费力等）
3. **提取约束**：有什么限制条件？（规模、预算、排除条件等）
4. **判断清晰度**：用户的意图是否足够明确？

请先用自然语言逐步分析你的推理过程，然后在最后返回JSON格式的结果：

{{
  "reasoning": "这里写你的推理过程，逐步分析...",
  "summary": "用1-2句话总结你对用户意图的理解，例如：'您希望针对春季新品手袋上市，圈选25-44岁的VVIP和VIP客户，以提升产品转化率。'",
  "business_goal": "业务目标",
  "target_audience": {{...}},
  "constraints": [...],
  "kpi": "conversion_rate/revenue/visit_rate",
  "size_preference": {{"min": 最小人数, "max": 最大人数}},
  "is_clear": true/false
}}

重要：
1. 只有当用户明确提供了业务目标、目标人群特征时，is_clear才为true
2. summary字段要用简洁、专业的语言总结意图，让用户确认理解是否正确
"""

    try:
        full_response = ""
        reasoning_text = ""

        # Stream the LLM response with reasoning
        async for event in stream_llm_with_reasoning(prompt, max_tokens=600):
            if event["type"] == "reasoning":
                reasoning_text += event["data"]
                # Stream reasoning chunks to frontend
                yield {
                    "type": "reasoning",
                    "node": "intent_recognition",
                    "data": event["data"]
                }

            elif event["type"] == "result":
                result = event["data"]

                # Parse the result
                is_clear = result.get("is_clear", True)

                user_intent: UserIntent = {
                    "business_goal": result.get("business_goal", ""),
                    "target_audience": result.get("target_audience", {}),
                    "constraints": result.get("constraints", []),
                    "kpi": result.get("kpi", "conversion_rate"),
                    "size_preference": result.get("size_preference", {"min": 50, "max": 500}),
                }

                # 提取自然语言摘要
                summary = result.get("summary", "")
                if not summary:
                    # 如果LLM没有返回summary，生成一个简单的
                    goal = user_intent.get("business_goal", "营销活动")
                    summary = f"理解您的需求：{goal}"

                # Yield node completion with natural language summary
                yield {
                    "type": "node_complete",
                    "node": "intent_recognition",
                    "data": {
                        "user_intent": user_intent,
                        "intent_status": "clear" if is_clear else "ambiguous",
                        "reasoning": result.get("reasoning", reasoning_text[:500]),
                        "summary": summary,  # 新增：自然语言摘要
                        "display_text": f"✓ 意图识别完成\n\n{summary}"  # 新增：前端显示文本
                    }
                }
                return

            elif event["type"] == "error":
                logger.error(f"Error in intent recognition: {event['data']}")
                yield {
                    "type": "node_complete",
                    "node": "intent_recognition",
                    "data": {
                        "user_intent": {
                            "business_goal": "",
                            "target_audience": {},
                            "constraints": [],
                            "kpi": "conversion_rate",
                            "size_preference": {"min": 50, "max": 500},
                        },
                        "intent_status": "ambiguous",
                        "error": event["data"]
                    }
                }
                return

    except Exception as e:
        logger.error(f"Error in intent_recognition_node_stream: {e}")
        yield {
            "type": "node_complete",
            "node": "intent_recognition",
            "data": {
                "user_intent": {
                    "business_goal": "",
                    "target_audience": {},
                    "constraints": [],
                    "kpi": "conversion_rate",
                    "size_preference": {"min": 50, "max": 500},
                },
                "intent_status": "ambiguous",
                "error": str(e)
            }
        }


# =====================================================
# Node C: feature_matching (streaming version)
# =====================================================
async def feature_matching_node_stream(state: AgentState) -> AsyncIterator[dict[str, Any]]:
    """
    Node C: 特征匹配 (流式版本)

    将用户意图映射到具体的数据库特征字段，并流式返回推理过程。

    Yields:
        - {"type": "node_start", "node": "feature_matching"}
        - {"type": "reasoning", "data": str} - 推理步骤
        - {"type": "node_complete", "data": {...}} - 节点结果
    """
    logger.info("Executing feature_matching_node_stream")

    yield {"type": "node_start", "node": "feature_matching", "title": "特征匹配"}

    user_intent = state.get("user_intent", {})

    # 准备特征元数据摘要
    feature_summary = {}
    for name, meta in FEATURE_METADATA.items():
        feature_summary[name] = {
            "display_name": meta["display_name"],
            "type": meta["type"],
            "description": meta["description"],
            "examples": meta["examples"][:2],
        }

    # 构建带推理的提示词
    prompt = f"""你是一个数据分析专家。用户想进行人群圈选，你需要将用户意图映射到具体的数据库特征字段。

用户意图：
{json.dumps(user_intent, ensure_ascii=False, indent=2)}

可用的特征字段：
{json.dumps(feature_summary, ensure_ascii=False, indent=2)}

请按照以下步骤分析：

1. **分析需求**：用户意图中包含哪些关键条件？
2. **匹配特征**：每个条件对应哪些数据库特征？
3. **选择操作符**：使用什么操作符（>、>=、in、between等）？
4. **验证可行性**：现有特征是否能完全满足需求？

请先用自然语言逐步分析你的推理过程，然后在最后返回JSON格式的结果：

{{
  "reasoning": "这里写你的推理过程...",
  "summary": "用简洁的语言描述匹配到的特征，例如：'已为您匹配4个关键特征：会员等级（VVIP/VIP）、年龄段（25-44岁）、手袋浏览兴趣、高消费力（年消费>5万）。'",
  "matched_features": [
    {{
      "feature_name": "特征名称",
      "operator": "操作符",
      "value": "特征值",
      "description": "自然语言描述"
    }}
  ],
  "is_success": true/false,
  "reason": "如果失败，说明原因"
}}

注意：
1. 如果某些条件无法用现有特征表达，设置 is_success=false
2. summary要清晰列出匹配到的特征维度，让用户快速了解圈选条件
"""

    try:
        async for event in stream_llm_with_reasoning(prompt, max_tokens=700):
            if event["type"] == "reasoning":
                yield {
                    "type": "reasoning",
                    "node": "feature_matching",
                    "data": event["data"]
                }

            elif event["type"] == "result":
                result = event["data"]

                is_success = result.get("is_success", True)
                matched_features_raw = result.get("matched_features", [])

                # 转换为 MatchedFeature 类型
                matched_features: list[MatchedFeature] = []
                for feat in matched_features_raw:
                    meta = FEATURE_METADATA.get(feat.get("feature_name"))
                    if meta:
                        matched_features.append({
                            "feature_name": feat.get("feature_name", ""),
                            "feature_type": meta["type"],
                            "operator": feat.get("operator", "=="),
                            "value": feat.get("value"),
                            "description": feat.get("description", ""),
                        })

                # 提取自然语言摘要
                summary = result.get("summary", "")
                if not summary and matched_features:
                    # 如果LLM没有返回summary，生成一个简单的
                    feature_count = len(matched_features)
                    summary = f"已为您匹配{feature_count}个关键特征，用于精准圈选目标人群。"

                # 构建前端显示文本
                display_lines = [f"✓ 特征匹配完成\n\n{summary}\n"]
                if matched_features:
                    display_lines.append("匹配的特征：")
                    for i, feat in enumerate(matched_features[:5], 1):  # 只显示前5个
                        display_lines.append(f"{i}. {feat['description']}")
                    if len(matched_features) > 5:
                        display_lines.append(f"... 及其他{len(matched_features) - 5}个特征")

                display_text = "\n".join(display_lines)

                yield {
                    "type": "node_complete",
                    "node": "feature_matching",
                    "data": {
                        "matched_features": matched_features,
                        "match_status": "success" if is_success else "needs_refinement",
                        "reasoning": result.get("reasoning", ""),
                        "summary": summary,  # 新增：自然语言摘要
                        "display_text": display_text  # 新增：前端显示文本
                    }
                }
                return

            elif event["type"] == "error":
                yield {
                    "type": "node_complete",
                    "node": "feature_matching",
                    "data": {
                        "matched_features": [],
                        "match_status": "needs_refinement",
                        "error": event["data"]
                    }
                }
                return

    except Exception as e:
        logger.error(f"Error in feature_matching_node_stream: {e}")
        yield {
            "type": "node_complete",
            "node": "feature_matching",
            "data": {
                "matched_features": [],
                "match_status": "needs_refinement",
                "error": str(e)
            }
        }


# =====================================================
# Node E: strategy_generation (streaming version)
# =====================================================
async def strategy_generation_node_stream(state: AgentState) -> AsyncIterator[dict[str, Any]]:
    """
    Node E: 策略生成 (流式版本)

    用自然语言解释如何组合这些特征来满足圈人意图，并流式返回。
    """
    logger.info("Executing strategy_generation_node_stream")

    yield {"type": "node_start", "node": "strategy_generation", "title": "策略生成"}

    user_intent = state.get("user_intent", {})
    matched_features = state.get("matched_features", [])

    prompt = f"""你是一个营销策略专家。用户想进行人群圈选，你已经匹配好了特征，现在需要生成策略解释。

用户意图：
{json.dumps(user_intent, ensure_ascii=False, indent=2)}

匹配的特征：
{json.dumps(matched_features, ensure_ascii=False, indent=2)}

请按照以下思路生成策略：

1. **目标定位**：我们要圈选什么样的人群？
2. **特征组合**：如何组合这些特征来实现目标？
3. **预期效果**：这个策略为什么有效？

请先用自然语言分析推理过程，然后返回JSON格式：

{{
  "reasoning": "推理过程...",
  "strategy_summary": "用2-3句话概括策略核心，例如：'本次圈选策略锁定高价值VIP客户群体，通过消费力和品类兴趣双重筛选，预计能够精准触达300-500位高转化潜力用户。'",
  "strategy_detail": "详细的策略说明（200-300字），包含：目标人群定位、行为筛选逻辑、预期效果等。格式清晰，分段说明。"
}}

要求：
1. strategy_summary要简洁有力，突出策略核心价值
2. strategy_detail要专业详细，让用户理解圈选逻辑
"""

    try:
        async for event in stream_llm_with_reasoning(prompt, max_tokens=600):
            if event["type"] == "reasoning":
                yield {
                    "type": "reasoning",
                    "node": "strategy_generation",
                    "data": event["data"]
                }

            elif event["type"] == "result":
                result = event["data"]

                # 提取策略说明
                strategy_summary = result.get("strategy_summary", "")
                strategy_detail = result.get("strategy_detail", "")

                # 如果没有返回结构化数据，尝试从text字段获取
                if not strategy_detail:
                    strategy_detail = result.get("text", "策略生成中...")

                if not strategy_summary and strategy_detail:
                    # 从详细说明中提取前2句作为摘要
                    sentences = strategy_detail.split('。')
                    strategy_summary = '。'.join(sentences[:2]) + '。' if len(sentences) >= 2 else strategy_detail[:100]

                # 构建前端显示文本
                display_text = f"✓ 策略生成完成\n\n{strategy_summary}\n\n{strategy_detail}"

                yield {
                    "type": "node_complete",
                    "node": "strategy_generation",
                    "data": {
                        "strategy_explanation": strategy_detail,  # 兼容旧字段
                        "strategy_summary": strategy_summary,  # 新增：简短摘要
                        "strategy_detail": strategy_detail,  # 新增：详细说明
                        "display_text": display_text  # 新增：前端显示文本
                    }
                }
                return

    except Exception as e:
        logger.error(f"Error in strategy_generation_node_stream: {e}")
        yield {
            "type": "node_complete",
            "node": "strategy_generation",
            "data": {
                "strategy_explanation": "策略生成失败，请稍后重试。",
                "error": str(e)
            }
        }


# =====================================================
# Node G: final_analysis (streaming version)
# =====================================================
async def final_analysis_node_stream(state: AgentState) -> AsyncIterator[dict[str, Any]]:
    """
    Node G: 结果输出 (流式版本)

    将预测数据转化为自然语言的分析报告，并流式返回。
    """
    logger.info("Executing final_analysis_node_stream")

    yield {"type": "node_start", "node": "final_analysis", "title": "结果输出"}

    prediction_result = state.get("prediction_result", {})
    strategy_explanation = state.get("strategy_explanation", "")

    prompt = f"""你是一个数据分析专家。根据圈人策略和预测结果，生成一份完整的分析报告。

策略说明：
{strategy_explanation}

预测结果：
{json.dumps(prediction_result, ensure_ascii=False, indent=2)}

请生成一份专业的分析报告，先分析推理，然后返回JSON格式：

{{
  "reasoning": "分析推理过程...",
  "executive_summary": "用2-3句话总结核心结果，例如：'本次圈选共锁定28位高价值客户，预估转化率8.5%，预期收入33.6万元，ROI达5倍。建议立即执行营销活动。'",
  "full_report": "完整的markdown格式分析报告（400-600字），包含：\n1. 圈选结果概览（人群规模、会员分布）\n2. 核心指标预测（转化率、预估收入、ROI）\n3. Top用户预览（列出前3-5个高价值用户）\n4. 执行建议（基于数据给出的建议）"
}}

要求：
1. executive_summary要突出核心数据和建议
2. full_report要专业、清晰，使用markdown格式
"""

    try:
        async for event in stream_llm_with_reasoning(prompt, max_tokens=800):
            if event["type"] == "reasoning":
                yield {
                    "type": "reasoning",
                    "node": "final_analysis",
                    "data": event["data"]
                }

            elif event["type"] == "result":
                result = event["data"]

                # 提取报告内容
                executive_summary = result.get("executive_summary", "")
                full_report = result.get("full_report", "")

                # 如果没有返回结构化数据，尝试从text字段获取
                if not full_report:
                    full_report = result.get("text", "")

                # 如果没有摘要，从完整报告中提取
                if not executive_summary and full_report:
                    sentences = full_report.split('。')
                    executive_summary = '。'.join(sentences[:3]) + '。' if len(sentences) >= 3 else full_report[:150]

                # 如果仍然没有报告内容，生成fallback
                if not full_report:
                    audience_size = prediction_result.get("audience_size", 0)
                    conversion_rate = prediction_result.get("conversion_rate", 0)
                    estimated_revenue = prediction_result.get("estimated_revenue", 0)
                    roi = prediction_result.get("roi", 0)

                    full_report = f"""# 圈人分析报告

## 圈选结果概览
- **圈选人数**: {audience_size}人
- **预估转化率**: {conversion_rate:.2%}
- **预估收入**: ¥{estimated_revenue:,.0f}
- **投资回报率(ROI)**: {roi:.2f}倍

## 执行建议
基于以上数据，建议立即执行营销活动。
"""
                    executive_summary = f"本次圈选共锁定{audience_size}位客户，预估转化率{conversion_rate:.2%}，预期收入¥{estimated_revenue:,.0f}，ROI达{roi:.2f}倍。"

                # 构建前端显示文本
                display_text = f"✓ 分析完成\n\n{executive_summary}\n\n{full_report}"

                yield {
                    "type": "node_complete",
                    "node": "final_analysis",
                    "data": {
                        "final_response": full_report,  # 兼容旧字段
                        "executive_summary": executive_summary,  # 新增：执行摘要
                        "full_report": full_report,  # 新增：完整报告
                        "display_text": display_text  # 新增：前端显示文本
                    }
                }
                return

    except Exception as e:
        logger.error(f"Error in final_analysis_node_stream: {e}")
        # Generate fallback report
        audience_size = prediction_result.get("audience_size", 0)
        conversion_rate = prediction_result.get("conversion_rate", 0)
        estimated_revenue = prediction_result.get("estimated_revenue", 0)
        roi = prediction_result.get("roi", 0)

        fallback_report = f"""# 圈人分析报告

## 圈选结果概览
- **圈选人数**: {audience_size}人
- **预估转化率**: {conversion_rate:.2%}
- **预估收入**: ¥{estimated_revenue:,.0f}
- **投资回报率(ROI)**: {roi:.2f}倍

## 执行建议
基于以上数据，建议立即执行营销活动。
"""

        yield {
            "type": "node_complete",
            "node": "final_analysis",
            "data": {
                "final_response": fallback_report,
                "error": str(e)
            }
        }
