"""LangGraph nodes for the marketing agent - Refactored for multi-turn dialogue."""
import logging
import json
import re
from typing import Any

from app.agent.state import AgentState, UserIntent, MatchedFeature, PredictionResult
from app.models.llm import get_llm_manager
from app.models.segmentation import SegmentationProposal, TargetTrait, FeatureRule
from app.data.feature_metadata import FEATURE_METADATA, search_features_by_keywords
from app.data.mock_users import MOCK_USERS_WITH_FEATURES
from langgraph.types import Send, interrupt

logger = logging.getLogger(__name__)


# =====================================================
# Node A: intent_recognition (意图识别)
# =====================================================
async def intent_recognition_node(state: AgentState) -> dict[str, Any]:
    """
    Node A: 意图识别

    分析用户输入，识别业务目标、目标人群和约束条件。
    判断意图是否明确，如果不明确则标记为 "ambiguous"。
    支持多轮对话，会考虑对话历史。
    """
    logger.info("Executing intent_recognition_node")

    user_input = state.get("user_input", "")
    messages = state.get("messages", [])
    conversation_context = state.get("conversation_context", "")
    previous_intent = state.get("previous_intent")  # 🔥 获取上一轮的结构化意图

    llm = get_llm_manager()

    # 🔥 构建提示词 - 如果有上一轮意图，使用它作为基线
    context_section = ""
    if previous_intent:
        # 有对话历史 - 多轮对话模式，使用上一轮意图作为基线
        logger.info(f"Multi-turn mode: Using previous intent as baseline")
        logger.info(f"Previous intent: {previous_intent}")

        # 将上一轮意图转换为JSON字符串，作为融合的基线
        previous_intent_json = json.dumps(previous_intent, ensure_ascii=False, indent=2)

        context_section = f"""
{conversation_context}

**多轮对话模式 - 重要**：
这是一个多轮对话。上一轮我们已经识别出的意图是：

```json
{previous_intent_json}
```

现在用户提供了新的输入："{user_input}"

**你的任务**：
1. **以上一轮意图为基线**：如果新输入没有提到某个字段（如business_goal、kpi），保留上一轮的值
2. **累积约束条件**：将新的约束条件追加到constraints列表中（除非用户明确说"去掉"某条件）
3. **更新提到的字段**：如果新输入提到了某个维度（如消费偏好、性别），更新target_audience中的对应字段
4. **覆盖冲突信息**：如果新输入与历史冲突（如之前说"VIP"，现在说"VVIP"），以新输入为准

**关键**：不要从头构建意图！从上面的previous_intent开始，根据新输入进行增量更新。

"""
    else:
        # 首次对话
        context_section = f"""
用户输入：{user_input}

"""

    prompt = f"""{context_section}你是一个营销专家，负责分析用户的圈人需求。

{"**重要提醒**：这是多轮对话，你必须在上一轮意图的基础上进行增量更新，而不是从零开始。" if previous_intent else ""}

请分析{"用户的新输入，并更新意图" if previous_intent else "用户的意图"}，并返回JSON格式的结果，包含以下字段：

- business_goal: 业务目标（如 "提升转化率", "扩大客户群", "促进复购"等）{"- 如果新输入未提及，保留上一轮的值" if previous_intent else ""}
- target_audience: 目标人群描述（包含会员等级、年龄、性别、消费力等维度）{"- 只更新新输入提到的字段，其他字段保留上一轮的值" if previous_intent else ""}
- constraints: **所有的**约束条件列表（如 "排除近期已购买用户", "只要女性客户"等）{"- 在上一轮的基础上追加新约束" if previous_intent else ""}
- kpi: 核心KPI（conversion_rate/revenue/visit_rate/engagement）{"- 如果新输入未提及，保留上一轮的值" if previous_intent else ""}
- size_preference: 人群规模偏好 {{"min": 最小人数, "max": 最大人数}}{"- 如果新输入未提及，保留上一轮的值" if previous_intent else ""}
- is_clear: 意图是否明确（true/false）。如果用户描述模糊、缺少关键信息，则为false
- summary: 用1-2句话总结你对用户**完整需求**的理解（融合所有历史信息后的理解）

{"**再次强调**：你必须以上面提供的previous_intent为起点，根据新输入进行增量修改。不要丢失任何历史信息！" if previous_intent else ""}

只返回JSON，不要其他内容。

示例：
{{
  "business_goal": "提升春季新品转化率",
  "target_audience": {{
    "tier": ["VVIP"],
    "age_group": "25-44",
    "gender": "female",
    "has_recent_purchase": false
  }},
  "constraints": ["排除近7天已购买用户", "只要女性客户", "只要VVIP等级"],
  "kpi": "conversion_rate",
  "size_preference": {{"min": 100, "max": 500}},
  "is_clear": true,
  "summary": "您希望针对春季新品手袋上市，圈选25-44岁的女性VVIP客户（排除近期已购买用户），以提升产品转化率。"
}}
"""

    try:
        # 🔥 打印完整的提示词
        logger.info("=" * 80)
        logger.info("🤖 LLM CALL - Intent Recognition Node")
        logger.info("=" * 80)
        logger.info(f"Multi-turn mode: {previous_intent is not None}")
        if previous_intent:
            logger.info(f"Previous intent: {json.dumps(previous_intent, ensure_ascii=False, indent=2)}")
        logger.info("-" * 80)
        logger.info("📝 PROMPT TO LLM:")
        logger.info(prompt)
        logger.info("-" * 80)

        # 直接调用LLM底层方法（不使用旧的 analyze_intent）
        logger.info(f"Calling LLM for intent recognition (multi-turn: {previous_intent is not None})")
        response_text = await llm.model.call(prompt)

        # 🔥 打印LLM的完整响应
        logger.info("-" * 80)
        logger.info("📥 LLM RESPONSE:")
        logger.info(response_text)
        logger.info("=" * 80)

        logger.info(f"Intent recognition raw response: {response_text[:200]}...")

        # 尝试解析JSON
        try:
            response = json.loads(response_text)
        except json.JSONDecodeError:
            # 如果无法解析JSON，尝试提取JSON部分
            logger.warning("Failed to parse as JSON, trying to extract JSON block")
            # 尝试提取 {...} 部分
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                response = json.loads(json_match.group())
            else:
                raise ValueError("Cannot extract JSON from response")

        logger.info(f"Intent recognition parsed: {response}")

        # 🔥 如果是多轮对话，记录融合情况
        if previous_intent:
            logger.info("=" * 50)
            logger.info("Multi-turn Intent Merge Report:")
            logger.info(f"  Previous business_goal: {previous_intent.get('business_goal', 'N/A')}")
            logger.info(f"  New business_goal: {response.get('business_goal', 'N/A')}")
            logger.info(f"  Previous constraints: {previous_intent.get('constraints', [])}")
            logger.info(f"  New constraints: {response.get('constraints', [])}")
            logger.info(f"  Previous kpi: {previous_intent.get('kpi', 'N/A')}")
            logger.info(f"  New kpi: {response.get('kpi', 'N/A')}")
            logger.info("=" * 50)

        # 解析结果
        is_clear = response.get("is_clear", True)  # 默认为True，只有明确标记false才认为不清楚

        # 构建 UserIntent
        user_intent: UserIntent = {
            "business_goal": response.get("business_goal", ""),
            "target_audience": response.get("target_audience", {}),
            "constraints": response.get("constraints", []),
            "kpi": response.get("kpi", "conversion_rate"),
            "size_preference": response.get("size_preference", {"min": 50, "max": 500}),
        }

        # 提取自然语言摘要
        summary = response.get("summary", "")
        if not summary:
            # 如果LLM没有返回summary，生成一个简单的
            goal = user_intent.get("business_goal", "营销活动")
            summary = f"理解您的需求：{goal}"

        logger.info(f"Intent summary: {summary}")

        return {
            "user_intent": user_intent,
            "intent_status": "clear" if is_clear else "ambiguous",
            "intent_summary": summary,  # 新增：自然语言摘要
        }

    except Exception as e:
        logger.error(f"Error in intent_recognition: {e}")
        # 默认返回不明确状态
        return {
            "user_intent": {
                "business_goal": "",
                "target_audience": {},
                "constraints": [],
                "kpi": "conversion_rate",
                "size_preference": {"min": 50, "max": 500},
            },
            "intent_status": "ambiguous",
        }


