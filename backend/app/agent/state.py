"""LangGraph state definition for the marketing agent."""
from typing import TypedDict, Any


class ThinkingStep(TypedDict):
    """A step in the agent's thinking process."""
    id: str
    title: str
    description: str
    status: str  # 'pending', 'active', 'completed'


class AgentState(TypedDict, total=False):
    """State for the marketing agent."""
    # Input
    user_input: str

    # Processing stages
    intent: dict[str, Any]  # Parsed user intent
    features: dict[str, Any]  # Extracted features/rules
    audience: list[dict[str, Any]]  # Selected users
    metrics: dict[str, Any]  # Calculated metrics

    # Tracking
    thinking_steps: list[ThinkingStep]

    # Output
    final_response: str
