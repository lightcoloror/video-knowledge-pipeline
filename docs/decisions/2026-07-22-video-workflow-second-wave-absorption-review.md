# VKP 视频工作流第二批吸收审核与排期

- 状态：Implemented（P0/P1/P2 已实施；focused 验收通过；全仓剩余 3 项与本轮无关的并发改动失败）
- 日期：2026-07-22
- 执行者：Codex / GPT-5.6
- 适用仓库：`%WORKSPACE_ROOT%\video-knowledge-pipeline`
- 依据交接：`%WORKSPACE_ROOT%\docs\codex-session-index\handoffs\20260722-vkp视频工作流第二批吸收待发送\VKP待吸收交接.md`

## 决策摘要

VKP 应吸收人工确认失效、内容寻址新鲜度、生成能力证据展示和 3D 预演候选回流，但不应吸收第二套生成队列、项目数据库、审核服务、FFmpeg、ASR、Timeline 或 provider gateway。

本轮采用以下总原则：

1. 优先复用固定 commit 的成熟开源模块和视频创作侧已实现契约；没有经过源码核对的模块不得进入实施排期。
2. 能以 JSON 契约和稳定 CLI 消费的能力，不复制实现、不做私有 Python import。
3. VKP 继续以 Timeline、Bundle、run registry、Workbench 和现有审核回流为真源。
4. 远程操作继续经过 VKP provider gateway、allowlist 和 consent；本决策不扩大数据外发权限。
5. 3D 预演、生成回执和代表帧都是 derived candidate evidence，不是已观察到的视频事实。

## 固定上游源码证据

| 项目 | 固定 commit | 许可证 | 已核对源码模块 | 本轮使用方式 |
| --- | --- | --- | --- | --- |
| 灵剪 `dososo/blcaptain-lingjian-video` | `5c2c77b319117de6f15211349ebbe462d3b40384` | Apache-2.0 | `packages/core/approvals.py`：`approve_target()`、`validate_render_gate()`、规范化摘要、实际音频摘要、审批失效 | 复用“确认绑定内容摘要、使用前重新计算、变化即 stale”的机制；不引入其项目状态、HMAC 密钥、Provider、渲染或审核文件真源 |
| Codex Storyboard `Yuuhann1999/codex-storyboard` | `ac9057dee3a903eb211d8399a439ae9992e7656a` | MIT | `plugins/codex-storyboard/skills/process-storyboard-tasks/SKILL.md`：claim 前 capability 检查、禁止隐式安装、固定 generator、技术探针、代表帧检查、显性失败 | 复用可见失败与生成验收语义；不引入其项目数据库、本地服务器或单进程任务队列 |
| StoryAI 3D Director Desk `jiguang132/storyai-3d-director-desk` | `8c8bd361790be4d37158a7430365e65546e358fe` | MIT | `directorProject.ts`、`cameraGeometry.ts`、`captureBridge.ts`：camera id、FOV、position、target、capture request | 只复用相机意图和截图元数据；不引入编辑器运行时，不允许 `localStorage` 或 data URL 成为 VKP 真源 |
| 视频创作侧契约实现 | `27acddc` | 仓内代码 | `creative_gates.py`、`generation_contracts.py`、`previs_contracts.py`、`contract_io.py`；48 个测试通过 | 优先直接消费 `approval_record.v1`、`generation_task.v1`、generation receipt、`previs_scene.v1` 和 capture manifest；VKP 不复制其状态机或生成执行器 |

本地固定源码均已存在，无需重新下载。实施前若上游 commit 改变，必须重新做源码差异审查，不能沿用本文件的结论。

## VKP 当前能力盘点

### 可直接复用

- `storage.py` 已提供临时文件加 `os.replace` 的原子 JSON 写入和 Bundle 写锁。
- `artifact_validation.py` 已提供 allowed-root、本地路径和 SHA-256/字节数证据。
- `review_writeback.py` 与 `review_session.py` 已提供 candidate-bound 人工纠错、审核备注校验、原子回流和非破坏性写回。
- `knowledge_note_export.py` 已有 canonical transcript SHA-256 硬门，可作为通用内容寻址新鲜度的仓内先例。
- `run_artifact_registry.py`、`task_console.py`、`video_workbench.py` 已是任务、产物、失败项和人工动作的统一展示面。
- `vision_preflight.py` 已有 provider 能力检查、预期调用数、显式确认、失败阻断和密钥脱敏。
- `media_capability_registry.py` 已明确本地/远程能力、GPU 要求、candidate-only、禁止自动下载和禁止 silent local/cloud fallback。
- `video_edit_review_pack.py` 已要求 active edit decisions 必须来自用户或带 `confirmed=true`，并在 artifact validation 不通过时阻断单一 FFmpeg/render handoff。
- `scene_candidate_evidence.py`、`shot_breakdown.py`、`video_structure.py` 等已形成 candidate-only 与字段级 provenance 先例。

