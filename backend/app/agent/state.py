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

    # Multi-turn conversation support
    conversation_context: str  # Formatted context from previous turns
    is_modification: bool  # Whether this is modifying existing intent
    previous_intent: dict[str, Any] | None  # Intent from previous turn

    # Processing stages
    intent: dict[str, Any]  # Parsed user intent
    features: dict[str, Any]  # Extracted features/rules
    audience: list[dict[str, Any]]  # Selected users
    metrics: dict[str, Any]  # Calculated metrics

    # Tracking
    thinking_steps: list[ThinkingStep]

    # Output
    final_response: str
