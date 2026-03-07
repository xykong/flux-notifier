from __future__ import annotations

from pytest_httpx import HTTPXMock

from flux_notifier.adapters.wechat_work import (
    _MSG_URL,
    _TOKEN_URL,
    WechatWorkAdapter,
    _build_text_card,
)
from flux_notifier.config import WechatWorkConfig
from flux_notifier.schema import Action, ActionStyle, JumpTo, JumpToType, NotificationPayload

CFG = WechatWorkConfig(
    corp_id="ww_test_corp",
    agent_id=1000001,
    secret="test_secret",
    to_user="test_user",
)

_TOKEN_RESP = {"errcode": 0, "errmsg": "ok", "access_token": "test-token", "expires_in": 7200}
_MSG_OK = {"errcode": 0, "errmsg": "ok", "msgid": "id_abc"}


def _add_token(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{_TOKEN_URL}?corpid=ww_test_corp&corpsecret=test_secret",
        method="GET",
        json=_TOKEN_RESP,
    )


def _add_msg(httpx_mock: HTTPXMock, json: dict | None = None, status_code: int = 200) -> None:
    httpx_mock.add_response(
        url=f"{_MSG_URL}?access_token=test-token",
        method="POST",
        json=json if json is not None else _MSG_OK,
        status_code=status_code,
    )


def test_build_text_card_basic():
    payload = NotificationPayload(title="Hello", body="some body")
    card = _build_text_card(payload)
    assert card["msgtype"] == "textcard"
    assert card["textcard"]["title"] == "Hello"
    assert "some body" in card["textcard"]["description"]


def test_build_text_card_no_body():
    payload = NotificationPayload(title="T")
    card = _build_text_card(payload)
    assert card["textcard"]["description"] == "T"


def test_build_text_card_actions_in_description():
    payload = NotificationPayload(
        title="T",
        actions=[
            Action(id="a", label="Accept", style=ActionStyle.PRIMARY),
            Action(id="b", label="Reject"),
        ],
    )
    card = _build_text_card(payload)
    assert "Accept" in card["textcard"]["description"]
    assert "Reject" in card["textcard"]["description"]
    assert card["textcard"]["btntxt"] == "Accept"


def test_build_text_card_jump_to_url():
    payload = NotificationPayload(
        title="T",
        actions=[
            Action(
                id="open",
                label="Open",
                jump_to=JumpTo(type=JumpToType.URL, target="https://example.com"),
            )
        ],
    )
    card = _build_text_card(payload)
    assert card["textcard"]["url"] == "https://example.com"


def test_build_text_card_no_jump_has_fallback_url():
    payload = NotificationPayload(title="T")
    card = _build_text_card(payload)
    assert card["textcard"]["url"].startswith("https://")


async def test_send_success(httpx_mock: HTTPXMock):
    _add_token(httpx_mock)
    _add_msg(httpx_mock)

    adapter = WechatWorkAdapter(CFG)
    result = await adapter.send(NotificationPayload(title="Hello"))

    assert result.success is True
    assert result.adapter == "wechat_work"


async def test_send_api_error(httpx_mock: HTTPXMock):
    _add_token(httpx_mock)
    _add_msg(httpx_mock, json={"errcode": 60011, "errmsg": "no privilege"})

    adapter = WechatWorkAdapter(CFG)
    result = await adapter.send(NotificationPayload(title="Hello"))

    assert result.success is False
    assert "60011" in result.message
    assert "no privilege" in result.message


async def test_send_token_error(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{_TOKEN_URL}?corpid=ww_test_corp&corpsecret=test_secret",
        method="GET",
        json={"errcode": 40013, "errmsg": "invalid corpid"},
    )

    adapter = WechatWorkAdapter(CFG)
    result = await adapter.send(NotificationPayload(title="Hello"))

    assert result.success is False
    assert "40013" in result.message


async def test_send_http_error(httpx_mock: HTTPXMock):
    _add_token(httpx_mock)
    _add_msg(httpx_mock, status_code=500)

    adapter = WechatWorkAdapter(CFG)
    result = await adapter.send(NotificationPayload(title="Hello"))

    assert result.success is False


async def test_send_body_contains_agent_and_user(httpx_mock: HTTPXMock):
    _add_token(httpx_mock)
    _add_msg(httpx_mock)

    adapter = WechatWorkAdapter(CFG)
    await adapter.send(NotificationPayload(title="Hello"))

    import json

    requests = httpx_mock.get_requests()
    msg_req = requests[1]
    body = json.loads(msg_req.content)
    assert body["touser"] == "test_user"
    assert body["agentid"] == 1000001


async def test_health_check_fully_configured():
    adapter = WechatWorkAdapter(CFG)
    assert await adapter.health_check() is True


async def test_health_check_missing_corp_id():
    cfg = WechatWorkConfig(corp_id="", agent_id=1, secret="s")
    adapter = WechatWorkAdapter(cfg)
    assert await adapter.health_check() is False


async def test_health_check_missing_secret():
    cfg = WechatWorkConfig(corp_id="ww", agent_id=1, secret="")
    adapter = WechatWorkAdapter(cfg)
    assert await adapter.health_check() is False
