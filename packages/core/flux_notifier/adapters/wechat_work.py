from __future__ import annotations

import logging
from typing import Any

import httpx

from flux_notifier.adapters.base import AdapterBase, SendResult
from flux_notifier.config import WechatWorkConfig
from flux_notifier.schema import NotificationPayload

logger = logging.getLogger(__name__)

_TIMEOUT = 10.0
_TOKEN_URL = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
_MSG_URL = "https://qyapi.weixin.qq.com/cgi-bin/message/send"


async def _get_access_token(client: httpx.AsyncClient, config: WechatWorkConfig) -> str:
    resp = await client.get(
        _TOKEN_URL,
        params={
            "corpid": config.corp_id,
            "corpsecret": config.secret,
        },
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("errcode", 0) != 0:
        raise RuntimeError(f"wechat_work token error {data.get('errcode')}: {data.get('errmsg')}")
    return str(data["access_token"])


def _build_text_card(payload: NotificationPayload) -> dict[str, Any]:
    description_parts = []
    if payload.body:
        description_parts.append(payload.body)
    if payload.actions:
        labels = " | ".join(a.label for a in payload.actions)
        description_parts.append(f"\n选项：{labels}")

    description = "\n".join(description_parts) if description_parts else payload.title

    jump_url = ""
    if payload.actions:
        for action in payload.actions:
            if action.jump_to:
                jump_url = action.jump_to.target
                break

    return {
        "msgtype": "textcard",
        "textcard": {
            "title": payload.title,
            "description": description,
            "url": jump_url or "https://work.weixin.qq.com",
            "btntxt": payload.actions[0].label if payload.actions else "查看",
        },
    }


class WechatWorkAdapter(AdapterBase):
    name = "wechat_work"

    def __init__(self, config: WechatWorkConfig) -> None:
        self._config = config

    async def send(self, payload: NotificationPayload) -> SendResult:
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                token = await _get_access_token(client, self._config)
                card = _build_text_card(payload)
                body: dict[str, Any] = {
                    **card,
                    "touser": self._config.to_user,
                    "agentid": self._config.agent_id,
                }
                resp = await client.post(
                    _MSG_URL,
                    params={"access_token": token},
                    json=body,
                )
                resp.raise_for_status()
                data = resp.json()
                errcode = data.get("errcode", 0)
                if errcode != 0:
                    return SendResult(
                        success=False,
                        adapter=self.name,
                        message=f"wechat_work error {errcode}: {data.get('errmsg')}",
                    )
                return SendResult(success=True, adapter=self.name)
        except httpx.HTTPError as exc:
            logger.error("wechat_work send failed: %s", exc)
            return SendResult(success=False, adapter=self.name, message=str(exc))
        except Exception as exc:
            logger.error("wechat_work unexpected error: %s", exc)
            return SendResult(success=False, adapter=self.name, message=str(exc))

    async def health_check(self) -> bool:
        return bool(
            self._config.corp_id
            and self._config.secret
            and self._config.agent_id
        )
