# VKP 本地模型 API 设置 UI 设计

更新时间：2026-07-14 22:04:52
执行者：Codex / GPT-5

## 目标

在 VKP WebUI 中提供显式的在线模型供应商配置入口。用户可以分别为 ASR、OCR、文档视觉、单帧语义、多帧时序、文本模型、摘要改写和转录纠错选择供应商、模型、Base URL 与适配器，并把设置持久化在本机。

## 方案比较

1. 浏览器 `localStorage`：实现最轻，但设置只属于单个浏览器来源，API Key 以浏览器数据形式保存，静态 `file://` 页面也无法可靠写回 VKP 运行时，因此不采用。
2. 继续生成 PowerShell 命令：当前已经具备，但需要人工复制执行，不满足“在 UI 中保存”，因此保留为恢复入口，不作为主路径。
3. 独立 loopback 设置服务：推荐。仅监听 `127.0.0.1`，与 Secure MCP Tunnel 的 `/mcp` 服务分离；同源页面通过本地 JSON API 保存设置。

## 存储与安全

- 非密钥配置：`.local/model-api-settings.json`。
- API Key：Windows DPAPI 加密后写入 `.local/model-api-secrets.json`，只对当前 Windows 用户可解密。
- 公共状态和 HTTP 响应只返回 `api_key_configured`，永不返回 Key 或密文。
- Base URL 禁止用户名/密码、query 与 fragment；远程地址必须是 HTTPS，本地地址可使用 loopback HTTP。
- 保存配置不等于授权外发。真实调用继续受 consent、精确 artifact hash、调用次数、过期时间及 Trusted Broker 目的地白名单约束。
- 设置服务不注册为 MCP 工具，不通过 Secure MCP Tunnel 暴露。

## 数据流

1. 用户从 `model-settings.html` 打开本地设置页。
2. 页面从同源 `/api/settings` 读取脱敏 profile 与任务映射。
3. 保存时，普通字段写入 settings JSON，非空 Key 交给 DPAPI；空 Key 保留现有凭据。
4. `online_model_gateway` 在没有显式 runtime provider config 时，按 `model_type` 读取本地 task route。
5. 显式 runtime config 仍具有最高优先级；环境变量和旧版 `vision_execution` 继续作为兼容回退。

## UI

- 左侧显示已保存供应商 profile 与 Key 状态。
- 右侧编辑名称、供应商、适配器、模型、Base URL、超时和任务复选框。
- API Key 输入框永远为空；保存空值不会删除旧 Key，显式“删除凭据”才删除。
- 页面提供保存、验证（只做结构/策略验证，不联网）、新建和删除操作。
- 顶部明确显示配置文件路径、服务地址和“保存不代表目的地已获授权”。

## 验证

- 单元测试覆盖：原子持久化、DPAPI codec 替身、Key 不落明文、任务路由、显式配置优先、URL 校验。
- HTTP 测试覆盖：页面、脱敏 GET、带 CSRF 的保存、错误输入与凭据删除。
- WebUI 测试覆盖：任务控制台仍生成模型设置入口并指向 loopback 设置服务。
- 最后运行相关测试、Python 编译检查和完整回归；不发起真实在线模型调用。
