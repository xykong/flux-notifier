from __future__ import annotations

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from flux_notifier.adapters.windows import WindowsAdapter
from flux_notifier.schema import NotificationPayload


async def test_send_non_win32(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    adapter = WindowsAdapter()
    result = await adapter.send(NotificationPayload(title="Hello"))
    assert result.success is False
    assert "win32" in result.message


@pytest.mark.skipif(sys.platform != "win32", reason="Windows only")
async def test_health_check_on_windows():
    adapter = WindowsAdapter()
    assert await adapter.health_check() is True


async def test_health_check_non_windows(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    adapter = WindowsAdapter()
    assert await adapter.health_check() is False


async def test_send_success_via_mock(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.communicate = AsyncMock(return_value=(b"", b""))

    with patch("asyncio.create_subprocess_exec", new=AsyncMock(return_value=mock_proc)):
        adapter = WindowsAdapter()
        result = await adapter.send(NotificationPayload(title="Test"))

    assert result.success is True
    assert result.adapter == "windows"


async def test_send_powershell_error(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")

    mock_proc = MagicMock()
    mock_proc.returncode = 1
    mock_proc.communicate = AsyncMock(return_value=(b"", b"error message"))

    with patch("asyncio.create_subprocess_exec", new=AsyncMock(return_value=mock_proc)):
        adapter = WindowsAdapter()
        result = await adapter.send(NotificationPayload(title="Test"))

    assert result.success is False
    assert "error message" in result.message


async def test_send_powershell_not_found(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")

    with patch("asyncio.create_subprocess_exec", new=AsyncMock(side_effect=FileNotFoundError)):
        adapter = WindowsAdapter()
        result = await adapter.send(NotificationPayload(title="Test"))

    assert result.success is False
    assert "powershell not found" in result.message
