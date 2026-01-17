"""LangGraph state graph for the marketing agent - Refactored for multi-turn dialogue."""
import logging
from typing import Any, Literal

from langgraph.graph import StateGraph, END

from app.agent.state import AgentState
from app.agent.nodes import (
    intent_recognition_node,
    ask_clarification_node,
    feature_matching_node,
    request_modification_node,
    strategy_generation_node,
    impact_prediction_node,
    final_analysis_node,
)

logger = logging.getLogger(__name__)


# =====================================================
# 条件路由函数
# =====================================================

def route_after_intent_recognition(state: AgentState) -> Literal["ask_clarification", "feature_matching"]:
    """
    路由条件1: 意图识别后的路由

    - 如果 intent_status == "ambiguous" -> ask_clarification (然后END)
    - 如果 intent_status == "clear" -> feature_matching
    """
    intent_status = state.get("intent_status", "ambiguous")

    if intent_status == "ambiguous":
        logger.info("Intent is ambiguous, routing to ask_clarification")
        return "ask_clarification"
    else:
        logger.info("Intent is clear, routing to feature_matching")
        return "feature_matching"


def route_after_feature_matching(state: AgentState) -> Literal["request_modification", "strategy_generation"]:
    """
    路由条件2: 特征匹配后的路由

    - 如果 match_status == "needs_refinement" -> request_modification (然后END)
    - 如果 match_status == "success" -> strategy_generation
    """
    match_status = state.get("match_status", "needs_refinement")

    if match_status == "needs_refinement":
        logger.info("Feature matching needs refinement, routing to request_modification")
        return "request_modification"
    else:
        logger.info("Feature matching successful, routing to strategy_generation")
        return "strategy_generation"


# =====================================================
# Graph 构建
# =====================================================

def create_agent_graph() -> StateGraph:
    """
    Create and compile the marketing agent state graph.

    工作流程：
    1. Start -> intent_recognition
    2. Condition 1 (After intent_recognition):
       - intent_status == "ambiguous" -> ask_clarification -> END
       - intent_status == "clear" -> feature_matching
    3. Condition 2 (After feature_matching):
       - match_status == "needs_refinement" -> request_modification -> END
       - match_status == "success" -> strategy_generation
    4. Sequential flow:
       - strategy_generation -> impact_prediction -> final_analysis -> END

    Returns:
        Compiled StateGraph ready for execution.
    """
    # Create the state graph
    workflow = StateGraph(AgentState)

    # Add all nodes
    workflow.add_node("intent_recognition", intent_recognition_node)
    workflow.add_node("ask_clarification", ask_clarification_node)
    workflow.add_node("feature_matching", feature_matching_node)
    workflow.add_node("request_modification", request_modification_node)
    workflow.add_node("strategy_generation", strategy_generation_node)
    workflow.add_node("impact_prediction", impact_prediction_node)
    workflow.add_node("final_analysis", final_analysis_node)

    # Set entry point
    workflow.set_entry_point("intent_recognition")

    # Conditional routing after intent_recognition
    workflow.add_conditional_edges(
        "intent_recognition",
        route_after_intent_recognition,
        {
            "ask_clarification": "ask_clarification",
            "feature_matching": "feature_matching",
        }
    )

    # ask_clarification leads to END (user needs to provide more info)
    workflow.add_edge("ask_clarification", END)

    # Conditional routing after feature_matching
    workflow.add_conditional_edges(
        "feature_matching",
        route_after_feature_matching,
        {
            "request_modification": "request_modification",
            "strategy_generation": "strategy_generation",
        }
    )

    # request_modification leads to END (user needs to modify intent)
    workflow.add_edge("request_modification", END)

    # Sequential flow: strategy_generation -> impact_prediction -> final_analysis -> END
    workflow.add_edge("strategy_generation", "impact_prediction")
    workflow.add_edge("impact_prediction", "final_analysis")
    workflow.add_edge("final_analysis", END)

    # Compile the graph
    app = workflow.compile()
    logger.info("Agent graph compiled successfully with multi-turn dialogue support")

    return app


# =====================================================
# Global graph instance
# =====================================================

_agent_graph = None


def get_agent_graph():
    """Get or create the global agent graph instance."""
    global _agent_graph
    if _agent_graph is None:
        _agent_graph = create_agent_graph()
    return _agent_graph


# =====================================================
# 执行函数
# =====================================================

async def run_agent(user_input: str, conversation_history: list[dict] = None) -> dict[str, Any]:
    """
    Run the agent with the given user input.

    Args:
        user_input: User's current input.
        conversation_history: Previous conversation messages (optional).

    Returns:
        Final state dictionary containing the response and all intermediate results.
    """
    graph = get_agent_graph()

    # Initialize state with user input and conversation history
    initial_state: AgentState = {
        "user_input": user_input,
        "messages": conversation_history or [],
    }

    logger.info(f"Starting agent execution with input: {user_input}")

    # Run the graph
    final_state = await graph.ainvoke(initial_state)

    logger.info(f"Agent execution completed. Final state keys: {final_state.keys()}")

    return final_state