# =====================================================
# Node B: ask_clarification (澄清/反问)
# =====================================================
async def ask_clarification_node(state: AgentState) -> dict[str, Any]:
    """
    Node B: 澄清/反问

    当意图不明时，生成自然语言引导用户继续补充信息。
    """
    logger.info("Executing ask_clarification_node")

    user_input = state.get("user_input", "")
    user_intent = state.get("user_intent", {})

    llm = get_llm_manager()

    # 构建提示词
    prompt = f"""你是一个营销专家助手。用户的描述不够清晰，你需要引导用户补充更多信息。

用户输入：{user_input}
当前识别的意图：{json.dumps(user_intent, ensure_ascii=False)}

请生成一个自然语言的反问，引导用户补充以下信息：
1. 业务目标是什么？（如提升转化、增加营收、促进到店等）
2. 想圈选哪类人群？（会员等级、年龄段、消费力等）
3. 有什么约束条件？（人群规模、预算、排除条件等）

返回一段自然、友好的引导语，不要生成JSON。

示例：
"我理解您想进行人群圈选。为了更精准地帮您，能否告诉我：您的核心目标是什么？比如是提升转化率、增加营收，还是促进到店？另外，您希望圈选哪类客户？比如VIP客户、年轻客户、高消费客户等？"
"""

    try:
        # 🔥 打印完整的提示词
        logger.info("=" * 80)
        logger.info("🤖 LLM CALL - Ask Clarification Node")
        logger.info("=" * 80)
        logger.info("-" * 80)
        logger.info("📝 PROMPT TO LLM:")
        logger.info(prompt)
        logger.info("-" * 80)

        # 直接调用LLM
        response = await llm.model.call(prompt)
        clarification = response.strip()

        # 🔥 打印LLM的完整响应
        logger.info("-" * 80)
        logger.info("📥 LLM RESPONSE:")
        logger.info(response)
        logger.info("=" * 80)

        logger.info(f"Clarification question: {clarification}")

        return {
            "clarification_question": clarification,
            "final_response": clarification,  # 直接返回给用户
        }

    except Exception as e:
        logger.error(f"Error in ask_clarification: {e}")
        return {
            "clarification_question": "请问您想圈选什么样的人群？能否提供更多细节？",
            "final_response": "请问您想圈选什么样的人群？能否提供更多细节？",
        }


