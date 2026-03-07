# Windows Adapter

在 Windows 上通过 PowerShell + `System.Windows.Forms.NotifyIcon` 发送系统气泡通知。

无需额外配置，Windows 平台自动可用。

---

## 配置

```toml
[targets]
enabled = ["windows"]

[windows]
app_id = "FluxNotifier"    # 可选，通知来源标识
```

---

## 前置要求

- Windows 10 / 11
- PowerShell 5.1+（系统自带）

---

## 能力

| 功能 | 支持情况 |
|---|---|
| 标题 + 正文 | ✅ |
| 图片 | ❌ |
| 按钮 | ❌（Windows Toast 按钮需 WinRT，暂不支持） |
| 用户响应回传 | ❌ |

Windows Adapter 为单向通知，不支持用户响应回传。
