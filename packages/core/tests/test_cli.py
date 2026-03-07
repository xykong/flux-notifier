import json
from unittest.mock import AsyncMock, patch

import pytest
from click.testing import CliRunner

from flux_notifier.cli import cli
from flux_notifier.schema import DeliveryResult


@pytest.fixture
def runner():
    return CliRunner()


def test_version(runner: CliRunner):
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "flux-notifier" in result.output


def test_send_help(runner: CliRunner):
    result = runner.invoke(cli, ["send", "--help"])
    assert result.exit_code == 0
    assert "--title" in result.output


def test_send_requires_title(runner: CliRunner):
    result = runner.invoke(cli, ["send"])
    assert result.exit_code != 0


def test_send_minimal(runner: CliRunner, tmp_path):
    delivery = DeliveryResult(notification_id="test-id", delivered=[], failed=[])

    with patch("flux_notifier.router.dispatch", new=AsyncMock(return_value=delivery)):
        result = runner.invoke(
            cli,
            ["send", "--title", "Hello"],
            env={"FLUX_NOTIFIER_CONFIG": str(tmp_path / "nonexistent.toml")},
        )

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["notification_id"] == "test-id"


def test_send_with_json_payload(runner: CliRunner, tmp_path):
    payload_json = json.dumps({"version": "1", "title": "Test", "event_type": "info"})
    delivery = DeliveryResult(notification_id="x", delivered=[], failed=[])

    with patch("flux_notifier.router.dispatch", new=AsyncMock(return_value=delivery)):
        result = runner.invoke(
            cli,
            ["send", "--json", payload_json],
            env={"FLUX_NOTIFIER_CONFIG": str(tmp_path / "nonexistent.toml")},
        )

    assert result.exit_code == 0


def test_send_invalid_json(runner: CliRunner, tmp_path):
    result = runner.invoke(
        cli,
        ["send", "--json", "{bad json}"],
        env={"FLUX_NOTIFIER_CONFIG": str(tmp_path / "nonexistent.toml")},
    )
    assert result.exit_code != 0


def test_config_path(runner: CliRunner):
    result = runner.invoke(cli, ["config", "path"])
    assert result.exit_code == 0
    assert "flux-notifier" in result.output


def test_config_list_empty(runner: CliRunner, tmp_path):
    result = runner.invoke(
        cli,
        ["config", "list"],
        env={"FLUX_NOTIFIER_CONFIG": str(tmp_path / "nonexistent.toml")},
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "targets" in data


def test_status(runner: CliRunner, tmp_path):
    result = runner.invoke(
        cli,
        ["status"],
        env={"FLUX_NOTIFIER_CONFIG": str(tmp_path / "nonexistent.toml")},
    )
    assert result.exit_code == 0
    assert "macOS App" in result.output
