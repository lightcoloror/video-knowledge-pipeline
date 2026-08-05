# 转写证据仲裁纠错主链路

更新时间：2026-07-09 由 Codex / GPT-5 更新。

## 目标

VKP 的逐字稿不应该只等于 SenseVoice/FunASR 的原始 ASR。理想链路是把所有能证明“某个词可能识别错了”的证据合到一个保守的语义仲裁流程里，再生成最终可读稿和智能总结。

```text
SenseVoice 原始 ASR
+ 自带字幕/本地其他项目抓取到的字幕和网页上下文信息
+ 青龙打标器提供的时间轴重点/段落/话题标签、画面状态、哪些地方值得复核
+ OCR/多模态证据
+ 本地 agent-substitute 标点/断句后处理（默认，不外发，只改可读性，不改事实）
+ 本地 agent-substitute 语义仲裁（默认，只审真实证据冲突）
+ 本地 agent-readable-transcript-rewrite（默认，语义纠错后再做最终可读化）
+ transcript-quality-gate（默认，检查错词残留、标点毛刺和可读性门禁）
+ 在线 LLM 标点/断句后处理（可选，显式执行）
+ 在线 LLM 语义仲裁（可选，显式执行）
-> source-arbitrated-transcript.json
-> llm-readable-transcript.json（可选，显式 promote 后进入 corrected）
-> agent-readable-transcript.json
-> transcript-quality-gate.json
-> corrected-transcript.json
-> full-transcript.md
-> smart-summary.md
```

## 新入口

CLI：

```powershell
.\scripts\video-knowledge.ps1 transcript-evidence-correction-pipeline <webui-bundle>
```

MCP：

```text
transcript_evidence_correction_pipeline
```

默认行为：

- 执行本地多源仲裁：ASR、自带字幕、本地字幕、glossary、已有 corrected transcript。
- 生成通用语义纠错证据包：ASR/字幕可疑片段、timeline、青龙打标、OCR、ebook 结构化、多模态、网页/manifest 上下文。
- 写出 `source-arbitrated-transcript.*` 和稳定别名 `corrected-transcript.*`。
- 默认执行本地 `agent_substitute` 可读性处理，写出 `llm-readable-transcript.*` 并 promote 到 `corrected-transcript.*`。
- 默认执行本地 `agent_substitute` 语义候选草稿、验证和高置信 closure。
- 语义闭环后默认执行 `agent-readable-transcript-rewrite`，把最终 corrected transcript 再做一次本地 agent 可读化，写出 `agent-readable-transcript.*`，并 promote 回 `corrected-transcript.*`。
- 默认执行 `transcript-quality-gate`，检查已知错词残留、空冒号、中英文边界、标点毛刺和标点密度。
- `export-knowledge-note` 会再次运行 `transcript-quality-gate`，把门禁状态写入 `exports/full-transcript.md` 头部、`exports/export-summary.json` 和 `manifest.transcript_quality_gate_summary`。
- `smart-summary-input-pack` 优先读取 human/LLM/corrected transcript；因此 `agent-readable-transcript-rewrite --promote` 产生的 `corrected-transcript.json` 会成为智能总结输入，优先级高于旧的 `source-arbitrated-transcript.json` 和 normalized/raw ASR。
- 默认仍会写出 `exports/readable-transcript-llm-requests.json`，作为后续在线 LLM 对照计划。
- 不默认调用在线 LLM，不外发逐字稿。
- 在线 LLM 的标点/断句和语义仲裁仍需要显式执行参数。

执行在线 LLM 标点/断句后处理：

```powershell
.\scripts\video-knowledge.ps1 transcript-evidence-correction-pipeline <webui-bundle> `
  --provider-config <json-or-profile> `
  --execute-readable-llm
```

如果人工/质量门禁确认可读性结果只修标点、断句、段落，不改事实，再显式 promote：

```powershell
.\scripts\video-knowledge.ps1 transcript-evidence-correction-pipeline <webui-bundle> `
  --provider-config <json-or-profile> `
  --execute-readable-llm `
  --promote-readable-llm
