"""FastAPI routes for the marketing agent API."""
import json
import logging
import uuid
from typing import AsyncIterator
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse

from app.api.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    UserListResponse,
    PredictionRequest,
    PredictionMetrics,
    User,
    ThinkingStep,
    SessionResponse,
    CampaignApplicationRequest,
    CampaignApplicationResponse,
    # New V2 schemas
    AnalysisResponseV2,
    MatchedFeature as MatchedFeatureSchema,
    UserIntent as UserIntentSchema,
    PredictionResult as PredictionResultSchema,
    TopUser as TopUserSchema,
)
from app.agent.graph import get_agent_graph
from app.data.selectors import AudienceSelector
from app.data.mock_users import MOCK_USERS, AVG_ORDER_VALUE
from app.utils.metrics import get_calculator
from app.core.session import (
    get_session_manager,
    ConversationTurn,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["analysis"])

# Store recent analysis for quick access
_last_analysis_result = None


@router.post("/analysis", response_model=AnalysisResponse)
async def analyze_marketing_goal(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
) -> AnalysisResponse:
    """
    Analyze marketing goal and return segmented audience with metrics.

    This endpoint processes the user's marketing prompt through the LangGraph agent,
    which performs multi-step reasoning to:
    1. Parse intent and extract KPIs (with multi-turn context awareness)
    2. Extract multi-dimensional features
    3. Select high-potential audience
    4. Predict campaign performance
    5. Generate strategic recommendations

    Supports multi-turn conversations:
    - If session_id is provided, retrieves conversation history
    - Determines if input is a modification or new request
    - Adjusts analysis based on previous context

    Args:
        request: AnalysisRequest containing the marketing goal prompt and optional session_id
        background_tasks: FastAPI background tasks

    Returns:
        AnalysisResponse with session_id, selected audience, metrics, and thinking steps
    """
    logger.info(f"Received analysis request: {request.prompt}")

    if not request.prompt or not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    try:
        # Get or create session
        session_manager = get_session_manager()
        session = session_manager.get_or_create_session(request.session_id)

        logger.info(f"Using session: {session.session_id}")

        # Build context for multi-turn conversation
        memory_manager = session_manager.memory_manager
        llm_context = memory_manager.build_context_for_llm(session, request.prompt)

        # Check if this is a modification
        is_modification = memory_manager.should_modify_intent(session, request.prompt)

        # Prepare agent state with context
        initial_state = {
            "user_input": request.prompt,
            "thinking_steps": [],
            "conversation_context": llm_context,
            "is_modification": is_modification,
            "previous_intent": session.current_context.get("latest_intent") if session.turns else None
        }

        # Run the agent graph
        graph = get_agent_graph()
        final_state = await graph.ainvoke(initial_state)

        # Extract results
        audience_list = final_state.get("audience", [])
        metrics_data = final_state.get("metrics", {})
        response_text = final_state.get("final_response", "")
        thinking_steps_raw = final_state.get("thinking_steps", [])
        intent = final_state.get("intent", {})

        # Convert to response models
        audience = [
            User(
                id=u["id"],
                name=u["name"],
                tier=u["tier"],
                score=u["score"],
                recentStore=u["recentStore"],
                lastVisit=u["lastVisit"],
                reason=u["reason"],
                matchScore=u.get("matchScore")
            )
            for u in audience_list
        ]

        metrics = PredictionMetrics(
            audienceSize=metrics_data.get("audience_size", 0),
            conversionRate=metrics_data.get("conversion_rate", 0),
            estimatedRevenue=metrics_data.get("estimated_revenue", 0),
            roi=metrics_data.get("roi", 0),
            reachRate=metrics_data.get("reach_rate", 0),
            qualityScore=metrics_data.get("quality_score", 0)
        )

        thinking_steps = [
            ThinkingStep(
                id=step["id"],
                title=step["title"],
                description=step["description"],
                status=step["status"]
            )
            for step in thinking_steps_raw
        ]

        # Save turn to session
        turn = ConversationTurn(
            user_input=request.prompt,
            intent=intent,
            audience=audience_list,
            metrics=metrics_data,
            response=response_text
        )
        session.add_turn(turn)

        response = AnalysisResponse(
            session_id=session.session_id,
            audience=audience,
            metrics=metrics,
            response=response_text,
            thinkingSteps=thinking_steps,
            timestamp=datetime.now()
        )

        # Cache the result (keep for backward compatibility)
        global _last_analysis_result
        _last_analysis_result = response

        logger.info(
            f"Analysis completed for session {session.session_id}. "
            f"Selected {len(audience)} users. Turn {len(session.turns)}."
        )
        return response

    except Exception as e:
        logger.error(f"Error during analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/analysis/stream")
