from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import sys

from flux_notifier.adapters.base import AdapterBase, SendResult
from flux_notifier.config import SOCKET_PATH, MacOSConfig
from flux_notifier.schema import NotificationPayload

logger = logging.getLogger(__name__)

_CONNECT_TIMEOUT = 3.0
_SEND_TIMEOUT = 5.0


class MacOSAdapter(AdapterBase):
    name = "macos"

    def __init__(self, config: MacOSConfig | None = None) -> None:
        self._config = config or MacOSConfig()

    async def send(self, payload: NotificationPayload) -> SendResult:
        if sys.platform != "darwin":
            return SendResult(
                success=False,
                adapter=self.name,
                message="macOS adapter only runs on darwin",
            )

        socket_path = str(SOCKET_PATH)
        message = payload.model_dump_json().encode()

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_unix_connection(socket_path),
                timeout=_CONNECT_TIMEOUT,
            )
        except FileNotFoundError:
            return SendResult(
                success=False,
                adapter=self.name,
                message=f"macOS App socket not found at {socket_path}. Is FluxNotifier running?",
            )
        except (OSError, TimeoutError) as exc:
            return SendResult(
                success=False,
                adapter=self.name,
                message=f"failed to connect to macOS App: {exc}",
            )

        try:
            length_prefix = len(message).to_bytes(4, "big")
            writer.write(length_prefix + message)
            await asyncio.wait_for(writer.drain(), timeout=_SEND_TIMEOUT)

            raw = await asyncio.wait_for(reader.read(256), timeout=_SEND_TIMEOUT)
            ack = json.loads(raw.decode())
            success = ack.get("ok", False)
            return SendResult(
                success=success,
                adapter=self.name,
                message=ack.get("error", "") if not success else "",
            )
        except (OSError, TimeoutError, json.JSONDecodeError) as exc:
            return SendResult(
                success=False,
                adapter=self.name,
                message=f"send error: {exc}",
            )
        finally:
            writer.close()
            with contextlib.suppress(OSError):
                await writer.wait_closed()

    async def health_check(self) -> bool:
        if sys.platform != "darwin":
            return False
        return SOCKET_PATH.exists()