```
执行在线 LLM 语义仲裁：

```powershell
.\scripts\video-knowledge.ps1 transcript-evidence-correction-pipeline <webui-bundle> `
  --provider-config <json-or-profile> `
  --execute-llm `
  --semantic-limit 80
```

将本地校验通过的高置信 LLM 决策写回并刷新人类可读导出：

```powershell
.\scripts\video-knowledge.ps1 transcript-evidence-correction-pipeline <webui-bundle> `
  --provider-config <json-or-profile> `
  --execute-llm `
  --auto-apply-high-confidence `
  --semantic-limit 80
```

## 给其他 agent 的本地替代调用方式

默认本地替代层不是 Codex 专属。WorkBuddy、OpenCode、Hermes Agent、OpenClaw 或其他 agent 都可以调用同一个 CLI/MCP 入口，并通过 `agent_name` 标记自己：

```powershell
.\scripts\video-knowledge.ps1 transcript-evidence-correction-pipeline <webui-bundle> --agent-name openclaw
.\scripts\video-knowledge.ps1 transcript-evidence-correction-pipeline <webui-bundle> --agent-name hermes_agent
.\scripts\video-knowledge.ps1 transcript-evidence-correction-pipeline <webui-bundle> --agent-name workbuddy
.\scripts\video-knowledge.ps1 transcript-evidence-correction-pipeline <webui-bundle> --agent-name opencode
```

MCP 调用参数：

```json
{
  "bundle_dir": "D:/path/to/webui-bundle",
  "use_agent_substitute": true,
  "agent_name": "openclaw",
  "execute_llm": false,
  "execute_readable_llm": false
}
```

输出报告会包含：

- `operator_boundary.agent_substitute_default=true`
- `operator_boundary.agent_substitute_name=<agent>`
- `readable_llm_polish.agent_substitute=true`
- `agent_readable_transcript_rewrite.status`
- `transcript_quality_gate.status`
- `agent_review`，等价于旧的 `codex_review` 兼容字段

也可以单独调用本地 agent 可读化和质量门禁：

```powershell
.\scripts\video-knowledge.ps1 agent-readable-transcript-rewrite <webui-bundle> --agent-name openclaw --promote
.\scripts\video-knowledge.ps1 transcript-quality-gate <webui-bundle>
```

MCP 工具名：

```text
agent_readable_transcript_rewrite
transcript_quality_gate
```

旧参数 `codex_substitute` / `--codex-substitute` / `--no-codex-substitute` 保留为兼容别名。新 agent 不应该依赖这些旧名。

如需完全回到只生成计划、不执行本地替代层：

```powershell
.\scripts\video-knowledge.ps1 transcript-evidence-correction-pipeline <webui-bundle> --no-agent-substitute
```


## 关键产物

| 产物 | 作用 |
| --- | --- |
| `transcript-source-arbitration.json/md` | 本地多源仲裁报告。 |
| `source-arbitrated-transcript.json/srt/md` | 本地/语义纠错前的证据仲裁转写。 |
| `exports/readable-transcript-llm-requests.json` | 标点/断句 LLM 请求计划，默认只生成不执行。 |
| `llm-readable-transcript.json/srt/md` | 在线 LLM 或本地 agent_substitute 可读性后处理结果；在线结果只有显式 `--promote-readable-llm` 才会进入最终别名。 |
| `agent-readable-transcript.json/srt/md` | 语义闭环后的本地 agent 最终可读化逐字稿；可由 Codex/OpenClaw/Hermes/WorkBuddy 等 agent 通过 `input_json` 导入人工/agent 改写结果。 |
| `agent-readable-transcript-task.json/md` | 给其他 agent 的段落级逐字稿改写任务包。 |
| `transcript-quality-gate.json/md` | 最终逐字稿质量门禁，检查错词残留和标点/断句毛刺。 |
| `corrected-transcript.json/srt/md` | 稳定的最终纠正版逐字稿别名，给导出和下游工具优先读取。 |
| `transcript-semantic-correction-pack.json` | LLM/agent-substitute 判读的证据包。 |
| `transcript-semantic-correction-llm-prompt.md` | 在线 LLM 请求计划；没有 `--execute-llm` 时只生成它。 |
| `transcript-semantic-correction-result.llm.json` | 在线 LLM 返回的判读结果。 |
| `transcript-semantic-correction-validation.json/md` | 本地校验结果，拒绝低置信或证据不足判断。 |
| `transcript-semantic-correction-closure.json/md` | 高置信决策写回结果。 |
| `exports/full-transcript.md` | 人类可读逐字稿。 |
| `exports/smart-summary.md` | 智能总结。 |
| `transcript-evidence-correction-pipeline.json/md` | 主链路总报告。 |

