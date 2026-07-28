from dataclasses import dataclass, field
from pathlib import Path
import time

import litellm
import yaml
from sgc_shared.config import get_settings
from sgc_shared.constants import TaskType


@dataclass
class LLMResponse:
    content: str
    model: str
    latency_ms: int
    tokens_used: int = 0
    fallback_used: bool = False


@dataclass
class RouterConfig:
    task_routing: dict[str, dict[str, str]]
    allowlist: list[str]
    defaults: dict[str, float | int]
    providers: dict[str, dict[str, str]]


def load_router_config() -> RouterConfig:
    config_path = Path(__file__).parent / "config" / "models.yaml"
    with config_path.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return RouterConfig(
        task_routing=raw.get("task_routing", {}),
        allowlist=raw.get("allowlist", []),
        defaults=raw.get("defaults", {}),
        providers=raw.get("providers", {}),
    )


class ModelRouter:
    """Routes LLM requests to self-hosted or API models based on task type."""

    def __init__(self, config: RouterConfig | None = None, use_mock: bool = False):
        self.config = config or load_router_config()
        self.use_mock = use_mock
        if not use_mock:
            settings = get_settings()
            if settings.openai_api_key:
                litellm.openai_key = settings.openai_api_key
            litellm.set_verbose = False

    def _resolve_model(self, task: TaskType, prefer_local: bool = False) -> tuple[str, str]:
        routing = self.config.task_routing.get(task.value, {})
        if prefer_local:
            primary = routing.get("primary", get_settings().default_llm_model)
            fallback = routing.get("fallback", get_settings().fallback_llm_model)
        else:
            primary = routing.get("primary", get_settings().default_llm_model)
            fallback = routing.get("fallback", get_settings().fallback_llm_model)
        return primary, fallback

    def _is_allowed(self, model: str) -> bool:
        if not self.config.allowlist:
            return True
        return model in self.config.allowlist

    async def complete(
        self,
        messages: list[dict[str, str]],
        task: TaskType = TaskType.TOOL_NLG,
        prefer_local: bool = False,
        temperature: float | None = None,
    ) -> LLMResponse:
        if self.use_mock:
            from sgc_llm.providers.mock import MockModelRouter
            mock = MockModelRouter()
            result = await mock.complete(messages, task=task)
            return LLMResponse(
                content=result.content,
                model=result.model,
                latency_ms=result.latency_ms,
                tokens_used=result.tokens_used,
            )

        primary, fallback = self._resolve_model(task, prefer_local)
        temp = temperature if temperature is not None else float(self.config.defaults.get("temperature", 0.3))
        max_tokens = int(self.config.defaults.get("max_tokens", 2048))

        for idx, model in enumerate([primary, fallback]):
            if not self._is_allowed(model):
                continue
            try:
                start = time.perf_counter()
                kwargs: dict = {
                    "model": model,
                    "messages": messages,
                    "temperature": temp,
                    "max_tokens": max_tokens,
                }
                if model.startswith("ollama/"):
                    kwargs["api_base"] = get_settings().ollama_base_url

                response = await litellm.acompletion(**kwargs)
                latency = int((time.perf_counter() - start) * 1000)
                content = response.choices[0].message.content or ""
                tokens = getattr(response.usage, "total_tokens", 0) if response.usage else 0
                return LLMResponse(
                    content=content,
                    model=model,
                    latency_ms=latency,
                    tokens_used=tokens,
                    fallback_used=idx > 0,
                )
            except Exception:
                if idx == 1:
                    raise
                continue

        raise RuntimeError("All configured models failed")

    def list_models(self) -> list[str]:
        return self.config.allowlist
