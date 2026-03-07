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

cd packages/core
pip install -e ".[dev]"

pytest tests/ -v
```

---

## 新增 Adapter（强制清单）

每个 Adapter 必须同时完成以下全部 6 项，缺一不可：

1. `packages/core/flux_notifier/adapters/<name>.py` — 实现 `AdapterBase`
2. `packages/core/flux_notifier/config.py` — 添加 `<Name>Config(BaseModel)` 和 `AppConfig` 字段
3. `packages/core/flux_notifier/router.py` — 在 `_build_adapters()` 注册
4. `packages/core/tests/adapters/test_<name>.py` — 完整测试覆盖（见测试规范）
5. `config/config.example.toml` — 添加带注释的配置段落
6. `docs/adapters/<name>.md` — 面向用户的配置和使用说明

### Adapter 实现模板

```python
from __future__ import annotations

import logging

from flux_notifier.adapters.base import AdapterBase, SendResult
from flux_notifier.config import MyAdapterConfig
from flux_notifier.schema import NotificationPayload

logger = logging.getLogger(__name__)


class MyAdapter(AdapterBase):
    name = "my_adapter"

    def __init__(self, config: MyAdapterConfig) -> None:
        self._config = config

    async def send(self, payload: NotificationPayload) -> SendResult:
        try:
            ...
            return SendResult(success=True, adapter=self.name)
        except Exception as exc:
            logger.error("my_adapter send failed: %s", exc)
            return SendResult(success=False, adapter=self.name, message=str(exc))

    async def health_check(self) -> bool:
        return bool(self._config.api_key)
```

关键约束：
- `send()` 绝不能 raise — 所有异常必须被捕获，返回 `SendResult(success=False)`
- `health_check()` 绝不发网络请求 — 只检查配置是否完整
- 构造函数只接受一个对应的 `*Config` Pydantic 对象

### Router 注册方式

```python
def _build_adapters(config: AppConfig, targets: list[str] | None) -> list[AdapterBase]:
    from flux_notifier.adapters.my_adapter import MyAdapter

    registry: dict[str, AdapterFactory] = {
        "macos": MacOSAdapter,
        "feishu_webhook": FeishuWebhookAdapter,
        "my_adapter": MyAdapter,
    }
```

### Config 模式

```python
class MyAdapterConfig(BaseModel):
    api_key: str
    endpoint: str = "https://default.example.com"

class AppConfig(BaseModel):
    ...
    my_adapter: MyAdapterConfig | None = None
```

---

## 代码规范

### Python

- `ruff check .` — lint，提交前必须通过
- 所有公开 API 必须有类型注解
- 异步使用 `async/await`，禁止 `threading`
- 禁止 `print`，使用 `logging.getLogger(__name__)`
- 禁止不必要的注释 — 代码应自注释
- 禁止 `# type: ignore`、`cast`、`Any`（除非匹配现有模式）

### Swift

- 遵循 Swift API Design Guidelines
- UI 组件使用 SwiftUI，仅在必须时使用 AppKit
- `swift build` 必须零警告零错误

---

## 测试规范

```bash
cd packages/core

pytest tests/ -v

pytest tests/adapters/test_feishu_webhook.py -v

pytest tests/ --cov=flux_notifier --cov-report=html
```

- HTTP Adapter：用 `pytest-httpx` mock，不发真实网络请求
- Socket Adapter：用 `unittest.mock.AsyncMock`，不依赖运行中的服务
- 覆盖：成功路径、API 错误响应、HTTP 传输错误、`health_check` 真/假
- 目标：100% 分支覆盖

---

## 验证门控（完成标准）

| 变更类型 | 必须通过 |
|---|---|
| Python 文件编辑 | `ruff check .` 无错误 + `pytest tests/ -v` 全绿 |
| 新增 Adapter | 上述 6 项清单全部完成 + 全套测试通过 |
| Swift 文件编辑 | `swift build` 退出码 0，零警告 |
| 文档编辑 | 相对链接无死链 |

---

## 发布流程

### Python 包（PyPI）

```bash
cd packages/core
python -m build
twine upload dist/*
```

git tag 时 CI 自动触发。

### macOS App（Homebrew Cask）

CI（`release.yml`）自动：
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

- `packages/core/` — 所有 Python 代码：CLI、路由引擎、所有 Adapter
- `packages/macos-app/` — 纯 Swift：只负责接收消息和 UI 展示
- `packages/relay-server/` — 独立 FastAPI 服务：仅处理手机 Push 中继
- `packages/opencode-skill/` — 纯文档，无代码逻辑
- `docs/` — 面向用户的文档
- `config/` — 配置模板
- `scripts/` — 安装脚本
