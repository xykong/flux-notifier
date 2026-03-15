# Flux Notifier — 首次配置与问题排查指南

> **AI 使用说明**：当 `notify send` 返回 `delivered: []`、出现 `WARNING: no adapters configured`、
> 或用户反映"没有收到通知"时，**必须**遵循本文档的诊断流程，主动引导用户完成配置，
> 而不是直接报错或让用户自己翻文档。

---

## 诊断流程（AI 必读）

遇到通知问题时，按以下顺序检查，**每步确认后再进行下一步**：

```
Step 1：flux-notifier CLI 是否已安装？
  └─ 否 → 执行 [安装 Python CLI]
  └─ 是 ↓

Step 2：配置文件是否存在？
  └─ 否 → 执行 [选择适配器] 流程
  └─ 是 ↓

Step 3：[targets] enabled 列表是否非空？
  └─ 空 → 执行 [选择适配器] 流程
  └─ 非空 ↓

Step 4：适配器本身是否就绪（App 运行、网络通等）？
  └─ 否 → 执行对应 [故障排除] 流程
  └─ 是 → 通知应正常工作，重新发送测试
```

### 快速诊断命令（AI 直接执行）

```bash
# 1. 检查 CLI 是否可用
notify --version 2>/dev/null && echo "CLI OK" || echo "CLI NOT FOUND"

# 2. 检查配置文件是否存在
ls ~/.flux-notifier/config.toml 2>/dev/null && echo "CONFIG EXISTS" || echo "CONFIG MISSING"

# 3. 检查已启用的适配器
python3 -c "
import tomllib, pathlib, sys
p = pathlib.Path('~/.flux-notifier/config.toml').expanduser()
if not p.exists(): sys.exit('CONFIG_MISSING')
cfg = tomllib.loads(p.read_text())
enabled = cfg.get('targets', {}).get('enabled', [])
print('ENABLED:', enabled if enabled else 'NONE')
" 2>&1
```

---

## 安装 Python CLI

### 推荐：uv tool（全局安装，无环境污染）

```bash
uv tool install flux-notifier
```

安装后 `notify` 命令全局可用：

```bash
notify --version
```

### 备选：pipx / pip

```bash
# pipx（推荐，隔离环境）
pipx install flux-notifier

# pip（直接安装到当前环境）
pip install flux-notifier
```

> 安装完成后如提示找不到命令，重新打开终端，或将 `~/.local/bin` 加入 PATH。

---

## 选择适配器（AI 引导用户）

当用户没有配置适配器时，**先询问用户的使用场景**，然后推荐最合适的方案：

### 询问用户的问题

> "你希望通知发送到哪里？以下是可用的选项：
>
> 1. **macOS 系统通知**（本机弹窗，最简单，无需任何账号）
> 2. **飞书**（手机 / 电脑 App 均可收到，适合远程场景）
> 3. **企业微信**（有企业微信账号的用户）
> 4. **邮件**（适合非实时场景）
> 5. **同时启用多个**（推荐：macOS + 飞书）
>
> 你在哪个平台上工作，希望在哪里收到通知？"

根据用户回答，跳转到对应的配置节。

---

## 适配器配置

### A. macOS 原生通知（推荐首选）

**适用**：在 macOS 上工作，需要本机弹窗通知。无需任何账号，5 分钟配置完成。

#### Step 1：安装 FluxNotifier.app

```bash
# 方式一：Homebrew Cask（推荐）
brew tap xykong/tap
brew install --cask flux-notifier

# 方式二：手动下载
# 访问 https://github.com/xykong/flux-notifier/releases 下载最新 FluxNotifier.zip
# 解压后将 FluxNotifier.app 拖入 /Applications
```

#### Step 2：启动 App

```bash
open /Applications/FluxNotifier.app
```

App 启动后会在菜单栏出现图标（无 Dock 图标）。

#### Step 3：授权系统通知

首次启动时系统会弹出通知权限请求，点击"允许"。

如果错过了：**系统设置 → 通知 → FluxNotifier → 允许通知**

#### Step 4：写入配置

```bash
cat > ~/.flux-notifier/config.toml << 'EOF'
[targets]
enabled = ["macos"]

[macos]
window_position = "top-right"
auto_dismiss = 30
EOF
```

#### Step 5：验证