async def analyze_marketing_goal_stream(
    prompt: str,
    session_id: str = None
):
    """
    Analyze marketing goal with Server-Sent Events (SSE) streaming.

    Streams thinking steps in real-time as the agent processes the request,
    then sends the final analysis result.

    Supports multi-turn conversations via session_id parameter.

    Args:
        prompt: Marketing goal prompt as query parameter
        session_id: Optional session ID for multi-turn conversation

    Returns:
        StreamingResponse with SSE events
    """
    logger.info(f"Received streaming analysis request: {prompt}")

    async def event_generator() -> AsyncIterator[str]:
        """Generate SSE events for thinking steps and final result."""
        import asyncio
        import sys

        try:
            # Get or create session
            session_manager = get_session_manager()
            session = session_manager.get_or_create_session(session_id)

            logger.info(f"Streaming for session: {session.session_id}")

            # Build context for multi-turn conversation
            memory_manager = session_manager.memory_manager
            llm_context = memory_manager.build_context_for_llm(session, prompt)

            # Check if this is a modification
            is_modification = memory_manager.should_modify_intent(session, prompt)

            # Prepare agent state with context
            initial_state = {
                "user_input": prompt,
                "thinking_steps": [],
                "conversation_context": llm_context,
                "is_modification": is_modification,
                "previous_intent": session.current_context.get("latest_intent") if session.turns else None
            }

            # Run the agent graph with real-time streaming
            graph = get_agent_graph()
            final_state = None

            # Send initial "active" status for all 5 steps immediately
            # This gives users instant feedback
            initial_steps = [
                {"stepId": "1", "title": "业务意图与约束解析", "description": "正在分析营销目标和核心KPI...", "status": "active"},
                {"stepId": "2", "title": "多维特征扫描", "description": "正在提取人群的消费力、兴趣、活跃度等特征...", "status": "pending"},
                {"stepId": "3", "title": "人群策略组合计算", "description": "正在圈选高潜力目标人群...", "status": "pending"},
                {"stepId": "4", "title": "效果预测与优化", "description": "正在预测营销活动的核心业绩指标...", "status": "pending"},
                {"stepId": "5", "title": "策略总结与建议", "description": "正在生成营销策略总结...", "status": "pending"},
            ]

            # Send all steps immediately
            for step in initial_steps:
                yield f"event: thinking_step\n"
                yield f"data: {json.dumps(step, ensure_ascii=False)}\n\n"
                # 发送填充数据确保立即发送
                yield ": ping\n\n"
                sys.stdout.flush()
                await asyncio.sleep(0)

            logger.info("Sent initial thinking steps framework to frontend")

            # Use astream() to get real-time node outputs
            async for output in graph.astream(initial_state):
                # Output format: {node_name: node_output_state}
                for node_name, node_output in output.items():
                    logger.info(f"Node '{node_name}' completed, streaming updated thinking step")

                    # 🔥 调试：打印 node_output 的键
                    logger.info(f"Node '{node_name}' output keys: {list(node_output.keys())}")

                    # 发送节点完成的自然语言摘要（新增）
                    summary_text = None
                    if node_name == "intent_recognition" and "intent_summary" in node_output:
                        summary_text = f"✓ 意图识别完成\n\n{node_output['intent_summary']}"
                        logger.info(f"Found intent_summary: {node_output['intent_summary'][:50]}...")
                    elif node_name == "feature_matching" and "feature_summary" in node_output:
                        summary_text = f"✓ 特征匹配完成\n\n{node_output['feature_summary']}"
                        logger.info(f"Found feature_summary: {node_output['feature_summary'][:50]}...")
                    elif node_name == "strategy_generation" and "strategy_summary" in node_output:
                        summary_text = f"✓ 策略生成完成\n\n{node_output['strategy_summary']}"
                        logger.info(f"Found strategy_summary: {node_output['strategy_summary'][:50]}...")

                    # 如果有自然语言摘要，发送给前端
                    if summary_text:
                        summary_event = {
                            "node": node_name,
                            "summary": summary_text
                        }
                        yield f"event: node_summary\n"
                        yield f"data: {json.dumps(summary_event, ensure_ascii=False)}\n\n"
                        # 🔥 发送 SSE 注释行强制刷新（关键！）
                        yield f": heartbeat\n\n"
                        sys.stdout.flush()
                        await asyncio.sleep(0)
                        logger.info(f"Sent node summary for {node_name}")

                    # 🔥 新增：即使没有 summary，也要发送节点完成事件（关键！）
                    # 这确保每个节点完成后前端都能立即收到通知
                    node_complete_event = {
                        "node": node_name,
                        "status": "completed",
                        "timestamp": datetime.now().isoformat()
                    }
                    yield f"event: node_complete\n"
                    yield f"data: {json.dumps(node_complete_event, ensure_ascii=False)}\n\n"

                    # 🔥 发送 SSE 注释行强制刷新 HTTP chunk（最关键！）
                    # 发送足够大的填充数据（~1KB）来触发 HTTP chunk 发送
                    padding = ": " + (" " * 1000) + "\n\n"
                    yield padding
                    sys.stdout.flush()
                    await asyncio.sleep(0)

                    logger.info(f"[REALTIME] Sent node_complete event for {node_name}")

                    # Get thinking steps from current node output
                    thinking_steps = node_output.get("thinking_steps", [])

                    # Find and stream the latest thinking step(s) added by this node
                    if thinking_steps:
                        # Typically the last step is the one just added by this node
                        latest_step = thinking_steps[-1]
                        # Update the step status to "completed" with real description
                        step_event = {
                            "stepId": latest_step["id"],
                            "title": latest_step["title"],
                            "description": latest_step["description"],
                            "status": "completed"  # Mark as completed
                        }
                        yield f"event: thinking_step_update\n"  # Different event type for update
                        yield f"data: {json.dumps(step_event, ensure_ascii=False)}\n\n"
                        yield ": ping\n\n"
                        sys.stdout.flush()
                        await asyncio.sleep(0)

                    # Save the latest state
                    final_state = node_output

            # Extract results from final state
            if not final_state:
                raise ValueError("Graph execution completed but no final state received")

            audience_list = final_state.get("audience", [])
            metrics_data = final_state.get("metrics", {})
            response_text = final_state.get("final_response", "")
            intent = final_state.get("intent", {})

            # Convert to response models
            audience = [
                {
                    "id": u["id"],
                    "name": u["name"],
                    "tier": u["tier"],
                    "score": u["score"],
                    "recentStore": u["recentStore"],
                    "lastVisit": u["lastVisit"],
                    "reason": u["reason"],
                    "matchScore": u.get("matchScore")
                }
                for u in audience_list
            ]

            metrics = {
                "audienceSize": metrics_data.get("audience_size", 0),
                "conversionRate": metrics_data.get("conversion_rate", 0),
                "estimatedRevenue": metrics_data.get("estimated_revenue", 0),
                "roi": metrics_data.get("roi", 0),
                "reachRate": metrics_data.get("reach_rate", 0),
                "qualityScore": metrics_data.get("quality_score", 0)
            }

            # Save turn to session
            turn = ConversationTurn(
                user_input=prompt,
                intent=intent,
                audience=audience_list,
                metrics=metrics_data,
                response=response_text
            )
            session.add_turn(turn)

            # Stream final result (thinking steps already streamed above)
            result = {
                "session_id": session.session_id,
                "audience": audience,
                "metrics": metrics,
                "response": response_text,
                "thinkingSteps": final_state.get("thinking_steps", []),
                "timestamp": datetime.now().isoformat()
            }
            yield f"event: analysis_complete\n"
            yield f"data: {json.dumps(result, ensure_ascii=False)}\n\n"

            logger.info(
                f"Streaming analysis completed for session {session.session_id}. "
                f"Selected {len(audience)} users. Turn {len(session.turns)}."
            )

        except Exception as e:
            logger.error(f"Error during streaming analysis: {e}", exc_info=True)
            error_event = {"error": str(e)}
            yield f"event: error\n"
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 nginx 缓冲
            "Content-Encoding": "none",  # 禁用压缩
        }
    )