### 已确认缺口

1. `review-notes.json` 和 Timeline 上的确认状态没有通用不可变 attestation，未绑定确认时的精确依赖 artifact 集合；上游输入变化后不能统一说明哪项确认失效。
2. `run_artifact_registry.py` 当前 artifact row 只记录路径和是否存在，不记录字节数、SHA-256、依赖快照或 stale 原因。
3. `acceptance_check.py` 的知识导出新鲜度主要依据文件 mtime；它能发现部分变更，但不足以作为 Bundle/export/render 的内容寻址硬门。
4. VKP 没有生成任务专用队列或 receipt 校验器；这是有意边界，不应通过复制 Codex Storyboard 来补齐。
5. Task Console/Workbench 目前能显示视觉 preflight 和一般 run artifacts，但没有统一展示视频创作侧 generation preflight、技术探针、代表帧和人工检查结果。
6. VKP 没有 `previs_scene.v1` 导入层，也没有独立“预演候选”展示通道。

## P0：人工确认失效语义

### 判断：adapt / P0

复用灵剪 `approvals.py` 的内容摘要与使用前复核机制，复用视频创作侧 `approval_record.v1` 的文件 SHA-256、规范化 JSON SHA-256、附件和操作者绑定方式；在 VKP 内只增加一个薄的 attestation 适配层。

### 建议落点

- 新增 VKP 自有 `video_knowledge_pipeline.review_attestation.v1`，而不是把视频创作侧审批文件复制成 VKP 第二真源。
- attestation 引用现有 Bundle artifact，至少记录：相对路径、字节数、文件 SHA-256、可用时的规范化 JSON SHA-256、artifact role、确认对象、确认人、确认时间、评语和依赖快照摘要。
- 审核写回仍走 `review_writeback.py` / `review_session.py`；attestation 是现有人工状态的不可变证据，不创建第二审核服务。
- 校验时从当前 Bundle 重新计算依赖摘要。任何 Timeline、canonical transcript、Smart Summary、visual evidence、字幕仲裁或 active edit decision 的变化，都把依赖确认标为 `stale`，并列出发生变化的精确 artifact。
- Workbench 和 Task Console 只展示 `valid / stale / missing / invalid`、失效原因和重新确认命令。

### 拒绝项

- 不复制灵剪的项目级 HMAC secret。它证明同一项目内记录未被静默改写，但不等同于操作者身份认证；VKP 当前需求是内容完整性和可见人工确认。
- 不让 `review-notes.json`、浏览器 localStorage 或视频创作侧 approval 文件单独成为 VKP 真源。
- 不把普通证据生成全部阻断；硬门只放在导出、provider handoff、剪辑/生成交接和其他声明“可交付”的边界。

### 验收

- 已确认 artifact 原样时校验通过。
- 修改 Timeline、canonical transcript、Smart Summary、visual evidence 或 active edit decision 中任一依赖后，旧确认变为 stale。
- stale 状态明确列出 changed/missing artifacts，导出和 provider request 构建被阻断。
- 只有通过现有可见审核入口重新确认后才能恢复。

## P0：Bundle/export/render manifest 新鲜度硬门

### 判断：adapt / P0

复用灵剪 `validate_render_gate()` 和视频创作侧 `release_gate.v1` 的“当前内容重新计算”方式；复用 VKP `knowledge_note_export.py` 的 canonical hash 硬门，将 `acceptance_check.py` 的 mtime 棲测升级为内容寻址依赖快照。

### 建议契约

定义 `video_knowledge_pipeline.artifact_dependency_snapshot.v1`：

- `subject`：Bundle、export、clip/highlight manifest 或 render handoff。
- `inputs[]`：role、bundle-relative path、bytes、sha256、可选 canonical_json_sha256。
- `snapshot_sha256`：按稳定排序后的规范化 JSON 计算。
- `created_at`、`source_run_id`、`producer_schema`。
- 校验结果：`fresh / stale / missing / invalid`，以及逐 artifact 差异。

run registry 继续是索引，不允许 run/export/render manifest 自证。每次交付前都必须从磁盘和 Bundle manifest 重新计算当前摘要。

### 硬门位置

- `video-edit-review-pack` 的 ready-for-render/handoff 判断。
- 知识导出与 Bundle handoff。
- provider request / video creation edit job 的构建前门。
- 后续 clip/highlight/export/render manifest 的消费入口。

