# VKP 混合模型网关实施说明

- 更新时间：2026-07-15 04:05:16 +08:00
- 执行者：Codex / GPT-5
- 决策依据：`docs/decisions/2026-07-14-hybrid-model-gateway.md`
- 当前阶段：阶段 0–5 的代码与离线测试已实现；阶段 6 清理尚未启用

## 已实现的运行结构

```text
VKP task / UI / Broker
        |
model_runtime_client
        |
LiteLLM Proxy (127.0.0.1:8776)
        |
  local-only pool     remote-approved pool
```

- `model_api_settings.py` 使用 `local_model_api_settings.v2`，profile 明确声明 `location` 与 `capabilities`。
- `route_pools` 保存有序 deployments 与 retry/timeout/cooldown 策略；本地和远程 profile 不能混入同一池。
- `route_bindings` 为每类任务保存默认位置、本地池和远程池。
- v1 设置只读迁移为单成员池；保存 v2 前保留旧文件备份。旧 profile 默认 `legacy`，新 profile 默认 `proxy`。
- virtual model 采用 `vkp-{location}-{capability}-{pool_slug}-{route_revision_sha12}`；路由内容变化会改变 revision。
- `model_runtime_client.py` 统一文本、视觉、ASR、OCR 结果 schema，并只访问固定 loopback LiteLLM Proxy。
- 本地图片/文档先校验 allowed roots，再在请求内存中临时编码为完整 MIME data URL；data URL、裸 base64 与无协议路径不会写入 Bundle、日志或结果。
- ASR 使用 `/v1/audio/transcriptions`，OCR 使用 `/v1/ocr`，文本与视觉使用 `/v1/chat/completions`。
- 原始 ASR provider 响应保留为 `raw_output`；OCR 每个图片/文档独立计数并保留来源 hash 与 candidate evidence。

## Consent v2 与 Broker

Consent v2 锁定：

- `authorized_deployments[]` 中每个 provider、model、Base URL、协议与目的地；
- `route_id`、`route_revision`、virtual model 与路由快照 SHA-256；
- artifact 精确路径、大小、SHA-256、任务、提示、调用次数和有效期。

创建 route-based consent 时，CLI 必须同时提供当前 `route_id` 与完整 `route_revision`；在写 consent 前校验远程池全部 deployment 的 Broker allowlist。v1 consent 继续作为单 deployment 授权读取，不重写旧文件。

固定 temporal 验收使用一份 consent 精确覆盖所选各组的全部帧，`max_calls` 等于组数。Broker 按父目录帧组逐组执行、逐组预留/完成计数，并生成统一 runtime 聚合结果；本地 VLM 使用相同的分组契约，但不需要远程导出 consent。

Secure MCP Broker 的远程主执行接口只接受：

```text
execute_consented_model_task_tool(consent_path, route_revision)
```

它不接收 Agent 提交的 provider URL 或 API Key。旧 semantic/temporal 工具仅允许已保存的 singleton `legacy` 路由，并同样要求 route revision；多 deployment 或 Proxy 路由必须使用 consent v2 主接口。本地接口只允许 loopback route：

```text
execute_local_model_task_tool(task, artifact_paths, route_id)
```

Secure MCP Tunnel 只把 Broker 暴露给平台，不扩展目的地白名单，也不覆盖 Agent 平台策略。

## 配置和启动

设置 UI：

```powershell
.\scripts\start-model-api-settings.ps1
```

UI 可配置 profile 位置/能力、local/remote pools、deployment 顺序、每任务默认位置，并展示 route revision、健康状态、最后检查时间、费用未知状态、consent 与 allowlist 状态。页面固定显示“保存配置不等于授权外发”。API Key 使用本机 DPAPI 持久化且不回填。

模型网关命令：

```powershell
video-knowledge-model-gateway render-config
video-knowledge-model-gateway doctor
video-knowledge-model-gateway status
video-knowledge-model-gateway start          # 预览
video-knowledge-model-gateway start --execute
video-knowledge-model-smoke-readiness <webui-bundle> --indexes 6,80,112,135,199,201
```

默认地址为 `127.0.0.1:8776`。启动执行前检查端口登记、实时监听和真实 bind；端口记录必须是精确端口且同一行归属 `VKP LiteLLM Proxy`。如果端口已有监听，doctor 还必须通过 LiteLLM HTTP 健康探针，任意占端口进程不会被误判为网关。生成的 LiteLLM YAML 只引用环境变量；DPAPI 明文只进入子进程环境。telemetry 默认关闭，不使用数据库、Docker 或计划任务。

`video-knowledge-model-smoke-readiness` 是纯检查入口，状态依次为 `configuration_required`、`operator_start_required`、`operator_consent_required`、`operator_smoke_required`、`ready_for_final_review`。它不会启动网关、调用模型、上传文件、创建 consent 或写端口记录。

Route-based consent 示例：

```powershell
.\scripts\model-connector-consent.ps1 create <approved-run-dir> `
  --task temporal_visual_analysis `
  --artifact <frame-01.jpg> `
  --artifact <frame-02.jpg> `
  --route-id <remote-pool-route-id> `
  --route-revision <full-route-revision> `
  --max-calls 1 `
  --confirm-data-export