# =====================================================
# Node C: feature_matching (特征匹配)
# =====================================================
async def feature_matching_node(state: AgentState) -> dict[str, Any]:
    """
    Node C: 特征匹配

    将用户意图映射到具体的数据库特征字段。
    """
    logger.info("Executing feature_matching_node")

    user_intent = state.get("user_intent", {})

    llm = get_llm_manager()

    # 准备特征元数据摘要
    feature_summary = {}
    for name, meta in FEATURE_METADATA.items():
        feature_summary[name] = {
            "display_name": meta["display_name"],
            "type": meta["type"],
            "description": meta["description"],
            "examples": meta["examples"][:2],  # 只取前2个示例
        }

    # 构建提示词
    prompt = f"""你是一个数据分析专家。用户想进行人群圈选，你需要将用户意图映射到具体的数据库特征字段。

用户意图：
{json.dumps(user_intent, ensure_ascii=False, indent=2)}

可用的特征字段：
{json.dumps(feature_summary, ensure_ascii=False, indent=2)}

请分析用户意图，匹配合适的特征字段，返回JSON格式：
{{
  "matched_features": [
    {{
      "feature_name": "特征名称",
      "operator": "操作符（>、>=、<、<=、==、in、between）",
      "value": "特征值",
      "description": "自然语言描述"
    }}
  ],
  "is_success": true/false,  # 是否成功匹配
  "reason": "如果失败，说明原因"
}}

注意：
1. 如果用户意图中的某些条件无法用现有特征表达，设置 is_success=false
2. 尽量匹配多个特征，组合使用以满足用户需求
3. 对于年龄、会员等级等分类特征，使用 "in" 操作符
4. 对于消费额、次数等数值特征，使用 >、>=、< 等操作符

只返回JSON，不要其他内容。
"""

    try:
        # 🔥 打印完整的提示词
        logger.info("=" * 80)
        logger.info("🤖 LLM CALL - Feature Matching Node")
        logger.info("=" * 80)
        logger.info("-" * 80)
        logger.info("📝 PROMPT TO LLM:")
        logger.info(prompt)
        logger.info("-" * 80)

        # 直接调用LLM进行特征匹配
        response_text = await llm.model.call(prompt)

        # 🔥 打印LLM的完整响应
        logger.info("-" * 80)
        logger.info("📥 LLM RESPONSE:")
        logger.info(response_text)
        logger.info("=" * 80)

        logger.info(f"Feature matching raw response: {response_text[:200]}...")

        # 解析JSON
        try:
            response = json.loads(response_text)
        except json.JSONDecodeError:
            # 尝试提取JSON部分
            logger.warning("Failed to parse as JSON, trying to extract JSON block")
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                response = json.loads(json_match.group())
            else:
                raise ValueError("Cannot extract JSON from response")

        logger.info(f"Feature matching result: {response}")

        is_success = response.get("is_success", True)  # 默认成功
        matched_features_raw = response.get("matched_features", [])

        # 转换为 MatchedFeature 类型
        matched_features: list[MatchedFeature] = []
        for feat in matched_features_raw:
            # 获取特征元数据
            meta = FEATURE_METADATA.get(feat.get("feature_name"))
            if meta:
                matched_features.append({
                    "feature_name": feat.get("feature_name", ""),
                    "feature_type": meta["type"],
                    "operator": feat.get("operator", "=="),
                    "value": feat.get("value"),
                    "description": feat.get("description", ""),
                })

        # 生成自然语言摘要
        if matched_features:
            feature_list = "\n".join([f"• {f['description']}" for f in matched_features[:5]])
            summary = f"已为您匹配{len(matched_features)}个关键特征：\n{feature_list}"
        else:
            summary = "未能找到匹配的特征字段，建议调整需求描述。"

        return {
            "matched_features": matched_features,
            "match_status": "success" if is_success else "needs_refinement",
            "feature_summary": summary,  # 新增：自然语言摘要
        }

    except Exception as e:
        logger.error(f"Error in feature_matching: {e}")
        return {
            "matched_features": [],
            "match_status": "needs_refinement",
        }


