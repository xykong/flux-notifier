from __future__ import annotations

import time
from typing import Any

import httpx
import jwt

from app.config import settings

_APNS_HOST_PROD = "https://api.push.apple.com"
_APNS_HOST_DEV = "https://api.sandbox.push.apple.com"
_APNS_PATH = "/3/device/{token}"


def _make_jwt() -> str:
    now = int(time.time())
    payload = {"iss": settings.apns_team_id, "iat": now}
    token: str = jwt.encode(
        payload,
        settings.apns_private_key,
        algorithm="ES256",
        headers={"kid": settings.apns_key_id},
    )
    return token


async def send_apns(device_token: str, title: str, body: str, data: dict[str, Any]) -> None:
    host = _APNS_HOST_PROD if settings.apns_production else _APNS_HOST_DEV
    url = host + _APNS_PATH.format(token=device_token)

    notification = {
        "aps": {
            "alert": {"title": title, "body": body},
            "sound": "default",
        },
        **data,
    }

    headers = {
        "authorization": f"bearer {_make_jwt()}",
        "apns-push-type": "alert",
        "apns-topic": settings.apns_bundle_id,
    }

    async with httpx.AsyncClient(http2=True) as client:
        resp = await client.post(url, json=notification, headers=headers)

    if resp.status_code != 200:
        raise RuntimeError(f"APNs error {resp.status_code}: {resp.text}")
