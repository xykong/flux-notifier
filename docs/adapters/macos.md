# macOS Adapter

macOS Adapter 将通知发送到本地运行的 macOS App，展示系统通知和自定义悬浮窗。

---

## 安装

### 安装 macOS App

```bash
# 通过 Homebrew Cask 安装
brew install --cask flux-notifier

# 或手动下载 DMG
# https://github.com/xykong/flux-notifier/releases
```

App 安装后会以 MenuBar 图标形式常驻，无 Dock 图标，资源占用极低（空闲时 < 5MB 内存）。

### 设置开机自启

点击 MenuBar 图标 → **Preferences** → 勾选 **Launch at Login** 。

---

## 配置

macOS Adapter 无需额外凭证配置，在 `config.toml` 中添加：

```toml
[targets]
enabled = ["macos"]

[macos]
window_position = "top-right"    # 悬浮窗位置
auto_dismiss = 30                # 自动关闭时间（秒），0 表示不自动关闭
```

### `window_position` 可选值

| 值 | 位置 |
|----|------|
| `top-right` | 右上角（默认） |
| `top-left` | 左上角 |
| `bottom-right` | 右下角 |
| `bottom-left` | 左下角 |

---

## 能力

| 功能 | 支持情况 |
|------|---------|
| 系统通知栏 | ✅ `UNUserNotificationCenter` |
| 自定义悬浮窗 | ✅ `NSPanel` + SwiftUI，始终置顶 |
| Markdown 渲染 | ✅ `AttributedString` |
| 图片显示 | ✅ URL 和 Base64 |
| 按钮交互 | ✅ primary / destructive / default 样式 |
| 用户响应回传 | ✅ 写入临时文件 |
| IDE 跳转 | ✅ `vscode://`、`pycharm://` 等 URL Scheme |
| 开机自启 | ✅ `SMAppService` |

---

## 工作机制

```
Python core (notify send)
  │
  └── Unix Domain Socket (~/.flux-notifier/macos.sock)
        │
        └── macOS App (FluxNotifier)
              ├── UNUserNotificationCenter → 系统通知栏
              └── NSPanel (SwiftUI) → 自定义悬浮窗
                    └── 用户点击按钮 → 写入 ~/.flux-notifier/responses/<id>
```

Python core 通过 Unix Socket 发送 JSON，macOS App 同时：
1. 触发一条系统通知（出现在通知中心）
2. 弹出自定义悬浮窗（完整 UI，含按钮和图片）

两者不冲突，系统通知作为提醒，悬浮窗作为交互界面。

---

## 故障排除

**App 未运行时通知不显示**

```bash
# 检查 App 是否运行
flux-notifier status

# 手动启动
flux-notifier start
# 或直接打开
open /Applications/FluxNotifier.app
```

**权限问题（通知权限未授予）**

系统偏好设置 → 通知 → FluxNotifier → 允许通知。

**Socket 连接失败**

```bash
# 重启 App
flux-notifier stop && flux-notifier start
```
