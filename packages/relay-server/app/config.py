from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_key: str = ""
    apns_key_id: str = ""
    apns_team_id: str = ""
    apns_bundle_id: str = "dev.flux-notifier.app"
    apns_private_key: str = ""
    apns_production: bool = False
    fcm_server_key: str = ""

    model_config = {"env_prefix": "RELAY_", "env_file": ".env"}


settings = Settings()