@router.get("/users/high-potential", response_model=UserListResponse)
async def get_high_potential_users(limit: int = 50) -> UserListResponse:
    """
    Get high-potential users from the last analysis (cached result).

    If no analysis has been performed yet, returns all mock users ranked by score.

    Args:
        limit: Maximum number of users to return. Defaults to 50.

    Returns:
        List of high-potential users
    """
    global _last_analysis_result

    if _last_analysis_result:
        # Return cached analysis result
        users = _last_analysis_result.audience[:limit]
        return UserListResponse(users=users, total=len(users))
    else:
        # Return top users ranked by score
        selector = AudienceSelector()
        ranked = selector.rank_users(MOCK_USERS, limit=limit)
        users = [
            User(
                id=u["id"],
                name=u["name"],
                tier=u["tier"],
                score=u["score"],
                recentStore=u["recentStore"],
                lastVisit=u["lastVisit"],
                reason=u["reason"],
                matchScore=u.get("matchScore")
            )
            for u in ranked
        ]
        return UserListResponse(users=users, total=len(users))


@router.post("/prediction/metrics", response_model=PredictionMetrics)
async def predict_metrics(request: PredictionRequest) -> PredictionMetrics:
    """
    Predict marketing campaign metrics based on audience size.

    Args:
        request: PredictionRequest with audience size and optional constraints

    Returns:
        Predicted metrics including conversion rate, revenue, and ROI
    """
    logger.info(f"Predicting metrics for audience size: {request.audienceSize}")

    try:
        calculator = get_calculator()

        # Calculate metrics
        conversion_rate = calculator.calculate_conversion_rate(request.audienceSize)
        estimated_revenue = calculator.calculate_estimated_revenue(
            request.audienceSize,
            conversion_rate,
            AVG_ORDER_VALUE
        )
        roi = calculator.calculate_roi(estimated_revenue)
        reach_rate = calculator.calculate_reach_rate(request.audienceSize)

        metrics = PredictionMetrics(
            audienceSize=request.audienceSize,
            conversionRate=conversion_rate,
            estimatedRevenue=estimated_revenue,
            roi=roi,
            reachRate=reach_rate,
            qualityScore=85.0  # Default quality score
        )

        logger.info(f"Predicted metrics: {metrics}")
        return metrics

    except Exception as e:
        logger.error(f"Error predicting metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get("/health")
async def health_check() -> dict:
    """
    Health check endpoint with component initialization status.

    Returns:
        Health status including LLM, Graph, and Session Manager readiness.
    """
    from app.models.llm import get_llm_manager
    from app.agent.graph import get_agent_graph
    from app.core.session import get_session_manager

    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }

    try:
        # Check LLM Manager
        llm_manager = get_llm_manager()
        health_status["components"]["llm_manager"] = {
            "status": "ready",
            "model_type": llm_manager.model_type,
            "sdk_available": llm_manager.model.sdk_available if hasattr(llm_manager.model, 'sdk_available') else True
        }
    except Exception as e:
        health_status["components"]["llm_manager"] = {
            "status": "error",
            "error": str(e)
        }
        health_status["status"] = "degraded"

    try:
        # Check Agent Graph
        agent_graph = get_agent_graph()
        health_status["components"]["agent_graph"] = {
            "status": "ready",
            "nodes": 5
        }
    except Exception as e:
        health_status["components"]["agent_graph"] = {
            "status": "error",
            "error": str(e)
        }
        health_status["status"] = "degraded"

    try:
        # Check Session Manager
        session_manager = get_session_manager()
        active_sessions = len(session_manager.sessions)
        health_status["components"]["session_manager"] = {
            "status": "ready",
            "active_sessions": active_sessions
        }
    except Exception as e:
        health_status["components"]["session_manager"] = {
            "status": "error",
            "error": str(e)
        }
        health_status["status"] = "degraded"

    return health_status


