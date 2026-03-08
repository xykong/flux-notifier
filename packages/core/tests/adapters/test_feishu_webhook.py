from __future__ import annotations

import hashlib
import hmac
import json
from base64 import b64encode

import pytest
from pytest_httpx import HTTPXMock

from flux_notifier.adapters.feishu_webhook import FeishuWebhookAdapter, _build_card, _sign
from flux_notifier.config import FeishuWebhookConfig
from flux_notifier.schema import (
    Action,
    ActionStyle,
    EventType,
    Image,
    JumpTo,
    JumpToType,
    NotificationPayload,
)

WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/test-token"


def test_sign_produces_valid_hmac():
    secret = "mysecret"
    timestamp = 1700000000
    expected_payload = f"{timestamp}\n{secret}".encode()
    expected = b64encode(hmac.new(expected_payload, digestmod=hashlib.sha256).digest()).decode()
    assert _sign(secret, timestamp) == expected


def test_sign_different_timestamps_differ():
    assert _sign("s", 1000) != _sign("s", 2000)


def test_sign_different_secrets_differ():
    assert _sign("s1", 1000) != _sign("s2", 1000)


def test_build_card_basic_structure():
    payload = NotificationPayload(title="Hello", body="World")
    card = _build_card(payload)

    assert card["msg_type"] == "interactive"
    assert card["card"]["header"]["title"]["content"] == "Hello"
    assert card["card"]["header"]["title"]["tag"] == "plain_text"


def test_build_card_body_element():
    payload = NotificationPayload(title="T", body="**bold** text")
    elements = _build_card(payload)["card"]["elements"]
    assert any(e["tag"] == "markdown" and e["content"] == "**bold** text" for e in elements)


def test_build_card_no_body_no_markdown_element():
    payload = NotificationPayload(title="T")
    elements = _build_card(payload)["card"]["elements"]
    assert not any(e["tag"] == "markdown" for e in elements)


def test_build_card_body_escapes_literal_newlines():
    payload = NotificationPayload(title="T", body="line1\\nline2")
    elements = _build_card(payload)["card"]["elements"]
    md = next(e for e in elements if e["tag"] == "markdown" and "line1" in e["content"])
    assert "\n" in md["content"]
    assert "\\n" not in md["content"]


def test_build_card_image_element():
    payload = NotificationPayload(
        title="T",
        image=Image(url="https://example.com/img.png", alt="screenshot"),
    )
    elements = _build_card(payload)["card"]["elements"]
    img = next(e for e in elements if e["tag"] == "img")
    assert img["img_key"] == "https://example.com/img.png"
    assert img["alt"]["content"] == "screenshot"


def test_build_card_no_image_when_not_set():
    payload = NotificationPayload(title="T")
    elements = _build_card(payload)["card"]["elements"]
    assert not any(e["tag"] == "img" for e in elements)


def test_build_card_actions_renders_hint_not_buttons():
    payload = NotificationPayload(
        title="T",
        actions=[
            Action(id="ok", label="Confirm", style=ActionStyle.PRIMARY),
            Action(id="rm", label="Delete", style=ActionStyle.DESTRUCTIVE),
            Action(id="no", label="Cancel", style=ActionStyle.DEFAULT),
        ],
    )
    elements = _build_card(payload)["card"]["elements"]

    assert not any(e["tag"] == "action" for e in elements)
    hint = next(e for e in elements if e["tag"] == "markdown" and "💡" in e["content"])
    assert "Confirm" in hint["content"]
    assert "Delete" in hint["content"]
    assert "Cancel" in hint["content"]


def test_build_card_action_with_jump_to_renders_hint():
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
    elements = _build_card(payload)["card"]["elements"]
    assert not any(e["tag"] == "action" for e in elements)
    hint = next(e for e in elements if e["tag"] == "markdown" and "💡" in e["content"])
    assert "Open" in hint["content"]


