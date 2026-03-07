from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

import click

from flux_notifier import __version__
from flux_notifier.config import (
    CONFIG_FILE,
    load_config,
    get_config_dir,
)
from flux_notifier.schema import (
    NotificationPayload,
    EventType,
    Action,
    Image,
    Metadata,
    Priority,
    ActionStyle,
)

LOG_LEVELS = {"debug": logging.DEBUG, "info": logging.INFO, "warning": logging.WARNING, "error": logging.ERROR}


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=LOG_LEVELS.get(level.lower(), logging.WARNING),
        format="%(levelname)s %(name)s: %(message)s",
    )


@click.group()
@click.version_option(__version__, prog_name="flux-notifier")
@click.option("--log-level", default=os.environ.get("FLUX_NOTIFIER_LOG_LEVEL", "warning"), hidden=True)
@click.pass_context
def cli(ctx: click.Context, log_level: str) -> None:
    _setup_logging(log_level)
    ctx.ensure_object(dict)
    config_path_env = os.environ.get("FLUX_NOTIFIER_CONFIG")
    ctx.obj["config_path"] = Path(config_path_env) if config_path_env else None


# ─── notify send ─────────────────────────────────────────────────────────────

@cli.command("send")
@click.option("--title", "-t", default=None, help="Notification title (plain text, max 128 chars).")
@click.option("--body", "-b", default=None, help="Notification body (Markdown, max 4096 chars).")
@click.option(
    "--event-type",
    "-e",
    default="info",
    type=click.Choice([e.value for e in EventType], case_sensitive=False),
    show_default=True,
)
@click.option("--actions", default=None, help="JSON array of action objects.")
@click.option("--image", default=None, help="Image URL or local path.")
@click.option(
    "--priority",
    default="normal",
    type=click.Choice([p.value for p in Priority], case_sensitive=False),
    show_default=True,
)
@click.option("--source-app", default=None, help="Name of the calling application.")
@click.option("--json", "json_payload", default=None, help="Full notification JSON (overrides other flags).")
@click.option("--file", "-f", "payload_file", type=click.Path(exists=True), default=None, help="Read notification JSON from file.")
@click.option("--targets", default=None, help="Comma-separated list of adapters to use.")
@click.option("--timeout", type=float, default=None, help="Seconds to wait for user response.")
@click.option("--no-wait", is_flag=True, default=False, help="Do not wait for user response even if actions are present.")
@click.pass_context
def send_cmd(
    ctx: click.Context,
    title: str | None,
    body: str | None,
    event_type: str,
    actions: str | None,
    image: str | None,
    priority: str,
    source_app: str | None,
    json_payload: str | None,
    payload_file: str | None,
    targets: str | None,
    timeout: float | None,
    no_wait: bool,
) -> None:
    try:
        payload = _build_payload(
            title=title,
            body=body,
            event_type=event_type,
            actions_json=actions,
            image_url=image,
            priority=priority,
            source_app=source_app,
            json_payload=json_payload,
            payload_file=payload_file,
        )
    except (ValueError, click.BadParameter) as exc:
        click.echo(json.dumps({"error": str(exc)}), err=True)
        sys.exit(1)

    config = load_config(ctx.obj.get("config_path"))

    targets_list: list[str] | None = None
    if targets:
        targets_list = [t.strip() for t in targets.split(",") if t.strip()]

    targets_env = os.environ.get("FLUX_NOTIFIER_TARGETS")
    if targets_list is None and targets_env:
        targets_list = [t.strip() for t in targets_env.split(",") if t.strip()]

    from flux_notifier.router import dispatch
    from flux_notifier.schema import DeliveryResult, UserResponse

    result = asyncio.run(
        dispatch(
            payload=payload,
            config=config,
            targets=targets_list,
            timeout=timeout,
            no_wait=no_wait,
        )
    )

    if isinstance(result, UserResponse):
        click.echo(result.model_dump_json())
    else:
        click.echo(result.model_dump_json())