# =====================================================
# Node D: request_modification (请求修正)
# =====================================================
async def request_modification_node(state: AgentState) -> dict[str, Any]:
    """
    Node D: 请求修正

    当无法找到匹配特征或意图不可执行时，告知用户原因并引导修改。
    """
    logger.info("Executing request_modification_node")

    user_intent = state.get("user_intent", {})
    matched_features = state.get("matched_features", [])

    llm = get_llm_manager()

    # 构建提示词
    prompt = f"""你是一个营销专家助手。用户的圈人需求无法用现有的数据特征满足，你需要告知原因并引导修改。

用户意图：
{json.dumps(user_intent, ensure_ascii=False, indent=2)}

已匹配的特征：
{json.dumps(matched_features, ensure_ascii=False, indent=2)}

请生成一段自然、友好的引导语，说明：
1. 哪些需求无法满足，为什么
2. 建议用户如何调整需求（简化条件、换个角度描述等）

返回纯文本，不要JSON格式。

示例：
"抱歉，根据您的描述，我们暂时无法匹配到合适的数据特征。建议您：1) 简化一些条件，比如先不限制地域；2) 或者换个角度，比如关注用户的消费行为而不是兴趣标签。您可以重新描述一下需求吗？"
"""

    try:
        # 🔥 打印完整的提示词
        logger.info("=" * 80)
        logger.info("🤖 LLM CALL - Request Modification Node")
        logger.info("=" * 80)
        logger.info("-" * 80)
        logger.info("📝 PROMPT TO LLM:")
        logger.info(prompt)
        logger.info("-" * 80)

        # 直接调用LLM生成修正建议
        response = await llm.model.call(prompt)
        modification_request = response.strip()

        # 🔥 打印LLM的完整响应
        logger.info("-" * 80)
        logger.info("📥 LLM RESPONSE:")
        logger.info(response)
        logger.info("=" * 80)

        logger.info(f"Modification request: {modification_request}")

        return {
            "modification_request": modification_request,
            "final_response": modification_request,  # 直接返回给用户
        }

    except Exception as e:
        logger.error(f"Error in request_modification: {e}")
        return {
            "modification_request": "抱歉，无法满足您的需求。请重新描述或简化条件。",
            "final_response": "抱歉，无法满足您的需求。请重新描述或简化条件。",
        }


