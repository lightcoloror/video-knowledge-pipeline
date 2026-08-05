# 公开仓库脱敏与发布边界

更新工具/模型：Codex（GPT-5）

更新时间：2026-08-05 13:08:24

## 当前快照

- 意图：让 VKP 的公开源码不依赖或暴露单台电脑的用户名、磁盘布局和同步目录。
- 决策：运行时路径统一通过 `VKP_*` 环境变量或仓库相对路径解析；文档使用 `%WORKSPACE_ROOT%`、`%MEDIA_ROOT%`、`%LOCAL_MODEL_ROOT%` 等占位符。
- 理由：硬编码个人绝对路径既无法复用，也会暴露本地目录结构。
- 证据：`tests/test_publication_safety.py` 会扫描 Git 当前跟踪快照，并阻止已知个人路径重新进入版本库。
- 生效范围：当前 Git 快照中的源码、脚本、示例、测试与文档；不自动修改用户的本地配置、`.local` 产物或媒体文件。

## 环境变量

常用覆盖项包括：

- `VKP_WORKSPACE_ROOT`
- `VKP_PROVIDER_ENV_FILE`
- `VKP_PORT_RECORD_PATH`
- `VKP_OPENCLAW_COMPOSE_PATH`
- `VKP_TOOL_SOURCE_REVIEW_ROOT`
- `VKP_SOURCE_REVIEWS_ROOT`
- `VKP_LOCAL_MODEL_ROOT`
- `VKP_DATASET_ROOT`
- `VKP_VIDEO_TOOL_LAB_ROOT`

未配置时优先使用仓库相对位置或当前用户的标准目录，不包含开发者姓名。

## 不进入公开仓库的内容

- API Key、密码、令牌、DPAPI 凭据和环境文件。
- 原始视频、音频、逐字稿、客户资料和人工审核内容。
- `.local` 中的模型、缓存、网关状态、运行日志和评测中间产物。
- 仅服务于本机调度的临时计划、端口记录和路径映射。

## 历史发布边界

当前快照脱敏并不等于旧 Git 历史已经脱敏。将私有仓库改为公开前，必须另行执行历史扫描；若旧提交包含个人路径或敏感产物，应在明确授权后重写历史并使用受控的 `--force-with-lease` 发布。普通追加提交无法隐藏旧提交中的内容。
## 许可证决策

- 意图：为公开后的源码复用、修改和网络部署提供明确且严格的共享边界。
- 决策：采用 AGPL-3.0-only，许可证正文复用已审查的 LogseqMarkdownParser 固定源码 LICENSE，SHA-256 为 E0EEDBA615D5CD1B986AFB6C5B3A4B1AE33713E7E9DC74D19DAEC5E3221F9D2E。
- 理由：VKP 账本中的 GPL-3.0 项目仅作设计研究且未复制源码；已参考项目中 AGPL-3.0 是更严格且有本地原文可验证的许可证，覆盖分发与网络服务修改版的源码提供义务。
- 证据：LogseqMarkdownParser 固定 commit ce8f29c4b50d37e21d491887dc31c584efc8d919；MindGraph 固定 commit 9c9da2efd3f48f1191c3d23c4662845e4a8d979c 也声明 GNU AGPL v3。
- 生效范围：VKP 自有源码和本仓库整体发布；第三方依赖、模型、独立服务及仅供源码研究的 checkout 继续适用其各自许可证与通知。
