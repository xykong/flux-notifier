import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from flux_notifier.adapters.macos import MacOSAdapter
from flux_notifier.schema import NotificationPayload


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS only")
async def test_send_when_socket_missing(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("flux_notifier.adapters.macos.SOCKET_PATH", tmp_path / "missing.sock")
    adapter = MacOSAdapter()
    payload = NotificationPayload(title="Test")
    result = await adapter.send(payload)
    assert result.success is False
    assert result.adapter == "macos"


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS only")
async def test_health_check_no_socket(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("flux_notifier.adapters.macos.SOCKET_PATH", tmp_path / "missing.sock")
    adapter = MacOSAdapter()
    assert await adapter.health_check() is False


async def test_send_non_darwin(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    adapter = MacOSAdapter()
    payload = NotificationPayload(title="Test")
    result = await adapter.send(payload)
    assert result.success is False
    assert "darwin" in result.message


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS only")
async def test_send_successful_via_mock_socket(tmp_path: Path, monkeypatch):
    socket_path = tmp_path / "macos.sock"

    ack = json.dumps({"ok": True}).encode()
    mock_reader = AsyncMock()
    mock_reader.read = AsyncMock(return_value=ack)
    mock_writer = AsyncMock()
    mock_writer.drain = AsyncMock()
    mock_writer.write = lambda data: None
    mock_writer.close = lambda: None
    mock_writer.wait_closed = AsyncMock()

    monkeypatch.setattr("flux_notifier.adapters.macos.SOCKET_PATH", socket_path)
    socket_path.touch()

    with patch(
        "asyncio.open_unix_connection",
        new=AsyncMock(return_value=(mock_reader, mock_writer)),
    ):
        adapter = MacOSAdapter()
        result = await adapter.send(NotificationPayload(title="Hello"))

    assert result.success is True
    assert result.adapter == "macos"