### 兼容策略

- 旧 Bundle 没有 snapshot 时标记 `missing`，允许继续本地分析，但不能声明当前 export/render 可交付。
- 保留 mtime 作为诊断提示，不再作为最终新鲜度真源。
- v1 run artifact schema 继续可读；新 schema 或扩展字段按兼容读取处理。

## P1：生成能力预检与生成证据进入 Task Console

### 判断：reuse + thin adapter / P1

生成任务、预检和回执由视频创作侧现有 `generation_task.v1` 与验证 CLI 负责。VKP 只消费验证后的契约、绑定来源 Bundle/shot/evidence hash，并登记到现有 run registry；不在 VKP 创建第二生成队列。

### 复用链路

1. 视频创作侧构建固定 generator 的 `generation_task.v1`。
2. capability preflight 必须在 claim 前完成；禁止隐式安装和 silent generator fallback。
3. 本地工具能力通过 `%WORKSPACE_ROOT%\tool-registry.json` 和 stable local-tools health check 提供；远程能力仍通过 VKP provider gateway/consent 的 capability receipt 提供。
4. 视频创作侧稳定 CLI 验证 generation receipt，包含尺寸、时长、流/codec 或可解码图片、代表帧、人工检查和 candidate-only 边界。
5. VKP 薄适配器只导入已验证 receipt 的摘要与精确 artifact hashes，注册 `generation_contract_import` run。
6. Task Console/Workbench 增加只读卡片：generator、preflight 状态/时间/探针方法、technical probe、代表帧、人工检查、失败原因和上游恢复命令。

### 状态映射

- capability 不可用：`blocked` / `needs_input`，不能 claim。
- 生成失败或技术探针失败：`failed` / `needs_retry`。
- 代表帧未人工检查：`needs_review`。
- 验证完成：仍为 candidate-only；不得等同于发布通过。

### 拒绝项

- 不引入 Codex Storyboard 的 server、项目数据库、任务队列和任意路径复制。
- 不复制视频创作侧 `generation_contracts.py` 为 VKP 私有实现。
- 不自动安装生成器，不把 image-gen 静默换成 HyperFrames/Remotion，反之亦然。
- 不因 Secure MCP Tunnel 可访问 Broker 就扩大 provider 或上传目的地。

## P2：3D 预演作为候选 temporal visual evidence

### 判断：defer，随后 thin import adapter / P2

P0/P1 完成后，消费视频创作侧已验证的 `previs_scene.v1` 和 capture manifest。VKP 不运行 3D 编辑器，只导入本地截图文件及其精确 SHA-256。

### 建议映射

- 新增独立 derived evidence sidecar，而非写入 observed Timeline 字段。
- 每条记录至少包含：source shot unit、scene id、camera id、FOV、position、target、frame width/height、capture path、capture SHA-256、source manifest SHA-256。
- 强制 `synthetic=true`、`candidate_only=true`、`observed_video_fact=false`、`timeline_writeback_allowed=false`。
- Workbench 使用独立“3D 预演候选”分组，避免与真实 temporal frames 混淆。
- 只有人工确认后才能进入拍摄/生成计划；即使确认，也不能倒写为原视频已发生的事实。

### 拒绝项

- 不接受 data URL、裸 base64 或 localStorage 状态作为正式 artifact。
- 不把 StoryAI 编辑器、Three.js runtime 或 camera state manager 引入 VKP 核心。
- 不覆盖 `temporal_visual_understanding`、Timeline、OCR、ASR 或人工确认事实。

## 复用 / 缺口 / 拒绝 / 延期总表

| 条目 | 判断 | 现有重合 | 需要补的最小增量 |
| --- | --- | --- | --- |
| 审批内容绑定和失效 | adapt / P0 | review writeback、candidate ID、原子写入、canonical transcript hash | 通用 review attestation 与依赖差异报告 |
| Bundle/export/render 新鲜度 | adapt / P0 | acceptance mtime gate、knowledge export canonical hash | 内容寻址 dependency snapshot 与交付硬门 |
| 生成 capability preflight | reuse / P1 | vision/model preflight、media capability registry、tool registry | 消费视频创作 generation contract，不复制队列 |
| 技术探针和代表帧 | reuse / P1 | run registry、Task Console、Workbench、artifact validation | generation receipt import/status card |
| 禁止 silent fallback | reuse / P1 | model gateway 和 media registry 已禁止跨池/本地远程 fallback | 将固定 generator 与失败原因显示到 UI |
| 3D 相机意图和截图 | defer / P2 | candidate evidence、shot breakdown、Workbench | previs sidecar import 和独立候选视图 |
| 第二 FFmpeg/ASR/Timeline/审核服务/provider gateway | reject | VKP 已有真源和前门 | 无 |
| StoryAI localStorage / data URL 真源 | reject | VKP 只接受合法本地文件路径 | 无 |
| Seelyn 闭源运行时、未签名分析工具 | reject | 无可信可复用源码 | 无 |

