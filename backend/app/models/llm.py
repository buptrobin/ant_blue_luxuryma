"""LLM integration for Volc Engine Ark API (火山引擎大模型API)."""
import os
import json
import logging
from typing import Any, AsyncIterator
from abc import ABC, abstractmethod

import httpx

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


class ArkChat(ChatModel):
    """Chat model using Volc Engine Ark API (OpenAI-compatible)."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = "doubao-seed-1-8-251228",
        timeout: int = 60
    ):
        """Initialize Ark chat model.

        Args:
            api_key: Ark API Key. Defaults to ARK_API_KEY env var.
            base_url: Ark base URL. Defaults to ARK_BASE_URL env var.
            model: Model name. Defaults to 'doubao-seed-1-8-251228'.
            timeout: Request timeout in seconds.
        """
        self.api_key = api_key or os.getenv("ARK_API_KEY", "")
        self.base_url = base_url or os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3/")
        self.model = model or os.getenv("ARK_MODEL", "doubao-seed-1-8-251228")
        self.timeout = timeout

        # Ensure base_url has proper format
        if self.base_url and not self.base_url.endswith("/"):
            self.base_url += "/"

        if not self.api_key or not self.base_url:
            logger.warning(
                "Ark API credentials not fully configured. "
                "Please set ARK_API_KEY and ARK_BASE_URL."
            )
            self.sdk_available = False
        else:
            self.sdk_available = True
            logger.info(f"Ark API initialized with model: {self.model}")

    async def call(self, prompt: str, **kwargs) -> str:
        """Call Ark API and return response.

        Args:
            prompt: User prompt.
            **kwargs: Additional parameters (temperature, max_tokens, etc).

        Returns:
            Model response.
        """
        if not self.sdk_available:
            logger.warning("Ark API not available. Using mock response.")
            return self._get_mock_response(prompt)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}chat/completions",
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": kwargs.get("temperature", 0.7),
                        "max_tokens": kwargs.get("max_tokens", 800),  # Reduced from 2048
                    },
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()
                result = response.json()

                # Extract text from OpenAI-compatible response
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    logger.error(f"Unexpected response format: {result}")
                    return self._get_mock_response(prompt)

        except Exception as e:
            logger.error(f"Error calling Ark API: {e}")
            # Fallback to mock response
            return self._get_mock_response(prompt)

    async def stream(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Stream response from Ark API.

        Args:
            prompt: User prompt.
            **kwargs: Additional parameters.

        Yields:
            Response chunks.
        """
        # Log the max_tokens parameter for debugging
        max_tokens_param = kwargs.get("max_tokens", 800)
        logger.info(f"[DEBUG] stream() called with max_tokens={max_tokens_param}")

        if not self.sdk_available:
            logger.warning("Ark API not available. Using mock stream.")
            for chunk in self._get_mock_stream(prompt):
                yield chunk
            return

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}chat/completions",
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": True,
                        "temperature": kwargs.get("temperature", 0.7),
                        "max_tokens": kwargs.get("max_tokens", 800),  # Reduced from 2048
                    },
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:].strip()
                            if data and data != "[DONE]":
                                try:
                                    chunk_data = json.loads(data)
                                    if "choices" in chunk_data:
                                        delta = chunk_data["choices"][0].get("delta", {})
                                        if "content" in delta:
                                            yield delta["content"]
                                except json.JSONDecodeError:
                                    pass

        except Exception as e:
            logger.error(f"Error streaming from Ark API: {e}")
            # Fallback to mock stream
            for chunk in self._get_mock_stream(prompt):
                yield chunk

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

    def __init__(self, model_type: str = "ark"):
        """Initialize LLM manager.

        Args:
            model_type: Type of model to use. Defaults to 'ark'.
        """
        self.model_type = model_type

        if model_type == "ark":
            self.model = ArkChat()
        else:
            raise ValueError(f"Unknown model type: {model_type}")

    async def analyze_intent(self, user_input: str) -> dict[str, Any]:
        """Analyze user input to extract marketing intent.

        Args:
            user_input: User's marketing goal/prompt.

        Returns:
            Parsed intent dictionary.
        """
        prompt = f"""你是一个营销专家。请分析以下用户的营销需求，提取出结构化的营销意图。

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

只返回JSON，不要其他内容。"""
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
        prompt = f"""你是一个人群分析专家。根据以下营销意图，生成详细的人群筛选特征。

营销意图：
{json.dumps(intent, ensure_ascii=False, indent=2)}

请生成包含以下信息的JSON结果：
- feature_rules: 筛选规则列表
- weights: 各维度权重
- explanation: 规则的业务含义

只返回JSON，不要其他内容。"""
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
        prompt = f"""你是一个营销策略师。根据以下分析结果，生成一个简洁专业的营销建议。

分析结果：
- 圈选人群数: {analysis_summary.get('audience_size', 0)}
- 平均匹配度: {analysis_summary.get('avg_score', 0):.1f}
- 转化率预估: {analysis_summary.get('conversion_rate', 0):.2%}
- 收入预估: ¥{analysis_summary.get('estimated_revenue', 0):,.0f}

请生成一个不超过100字的营销建议，突出策略的关键点。"""
        response = await self.model.call(prompt)
        return response.strip()

    async def analyze_intent_stream(self, user_input: str) -> AsyncIterator[dict[str, Any]]:
        """Analyze user input with streaming (yields chunks in real-time).

        Args:
            user_input: User's marketing goal/prompt.

        Yields:
            Dict with 'type' and 'data':
            - {"type": "chunk", "data": str} - Text chunk from LLM
            - {"type": "complete", "data": dict} - Final parsed intent
            - {"type": "error", "data": str} - Error message
        """
        prompt = f"""你是一个营销专家。请分析以下用户的营销需求，提取出结构化的营销意图。

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

重要：只返回JSON对象，不要任何解释、不要markdown代码块、不要其他文字。直接输出纯JSON。"""

        full_response = ""
        try:
            async for chunk in self.model.stream(prompt, max_tokens=300):  # 严格限制 tokens
                full_response += chunk
                yield {"type": "chunk", "data": chunk}

            # Log the full response for debugging
            logger.info(f"[DEBUG] Full LLM response length: {len(full_response)} chars")
            logger.debug(f"[DEBUG] Full response preview: {full_response[:500]}...")

            # Try to parse final JSON
            try:
                intent = json.loads(full_response)
                yield {"type": "complete", "data": intent}
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse intent response: {full_response}")
                # Return default intent
                default_intent = {
                    "kpi": "conversion_rate",
                    "target_tiers": ["VVIP", "VIP"],
                    "behavior_filters": {},
                    "size_preference": {"min": 50, "max": 500},
                    "constraints": []
                }
                yield {"type": "complete", "data": default_intent}

        except Exception as e:
            logger.error(f"Error in analyze_intent_stream: {e}")
            yield {"type": "error", "data": str(e)}

    async def extract_features_stream(self, intent: dict[str, Any]) -> AsyncIterator[dict[str, Any]]:
        """Extract features with streaming.

        Args:
            intent: Parsed user intent.

        Yields:
            Dict with 'type' and 'data':
            - {"type": "chunk", "data": str} - Text chunk
            - {"type": "complete", "data": dict} - Final features
            - {"type": "error", "data": str} - Error message
        """
        prompt = f"""你是一个人群分析专家。根据以下营销意图，生成详细的人群筛选特征。

营销意图：
{json.dumps(intent, ensure_ascii=False, indent=2)}

请生成包含以下信息的JSON结果：
- feature_rules: 筛选规则列表
- weights: 各维度权重
- explanation: 规则的业务含义

重要：只返回JSON对象，不要任何解释、不要markdown代码块、不要其他文字。直接输出纯JSON。"""

        full_response = ""
        try:
            async for chunk in self.model.stream(prompt, max_tokens=400):  # 限制 tokens
                full_response += chunk
                yield {"type": "chunk", "data": chunk}

            # Try to parse final JSON
            try:
                features = json.loads(full_response)
                yield {"type": "complete", "data": features}
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse features response: {full_response}")
                default_features = {
                    "feature_rules": [],
                    "weights": {},
                    "explanation": ""
                }
                yield {"type": "complete", "data": default_features}

        except Exception as e:
            logger.error(f"Error in extract_features_stream: {e}")
            yield {"type": "error", "data": str(e)}

    async def generate_response_stream(self, analysis_summary: dict[str, Any]) -> AsyncIterator[dict[str, Any]]:
        """Generate response with streaming.

        Args:
            analysis_summary: Summary of the analysis.

        Yields:
            Dict with 'type' and 'data':
            - {"type": "chunk", "data": str} - Text chunk
            - {"type": "complete", "data": str} - Final response
            - {"type": "error", "data": str} - Error message
        """
        prompt = f"""你是一个营销策略师。根据以下分析结果，生成一个简洁专业的营销建议。

分析结果：
- 圈选人群数: {analysis_summary.get('audience_size', 0)}
- 平均匹配度: {analysis_summary.get('avg_score', 0):.1f}
- 转化率预估: {analysis_summary.get('conversion_rate', 0):.2%}
- 收入预估: ¥{analysis_summary.get('estimated_revenue', 0):,.0f}

请生成一个不超过100字的营销建议，突出策略的关键点。"""

        full_response = ""
        try:
            async for chunk in self.model.stream(prompt):
                full_response += chunk
                yield {"type": "chunk", "data": chunk}

            yield {"type": "complete", "data": full_response.strip()}

        except Exception as e:
            logger.error(f"Error in generate_response_stream: {e}")
            yield {"type": "error", "data": str(e)}


# Global LLM manager instance
_llm_manager: LLMManager | None = None


def get_llm_manager() -> LLMManager:
    """Get or create global LLM manager instance."""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
    return _llm_manager
