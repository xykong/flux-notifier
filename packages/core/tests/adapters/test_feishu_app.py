from __future__ import annotations

from pytest_httpx import HTTPXMock

from flux_notifier.adapters.feishu_app import _MSG_URL, _TOKEN_URL, FeishuAppAdapter
from flux_notifier.config import FeishuAppConfig
from flux_notifier.schema import NotificationPayload

CFG = FeishuAppConfig(
    app_id="cli_test_app",
    app_secret="test_secret",
    receiver_id="ou_user123",
    receiver_id_type="open_id",
)

_TOKEN_RESP = {"code": 0, "msg": "ok", "tenant_access_token": "t-token123", "expire": 7200}
_MSG_OK = {"code": 0, "msg": "success", "data": {"message_id": "om_abc"}}
_MSG_URL_WITH_PARAMS = f"{_MSG_URL}?receive_id_type=open_id"


def _add_token(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=_TOKEN_URL, method="POST", json=_TOKEN_RESP)


def _add_msg(httpx_mock: HTTPXMock, json: dict | None = None, status_code: int = 200) -> None:
    httpx_mock.add_response(
        url=_MSG_URL_WITH_PARAMS,
        method="POST",
        json=json if json is not None else _MSG_OK,
        status_code=status_code,
    )


async def test_send_success(httpx_mock: HTTPXMock):
    _add_token(httpx_mock)
    _add_msg(httpx_mock)

    adapter = FeishuAppAdapter(CFG)
    result = await adapter.send(NotificationPayload(title="Hello"))

    assert result.success is True
    assert result.adapter == "feishu_app"


async def test_send_uses_bearer_token(httpx_mock: HTTPXMock):
    _add_token(httpx_mock)
    _add_msg(httpx_mock)

    adapter = FeishuAppAdapter(CFG)
    await adapter.send(NotificationPayload(title="Hello"))

    requests = httpx_mock.get_requests()
    msg_req = requests[1]
    assert msg_req.headers["Authorization"] == "Bearer t-token123"


async def test_send_passes_receiver_id_type_as_param(httpx_mock: HTTPXMock):
    _add_token(httpx_mock)
    _add_msg(httpx_mock)

    adapter = FeishuAppAdapter(CFG)
    await adapter.send(NotificationPayload(title="Hello"))

    requests = httpx_mock.get_requests()
    msg_req = requests[1]
    assert msg_req.url.params["receive_id_type"] == "open_id"


async def test_send_api_error(httpx_mock: HTTPXMock):
    _add_token(httpx_mock)
    _add_msg(httpx_mock, json={"code": 99991677, "msg": "bot not in chat"})

    adapter = FeishuAppAdapter(CFG)
    result = await adapter.send(NotificationPayload(title="Hello"))

    assert result.success is False
    assert "99991677" in result.message
    assert "bot not in chat" in result.message


async def test_send_token_api_error(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=_TOKEN_URL,
        method="POST",
        json={"code": 10003, "msg": "invalid app_id"},
    )

    adapter = FeishuAppAdapter(CFG)
    result = await adapter.send(NotificationPayload(title="Hello"))

    assert result.success is False
    assert "10003" in result.message


async def test_send_http_transport_error(httpx_mock: HTTPXMock):
    _add_token(httpx_mock)
    _add_msg(httpx_mock, status_code=500)

    adapter = FeishuAppAdapter(CFG)
    result = await adapter.send(NotificationPayload(title="Hello"))

    assert result.success is False
    assert result.message != ""


async def test_send_message_body_contains_card(httpx_mock: HTTPXMock):
    _add_token(httpx_mock)
    _add_msg(httpx_mock)

    adapter = FeishuAppAdapter(CFG)
    await adapter.send(NotificationPayload(title="Card Title", body="some body"))

    import json

    requests = httpx_mock.get_requests()
    msg_req = requests[1]
    body = json.loads(msg_req.content)
    assert body["receive_id"] == "ou_user123"
    assert body["msg_type"] == "interactive"
    assert "header" in body["content"]


async def test_health_check_fully_configured():
    adapter = FeishuAppAdapter(CFG)
    assert await adapter.health_check() is True


async def test_health_check_missing_app_id():
    cfg = FeishuAppConfig(
        app_id="",
        app_secret="s",
        receiver_id="r",
    )
    adapter = FeishuAppAdapter(cfg)
    assert await adapter.health_check() is False


async def test_health_check_missing_receiver_id():
    cfg = FeishuAppConfig(
        app_id="cli_x",
        app_secret="s",
        receiver_id="",
    )
    adapter = FeishuAppAdapter(cfg)
    assert await adapter.health_check() is False
