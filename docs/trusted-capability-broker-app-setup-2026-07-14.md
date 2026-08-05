# VKP Trusted Capability Broker App 配置手册

- 状态：本地 Broker 已实现，等待平台 App 创建和绑定
- acting tool/model：Codex（GPT-5）
- 更新时间：2026-07-14 12:35:00 +08:00

## 本地端点

Broker 使用 Streamable HTTP，但只监听回环地址：

```text
http://127.0.0.1:8766/mcp
```

平台访问应使用 OpenAI Secure MCP Tunnel。不要把服务绑定到 `0.0.0.0`，也不要使用 ngrok、通用 HTTP 中转或二次 Agent 隐藏最终目的地。

默认策略：

- 允许读取范围：`%WORKSPACE_ROOT%\video-knowledge-pipeline`
- 本地模型目的地：`localhost`、`127.0.0.1`、`::1`
- 首个远程目的地：`ark.cn-beijing.volces.com`
- 任意 URL：禁止
- 远程 HTTP：禁止，必须 HTTPS
- 密钥：只从 `.local` 环境文件加载，不进入 MCP 参数或 App 配置

## 启动

在可见 PowerShell 中运行：

```powershell
cd %WORKSPACE_ROOT%\video-knowledge-pipeline
.\scripts\start-trusted-capability-broker-http.ps1
```

保持该窗口运行。另开 PowerShell 进行只读 smoke：

```powershell
cd %WORKSPACE_ROOT%\video-knowledge-pipeline
$env:PYTHONPATH = 'src'
python .\scripts\smoke-trusted-capability-broker-http.py
```

预期扫描到 5 个工具：

1. `model_connector_capabilities`
2. `model_connector_consent_status`
3. `execute_consented_model_task_tool`
4. `execute_consented_semantic_vision`
5. `execute_consented_temporal_vision`

前两个工具带 read-only annotations；后三个工具标记为 open-world execution，便于平台单独配置 action approval。

## 需要用户点击的平台步骤

以下步骤只能由工作区管理员/所有者在 ChatGPT Web 完成：

1. 打开 `Settings -> Apps -> Advanced settings`，启用 Developer mode。
2. 进入 `Workspace settings -> Apps -> Create`。
3. 选择 Secure MCP Tunnel，用它连接本机 `http://127.0.0.1:8766/mcp`。不要创建公网 tunnel。
4. App 名称填写 `VKP Trusted Capability Broker`。
5. 点击 `Scan Tools`，核对只出现上述 5 个工具。
6. 首轮只启用 `model_connector_capabilities` 与 `model_connector_consent_status`；执行工具暂时保留需要确认。
7. 点击 `Create`，让 App 进入 Draft 状态。
8. 把创建后的 App ID（形如 `asdk_app_...`）发给 Codex。App ID 不是密钥，可以用于插件 `.app.json` 绑定；不要发送 OAuth token、API key 或 tunnel 凭据。

收到 App ID 后，Codex 将继续：

- 创建最终 `vkp-capability-broker` 插件及 `.app.json`；
- 运行 plugin validator；
- 更新 cachebuster 并安装到个人 marketplace；
- 在新任务中确认 App-backed tools 已出现；
- 完成一轮 capabilities、consent status 和非敏感 dry-run；
- 验证后再由管理员发布并逐步启用执行 actions。

## 平台限制

平台 App 批准后，Agent 可以在批准范围内调用本地或在线 provider，但并不意味着所有请求永不确认。敏感数据外发和高风险动作仍可能被要求确认或阻止；Broker 不会尝试绕过平台决定。
