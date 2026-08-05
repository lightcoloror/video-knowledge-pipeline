# Agent 在线多模态数据外发授权

## 更新记录

- 2026-07-13 20:54:49 | Codex / GPT-5：新增 bundle/provider/index 级授权、agent 执行门禁和合规回退说明。

## 要解决的问题

Agent 调用在线多模态 API 时，实际会把本地视频帧以及对应的字幕、OCR 上下文发送给第三方服务。仅有 API key 或一次聊天中的“允许”不足以形成可复核的运行契约，也不能证明 agent 没有扩大范围。

VKP 现在把问题拆成两层：

1. **项目执行门禁**：用持久化授权文件限定 bundle、provider、model、endpoint、timeline indexes、最大调用数、图像尺寸、有效期和用途。
2. **Agent 平台策略**：Codex、OpenClaw、Hermes 或其他平台仍可能拒绝本地数据外发。项目授权不能覆盖平台策略，也不得通过改名、编码、代理脚本或重试来绕过。

项目层的目标是减少“缺少明确授权、范围不清、批次过大、密钥泄漏”造成的拒绝。平台仍拒绝时，必须回退到可见 PowerShell 或本地 VLM。

## 实际发送的数据

每个获准的单帧或连续帧条目只允许发送：

- 预检选中的视频帧。
- 对应条目的 transcript 上下文。
- 对应条目的 OCR/visual_text 上下文。

明确禁止：

- 完整视频和完整音频。
- 未列入授权 indexes 的帧。
- cookies、账号登录态、API key、token、credentials。
- 无上限全量发送。

授权会对所选帧内容及其 transcript/OCR 上下文计算稳定证据哈希。模型结果写回 timeline 不会使授权失效；帧内容、帧路径或发送上下文变化会阻断执行并要求重新授权。

## CLI 流程

### 1. 先做疑难点 A/B/C 计划

```powershell
.\scripts\video-knowledge.ps1 visual-ab-benchmark-plan <bundle> --limit 10
```

A/B/C 含义：

- A：纠正版逐字稿。
- B：A + 本地 ebook/OCR。
- C：B + 只对疑难点执行在线多模态。

### 2. 创建显式授权

```powershell
.\scripts\video-knowledge.ps1 vision-export-consent-create <bundle> `
  --provider-config <provider-config.json> `
  --semantic-indexes "26,46" `
  --temporal-indexes "80,112" `
  --max-calls 4 `
  --image-max-edge 512 `
  --image-jpeg-quality 55 `
  --expires-hours 24 `
  --purpose "targeted visual review" `
  --confirm-data-export
```

授权文件是 `<bundle>\vision-export-consent.json`。它不保存 API key。

### 3. 校验授权

```powershell
.\scripts\video-knowledge.ps1 vision-export-consent-status <bundle> `
  --provider-config <provider-config.json> `
  --semantic-indexes "26,46" `
  --temporal-indexes "80,112" `
  --expected-calls 4 `
  --image-max-edge 512 `
  --image-jpeg-quality 55
```

只有 `valid=true` 才能进入 agent 执行。

### 4. 预检和执行

单帧与连续帧分别预检，复制预检给出的精确 `confirm_vision_calls` 和 `confirm_vision_indexes`。Agent 调用时必须增加：

```text
--execution-actor agent
--export-consent <bundle>\vision-export-consent.json
```

火山批次脚本也支持相同边界：

```powershell
.\scripts\run-volcengine-vision-batch.ps1 <bundle> `
  -Indexes "26,46" `
  -Limit 2 `
  -ExecutionActor agent `
  -ExportConsent <bundle>\vision-export-consent.json `
  -Execute
```

MCP 的多模态执行工具默认 `execution_actor=agent`，没有有效授权会返回 `vision_export_consent_required`，不会发请求。

### 5. 撤销

```powershell
.\scripts\video-knowledge.ps1 vision-export-consent-revoke <bundle>
```

## 平台仍拒绝时

这是平台级数据外发策略，不是 VKP bug，也不是授权文件能解决的问题。Agent 必须：

1. 停止在线调用，不做隐蔽重试。
2. 返回预检生成的精确可见 PowerShell 命令，让操作者在本机执行。
3. 或把同一批 indexes 切到 `local_vlm`，帧不离开本机。
4. 保留 `platform_policy_may_still_block=true` 和失败原因，不能伪报已执行。

## UI/MCP 约定

后续 UI 应只展示和调用这些稳定入口：

- `visual_ab_benchmark_plan`
- `vision_export_consent_create`
- `vision_export_consent_status`
- `vision_export_consent_revoke`
- `run_multimodal_frame_analysis_tool`
- `run_temporal_visual_analysis_tool`

UI 不保存 API key；密钥继续从环境变量或本机私有配置读取。
