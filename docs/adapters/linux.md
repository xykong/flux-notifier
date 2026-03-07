# Linux Adapter

在 Linux 上通过 `notify-send`（libnotify）发送系统桌面通知。

无需额外配置，Linux 平台自动可用（需要安装 libnotify）。

---

## 配置

```toml
[targets]
enabled = ["linux"]

[linux]
icon = ""    # 可选：自定义图标路径（如 /usr/share/icons/app.png）
```

---

## 前置要求

```bash
# Ubuntu / Debian
sudo apt install libnotify-bin

# Fedora / RHEL
sudo dnf install libnotify

# Arch
sudo pacman -S libnotify
```

---

## 能力

| 功能 | 支持情况 |
|---|---|
| 标题 + 正文 | ✅ |
| 优先级映射 | ✅ (`urgent` → `critical`，穿透勿扰) |
| 自定义图标 | ✅ |
| 图片 | ❌ |
| 按钮 | ❌ |
| 用户响应回传 | ❌ |

Linux Adapter 为单向通知，不支持用户响应回传。
