# 脚本驱动采访原声候选与剪后一致性检查

- 更新：2026-08-16 13:40:00 +08:00
- 执行：Codex (GPT-5.6 Sol)
- 状态：本地派生审核能力已实现；永远不授予发布权限

## 结论

VKP 新增两段式本地工作流：先将已审核脚本的槽位映射为采访源片段候选，再在人工选择和精剪后核对脚本、批准原话、剪辑区间、clip-only ASR、匿名说话人与字幕。它只生成候选、审核 TODO 和阻断报告，不自动选择候选、不自动剪片、不改字幕、不认定真人身份，也不发布。

```text
reviewed script slots
  -> existing VideoRAG + moment index
  -> transcript reference windows
  -> script_clip_candidate_pack.v1
  -> human selection/review notes
  -> fine-cut plan + clip-only ASR
  -> script_clip_alignment_check.v1
  -> human final review
```

## 复用而非重写

| 职责 | 复用 owner | 本层只增加 |
|---|---|---|
| 本地文本检索 | `video_rag_search` | 脚本槽位编排与候选去重 |
| 时间证据检索 | `video_moment_index` | 槽位级 lineage |
| 精确转写窗口 | `transcript_reference_window` | 将 receipt 嵌入候选 |
| 转写解析 | `transcript.parse_transcript` | 半开剪辑区间判断 |
| 原子写与互斥 | `storage` / Bundle lock | 派生 JSON、Markdown、TODO |
| 可发现运行记录 | `run_artifact_registry` / Workbench | 两个 run type 和 artifact cards |
| 人工边界 | 现有 transcript/subtitle review 语义 | hash-bound review notes，不新建状态机 |

Content Studio 的 `case-video-script-handoff.v1` 只作为可选、哈希绑定的上游证据。VKP 不修改该 Schema，也不把上游脚本当成媒体事实。

## 公共合同

### `video_knowledge_pipeline.script_clip_request.v1`

输入必须绑定脚本 SHA-256；可选绑定上游 handoff 和指定源逐字稿。每个 slot 显式给出检索词或首选时间窗、期望原话、说话人角色要求和 episode binding。重复 slot ID、非法时间窗、文件或哈希漂移全部 fail-closed。

### `video_knowledge_pipeline.script_clip_candidate_pack.v1`

输出候选的源时间范围、上下文范围、segment/source segment lineage、匿名说话人、显式角色、检索来源、分数与 reference-window receipt。机器候选永远 `review_required=true`、`publication_allowed=false`。

### `video_knowledge_pipeline.script_clip_review_notes.v1`

草稿必须由人工选择 candidate，绑定精剪 order/output、批准源窗口、批准原话、匿名说话人集合、clip-only ASR 路径和 SHA。`review_status=human_confirmed` 还必须绑定 candidate pack 的语义哈希与文件哈希。

### `video_knowledge_pipeline.script_clip_alignment_check.v1`

结果只允许以下状态：

- `ready_for_human_final_review`
- `needs_candidate_selection`
- `needs_speaker_review`
- `needs_transcript_review`
- `needs_recut`
- `needs_subtitle_revision`

即使状态是 `ready_for_human_final_review`，仍然 `publication_allowed=false`。

## 阻断代码

检查完整覆盖：`missing_required_slot`、`candidate_not_searched`、`speaker_role_unresolved`、`excluded_speaker_present`、`cut_outside_approved_window`、`approved_quote_missing_after_cut`、`clip_contains_unreviewed_claim`、`subtitle_semantic_expansion`、`sentence_fragment_at_boundary`、`multiple_speakers_mislabeled_as_customer_quote`、`source_only_not_clip_present`、`duplicate_or_conflicting_episode_binding`。

源逐字稿只能证明“原视频里说过”，不能证明“剪后片段里仍然存在”。因此没有独立 clip-only ASR 时必须进入 `source_only_not_clip_present`，不能把源文本命中当成剪辑验收通过。

## CLI 与 MCP

```powershell
.\scripts\video-knowledge.ps1 script-clip-candidate-pack <bundle> <request.json> --top-k 8 --retrieval-backend keyword
.\scripts\video-knowledge.ps1 script-clip-alignment-check <bundle> <review-notes.json> <fine-cut-plan.json>
```

对应 MCP 工具：

- `script_clip_candidate_pack`
- `script_clip_alignment_check`

MCP 与 CLI 调用同一 Python 实现，不复制检索、校验或运行状态。

## 变更理由

### SC-20260816-01 — 脚本槽位候选包

- 意图：让内容脚本反向定位采访原声，而不是人工在长视频中反复拖动查找。
- 决策：编排现有 VideoRAG、moment index 和 reference-window；增加 slot 级候选、哈希与人工选择 TODO。
- 理由：检索、时间证据和转写 lineage 已有成熟 owner，重新实现会产生第二套索引。
- 证据：合成 Bundle 同时命中两条本地检索路线，候选保留 segment/source ID、说话人与 reference receipt；无写预览不改 Bundle。
- 生效范围：Bundle 派生 review artifacts。
- 回滚：停止调用并删除候选派生文件；Timeline、逐字稿、脚本与媒体不变。

