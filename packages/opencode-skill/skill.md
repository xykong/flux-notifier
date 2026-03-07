# Flux Notifier Skill

## Purpose

Use this skill whenever you need to notify the user, ask a question, or wait for a decision
during an autonomous task. The `notify send` command blocks until the user responds from any
configured terminal (macOS, Feishu, email, WeChat, mobile push, etc.) and returns their
choice on stdout.

## When to Use

| Situation | Event Type | Wait? |
|---|---|---|
| Task completed, no decision needed | `completion` | No (`--no-wait`) |
| Need user to choose next action | `choice` | Yes (default) |
| Background step finished | `step` | No (`--no-wait`) |
| Need user to provide text/input | `input_required` | Yes |
| Informational update | `info` | No (`--no-wait`) |
| Non-critical warning | `warning` | No (`--no-wait`) |
| Critical error requiring attention | `error` | Yes |

## Command Reference

```bash
notify send [OPTIONS]

Options:
  --title TEXT         Notification title (required)
  --body TEXT          Notification body (Markdown supported)
  --json TEXT          Full JSON payload (overrides other flags)
  --file PATH          Read payload from JSON file
  --actions TEXT       JSON array of action objects
  --targets TEXT       Comma-separated adapter names (default: all enabled)
  --timeout FLOAT      Seconds to wait for response (default: no timeout)
  --no-wait            Send and return immediately without waiting
```

## Usage Patterns

### 1. Simple completion (non-blocking)

```bash
notify send \
  --title "Code review complete" \
  --body "Found 3 issues in **auth.py**. Ready to fix." \
  --no-wait
```

### 2. Decision required (blocking)

```python
import subprocess, json

payload = {
    "version": "1",
    "event_type": "choice",
    "title": "Deploy to production?",
    "body": "All tests pass. **3 files changed.** Ready to deploy.",
    "actions": [
        {"id": "deploy", "label": "Deploy", "style": "primary"},
        {"id": "review", "label": "Review first", "style": "default"},
        {"id": "abort",  "label": "Abort",  "style": "destructive"}
    ],
    "metadata": {"source_app": "opencode", "priority": "high"}
}

result = subprocess.run(
    ["notify", "send", "--json", json.dumps(payload), "--timeout", "300"],
    capture_output=True, text=True
)
response = json.loads(result.stdout)
action_id = response.get("action_id")   # "deploy" | "review" | "abort" | None (timeout)
```

### 3. Jump to context

```python
payload = {
    "version": "1",
    "event_type": "error",
    "title": "Build failed",
    "body": "TypeError in `src/auth.ts:42`",
    "actions": [
        {
            "id": "open",
            "label": "Open in VS Code",
            "style": "primary",
            "jump_to": {"type": "vscode", "target": "vscode://file/path/to/src/auth.ts:42"}
        }
    ]
}
```

### 4. Step summary with screenshot

```python
payload = {
    "version": "1",
    "event_type": "step",
    "title": "Database migration complete",
    "body": "Applied **12 migrations** in 3.2s.",
    "image": {"url": "https://...screenshot.png", "alt": "migration log"},
    "metadata": {"source_app": "opencode", "priority": "low"}
}
subprocess.run(["notify", "send", "--json", json.dumps(payload), "--no-wait"])
```

## Response Format

```json
{
  "notification_id": "uuid",
  "action_id": "deploy",
  "timestamp": "2026-03-08T10:00:00Z",
  "source_terminal": "macos",
  "timeout": false
}
```

On timeout: `{"action_id": null, "timeout": true, ...}`

## Decision Rules

- **choice / input_required / error**: Always block and wait for user response.
- **completion / step / info / warning**: Use `--no-wait` to avoid blocking the AI workflow.
- **urgent priority**: Set `"priority": "urgent"` in metadata for critical alerts.
- **Always set `--timeout`** for blocking calls (300s recommended) to prevent permanent blocking.
- **Check `timeout: true`** in response and handle gracefully (retry or abort).

## JSON Schema Reference

```json
{
  "version": "1",
  "event_type": "completion | choice | step | input_required | info | warning | error",
  "title": "string (required, max 128 chars)",
  "body": "string (optional, Markdown, max 4096 chars)",
  "image": {"url": "string", "alt": "string"},
  "actions": [
    {
      "id": "string (unique, max 64 chars)",
      "label": "string (max 64 chars)",
      "style": "primary | destructive | default",
      "jump_to": {"type": "url | vscode | pycharm | terminal", "target": "string"}
    }
  ],
  "metadata": {
    "source_app": "opencode",
    "priority": "low | normal | high | urgent",
    "ttl": 300
  }
}
```
