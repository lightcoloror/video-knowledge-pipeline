# VKP 通用内容片段检索、定界与剪后验真 v1

- 更新时间：2026-08-16 15:21:15 +08:00
- 执行：Codex (GPT-5.6 Sol)
- 状态：本地派生能力已实现；人工选择与最终复核仍为硬门

## 结论

采访片段链路已经泛化为统一的“内容片段请求”。课程解释、教程步骤、人物动作、PPT/网页文字、声音事件、B-roll、高光和故事节拍现在共用现有 Bundle、VideoRAG、moment index、转写、OCR、temporal evidence 和技术镜头真源，但分别使用适合自身模态的定界与剪后验真规则。

```text
content_clip_request.v1
  -> profile (quote / lecture / tutorial / visual / screen / audio / broll / highlight / story beat)
  -> existing VideoRAG + moment index + explicit time window
  -> existing transcript / Timeline OCR / temporal evidence / technical shots
  -> content_clip_candidate_pack.v1
  -> human selection + fine cut
  -> clip-only ASR/OCR/visual/audio evidence
  -> content_clip_alignment_check.v1
  -> human final review
```

旧 `script_clip_request.v1`、CLI 和产物保持可用；通用候选器也可将旧请求只读映射为 `spoken-quote-v1`，不修改旧文件。

## Source-first 复核与复用裁决

| 来源 | 固定版本 | 实际检查 | 本次裁决 |
| --- | --- | --- | --- |
| VKP VideoRAG / moment index / transcript reference window | 当前仓库 `475824f` 基线 | 读取实际检索、时间窗和 hash 绑定代码；旧脚本片段 12 项关联回归通过 | 直接复用为唯一文本/时间检索实现 |
| VKP technical shot detection | 当前仓库现有合同 | 读取 `load_verified_technical_shots`，确认章节、Timeline 和整段视频不能伪装成 shot | 直接复用，缺镜头即 `unavailable` |
| Subtitle Edit 适配 | VKP 已登记固定上游 | 复核现有静音区解析/吸附 owner | 继续作为既有媒体边界证据；本层不新跑 FFmpeg |
| Moyf/moys-asr-workflow | `949bc84058cdae1d9c021c50203e6d2742f9392c` / AGPL-3.0 | 读取 `web/editor-utils.js`；2026-08-16 复跑 64/64 编辑与 timing 测试 | 复用已集成的人工时间编辑语义，不复制新算法 |
| WhisperX | `5f2f9d4320dd93a7d12f5ba2495eef7e0a5af963` / BSD-4-Clause | 读取 `whisperx/diarize.py` 的词/说话人区间分配 | 只消费现有词时间戳和匿名 speaker lineage，不复制推理 |
| AutoShot | `77c82ff826a9301bb173d9be786297a49d73d081` / MIT | 核对实际源码与已完成 32 视频 GPU benchmark | 只通过 VKP technical-shot 合同消费，不直接调用第二次 |
| Shot2Story | `ae26ac3d2f9e9a91a7fd0653bfb6a2b3cb250308` / Apache-2.0 | 读取镜头事实到跨镜头结构的任务边界 | 复用分层合同思想，不引入整段视频模型 |

未引入新的 Provider SDK、索引、FFmpeg、ASR、OCR、模型路由、服务端口或状态机。网页检索发现的其他项目只保留候选研究状态；没有固定源码、本地运行和许可证证据的实现没有进入本次生产代码。

## 公共接口

```powershell
.\scripts\video-knowledge.ps1 content-clip-candidate-pack <bundle> <request.json> --top-k 8 --retrieval-backend keyword
.\scripts\video-knowledge.ps1 content-clip-alignment-check <bundle> <review-notes.json> <fine-cut-plan.json>
```

MCP 使用同一 Python 实现：

- `content_clip_candidate_pack`
- `content_clip_alignment_check`

Workbench 显示 `通用内容片段候选` 与 `通用片段剪后多模态验真`，不创建第二个审核服务。

## 九种查询预设

| 预设 | 主要真源 | 默认边界 | 剪后硬门 |
| --- | --- | --- | --- |
| `spoken-quote-v1` | ASR | 完整句、说话人轮次 | clip-only ASR、speaker、字幕语义 |
| `lecture-explanation-v1` | ASR，OCR 辅助 | 完整解释段 | clip-only ASR、术语/数字、句界 |
| `tutorial-step-v1` | ASR + visual | 讲解开始到结果稳定 | ASR、视觉人工确认、结果画面 |
| `visual-event-v1` | visual + shot | 动作开始—峰值—结束 | clip-only visual、技术镜头 |
| `screen-content-v1` | OCR | 文字稳定出现到页面切换 | clip-only OCR、目标/排除词 |
| `audio-event-v1` | audio | 声音事件起止 | clip-only audio 人工确认 |
| `broll-v1` | shot | 完整技术镜头 | shot、visual、排除内容 |
| `highlight-v1` | ASR + visual/audio | 前因—峰值—结果 | 内容完整和多模态复核 |
| `story-beat-v1` | ASR + visual/shot | 原因—变化—结果 | 上下文完整和视觉复核 |

