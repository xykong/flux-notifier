# AGENTS.md — AI Working Principles for Flux Notifier

This file is the authoritative guide for any AI agent (Claude, OpenCode, Copilot, etc.)
working on this codebase. Read this before touching any file.

---

## Project Summary

Flux Notifier is an AI event notification system. A Python CLI core routes a unified JSON
message to all configured terminals (macOS, Feishu, email, WeChat, mobile push, etc.) in
parallel. The `notify send` command blocks until the user responds from any terminal, then
returns the response on stdout for the calling AI to consume.

Core repo: `packages/core` (Python). macOS client: `packages/macos-app` (Swift/SwiftUI).

---

## Repository Layout

```
flux-notifier/
├── AGENTS.md                  ← you are here
├── README.md
├── config/
│   └── config.example.toml   ← canonical config template
├── docs/
│   ├── project-plan.md       ← roadmap and architecture
│   ├── schema.md             ← JSON message schema spec
│   ├── cli-reference.md      ← CLI command reference
│   ├── development.md        ← developer guide (toolchain, conventions)
│   ├── opencode-integration.md
│   └── adapters/             ← per-adapter user docs
├── packages/
│   ├── core/                 ← Python CLI + router + all adapters
│   ├── macos-app/            ← Swift/SwiftUI macOS Menu Bar App
│   ├── relay-server/         ← FastAPI mobile push relay (Phase 3)
│   └── ai-skill/       ← OpenCode skill definition (Phase 3)
└── scripts/
```

---

## Design Principles (Non-Negotiable)

1. **Minimal footprint** — platform apps must be tiny. macOS App target: < 5 MB RAM idle,
   0% CPU idle. Every dependency added to a platform client must be justified.

2. **Unified schema, adapter-specific rendering** — the `NotificationPayload` JSON shape is
   the single source of truth. Adapters translate it; they never invent new message fields.

3. **Blocking response, stdout delivery** — `notify send` blocks until a user responds or
   timeout. The response JSON goes to stdout. No daemons, no polling services, no databases.

4. **Python core owns all logic** — the router, schema validation, config, and adapter
   dispatch all live in `packages/core`. Platform clients (macOS App) are display-only.

5. **AI maintainability first** — prefer explicit, flat, readable code over clever abstractions.
   One file = one adapter. No metaclasses, no dynamic imports at module level, no magic.

---

## Working Rules for AI Agents

### Before You Start

- Read `docs/project-plan.md` to understand current phase and roadmap.
- Check `git log --oneline -10` to see what was done recently.
- Run `pytest tests/ -v` in `packages/core` to confirm the baseline is green.

### Code Changes

- **Never suppress type errors** — no `# type: ignore`, no `cast`, no `Any` unless
  the existing code already uses it and you're matching the pattern exactly.
- **Never commit** unless the user explicitly asks.
- **Never leave tests broken** — if you change a public interface, update all callers
  and tests before finishing.
- **Match existing style exactly** — ruff enforces lint. Run `ruff check .` before
  considering a Python task done.
- **No print statements** — use `logging.getLogger(__name__)` everywhere in `flux_notifier/`.
- **No unnecessary comments** — code must be self-documenting. Remove any comment that
  merely restates what the code does.

### Adding a New Adapter (Mandatory Checklist)

Every new adapter requires all six of these before it is considered done:

1. `packages/core/flux_notifier/adapters/<name>.py` — implements `AdapterBase`
2. `packages/core/flux_notifier/config.py` — add `<Name>Config(BaseModel)` and field on `AppConfig`
3. `packages/core/flux_notifier/router.py` — register in `_build_adapters()` registry dict
4. `packages/core/tests/adapters/test_<name>.py` — full test coverage (see Testing Rules)
5. `config/config.example.toml` — add documented config section
6. `docs/adapters/<name>.md` — user-facing setup and usage doc

Missing any item = incomplete work.

### Testing Rules

- All tests live in `packages/core/tests/`.
- HTTP adapters: mock with `pytest-httpx`. Never make real network calls in tests.
- Socket adapters: mock with `unittest.mock.AsyncMock`. Never require a running service.
- Cover: success path, API error response, HTTP transport error, health_check true/false.
- Target: 100% branch coverage on adapter files.
- Run the full suite (`pytest tests/ -v`) and confirm all pass before marking done.

### Verification Gates (task is NOT done without these)

| Change type | Required evidence |
|---|---|
| Python file edit | `ruff check` clean + `pytest tests/ -v` all pass |
| New adapter | All 6 checklist items done + full suite green |
| Swift file edit | `swift build` exit 0, zero warnings |
| Documentation edit | No broken relative links |

---

## Adapter Implementation Patterns

### Python Adapter Template

