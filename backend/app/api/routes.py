"""FastAPI routes for the marketing agent API."""
import json
import logging
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
)
from app.agent.graph import get_agent_graph
from app.data.selectors import AudienceSelector
from app.data.mock_users import MOCK_USERS, AVG_ORDER_VALUE
from app.utils.metrics import get_calculator

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
    1. Parse intent and extract KPIs
    2. Extract multi-dimensional features
    3. Select high-potential audience
    4. Predict campaign performance
    5. Generate strategic recommendations

    Args:
        request: AnalysisRequest containing the marketing goal prompt
        background_tasks: FastAPI background tasks

    Returns:
        AnalysisResponse with selected audience, metrics, and thinking steps
    """
    logger.info(f"Received analysis request: {request.prompt}")

    if not request.prompt or not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    try:
        # Run the agent graph
        graph = get_agent_graph()
        final_state = await graph.ainvoke({
            "user_input": request.prompt,
            "thinking_steps": []
        })

        # Extract results
        audience_list = final_state.get("audience", [])
        metrics_data = final_state.get("metrics", {})
        response_text = final_state.get("final_response", "")
        thinking_steps_raw = final_state.get("thinking_steps", [])

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

        response = AnalysisResponse(
            audience=audience,
            metrics=metrics,
            response=response_text,
            thinkingSteps=thinking_steps,
            timestamp=datetime.now()
        )

        # Cache the result
        global _last_analysis_result
        _last_analysis_result = response

        logger.info(f"Analysis completed. Selected {len(audience)} users.")
        return response

    except Exception as e:
        logger.error(f"Error during analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analysis/stream")
async def analyze_marketing_goal_stream(request: AnalysisRequest):
    """
    Analyze marketing goal with Server-Sent Events (SSE) streaming.

    Streams thinking steps in real-time as the agent processes the request,
    then sends the final analysis result.

    Args:
        request: AnalysisRequest containing the marketing goal prompt

    Returns:
        StreamingResponse with SSE events
    """
    logger.info(f"Received streaming analysis request: {request.prompt}")

    async def event_generator() -> AsyncIterator[str]:
        """Generate SSE events for thinking steps and final result."""
        try:
            # Run the agent graph
            graph = get_agent_graph()
            final_state = await graph.ainvoke({
                "user_input": request.prompt,
                "thinking_steps": []
            })

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

            # Stream final result
            result = {
                "audience": audience,
                "metrics": metrics,
                "response": response_text,
                "thinkingSteps": thinking_steps,
                "timestamp": datetime.now().isoformat()
            }
            yield f"event: analysis_complete\n"
            yield f"data: {json.dumps(result, ensure_ascii=False)}\n\n"

            logger.info(f"Streaming analysis completed. Selected {len(audience)} users.")

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
