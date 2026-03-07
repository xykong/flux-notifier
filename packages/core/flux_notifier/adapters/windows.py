from __future__ import annotations

import asyncio
import logging
import sys

from flux_notifier.adapters.base import AdapterBase, SendResult
from flux_notifier.config import WindowsConfig
from flux_notifier.schema import NotificationPayload

logger = logging.getLogger(__name__)

_PS_SCRIPT = """
Add-Type -AssemblyName System.Windows.Forms
$notify = New-Object System.Windows.Forms.NotifyIcon
$notify.Icon = [System.Drawing.SystemIcons]::Information
$notify.BalloonTipTitle = {title!r}
$notify.BalloonTipText = {body!r}
$notify.Visible = $true
$notify.ShowBalloonTip(5000)
Start-Sleep -Milliseconds 200
$notify.Dispose()
"""


class WindowsAdapter(AdapterBase):
    name = "windows"

    def __init__(self, config: WindowsConfig | None = None) -> None:
        self._config = config or WindowsConfig()

    async def send(self, payload: NotificationPayload) -> SendResult:
        if sys.platform != "win32":
            return SendResult(
                success=False,
                adapter=self.name,
                message="windows adapter only runs on win32",
            )

        body = payload.body or ""
        script = _PS_SCRIPT.format(title=payload.title, body=body)

        try:
            proc = await asyncio.create_subprocess_exec(
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await asyncio.wait_for(proc.communicate(), timeout=15.0)
            if proc.returncode != 0:
                msg = stderr.decode(errors="replace").strip()
                return SendResult(success=False, adapter=self.name, message=msg)
            return SendResult(success=True, adapter=self.name)
        except FileNotFoundError:
            return SendResult(
                success=False,
                adapter=self.name,
                message="powershell not found",
            )
        except Exception as exc:
            logger.error("windows adapter send failed: %s", exc)
            return SendResult(success=False, adapter=self.name, message=str(exc))

    async def health_check(self) -> bool:
        return sys.platform == "win32"
