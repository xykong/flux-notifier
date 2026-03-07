from __future__ import annotations

import logging
import platform
from typing import Any

import httpx

from flux_notifier.adapters.base import AdapterBase, SendResult
from flux_notifier.config import PushConfig
from flux_notifier.schema import NotificationPayload

logger = logging.getLogger(__name__)

_TIMEOUT = 15.0


def _detect_platform() -> str:
    system = platform.system().lower()
    if system == "darwin":
        return "apns"
    return "fcm"


def _build_payload(payload: NotificationPayload) -> dict[str, Any]:
    data: dict[str, Any] = {
        "notification_id": payload.id,
        "event_type": payload.event_type.value,
    }
    if payload.actions:
        data["actions"] = [
            {"id": a.id, "label": a.label, "style": a.style.value} for a in payload.actions
        ]
    return data


class PushAdapter(AdapterBase):
    name = "push"

    def __init__(self, config: PushConfig) -> None:
        self._config = config

    async def send(self, payload: NotificationPayload) -> SendResult:
        push_platform = _detect_platform()
        body: dict[str, Any] = {
            "platform": push_platform,
            "device_token": self._config.device_token,
            "title": payload.title,
            "body": payload.body or "",
            "data": _build_payload(payload),
        }
        headers = {"Authorization": f"Bearer {self._config.api_key}"}

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.post(
                    f"{self._config.relay_url.rstrip('/')}/v1/push",
                    json=body,
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()
                if not data.get("ok", False):
                    return SendResult(
                        success=False,
                        adapter=self.name,
                        message=f"relay rejected: {data}",
                    )
                return SendResult(success=True, adapter=self.name)
        except httpx.HTTPStatusError as exc:
            logger.error("push relay error %s: %s", exc.response.status_code, exc.response.text)
            return SendResult(success=False, adapter=self.name, message=str(exc))
        except httpx.HTTPError as exc:
            logger.error("push relay transport error: %s", exc)
            return SendResult(success=False, adapter=self.name, message=str(exc))
        except Exception as exc:
            logger.error("push unexpected error: %s", exc)
            return SendResult(success=False, adapter=self.name, message=str(exc))

    async def health_check(self) -> bool:
        return bool(
            self._config.relay_url
            and self._config.api_key
            and self._config.device_token
        )