# =====================================================
# Node E: strategy_generation (策略生成)
# =====================================================
async def strategy_generation_node(state: AgentState) -> dict[str, Any]:
    """
    Node E: 策略生成

    用自然语言解释如何组合这些特征来满足圈人意图。
    """
    logger.info("Executing strategy_generation_node")

    user_intent = state.get("user_intent", {})
    matched_features = state.get("matched_features", [])

    llm = get_llm_manager()

    # 构建提示词
    prompt = f"""你是一个营销策略专家。用户想进行人群圈选，你已经匹配好了特征，现在需要生成策略解释。

用户意图：
{json.dumps(user_intent, ensure_ascii=False, indent=2)}

匹配的特征：
{json.dumps(matched_features, ensure_ascii=False, indent=2)}

请用自然语言解释：
1. 我们将如何组合这些特征来圈选人群
2. 这个策略为什么能满足用户的业务目标
3. 预期能达到什么效果

返回一段专业、清晰的策略说明（200-300字），不要JSON格式。

示例：
"根据您的需求，我们将采用以下圈选策略：

**目标人群定位**：锁定VVIP和VIP客户，年龄在25-44岁之间，近12个月消费额超过10万元。

**行为筛选**：优先选择近30天浏览手袋品类超过10次、且有加购未下单记录的高意向用户。

**排除条件**：排除近7天已购买用户，避免营销疲劳。

**预期效果**：这一策略能够精准触达高价值、高意向的潜在客户，预计转化率可提升30-50%，同时避免对已转化用户的重复打扰。"
"""

    try:
        # 🔥 打印完整的提示词
        logger.info("=" * 80)
        logger.info("🤖 LLM CALL - Strategy Generation Node")
        logger.info("=" * 80)
        logger.info("-" * 80)
        logger.info("📝 PROMPT TO LLM:")
        logger.info(prompt)
        logger.info("-" * 80)

        # 直接调用LLM生成策略解释
        response = await llm.model.call(prompt)
        strategy = response.strip()

        # 🔥 打印LLM的完整响应
        logger.info("-" * 80)
        logger.info("📥 LLM RESPONSE:")
        logger.info(response)
        logger.info("=" * 80)

        logger.info(f"Strategy explanation: {strategy[:100]}...")

        # 提取前200字作为摘要
        strategy_summary = strategy[:200] + "..." if len(strategy) > 200 else strategy

        return {
            "strategy_explanation": strategy,
            "strategy_summary": strategy_summary,  # 新增：策略摘要
        }

    except Exception as e:
        logger.error(f"Error in strategy_generation: {e}")
        return {
            "strategy_explanation": "策略生成失败，请稍后重试。",
        }


