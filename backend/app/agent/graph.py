"""LangGraph state graph for the marketing agent."""
import logging
from typing import Any

from langgraph.graph import StateGraph

from app.agent.state import AgentState
from app.agent.nodes import (
    intent_analysis_node,
    feature_extraction_node,
    audience_selection_node,
    prediction_optimization_node,
    response_generation_node,
)

logger = logging.getLogger(__name__)


def create_agent_graph() -> StateGraph:
    """Create and compile the marketing agent state graph.

    The graph follows this flow:
    user_input → intent_analysis → feature_extraction → audience_selection
                 → prediction_optimization → response_generation

    Returns:
        Compiled StateGraph ready for execution.
    """
    # Create the state graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("intent_analysis", intent_analysis_node)
    workflow.add_node("feature_extraction", feature_extraction_node)
    workflow.add_node("audience_selection", audience_selection_node)
    workflow.add_node("prediction_optimization", prediction_optimization_node)
    workflow.add_node("response_generation", response_generation_node)

    # Add edges (workflow)
    workflow.add_edge("intent_analysis", "feature_extraction")
    workflow.add_edge("feature_extraction", "audience_selection")
    workflow.add_edge("audience_selection", "prediction_optimization")
    workflow.add_edge("prediction_optimization", "response_generation")

    # Set start node
    workflow.set_entry_point("intent_analysis")

    # Set end node
    workflow.set_finish_point("response_generation")

    # Compile the graph
    app = workflow.compile()
    logger.info("Agent graph compiled successfully")

    return app


# Global graph instance
_agent_graph = None


def get_agent_graph():
    """Get or create the global agent graph instance."""
    global _agent_graph
    if _agent_graph is None:
        _agent_graph = create_agent_graph()
    return _agent_graph


async def run_agent(user_input: str) -> tuple[dict[str, Any], list[dict]]:
    """Run the agent with the given user input.

    Args:
        user_input: User's marketing goal/prompt.

    Returns:
        Tuple of (final_state, thinking_steps)
    """
    graph = get_agent_graph()

    # Initialize state with user input
    initial_state: AgentState = {
        "user_input": user_input,
        "thinking_steps": [],
    }

    logger.info(f"Starting agent execution with input: {user_input}")

    # Run the graph
    final_state = await graph.ainvoke(initial_state)

    logger.info(f"Agent execution completed. Final state keys: {final_state.keys()}")

    thinking_steps = final_state.get("thinking_steps", [])

    return final_state, thinking_steps
