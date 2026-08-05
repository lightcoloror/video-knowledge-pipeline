# VKP 混合模型网关实施与验收记录

- 状态：阶段 0–5 代码与离线验收完成；阶段 6 清理等待真实 smoke
- 时间：2026-07-15 04:05:16 +08:00
- 执行者：Codex / GPT-5
- 对应 ADR：`docs/decisions/2026-07-14-hybrid-model-gateway.md`

## 实施结果

| 阶段 | 状态 | 结果 |
|---|---|---|
| 0 可信基线 | 完成 | 保留既有提交与工作树，扫描本次差异中的常见明文密钥模式为 0；未 reset/stash/checkout/push。 |
| 1 路由控制面 | 完成 | v2 profile、严格分离的 local/remote pool、内容寻址 route revision/virtual model、v1 迁移备份、secretless LiteLLM 配置和 render/doctor/status/start 已落地。默认端口候选为 `127.0.0.1:8776`；doctor 要求精确端口归属、监听/bind，并拒绝没有通过 LiteLLM HTTP 健康探针的占端口进程。 |
| 2 Consent v2 | 完成 | 多 deployment、route snapshot hash、目的地集合、精确 artifact hash、有效期/调用数和原子 reservation 已覆盖；temporal consent 按父目录帧组逐组预留/执行；远程 Proxy 只能在 Broker grant 上下文中联网。 |
| 3 文本与视觉 | 完成 | 生产入口经统一客户端到 Proxy，legacy 保留为显式模式；单帧、temporal、Smart Summary 继续由原业务模块写回现有 schema。 |
| 4 ASR 与 OCR | 完成 | ASR 使用 `/v1/audio/transcriptions` 并保留 raw response；在线 OCR 使用 `/v1/ocr`、逐 artifact 计数并规范化 candidate evidence；本地 ebook Markdown OCR 保持原路径。 |
| 5 UI/安装/验收工具 | 完成 | UI 可配置位置、能力、池、默认位置、revision、健康、费用未知、consent/allowlist，并固定提示“保存配置不等于授权外发”；core/online/local/hybrid extras 和离线 A/B/C 工具已覆盖。 |
| 6 清理重复实现 | 未执行（按设计） | 真实本地 VLM、Speaches 与每类远程 smoke 尚需操作者单独授权；在全部门槛满足前不 deprecated/删除 legacy。 |

## 安全与运行边界

- 本地池失败返回 `local_gateway_unavailable`，不切换远程池，并报告 `remote_requests_made=false`。
- 远程 Proxy 执行必须同时匹配 Broker allowlist、consent ID、route revision 和 reservation 调用额度；调用者仅传 `consent_id` 不能取得联网权。
- Provider API Key 由 DPAPI 解密后只注入 LiteLLM 子进程环境；生成 YAML、Bundle、日志和 MCP 参数均不保存明文。网关 master key 仅由本地客户端读取后用于 loopback Authorization，不进入生成配置或产物。
- 本地图片由 VKP 校验路径和 allowed roots 后临时编码为完整 MIME data URL；裸 base64、无协议路径和临时编码正文不进入日志、Bundle 或聊天历史。
- Broker 的通用执行结果保持为审计 runtime result；现有任务模块/导入门负责 Timeline、Bundle、Smart Summary、ASR 与 OCR candidate evidence 的规范化写回，模型输出不会绕过质量门直接提升为事实。
- 本轮未启动 LiteLLM、Docker、计划任务或本地模型服务；未调用真实外部 API，未上传图片、音频或文档，未写 Obsidian。

## 离线验证证据

| 检查 | 结果 |
|---|---|
| 路由 profile 必填、v2 池与 revision | `10 passed` |
| UI/安装/consent/Broker/fake loopback/A-B-C 工具 | `76 passed` |
| 任务覆盖审计 | 16 total；15 unified；1 deferred（native whole-video）；0 contract drift |
| `python -m compileall -q src` | 通过（使用独立临时 pycache 避开旧 Windows ACL） |
| 网关/Broker/consent/A-B-C 定向回归 | `46 passed` |
| Ruff（本轮源文件与测试） | 通过 |
| 完整回归第 1 轮 | `697 passed, 1 warning` |
| 完整回归第 2 轮 | `697 passed, 1 warning` |
| 明文密钥模式扫描 | `sk-*` / `AKLT*` / `AIza*` / 长 Bearer：0 命中 |

