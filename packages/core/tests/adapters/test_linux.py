from __future__ import annotations

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from flux_notifier.adapters.linux import LinuxAdapter
from flux_notifier.config import LinuxConfig
from flux_notifier.schema import Metadata, NotificationPayload, Priority


async def test_send_non_linux(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    adapter = LinuxAdapter()
    result = await adapter.send(NotificationPayload(title="Hello"))
    assert result.success is False
    assert "linux" in result.message


async def test_send_notify_send_missing(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    with patch("shutil.which", return_value=None):
        adapter = LinuxAdapter()
        result = await adapter.send(NotificationPayload(title="Hello"))
    assert result.success is False
    assert "notify-send" in result.message


async def test_send_success(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.communicate = AsyncMock(return_value=(b"", b""))

    with (
        patch("shutil.which", return_value="/usr/bin/notify-send"),
        patch("asyncio.create_subprocess_exec", new=AsyncMock(return_value=mock_proc)),
    ):
        adapter = LinuxAdapter()
        result = await adapter.send(NotificationPayload(title="Hello", body="World"))

    assert result.success is True
    assert result.adapter == "linux"


async def test_send_process_error(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")

    mock_proc = MagicMock()
    mock_proc.returncode = 1
    mock_proc.communicate = AsyncMock(return_value=(b"", b"dbus error"))

    with (
        patch("shutil.which", return_value="/usr/bin/notify-send"),
        patch("asyncio.create_subprocess_exec", new=AsyncMock(return_value=mock_proc)),
    ):
        adapter = LinuxAdapter()
        result = await adapter.send(NotificationPayload(title="Hello"))

    assert result.success is False
    assert "dbus error" in result.message


async def test_send_passes_urgency_critical_for_urgent(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.communicate = AsyncMock(return_value=(b"", b""))

    captured: list[tuple] = []

    async def mock_exec(*args, **kwargs):
        captured.append(args)
        return mock_proc

    with (
        patch("shutil.which", return_value="/usr/bin/notify-send"),
        patch("asyncio.create_subprocess_exec", new=mock_exec),
    ):
        adapter = LinuxAdapter()
        payload = NotificationPayload(
            title="Urgent",
            metadata=Metadata(priority=Priority.URGENT),
        )
        await adapter.send(payload)

    assert "critical" in captured[0]


async def test_send_uses_icon_when_configured(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.communicate = AsyncMock(return_value=(b"", b""))

    captured: list[tuple] = []

    async def mock_exec(*args, **kwargs):
        captured.append(args)
        return mock_proc

    with (
        patch("shutil.which", return_value="/usr/bin/notify-send"),
        patch("asyncio.create_subprocess_exec", new=mock_exec),
    ):
        adapter = LinuxAdapter(config=LinuxConfig(icon="/usr/share/icons/my.png"))
        await adapter.send(NotificationPayload(title="Test"))

    assert "--icon" in captured[0]
    assert "/usr/share/icons/my.png" in captured[0]


@pytest.mark.skipif(sys.platform != "linux", reason="Linux only")
async def test_health_check_on_linux():
    adapter = LinuxAdapter()
    result = await adapter.health_check()
    assert isinstance(result, bool)


async def test_health_check_non_linux(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    adapter = LinuxAdapter()
    assert await adapter.health_check() is False


async def test_health_check_no_notify_send(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    with patch("shutil.which", return_value=None):
        adapter = LinuxAdapter()
        assert await adapter.health_check() is False