检索排序先执行 source video/time、`must_include`、`must_exclude` 和显式 speaker 约束等硬过滤，再做证据分层并在同一来源内部保留原排名；VideoRAG 与 moment index 的原始分数永远不跨检索器直接比较。候选记录 `semantic_match_range`、`recommended_cut_range`、`safe_extension_range`、`source_shot_ids`、`source_segment_ids` 和 `boundary_reason`。上下文邻段不会参与候选主体的 speaker 硬过滤。

## 状态边界

剪后检查只输出：

- `ready_for_human_final_review`
- `needs_candidate_selection`
- `needs_boundary_review`
- `needs_speaker_review`
- `needs_transcript_review`
- `needs_visual_review`
- `needs_recut`
- `needs_subtitle_revision`

`ready_for_human_final_review` 仍然不是发布批准。视觉事件不能由 ASR 命中代替；屏幕文字不能由源 OCR 代替 clip-only OCR；声音事件不能由文本猜测；没有技术镜头时 B-roll 和动作边界保持 unavailable。

## 变更记录

### CC-20260816-01 — 查询预设与旧合同兼容

- 意图：让采访以外的内容使用同一条可追溯片段链路。
- 决策：新增九个版本化 profile，并把旧 script slot 只读映射到 `spoken-quote-v1`。
- 理由：内容类型只应改变证据源、排序、边界和验真规则，不应复制索引或状态机。
- 证据：旧脚本片段关联回归保持通过；兼容映射保留 source transcript、时间窗和 speaker 约束。
- 生效范围：通用请求解析和派生候选；旧 CLI/Schema 不迁移。
- 回滚：停用新命令；旧采访链路保持原样。

### CC-20260816-02 — 多模态候选与分层排序

- 意图：避免用 ASR 强行证明画面、屏幕或声音事件。
- 决策：在现有检索候选上只读附加 ASR/OCR/visual/audio/shot 覆盖与缺口；排序使用证据 tier 和来源内百分位。
- 理由：不同检索器分数未校准，且文本命中不是视觉事实。
- 证据：合成 Timeline/technical shots 正例和缺镜头负例；`raw_scores_compared_across_retrievers=false`。
- 生效范围：`content_clip_candidate_pack.v1`。
- 回滚：删除通用派生文件；VideoRAG、Timeline 与技术镜头不变。

### CC-20260816-03 — 内容类型定界

- 意图：分别处理句子、整镜头、屏幕稳定区、教程和声音事件。
- 决策：消费已有 transcript segment、Timeline 和 verified technical shot；输出语义范围、推荐范围与安全扩展范围。
- 理由：统一按一句话或统一按镜头切都会破坏其他内容类型。
- 证据：技术镜头规范化 ID、完整句边界、时长上/下限和 evidence missing 回归。
- 生效范围：派生边界建议，不执行媒体切割。
- 回滚：人工继续直接填写精剪范围；源证据不变。

### CC-20260816-04 — 剪后多模态验真

- 意图：证明目标内容实际存在于剪后片段，而不仅是源视频。
- 决策：复用旧 alignment 的 hash、range、speaker、ASR 和字幕检查，新增 clip-only OCR/visual/audio/shot 门。
- 理由：源证据存在不能证明剪后仍保留，也不能证明人物动作或页面文字完整。
- 证据：正常 quote 进入最终人工复核；缺 visual、hash drift、缺 shot 和越界范围 fail-closed。
- 生效范围：`content_clip_alignment_check.v1` 与 repair TODO。
- 回滚：停用检查器；不会回写或恢复媒体。

### CC-20260816-05 — CLI/MCP/Workbench 薄入口

- 意图：让 Agent 与人工操作台调用相同实现。
- 决策：注册两个 CLI、两个 MCP 工具、run type 和 Workbench 卡片。
- 理由：不应另建服务、端口或审核状态机。
- 证据：parser、MCP roundtrip、run registry 与 Workbench artifact 回归。
- 生效范围：本地发现、执行和审核导航。
- 回滚：移除入口；核心已有模块不受影响。

## 安全与未覆盖边界

- 本次不调用模型、不联网、不上传、不下载权重、不执行精剪、不发布。
- 不推断真人身份；只消费匿名 speaker 与人工角色。
- visual/audio 的语义正确性仍要求 clip-only evidence 与人工确认。
- 有 segment 级词时间戳时会显式记录 `word_timestamp_used=true`；没有时定界安全退回完整 segment，不会伪造词级精度。独立 ForcedAligner sidecar 的自动关联仍是后续增强项。
- 真实视频的视觉、音频事件和高光仍需固定样本人工测量复核时间与误切率。

## 真实 Bundle dry-run

使用既有《一次癌症诊治中保险如何真正用起来》正式采访 Bundle 做了两次 `--no-write` 本地验证：

1. 旧 `script_clip_request.v1` 经兼容层生成 4 个通用 quote 请求和 20 个候选，缺必需候选为 0。
2. 新通用请求同时包含 `lecture-explanation-v1` 与 `visual-event-v1`。source scope、must terms 和 speaker 硬门后各保留 1 个候选；解释片段由 ASR 支持，视觉片段因现有 Bundle 没有足够的 clip-level visual/shot 证据，被准确标为 1 个 required-evidence 缺口。

这次 dry-run 没有写 Bundle、没有抽帧、没有模型调用、没有上传，也没有自动把视觉请求降级为文本请求。机器结果只能进入候选选择。
