# Flux Notifier

> AI 事件通知系统 —— 让 AI 程序在需要用户关注时，主动推送到你的所有设备。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey.svg)]()

---

## 是什么

当 AI 程序（如 OpenCode、Claude、AutoGPT 等）在运行时需要用户参与——等待选择、步骤完成、需要输入——它们现在可以通过一行命令，同时通知到你配置的所有终端。

```bash
notify send --title "需要你的决策" \
            --body "AI 已完成代码审查，请选择是否继续部署" \
            --actions '[{"id":"deploy","label":"部署","style":"primary"},{"id":"cancel","label":"取消"}]'

# stdout 阻塞等待，直到用户在任意终端做出选择
# → {"action_id": "deploy", "timestamp": "2026-03-07T13:00:00Z"}
```

## 支持的终端

| 终端 | 能力 | 状态 |
|------|------|------|
| **macOS 原生** | 系统通知 + 完整自定义悬浮窗（按钮/图片/跳转） | ✅ 已发布 |
| **飞书机器人** | 消息卡片（按钮/图片/链接） | ✅ 已发布 |
| **飞书应用** | 企业应用消息 | ✅ 已发布 |
| **邮件** | HTML 富文本邮件 | ✅ 已发布 |
| **企业微信** | 应用消息 | ✅ 已发布 |
| **手机 Push** | APNs / FCM 推送 | ✅ 已发布 |
| **Windows** | Toast 通知 | ✅ 已发布 |
| **Linux** | libnotify / D-Bus | ✅ 已发布 |
| **手表** | 通过手机 Push 透传 | 📋 规划中 |

## 架构

```
AI 程序
  │  notify send --json '{...}'
  ▼
flux-notifier CLI (Python)
  │  解析统一消息格式 (JSON Schema)
  ▼
并发路由引擎
  ├──► macOS App (Unix Socket) → 系统通知 + 自定义悬浮窗
  ├──► 飞书 Webhook → 消息卡片
  ├──► 邮件 → SMTP
  ├──► 微信 → 模板消息
  ├──► Push 中继服务 → APNs / FCM → 手机/手表
  ├──► Windows Toast
  └──► Linux notify-send

用户响应（任意终端）
  └──► stdout 返回给 AI 程序
```

## 快速开始

### 安装

```bash
# Python CLI（推荐）
pip install flux-notifier
# 或
uv tool install flux-notifier

# macOS App（可选，用于原生通知）
brew tap xykong/tap
brew install --cask flux-notifier
```

### 配置

```bash
# 交互式配置向导
flux-notifier setup

# 或手动编辑配置文件
cp config/config.example.toml ~/.flux-notifier/config.toml
```

### 发送通知

```bash
# 最简单的通知
notify send --title "任务完成" --body "模型训练已完成"

# 带按钮的交互式通知（会阻塞等待用户选择）
notify send --title "需要确认" \
            --body "是否提交这批代码？" \
            --actions '[{"id":"yes","label":"提交"},{"id":"no","label":"取消"}]'

# 从 JSON 文件读取
notify send --file ./notification.json

# 只推送特定终端
notify send --title "Done" --targets macos,feishu_webhook

# 查看响应
result=$(notify send --title "选择" --actions '[{"id":"a","label":"A"},{"id":"b","label":"B"}]')
echo $result  # {"action_id":"a","timestamp":"..."}
```

### 在 OpenCode 中使用

在 OpenCode 的 skill 配置中添加 `flux-notifier-skill/skill.md`，AI 将自动在需要时调用 `notify send`。

## 消息格式

所有通知使用统一的 JSON Schema，各终端自行负责渲染：

```json
{
  "version": "1",
  "event_type": "completion",
  "title": "任务完成",
  "body": "**代码审查**已完成，发现 3 个问题需要处理。",
  "image": { "url": "https://...", "alt": "审查报告截图" },
  "actions": [
    {
      "id": "fix",
      "label": "立即修复",
      "style": "primary",
      "jump_to": { "type": "vscode", "target": "vscode://file/path/to/file" }
    },
    { "id": "ignore", "label": "忽略", "style": "default" }
  ],
  "metadata": {
    "source_app": "opencode",
    "priority": "high"
  }
}
```

完整 Schema 文档见 [docs/schema.md](docs/schema.md)。

## 项目结构

```
flux-notifier/
├── packages/
│   ├── core/              # Python CLI + 路由引擎 + 所有 Adapter
│   ├── macos-app/         # Swift + SwiftUI macOS 原生 App
│   ├── relay-server/      # FastAPI 手机 Push 中继服务
│   └── flux-notifier-skill/    # OpenCode Skill 集成
├── config/
│   └── config.example.toml
└── docs/                  # 完整设计文档
```

详细项目规划见 [docs/project-plan.md](docs/project-plan.md)。

## 文档

- [项目总体规划](docs/project-plan.md)
- [消息 Schema 规范](docs/schema.md)
- [CLI 使用参考](docs/cli-reference.md)
- [Adapter 配置指南](docs/adapters/)
  - [macOS](docs/adapters/macos.md)
  - [飞书](docs/adapters/feishu.md)
  - [邮件](docs/adapters/email.md)
  - [微信](docs/adapters/wechat.md)
  - [手机 Push](docs/adapters/push.md)
- [OpenCode 集成](docs/opencode-integration.md)
- [开发指南](docs/development.md)

## 设计原则

- **极小资源占用** ：macOS App 空闲时 < 5MB 内存，0% CPU
- **统一接口，差异渲染** ：一个 JSON 格式，各终端自行渲染最优效果
- **阻塞式响应** ：`notify send` 命令阻塞等待用户响应，天然适配 AI 工作流
- **易于 AI 维护** ：Python 主控，模块化 Adapter，清晰的扩展接口

## 参与贡献

欢迎 PR 和 Issue。新增 Adapter 请参考 [docs/development.md](docs/development.md)。

## License

MIT