唯一 warning 来自既有 `jieba` 对 `pkg_resources` 的弃用提示，不是本次网关回归。

## 固定 temporal 样本

- Bundle：`openclaw-runs/getbrain-acquisition-20260708/1-首次沟通环节的高频问题/full-vkp-quality-20260713/webui-bundle`
- Indexes：`6, 80, 112, 135, 199, 201`
- 帧完整性：`6/6` 组就绪，每组 `8/8`，失败 `0`
- Timeline 结构化 temporal 写回：`6/6`，全部 `validation_status=ok`
- Smart Summary：存在且写入时间晚于 Timeline
- 本地验收清单：`exports/temporal-gateway-acceptance-manifest.json` 与 `.md`
- A/B/C 状态报告：`exports/model-gateway-acceptance/model-gateway-abc-comparison.json` 与 `.md`

A/B/C 状态当前为 `incomplete`，因为 lane A legacy、lane B Proxy remote、lane C Proxy local 的真实结果文件尚未生成。该状态是操作者授权门禁，不是自动测试失败，也不会用旧的“视觉证据层 A/B/C”报告冒充模型网关 A/B/C。

## 真实 smoke readiness

稳定检查入口：

```powershell
video-knowledge-model-smoke-readiness <webui-bundle> --indexes 6,80,112,135,199,201
```

2026-07-15 04:05:16 的实际状态是 `configuration_required`：配置 profile `0`、route `0`，六项路线就绪 `0/6`，四份远程 consent 就绪 `0/4`；`127.0.0.1:8776` 未登记、未监听但可 bind；固定 temporal 样本仍为 `6/6`。报告位于 `exports/model-gateway-acceptance/model-gateway-smoke-readiness.json` 与 `.md`。该检查确认 `remote_requests_made=false`，没有启动服务、调用模型、上传 artifact、创建 consent 或写端口记录。

固定 temporal 远程验收采用一份 consent 精确覆盖 6 个父目录帧组的 48 帧，`max_calls=6`。Broker 每组独立调用并将调用数、成功数、失败组、usage、费用和 evidence 聚合为统一 runtime result。操作者完成 lane 执行后使用 `video-knowledge-model-acceptance capture-lane` 写入 A/B/C 固定文件，再运行离线比较。

## 剩余操作者门槛

1. 启动并 smoke 一次现有 OpenAI-compatible 本地 VLM。
2. 启动并 smoke 一次现有 Speaches/OpenAI-compatible ASR。
3. 对文本、视觉、ASR、OCR 分别创建有效远程 consent 并执行一次授权 smoke。
4. 为固定 6 组 temporal 样本生成 lane A/B/C runtime result，再运行离线比较器。
5. 只有上述结果、Bundle/Timeline/质量门无回归且完整测试仍连续两次通过，才进入阶段 6。

## Update Record

### 2026-07-15 02:42:54 | Codex / GPT-5

- Action：记录混合模型网关阶段 0–5 的实际实现、离线证据、固定 temporal 样本和阶段 6 操作者门槛。
- Boundary：没有真实模型或外部 API 调用，没有数据外发，没有服务/端口/Obsidian 变更。

### 2026-07-15 03:10:34 | Codex / GPT-5

- Action：新增真实 smoke readiness 阶段机、稳定 CLI、精确端口归属和 live-listener HTTP 健康门；实测固定 Bundle 的当前缺口。
- Result：路线 `0/6`、consent `0/4`、temporal `6/6`、A/B/C `incomplete`；剩余工作由操作者配置和单独授权门控制。
- Boundary：未启动网关或模型服务，未调用真实 API，未外发文件，未更新端口登记或 Obsidian。

