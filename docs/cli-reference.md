# CLI 使用参考

`flux-notifier` 提供两个命令：`notify`（快捷别名）和 `flux-notifier`（完整命令）。

---

## `notify send` — 发送通知

```
notify send [OPTIONS]
```

发送通知并等待用户响应（如有 actions）。有 actions 时阻塞，无 actions 时立即返回。

### 选项

| 选项 | 类型 | 说明 |
|------|------|------|
| `--title TEXT` | string | 通知标题（与 `--json` 二选一） |
| `--body TEXT` | string | 通知正文，支持 Markdown |
| `--event-type TEXT` | string | 事件类型，默认 `info` |
| `--actions TEXT` | JSON string | 操作按钮 JSON 数组 |
| `--image TEXT` | URL 或路径 | 附图 |
| `--priority TEXT` | string | `low` \| `normal` \| `high` \| `urgent` |
| `--json TEXT` | JSON string | 完整消息 JSON（与 `--title` 互斥） |
| `--file PATH` | 文件路径 | 从 JSON 文件读取消息 |
| `--targets TEXT` | 逗号分隔 | 指定推送终端，不填时推送全部已配置终端 |
| `--timeout INTEGER` | 秒 | 等待用户响应的超时时间，默认无超时 |
| `--no-wait` | flag | 有 actions 也不等待响应，立即返回 |

### 示例

```bash
# 最简通知
notify send --title "任务完成" --body "模型训练已完成，准确率 98.5%"

# 带按钮的交互式通知
notify send \
  --title "需要你的决策" \
  --body "代码审查完成，是否继续部署？" \
  --event-type choice \
  --actions '[
    {"id": "deploy", "label": "立即部署", "style": "primary"},
    {"id": "cancel", "label": "取消", "style": "destructive"}
  ]'

# 带跳转的通知
notify send \
  --title "发现 Bug" \
  --body "在 `auth.py:42` 发现空指针异常" \
  --actions '[
    {
      "id": "fix",
      "label": "在 VSCode 中打开",
      "jump_to": {"type": "vscode", "target": "vscode://file/path/auth.py:42"}
    }
  ]'

# 从 JSON 文件读取
notify send --file ./notification.json

# 只推送特定终端
notify send --title "Done" --targets macos,feishu_webhook

# 带超时
notify send --title "选择" --actions '[...]' --timeout 60

# 在 Python 中捕获响应
import subprocess, json

result = subprocess.run(
    ["notify", "send", "--json", json.dumps(payload)],
    capture_output=True, text=True
)
response = json.loads(result.stdout)
action_id = response.get("action_id")  # None 表示超时或无 actions
```

### 返回值（stdout）

有 actions 时（等待用户响应）：
```json
{"notification_id": "xxx", "action_id": "deploy", "timestamp": "...", "source_terminal": "macos"}
```

无 actions 时（立即返回）：
```json
{"notification_id": "xxx", "delivered": ["macos", "feishu_webhook"], "failed": [], "timestamp": "..."}
```

---

## `flux-notifier setup` — 初始化配置

```
flux-notifier setup [--adapter TEXT]
```

交互式配置向导，引导用户配置各终端。

```bash
# 配置所有终端
flux-notifier setup

# 只配置特定终端
flux-notifier setup --adapter feishu_webhook
flux-notifier setup --adapter email
```

---

## `flux-notifier config` — 管理配置

```bash
# 列出当前配置（隐藏敏感信息）
flux-notifier config list

# 测试所有已配置终端的连通性
flux-notifier config test

# 测试特定终端
flux-notifier config test --adapter feishu_webhook

# 查看配置文件路径
flux-notifier config path

# 打开配置文件（使用默认编辑器）
flux-notifier config edit
```

---

## `flux-notifier status` — 查看状态

```bash
# 查看 macOS App 运行状态、各 Adapter 状态
flux-notifier status

# 启动 macOS App（如未运行）
flux-notifier start

# 停止 macOS App
flux-notifier stop
```

---

## 环境变量

以下环境变量可覆盖配置文件：

| 变量名 | 说明 |
|--------|------|
| `FLUX_NOTIFIER_CONFIG` | 配置文件路径，默认 `~/.flux-notifier/config.toml` |
| `FLUX_NOTIFIER_TARGETS` | 覆盖启用的终端列表，逗号分隔 |
| `FLUX_NOTIFIER_LOG_LEVEL` | 日志级别：`DEBUG` \| `INFO` \| `WARNING` \| `ERROR` |

---

## 退出码

| 退出码 | 含义 |
|--------|------|
| `0` | 成功（通知已发送，或用户已响应） |
| `1` | 参数错误 |
| `2` | 配置错误（如缺少必要配置） |
| `3` | 所有终端推送失败 |
| `4` | 超时（`--timeout` 设置生效，用户未响应） |