# =====================================================
# Node F: impact_prediction (效果预测/Tool调用)
# =====================================================
async def impact_prediction_node(state: AgentState) -> dict[str, Any]:
    """
    Node F: 效果预测/Tool调用

    调用工具节点进行数据查询、效果预测。
    目前使用mock数据模拟真实预测结果。
    """
    logger.info("Executing impact_prediction_node")

    matched_features = state.get("matched_features", [])
    user_intent = state.get("user_intent", {})

    # TODO: 这里应该调用真实的数据查询工具
    # 目前使用mock数据模拟

    # 简单模拟：根据匹配的特征筛选用户
    filtered_users = MOCK_USERS_WITH_FEATURES.copy()

    # 应用特征过滤（简化版）
    for feature in matched_features:
        name = feature["feature_name"]
        operator = feature["operator"]
        value = feature["value"]
        feature_type = feature.get("feature_type", "categorical")

        try:
            # 根据特征类型转换 value 的类型
            if feature_type == "numeric":
                # 数值类型 - 转换为数字
                if operator == "between":
                    # 特殊处理 between 操作符
                    if isinstance(value, str):
                        # 尝试解析 "30 and 90" 或 "30-90" 或 "30,90" 格式
                        import re
                        parts = re.split(r'\s+and\s+|\s*-\s*|\s*,\s*', value.strip())
                        if len(parts) == 2:
                            try:
                                min_val = float(parts[0]) if '.' in parts[0] else int(parts[0])
                                max_val = float(parts[1]) if '.' in parts[1] else int(parts[1])
                                value = [min_val, max_val]
                            except ValueError:
                                logger.warning(f"Cannot parse between value: {value}")
                                continue
                        else:
                            logger.warning(f"Invalid between value format: {value}")
                            continue
                    elif isinstance(value, (list, tuple)) and len(value) == 2:
                        min_val = float(value[0]) if isinstance(value[0], str) else value[0]
                        max_val = float(value[1]) if isinstance(value[1], str) else value[1]
                        value = [min_val, max_val]
                    else:
                        logger.warning(f"Invalid between value: {value}")
                        continue

                    # 执行 between 过滤
                    filtered_users = [u for u in filtered_users if value[0] <= u.get(name, 0) <= value[1]]
                else:
                    # 其他数值操作符
                    if isinstance(value, str):
                        value = float(value) if '.' in value else int(value)

                    # 数值比较
                    if operator == ">":
                        filtered_users = [u for u in filtered_users if u.get(name, 0) > value]
                    elif operator == ">=":
                        filtered_users = [u for u in filtered_users if u.get(name, 0) >= value]
                    elif operator == "<":
                        filtered_users = [u for u in filtered_users if u.get(name, 0) < value]
                    elif operator == "<=":
                        filtered_users = [u for u in filtered_users if u.get(name, 0) <= value]
                    elif operator == "==":
                        filtered_users = [u for u in filtered_users if u.get(name, 0) == value]

            elif feature_type == "categorical":
                # 分类类型
                if operator == "==":
                    filtered_users = [u for u in filtered_users if u.get(name) == value]
                elif operator == "in":
                    # 确保 value 是列表
                    if not isinstance(value, (list, tuple)):
                        value = [value]
                    filtered_users = [u for u in filtered_users if u.get(name) in value]

            elif feature_type == "boolean":
                # 布尔类型
                if isinstance(value, str):
                    value = value.lower() in ['true', '1', 'yes']
                filtered_users = [u for u in filtered_users if u.get(name) == value]

        except (ValueError, TypeError) as e:
            logger.warning(f"Error filtering feature {name} with value {value}: {e}")
            # 跳过这个特征，继续处理其他特征
            continue

    # 计算预测指标
    audience_size = len(filtered_users)

    # Mock预测数据
    if audience_size > 0:
        # 基于人群规模和质量估算转化率
        avg_loyalty = sum(u.get("brand_loyalty_score", 0) for u in filtered_users) / audience_size
        base_conversion_rate = 0.05  # 基础转化率5%
        conversion_rate = base_conversion_rate * (1 + avg_loyalty / 100)  # 根据忠诚度调整

        # 统计会员等级分布
        tier_distribution = {}
        for user in filtered_users:
            tier = user.get("tier", "Member")
            tier_distribution[tier] = tier_distribution.get(tier, 0) + 1

        # 估算收入
        from app.data.mock_users import TIER_AVG_ORDER_VALUE
        estimated_revenue = 0
        for tier, count in tier_distribution.items():
            avg_order = TIER_AVG_ORDER_VALUE.get(tier, 18000)
            estimated_revenue += count * conversion_rate * avg_order

        # 计算ROI（假设营销成本为收入的20%）
        roi = estimated_revenue / (estimated_revenue * 0.2) if estimated_revenue > 0 else 0

        # 人群质量分
        quality_score = avg_loyalty

        # Top用户（取前5个）
        sorted_users = sorted(filtered_users, key=lambda u: u.get("score", 0), reverse=True)
        top_users = [
            {
                "name": u.get("name"),
                "tier": u.get("tier"),
                "score": u.get("score"),
                "r12m_spending": u.get("r12m_spending"),
            }
            for u in sorted_users[:5]
        ]

    else:
        # 没有匹配用户
        conversion_rate = 0
        estimated_revenue = 0
        roi = 0
        quality_score = 0
        tier_distribution = {}
        top_users = []

    prediction_result: PredictionResult = {
        "audience_size": audience_size,
        "conversion_rate": conversion_rate,
        "estimated_revenue": estimated_revenue,
        "roi": roi,
        "quality_score": quality_score,
        "tier_distribution": tier_distribution,
        "top_users": top_users,
    }

    logger.info(f"Prediction result: {prediction_result}")

    return {
        "prediction_result": prediction_result,
    }


