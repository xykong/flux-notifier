# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-03-15

### Added

- **PyPI Package**: `flux-notifier` now available on PyPI (`pip install flux-notifier`)
- **Homebrew Cask**: macOS App installable via `brew tap xykong/tap && brew install --cask flux-notifier`
- **GitHub Release**: Automated release workflow with FluxNotifier.zip artifact
- **troubleshooting.md**: Comprehensive user guide for first-time setup and problem diagnosis
- **Problem diagnosis rules in skill.md**: AI now automatically guides users through adapter configuration when `delivered: []` occurs

### Changed

- **skill.md**: Removed hardcoded local paths, now uses `notify send` directly (assumes pip/uv tool install)
- **release.yml**: macOS job now creates GitHub Release with zip artifact instead of just uploading artifact
- **README.md**: Updated adapter status from "开发中" to "已发布"

### Adapters

All adapters are now production-ready:
- macOS native notifications (via FluxNotifier.app)
- Feishu Webhook
- Feishu App
- Email (SMTP)
- WeChat Work
- Push (via relay-server)
- Windows Toast
- Linux notify-send