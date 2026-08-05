# PrideWood bilinote 源码复用评估

更新时间：2026-07-04 20:04:00 | Codex / GPT-5

## 来源

- GitHub: <https://github.com/PrideWood/bilinote>
- 本地源码：`%WORKSPACE_ROOT%\tool-source-review\PrideWood-bilinote`
- 当前审查提交：`25ee9ba`

注意：`%WORKSPACE_ROOT%\tool-source-review\BiliNote` 是另一个仓库 `JefferyHcool/BiliNote`，并且已有本地改动；本次没有复用该目录作为 PrideWood 源码。

## 结论

PrideWood/bilinote 是一个轻量的本地视频学习笔记工具，主要价值不在“完整替换 VKP”，而在几个低耦合模块：

1. 字幕优先、Whisper fallback 的处理顺序。
2. SRT/VTT 字幕清洗、普通 transcript 解析、相邻短句合并。
3. LLM 校对 transcript 的提示词：只纠错、不总结、不改原意、保持 segment index。
4. 思维导图按 transcript 分块生成，避免长视频只覆盖开头。
5. 前端任务历史、转录编辑、时间戳跳转、API 设置面板。
6. Bilibili 字幕抓取 debug 信息：候选字幕、实际尝试、cookie 是否配置、最终选择来源。

## 已直接落地到 VKP

新增 `src/video_knowledge_pipeline/bilinote_transcript_tools.py`，移植并 Python 化 BiliNote 的字幕解析/清洗/合并策略：

- `parse_subtitle_text`
- `parse_plain_transcript`
- `merge_transcript_segments`
- `segments_to_txt`
- `segments_to_srt`
- `clean_subtitle_text`

同时把 VKP 的 `.srt/.vtt` 解析切到这个更宽容的解析器。收益：

- 支持 `MM:SS.mmm` 和 `HH:MM:SS,mmm`。
- 清理 HTML tag、ASS tag、HTML entity。
- VTT cue settings 不再污染 end timestamp。
- 后续可用 `merge_transcript_segments` 改善人工审核/智能总结的断句质量。

测试文件：`tests/test_bilinote_transcript_tools.py`。

## 暂不整体复用的原因

- 下载/在线链接处理仍由 `video-download-orchestrator` 负责；VKP 不重复吸收下载后端。
- ASR 主线仍是 SenseVoice/FunASR，本项目的 whisper.cpp 更适合作为 fallback 参考。
- BiliNote 主总结使用 `MAX_TRANSCRIPT_CHARS` 的截断策略，长视频容易牺牲全片覆盖；VKP 的 smart summary 应保持完整 ASR sidecar 覆盖。
- React/Express UI 适合参考交互，不适合直接搬进 VKP 当前静态 review bundle 和 CLI/MCP 架构。

## 值得继续吸收

### Transcript 校对

BiliNote 的 `correctTranscriptSegments` 提示词适合并入 VKP 的术语纠错/纠正版 ASR 流程：

- 输入保持 `{index,timestamp,text}`。
- 输出只允许 `{segments:[{index,text}]}`。
- 明确禁止总结、扩写、改变原意。
- 保持 segment 数量和 index 不变。

这可以作为 VKP `resolve-terms` 之后的“纠正版语音识别”生成层。

### 思维导图/智能总结

BiliNote 的 `splitTranscriptForMindMap` 是一个可借鉴点：把完整 transcript 按行累积到固定字符块，然后逐块请求模型，最后合并节点。VKP 后续 smart-summary/codex 版本也应采用“全片分块 -> 每块总结 -> 全局二次综合”，避免前段偏置。

### UI

前端 `App.tsx` 里值得参考：

- API 设置写入 localStorage，再随本地后端请求发送。
- 转录列表支持按播放时间高亮、点击时间戳跳转。
- 思维导图节点带 timestamp，可跳到视频时刻。
- transcript 可编辑后重新保存。

VKP 当前更适合吸收这些交互到 task console / review UI，而不是搬整套 UI。

### Bilibili 字幕 debug

`server/bilibili.ts` 的 subtitle debug 结构适合交给 VDO 线程参考。VKP 可在 VDO handoff manifest 中接收这些字段：

- subtitle sources checked
- candidate count
- selected language/source
- attempted count
- cookie configured

这样 VKP 能判断“平台字幕是否可信”，而不是只知道有一条 transcript。
## 深度复用模块清单

### 已复用：字幕解析与合并

来源：`server/transcriber.ts`

VKP 落地：

- `src/video_knowledge_pipeline/bilinote_transcript_tools.py`
- `src/video_knowledge_pipeline/transcript.py` 的 `.srt/.vtt` 解析入口
- `tests/test_bilinote_transcript_tools.py`

复用点：SRT/VTT/plain transcript 解析、HTML/ASS 标签清理、HTML entity 解码、短句合并、SRT/TXT 渲染。

### 已复用：转写校对 Prompt 与固定 index 契约

来源：`server/summarizer.ts` 的 `correctTranscriptSegments`

VKP 落地：

- `src/video_knowledge_pipeline/bilinote_summary_tools.py`
- `src/video_knowledge_pipeline/transcript_correction_pack.py`
- CLI：`transcript-correction-pack`
- MCP：`transcript_correction_pack`
- 测试：`tests/test_bilinote_summary_tools.py`、`tests/test_transcript_correction_pack.py`

复用点：

- system prompt：只修正 ASR 错别字、同音字、断句、专有名词；不总结、不扩写、不改原意。
- user prompt：保持 `segments` 长度和 `index` 不变。
- JSON contract：只返回 `{segments:[{index,text}]}`。
- 导入结果不覆盖 `term_resolution` 的 `corrected-transcript.*`，而是写入 `llm-corrected-transcript.*`，避免误把模型校对当作已验证事实。

使用示例：

```powershell
.\scripts\video-knowledge.ps1 transcript-correction-pack D:\path\to\webui-bundle
.\scripts\video-knowledge.ps1 transcript-correction-pack D:\path\to\webui-bundle --input-json D:\path\to\correction.json
```

如要真实调用文本 LLM：

```powershell
.\scripts\video-knowledge.ps1 transcript-correction-pack D:\path\to\webui-bundle `
  --provider-config D:\path\to\provider-config.json `
  --execute
```

### 已复用：长 transcript 分块策略

来源：`server/summarizer.ts` 的 `splitTranscriptForMindMap`

VKP 落地：`split_transcript_for_mind_map`。

用途：给智能总结、思维导图、转写校对准备“全片覆盖”的块，不再只取开头/结尾。

## 值得继续复用但尚未搬代码

| BiliNote 模块 | 价值 | 暂缓原因 |
| --- | --- | --- |
| `summarizeMindMapTranscript` | 可生成多层思维导图 | VKP 已有 `smart_summary_chapters/course_map`，下一步应融合提示词，不直接复制输出结构 |
| `App.tsx` 转录编辑/时间跳转 | UI 体验好 | VKP 当前是静态 review/task console，应吸收交互，不搬整套 React App |
| `jobs.ts` 本地任务历史 | 简单可维护 | VKP 已用 bundle manifest/run reports，任务历史可后续参考但不重复引入 |
| `bilibili.ts` 字幕 debug | 可作为 VDO handoff 字段 | 下载/平台访问归 VDO，不放进 VKP 主流程 |
| `video.ts` yt-dlp/ffmpeg 下载和字幕下载 | 逻辑清晰 | 明确不在 VKP 重写下载后端 |