```

`route_id` 和 `route_revision` 从设置 UI 的 route 状态读取。配置或任一 deployment 改变后，旧 consent 会在联网前被拒绝。

## 安装矩阵

| Extra | 内容 |
|---|---|
| `core` | VKP 业务管线，不含 LiteLLM Proxy 或模型权重 |
| `local` | 与 core 相同的客户端契约；本地模型服务由操作者管理 |
| `online` | `litellm[proxy]>=1.81.7,<2` |
| `hybrid` | online + local 配置能力，不复制业务代码 |

## A/B/C 与固定 temporal 样本

离线比较命令只读取保存的结果 JSON，不调用模型或读取源媒体：

```powershell
video-knowledge-model-acceptance capture-lane `
  --lane B `
  --input <connector-execution.json> `
  --output-dir <report-dir>

video-knowledge-model-acceptance compare `
  --a <legacy-result.json> `
  --b <proxy-remote-result.json> `
  --c <proxy-local-result.json> `
  --output-dir <report-dir> `
  --sample-id <id>
```

输出比较 schema、质量门、延迟、调用数、费用和失败恢复。模型内容只转成 hash/字节数，不复制进比较报告。

6 组既有 temporal 样本已完成本地清点：indexes `6,80,112,135,199,201`，每组 `8/8`；Timeline 当前结构化写回 `6/6`、验证失败 `0`。本地验收清单：

```text
openclaw-runs/getbrain-acquisition-20260708/1-首次沟通环节的高频问题/full-vkp-quality-20260713/webui-bundle/exports/temporal-gateway-acceptance-manifest.json
```

清单只含本地路径、大小和 SHA-256，模型调用数为 0，上传数为 0。它不是自动化远程测试；B 路线真实远程视觉验收仍需单独有效 consent 与操作者授权。

## 测试边界与剩余门槛

自动测试使用 fake loopback HTTP 服务，覆盖文本、单图、多图、ASR、OCR、非法图片输入、越界文件、route 篡改、429/5xx、超时、部分 OCR 页失败、UI 与安装矩阵。测试不会调用真实外部 API。

阶段 6 暂不执行，旧适配器不会删除。仍需操作者单独完成：

- 一次本地 VLM smoke；
- 一次本地 Speaches smoke；
- 文本、视觉、ASR、OCR 每类至少一次远程 consented smoke；
- 用真实 A/B/C 结果生成最终比较报告；
- 如需更新 Obsidian 端口记录，单独明确授权。

在这些 smoke 与完整测试连续两次通过前，legacy 兼容实现仅保留，不标记删除。

## Update Record

### 2026-07-15 01:21:45 | Codex / GPT-5

- 实现路由设置 v2、LiteLLM 控制面、统一运行时客户端、consent v2、Broker 路由收口、ASR/OCR 标准端点、设置 UI、安装矩阵与 A/B/C 离线验收工具。
- 保留本地 ebook Markdown OCR 及其 PPT 文本/热词的只读消费路径。
- 未执行真实远程调用、Docker、计划任务、外部写入或 Obsidian 更新。

### 2026-07-15 01:42:06 | Codex / GPT-5

- Validation：改动模块离线回归 `80 passed`；最终完整回归连续两次均为 `669 passed, 1 warning`。
- Static checks：设置 UI JavaScript 语法、改动 Python AST、`python -m compileall -q src`、`git diff --check` 全部通过。
- Secret scan：扫描 29 个改动/新增文件，明文密钥模式命中 0。
- Temporal evidence：6/6 组 ready、每组 8/8 帧；Timeline 结构化写回 6/6、validation failure 0；未调用模型、未上传。

### 2026-07-15 03:10:34 | Codex / GPT-5

- 增加真实 smoke readiness 审计入口和稳定 CLI，显式检查六条路线、远程 allowlist/凭据、精确端口归属、LiteLLM 健康、四份 consent 与 A/B/C lane 文件。
- 当前实测为 `configuration_required`：路线 `0/6`、consent `0/4`、固定 temporal 样本 `6/6`，网关未监听且未登记；没有启动服务、调用模型、上传数据或写端口记录。

### 2026-07-15 03:33:38 | Codex / GPT-5

- temporal consent 现在按帧组独立预留与执行；固定 6 组必须精确覆盖 48 帧并保留 6 次可用额度，避免把全部帧静默合并成一次请求。
- 增加离线 `capture-lane`，严格校验 A=remote legacy、B=remote proxy、C=local proxy 后写入固定 lane 文件；完整回归连续两次均为 `695 passed, 1 warning`，Ruff 与 compileall 通过。

### 2026-07-15 04:05:16 | Codex / GPT-5

- 网关健康探针只接受 2xx；`start --execute` 遇到已占用但不健康的端口返回 `port_blocked`，不再把通用 404 服务误判为 LiteLLM。
- 最终完整离线回归连续两次均为 `697 passed, 1 warning`；真实服务、API 与数据外发均未执行。
