from __future__ import annotations

import logging
from typing import Any

import httpx

from flux_notifier.adapters.base import AdapterBase, SendResult
from flux_notifier.adapters.feishu_webhook import _build_card
from flux_notifier.config import FeishuAppConfig
from flux_notifier.schema import NotificationPayload

logger = logging.getLogger(__name__)

_TIMEOUT = 10.0
_TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
_MSG_URL = "https://open.feishu.cn/open-apis/im/v1/messages"


async def _get_tenant_token(client: httpx.AsyncClient, config: FeishuAppConfig) -> str:
    resp = await client.post(
        _TOKEN_URL,
        json={"app_id": config.app_id, "app_secret": config.app_secret},
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code", -1) != 0:
        raise RuntimeError(f"tenant token error {data.get('code')}: {data.get('msg')}")
    return str(data["tenant_access_token"])


def _build_message_body(payload: NotificationPayload) -> dict[str, Any]:
    card = _build_card(payload)
    return {
        "msg_type": "interactive",
        "content": card["card"],
    }


class FeishuAppAdapter(AdapterBase):
    name = "feishu_app"

    def __init__(self, config: FeishuAppConfig) -> None:
        self._config = config

    async def send(self, payload: NotificationPayload) -> SendResult:
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                token = await _get_tenant_token(client, self._config)
                headers = {"Authorization": f"Bearer {token}"}
                body: dict[str, Any] = {
                    "receive_id": self._config.receiver_id,
                    "msg_type": "interactive",
                    "content": _build_card(payload)["card"],
                }
                resp = await client.post(
                    _MSG_URL,
                    params={"receive_id_type": self._config.receiver_id_type},
                    json=body,
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()
                code = data.get("code", 0)
                if code != 0:
                    return SendResult(
                        success=False,
                        adapter=self.name,
                        message=f"feishu_app error {code}: {data.get('msg')}",
                    )
                return SendResult(success=True, adapter=self.name)
        except httpx.HTTPError as exc:
            logger.error("feishu_app send failed: %s", exc)
            return SendResult(success=False, adapter=self.name, message=str(exc))
        except Exception as exc:
            logger.error("feishu_app unexpected error: %s", exc)
            return SendResult(success=False, adapter=self.name, message=str(exc))

    async def health_check(self) -> bool:
        return bool(
            self._config.app_id
            and self._config.app_secret
            and self._config.receiver_id
        )
