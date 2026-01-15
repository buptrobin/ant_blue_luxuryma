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

            # Run the agent graph
            graph = get_agent_graph()
            final_state = await graph.ainvoke(initial_state)

            # Stream thinking steps
            thinking_steps = final_state.get("thinking_steps", [])
            for step in thinking_steps:
                step_event = {
                    "stepId": step["id"],
                    "title": step["title"],
                    "description": step["description"],
                    "status": step["status"]
                }
                yield f"event: thinking_step\n"
                yield f"data: {json.dumps(step_event, ensure_ascii=False)}\n\n"

            # Extract results
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

            # Stream final result
            result = {
                "session_id": session.session_id,
                "audience": audience,
                "metrics": metrics,
                "response": response_text,
                "thinkingSteps": thinking_steps,
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
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
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
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


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
