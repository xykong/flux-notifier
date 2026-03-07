from __future__ import annotations

import asyncio
import logging
import shutil
import sys

from flux_notifier.adapters.base import AdapterBase, SendResult
from flux_notifier.config import LinuxConfig
from flux_notifier.schema import NotificationPayload

logger = logging.getLogger(__name__)

_URGENCY = {
    "low": "low",
    "normal": "normal",
    "high": "critical",
    "urgent": "critical",
}


class LinuxAdapter(AdapterBase):
    name = "linux"

    def __init__(self, config: LinuxConfig | None = None) -> None:
        self._config = config or LinuxConfig()

    async def send(self, payload: NotificationPayload) -> SendResult:
        if sys.platform != "linux":
            return SendResult(
                success=False,
                adapter=self.name,
                message="linux adapter only runs on linux",
            )

        if not shutil.which("notify-send"):
            return SendResult(
                success=False,
                adapter=self.name,
                message="notify-send not found; install libnotify-bin",
            )

        urgency = _URGENCY.get(payload.metadata.priority.value, "normal")
        cmd = ["notify-send", "--urgency", urgency]

        if self._config.icon:
            cmd += ["--icon", self._config.icon]

        cmd.append(payload.title)
        if payload.body:
            cmd.append(payload.body)

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await asyncio.wait_for(proc.communicate(), timeout=10.0)
            if proc.returncode != 0:
                msg = stderr.decode(errors="replace").strip()
                return SendResult(success=False, adapter=self.name, message=msg)
            return SendResult(success=True, adapter=self.name)
        except Exception as exc:
            logger.error("linux adapter send failed: %s", exc)
            return SendResult(success=False, adapter=self.name, message=str(exc))

    async def health_check(self) -> bool:
        return sys.platform == "linux" and shutil.which("notify-send") is not None