```bash
notify send --title "✅ 配置成功" --body "macOS 通知已正常工作！" --no-wait
```

**预期结果**：右上角弹出通知悬浮窗，且命令输出 `"delivered": ["macos"]`。

#### macOS 故障排除

| 症状 | 检查 | 解决 |
|------|------|------|
| `delivered: []`，无弹窗 | App 是否运行？ | `open /Applications/FluxNotifier.app` |
| Socket 连接失败 | Socket 文件是否存在？ | `ls ~/.flux-notifier/macos.sock` |
| 通知不显示但 delivered | 通知权限未授予 | 系统设置 → 通知 → FluxNotifier → 开启 |
| App 无法打开 | Gatekeeper 拦截 | 系统设置 → 隐私与安全 → 仍要打开 |

```bash
# 检查 App 进程
pgrep -l FluxNotifier

# 检查 Socket
ls -la ~/.flux-notifier/macos.sock

# 重启 App
pkill FluxNotifier; sleep 1; open /Applications/FluxNotifier.app
```

---

### B. 飞书 Webhook（推荐远程/手机场景）

**适用**：需要在手机或其他设备收到通知，有飞书账号。10 分钟配置完成。

#### Step 1：创建飞书机器人

1. 打开任意飞书群聊（可以创建一个专门的「AI 通知」群）
2. 群设置 → 机器人 → 添加自定义机器人
3. 填写机器人名称（如"Flux Notifier"），点击添加
4. 复制 Webhook URL（格式：`https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx`）

#### Step 2：写入配置

将 `YOUR_WEBHOOK_TOKEN` 替换为第 4 步复制的 URL 末尾部分：

```bash
# AI 执行时替换实际 webhook_url
cat > ~/.flux-notifier/config.toml << 'EOF'
[targets]
enabled = ["feishu_webhook"]

[feishu_webhook]
webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK_TOKEN"
EOF
```

如果群机器人开启了**签名校验**，还需加上 secret：

```toml
[feishu_webhook]
webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK_TOKEN"
secret = "YOUR_SECRET"
```

#### Step 3：验证

```bash
notify send --title "✅ 飞书通知测试" --body "来自 flux-notifier，配置成功！" --no-wait
```

**预期结果**：飞书群收到消息卡片，命令输出 `"delivered": ["feishu_webhook"]`。

#### 飞书故障排除

| 症状 | 原因 | 解决 |
|------|------|------|
| `{"code":19001}` | Webhook URL 无效或已过期 | 重新从群设置复制 URL |
| `{"code":19021}` | 签名校验失败 | 检查 secret 是否正确，或去掉签名校验 |
| 请求超时 | 网络问题 | 检查能否访问 `open.feishu.cn` |

---

### C. 飞书企业应用（feishu_app）

**适用**：需要给指定用户发消息（不依赖群聊），或有企业飞书账号。

#### Step 1：创建飞书自建应用