### 2026-07-15 03:52:28 | Codex / GPT-5

- Action：完成 temporal 六组独立 consent 调用、统一聚合结果、A/B/C lane 捕获及精确覆盖 readiness 门禁。
- Verification：定向 `46 passed`；compileall 与 Ruff 通过；完整回归连续两次均为 `695 passed, 1 warning`；secret pattern 命中 0。
- Remaining：真实 profile/route `0/6`、远程 consent `0/4`、A/B/C lane `0/3`；必须由操作者完成服务配置与分别授权，阶段 6 仍未执行。

### 2026-07-15 04:05:16 | Codex / GPT-5

- Action：将 LiteLLM live health 收紧为仅接受 2xx，并让 start 对不健康占端口进程 fail closed。
- Verification：健康门定向 `18 passed`；最终完整回归连续两次 `697 passed, 1 warning`。
- Boundary：readiness 仍为 `configuration_required`；未启动服务、未调用模型、未写端口/Obsidian。

### 2026-07-15 04:24:34 | Codex / GPT-5

- Action：把混合网关与 smoke readiness 稳定入口登记到本地工具注册表，并为本地 VLM/Speaches 共用同一 origin 增加显式配置警告。
- Rationale：现有示例默认都指向 `127.0.0.1:8000`；只有同一服务确实同时实现 chat completions 与 audio transcriptions 时才应共用，否则由操作者配置不同端口，VKP 不猜测运行地址。
- Verification：定向 `6 passed`；Ruff 与 compileall 通过；完整回归连续两次均为 `699 passed, 1 warning`。固定 Bundle readiness 仍为路线 `0/6`、consent `0/4`、temporal `6/6`、A/B/C `0/3`，`remote_requests_made=false`。
- Boundary：该警告不阻断有意部署的统一服务；没有启动服务、探测模型能力、调用模型、外发数据或写端口/Obsidian。

### 2026-07-15 09:46:59 | Codex / GPT-5

- Action：完成“旧配置安全导入”入口与本机首次导入；从已核验旧产物生成 `remote-ark` 文本/视觉 profile 和 `local-qwen-vl` 视觉 profile。
- Result：profile `2`、route pool `3`、task binding `7`；Ark 密钥仅以 DPAPI ciphertext 持久化。Agnes、旧快照与 2 份旧 consent 未导入，ASR/OCR 保持待配置。
- Readiness：导入后 profile `2`、route status `11`、六项能力路线 `1/6`、远程 consent `0/4`、temporal `6/6`、A/B/C `0/3`；远程 Ark allowlist 在当前检查进程中为 `unknown`，本地 VLM 仍未执行真实服务 smoke。
- Verification：新增导入测试 `7 passed`，与现有网关联合回归 `20 passed`，完整回归补强前连续两次均为 `705 passed, 1 warning`；新增写后验证回滚用例后最终为 `706 passed, 1 warning`；明文泄漏检查为 `False`，`remote_requests_made=false`。
- Boundary：没有启动服务、调用模型、外发 artifact、创建 consent、修改端口登记或写 Obsidian。

### 2026-07-15 13:15:34 | Codex / GPT-5

- Action：完成统一 Provider Catalog、通用 LiteLLM-native 扩展、远程文本/视觉/ASR/OCR 目录、本地 OpenAI-compatible/Speaches profile，以及 Broker/UI 的能力发现。
- Result：35 个 profile；能力索引为 text `25`、vision `23`、ASR `8`、OCR `3`。预置 prefix 锁定；通用 prefix、模型、Base URL 或能力变化都会改变 route revision 并使旧 consent 失配。
- Broker：`model_connector_capabilities` 返回 catalog revision 和每任务 `provider_profile_ids`；执行接口仍不接收任意 URL/Key。
- Cross-project：只读核对视频创作侧 edit-job v3/provider handoff；VKP consent v2 继续是 provider、route、任务、额度和 upload manifest 的唯一授权真源。
- Verification：定向 `99 passed`；Ruff、compileall、secret pattern 0 命中、`git diff --check` 通过；完整离线回归 `722 passed, 1 warning`。
- Remaining：真实 profile 账户/模型名/价格、local VLM、Speaches、四类远程 smoke 和 A/B/C lane 仍需操作者逐项授权；阶段 6 未执行。
- Boundary：未调用真实外部 API、未上传视频帧/音频/文档、未启动 Docker/计划任务、未修改端口登记、未写 Obsidian。

