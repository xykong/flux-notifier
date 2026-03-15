---
name: flux-notifier
description: >
  AI 事件通知系统，用于在自主任务执行过程中向用户发送通知、询问决策或等待用户输入。
  支持 macOS 系统通知、飞书、邮件、微信、手机推送等多个终端，notify send 命令阻塞等待用户响应后将结果返回 stdout。
  触发场景：(1) 任务完成需要告知用户、(2) 需要用户做选择或提供输入、(3) 发生错误需要用户介入、
  (4) 后台步骤完成需要汇报进度、(5) 任何需要用户注意的事件。
---

# Flux Notifier Skill

## 使用时机

| 场景 | event_type | 是否阻塞 |
|---|---|---|
| 任务完成，无需决策 | `completion` | 否（加 `--no-wait`） |
| 需要用户选择下一步 | `choice` | 是（默认） |
| 后台步骤完成汇报 | `step` | 否（加 `--no-wait`） |
| 需要用户提供文字输入 | `input_required` | 是 |
| 普通信息推送 | `info` | 否（加 `--no-wait`） |
| 非关键警告 | `warning` | 否（加 `--no-wait`） |
| 需要用户介入的严重错误 | `error` | 是 |

## 调用方式

安装后直接调用（推荐）：

```bash
# 安装
uv tool install flux-notifier   # 或: pipx install flux-notifier / pip install flux-notifier

# 调用
notify send [选项]
```

### 常用选项

| 选项 | 说明 |
|---|---|
| `--title TEXT` | 通知标题（必填） |
| `--body TEXT` | 正文，支持 Markdown |
| `--json TEXT` | 完整 JSON payload（与 `--title` 互斥） |
| `--file PATH` | 从 JSON 文件读取 payload |
| `--actions TEXT` | 操作按钮 JSON 数组 |
| `--event-type TEXT` | 事件类型，默认 `info` |
| `--targets TEXT` | 逗号分隔的终端名，不填则推送全部 |
| `--timeout INTEGER` | 等待响应超时秒数（阻塞场景必须设置） |
| `--no-wait` | 有 actions 也立即返回，不等待用户响应 |

## 使用示例

### 1. 简单完成通知（非阻塞）

```bash
notify send \
  --title "代码审查完成" \
  --body "在 **auth.py** 发现 3 个问题，已生成修复方案。" \
  --no-wait
```

### 2. 需要用户决策（阻塞）

```python
import subprocess, json

payload = {
    "version": "1",
    "event_type": "choice",
    "title": "是否部署到生产环境？",
    "body": "所有测试通过，**3 个文件**已修改，准备部署。",
    "actions": [
        {"id": "deploy", "label": "立即部署", "style": "primary"},
        {"id": "review", "label": "先审查",  "style": "default"},
        {"id": "abort",  "label": "中止",    "style": "destructive"}
    ],
    "metadata": {"source_app": "opencode", "priority": "high"}
}

result = subprocess.run(
    ["notify", "send", "--json", json.dumps(payload), "--timeout", "300"],
    capture_output=True, text=True
)
response = json.loads(result.stdout)
action_id = response.get("action_id")  # "deploy" | "review" | "abort" | None（超时）
```

### 3. 带跳转链接的错误通知

```python
payload = {
    "version": "1",
    "event_type": "error",
    "title": "构建失败",
    "body": "`src/auth.ts:42` 发现类型错误",
    "actions": [
        {
            "id": "open",
            "label": "在 VS Code 中打开",
            "style": "primary",
            "jump_to": {"type": "vscode", "target": "vscode://file/path/to/src/auth.ts:42"}
        }
    ]
}

result = subprocess.run(
    ["notify", "send", "--json", json.dumps(payload), "--timeout", "300"],
    capture_output=True, text=True
)
```

### 4. 步骤汇报附带截图（非阻塞）

```python
payload = {
    "version": "1",
    "event_type": "step",
    "title": "数据库迁移完成",
    "body": "已执行 **12 条迁移**，耗时 3.2s。",
    "image": {"url": "https://...screenshot.png", "alt": "迁移日志"},
    "metadata": {"source_app": "opencode", "priority": "low"}
}

subprocess.run(
    ["notify", "send", "--json", json.dumps(payload), "--no-wait"],
    capture_output=True
)
```

## 响应格式

有 actions 时（等待用户响应）：

```json
{
  "notification_id": "uuid",
  "action_id": "deploy",
  "timestamp": "2026-03-08T10:00:00Z",
  "source_terminal": "macos",
  "timeout": false
}
```

超时时：`{"action_id": null, "timeout": true, ...}`

无 actions 时（立即返回）：

```json
{"notification_id": "uuid", "delivered": ["macos", "feishu_webhook"], "failed": [], "timestamp": "..."}
```

## 决策规则

- **choice / input_required / error**：必须阻塞等待用户响应，`--timeout 300` 为推荐值。
- **completion / step / info / warning**：使用 `--no-wait`，避免阻断 AI 工作流。
- **紧急事件**：在 metadata 中设置 `"priority": "urgent"`。
- **超时处理**：检查响应中的 `"timeout": true`，并进行重试或中止处理。

## 问题诊断与首次配置

**触发条件**：以下任一情况出现时，**必须**读取 `troubleshooting.md` 并主动引导用户修复，
而不是直接报错或停止工作：

| 触发信号 | 说明 |
|----------|------|
| 输出包含 `WARNING flux_notifier.router: no adapters configured` | 无任何适配器启用 |
| 响应 JSON 中 `delivered: []` | 通知未送达任何终端 |
| 响应 JSON 中 `failed` 列表非空 | 至少一个适配器发送失败 |
| 用户说"没收到通知" / "通知没弹出来" | 用户侧感知到通知丢失 |
| 执行时报 `FileNotFoundError`、`ValidationError` | 配置文件缺失或格式错误 |

**处理规则**：

1. 执行 `troubleshooting.md` 中的"快速诊断命令"，定位问题层级。
2. 根据诊断结果，**主动询问用户**期望使用哪个通知终端（`troubleshooting.md` § 选择适配器）。
3. 按用户选择，**逐步执行**对应适配器的配置流程，途中需要用户提供的信息（Webhook URL、
   App Secret 等）要明确向用户索取，不要假设或跳过。
4. 配置完成后，**必须执行验证命令**，确认 `delivered` 非空后再继续原任务。
5. 若用户环境不在 macOS 上（如服务器、CI），跳过 macOS 选项，优先推荐飞书 Webhook 或邮件。

> 附加文件路径（同目录）：`troubleshooting.md`

## JSON Schema 快速参考

```json
{
  "version": "1",
  "event_type": "completion | choice | step | input_required | info | warning | error",
  "title": "string（必填，最长 128 字符）",
  "body": "string（可选，支持 Markdown，最长 4096 字符）",
  "image": {"url": "string", "alt": "string"},
  "actions": [
    {
      "id": "string（唯一，最长 64 字符）",
      "label": "string（最长 64 字符）",
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
