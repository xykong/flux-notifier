from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from flux_notifier.adapters.base import AdapterBase, SendResult
from flux_notifier.config import AppConfig
from flux_notifier.response import cleanup_response_file, wait_for_response
from flux_notifier.schema import DeliveryResult, NotificationPayload, UserResponse

logger = logging.getLogger(__name__)

AdapterFactory = Callable[..., AdapterBase]


def _build_adapters(config: AppConfig, targets: list[str] | None) -> list[AdapterBase]:
    from flux_notifier.adapters.email import EmailAdapter
    from flux_notifier.adapters.feishu_app import FeishuAppAdapter
    from flux_notifier.adapters.feishu_webhook import FeishuWebhookAdapter
    from flux_notifier.adapters.linux import LinuxAdapter
    from flux_notifier.adapters.macos import MacOSAdapter
    from flux_notifier.adapters.push import PushAdapter
    from flux_notifier.adapters.wechat_work import WechatWorkAdapter
    from flux_notifier.adapters.windows import WindowsAdapter

    registry: dict[str, AdapterFactory] = {
        "macos": MacOSAdapter,
        "feishu_webhook": FeishuWebhookAdapter,
        "feishu_app": FeishuAppAdapter,
        "email": EmailAdapter,
        "wechat_work": WechatWorkAdapter,
        "push": PushAdapter,
        "windows": WindowsAdapter,
        "linux": LinuxAdapter,
    }

    enabled = targets if targets is not None else config.targets.enabled

    adapters: list[AdapterBase] = []
    for name in enabled:
        factory = registry.get(name)
        if factory is None:
            logger.warning("unknown adapter %r, skipping", name)
            continue
        adapter_config: Any = getattr(config, name, None)
        try:
            instance = factory(adapter_config) if adapter_config is not None else factory()
        except Exception as exc:
            logger.warning("failed to initialize adapter %r: %s", name, exc)
            continue
        adapters.append(instance)

    return adapters


async def _send_one(adapter: AdapterBase, payload: NotificationPayload) -> SendResult:
    try:
        return await adapter.send(payload)
    except Exception as exc:
        logger.error("adapter %r raised: %s", adapter.name, exc)
        return SendResult(success=False, adapter=adapter.name, message=str(exc))


async def dispatch(
    payload: NotificationPayload,
    config: AppConfig,
    targets: list[str] | None = None,
    timeout: float | None = None,
    no_wait: bool = False,
) -> DeliveryResult | UserResponse:
    adapters = _build_adapters(config, targets)

    if not adapters:
        logger.warning("no adapters configured or enabled")
        return DeliveryResult(
            notification_id=payload.id,
            delivered=[],
            failed=[],
        )

    tasks = [asyncio.create_task(_send_one(a, payload)) for a in adapters]
    results: list[SendResult] = await asyncio.gather(*tasks)

    delivered = [r.adapter for r in results if r.success]
    failed = [r.adapter for r in results if not r.success]

    for result in results:
        if result.success:
            logger.info("delivered via %s", result.adapter)
        else:
            logger.warning("failed via %s: %s", result.adapter, result.message)

    if payload.has_actions and not no_wait:
        try:
            return await wait_for_response(payload.id, timeout=timeout)
        finally:
            cleanup_response_file(payload.id)

    return DeliveryResult(
        notification_id=payload.id,
        delivered=delivered,
        failed=failed,
    )
