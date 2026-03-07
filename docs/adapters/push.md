# 手机 Push Adapter

通过 APNs（Apple Push Notification Service）和 FCM（Firebase Cloud Messaging）向 iOS/Android 手机和 Apple Watch 推送通知。

---

## 架构

由于 APNs 和 FCM 需要服务端证书，Push 通知通过中继服务转发：

```
notify CLI → relay-server → APNs → iPhone/Apple Watch
                          → FCM  → Android
```

---

## 快速开始

### 使用官方公共中继服务

1. 访问 [flux-notifier.dev](https://flux-notifier.dev)（待上线）注册账号
2. 在手机上安装 Flux Notifier App，登录账号获取设备 Token
3. 在管理后台复制 API Key

```toml
[targets]
enabled = ["push"]

[push]
relay_url = "https://push.flux-notifier.dev"
api_key = "YOUR_API_KEY"
device_token = "YOUR_DEVICE_TOKEN"
```

### 自托管中继服务

适合对隐私有较高要求的用户。

```bash
# 使用 Docker 部署
git clone https://github.com/xykong/flux-notifier.git
cd packages/relay-server

# 配置环境变量
cp .env.example .env
# 填写 APNs 证书路径和 FCM 服务账号 JSON 路径

# 启动服务
docker-compose up -d
```

```toml
[push]
relay_url = "https://your-relay-server.com"
api_key = "YOUR_SELF_HOSTED_API_KEY"
device_token = "YOUR_DEVICE_TOKEN"
```

---

## 能力

| 功能 | iOS | Android | Apple Watch |
|------|-----|---------|-------------|
| 标题 + 正文 | ✅ | ✅ | ✅（简短） |
| 图片 | ✅ | ✅ | ❌ |
| 按钮（最多 2 个） | ✅ | ✅ | ✅ |
| 跳转链接 | ✅ | ✅ | ✅ |
| `urgent` 穿透勿扰 | ✅ (关键通知) | ✅ | ✅ |
| 用户响应回传 | 有限 | 有限 | ❌ |

**注意** ：Push 通知按钮响应回传依赖手机 App，目前规划为 Phase 3 功能。

---

## relay-server 自托管配置

### APNs 配置

1. Apple Developer Center → Certificates → 创建 APNs Key（`.p8` 文件）
2. 记录 Key ID 和 Team ID

```env
APNS_KEY_PATH=/path/to/AuthKey_XXXXXXXXXX.p8
APNS_KEY_ID=XXXXXXXXXX
APNS_TEAM_ID=XXXXXXXXXX
APNS_BUNDLE_ID=dev.flux-notifier.app
```

### FCM 配置

1. Firebase Console → 项目设置 → 服务账号 → 生成新私钥
2. 保存 JSON 文件

```env
FCM_SERVICE_ACCOUNT_PATH=/path/to/firebase-service-account.json
```
