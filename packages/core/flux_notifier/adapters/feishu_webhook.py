from __future__ import annotations

import hashlib
import hmac
import time
from base64 import b64encode
from typing import Any

import httpx

from flux_notifier.adapters.base import AdapterBase, SendResult
from flux_notifier.config import FeishuWebhookConfig
from flux_notifier.schema import NotificationPayload

_TIMEOUT = 10.0


def _sign(secret: str, timestamp: int) -> str:
    payload = f"{timestamp}\n{secret}".encode()
    return b64encode(hmac.new(payload, digestmod=hashlib.sha256).digest()).decode()


def _build_card(payload: NotificationPayload) -> dict[str, Any]:
    header_color = {
        "completion": "green",
        "choice": "blue",
        "step": "purple",
        "input_required": "orange",
        "info": "grey",
        "warning": "yellow",
        "error": "red",
    }.get(payload.event_type.value, "grey")

    elements: list[dict[str, Any]] = []

    if payload.body:
        elements.append({
            "tag": "markdown",
            "content": payload.body.replace("\\n", "\n"),
        })

    if payload.image:
        elements.append({
            "tag": "img",
            "img_key": payload.image.url,
            "alt": {"tag": "plain_text", "content": payload.image.alt or ""},
            "mode": "fit_horizontal",
        })

    if payload.actions:
        labels = " / ".join(f"**{a.label}**" for a in payload.actions)
        elements.append({
            "tag": "markdown",
            "content": f"💡 请在其他终端响应：{labels}",
        })

    return {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": payload.title},
                "template": header_color,
            },
            "elements": elements,
        },
    }


class FeishuWebhookAdapter(AdapterBase):
    name = "feishu_webhook"

    def __init__(self, config: FeishuWebhookConfig) -> None:
        self._config = config

    async def send(self, payload: NotificationPayload) -> SendResult:
        body = _build_card(payload)

        if self._config.secret:
            timestamp = int(time.time())
            body["timestamp"] = str(timestamp)
            body["sign"] = _sign(self._config.secret, timestamp)

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.post(self._config.webhook_url, json=body)
                resp.raise_for_status()
                data = resp.json()
                if data.get("code", 0) != 0:
                    return SendResult(
                        success=False,
                        adapter=self.name,
                        message=f"feishu error {data.get('code')}: {data.get('msg')}",
                    )
                return SendResult(success=True, adapter=self.name)
        except httpx.HTTPError as exc:
            return SendResult(success=False, adapter=self.name, message=str(exc))

    async def health_check(self) -> bool:
        return bool(self._config.webhook_url)
