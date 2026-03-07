# 开发指南

## 开发环境准备

### 前置要求

- Python 3.11+
- Xcode 15+（macOS App 开发）
- Docker（relay-server 开发）

### 初始化开发环境

```bash
git clone https://github.com/xykong/flux-notifier.git
cd flux-notifier

# 安装 Python core 包（开发模式）
cd packages/core
pip install -e ".[dev]"

# 运行测试
pytest tests/
```

---

## 新增 Adapter

每个 Adapter 是一个继承自 `AdapterBase` 的 Python 类，放置于 `packages/core/flux_notifier/adapters/` 目录下。

### 1. 实现 Adapter 类

```python
from flux_notifier.adapters.base import AdapterBase, SendResult
from flux_notifier.schema import NotificationPayload


class MyAdapter(AdapterBase):
    name = "my_adapter"

    async def send(self, payload: NotificationPayload) -> SendResult:
        """
        发送通知。
        返回 SendResult(success=True/False, message="...", response_url="...")
        response_url 是用户可以在此 URL 回传响应的地址（可选）。
        """
        ...

    async def health_check(self) -> bool:
        """
        检查 Adapter 是否可用（连通性检查）。
        """
        ...
```

### 2. 注册 Adapter

在 `packages/core/flux_notifier/router.py` 中注册：

```python
from flux_notifier.adapters.my_adapter import MyAdapter

ADAPTER_REGISTRY = {
    ...
    "my_adapter": MyAdapter,
}
```

### 3. 添加配置 Schema

在 `packages/core/flux_notifier/config.py` 中添加对应的 Pydantic 配置模型：

```python
class MyAdapterConfig(BaseModel):
    api_key: str
    endpoint: str = "https://default.example.com"
```

### 4. 添加配置示例

在 `config/config.example.toml` 中添加对应的配置段落。

### 5. 编写测试

在 `packages/core/tests/adapters/test_my_adapter.py` 中添加测试。

### 6. 编写文档

在 `docs/adapters/my_adapter.md` 中添加配置和使用说明。

---

## 代码规范

### Python

- 使用 `ruff` 进行 lint 和格式化
- 类型注解覆盖所有公开 API
- 异步方法使用 `async/await`，不使用 `threading`
- 禁止 `print`，使用 `logging`

### Swift

- 使用 SwiftLint
- 遵循 Swift API Design Guidelines
- 所有 UI 组件使用 SwiftUI，不使用 AppKit（除非必须）

---

## 测试

```bash
# 运行所有测试
cd packages/core
pytest tests/ -v

# 运行特定 Adapter 测试
pytest tests/adapters/test_feishu_webhook.py -v

# 覆盖率报告
pytest tests/ --cov=flux_notifier --cov-report=html
```

**Adapter 测试规范** ：
- 使用 `pytest-httpx` mock HTTP 请求，不发送真实网络请求
- 覆盖成功、失败、超时、认证错误等场景

---

## 发布流程

### Python 包（PyPI）

```bash
cd packages/core
python -m build
twine upload dist/*
```

CI 会在 git tag 时自动发布。

### macOS App（Homebrew Cask）

CI 会在 `release.yml` 中自动：
1. 编译并签名 macOS App
2. 打包为 `.dmg`
3. 上传到 GitHub Releases
4. 更新 Homebrew Cask formula

### relay-server（Docker Hub）

```bash
cd packages/relay-server
docker build -t flux-notifier/relay-server .
docker push flux-notifier/relay-server:latest
```

---

## 项目结构约定

- `packages/core/` — 所有 Python 代码，包括 CLI、路由引擎、所有 Adapter
- `packages/macos-app/` — 仅 Swift 代码，只负责接收消息和 UI 展示
- `packages/relay-server/` — 独立的 FastAPI 服务，仅处理手机 Push 中继
- `packages/opencode-skill/` — 纯文档，无代码逻辑
- `docs/` — 面向用户的文档
- `config/` — 配置模板
- `scripts/` — 安装脚本
