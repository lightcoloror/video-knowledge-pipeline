# 得到大脑说话人时间轴逐字稿导入

更新时间：2026-07-28 22:56:00（Asia/Shanghai）
执行工具/模型：Codex（GPT-5.6）
状态：已实现并完成真实只读解析验证。

## 结果

VKP 现在可以直接识别以下本地 TXT/Markdown 合同：

```text
说话人1 00:00:00
第一位说话人的原始 ASR 文本

说话人2 00:00:05
第二位说话人的原始 ASR 文本
```

不会再把标题、说话人行和正文拆成三个伪 segment，也不会把真实时间替换成行号。

对用户提供的真实原始 ASR 文本和“智能总结＋逐字稿”合并 Markdown 分别执行只读解析，两个入口均得到：

- 433 个 source segment；
- 2 个匿名说话人：`说话人1`、`说话人2`；
- 首段开始时间 0 秒；
- 最后一段开始时间 3529 秒；
- 合并 Markdown 的智能总结前言未混入逐字稿；
- 四处原始误识别文本仍保持原样，证明导入层没有越权纠错。

同时兼容得到大脑最终文档的 `🟢 说话人1 [00:00:00]` / `🟣 说话人2 [00:00:05]` header。

没有把敏感录音或完整逐字稿写入仓库、文档或测试 fixture。

## 变动记录

### 变动 1：格式识别

- **意图**：直接消费已经包含 speaker 和时间的得到大脑原始逐字稿。
- **决策**：在现有 `parse_transcript` 的普通 TXT/Markdown fallback 前增加一个窄格式探测器。
- **理由**：已有说话人证据应优先保留；重新跑 diarization 会增加耗时和错误机会。
- **证据**：真实导出采用 `说话人N HH:MM:SS` 标题行；只读 smoke 得到 433 段、2 位说话人和完整时间范围。
- **生效范围**：本地 `.txt` / `.md` 输入；JSON、SRT、VTT 和无 speaker 普通文本路径保持不变。

### 变动 2：复用而非第二套解析架构

- **意图**：避免为一种导出格式新建 transcript 状态机。
- **决策**：复用 VKP 现有 `parse_timestamp`、`normalise_speaker_value` 和 `TranscriptCue`；参考固定 MOSS `TranscriptStreamParser` 的“source segment 字段分离”边界，只适配行式 header。
- **理由**：MOSS 已证明 start/speaker/text 应是独立源字段；VKP 已有时间与 speaker 标准化，不应重复实现。
- **证据**：MOSS commit `eda4b9f13f1574765a80438c9797780a9bd48112`；VKP 现有 speaker source-fidelity 链。
- **生效范围**：`src/video_knowledge_pipeline/transcript.py`；不复制 MOSS 模型、推理、字幕导出或状态机。

### 变动 2A：与既有 GetBrain / Logseq 参考提取器的边界

- **意图**：复用已有代码，同时避免把评测参考错误提升为生产逐字稿真源。
- **决策**：保留 `transcript_stability_evaluation.extract_logseq_original_transcript` 负责 `- 原始转录` 缩进树；本次窄适配器只负责 `说话人N HH:MM:SS` 和 `🟢 说话人N [HH:MM:SS]` 两种导出 header。
- **理由**：既有提取器依赖 Logseq 树结构，当前真实文件不是该合同；强行复用会漏段。其模块又明确是 evaluation-only，不能让参考稿自动改写另一个 ASR。
- **证据**：已读取既有函数源码；它从顶层 `- 原始转录` 开始、只消费缩进子项，并返回 `video_knowledge_pipeline.logseq_original_transcript.v1`。当前两个真实输入均无该树结构，但含 433 个 speaker header。
- **生效范围**：格式分派与来源权限。显式传入本地 TXT/Markdown 时才解析；不扫描、不自动发现、不把得到大脑文本套到其他 ASR，也不自动提升为 human-confirmed。

### 变动 3：结束时间推断与保真边界

- **意图**：在导出仅提供每段开始时间时，仍保持可用时间区间。
- **决策**：当前段结束时间取下一段开始时间；最后一段保留零长度并标记 `end_unknown=true`；时间倒退不排序，只标记 `non_monotonic_next_start=true`。
- **理由**：不存在的结束时间不能凭文本长度或模型猜测；重排会破坏来源顺序。
- **证据**：真实格式只有 start header；现有 VKP 段落合同要求保留顺序、ID 和边界 lineage。
- **生效范围**：此格式导入 metadata；后续若有音频对齐证据，可在独立对齐层补结束时间。

### 变动 4：纠错权分离

- **意图**：让“佛医保、意外险、根据情况、明亚保险”等人工确认纠错继续走既有证据/审核链。
- **决策**：导入器逐字复制 ASR 正文，不自动套用任何词表替换。
- **理由**：格式解析器只拥有结构，不拥有语义纠错权；同音词在其他录音中可能有不同答案。
- **证据**：真实只读 smoke 确认四个原始误识别仍存在；既有 human-confirmed 纠错测试负责正式写回。
- **生效范围**：所有此格式输入；不做外部事实核查，只还原录音原意。

## 回归

```powershell
python -m pytest -q `
  tests\test_getbrain_speaker_timeline_parser.py `
  tests\test_transcript_speaker_source_fidelity.py `
  tests\test_transcript_speaker_partial_boundary.py `
  --basetemp C:\tmp\vkp-getbrain-parser-20260728-2254 `
  -p no:cacheprovider
```

结果：`14 passed`，仅 1 个既有第三方 `jieba/pkg_resources` warning。

覆盖：

- 标题忽略；
- speaker/time/body 分离；
- 下一段开始时间推断结束时间；
- 最后一段 `end_unknown`；
- 多行正文；
- 原始误识别不被导入器静默纠正；
- 无 speaker 普通文本继续走旧 fallback；
- 非单调时间只标记、不重排；
- 既有 speaker/source-fidelity 行为无回归。
