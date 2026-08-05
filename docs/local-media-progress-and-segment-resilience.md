# VKP 本地媒体进度、分块降级与字幕谱系

更新时间：2026-07-19 11:10:19
执行工具/模型：Codex / GPT-5.6

## 决策

VKP 为本地 ASR、转写后处理和 Smart Summary 本地准备阶段采用统一、机器可读的进度协议，并把字幕 segment 视为不可静默破坏的证据单元。

本设计参考了本地研究副本
`%WORKSPACE_ROOT%\tmp\open-video-tools-source\VideoCaptioner` 中“进度回调驱动 UI”“分项失败继续”“显式字幕合并”的产品设计。参考项目是 GPL-3.0；VKP 只研究行为与边界，以下协议和实现均为独立设计，没有复制其源码、函数、类型或常量。

## 统一进度协议

协议：

- 快照：`video_knowledge_pipeline.local_media_progress.v1`
- 事件：`video_knowledge_pipeline.local_media_progress_event.v1`
- JSONL 中每行一个事件，`sequence` 和 `percent` 单调递增。
- 状态仅为 `running`、`completed`、`failed`、`degraded`。
- 终态事件固定为 100%，终态之后禁止再追加事件。

每个事件至少包含：

- `stage`
- `percent`
- `current_item` / `total_items`
- `message`
- `status`
- `output_paths`
- `report_paths`

CLI 的人类可读进度由同一事件调用 `render_progress_line()` 生成并写到 stderr；最终 JSON 仍写 stdout，避免破坏脚本调用。

当前产物：

- Qwen3 ASR：`<output-stem>-progress.json/jsonl`
- ASR plan：`asr-plan-progress.json/jsonl`
- 转写后处理：`asr-transcript-postprocess-progress.json/jsonl`
- Smart Summary 输入：`exports/smart-summary-input-progress.json/jsonl`
- Smart Summary 章节：`exports/smart-summary-chapters-progress.json/jsonl`

## 长媒体分块降级

Qwen3 本地 ASR 对每个 chunk 独立捕获失败：

- 成功 chunk 的原始结果、segment 和文本继续保留。
- 失败 chunk 被复制到 `<output-stem>-failed-chunks`（复制失败也会记录原因）。
- `<output-stem>-chunk-report.json` 记录失败原因、时间缺口与精确重试命令。
- 部分成功时终态为 `degraded`，进程退出码为 2。
- 全部成功时为 `completed`、退出码 0；无可用结果时为 `failed`、退出码 1。
- 上层 `run-asr-plan` 接受退出码 2 的可用原始结果并继续规范化，但不会把它改写成成功。

只重试失败分块：

```powershell
.\scripts\video-knowledge.ps1 run-asr-plan <plan.json> --execute
```

具体的逐 chunk 命令从 chunk report 的 `retry_commands[].powershell` 读取；命令通过 `--chunk-indexes` 锁定原分块索引。

## 字幕 segment 保持

`TranscriptCue` 增加兼容默认字段：

- `segment_id`
- `source_segment_ids`
- `transformations`

JSON、SRT/VTT 和逐行纯文本解析会生成或保留稳定 ID。ASR 规范化、转写后处理和 Smart Summary 输入继续携带这些字段。

`postprocess-asr-transcript` 默认使用 `--segment-policy preserve`：

- 顺序、ID、start、end 和边界不变。
- 允许在单个 segment 内做清理或标点提示，但记录 `boundary_changed: false`。
- 不因文本清理默认合并、重排或丢段。

兼容旧的可读性合并必须显式指定：

```powershell
.\scripts\video-knowledge.ps1 postprocess-asr-transcript <bundle> --segment-policy readable_merge
```

显式拆分/合并会写入：

- 每个输出 segment 的 `source_segment_ids` 和 `transformations`
- 顶层 `transformations`
- 独立 `transcript-transformations.json`

Smart Summary 输入不合并 transcript segments；章节聚合是显式摘要变换，每章输出完整 `source_segment_ids` 和 `explicit_summary_aggregation` 记录。

## 兼容性

- `TranscriptCue` 新字段都有默认值，旧 Python 调用仍可只传 start/end/text。
- 旧 JSON 没有 ID 时会按原顺序生成稳定的 `segment-000001` 形式 ID。
- 行为变化仅在转写后处理默认策略：从隐式合并改为保持。需要旧行为的调用方必须显式选择 `readable_merge`。
- Timeline、Bundle 和现有 transcript schema 的既有字段没有删除。

## 安全边界

本功能只处理本地文件，不调用外部 API，不下载模型，不上传媒体，不改变 provider route、consent 或远程 fallback 策略。