# =====================================================
# Node G: final_analysis (结果输出)
# =====================================================
async def final_analysis_node(state: AgentState) -> dict[str, Any]:
    """
    Node G: 结果输出

    将预测数据转化为自然语言的分析报告。
    同时输出结构化的圈人方案数据。
    """
    logger.info("Executing final_analysis_node")

    prediction_result = state.get("prediction_result", {})
    strategy_explanation = state.get("strategy_explanation", "")
    user_intent = state.get("user_intent", {})
    matched_features = state.get("matched_features", [])

    llm = get_llm_manager()

    # 构建提示词
    prompt = f"""你是一个数据分析专家。根据圈人策略和预测结果，生成一份完整的分析报告。

策略说明：
{strategy_explanation}

预测结果：
{json.dumps(prediction_result, ensure_ascii=False, indent=2)}

请生成一份专业的分析报告，包含：
1. **圈选结果概览**（人群规模、会员分布）
2. **核心指标预测**（转化率、预估收入、ROI）
3. **Top用户预览**（列出前3-5个高价值用户）
4. **执行建议**（基于数据给出的建议）

返回清晰、专业的markdown格式报告（400-600字）。
"""

    try:
        # 🔥 打印完整的提示词
        logger.info("=" * 80)
        logger.info("🤖 LLM CALL - Final Analysis Node")
        logger.info("=" * 80)
        logger.info("-" * 80)
        logger.info("📝 PROMPT TO LLM:")
        logger.info(prompt)
        logger.info("-" * 80)

        # 直接调用LLM生成分析报告
        response = await llm.model.call(prompt)
        report = response.strip()

        # 🔥 打印LLM的完整响应
        logger.info("-" * 80)
        logger.info("📥 LLM RESPONSE:")
        logger.info(response)
        logger.info("=" * 80)

        logger.info(f"Final analysis report generated")

        # 构建结构化的圈人方案
        logger.info("Building segmentation proposal...")
        segmentation_proposal = _build_segmentation_proposal(
            user_intent,
            matched_features,
            prediction_result
        )
        logger.info(f"Segmentation proposal built: {segmentation_proposal is not None}")

        return {
            "final_response": report,
            "segmentation_proposal": segmentation_proposal,  # 新增：结构化方案
        }

    except Exception as e:
        logger.error(f"Error in final_analysis: {e}")
        # 生成简单的后备报告
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

        # 构建结构化的圈人方案（即使出错也要返回）
        try:
            segmentation_proposal = _build_segmentation_proposal(
                user_intent,
                matched_features,
                prediction_result
            )
        except Exception as e2:
            logger.error(f"Error building segmentation proposal: {e2}")
            segmentation_proposal = None

        return {
            "final_response": fallback_report,
            "segmentation_proposal": segmentation_proposal,
        }


