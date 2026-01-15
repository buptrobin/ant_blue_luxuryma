"""LLM integration for Volc Engine (火山引擎大模型API)."""
import os
import json
import logging
from typing import Any, AsyncIterator
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ChatModel(ABC):
    """Base class for chat models."""

    @abstractmethod
    async def call(self, prompt: str, **kwargs) -> str:
        """Call the model and return response.

        Args:
            prompt: User prompt/message.
            **kwargs: Additional parameters.

        Returns:
            Model response string.
        """
        pass

    @abstractmethod
    async def stream(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Stream the model response.

        Args:
            prompt: User prompt/message.
            **kwargs: Additional parameters.

        Yields:
            Response chunks.
        """
        pass


class VolcEngineChat(ChatModel):
    """Chat model using Volc Engine (ByteDance) API."""

    def __init__(
        self,
        access_key: str | None = None,
        secret_key: str | None = None,
        endpoint_id: str | None = None,
        region: str = "cn-beijing",
        model: str = "doubao-pro-32k",
        timeout: int = 60
    ):
        """Initialize Volc Engine chat model.

        Args:
            access_key: Volc Engine AccessKey. Defaults to VOLC_ACCESS_KEY env var.
            secret_key: Volc Engine SecretKey. Defaults to VOLC_SECRET_KEY env var.
            endpoint_id: Volc Engine endpoint ID. Defaults to VOLC_ENDPOINT_ID env var.
            region: Volc Engine region. Defaults to 'cn-beijing'.
            model: Model name. Defaults to 'doubao-pro-32k'.
            timeout: Request timeout in seconds.
        """
        self.access_key = access_key or os.getenv("VOLC_ACCESS_KEY", "")
        self.secret_key = secret_key or os.getenv("VOLC_SECRET_KEY", "")
        self.endpoint_id = endpoint_id or os.getenv("VOLC_ENDPOINT_ID", "")
        self.region = region
        self.model = model
        self.timeout = timeout

        if not all([self.access_key, self.secret_key, self.endpoint_id]):
            logger.warning(
                "Volc Engine credentials not fully configured. "
                "Please set VOLC_ACCESS_KEY, VOLC_SECRET_KEY, and VOLC_ENDPOINT_ID."
            )

        # Try to import SDK
        try:
            import volcenginesdkarkruntime
            self.sdk = volcenginesdkarkruntime
            self.sdk_available = True
        except ImportError:
            logger.warning("volcenginesdkarkruntime SDK not available. Using mock mode.")
            self.sdk = None
            self.sdk_available = False

    async def call(self, prompt: str, **kwargs) -> str:
        """Call Volc Engine API.

        Args:
            prompt: User prompt.
            **kwargs: Additional parameters (temperature, max_tokens, etc).

        Returns:
            Model response.
        """
        if not self.sdk_available:
            # Mock response for development
            logger.info("Using mock Volc Engine response for development")
            return self._get_mock_response(prompt)

        try:
            # Placeholder for actual SDK call
            # This would use the Volc Engine SDK when available
            logger.error("Volc Engine SDK call not yet implemented. Using mock response.")
            return self._get_mock_response(prompt)
        except Exception as e:
            logger.error(f"Error calling Volc Engine API: {e}")
            raise

    async def stream(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Stream response from Volc Engine API.

        Args:
            prompt: User prompt.
            **kwargs: Additional parameters.

        Yields:
            Response chunks.
        """
        if not self.sdk_available:
            # Mock streaming response for development
            for chunk in self._get_mock_stream(prompt):
                yield chunk
            return

        try:
            # Placeholder for actual SDK stream call
            logger.error("Volc Engine SDK streaming not yet implemented. Using mock response.")
            for chunk in self._get_mock_stream(prompt):
                yield chunk
        except Exception as e:
            logger.error(f"Error streaming from Volc Engine API: {e}")
            raise

    def _get_mock_response(self, prompt: str) -> str:
        """Get mock response for development and testing.

        Args:
            prompt: User prompt.

        Returns:
            Mock response string.
        """
        # Simple mock responses for different intent types
        if "圈选" in prompt or "人群" in prompt:
            return json.dumps({
                "kpi": "conversion_rate",
                "target_tiers": ["VVIP", "VIP"],
                "behavior_filters": {
                    "browse_frequency": 85,
                    "engagement_level": "high"
                },
                "size_preference": {"min": 50, "max": 500},
                "constraints": []
            }, ensure_ascii=False)
        else:
            return json.dumps({
                "kpi": "revenue",
                "target_tiers": ["VVIP", "VIP", "Member"],
                "behavior_filters": {},
                "size_preference": {"min": 100, "max": 1000},
                "constraints": []
            }, ensure_ascii=False)

    def _get_mock_stream(self, prompt: str):
        """Get mock streaming response for development.

        Args:
            prompt: User prompt.

        Yields:
            Mock response chunks.
        """
        mock_response = self._get_mock_response(prompt)
        # Simulate streaming by yielding character by character
        for char in mock_response:
            yield char


class LLMManager:
    """Manager for LLM operations."""

    def __init__(self, model_type: str = "volc_engine"):
        """Initialize LLM manager.

        Args:
            model_type: Type of model to use. Defaults to 'volc_engine'.
        """
        self.model_type = model_type

        if model_type == "volc_engine":
            self.model = VolcEngineChat()
        else:
            raise ValueError(f"Unknown model type: {model_type}")

    async def analyze_intent(self, user_input: str) -> dict[str, Any]:
        """Analyze user input to extract marketing intent.

        Args:
            user_input: User's marketing goal/prompt.

        Returns:
            Parsed intent dictionary.
        """
        prompt = f"""
你是一个营销专家。请分析以下用户的营销需求，提取出结构化的营销意图。

用户需求：{user_input}

请返回一个JSON格式的结果，包含以下字段：
- kpi: 核心KPI目标 (conversion_rate/revenue/visit_rate)
- target_tiers: 目标会员等级 (VVIP/VIP/Member)
- behavior_filters: 行为筛选条件
  - browse_frequency: 浏览频次阈值 (0-100)
  - engagement_level: 参与度级别 (high/medium/low)
- size_preference: 人群规模偏好
  - min: 最小规模
  - max: 最大规模
- constraints: 额外约束条件列表

只返回JSON，不要其他内容。
"""
        response = await self.model.call(prompt)
        try:
            intent = json.loads(response)
            return intent
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse intent response: {response}")
            # Return default intent
            return {
                "kpi": "conversion_rate",
                "target_tiers": ["VVIP", "VIP"],
                "behavior_filters": {},
                "size_preference": {"min": 50, "max": 500},
                "constraints": []
            }

    async def extract_features(self, intent: dict[str, Any]) -> dict[str, Any]:
        """Extract features for audience selection based on intent.

        Args:
            intent: Parsed user intent.

        Returns:
            Feature extraction result.
        """
        prompt = f"""
你是一个人群分析专家。根据以下营销意图，生成详细的人群筛选特征。

营销意图：
{json.dumps(intent, ensure_ascii=False, indent=2)}

请生成包含以下信息的JSON结果：
- feature_rules: 筛选规则列表
- weights: 各维度权重
- explanation: 规则的业务含义

只返回JSON，不要其他内容。
"""
        response = await self.model.call(prompt)
        try:
            features = json.loads(response)
            return features
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse features response: {response}")
            return {
                "feature_rules": [],
                "weights": {},
                "explanation": ""
            }

    async def generate_response(self, analysis_summary: dict[str, Any]) -> str:
        """Generate natural language response summarizing the analysis.

        Args:
            analysis_summary: Summary of the analysis including audience stats and metrics.

        Returns:
            Natural language response.
        """
        prompt = f"""
你是一个营销策略师。根据以下分析结果，生成一个简洁专业的营销建议。

分析结果：
- 圈选人群数: {analysis_summary.get('audience_size', 0)}
- 平均匹配度: {analysis_summary.get('avg_score', 0):.1f}
- 转化率预估: {analysis_summary.get('conversion_rate', 0):.2%}
- 收入预估: ¥{analysis_summary.get('estimated_revenue', 0):,.0f}

请生成一个不超过100字的营销建议，突出策略的关键点。
"""
        response = await self.model.call(prompt)
        return response.strip()


# Global LLM manager instance
_llm_manager: LLMManager | None = None


def get_llm_manager() -> LLMManager:
    """Get or create global LLM manager instance."""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
    return _llm_manager
