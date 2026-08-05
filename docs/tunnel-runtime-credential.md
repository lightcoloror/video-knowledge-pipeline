# Secure MCP Tunnel 运行密钥本地持久化

更新时间：2026-07-16 20:45:00
执行工具/模型：Codex（GPT-5）

## 稳定入口

```powershell
.\scripts\start-trusted-capability-tunnel.ps1
```

首次运行时输入一次 OpenAI Tunnel Runtime API Key。脚本使用 Windows DPAPI
加密后保存到：

```text
.local\tunnel-client\secrets\vkp-tunnel-runtime.credential.xml
```

密文绑定当前 Windows 用户和当前机器。后续启动只在当前进程内解密并注入
`CONTROL_PLANE_API_KEY`，不会把明文写入脚本、Tunnel profile、项目配置、日志
或提交记录。

## 状态与删除

状态检查不会回显密钥：

```powershell
.\scripts\start-trusted-capability-tunnel.ps1 -CredentialStatus
```

删除本地加密凭据：

```powershell
.\scripts\start-trusted-capability-tunnel.ps1 -ForgetCredential
```

删除后下次启动会重新提示输入。

## 安全边界

- Runtime API Key 只用于认证 OpenAI Tunnel 控制平面。
- 它不是 Groq、Mistral、Gemini、SiliconFlow 或火山引擎模型密钥。
- 它不会扩大 VKP Broker 目的地白名单，也不会替代 consent v2。
- Secure MCP Tunnel 仍只能访问 profile 指向的本机 Broker。
- 不应把密钥复制到聊天、Markdown、YAML、命令行参数或 Git。
