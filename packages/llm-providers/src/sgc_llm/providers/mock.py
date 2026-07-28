"""Fallback LLM provider when LiteLLM/API is unavailable (dev/test)."""

from dataclasses import dataclass

from sgc_shared.constants import TaskType


@dataclass
class MockLLMResponse:
    content: str
    model: str
    latency_ms: int
    tokens_used: int = 0
    fallback_used: bool = False


class MockModelRouter:
    """Rule-based response generator for offline dev and testing."""

    async def complete(self, messages, task=TaskType.TOOL_NLG, **kwargs) -> MockLLMResponse:
        user_msg = messages[-1]["content"] if messages else ""
        if "Tool results" in user_msg:
            return MockLLMResponse(
                content=(
                    "Based on our records, I found the information you requested. "
                    "Please see the details above from our system. "
                    "Would you like me to help with anything else?"
                ),
                model="mock/local",
                latency_ms=10,
            )
        return MockLLMResponse(
            content="Hello! I'm your Smart Garage assistant. How can I help you with your vehicle today?",
            model="mock/local",
            latency_ms=5,
        )

    def list_models(self) -> list[str]:
        return ["mock/local"]