### 2026-07-15 14:35:19 | Codex / GPT-5

- Action：Provider Catalog 从 35 扩展到 41 个 profile，新增 Azure/Vertex/AWS 高级认证与网关 credential blockers。
- Route：认证模式、非密钥 provider options、必需参数和环境绑定名均锁入 deployment identity 与 consent v2；配置变化会生成新 revision。
- UI：显式编辑 allowlisted provider options，并只显示外部环境变量名/就绪状态；不回显环境值。
- Cross-repo：新增 `video-knowledge.ps1 execute-consented-model-task <consent> --route-revision <revision> --write`，视频创作侧无需私有 import 或复制授权逻辑。
- Exit codes：`0` completed，`1` execution failed，`2` blocked，`3` invalid；handled result 始终输出完整 JSON。
- Boundary：本轮没有启动 LiteLLM/本地模型、调用真实 API、上传文件、修改端口或写 Obsidian。

### 2026-07-15 14:47:20 | Codex / GPT-5

- Checkpoint：高级认证与跨仓 consent execute CLI 已完成，失败 `0`。
- Provider：Catalog `41`；能力索引 text `29`、vision `27`、ASR `10`、OCR `5`。
- CLI：完整 JSON stdout；退出码 `0/1/2/3` 分别为 completed/execution_failed/blocked/invalid；缺失 consent 实测返回 `3` 且 `remote_requests_made=false`。
- Registry：`%WORKSPACE_ROOT%\tool-registry.json` 已登记 `cli.consent_execute`；`AGENT_DISCOVERY.md` 已登记同一命令与边界。
- Verification：联合离线回归 `51 passed`；完整回归 `731 passed, 1 warning`；Ruff、compileall、JSON、`git diff --check` 通过。
- Warning：仅既有 jieba/pkg_resources 弃用提示，与本轮无关。
- Boundary：真实模型/API 调用 `0`、上传文件 `0`、发布 `0`、自动 fallback `0`；未启动 LiteLLM、本地模型、Docker 或计划任务，未写 Obsidian，未 push。

## 2026-07-18 生产线上链路补强

- 新增生产预设 `online-production-existing-apis-v1`，复用既有 DPAPI `secret_ref`，不要求重新填写 API Key。
- 任务映射：ASR → Groq Whisper Large V3 Turbo；OCR → Mistral OCR 4；PPT/文档视觉 → SiliconFlow PaddleOCR-VL 1.5；单帧语义 → SiliconFlow GLM-4.1V-9B-Thinking；temporal、通用文本、摘要改写、转录纠错 → Google Gemini 3.5 Flash。
- 9 个 task binding 收敛为 6 个单 deployment pool；fallback chain 为 0；Coding Plan profile 不进入 VKP 生产内容路由。
- LiteLLM Proxy 从 `127.0.0.1:8776` 迁移到 `127.0.0.1:18776`。本机 Windows 动态 TCP client range 为 `1024-15000`；doctor 新增动态区间门，避免出站 socket 再占用服务端口。
- 端口真源已追加 18776；旧 8776 标记为 VKP 退役端口。
- 网关渲染错误现在返回 `configuration_blocked` / `route_render_failed` JSON，不再抛出未处理 traceback。
- 新增仓库稳定前门：`scripts\video-knowledge-model-gateway.ps1` 与 `scripts\video-knowledge-model-smoke-readiness.ps1`，不依赖 console script 已安装。
- online-only readiness 审计 8 类在线任务；本地 VLM/Speaches 不再阻塞纯线上验收。Groq/Mistral/OpenAI-compatible ASR 均可进入代表性 consent 路由识别。

