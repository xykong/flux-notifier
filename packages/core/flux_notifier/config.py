from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


CONFIG_DIR = Path.home() / ".flux-notifier"
CONFIG_FILE = CONFIG_DIR / "config.toml"
SOCKET_PATH = CONFIG_DIR / "macos.sock"
RESPONSES_DIR = CONFIG_DIR / "responses"


class MacOSConfig(BaseModel):
    window_position: str = "top-right"
    auto_dismiss: int = 30


class FeishuWebhookConfig(BaseModel):
    webhook_url: str
    secret: str | None = None


class FeishuAppConfig(BaseModel):
    app_id: str
    app_secret: str
    receiver_id: str
    receiver_id_type: str = "open_id"


class EmailConfig(BaseModel):
    smtp_host: str
    smtp_port: int = 587
    username: str
    password: str
    from_: str = Field(alias="from")
    to: list[str]
    use_tls: bool = True

    model_config = {"populate_by_name": True}


class WechatMpConfig(BaseModel):
    app_id: str
    app_secret: str
    template_id: str
    open_id: str


class WechatWorkConfig(BaseModel):
    corp_id: str
    agent_id: int
    secret: str
    to_user: str = "@all"


class PushConfig(BaseModel):
    relay_url: str
    api_key: str
    device_token: str


class WindowsConfig(BaseModel):
    app_id: str = "FluxNotifier"


class LinuxConfig(BaseModel):
    icon: str = ""


class TargetsConfig(BaseModel):
    enabled: list[str] = Field(default_factory=list)


class AppConfig(BaseModel):
    targets: TargetsConfig = Field(default_factory=TargetsConfig)
    macos: MacOSConfig = Field(default_factory=MacOSConfig)
    feishu_webhook: FeishuWebhookConfig | None = None
    feishu_app: FeishuAppConfig | None = None
    email: EmailConfig | None = None
    wechat_mp: WechatMpConfig | None = None
    wechat_work: WechatWorkConfig | None = None
    push: PushConfig | None = None
    windows: WindowsConfig = Field(default_factory=WindowsConfig)
    linux: LinuxConfig = Field(default_factory=LinuxConfig)


def load_config(path: Path | None = None) -> AppConfig:
    config_path = path or CONFIG_FILE
    if not config_path.exists():
        return AppConfig()
    with open(config_path, "rb") as f:
        raw: dict[str, Any] = tomllib.load(f)
    return AppConfig.model_validate(raw)


def get_config_dir() -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR


def get_responses_dir() -> Path:
    RESPONSES_DIR.mkdir(parents=True, exist_ok=True)
    return RESPONSES_DIR