# ====== Session Management Endpoints ======


@router.post("/session/reset", response_model=SessionResponse)
async def reset_session(session_id: str = None) -> SessionResponse:
    """
    Reset/clear a session and create a new one.

    This endpoint:
    1. Clears all conversation history for the given session
    2. Creates a new session with a fresh ID
    3. Returns the new session information

    When the user clicks "Clear" (清空), this endpoint should be called.

    Args:
        session_id: Optional existing session ID to clear. If not provided, creates new session.

    Returns:
        SessionResponse with new session_id and confirmation message.
    """
    logger.info(f"Resetting session: {session_id}")

    session_manager = get_session_manager()

    if session_id:
        # Clear existing session
        new_session = session_manager.clear_session(session_id)
    else:
        # Create new session
        new_session = session_manager.create_session()

    return SessionResponse(
        session_id=new_session.session_id,
        message="Session cleared. New session started." if session_id else "New session created.",
        created_at=new_session.created_at.isoformat()
    )


@router.post("/session/create", response_model=SessionResponse)
async def create_session() -> SessionResponse:
    """
    Create a new session explicitly.

    Returns:
        SessionResponse with new session_id.
    """
    session_manager = get_session_manager()
    new_session = session_manager.create_session()

    logger.info(f"Created new session: {new_session.session_id}")

    return SessionResponse(
        session_id=new_session.session_id,
        message="New session created.",
        created_at=new_session.created_at.isoformat()
    )