def test_build_card_action_without_jump_to_renders_hint():
    payload = NotificationPayload(
        title="T",
        actions=[Action(id="x", label="MyAction")],
    )
    elements = _build_card(payload)["card"]["elements"]
    assert not any(e["tag"] == "action" for e in elements)
    hint = next(e for e in elements if e["tag"] == "markdown" and "💡" in e["content"])
    assert "MyAction" in hint["content"]


@pytest.mark.parametrize(
    "event_type, expected_color",
    [
        (EventType.COMPLETION, "green"),
        (EventType.CHOICE, "blue"),
        (EventType.STEP, "purple"),
        (EventType.INPUT_REQUIRED, "orange"),
        (EventType.INFO, "grey"),
        (EventType.WARNING, "yellow"),
        (EventType.ERROR, "red"),
    ],
)
def test_build_card_header_color_by_event_type(event_type, expected_color):
    payload = NotificationPayload(title="T", event_type=event_type)
    card = _build_card(payload)
    assert card["card"]["header"]["template"] == expected_color


async def test_send_success(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=WEBHOOK_URL,
        method="POST",
        json={"code": 0, "msg": "success"},
    )
    adapter = FeishuWebhookAdapter(FeishuWebhookConfig(webhook_url=WEBHOOK_URL))
    result = await adapter.send(NotificationPayload(title="Hello"))

    assert result.success is True
    assert result.adapter == "feishu_webhook"


async def test_send_feishu_api_error(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=WEBHOOK_URL,
        method="POST",
        json={"code": 9499, "msg": "token invalid"},
    )
    adapter = FeishuWebhookAdapter(FeishuWebhookConfig(webhook_url=WEBHOOK_URL))
    result = await adapter.send(NotificationPayload(title="Hello"))

    assert result.success is False
    assert "9499" in result.message
    assert "token invalid" in result.message


async def test_send_http_error(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=WEBHOOK_URL,
        method="POST",
        status_code=500,
    )
    adapter = FeishuWebhookAdapter(FeishuWebhookConfig(webhook_url=WEBHOOK_URL))
    result = await adapter.send(NotificationPayload(title="Hello"))

    assert result.success is False
    assert result.message != ""


async def test_send_includes_sign_when_secret_set(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=WEBHOOK_URL,
        method="POST",
        json={"code": 0, "msg": "success"},
    )
    adapter = FeishuWebhookAdapter(
        FeishuWebhookConfig(webhook_url=WEBHOOK_URL, secret="mysecret")
    )
    await adapter.send(NotificationPayload(title="Hello"))

    request = httpx_mock.get_request()
    assert request is not None
    body = json.loads(request.content)
    assert "sign" in body
    assert "timestamp" in body


async def test_send_no_sign_when_no_secret(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=WEBHOOK_URL,
        method="POST",
        json={"code": 0, "msg": "success"},
    )
    adapter = FeishuWebhookAdapter(FeishuWebhookConfig(webhook_url=WEBHOOK_URL))
    await adapter.send(NotificationPayload(title="Hello"))

    request = httpx_mock.get_request()
    assert request is not None
    body = json.loads(request.content)
    assert "sign" not in body
    assert "timestamp" not in body


async def test_send_sign_is_valid(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=WEBHOOK_URL,
        method="POST",
        json={"code": 0, "msg": "success"},
    )
    secret = "supersecret"
    adapter = FeishuWebhookAdapter(
        FeishuWebhookConfig(webhook_url=WEBHOOK_URL, secret=secret)
    )
    await adapter.send(NotificationPayload(title="Hello"))

    request = httpx_mock.get_request()
    assert request is not None
    body = json.loads(request.content)
    timestamp = int(body["timestamp"])
    assert body["sign"] == _sign(secret, timestamp)


async def test_health_check_with_url():
    adapter = FeishuWebhookAdapter(FeishuWebhookConfig(webhook_url=WEBHOOK_URL))
    assert await adapter.health_check() is True


async def test_health_check_empty_url():
    adapter = FeishuWebhookAdapter(FeishuWebhookConfig(webhook_url=""))
    assert await adapter.health_check() is False
