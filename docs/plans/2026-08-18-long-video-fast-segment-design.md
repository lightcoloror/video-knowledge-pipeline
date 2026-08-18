# VKP 超长视频内容感知快速分段设计

- 更新时间：2026-08-18 16:52:01 +08:00
- 执行工具/模型：Codex (GPT-5.6 Sol)
- Dispatch：`VKP-LONG-VIDEO-FAST-SEGMENT-20260818-01`

## 目标

在不建立第二套 ASR、VAD、镜头检测、FFmpeg 或审核状态机的前提下，把已有证据组合成以下安全闭环：

`现有 ASR/VAD/OCR/镜头证据 → 删除候选 → 人工逐段确认 → 新副本渲染 → FFmpeg 回执与时长 QA`

默认只生成审核计划。任何证据不足、模态冲突或低置信区间都保留；永不修改原片。

## 方案比较

1. **音频优先快速路线**：只用 VAD 和 ASR 空隙。速度最快，但会误删没有对白的独有 PPT、操作演示和环境镜头。
2. **分层多证据路线（采用）**：先用 VAD/ASR 找候选，再用 Timeline/OCR/技术镜头证据降级为人工复核；等待、重说、片头片尾走各自规则。速度接近音频路线，但能保护视觉独有内容。
3. **整段 VLM 路线（拒绝）**：语义能力较强，但长视频速度慢、成本高、难以复现，也会引入上传/授权和模型幻觉风险。

## 复用依据

| 能力 | 已有来源 | 复用方式 |
|---|---|---|
| 人声与长静音 | FunASR FSMN-VAD；faster-whisper 内置 Silero VAD | 只读现有 VAD sidecar，不加载第二套模型 |
| 句子、说话人和时间边界 | VKP canonical/human-corrected transcript | 复用 `parse_transcript`，不改逐字稿 |
| 独有视觉内容 | VKP Timeline/OCR/temporal evidence | 有视觉证据的空语音区间降级为人工复核 |
| 技术镜头 | AutoShot/PySceneDetect/OmniShotCut 的 `technical_shot_boundaries.v1` | 只读已验证技术镜头，不重新解码 |
| 边界与审核不变量 | videocut-kit `b07990f...`；VKP `video_edit_review_pack` | 复用人工确认、边界、产物一致性和新副本原则 |
| 渲染与审计 | VKP shared media resolver + `single_ffmpeg_outlet` receipt | 明确 `--execute` 后才运行；CPU 精确重编码，无静默 fallback |

源码准入已由 `SOURCE_INVENTORY.json` 与 `docs/external-code-reuse-ledger-2026-07-04.md` 核对；没有重复拉取源码或下载模型。

## “无意义片段”合同

候选类型：

- `long_silence`：VAD 或时间戳显示的长无语音区间。
- `intro_outro_blank`：首尾的长无语音技术空白。
- `waiting_or_technical_setup`：明确的等待、试音、调试、尚未开始。
- `possible_retake_or_restatement`：相邻窗口内的近重复说法；不自动判断保留哪一遍。
- `non_information_smalltalk`、`technical_blank`：合同保留扩展位，首版不凭主观词表自动生成。

安全分类：

- `drop_safe_candidate`：VAD 已完成且区间没有 OCR/temporal/镜头证据。名称中的 safe 只表示“适合优先审核”，不允许自动删除。
- `drop_review_required`：存在视觉证据、只由逐字稿空隙推断，或属于等待/重说等语义候选。
- `unknown_keep`：证据不足或冲突；强制保留。

## 生命周期与失败恢复

1. `long-video-fast-segment-plan` 绑定媒体、逐字稿、VAD、Timeline 和镜头证据哈希，生成 Markdown 时间码预览和 review todo。
2. `apply-long-video-fast-segment-review` 要求每个候选明确选择 `keep|drop`，同时绑定当前计划和源媒体哈希；任一输入变化即拒绝应用。
3. 应用只写派生 `edit.decisions.json`、`delete_segments.json`、`cut.segments.json` 与 approved receipt。
4. `render-long-video-fast-segment` 默认仅预览命令；只有 `--execute` 才运行共享 FFmpeg。输出存在时拒绝覆盖，源路径与输出路径相同则拒绝。
5. 成功后写共享 FFmpeg receipt 与 duration QA；失败保留结构化回执，不自动切换硬件或云端。

## 边界

- 不自动判定观点价值或剪除低密度知识内容。
- 不自动剪除沉默中的视觉演示、PPT、情绪停顿或 B-roll。
- 不调用在线模型，不上传媒体，不自动发布。
- 首版精确渲染要求同时有视频流和音频流；无音频素材明确阻断，不静默换路线。

## 回滚

删除新增模块、Schema、CLI/Workbench 入口和文档即可恢复旧行为。所有产物均为 Bundle 派生文件；原片、Timeline、ASR/OCR 与人工证据无须回滚。
