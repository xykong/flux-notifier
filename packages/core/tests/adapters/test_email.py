from __future__ import annotations

from unittest.mock import AsyncMock, patch

import aiosmtplib
import pytest

from flux_notifier.adapters.email import EmailAdapter, _build_html, _build_message, _md_to_html
from flux_notifier.config import EmailConfig
from flux_notifier.schema import (
    Action,
    ActionStyle,
    EventType,
    Image,
    JumpTo,
    JumpToType,
    NotificationPayload,
)

CFG = EmailConfig(
    smtp_host="smtp.example.com",
    smtp_port=587,
    username="user@example.com",
    password="secret",
    **{"from": "Flux Notifier <user@example.com>"},
    to=["dest@example.com"],
    use_tls=True,
)


def test_md_to_html_bold():
    assert "<strong>hello</strong>" in _md_to_html("**hello**")


def test_md_to_html_italic():
    assert "<em>world</em>" in _md_to_html("*world*")


def test_md_to_html_code():
    assert "<code>x</code>" in _md_to_html("`x`")


def test_md_to_html_newline():
    assert "<br>" in _md_to_html("line1\nline2")


def test_build_html_contains_title():
    payload = NotificationPayload(title="My Title")
    html = _build_html(payload)
    assert "My Title" in html


def test_build_html_contains_body():
    payload = NotificationPayload(title="T", body="**important**")
    html = _build_html(payload)
    assert "<strong>important</strong>" in html


def test_build_html_no_body_section_when_empty():
    payload = NotificationPayload(title="T")
    html = _build_html(payload)
    assert "<p" not in html


def test_build_html_contains_image():
    payload = NotificationPayload(
        title="T",
        image=Image(url="https://example.com/img.png", alt="shot"),
    )
    html = _build_html(payload)
    assert "https://example.com/img.png" in html
    assert 'alt="shot"' in html


def test_build_html_no_image_tag_when_none():
    payload = NotificationPayload(title="T")
    html = _build_html(payload)
    assert "<img" not in html


def test_build_html_action_buttons_present():
    payload = NotificationPayload(
        title="T",
        actions=[
            Action(id="ok", label="Confirm", style=ActionStyle.PRIMARY),
            Action(id="no", label="Cancel", style=ActionStyle.DEFAULT),
        ],
    )
    html = _build_html(payload)
    assert "Confirm" in html
    assert "Cancel" in html


def test_build_html_action_with_jump_url():
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
    html = _build_html(payload)
    assert "https://example.com" in html


@pytest.mark.parametrize(
    "event_type, expected_color",
    [
        (EventType.COMPLETION, "#22c55e"),
        (EventType.ERROR, "#ef4444"),
        (EventType.WARNING, "#eab308"),
    ],
)
def test_build_html_event_color(event_type, expected_color):
    payload = NotificationPayload(title="T", event_type=event_type)
    assert expected_color in _build_html(payload)


def test_build_message_headers():
    payload = NotificationPayload(title="Hello Email")
    msg = _build_message(payload, CFG)
    assert msg["Subject"] == "Hello Email"
    assert "user@example.com" in msg["From"]
    assert "dest@example.com" in msg["To"]


def test_build_message_is_html():
    payload = NotificationPayload(title="T", body="body text")
    msg = _build_message(payload, CFG)
    payloads = msg.get_payload()
    assert isinstance(payloads, list)
    content_types = [p.get_content_type() for p in payloads]
    assert "text/html" in content_types


async def test_send_success():
    with patch("aiosmtplib.send", new=AsyncMock(return_value=(None, ""))) as mock_send:
        adapter = EmailAdapter(CFG)
        result = await adapter.send(NotificationPayload(title="Hello"))

    assert result.success is True
    assert result.adapter == "email"
    mock_send.assert_awaited_once()


async def test_send_calls_correct_smtp_params():
    with patch("aiosmtplib.send", new=AsyncMock(return_value=(None, ""))) as mock_send:
        adapter = EmailAdapter(CFG)
        await adapter.send(NotificationPayload(title="Hello"))

    _, kwargs = mock_send.call_args
    assert kwargs["hostname"] == "smtp.example.com"
    assert kwargs["port"] == 587
    assert kwargs["username"] == "user@example.com"
    assert kwargs["start_tls"] is True
    assert kwargs["use_tls"] is False


async def test_send_smtp_error():
    with patch(
        "aiosmtplib.send",
        new=AsyncMock(side_effect=aiosmtplib.SMTPAuthenticationError(535, "bad credentials")),
    ):
        adapter = EmailAdapter(CFG)
        result = await adapter.send(NotificationPayload(title="Hello"))

    assert result.success is False
    assert result.message != ""


async def test_send_unexpected_error():
    with patch(
        "aiosmtplib.send",
        new=AsyncMock(side_effect=OSError("connection refused")),
    ):
        adapter = EmailAdapter(CFG)
        result = await adapter.send(NotificationPayload(title="Hello"))

    assert result.success is False
    assert "connection refused" in result.message


async def test_health_check_fully_configured():
    adapter = EmailAdapter(CFG)
    assert await adapter.health_check() is True


async def test_health_check_missing_host():
    cfg = EmailConfig(
        smtp_host="",
        smtp_port=587,
        username="u",
        password="p",
        **{"from": "f"},
        to=["t"],
    )
    adapter = EmailAdapter(cfg)
    assert await adapter.health_check() is False


async def test_health_check_missing_password():
    cfg = EmailConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        username="u",
        password="",
        **{"from": "f"},
        to=["t"],
    )
    adapter = EmailAdapter(cfg)
    assert await adapter.health_check() is False
