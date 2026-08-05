# VKP Trusted Capability Broker App 入口核对

- 状态：替代旧手册中不适用于所有套餐的统一菜单路径
- acting tool/model：Codex（GPT-5）
- 更新时间：2026-07-14 12:46:00 +08:00

## 前置条件

创建自定义 MCP App 的界面只在 ChatGPT Web 提供。Codex 桌面端和 ChatGPT 移动端不会显示创建入口。

先确认：

1. 当前位于 ChatGPT Business、Enterprise 或 Edu 工作区，而不是 Personal 工作区。
2. 当前账号是工作区 Admin/Owner，或已由 Enterprise/Edu 管理员授予 Developer mode 权限。
3. 使用浏览器打开 ChatGPT Web，并从账号菜单切换到对应工作区。

## 当前官方入口

管理员总开关：

`Workspace settings -> Permissions & Roles -> Connected Data -> Developer mode / Create custom MCP connectors`

套餐分流：

- Business：只有 Admin/Owner 可以启用 Developer mode、创建和发布 App；也可从 `Workspace settings -> Apps -> Create` 进入。
- Enterprise/Edu：管理员先在 `Permissions & Roles -> Connected Data` 授权；获授权用户再到 `Settings -> Apps -> Advanced Settings` 为自己启用 Developer mode。
- Pro：只能连接读/搜索权限的 MCP；完整 MCP 执行能力当前不开放。

满足条件后，进入 `Workspace settings -> Apps -> Create`。Enterprise/Edu 获授权开发者也可能在个人 `Settings -> Apps -> Create` 看到入口。

## 入口缺失的含义

- 看不到 `Workspace settings`：通常位于 Personal 工作区，或当前账号不是 Admin/Owner。
- 能看到 Workspace settings，但没有 `Permissions & Roles -> Connected Data`：通常是角色权限不足，或该 beta 尚未向工作区开放。
- 有 `Apps`，但没有 `Create`：通常没有 Developer mode 权限，或当前套餐不支持完整 MCP。
- 当前位于 Codex 桌面端：改用浏览器打开 ChatGPT Web 后再检查。

## 创建参数

入口出现后：

1. App 名称：`VKP Trusted Capability Broker`
2. 本机 MCP：`http://127.0.0.1:8766/mcp`
3. 本地服务不能直接连接，必须选择 Secure MCP Tunnel。
4. `Scan Tools` 应只发现 5 个工具。
5. 首轮仅允许 `model_connector_capabilities` 与 `model_connector_consent_status`；三个执行工具保留确认。
6. 创建为 Draft，并把非敏感 App ID `asdk_app_...` 交给 Codex完成插件绑定。

不要发送 OAuth token、API key 或 tunnel 凭据。

## 官方依据

- https://help.openai.com/en/articles/12584461
- https://help.openai.com/en/articles/11487775-connectors-in-chatgpt/
