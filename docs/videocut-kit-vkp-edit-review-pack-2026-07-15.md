# videocut-kit → VKP 剪辑交接包实施记录

- 执行工具/模型：Codex / GPT-5.6
- 时间：2026-07-15 11:05:33
- VKP 落点：`src/video_knowledge_pipeline/video_edit_review_pack.py`
- 上游源码：`%WORKSPACE_ROOT%\ai-video-tools-20260708\sources\videocut-kit`
- 固定源码版本：`b07990f9e57e6eeb801887fa3e36af5c8450ae68`
- 状态：P0 已实现；P1 候选契约已实现；P2 偏好证据门已实现；FCPXML 延期

## 实施结论

VKP 只吸收 videocut-kit 的确定性剪辑不变量，不复制它的 FFmpeg 流水线、状态机、审核服务器或最终创作判断。

新增的 `video-edit-review-pack` 把 VKP Timeline、Smart Summary chapter、ASR/OCR 仲裁和 temporal visual evidence 规范化为视频创作线可只读消费的交接产物：

```text
Timeline + Smart Summary + ASR/OCR arbitration
                       ↓
            video-edit-review-pack
      ┌────────────────┼────────────────┐
      │                │                │
Storyboard 候选   边界/静音精修     产物一致性硬门
      │                │                │
      └────────────────┼────────────────┘
                       ↓
       现有 Workbench 人工确认与接缝复核
                       ↓
          既有单一 FFmpeg/render 出口
```

该命令只生成候选、审计与运行登记，不编辑媒体，不调用模型，不联网，不自动写全局偏好。

## 已复用的源码设计

| 上游模块/符号 | VKP 实现 | 复用方式 | 硬边界 |
|---|---|---|---|
| `scripts/snap_boundaries.js::buildSilences` | `build_token_silences` | 算法适配 | 只用 token gap/显式 silence 作为本地锚点 |
| `mergeSilences` | `merge_silences` | 算法适配 | 丢弃非法段，稳定排序并合并 |
| `snapDecisions` / `guardFor` | `refine_edit_boundaries` / `_snap_point` / `_guard_for` | 算法适配 | 尊重 `lock_start/lock_end`；吸附塌缩时回退 |
| `absorbSilentSlivers` | `_absorb_silent_slivers` | 算法适配 | 间隙含 token 时绝不吞并 |
| `reclaim_silence.js::reclaim` | `reclaim_silence_from_envelope` / `reclaim_silence_from_media` | 算法适配 | 仅显式 `--reclaim-silence` 才调用本地 ffmpeg 解码能量，不生成第二条渲染线 |
| `validate_artifacts.js::normalizeSegments` | `normalize_segments` | 不变量复用 | 删除段与实际导出段不一致时硬阻断 |
| `transformLikeServer` | `validate_edit_artifacts` 的 `boundary_refined` 比较 | 不变量复用 | 先原始比较，再按同一边界算法比较；仍不一致才失败 |
| `model/schema.md::StoryboardScene` | `build_storyboard_candidates` | 契约适配 | Smart Summary 优先、Timeline 回退；始终 `confirmed=false` 候选 |
| `diff_decisions.js` | `build_preference_evidence` | 契约适配 | 未显式标记人工确认的差异不可学习 |
| `distill_prefs.js` | `promotion_rule` 与 `promotion_eligible=false` | 规则吸收 | 至少 3 个独立视频或用户明确固化；本模块不写偏好真源 |

## 产物合同

写入一个 WebUI Bundle 的 `exports/`：

- `video-edit-review-pack.json` / `.md`：统一交接与阻断状态。
- `storyboard.candidates.json`：可追溯到 Timeline index、chapter citation 与 temporal evidence 的场景候选。
- `edit.decisions.refined.json`：带 `orig_start/orig_end` 的边界审计结果。
- `video-edit-artifact-validation.json`：删除段、保留段和时间线覆盖校验硬门。
- `video-edit-preference-evidence.json`：只读、人工确认门控的偏好候选证据。
- `mcp-video-edit-review-pack.args.json`：不含媒体内容或密钥的本地 MCP 参数。
- `runs/video-edit-review-pack/run.json`：复用 VKP run registry 的状态登记。

Manifest 同步登记对应路径；现有 `video-workbench` 的外部复用面板新增“剪辑交接 / videocut-kit”能力状态和三个产物链接。

## 接口

CLI：

```powershell
.\scripts\video-knowledge.ps1 video-edit-review-pack <webui-bundle>
```

显式本地能量恢复：

```powershell
.\scripts\video-knowledge.ps1 video-edit-review-pack <webui-bundle> `
  --media-path <local-video> `
  --reclaim-silence
```

MCP：

- `video_edit_review_pack_tool`
- `video_edit_review_pack`

## 人工与执行门

- `edit.decisions.json` 的活动决策必须 `confirmed=true` 或 `source=user`，否则 `unconfirmed_edit_decisions` 阻断既有渲染线。
- Storyboard 始终作为候选进入现有 Workbench；run 状态保持 `needs_review`，不能因 pack 生成成功就视为创作确认。
- `artifact_validation.ok=false` 时不得进入现有 FFmpeg/render 出口。
- 偏好差异即使人工确认，也先保持 `observing`；本模块绝不自动升级或写全局偏好。
- 本模块不调用 MediaKit、LiteLLM 或任何在线 API；也不执行上传、发布或 local/cloud fallback。

## 验证

新增 `tests/test_video_edit_review_pack.py`，覆盖：

1. token gap 边界吸附和审计字段。
2. ASR 时间戳吞静音的能量包络恢复。
3. 原始/边界精修两种删除段一致性比较及漂移阻断。
4. 未人工确认的偏好差异不可学习。
5. 未人工确认的剪辑决策阻断。
6. Smart Summary → Storyboard、Manifest、run registry、CLI 全链写入。

相关 Workbench/run registry 回归也必须一起运行。

## 明确不做

- 不复制 videocut-kit 的 `pipeline.js` 状态机。
- 不新增第二套 FFmpeg、ASR、Smart Summary、RAG 索引或审核服务器。
- 不把 Storyboard 候选当成最终创作判断。
- 不在 VKP 内实现 FCPXML；待有真实编辑器 round-trip fixture 后再评估薄出口适配器。