async def run_agent_stream(user_input: str, conversation_history: list[dict] = None):
    """
    Run the agent with streaming support.

    Args:
        user_input: User's current input.
        conversation_history: Previous conversation messages (optional).

    Yields:
        State updates as they happen during graph execution.
    """
    graph = get_agent_graph()

    # Initialize state
    initial_state: AgentState = {
        "user_input": user_input,
        "messages": conversation_history or [],
    }

    logger.info(f"Starting agent execution (streaming) with input: {user_input}")

    # Stream the graph execution
    async for event in graph.astream(initial_state):
        logger.info(f"Stream event: {event}")
        yield event


async def run_agent_stream_v2(user_input: str, conversation_history: list[dict] = None):
    """
    Run the agent V2 workflow with streaming step-by-step reasoning.

    这个函数手动编排工作流，使用流式节点来提供实时推理过程。

    工作流程：
    1. intent_recognition (流式) -> 如果模糊 -> ask_clarification -> 结束
    2. feature_matching (流式) -> 如果失败 -> request_modification -> 结束
    3. strategy_generation (流式) -> impact_prediction -> final_analysis (流式) -> 结束

    Args:
        user_input: User's current input.
        conversation_history: Previous conversation messages (optional).

    Yields:
        Streaming events:
        - {"type": "node_start", "node": str, "title": str}
        - {"type": "reasoning", "node": str, "data": str}
        - {"type": "node_complete", "node": str, "data": dict}
    """
    from app.agent.streaming_nodes import (
        intent_recognition_node_stream,
        feature_matching_node_stream,
        strategy_generation_node_stream,
        final_analysis_node_stream,
    )
    from app.agent.nodes import (
        ask_clarification_node,
        request_modification_node,
        impact_prediction_node,
    )

    logger.info(f"[V2 Stream] Starting agent execution with input: {user_input}")

    # Initialize state
    state: AgentState = {
        "user_input": user_input,
        "messages": conversation_history or [],
    }

    # Step 1: Intent Recognition (streaming)
    logger.info("[V2 Stream] Step 1: Intent Recognition")
    async for event in intent_recognition_node_stream(state):
        yield event

        if event["type"] == "node_complete":
            # Update state with results
            state.update(event["data"])

    # Check intent status
    intent_status = state.get("intent_status", "ambiguous")

    if intent_status == "ambiguous":
        # Need clarification - run ask_clarification node (non-streaming)
        logger.info("[V2 Stream] Intent ambiguous, asking clarification")
        yield {"type": "node_start", "node": "ask_clarification", "title": "澄清问题"}

        clarification_result = await ask_clarification_node(state)
        state.update(clarification_result)

        yield {
            "type": "node_complete",
            "node": "ask_clarification",
            "data": clarification_result
        }

        # End workflow here
        logger.info("[V2 Stream] Workflow ended: clarification needed")
        return

    # Step 2: Feature Matching (streaming)
    logger.info("[V2 Stream] Step 2: Feature Matching")
    async for event in feature_matching_node_stream(state):
        yield event

        if event["type"] == "node_complete":
            state.update(event["data"])

    # Check match status
    match_status = state.get("match_status", "needs_refinement")

    if match_status == "needs_refinement":
        # Need modification - run request_modification node (non-streaming)
        logger.info("[V2 Stream] Feature matching failed, requesting modification")
        yield {"type": "node_start", "node": "request_modification", "title": "请求修正"}

        modification_result = await request_modification_node(state)
        state.update(modification_result)

        yield {
            "type": "node_complete",
            "node": "request_modification",
            "data": modification_result
        }

        # End workflow here
        logger.info("[V2 Stream] Workflow ended: modification needed")
        return

    # Step 3: Strategy Generation (streaming)
    logger.info("[V2 Stream] Step 3: Strategy Generation")
    async for event in strategy_generation_node_stream(state):
        yield event

        if event["type"] == "node_complete":
            state.update(event["data"])

    # Step 4: Impact Prediction (non-streaming, fast computation)
    logger.info("[V2 Stream] Step 4: Impact Prediction")
    yield {"type": "node_start", "node": "impact_prediction", "title": "效果预测"}

    prediction_result = await impact_prediction_node(state)
    state.update(prediction_result)

    yield {
        "type": "node_complete",
        "node": "impact_prediction",
        "data": prediction_result
    }

    # Step 5: Final Analysis (streaming)
    logger.info("[V2 Stream] Step 5: Final Analysis")
    async for event in final_analysis_node_stream(state):
        yield event

        if event["type"] == "node_complete":
            state.update(event["data"])

    logger.info("[V2 Stream] Workflow completed successfully")
    # Workflow ends naturally after final_analysis
