from __future__ import annotations

from unittest.mock import patch

from pytest_httpx import HTTPXMock

from flux_notifier.adapters.push import PushAdapter, _build_payload, _detect_platform
from flux_notifier.config import PushConfig
from flux_notifier.schema import Action, ActionStyle, NotificationPayload

RELAY = "https://push.flux-notifier.dev"
CFG = PushConfig(relay_url=RELAY, api_key="key-abc", device_token="dev-tok-123")
PUSH_URL = f"{RELAY}/v1/push"


def test_detect_platform_darwin(monkeypatch):
    with patch("platform.system", return_value="Darwin"):
        assert _detect_platform() == "apns"


def test_detect_platform_linux(monkeypatch):
    with patch("platform.system", return_value="Linux"):
        assert _detect_platform() == "fcm"


def test_build_payload_basic():
    payload = NotificationPayload(title="T")
    data = _build_payload(payload)
    assert data["notification_id"] == payload.id
    assert data["event_type"] == payload.event_type.value


def test_build_payload_with_actions():
    payload = NotificationPayload(
        title="T",
        actions=[Action(id="ok", label="OK", style=ActionStyle.PRIMARY)],
    )
    data = _build_payload(payload)
    assert len(data["actions"]) == 1
    assert data["actions"][0]["id"] == "ok"


async def test_send_success(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=PUSH_URL, method="POST", json={"ok": True, "platform": "apns"})

    adapter = PushAdapter(CFG)
    result = await adapter.send(NotificationPayload(title="Hello"))

    assert result.success is True
    assert result.adapter == "push"


async def test_send_relay_rejection(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=PUSH_URL,
        method="POST",
        json={"ok": False, "detail": "bad token"},
    )

    adapter = PushAdapter(CFG)
    result = await adapter.send(NotificationPayload(title="Hello"))

    assert result.success is False
    assert "relay rejected" in result.message


async def test_send_http_error(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=PUSH_URL, method="POST", status_code=502)

    adapter = PushAdapter(CFG)
    result = await adapter.send(NotificationPayload(title="Hello"))

    assert result.success is False


async def test_send_bearer_header(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=PUSH_URL, method="POST", json={"ok": True, "platform": "apns"})

    adapter = PushAdapter(CFG)
    await adapter.send(NotificationPayload(title="Hello"))

    req = httpx_mock.get_request()
    assert req is not None
    assert req.headers["Authorization"] == "Bearer key-abc"


async def test_health_check_fully_configured():
    adapter = PushAdapter(CFG)
    assert await adapter.health_check() is True


async def test_health_check_missing_device_token():
    cfg = PushConfig(relay_url=RELAY, api_key="k", device_token="")
    adapter = PushAdapter(cfg)
    assert await adapter.health_check() is False


async def test_health_check_missing_relay_url():
    cfg = PushConfig(relay_url="", api_key="k", device_token="d")
    adapter = PushAdapter(cfg)
    assert await adapter.health_check() is False
