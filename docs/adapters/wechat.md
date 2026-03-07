# 微信 Adapter

支持 **微信公众号模板消息** 和 **企业微信应用消息** 两种方式。

---

## 微信公众号 (`wechat_mp`)

适合已有服务号的用户，向关注了公众号的用户发送模板消息。

### 前置要求

- 拥有微信 **服务号** （订阅号不支持模板消息）
- 创建一个模板消息，获取模板 ID
- 获取用户的 OpenID

### 配置

```toml
[targets]
enabled = ["wechat_mp"]

[wechat_mp]
app_id = "YOUR_MP_APPID"
app_secret = "YOUR_MP_SECRET"
template_id = "YOUR_TEMPLATE_ID"
open_id = "YOUR_USER_OPENID"
```

### 限制

- 不支持 Markdown，正文为纯文本
- 不支持图片
- 不支持按钮交互，只支持跳转链接
- 发送有频率限制（每个用户每天 1 条相同模板消息）

---

## 企业微信应用消息 (`wechat_work`)

适合企业用户，通过企业微信自建应用向员工发送消息，无需关注公众号。

### 创建应用

1. 企业微信管理后台 → 应用管理 → 自建 → 创建应用
2. 获取 AgentId 和 Secret
3. 获取企业 CorpID

### 配置

```toml
[targets]
enabled = ["wechat_work"]

[wechat_work]
corp_id = "YOUR_CORP_ID"
agent_id = 1000001
secret = "YOUR_AGENT_SECRET"
to_user = "YOUR_USERID"     # 指定用户，或 "@all" 发给全员
```

### 能力

| 功能 | 支持情况 |
|------|---------|
| 标题 + 正文 | ✅ 文本卡片消息 |
| 图片 | ✅ 图片消息 |
| 跳转链接 | ✅ 文本卡片 URL |
| 按钮 | 有限（最多跳转 1 个 URL） |
| Markdown | ✅ 企业微信支持 Markdown 消息 |

---

## 渲染说明

由于微信平台限制，消息渲染会有所简化：

- `body` 中的 Markdown 格式化语法（`**bold**` 等）在微信公众号中会显示为纯文本
- 企业微信支持 Markdown 消息类型，会有较好的渲染效果
- 所有 `actions` 只有第一个 `jump_to.url` 会生效（作为卡片跳转链接）