### SC-20260816-02 — 精剪与 clip-only ASR 对齐门

- 意图：区分“源视频说过”和“最终剪辑里仍然完整说过”。
- 决策：人工确认后同时核对 fine-cut keep range 与独立 clip transcript；相邻区间按半开区间处理。
- 理由：只查源逐字稿会漏掉剪掉原话、句子截断、混入另一说话人和字幕扩写。
- 证据：12 类故障合成回归；边界测试证明 4 秒结束的片段不会吸入恰好从 4 秒开始的下一位说话人。
- 生效范围：只读 alignment report 与 repair TODO。
- 回滚：停用检查器；不会恢复或修改任何媒体。

### SC-20260816-03 — 匿名说话人 fail-closed

- 意图：阻止机器把采访者或家属误标成客户原声。
- 决策：只消费已有匿名 speaker ID 和显式人工角色；源窗口与 clip ASR 都检查 expected/excluded speaker 集合，不推断真人身份。
- 理由：分块聚类和跨视频声纹仍是候选生物特征证据，不能自动变成人物身份。
- 证据：角色缺失、错误匿名 speaker、排除 speaker 和多说话人 customer quote 均进入 `needs_speaker_review`。
- 生效范围：派生审核状态；不改 speaker sidecar 或角色绑定。
- 回滚：删除 review notes 的 speaker 约束后重新生成候选，但不得把结果称为已核验客户原声。

### SC-20260816-04 — CLI/MCP/Workbench 单一入口

- 意图：让本地 Agent 和人工操作台发现同一能力与同一边界。
- 决策：在现有 CLI、MCP server、run registry 和 Workbench 中注册薄入口与 artifact cards。
- 理由：不应新建服务器、端口、状态机或发布工作流。
- 证据：CLI、MCP source contract、run registry 与 Workbench projection 定向测试通过。
- 生效范围：本地发现与审核导航。
- 回滚：移除两个命令和 Workbench 卡片；核心现有模块不受影响。

## 安全边界

- 仅本地文件；不调用 Provider、不上传媒体、不下载模型。
- 不读取或写入 Key、cookie、账号信息。
- 不修改源视频、精剪片段、canonical transcript、Timeline、上游脚本或 Obsidian。
- 不推断真人身份。
- 不自动选择、裁切、改字幕、批准或发布。

## 真实本地 dry-run（2026-08-16）

在既有采访 Bundle 上完成一次不调用模型、不重切媒体的真实验收。候选阶段生成 4 个脚本槽位、32 个候选，所有槽位均有搜索结果；显式首选时间窗优先于不可直接比较的 VideoRAG/moment 原始分数，候选正文只使用源逐字稿，不再把脚本期望原话伪装成 ASR 命中。

复用既有人工精剪计划与既有 clip-only ASR 后，对齐门输出 `needs_speaker_review`，共 11 个问题：4 个 `speaker_role_unresolved`、4 个 `approved_quote_missing_after_cut`、2 个 `sentence_fragment_at_boundary`、1 个 `clip_contains_unreviewed_claim`。这证明检查器没有把“源视频里说过”误判为“剪后仍完整保留”，也没有把缺失的说话人角色自动推断为真人身份。

本次比较存在一项明确边界：脚本为普通话概括，源与剪后 ASR 含粤语口语，因此字符串语义门会偏保守；这些 issue 是人工听审候选，不是对原意是否存在的最终事实判决。成熟的后续路线应消费人工确认的粤语原话或受控双语对齐 sidecar，而不是放宽 fail-closed 门。

真实产物仅写入用户本地 Bundle，未纳入 Git：

- `exports/script-clip-candidate-pack.json/md`
- `script-clip-review-notes.todo.json`
- `exports/script-clip-alignment-check.json/md`
- `script-clip-repair.todo.json`

### SC-20260816-05 — 窗口级转写校验

- 意图：不让候选窗外的旧分块微小重叠阻断当前片段检索，同时继续拦截候选窗内的乱序。
- 决策：为既有 reference-window exporter 增加显式 `validation_scope=source|window`；默认仍为 `source`，本工作流只选择 `window`。
- 理由：真实逐字稿在约 1019.74/1019.73 秒有 10ms 历史分块重叠，但本次四个候选窗均不经过该位置；全局放宽会削弱旧调用方契约。
- 证据：默认严格模式回归保持不变，窗口模式的乱序负例与真实 Bundle dry-run 均通过。
- 生效范围：仅显式选择窗口校验的调用方。
- 回滚：移除可选参数，恢复全部调用的全源校验；现有默认调用行为无需迁移。
