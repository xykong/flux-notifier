# 消息 Schema 规范

Flux Notifier 使用统一的 JSON 消息格式，所有终端 Adapter 基于此格式自行渲染。

---

## 完整 Schema

```json
{
  "version": "1",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-03-07T13:00:00Z",
  "event_type": "completion",
  "title": "代码审查完成",
  "body": "**代码审查**已完成，发现 3 个潜在问题。\n\n请查看详情并决定是否继续部署。",
  "image": {
    "url": "https://example.com/screenshot.png",
    "alt": "代码审查报告截图",
    "width": 800,
    "height": 400
  },
  "actions": [
    {
      "id": "deploy",
      "label": "立即部署",
      "style": "primary",
      "jump_to": {
        "type": "vscode",
        "target": "vscode://file/path/to/project"
      }
    },
    {
      "id": "review",
      "label": "查看详情",
      "style": "default",
      "jump_to": {
        "type": "url",
        "target": "https://github.com/org/repo/pull/123"
      }
    },
    {
      "id": "cancel",
      "label": "取消",
      "style": "destructive"
    }
  ],
  "metadata": {
    "source_app": "opencode",
    "session_id": "ses_abc123",
    "priority": "high",
    "ttl": 3600
  }
}
```

---

## 字段说明

### 顶层字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `version` | `string` | ✅ | Schema 版本，当前为 `"1"` |
| `id` | `string` | 否 | 通知唯一 ID，不填时自动生成 UUID |
| `timestamp` | `string` | 否 | ISO 8601 时间戳，不填时自动生成 |
| `event_type` | `string` | ✅ | 事件类型，见下表 |
| `title` | `string` | ✅ | 通知标题，纯文本，最长 128 字符 |
| `body` | `string` | 否 | 通知正文，支持 Markdown，最长 4096 字符 |
| `image` | `object` | 否 | 附图，见 Image 对象 |
| `actions` | `array` | 否 | 操作按钮列表，最多 5 个 |
| `metadata` | `object` | 否 | 元数据，见 Metadata 对象 |

### `event_type` 枚举值

| 值 | 含义 | 典型场景 |
|----|------|---------|
| `completion` | 任务完成 | 模型训练结束、代码生成完毕 |
| `choice` | 需要用户选择 | 有多个方案供选择 |
| `step` | 步骤摘要 | 某个阶段执行完毕的小结 |
| `input_required` | 需要用户输入 | 缺少必要信息，AI 无法继续 |
| `info` | 纯信息通知 | 进度更新、状态变更 |
| `warning` | 警告 | 发现潜在问题，需关注 |
| `error` | 错误 | 执行出错，需要处理 |

### Image 对象

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `url` | `string` | ✅ | 图片 URL 或 Base64 Data URL |
| `alt` | `string` | 否 | 无障碍替代文字 |
| `width` | `integer` | 否 | 建议宽度（px） |
| `height` | `integer` | 否 | 建议高度（px） |

### Action 对象

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | `string` | ✅ | 按钮唯一标识符，用户点击后回传此值 |
| `label` | `string` | ✅ | 按钮显示文字 |
| `style` | `string` | 否 | `primary`（主要）\| `destructive`（危险）\| `default`（默认） |
| `jump_to` | `object` | 否 | 点击后跳转目标，见 JumpTo 对象 |

### JumpTo 对象

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | `string` | ✅ | 跳转类型，见下表 |
| `target` | `string` | ✅ | 跳转目标 URL 或路径 |

`type` 枚举值：

| 值 | 说明 | 示例 |
|----|------|------|
| `url` | 普通 URL | `https://github.com/...` |
| `vscode` | VS Code URL Scheme | `vscode://file/path/to/file:42` |
| `pycharm` | PyCharm URL Scheme | `pycharm://open?file=/path/to/file&line=42` |
| `terminal` | 终端命令（在新终端执行） | `cd /path/to/project && git log` |

### Metadata 对象

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `source_app` | `string` | 否 | 发送方应用名称，如 `opencode`、`claude` |
| `session_id` | `string` | 否 | 关联的会话 ID |
| `priority` | `string` | 否 | `low` \| `normal`（默认）\| `high` \| `urgent` |
| `ttl` | `integer` | 否 | 通知有效期（秒），超时后自动消失 |
| `tags` | `array<string>` | 否 | 自定义标签，用于过滤 |

---

## 用户响应格式

当用户点击按钮后，`notify send` 命令输出以下 JSON 到 stdout：

```json
{
  "notification_id": "550e8400-e29b-41d4-a716-446655440000",
  "action_id": "deploy",
  "timestamp": "2026-03-07T13:01:23Z",
  "source_terminal": "macos"
}
```

超时未响应时：

```json
{
  "notification_id": "550e8400-e29b-41d4-a716-446655440000",
  "action_id": null,
  "timeout": true,
  "timestamp": "2026-03-07T13:10:00Z"
}
```

无 actions 时（纯通知），`notify send` 发送后立即返回：

```json
{
  "notification_id": "550e8400-e29b-41d4-a716-446655440000",
  "delivered": ["macos", "feishu_webhook"],
  "failed": [],
  "timestamp": "2026-03-07T13:00:01Z"
}
```

---

## 各终端渲染说明

### macOS

- `title` → 系统通知标题 + 悬浮窗大标题
- `body` → 悬浮窗正文（支持 Markdown 渲染）
- `image` → 悬浮窗内嵌图片
- `actions` → 悬浮窗按钮（支持全部样式和跳转）
- 系统通知栏仅显示 `title` + `body` 前 100 字符

### 飞书 Webhook（消息卡片）

- `title` → 卡片 header
- `body` → 卡片 markdown element
- `image` → 卡片 img element
- `actions` → 卡片 button element（`jump_to.url` 映射到按钮链接）
- `primary` → `primary` 按钮色，`destructive` → `danger` 按钮色

### 邮件

- `title` → 邮件主题
- `body` → HTML 正文（Markdown 转 HTML）
- `image` → 内嵌图片
- `actions` → HTML 链接按钮（无法回传响应）

### 手机 Push

- `title` → 推送标题
- `body` → 推送正文（截断至 256 字符）
- `priority: urgent` → iOS 关键通知（穿透勿扰模式）
- `actions` 最多显示 2 个（系统限制）

---

## 示例文件

完整示例见 [`packages/ai-skill/examples/`](../packages/ai-skill/examples/)。