```python
from __future__ import annotations

import logging
from typing import Any

from flux_notifier.adapters.base import AdapterBase, SendResult
from flux_notifier.config import MyAdapterConfig
from flux_notifier.schema import NotificationPayload

logger = logging.getLogger(__name__)


class MyAdapter(AdapterBase):
    name = "my_adapter"

    def __init__(self, config: MyAdapterConfig) -> None:
        self._config = config

    async def send(self, payload: NotificationPayload) -> SendResult:
        try:
            ...
            return SendResult(success=True, adapter=self.name)
        except Exception as exc:
            logger.error("my_adapter send failed: %s", exc)
            return SendResult(success=False, adapter=self.name, message=str(exc))

    async def health_check(self) -> bool:
        return bool(self._config.api_key)
```

Key invariants:
- `send()` must NEVER raise — catch all exceptions and return `SendResult(success=False)`.
- `health_check()` must NEVER make network calls — check config completeness only.
- Constructor always takes a single config object (the matching `*Config` Pydantic model).
- Adapters without config (e.g. macOS on non-darwin) call `factory()` with no args;
  adapters with required config are only instantiated when config is non-None.

### Router Registration

In `router.py` → `_build_adapters()`:

```python
from flux_notifier.adapters.my_adapter import MyAdapter

registry: dict[str, AdapterFactory] = {
    "macos": MacOSAdapter,
    "feishu_webhook": FeishuWebhookAdapter,
    "my_adapter": MyAdapter,       # add here
}
```

### Config Pattern

In `config.py`:

```python
class MyAdapterConfig(BaseModel):
    api_key: str
    endpoint: str = "https://default.example.com"

class AppConfig(BaseModel):
    ...
    my_adapter: MyAdapterConfig | None = None   # None = not configured
```

---

## Current Implementation State

### Completed (Phase 1 + Phase 2 + Phase 3)

| Component | Status | Tests |
|---|---|---|
| `packages/core` CLI skeleton | Done | — |
| `adapters/macos.py` | Done | 4 tests |
| `adapters/feishu_webhook.py` | Done | 26 tests |
| `adapters/email.py` | Done | 23 tests |
| `adapters/feishu_app.py` | Done | 10 tests |
| `adapters/wechat_work.py` | Done | 13 tests |
| `adapters/push.py` | Done | 10 tests |
| `adapters/windows.py` | Done | 5 tests |
| `adapters/linux.py` | Done | 8 tests |
| `packages/macos-app` Swift App | Done | builds clean |
| `packages/relay-server` FastAPI | Done | 7 tests |
| `packages/ai-skill/skill.md` | Done | — |
| `.github/workflows/ci.yml` | Done | — |
| `.github/workflows/release.yml` | Done | — |
| **Core total** | | **126/126 pass** |
| **Relay total** | | **7/7 pass** |

### Remaining (Phase 3 — release engineering)

- Homebrew Cask formula — needs Apple Developer account for signing
- Official documentation site
- watchOS companion app

---

## Key File Locations

| Purpose | Path |
|---|---|
| Message schema (Python) | `packages/core/flux_notifier/schema.py` |
| Config models (Python) | `packages/core/flux_notifier/config.py` |
| Router + adapter dispatch | `packages/core/flux_notifier/router.py` |
| Response wait/write | `packages/core/flux_notifier/response.py` |
| CLI entry point | `packages/core/flux_notifier/cli.py` |
| AdapterBase ABC | `packages/core/flux_notifier/adapters/base.py` |
| Config example | `config/config.example.toml` |
| Schema spec (docs) | `docs/schema.md` |
| Roadmap | `docs/project-plan.md` |

---

## Response Flow (How Blocking Works)

1. `notify send` generates a `notification_id` (UUID).
2. Router dispatches to all enabled adapters concurrently (`asyncio.gather`).
3. If payload has `actions` and `--no-wait` is not set, router calls
   `wait_for_response(notification_id, timeout=...)`.
4. `wait_for_response` polls `~/.flux-notifier/responses/<id>.json` with async sleep.
5. Any adapter that supports user interaction writes `UserResponse` JSON to that file.
6. `notify send` reads the file, prints JSON to stdout, and exits.
7. On timeout: prints `{"action_id": null, "timeout": true, ...}` and exits 0.

This design requires no daemon, no database, no network service for the core loop.

---

## IPC Protocol (Python → macOS App)

Socket: `~/.flux-notifier/macos.sock` (Unix Domain Socket)

Frame format:
```
[4 bytes big-endian uint32: body length][body: UTF-8 JSON]
```

Server (Swift) reads the length prefix, reads exactly that many bytes, decodes JSON,
dispatches to UI, then writes back:
```json
{"ok": true}
```
or
```json
{"ok": false, "error": "..."}
```

Python adapter reads the 4-byte length prefix from the ACK the same way.

---

## Git Conventions

- Commit style: `type(scope): description` (Conventional Commits)
- Types: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`
- Scope: `core`, `macos-app`, `relay-server`, `ai-skill`, `docs`, `ci`
- Never commit secrets, tokens, or real config files
- Never commit with `--no-verify`
- One logical change per commit

---

## Humans in the Loop

The human owner acts as a capability provider — they can:
- Set up external accounts (Feishu, Apple Developer, etc.)
- Run commands on devices the AI cannot access
- Provide credentials for testing (never commit them)

The AI is the primary engineer. When blocked on a human action, state clearly what is
needed and why, then stop and wait.
