"""Session and memory management for multi-turn conversations."""
import uuid
import logging
from datetime import datetime
from typing import Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class ConversationTurn:
    """A single turn in a conversation."""

    def __init__(
        self,
        user_input: str,
        intent: dict[str, Any],
        audience: list[dict[str, Any]],
        metrics: dict[str, Any],
        response: str,
        timestamp: Optional[datetime] = None
    ):
        """Initialize a conversation turn.

        Args:
            user_input: User's prompt/message.
            intent: Parsed marketing intent.
            audience: Selected audience.
            metrics: Campaign metrics.
            response: Agent's response.
            timestamp: When this turn occurred.
        """
        self.user_input = user_input
        self.intent = intent
        self.audience = audience
        self.metrics = metrics
        self.response = response
        self.timestamp = timestamp or datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user_input": self.user_input,
            "intent": self.intent,
            "audience": self.audience,
            "metrics": self.metrics,
            "response": self.response,
            "timestamp": self.timestamp.isoformat()
        }


class Session:
    """A marketing agent session with conversation history."""

    def __init__(self, session_id: Optional[str] = None):
        """Initialize a new session.

        Args:
            session_id: Unique session identifier. Generated if not provided.
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.turns: list[ConversationTurn] = []
        self.current_context: dict[str, Any] = {}

    def add_turn(self, turn: ConversationTurn) -> None:
        """Add a new conversation turn.

        Args:
            turn: The conversation turn to add.
        """
        self.turns.append(turn)
        self.updated_at = datetime.now()

        # Update current context with latest state
        self.current_context = {
            "latest_intent": turn.intent,
            "latest_audience": turn.audience,
            "latest_metrics": turn.metrics,
            "total_turns": len(self.turns)
        }

    def get_history_summary(self, max_turns: int = 3) -> str:
        """Get a summary of recent conversation history.

        Args:
            max_turns: Maximum number of recent turns to include.

        Returns:
            Formatted summary string.
        """
        if not self.turns:
            return "这是一个新会话。"

        recent_turns = self.turns[-max_turns:]
        summary_parts = []

        for i, turn in enumerate(recent_turns, 1):
            summary_parts.append(
                f"第{i}轮:\n"
                f"  用户需求: {turn.user_input}\n"
                f"  KPI目标: {turn.intent.get('kpi', 'N/A')}\n"
                f"  目标等级: {', '.join(turn.intent.get('target_tiers', []))}\n"
                f"  圈选人数: {len(turn.audience)}\n"
            )

        return "\n".join(summary_parts)

    def get_consolidated_context(self) -> dict[str, Any]:
        """Get consolidated context for current marketing campaign.

        This is used when user wants to apply the campaign.

        Returns:
            Dictionary with complete campaign context.
        """
        if not self.turns:
            return {}

        latest = self.turns[-1]

        # Consolidate information from all turns
        all_constraints = []
        for turn in self.turns:
            constraints = turn.intent.get("constraints", [])
            all_constraints.extend(constraints)

        return {
            "session_id": self.session_id,
            "campaign_intent": latest.intent,
            "target_audience": latest.audience,
            "predicted_metrics": latest.metrics,
            "conversation_history": self.get_history_summary(),
            "constraints": list(set(all_constraints)),  # Deduplicate
            "total_turns": len(self.turns),
            "created_at": self.created_at.isoformat(),
            "last_updated": self.updated_at.isoformat()
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "turns": [turn.to_dict() for turn in self.turns],
            "current_context": self.current_context
        }


class MemoryManager:
    """Manages conversation memory and summarization."""

    def __init__(self):
        """Initialize memory manager."""
        self.max_history_tokens = 2000  # Approximate token limit for context

    def build_context_for_llm(
        self,
        session: Session,
        current_input: str
    ) -> str:
        """Build context string to pass to LLM for multi-turn understanding.

        Args:
            session: Current session.
            current_input: Current user input.

        Returns:
            Formatted context string.
        """
        if not session.turns:
            # First turn - no history
            return f"用户需求：{current_input}"

        # Get history summary
        history = session.get_history_summary(max_turns=3)

        # Build context with previous intent
        latest_turn = session.turns[-1]
        latest_intent = latest_turn.intent

        context = f"""## 对话历史

{history}

## 当前营销策略状态

当前KPI目标: {latest_intent.get('kpi', 'N/A')}
当前目标等级: {', '.join(latest_intent.get('target_tiers', []))}
当前人群规模: {len(latest_turn.audience)}人
当前行为筛选: {latest_intent.get('behavior_filters', {})}

## 新的用户输入

{current_input}

---

请分析用户的新输入，判断是：
1. **修改意图**：用户想调整现有策略（如"去掉年龄限制"、"只要VVIP"、"扩大到200人"）
2. **全新需求**：用户提出了完全新的营销目标

如果是修改意图，请基于当前状态进行增量调整。如果是全新需求，请重新分析。
"""
        return context

    def should_modify_intent(
        self,
        session: Session,
        current_input: str
    ) -> bool:
        """Determine if current input is a modification vs new request.

        Args:
            session: Current session.
            current_input: Current user input.

        Returns:
            True if this is a modification, False if it's a new request.
        """
        if not session.turns:
            return False

        # Check for modification keywords
        modification_keywords = [
            "改", "调整", "修改", "去掉", "移除", "增加", "减少",
            "只要", "不要", "扩大", "缩小", "限制", "放宽",
            "换成", "改成", "变成", "更新"
        ]

        return any(keyword in current_input for keyword in modification_keywords)


class SessionManager:
    """Manages all active sessions."""

    def __init__(self):
        """Initialize session manager."""
        self._sessions: dict[str, Session] = {}
        self.memory_manager = MemoryManager()
        logger.info("SessionManager initialized")

    def create_session(self) -> Session:
        """Create a new session.

        Returns:
            New Session instance.
        """
        session = Session()
        self._sessions[session.session_id] = session
        logger.info(f"Created new session: {session.session_id}")
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get an existing session.

        Args:
            session_id: Session identifier.

        Returns:
            Session if found, None otherwise.
        """
        return self._sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: Session identifier.

        Returns:
            True if deleted, False if not found.
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
            return True
        return False

    def clear_session(self, session_id: str) -> Optional[Session]:
        """Clear a session's history and create new session.

        Args:
            session_id: Session identifier to clear.

        Returns:
            New Session instance, or None if original session not found.
        """
        if session_id in self._sessions:
            self.delete_session(session_id)

        # Create new session
        return self.create_session()

    def get_or_create_session(self, session_id: Optional[str] = None) -> Session:
        """Get existing session or create new one.

        Args:
            session_id: Optional session identifier.

        Returns:
            Session instance.
        """
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        return self.create_session()

    def get_all_sessions(self) -> list[Session]:
        """Get all active sessions.

        Returns:
            List of all sessions.
        """
        return list(self._sessions.values())

    def session_count(self) -> int:
        """Get total number of active sessions.

        Returns:
            Number of sessions.
        """
        return len(self._sessions)


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get or create global session manager instance.

    Returns:
        SessionManager instance.
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