@router.get("/session/{session_id}", response_model=dict)
async def get_session_info(session_id: str) -> dict:
    """
    Get information about a specific session.

    Args:
        session_id: Session ID to retrieve.

    Returns:
        Session information including history and context.
    """
    session_manager = get_session_manager()
    session = session_manager.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session.to_dict()


# ====== Campaign Application Endpoint ======


@router.post("/campaign/apply", response_model=CampaignApplicationResponse)
async def apply_campaign(request: CampaignApplicationRequest) -> CampaignApplicationResponse:
    """
    Apply the current marketing campaign from a session.

    This endpoint is called when the user clicks "Apply" (应用).
    It retrieves the consolidated campaign state from the session and
    simulates sending it to a downstream Marketing Engine.

    Args:
        request: CampaignApplicationRequest with session_id.

    Returns:
        CampaignApplicationResponse with success status and mock payload.
    """
    logger.info(f"Applying campaign for session: {request.session_id}")

    session_manager = get_session_manager()
    session = session_manager.get_session(request.session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.turns:
        raise HTTPException(
            status_code=400,
            detail="No campaign to apply. Please run an analysis first."
        )

    # Get consolidated campaign context
    campaign_context = session.get_consolidated_context()

    # Build campaign summary
    campaign_summary = {
        "target_audience_size": len(campaign_context.get("target_audience", [])),
        "estimated_revenue": campaign_context.get("predicted_metrics", {}).get("estimated_revenue", 0),
        "estimated_roi": campaign_context.get("predicted_metrics", {}).get("roi", 0),
        "conversion_rate": campaign_context.get("predicted_metrics", {}).get("conversion_rate", 0),
        "target_tiers": campaign_context.get("campaign_intent", {}).get("target_tiers", []),
        "kpi_target": campaign_context.get("campaign_intent", {}).get("kpi", ""),
        "total_conversation_turns": campaign_context.get("total_turns", 0)
    }

    # Build mock payload for Marketing Engine
    # In production, this would be sent to real marketing automation system
    mock_campaign_id = f"camp_{uuid.uuid4().hex[:12]}"
    audience_ids = [u["id"] for u in campaign_context.get("target_audience", [])]

    mock_payload = {
        "campaign_id": mock_campaign_id,
        "session_id": request.session_id,
        "audience_ids": audience_ids,
        "audience_count": len(audience_ids),
        "kpi_target": campaign_context.get("campaign_intent", {}).get("kpi", ""),
        "target_tiers": campaign_context.get("campaign_intent", {}).get("target_tiers", []),
        "behavior_filters": campaign_context.get("campaign_intent", {}).get("behavior_filters", {}),
        "predicted_metrics": campaign_context.get("predicted_metrics", {}),
        "constraints": campaign_context.get("constraints", []),
        "created_at": campaign_context.get("created_at", ""),
        "applied_at": datetime.now().isoformat()
    }

    logger.info(
        f"Mock campaign application: {mock_campaign_id} "
        f"with {len(audience_ids)} users"
    )

    return CampaignApplicationResponse(
        status="success",
        message=f"Campaign {mock_campaign_id} successfully applied to marketing engine. "
                f"Targeting {len(audience_ids)} users.",
        campaign_summary=campaign_summary,
        mock_payload=mock_payload,
        timestamp=datetime.now()
    )


# =====================================================
# New V2 Endpoints - Refactored Workflow
# =====================================================

@router.post("/analysis/v2", response_model=AnalysisResponseV2)
async def analyze_marketing_goal_v2(
    request: AnalysisRequest,
) -> AnalysisResponseV2:
    """
    Analyze marketing goal with refactored multi-turn dialogue workflow.

    新的工作流支持：
    1. 意图识别 -> 如果不明确，返回澄清问题
    2. 特征匹配 -> 如果无法匹配，返回修正建议
    3. 策略生成 -> 效果预测 -> 最终分析

    Args:
        request: AnalysisRequest containing the marketing goal prompt and optional session_id

    Returns:
        AnalysisResponseV2 with status and appropriate response
    """
    logger.info(f"[V2] Received analysis request: {request.prompt}")

    if not request.prompt or not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    try:
        # Get or create session
        session_manager = get_session_manager()
        session = session_manager.get_or_create_session(request.session_id)

        logger.info(f"[V2] Using session: {session.session_id}")

        # Get conversation history as messages
        conversation_history = []
        for turn in session.turns:
            conversation_history.append({"role": "user", "content": turn.user_input})
            conversation_history.append({"role": "assistant", "content": turn.response})

        # Run the agent graph with new workflow
        from app.agent.graph import run_agent
        final_state = await run_agent(request.prompt, conversation_history)

        # Determine response status based on final_state
        final_response = final_state.get("final_response", "")
        intent_status = final_state.get("intent_status")
        match_status = final_state.get("match_status")

        # Check which path the workflow took
        if final_state.get("clarification_question"):
            # Path 1: Intent was ambiguous, need clarification
            status = "clarification_needed"
            response_text = final_state.get("clarification_question", final_response)

            response = AnalysisResponseV2(
                session_id=session.session_id,
                status=status,
                response=response_text,
                timestamp=datetime.now()
            )

        elif final_state.get("modification_request"):
            # Path 2: Feature matching failed, need modification
            status = "modification_needed"
            response_text = final_state.get("modification_request", final_response)

            response = AnalysisResponseV2(
                session_id=session.session_id,
                status=status,
                response=response_text,
                user_intent=final_state.get("user_intent"),
                timestamp=datetime.now()
            )

        else:
            # Path 3: Success - full analysis completed
            status = "success"

            # Extract all results
            user_intent_dict = final_state.get("user_intent", {})
            matched_features_list = final_state.get("matched_features", [])
            strategy_explanation = final_state.get("strategy_explanation", "")
            prediction_result_dict = final_state.get("prediction_result", {})

            # Convert to Pydantic models
            user_intent = UserIntentSchema(**user_intent_dict) if user_intent_dict else None

            matched_features = [
                MatchedFeatureSchema(**feat)
                for feat in matched_features_list
            ] if matched_features_list else None

            # Convert prediction_result
            if prediction_result_dict:
                # Convert top_users
                top_users_dicts = prediction_result_dict.get("top_users", [])
                top_users = [TopUserSchema(**u) for u in top_users_dicts]

                prediction_result = PredictionResultSchema(
                    audience_size=prediction_result_dict.get("audience_size", 0),
                    conversion_rate=prediction_result_dict.get("conversion_rate", 0),
                    estimated_revenue=prediction_result_dict.get("estimated_revenue", 0),
                    roi=prediction_result_dict.get("roi", 0),
                    quality_score=prediction_result_dict.get("quality_score", 0),
                    tier_distribution=prediction_result_dict.get("tier_distribution", {}),
                    top_users=top_users
                )
            else:
                prediction_result = None

            response = AnalysisResponseV2(
                session_id=session.session_id,
                status=status,
                response=final_response,
                user_intent=user_intent,
                matched_features=matched_features,
                strategy_explanation=strategy_explanation,
                prediction_result=prediction_result,
                timestamp=datetime.now()
            )

        # Save turn to session
        turn = ConversationTurn(
            user_input=request.prompt,
            intent=final_state.get("user_intent", {}),
            audience=[],  # V2 doesn't return full audience list in same format
            metrics=final_state.get("prediction_result", {}),
            response=final_response
        )
        session.add_turn(turn)

        logger.info(
            f"[V2] Analysis completed for session {session.session_id}. "
            f"Status: {status}. Turn {len(session.turns)}."
        )
        return response

    except Exception as e:
        logger.error(f"[V2] Error during analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/analysis/v2/stream")
async def analyze_marketing_goal_v2_stream(
    prompt: str,
    session_id: str = None
):
    """
    Analyze marketing goal with V2 workflow and streaming step-by-step reasoning.

    这个endpoint使用新的V2工作流，并且流式返回：
    1. LLM的逐步推理过程（Chain-of-Thought）
    2. 每个节点的执行状态
    3. 最终的分析结果

    支持多轮对话，通过 session_id 参数传递。

    SSE事件类型：
    - node_start: 节点开始执行 {"type": "node_start", "node": "intent_recognition", "title": "意图识别"}
    - reasoning: LLM推理步骤 {"type": "reasoning", "node": "intent_recognition", "data": "推理文本..."}
    - node_complete: 节点完成 {"type": "node_complete", "node": "intent_recognition", "data": {...}}
    - workflow_complete: 工作流完成 {"type": "workflow_complete", "status": "success/clarification_needed/modification_needed", "data": {...}}
    - error: 错误 {"type": "error", "data": "错误信息"}

    Args:
        prompt: Marketing goal prompt as query parameter
        session_id: Optional session ID for multi-turn conversation

    Returns:
        StreamingResponse with SSE events
    """
    logger.info(f"[V2 Stream] Received streaming analysis request: {prompt}")

    async def event_generator() -> AsyncIterator[str]:
        """Generate SSE events for V2 workflow with reasoning."""
        try:
            # Get or create session
            session_manager = get_session_manager()
            session = session_manager.get_or_create_session(session_id)

            logger.info(f"[V2 Stream] Using session: {session.session_id}")

            # Get conversation history
            conversation_history = []
            for turn in session.turns:
                conversation_history.append({"role": "user", "content": turn.user_input})
                conversation_history.append({"role": "assistant", "content": turn.response})

            # Run the V2 workflow with streaming
            from app.agent.graph import run_agent_stream_v2

            final_state = {}
            final_response = ""
            status = "success"

            async for event in run_agent_stream_v2(prompt, conversation_history):
                # Forward all events to frontend - 立即发送，不缓冲
                event_data = f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                yield event_data

                # 记录发送的事件
                event_type = event.get("type")
                if event_type == "node_complete":
                    logger.info(f"[V2 Stream] Sent node_complete event for {event.get('node')}")
                elif event_type == "node_start":
                    logger.info(f"[V2 Stream] Sent node_start event for {event.get('node')}")

                # Track final state
                if event["type"] == "node_complete":
                    node = event.get("node")
                    data = event.get("data", {})
                    final_state.update(data)

                    # Check for early exits
                    if node == "ask_clarification" and data.get("clarification_question"):
                        status = "clarification_needed"
                        final_response = data.get("clarification_question", "")
                    elif node == "request_modification" and data.get("modification_request"):
                        status = "modification_needed"
                        final_response = data.get("modification_request", "")
                    elif node == "final_analysis" and data.get("final_response"):
                        status = "success"
                        final_response = data.get("final_response", "")

            # Send workflow completion event
            completion_event = {
                "type": "workflow_complete",
                "status": status,
                "session_id": session.session_id,
                "data": {
                    "response": final_response,
                    "user_intent": final_state.get("user_intent"),
                    "matched_features": final_state.get("matched_features"),
                    "strategy_explanation": final_state.get("strategy_explanation"),
                    "prediction_result": final_state.get("prediction_result"),
                }
            }
            logger.info(f"[V2 Stream] Sending workflow_complete event")
            yield f"data: {json.dumps(completion_event, ensure_ascii=False)}\n\n"

            # Save turn to session
            turn = ConversationTurn(
                user_input=prompt,
                intent=final_state.get("user_intent", {}),
                audience=[],
                metrics=final_state.get("prediction_result", {}),
                response=final_response
            )
            session.add_turn(turn)

            logger.info(
                f"[V2 Stream] Workflow completed for session {session.session_id}. "
                f"Status: {status}. Turn {len(session.turns)}."
            )

        except Exception as e:
            logger.error(f"[V2 Stream] Error during streaming: {e}", exc_info=True)
            error_event = {"type": "error", "data": str(e)}
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 nginx 缓冲
            "Content-Encoding": "none",  # 禁用压缩
        }
    )

