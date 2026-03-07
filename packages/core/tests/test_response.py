import asyncio
import json
from pathlib import Path

import pytest

from flux_notifier.schema import UserResponse


async def test_wait_for_response_success(tmp_path: Path, monkeypatch):
    from flux_notifier import response as resp_module

    monkeypatch.setattr(resp_module, "get_responses_dir", lambda: tmp_path)

    notification_id = "test-uuid-1234"

    async def _write_after_delay():
        await asyncio.sleep(0.1)
        r = UserResponse(notification_id=notification_id, action_id="ok", source_terminal="macos")
        (tmp_path / f"{notification_id}.json").write_text(r.model_dump_json())

    writer_task = asyncio.create_task(_write_after_delay())
    result = await resp_module.wait_for_response(notification_id, timeout=2.0)
    await writer_task

    assert result.action_id == "ok"
    assert result.timeout is False
    assert not (tmp_path / f"{notification_id}.json").exists()


async def test_wait_for_response_timeout(tmp_path: Path, monkeypatch):
    from flux_notifier import response as resp_module

    monkeypatch.setattr(resp_module, "get_responses_dir", lambda: tmp_path)

    result = await resp_module.wait_for_response("never-written", timeout=0.3)
    assert result.timeout is True
    assert result.action_id is None


def test_write_response(tmp_path: Path, monkeypatch):
    from flux_notifier import response as resp_module

    monkeypatch.setattr(resp_module, "get_responses_dir", lambda: tmp_path)

    r = UserResponse(notification_id="abc", action_id="deploy")
    resp_module.write_response(r)

    path = tmp_path / "abc.json"
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["action_id"] == "deploy"