## 安全边界

- 原始 ASR、自带字幕、网页上下文、OCR、多模态和青龙打标证据不被覆盖，只作为证据来源。
- 本地 `agent_substitute` 默认执行，但不调用网络、不外发逐字稿。
- 标点/断句在线 LLM 只在 `--execute-readable-llm` 时调用。
- 语义仲裁在线 LLM 只在 `--execute-llm` 时调用。
- provider config/API key 只允许运行时传入，不写入 manifest、报告或 MCP args。
- 数字、价格、人名、专名、事实主张默认高风险；除非证据足够强，否则进入 review。
- 在线标点/断句结果进入最终稿必须显式 `--promote-readable-llm`。
- 本地 `agent-readable-transcript-rewrite` 可以显式 `--promote`，主 pipeline 默认在语义闭环后执行并通过 `transcript-quality-gate` 验收。
- 语义仲裁自动写回在线 LLM 决策必须显式 `--auto-apply-high-confidence`；本地 agent-substitute 只写高置信保守候选。
- 低置信、高风险、证据冲突项必须进入人工复核，而不是直接修正文稿。

## 为什么这能改善逐字稿

得到大脑的逐字稿强，说明单纯本地 ASR 还不够。VKP 要超过它，核心不在“再跑一次 ASR”，而在于让多个来源互相校验：

- ASR 听错的专名，可由自带字幕、屏幕文字、网页标题、青龙标签和 LLM 语义共同证明。
- 自带字幕本身也可能是 ASR，所以不能盲信，只能作为一个来源。
- OCR/多模态不是替代 ASR，而是给“屏幕上到底写了什么、老师在讲哪一步”提供证据。
- LLM 的职责不是自由改写逐字稿，而是对候选错词做保守仲裁。

## 推荐顺序

1. `postprocess-asr-transcript`：先让 SenseVoice 原始 ASR 有基本标点和段落。
2. `transcript-evidence-correction-pipeline`：跑本地仲裁、语义证据包、本地 agent 可读化、质量门禁，并生成 readable LLM 请求计划。
3. `transcript-quality-gate`：单独复查最终 corrected transcript 是否还有错词残留或标点毛刺。
4. `agent-readable-transcript-rewrite --agent-name <agent> --promote`：如果门禁失败，先做本地 agent 可读化重写，再复跑质量门禁。
5. `transcript-evidence-correction-pipeline --execute-readable-llm --promote-readable-llm`：需要更自然的标点/断句时，显式调用在线 LLM，可读性结果通过门禁后再使用。
6. `transcript-evidence-correction-pipeline --execute-llm`：让在线 LLM 判读真实证据冲突里的疑似错词。
7. `transcript-evidence-correction-pipeline --execute-llm --auto-apply-high-confidence`：写回高置信语义仲裁结果并刷新导出。
8. `export-knowledge-note`：刷新 `full-transcript.md`、`smart-summary-input-pack`、`smart-summary.md` 和导出摘要；导出时会把质量门禁状态写进人类可读逐字稿头部。
9. `transcript-semantic-correction-status` / impact reports：确认纠错确实进入 `full-transcript.md` 和 `smart-summary.md`。