1. 访问 [飞书开放平台](https://open.feishu.cn/app)
2. 创建应用 → 自建应用
3. 权限管理 → 开通 `im:message:send_as_bot`
4. 发布应用（需管理员审批）
5. 凭证与基础信息 → 复制 App ID 和 App Secret

#### Step 2：获取接收用户的 open_id

```bash
# 在飞书开发者后台：人员 → 搜索用户 → 查看 open_id
# 或通过 API 查询自己的 open_id：
curl "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal" \
  -H "Content-Type: application/json" \
  -d '{"app_id":"YOUR_APP_ID","app_secret":"YOUR_APP_SECRET"}' | python3 -m json.tool
```

#### Step 3：写入配置

```bash
cat > ~/.flux-notifier/config.toml << 'EOF'
[targets]
enabled = ["feishu_app"]

[feishu_app]
app_id = "cli_YOUR_APP_ID"
app_secret = "YOUR_APP_SECRET"
receiver_id = "ou_YOUR_USER_OPEN_ID"
receiver_id_type = "open_id"
EOF
```

---

### D. 企业微信（wechat_work）

**适用**：企业微信用户。

#### Step 1：创建自建应用

1. 企业微信管理后台（[work.weixin.qq.com](https://work.weixin.qq.com)）→ 应用管理 → 自建 → 创建应用
2. 获取 AgentId 和 Secret
3. 管理后台首页 → 我的企业 → 获取企业 ID（CorpID）
4. 获取你自己的企业微信账号（userid）

#### Step 2：写入配置

```bash
cat > ~/.flux-notifier/config.toml << 'EOF'
[targets]
enabled = ["wechat_work"]

[wechat_work]
corp_id = "YOUR_CORP_ID"
agent_id = 1000001
secret = "YOUR_AGENT_SECRET"
to_user = "YOUR_USERID"
EOF
```

---

### E. 邮件（email）

**适用**：非实时场景，有 SMTP 邮件服务。

> **注意**：邮件适配器不支持用户响应回传，只适合单向通知。

#### 配置（以 Gmail 为例）

Gmail 需要先开启应用专用密码：
Google 账户 → 安全 → 两步验证（需已开启）→ 搜索"应用专用密码"→ 生成 16 位密码

```bash
cat > ~/.flux-notifier/config.toml << 'EOF'
[targets]
enabled = ["email"]

[email]
smtp_host = "smtp.gmail.com"
smtp_port = 587
username = "your@gmail.com"
password = "YOUR_16_CHAR_APP_PASSWORD"
from = "Flux Notifier <your@gmail.com>"
to = ["your@gmail.com"]
use_tls = true
EOF
```

| 服务商 | smtp_host | smtp_port |
|--------|-----------|-----------|
| Gmail | `smtp.gmail.com` | `587` |
| Outlook | `smtp.office365.com` | `587` |
| QQ 邮箱 | `smtp.qq.com` | `587` |
| 网易 163 | `smtp.163.com` | `994` |

---

### F. 同时启用多个适配器（推荐）

macOS + 飞书 Webhook 组合是最推荐的配置：本机弹窗 + 手机推送同时到达。

```bash
cat > ~/.flux-notifier/config.toml << 'EOF'
[targets]
enabled = ["macos", "feishu_webhook"]

[macos]
window_position = "top-right"
auto_dismiss = 30

[feishu_webhook]
webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK_TOKEN"
EOF
```

---

## 通用验证命令

配置完成后，始终用这条命令验证：

```bash
notify send \
  --title "✅ 配置验证" \
  --body "如果你看到这条通知，说明 flux-notifier 配置成功！" \
  --no-wait
```

**成功标志**：输出的 JSON 中 `delivered` 数组非空，例如：

```json
{"notification_id":"...","delivered":["macos","feishu_webhook"],"failed":[],"timestamp":"..."}
```

如果 `failed` 中有适配器名，说明该适配器配置有问题，回到对应配置节排查。

---

## 常见问题速查

| 错误信息 | 原因 | 解决 |
|----------|------|------|
| `WARNING: no adapters configured` | 配置文件不存在或 `enabled` 为空 | 执行 [首次安装流程] |
| `delivered: []` 且无警告 | 所有适配器均发送失败 | 检查 `failed` 列表，针对性排查 |
| `Connection refused` (macOS) | FluxNotifier.app 未运行 | `open /Applications/FluxNotifier.app` |
| `FileNotFoundError: config.toml` | 配置文件路径错误 | 确认文件在 `~/.flux-notifier/config.toml` |
| `ValidationError` | 配置字段格式错误 | 对照本文档检查 TOML 格式 |

---

## 配置文件完整模板

以下为包含所有适配器的完整配置示例。按需取用对应节，并在 `enabled` 中添加该适配器名：

```toml
# ~/.flux-notifier/config.toml

[targets]
enabled = ["macos"]   # 按需修改，可填多个

[macos]
window_position = "top-right"
auto_dismiss = 30

[feishu_webhook]
webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_TOKEN"
# secret = "YOUR_SECRET"

[feishu_app]
app_id = "cli_YOUR_APP_ID"
app_secret = "YOUR_APP_SECRET"
receiver_id = "ou_YOUR_USER_OPEN_ID"
receiver_id_type = "open_id"

[email]
smtp_host = "smtp.gmail.com"
smtp_port = 587
username = "your@gmail.com"
password = "YOUR_APP_PASSWORD"
from = "Flux Notifier <your@gmail.com>"
to = ["your@gmail.com"]
use_tls = true

[wechat_work]
corp_id = "YOUR_CORP_ID"
agent_id = 1000001
secret = "YOUR_AGENT_SECRET"
to_user = "YOUR_USERID"
```
