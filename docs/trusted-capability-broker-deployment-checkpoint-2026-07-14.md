# VKP Trusted Capability Broker 部署 Checkpoint

- acting tool/model：Codex（GPT-5）
- 更新时间：2026-07-14 16:05:00 +08:00
- 状态：Tunnel 与 App 已连接，等待新任务只读 smoke

## 完成情况

- 完成：OpenAI Secure MCP Tunnel 创建并启动
- 完成：本地 VKP Broker 通过 Tunnel 暴露为自定义 App
- 完成：ChatGPT/Codex 自动生成 remote plugin 并连接
- 完成：remote plugin manifest 与 `.app.json` 通过 plugin validator
- 失败：0 个阻断项
- 在线模型调用：0
- 帧外发：0

## 标识与路径

- Tunnel ID：`tunnel_6a55ea8b746c819190872066c7d22910`
- App ID：`asdk_app_6a55ecfac8b08191a111d722a26e0e5a`
- App 显示名：`VKP Trusted Capability Broker`
- 本地 Broker：`http://127.0.0.1:8766/mcp`
- Tunnel 管理 UI：`http://127.0.0.1:8080/ui`
- Tunnel profile：`%WORKSPACE_ROOT%\video-knowledge-pipeline\.local\tunnel-client\profiles\vkp-local.yaml`
- 验证过的 tunnel-client：`%WORKSPACE_ROOT%\video-knowledge-pipeline\.local\tunnel-client\v0.0.10\verified\tunnel-client.exe`
- 平台生成插件缓存：`%USERPROFILE%\.codex\plugins\cache\created-by-me-remote\dev-6a55ecfac8b08191a111d722a26e0e5a\1.0.0`

## 验证证据

- `GET http://127.0.0.1:8080/healthz`：`200 live`
- `GET http://127.0.0.1:8080/readyz`：`200 ready`
- MCP session：初始化成功
- MCP protocol：`2025-06-18`
- MCP server：`vkp-trusted-capability-broker`
- Control-plane metadata：获取成功
- Control-plane poller：启动成功
- Tool discovery：平台页面显示执行工具及其 open-world/risk annotations
- Plugin validator：passed

## 安全边界

- Broker 与 Tunnel 管理界面只监听 loopback。
- Runtime API Key 只存在于操作者 PowerShell 环境变量，不写入 profile、插件或项目文档。
- App 使用无认证 MCP；Tunnel 自身负责 OpenAI 控制面认证。
- 平台权限保持默认“允许低风险操作”；三个 `execute_*` 工具不设为无条件自动执行。
- Broker 继续执行 consent、路径根目录、provider destination 与调用次数检查。
- 当前仅完成连接和工具发现，没有运行任何模型任务。

## 已知非阻断问题

`tunnel-client v0.0.10 doctor` 会把无认证 MCP 的 OAuth metadata `404` 判为失败；其内置 `sample_mcp_remote_no_auth` 明确说明全候选 `404` 仍可 ready。实际运行结果为 `/readyz = 200 ready`，因此未伪造 OAuth metadata。

## 剩余缺口

1. 在新 Codex 任务加载新安装的 App 工具。
2. 仅调用 `model_connector_capabilities`，验证 App-backed tool 往返。
3. 再调用 `model_connector_consent_status` 做非执行状态检查。
4. 只有在用户明确批准具体 provider、artifact 与 consent 后，才测试一个 `execute_*` 调用。
