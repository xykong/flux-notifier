from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from flux_notifier.config import get_responses_dir
from flux_notifier.schema import UserResponse

logger = logging.getLogger(__name__)

_POLL_INTERVAL = 0.2


def response_file_path(notification_id: str) -> Path:
    return get_responses_dir() / f"{notification_id}.json"


async def wait_for_response(
    notification_id: str,
    timeout: float | None = None,
) -> UserResponse:
    path = response_file_path(notification_id)

    async def _poll() -> UserResponse:
        while True:
            if path.exists():
                try:
                    data = json.loads(path.read_text())
                    path.unlink(missing_ok=True)
                    return UserResponse.model_validate(data)
                except (json.JSONDecodeError, ValueError) as exc:
                    logger.warning("invalid response file %s: %s", path, exc)
                    path.unlink(missing_ok=True)
            await asyncio.sleep(_POLL_INTERVAL)

    try:
        if timeout is not None:
            return await asyncio.wait_for(_poll(), timeout=timeout)
        return await _poll()
    except TimeoutError:
        return UserResponse(
            notification_id=notification_id,
            action_id=None,
            timeout=True,
        )


def write_response(response: UserResponse) -> None:
    path = response_file_path(response.notification_id)
    path.write_text(response.model_dump_json())


def cleanup_response_file(notification_id: str) -> None:
    response_file_path(notification_id).unlink(missing_ok=True)
