# 飞书 Adapter

Flux Notifier 支持两种飞书集成方式： **自定义机器人 Webhook** （简单）和 **飞书开放平台应用** （完整能力）。

---

## 飞书自定义机器人 (`feishu_webhook`)

### 创建 Webhook

1. 打开飞书群聊 → 群设置 → 机器人 → 添加自定义机器人
2. 复制 Webhook URL
3. 可选：开启签名校验，复制密钥

### 配置

```toml
[targets]
enabled = ["feishu_webhook"]

[feishu_webhook]
webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_TOKEN"
secret = "YOUR_SECRET"    # 可选，开启签名校验时填写
```

### 能力

| 功能 | 支持情况 |
|------|---------|
| 标题 + 正文 | ✅ 消息卡片 header + markdown element |
| Markdown | ✅ 飞书 Markdown 语法 |
| 图片 | ✅ img element |
| 按钮 | ✅ button element（最多 5 个） |
| 跳转链接 | ✅ 按钮 URL 或卡片链接 |
| 用户响应回传 | ✅ 通过按钮回调（需配置回调 URL） |

---

## 飞书开放平台应用 (`feishu_app`)

支持向指定用户或群发送消息，可发送给 Bot 不在群内的用户。

### 创建应用

1. 访问[飞书开放平台](https://open.feishu.cn/)，创建企业自建应用
2. 开通权限：`im:message:send_as_bot`
3. 获取 App ID 和 App Secret
4. 获取接收用户的 open_id（在飞书开发者后台查询）

### 配置

```toml
[targets]
enabled = ["feishu_app"]

[feishu_app]
app_id = "cli_YOUR_APP_ID"
app_secret = "YOUR_APP_SECRET"
receiver_id = "ou_YOUR_USER_OPEN_ID"
receiver_id_type = "open_id"    # "open_id" | "user_id" | "email"
```

### 能力

与 `feishu_webhook` 基本相同，额外支持：

- 发送给指定用户（不局限于群聊）
- 支持更多消息类型（文本、富文本、卡片）
- 可撤回消息

---

## 消息卡片渲染示例

Flux Notifier 的消息在飞书中渲染为交互式消息卡片：

```
┌─────────────────────────────────────┐
│  🔔  代码审查完成                    │  ← title
├─────────────────────────────────────┤
│  **代码审查**已完成，发现 3 个问题。  │  ← body (Markdown)
│                                     │
│  [审查报告截图]                      │  ← image
├─────────────────────────────────────┤
│  [立即部署]  [查看详情]  [取消]      │  ← actions
└─────────────────────────────────────┘
```

---

## 按钮响应回传

飞书按钮点击后，飞书服务器会向配置的回调 URL 发送请求。需要在 relay-server 或自建服务中处理此回调。

**配置回调 URL** （飞书开放平台 → 应用 → 事件与回调）：
```
https://your-relay-server.com/callbacks/feishu
```

relay-server 内置了飞书回调处理，配置好后响应会自动回传给等待中的 `notify send` 命令。