## 排期与依赖

### 阶段 A：P0.1 review attestation contract

- 先为精确 artifact 集合、canonical JSON、依赖快照、失效原因写离线 contract/fake fixture 测试。
- 在现有 `artifact_validation.py`、`storage.py`、`review_writeback.py` 上做薄适配。
- 增加 Workbench/Task Console 的 stale/missing 展示，不新建审核页面。
- 完成标志：修改已确认依赖必定使确认失效，且恢复只走现有人工入口。

### 阶段 B：P0.2 内容寻址 freshness hard gate

- 扩展 run artifact 记录的 bytes/SHA-256/dependency snapshot。
- 将知识导出、edit review handoff、provider request 构建切到内容摘要硬门。
- 保留旧 schema 只读兼容和 mtime 诊断。
- 完成标志：旧 export/render manifest 在输入改变后无法被当作 current。

### 阶段 C：P1 generation contract import

- 先固定视频创作侧稳定 CLI/JSON 契约版本和调用边界。
- 导入经验证的 generation task/preflight/receipt 摘要，登记现有 run registry。
- 在 Task Console/Workbench 展示探针、代表帧、人工检查和明确失败。
- 完成标志：能力不可用、技术失败、未检查代表帧均不能显示 completed。

### 阶段 D：P2 previs candidate import

- 在 P0 内容绑定可复用后再实现。
- 只导入本地截图文件和相机元数据，生成 candidate sidecar。
- 完成标志：独立显示来源和 synthetic 边界，Timeline/temporal facts 无变化。

阶段依赖为 A → B → C → D。P0 未完成前不接收会被误判为 current/approved 的生成或预演证据。

## 非功能要求与失败模式

| 维度 | 要求 | 失败时行为 |
| --- | --- | --- |
| 一致性 | 所有确认和交付状态都从当前磁盘 artifact 重新计算 | fail closed，列出 changed/missing artifact |
| 原子性 | 复用 `write_json` 和 Bundle write lock | 不留下半写 attestation/manifest |
| 可追溯性 | 固定 schema、source commit、文件 hash、run id、操作者动作 | 证据缺失则 `invalid` 或 `missing` |
| 兼容性 | 旧 Bundle 可读但不能假定 fresh/approved | 允许本地修复，不允许交付声明 |
| 安全 | 无自动上传、安装、发布或 fallback | 远程动作继续被 gateway/consent 阻断 |
| 可运维性 | 只扩展既有 Task Console/Workbench/run registry | 不新增端口、常驻服务或第二队列 |
| 证据语义 | generated/previs 是 candidate/derived，不是 observed fact | 禁止写回 Timeline 事实字段 |

主要失败模式：

- 文件内容变化但 mtime 未变化：由 SHA-256 复核发现。
- 路径存在但指向新内容：由 bytes/SHA-256 不匹配发现。
- run manifest 自称 fresh：忽略自证，从磁盘重新计算。
- 代表帧丢失或 hash 改变：receipt 变为 stale/invalid。
- generation tool 不可用：在 claim 前 blocked，不自动安装或换 generator。
- previs 只有 data URL/localStorage：拒绝导入，要求导出合法本地文件和 manifest。
- 多线程同时确认/刷新：使用既有 Bundle lock 和原子替换。

## 开源优先实施门

每个后续实现任务必须在编码前记录：

1. 固定上游仓库、commit、许可证和精确源码 symbol。
2. 为什么能直接复用、为什么只能薄适配，或为什么必须拒绝。
3. VKP 现有落点，证明没有创建第二套真源或状态机。
4. fake fixture、artifact mutation、stale、missing、并发写入和兼容测试。
5. 若找不到成熟实现，状态保持 `defer`；不得默认转为从零自研。

优先顺序为：直接调用稳定 CLI/读取版本化 JSON契约 → 复用纯函数/已验证模块 → 薄适配 → 明确 defer。禁止先写新框架再寻找复用理由。

## 后续授权边界

下列离线动作在用户要求进入实施后可在 VKP 工作区内完成：读取固定源码、编写 contract/adapter/UI 显示、fake fixture、离线测试和本地文档。

下列动作仍需用户单独明确批准：

