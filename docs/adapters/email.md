# 邮件 Adapter

通过 SMTP 发送 HTML 格式的邮件通知。适合非实时场景，如日报、批量任务完成通知等。

---

## 配置

```toml
[targets]
enabled = ["email"]

[email]
smtp_host = "smtp.gmail.com"
smtp_port = 587
username = "your@gmail.com"
password = "YOUR_APP_PASSWORD"
from = "Flux Notifier <your@gmail.com>"
to = ["me@example.com", "team@example.com"]
use_tls = true
```

### 常用 SMTP 配置

| 服务商 | `smtp_host` | `smtp_port` | 备注 |
|--------|-------------|-------------|------|
| Gmail | `smtp.gmail.com` | `587` | 需要开启应用专用密码 |
| Outlook/Hotmail | `smtp.office365.com` | `587` | |
| QQ 邮箱 | `smtp.qq.com` | `587` | 需要开启 SMTP 并获取授权码 |
| 网易邮箱 | `smtp.163.com` | `994` | `use_tls = true` |
| 企业邮箱 | 联系管理员 | | |

---

## 渲染效果

邮件正文使用 HTML 模板，支持：

- `title` → 邮件主题 + 邮件顶部大标题
- `body` → Markdown 转 HTML，支持代码高亮
- `image` → 内嵌图片
- `actions` → HTML 链接按钮（点击跳转，无法回传响应）

**注意** ：邮件 Adapter 不支持用户响应回传，`notify send` 在邮件发出后立即返回已发送状态，不等待用户操作。

---

## Gmail 应用专用密码设置

1. 访问 Google 账户 → 安全 → 两步验证（需先开启）
2. 搜索"应用专用密码"→ 生成
3. 将生成的 16 位密码填入 `password` 字段
