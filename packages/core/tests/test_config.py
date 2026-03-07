from pathlib import Path

from flux_notifier.config import AppConfig, load_config


def test_load_missing_config(tmp_path: Path):
    config = load_config(tmp_path / "nonexistent.toml")
    assert isinstance(config, AppConfig)
    assert config.targets.enabled == []


def test_load_minimal_config(tmp_path: Path):
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text('[targets]\nenabled = ["macos"]\n')
    config = load_config(cfg_file)
    assert config.targets.enabled == ["macos"]


def test_load_full_config(tmp_path: Path):
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text(
        '[targets]\nenabled = ["macos", "feishu_webhook"]\n\n'
        '[feishu_webhook]\nwebhook_url = "https://open.feishu.cn/hook/xxx"\n'
    )
    config = load_config(cfg_file)
    assert "feishu_webhook" in config.targets.enabled
    assert config.feishu_webhook is not None
    assert config.feishu_webhook.webhook_url == "https://open.feishu.cn/hook/xxx"


def test_macos_defaults():
    config = AppConfig()
    assert config.macos.window_position == "top-right"
    assert config.macos.auto_dismiss == 30