def _build_segmentation_proposal(
    user_intent: dict[str, Any],
    matched_features: list[dict[str, Any]],
    prediction_result: dict[str, Any]
) -> dict[str, Any]:
    """
    构建结构化的圈人方案数据
    """
    # 提取营销目标
    business_goal = user_intent.get("business_goal", "未指定营销目标")

    # 提取约束条件
    constraints = user_intent.get("constraints", [])

    # 提取KPI
    kpi = user_intent.get("kpi", "conversion_rate")

    # 提取目标人群
    target_audience = user_intent.get("target_audience", {})

    # 将匹配的特征转换为 TargetTrait 结构
    trait_dict: dict[str, list[dict]] = {}
    for feature in matched_features:
        feature_name = feature.get("feature_name", "")
        feature_type = feature.get("feature_type", "categorical")
        operator = feature.get("operator", "=")
        value = feature.get("value", "")
        description = feature.get("description", "")

        # 确定特征分类
        category = _categorize_feature(feature_name, feature_type)

        if category not in trait_dict:
            trait_dict[category] = []

        trait_dict[category].append({
            "key": feature_name,
            "operator": operator,
            "value": value,
            "description": description
        })

    # 构建 target_traits
    target_traits = [
        {
            "category": category,
            "rules": rules
        }
        for category, rules in trait_dict.items()
    ]

    # 构建完整的方案
    proposal = {
        "marketing_goal": business_goal,
        "constraints": constraints,
        "target_traits": target_traits,
        "kpi": kpi,
        "target_audience": target_audience
    }

    return proposal


def _categorize_feature(feature_name: str, feature_type: str) -> str:
    """
    根据特征名称和类型，确定特征分类
    """
    # 消费相关
    if any(keyword in feature_name.lower() for keyword in ["amount", "value", "price", "消费", "金额"]):
        return "消费门槛"

    # 品类相关
    if any(keyword in feature_name.lower() for keyword in ["category", "品类", "类别", "product"]):
        return "品类兴趣"

    # 行为相关
    if any(keyword in feature_name.lower() for keyword in ["frequency", "visit", "购买", "访问", "次数"]):
        return "行为习惯"

    # 时间相关
    if any(keyword in feature_name.lower() for keyword in ["recency", "最近", "last", "时间"]):
        return "活跃度"

    # 会员等级
    if any(keyword in feature_name.lower() for keyword in ["tier", "level", "等级", "vip"]):
        return "会员等级"

    # 默认分类
    return "其他条件"


# =====================================================
# 节点注册表
# =====================================================
AGENT_NODES = {
    "intent_recognition": intent_recognition_node,
    "ask_clarification": ask_clarification_node,
    "feature_matching": feature_matching_node,
    "request_modification": request_modification_node,
    "strategy_generation": strategy_generation_node,
    "impact_prediction": impact_prediction_node,
    "final_analysis": final_analysis_node,
}