def _build_payload(
    title: str | None,
    body: str | None,
    event_type: str,
    actions_json: str | None,
    image_url: str | None,
    priority: str,
    source_app: str | None,
    json_payload: str | None,
    payload_file: str | None,
) -> NotificationPayload:
    if payload_file:
        raw = Path(payload_file).read_text()
        return NotificationPayload.model_validate_json(raw)

    if json_payload:
        return NotificationPayload.model_validate_json(json_payload)

    if not title:
        raise click.BadParameter("--title is required unless --json or --file is provided")

    parsed_actions: list[Action] = []
    if actions_json:
        raw_actions = json.loads(actions_json)
        if not isinstance(raw_actions, list):
            raise ValueError("--actions must be a JSON array")
        for item in raw_actions:
            parsed_actions.append(Action.model_validate(item))

    parsed_image: Image | None = None
    if image_url:
        parsed_image = Image(url=image_url)

    return NotificationPayload(
        event_type=EventType(event_type),
        title=title,
        body=body,
        actions=parsed_actions,
        image=parsed_image,
        metadata=Metadata(
            source_app=source_app,
            priority=Priority(priority),
        ),
    )


# ─── notify config ────────────────────────────────────────────────────────────

@cli.group("config")
def config_group() -> None:
    pass


@config_group.command("path")
def config_path_cmd() -> None:
    click.echo(str(CONFIG_FILE))


@config_group.command("list")
@click.pass_context
def config_list_cmd(ctx: click.Context) -> None:
    config = load_config(ctx.obj.get("config_path"))
    data = config.model_dump(mode="json")
    _redact_secrets(data)
    click.echo(json.dumps(data, indent=2, ensure_ascii=False))


@config_group.command("test")
@click.option("--adapter", default=None, help="Test a specific adapter.")
@click.pass_context
def config_test_cmd(ctx: click.Context, adapter: str | None) -> None:
    config = load_config(ctx.obj.get("config_path"))

    from flux_notifier.router import _build_adapters

    targets = [adapter] if adapter else None
    adapters = _build_adapters(config, targets)

    if not adapters:
        click.echo("No adapters configured.", err=True)
        sys.exit(2)

    async def _run() -> None:
        for a in adapters:
            ok = await a.health_check()
            status = click.style("✓ ok", fg="green") if ok else click.style("✗ fail", fg="red")
            click.echo(f"  {a.name}: {status}")

    asyncio.run(_run())


@config_group.command("edit")
def config_edit_cmd() -> None:
    get_config_dir()
    if not CONFIG_FILE.exists():
        click.echo(f"Config file not found. Create one at: {CONFIG_FILE}")
        sys.exit(2)
    click.edit(filename=str(CONFIG_FILE))


def _redact_secrets(data: dict) -> None:  # type: ignore[type-arg]
    sensitive = {"password", "secret", "app_secret", "api_key", "webhook_url"}
    for key in list(data.keys()):
        if key in sensitive and data[key]:
            data[key] = "***"
        elif isinstance(data[key], dict):
            _redact_secrets(data[key])


# ─── notify status ────────────────────────────────────────────────────────────

@cli.command("status")
@click.pass_context
def status_cmd(ctx: click.Context) -> None:
    config = load_config(ctx.obj.get("config_path"))

    from flux_notifier.config import SOCKET_PATH

    macos_running = SOCKET_PATH.exists()
    macos_status = click.style("running", fg="green") if macos_running else click.style("not running", fg="yellow")
    click.echo(f"macOS App:  {macos_status}")
    click.echo(f"Config:     {CONFIG_FILE}")
    click.echo(f"Adapters:   {', '.join(config.targets.enabled) or '(none enabled)'}")


# ─── notify start / stop ──────────────────────────────────────────────────────

@cli.command("start")
def start_cmd() -> None:
    import subprocess
    import sys

    if sys.platform != "darwin":
        click.echo("start command is only supported on macOS", err=True)
        sys.exit(1)

    app_path = "/Applications/FluxNotifier.app"
    if not Path(app_path).exists():
        click.echo(f"FluxNotifier.app not found at {app_path}. Install it first.", err=True)
        sys.exit(2)

    subprocess.Popen(["open", app_path])
    click.echo("FluxNotifier.app launched.")


@cli.command("stop")
def stop_cmd() -> None:
    import subprocess
    import sys

    if sys.platform != "darwin":
        click.echo("stop command is only supported on macOS", err=True)
        sys.exit(1)

    subprocess.run(["pkill", "-x", "FluxNotifier"], check=False)
    click.echo("FluxNotifier.app stopped.")
