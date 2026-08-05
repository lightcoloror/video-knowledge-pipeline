# VKP 一次业务授权与派生 consent v2

更新时间：2026-07-22 23:40:00 +08:00
执行工具/模型：Codex / GPT-5.6

## 结论

同一视频的已规划在线处理现在可以采用“一次业务确认，多个精确技术 consent”的方式。人工只确认一次完整业务边界；VKP 在边界内为后来生成的 OCR 输入、纠错包和章节摘要输入自动生成 consent v2，不再要求逐阶段重复确认。

这不是通配授权。每个实际外发文件仍然具有独立的绝对路径、字节数和 SHA-256，Broker 执行前仍验证当前 route revision、模型、目的地、调用数、费用、有效期和逐文件上传清单。

## 复用而非另建系统

- 路由与协议转换继续复用 LiteLLM Proxy。
- 执行继续复用 `execute_consented_model_task()`。
- 并发与 DAG 继续复用 `ConsentedModelBatchManager` 和 Python `graphlib.TopologicalSorter`。
- 子调用继续复用 consent v2、Broker allowlist 和原子调用/费用 reservation。
- 文件写入与互斥继续复用 VKP `bundle_write_lock` 和原子 JSON 写入。
- 新代码只增加父授权 envelope、hash-linked artifact admission 和窄 CLI/MCP 胶水。

## 两层契约

### 1. 业务授权

`video_knowledge_pipeline.model_business_authorization.v1` 固定：

- 精确源文件 SHA-256；
- 唯一 Bundle 根目录；
- 每个阶段的 task、route、route revision、virtual model、deployment 和目的地；
- 允许产生该派生文件的 VKP producer；
- 总调用/费用/文件数/字节数和各阶段上限；
- 零自动重试、零 fallback、零自动发布；
- 有效期。

### 2. 技术子 consent

Agent 只能在父授权范围内提交：

- 父授权路径；
- stage ID；
- producer ID；
- 已存在的派生文件；
- lineage 输入文件；
- 本次调用数。

它不能提交 Provider URL、模型、API Key、目的地或 route revision。VKP 验证派生文件位于 Bundle 内，且 lineage 中每个输入都匹配精确源或前一 admission，然后生成普通 consent v2。子 consent 的确认方式为 `parent_business_authorization`，并绑定父 authorization ID/hash、admission ID 和精确 upload manifest hash。

## 何时需要再次人工授权

只有以下任一项扩大时才需要新业务授权：

- 新源文件；
- 新任务或 producer；
- 新 Provider、目的地、模型、route ID 或 route revision；
- 新数据类型或 Bundle 外文件；
- 增加重试/fallback；
- 提高调用、费用、文件数量、字节数或有效期；
- 原始源文件内容发生变化。

同一授权范围内的新 OCR/视觉/纠错/摘要派生文件不需要再次人工确认。

## 稳定入口

一次可见确认：

```powershell
.\scripts\video-knowledge.ps1 model-business-authorization-create `
  <business-plan.json> `
  --output-path <business-authorization.json> `
  --confirm-data-export
```

只读状态：

```powershell
.\scripts\video-knowledge.ps1 model-business-authorization-status `
  <business-authorization.json>
```

边界内创建精确子 consent，不再要求确认：

```powershell
.\scripts\video-knowledge.ps1 model-business-child-consent `
  <business-authorization.json> `
  --stage-id summary `
  --producer smart_summary_input_pack `
  --artifact <derived-input.json> `
  --lineage-input <exact-source-or-prior-admission.json> `
  --max-calls 1
```

Secure MCP Broker 对应只暴露：

- `model_business_authorization_status_tool`
- `create_business_child_consent_tool`

MCP 不能创建或确认父授权，也不能覆盖 provider、模型、URL、密钥或 route revision。

## 计划文件最小结构

```json
{
  "schema": "video_knowledge_pipeline.model_business_authorization_plan.v1",
  "root_dir": "%WORKSPACE_ROOT%\\video-knowledge-pipeline",
  "bundle_dir": "D:\\...\\webui-bundle",
  "source_paths": ["D:\\...\\exact-source-artifact.json"],
  "purpose": "one video online OCR, vision, correction and summary",
  "expires_hours": 24,
  "scope": {
    "max_calls": 20,
    "max_estimated_cost_usd": 2.0
  },
  "stages": [
    {
      "id": "summary",
      "task": "smart_summary_section_rewrite",
      "route_id": "pool-example-summary",
      "route_revision": "<exact revision>",
      "allowed_producers": ["smart_summary_input_pack"],
      "max_calls": 8,
      "max_estimated_cost_usd": 0.8,
      "max_cost_per_call_usd": 0.1,
      "max_retries_per_call": 0,
      "max_artifacts": 8,
      "max_total_bytes": 8388608,
      "max_artifacts_per_child": 1,
      "max_bytes_per_child": 1048576
    }
  ]
}
```

计划可以携带完整 secretless `route_snapshot`，也可以只携带 route ID/revision，由创建命令从当前设置解析。API Key 仍只从本地凭据引用解析，不进入计划、父授权、子 consent、MCP 参数或文档。
## 分块 ASR 的批量派生入口

更新：2026-07-23 03:57:04 +08:00，Codex / GPT-5.6。

当父授权的某一 stage 已锁定 `cloud_asr`、允许 producer `asr_vad_chunking`，且调用/文件/字节/费用上限覆盖全部 chunk 时，不必逐块运行 child-consent 命令：

    .\scripts\video-knowledge.ps1 asr-chunk-business-workflow <chunk-manifest.json> <business-authorization.json> --stage-id <stage-id> --producer asr_vad_chunking --lineage-input <exact-source-media>

VKP 仍为每个 chunk 生成独立 consent v2；该入口只批量复用同一个已确认父授权并编译既有 Broker workflow。它不提交任务、不读取密钥、不调用 provider。重复运行只复用 identity 完全相同的已有 child consent；新的文件、hash、route、stage、producer 或超出预算仍会阻断。