### 本地运行验证

| Checkpoint | Result |
|---|---|
| 生产路由 | `8/8` online task routes ready |
| Gateway | `127.0.0.1:18776` live + HTTP health ready；6 virtual models；0 fallback；0 credential blockers |
| Broker | `127.0.0.1:8766` live；MCP smoke `7 tools` passed |
| Temporal sample | `6/6` groups；每组 `8/8` frames |
| Remote consent | `0/4`；状态准确停在 `operator_consent_required` |
| A/B/C | online lane B 尚未执行；A/C 不作为 online-only 阻塞项 |
| Tests | targeted `56 passed`；full `858 passed, 1 warning`；compileall/Ruff passed |
| Remote calls/uploads | `0/0` |

就绪证据：`openclaw-runs/getbrain-acquisition-20260708/1-首次沟通环节的高频问题/full-vkp-quality-20260713/webui-bundle/exports/model-gateway-acceptance/model-gateway-smoke-readiness.json` 与 `.md`。下一步必须先为文本、temporal 视觉、ASR、OCR 生成精确 route-revision consent；本轮没有创建 consent、调用模型或上传 artifact。

### 2026-07-18 22:48:45 | Codex / GPT-5

- Action：补强生产路线、动态端口门、结构化启动失败、稳定 PowerShell 前门和 online-only 整链审计。
- Verification：目标回归 `56 passed`；完整离线回归 `858 passed, 1 warning`；compileall/Ruff/diff check 通过；Gateway/Broker 本地健康；8/8 在线路线；6/6 temporal；停在 0/4 consent。
- Boundary：未调用任何在线模型，未上传帧、音频、文档，未创建 consent，未 push。

### 2026-07-19 00:45:50 | Codex / GPT-5

- Action：依据 `online-production-e2e-consent-plan-20260718.json`（26225 bytes，SHA-256 `9e3cd0432780d79ca82ea91d9839cdc97a587416aee4e50430282fa3861cb743`）完成生产线上链路真实验收；51 个精确文件只发送至 Google、Groq、Mistral 三个获授权目的地。
- Execution：文本 1 次（Gemini 3.5 Flash）、6 组 temporal 6 次（Gemini 3.5 Flash）、ASR 1 次（Groq Whisper Large V3 Turbo）、OCR 1 次（Mistral OCR 4）；合计 `9/9` 完成、失败 `0`、重试 `0`、fallback `0`，四类任务均通过 transport、contract、quality gate 与 production qualification。
- Writeback：temporal 在线结果作为 Lane B candidate evidence 保存，既有 6/6 `codex_manual_multiframe_review` 未被覆盖；Mistral OCR 通过精确 upload manifest 与显式 index 写入 Timeline 6；Smart Summary input pack 已刷新且质量状态 `passed`。
- Fix：在线 OCR 导入现在可在已审核 Timeline 行不再属于 unresolved candidates 时，用精确 artifact path/bytes/SHA-256 和显式 index 安全回绑；有实际导入时 run registry 状态为 `completed`。
- Cost：供应商响应没有返回可核实的实际费用；consent 台账保守提交 1.00 美元授权上限，该数字不是实际扣费证据。
- Evidence：`exports/model-gateway-acceptance/online-production-e2e-20260719.json` 与 `.md`；Lane B 为 `exports/model-gateway-acceptance/lane-b-proxy-remote.json`。
- Verification：定向 `23 passed, 1 warning`；变更文件 Ruff 通过；compileall 与 diff check 通过；完整回归最终 `859 passed, 1 warning`。全仓 Ruff 仍有 `955` 项既有 lint 债务，不纳入本次修复范围。
- Remaining：A/B/C 仅 Lane B 已捕获，legacy Lane A 与本地 OpenAI-compatible Lane C 尚未完成固定样本比较。
- Boundary：没有自动发布、未列明文件上传、静默 local/cloud fallback、secret 输出、Obsidian 写入或 push。
