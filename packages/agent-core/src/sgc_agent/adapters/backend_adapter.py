from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class WebhookPayload:
    event_type: str
    session_id: str
    data: dict[str, Any]


class BackendAdapter(ABC):
    """Optional callback interface for backend integration. Default: no-op."""

    @abstractmethod
    async def on_emergency_logged(self, payload: WebhookPayload) -> None:
        pass

    @abstractmethod
    async def on_human_review_required(self, payload: WebhookPayload) -> None:
        pass

    @abstractmethod
    async def on_booking_requested(self, payload: WebhookPayload) -> None:
        pass


class NoOpBackendAdapter(BackendAdapter):
    """Default stub — agent works fully standalone without backend callbacks."""

    async def on_emergency_logged(self, payload: WebhookPayload) -> None:
        pass

    async def on_human_review_required(self, payload: WebhookPayload) -> None:
        pass

    async def on_booking_requested(self, payload: WebhookPayload) -> None:
        pass


class WebhookBackendAdapter(BackendAdapter):
    """HTTP webhook adapter for backend event notifications."""

    def __init__(self, webhook_url: str, api_key: str = ""):
        self.webhook_url = webhook_url
        self.api_key = api_key

    async def _post(self, payload: WebhookPayload) -> None:
        import httpx
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        async with httpx.AsyncClient() as client:
            await client.post(
                self.webhook_url,
                json={
                    "event_type": payload.event_type,
                    "session_id": payload.session_id,
                    "data": payload.data,
                },
                headers=headers,
                timeout=10,
            )

    async def on_emergency_logged(self, payload: WebhookPayload) -> None:
        await self._post(payload)

    async def on_human_review_required(self, payload: WebhookPayload) -> None:
        await self._post(payload)

    async def on_booking_requested(self, payload: WebhookPayload) -> None:
        await self._post(payload)
