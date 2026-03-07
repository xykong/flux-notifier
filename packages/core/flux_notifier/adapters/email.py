from __future__ import annotations

import logging
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from flux_notifier.adapters.base import AdapterBase, SendResult
from flux_notifier.config import EmailConfig
from flux_notifier.schema import ActionStyle, NotificationPayload

logger = logging.getLogger(__name__)

_TIMEOUT = 30.0

_EVENT_COLOR = {
    "completion": "#22c55e",
    "choice": "#3b82f6",
    "step": "#a855f7",
    "input_required": "#f97316",
    "info": "#6b7280",
    "warning": "#eab308",
    "error": "#ef4444",
}

_BUTTON_STYLE = {
    ActionStyle.PRIMARY: "background:#3b82f6;color:#fff",
    ActionStyle.DESTRUCTIVE: "background:#ef4444;color:#fff",
    ActionStyle.DEFAULT: "background:#e5e7eb;color:#111827",
}


def _md_to_html(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    text = text.replace("\n", "<br>")
    return text


def _build_html(payload: NotificationPayload) -> str:
    accent = _EVENT_COLOR.get(payload.event_type.value, "#6b7280")

    body_html = ""
    if payload.body:
        body_html = f'<p style="color:#374151;line-height:1.6">{_md_to_html(payload.body)}</p>'

    image_html = ""
    if payload.image:
        image_html = (
            f'<img src="{payload.image.url}" alt="{payload.image.alt or ""}"'
            ' style="max-width:100%;border-radius:6px;margin:12px 0">'
        )

    actions_html = ""
    if payload.actions:
        btns = []
        for action in payload.actions:
            style = _BUTTON_STYLE.get(action.style, _BUTTON_STYLE[ActionStyle.DEFAULT])
            target = ""
            if action.jump_to:
                target = action.jump_to.target
            btns.append(
                f'<a href="{target}" style="{style};padding:8px 18px;border-radius:5px;'
                f'text-decoration:none;font-size:14px;margin-right:8px;display:inline-block">'
                f"{action.label}</a>"
            )
        actions_html = f'<div style="margin-top:16px">{"".join(btns)}</div>'

    return f"""<!DOCTYPE html>
<html>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
             background:#f9fafb;margin:0;padding:24px">
  <div style="max-width:560px;margin:0 auto;background:#fff;border-radius:10px;
              box-shadow:0 1px 4px rgba(0,0,0,.08);overflow:hidden">
    <div style="background:{accent};padding:16px 24px">
      <h2 style="margin:0;color:#fff;font-size:18px">{payload.title}</h2>
    </div>
    <div style="padding:20px 24px">
      {body_html}
      {image_html}
      {actions_html}
    </div>
    <div style="padding:10px 24px;background:#f3f4f6;font-size:12px;color:#9ca3af">
      Sent by Flux Notifier &middot; {payload.event_type.value}
    </div>
  </div>
</body>
</html>"""


def _build_message(payload: NotificationPayload, config: EmailConfig) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = payload.title
    msg["From"] = config.from_
    msg["To"] = ", ".join(config.to)
    msg.attach(MIMEText(_build_html(payload), "html", "utf-8"))
    return msg


class EmailAdapter(AdapterBase):
    name = "email"

    def __init__(self, config: EmailConfig) -> None:
        self._config = config

    async def send(self, payload: NotificationPayload) -> SendResult:
        msg = _build_message(payload, self._config)
        try:
            await aiosmtplib.send(
                msg,
                hostname=self._config.smtp_host,
                port=self._config.smtp_port,
                username=self._config.username,
                password=self._config.password,
                use_tls=False,
                start_tls=self._config.use_tls,
                timeout=_TIMEOUT,
            )
            return SendResult(success=True, adapter=self.name)
        except aiosmtplib.SMTPException as exc:
            logger.error("email send failed: %s", exc)
            return SendResult(success=False, adapter=self.name, message=str(exc))
        except Exception as exc:
            logger.error("email send unexpected error: %s", exc)
            return SendResult(success=False, adapter=self.name, message=str(exc))

    async def health_check(self) -> bool:
        return bool(self._config.smtp_host and self._config.username and self._config.password)
