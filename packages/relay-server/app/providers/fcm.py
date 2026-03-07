from __future__ import annotations

from typing import Any

import httpx

from app.config import settings

_FCM_URL = "https://fcm.googleapis.com/fcm/send"


async def send_fcm(device_token: str, title: str, body: str, data: dict[str, Any]) -> None:
    payload = {
        "to": device_token,
        "notification": {"title": title, "body": body},
        "data": data,
    }
    headers = {
        "Authorization": f"key={settings.fcm_server_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(_FCM_URL, json=payload, headers=headers)

    if resp.status_code != 200:
        raise RuntimeError(f"FCM error {resp.status_code}: {resp.text}")

    result = resp.json()
    if result.get("failure", 0) > 0:
        errors = [r.get("error") for r in result.get("results", []) if r.get("error")]
        raise RuntimeError(f"FCM delivery failure: {errors}")