- 下载或更新外部源码、安装依赖或模型。
- 启动新服务、登记或修改端口。
- 调用在线模型/生成器、上传任何文件或产生费用。
- 对真实媒体执行 render、FFmpeg 变更、NLE 导入或原地文件修改。
- 修改视频创作仓库或其他项目。
- push 到 GitHub、发布或写入 Logseq/Obsidian。

## 实施完成记录

更新时间：2026-07-22 11:44:11 +08:00
执行者：Codex / GPT-5.6

### 已实现

| 模块 | 状态 | VKP 落点 | 固定上游复用 |
| --- | --- | --- | --- |
| 内容寻址依赖快照 | implemented / adapted | `artifact_freshness.py`、`run_artifact_registry.py`、`knowledge_note_export.py`、`acceptance_check.py` | 灵剪 `validate_render_gate()` 的“当前内容重算”语义；VKP 既有 canonical hash、artifact validation 和原子写入 |
| 不可变人工确认及失效 | implemented / adapted | `review_attestation.py`、CLI/MCP 前门、`video_edit_review_pack.py` | 灵剪 `approve_target()`/失效语义；视频创作 `approval_record.v1` 的内容绑定思想；不复制审批服务或 HMAC 真源 |
| 剪辑交接新鲜度硬门 | implemented | `video_edit_review_pack.py` | 复用 VKP 既有 Bundle、run registry 和 artifact validation；没有新增 render/FFmpeg 状态机 |
| 生成 capability/receipt 导入 | implemented / thin adapter | `creative_contract_bridge.py`、CLI/MCP、run registry、Task Console/Workbench | 直接消费视频创作 commit `27acddc` 的 `generation_task.v1`、preflight、receipt、validation；上游校验继续由 `video-creative-contracts verify-generation-receipt` 负责 |
| 3D 预演候选导入 | implemented / thin adapter | `creative_contract_bridge.py`、Workbench 独立候选卡 | 直接消费视频创作 `previs_scene.v1`/capture manifest/validation；字段来自 StoryAI 固定 commit 的 camera/FOV/position/target/capture 设计 |
| 第二套队列、编辑器、FFmpeg、ASR、Timeline、审核服务、provider gateway | rejected | 无 | 保留 VKP 现有真源；未复制上游运行时 |

生成和预演契约会先复制为 `imports/video-creation-contracts/<role>-<canonical_sha12>.json`，再由 VKP dependency snapshot 绑定。生成产物、代表帧和预演截图均重新核对合法本地路径、字节数与 SHA-256。任何隐式安装、silent fallback、发布声明、data URL/裸 base64、相机元数据漂移或 observed-fact 越权都会被拒绝。

### 稳定前门

```powershell
.\scripts\video-knowledge.ps1 review-attestation-create <bundle> --target <target> --artifact role=path --approved-by <operator>
.\scripts\video-knowledge.ps1 review-attestation-status <bundle> --target <target>
.\scripts\video-knowledge.ps1 import-generation-contracts <bundle> --task <task.json> --receipt <receipt.json> --validation <validation.json> --preflight <preflight.json> --source-root <contract-root>
.\scripts\video-knowledge.ps1 import-previs-candidate <bundle> --scene <scene.json> --capture-manifest <captures.json> --validation <validation.json> --source-root <contract-root>
```

MCP 对应工具为 `create_review_attestation_tool`、`review_attestation_status_tool`、`import_generation_contracts_tool`、`import_previs_candidate_tool`。这些前门只读取/写入本地契约与 Bundle；不会启动生成器、3D 编辑器、外部 API 或媒体处理。

### 验证

- focused：`25 passed, 1 warning in 8.90s`。
- 本轮核心文件 Ruff：`All checks passed!`。
- `python -m compileall -q src`：通过。
- 全仓：`1051 passed, 3 failed, 1 warning in 358.43s`。3 项失败均来自本轮开始前已存在的并发改动范围：疑难帧 fast/实际帧存在性策略 2 项、Gemini 3.6/3.5-lite 目录与旧 probe fixture 不一致 1 项；本轮未回退或覆盖这些修改。
- 无网络调用、无上传、无模型执行、无服务启动、无端口/代理/计划任务修改、未修改视频创作仓库。

## 本轮结论

P0/P1/P2 的最小安全吸收已完成。VKP 继续以 Timeline、Bundle、run registry、Task Console/Workbench 为真源；视频创作侧继续拥有 generation/previs 契约及完整校验器。后续若上游 commit 或 schema 改变，必须重新审查并生成新 dependency snapshot，旧 attestation/receipt 不得继续冒充 current。
