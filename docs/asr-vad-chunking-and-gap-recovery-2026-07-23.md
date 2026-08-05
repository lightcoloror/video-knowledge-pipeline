# VKP 长音频 ASR：VAD 分块与缺段恢复

- 记录时间：2026-07-23 00:32:18 +08:00
- 执行者：Codex / GPT-5.6
- 状态：已实现首阶段本地适配；未调用在线 API

## 结论

“整段长音频单次 ASR”不是稳定的生产请求单元。VKP 采用成熟项目共有的做法：

1. 先用现有 FunASR FSMN-VAD 得到语音区间；
2. 在静音边界把语音区间聚合成中等长度请求块；
3. 相邻请求块保留少量上下文重叠；
4. 每块独立保留原始结果与质量状态；
5. 将 VAD 人声覆盖与有文字的 ASR 时间覆盖做差；
6. 只抽取未覆盖或质量失败的局部窗口重新授权、重跑；
7. 使用现有定向合并器回写，不覆盖成功分块。

这不是单纯把超时调大。超时只是延迟/完成稳定性问题；“请求最终完成但随机漏掉一段人声”属于内容稳定性失败。

## 参考实现与固定版本

| 上游 | 固定 commit | 吸收点 | VKP 决策 |
| --- | --- | --- | --- |
| OpenAI Whisper | 04f449b8a437f1bbd3dba5c9f826aca972e7709a | 约 30 秒滑窗、seek、前文条件、无语音/幻觉阈值 | 设计参考；不复制实现 |
| faster-whisper | ed9a06cd89a93e47838f564998a6c09b655d7f43 | Silero VAD、最长语音段、静音处分割、speech padding | 设计参考；VKP 复用现有 FunASR VAD，不新增第二个 VAD 运行时 |
| WhisperX | 5f2f9d4320dd93a7d12f5ba2495eef7e0a5af963 | VAD 预处理、约 30 秒逻辑块、批推理、强制对齐 | 设计参考；版本由全局源码账本和当前本地 checkout 共同验证，保留 VKP 既有 WhisperX 对齐支线 |
| Silero VAD | 未验证历史版本（当前无本地 checkout） | speech timestamps 与边界 padding | 仅保留未安装的设计候选；不作为当前实现或固定源码证据 |
| stable-ts | 未验证历史版本（当前无本地 checkout） | 静音抑制、VAD、可追踪 regroup | 仅保留设计候选；不新增第二套字幕真源，也不声称直接复用 |
| VideoCaptioner | 95842ecb5618c0b6a548a336bdfb0eb859bdb501 | 重叠分块、受控并发、单调进度和边界合并 | 延续既有独立适配；其当前实现不会隔离 `future.result()` 异常，VKP 的局部失败保留与 `degraded` 终态是独立补强，不复制 GPL-3.0 源码 |

## VKP 实际复用

- VAD：funasr_vad_runner.py，默认单个逻辑语音段最长 30 秒，GPU 可用时走 CUDA。
- 本地媒体切片：media_tools.resolve_media_tool("ffmpeg") 与统一子进程环境。
- 远程并发：consented_model_batch.py 的 TopologicalSorter、ThreadPoolExecutor 和目的地并发门。
- 质量门：asr_response_quality.py。
- 缺口片段：asr_retry_snippets.py。
- 定向回填：asr_targeted_retry_merge.py。
- 最终真源：现有 canonical transcript / Timeline，不新增第二份转录真源。

## 新增行为

### 首次请求分块

稳定入口：

    .\scripts\video-knowledge.ps1 prepare-cloud-asr-chunks <media> <funasr-vad.json> <output-dir> --max-request-seconds 180 --context-padding-seconds 1.5

默认仅生成计划和 manifest，不执行 FFmpeg。加入 --execute 也只做本地切片，不联网。

默认输出为 16 kHz、单声道、64 kbps MP3。64 kbps 是当前保守基线；同视频 32 kbps A/B 曾出现新的随机缺段，因此没有把 32 kbps 升为生产默认。

每个 manifest 固定：

- 源媒体和 VAD JSON 的 SHA-256；
- core 与 padded artifact 的起止时间；
- 对应 VAD segment IDs；
- 产物路径、字节数和 SHA-256；
- 单块成功/失败状态；
- 明确的零联网、零自动重试、零 fallback 边界。

远程调用仍须为生成后的每个精确 chunk 建立 consent。Secure MCP Tunnel 或一次业务授权只能简化确认过程，不能取消逐文件哈希和实际调用审计。

### 自动缺段检测

asr_response_quality 现在计算 VAD 语音总时长、被非空非 blocking 转录覆盖的时长、覆盖率，以及连续至少 2 秒的未覆盖语音区间。

发现缺口后：

- 整体状态为 degraded；
- quality_gate_passed=false；
- 输出 missing_speech_coverage；
- 保留所有成功文字；
- 仅生成缺口前后各 1.5 秒的 retry window；
- 不把合成的覆盖缺口伪装成 provider 失败 segment。

### VAD 自身盲区候选审计

更新：2026-07-23 01:50:17 +08:00，Codex / GPT-5.6。

仅比较 ASR 文本与 VAD 无法发现“VAD 本身没标出来”的人声。VKP 没有安装第二套 VAD，而是抽取并复用 `quality_benchmark.py` 已有的 FFmpeg `silencedetect` 实现，形成共享 `audio_silence_probe`：

    .\scripts\video-knowledge.ps1 asr-vad-activity-audit <media> <funasr-vad.json> --duration-seconds <seconds>

默认只生成计划。执行本地 FFprobe/FFmpeg：

    .\scripts\video-knowledge.ps1 asr-vad-activity-audit <media> <funasr-vad.json> --execute

审计把非静音区间作为 target、FunASR VAD 区间作为 coverage，并复用从 `asr_response_quality` 抽出的共享区间覆盖算法。连续至少 2 秒的未覆盖音频成为 `candidate_audio_activity`：

- 非静音可能是音乐、噪声或音效，绝不自动认定为语音；
- 不修改 VAD、chunk manifest 或 canonical transcript；
- 不自动切片、上传、重试或切换 provider；
- 必须经第二个语音 VAD 或人工确认。

若希望把审计作为远程分块的硬门，只接受 `passed` 且内容寻址匹配的审计：

    .\scripts\video-knowledge.ps1 asr-chunk-batch-workflow <chunk-manifest.json> --activity-audit <asr-vad-activity-audit.json> --consent-path <chunk-consent.json>

有候选盲区时 workflow 拒绝编译；审计文件、源媒体或 VAD JSON 的 SHA-256 改变后也必须重新审计。

## 稳定性口径

| 维度 | 通过条件 |
| --- | --- |
| 内容稳定 | VAD 人声覆盖无阻断缺口、Schema 合法、文本质量门通过 |
| 完成稳定 | 所有块都有终态；局部失败不丢成功块 |
| 延迟稳定 | 分块耗时分布和排队时间可观测、可预测 |
| 生产适配 | 总耗时符合业务要求，且调用数/费用在授权上限内 |

处理时间长但最终完整输出，可以是“完成稳定、内容稳定”，但不一定“延迟稳定”或“生产适配”。随机缺段即使 HTTP 200，也不能判定为稳定。

## 并发与恢复

- 不新增调度器；继续使用现有 consented_model_batch。
- 初始建议上限：全局 4、单目的地 2，实际值由 provider 限流和测得延迟调整。
- 每个 chunk 独立终态；429、5xx、超时与内容缺口分别记录。
- 本阶段不自动重试。缺口产物生成后仍需精确 consent。
- 本地池与远程池之间不自动 fallback。

## 批任务工作流编译

更新：2026-07-23 00:56:02 +08:00，Codex / GPT-5.6。

每个已完成 chunk 获得独立 consent v2 后，使用：

    .\scripts\video-knowledge.ps1 asr-chunk-batch-workflow <chunk-manifest.json> --consent-path <chunk-1-consent.json> --consent-path <chunk-2-consent.json> --bundle-dir <bundle>

该命令只生成 asr-chunk-batch-workflow.json，不提交批任务。它复用 model_connector_consent 的正式校验器，并验证：

- manifest 必须全部完成，不能把本地抽取失败静默跳过；
- chunk 与 consent 必须按顺序一一对应；
- 当前文件字节数和 SHA-256 必须同时匹配 chunk manifest 与 consent upload manifest；
- 每个 consent 必须为 active v2、剩余调用至少一次、锁定 route revision 和唯一目的地；
- max_retries_per_call 必须显式为 0；
- 最多 64 个节点，默认全局并行 4、单目的地并行 2；
- 所有节点互不依赖，交由现有 submit_consented_model_workflow_tool 和 consented_model_batch 执行。

生成的 submission.arguments 是既有 Broker MCP 工具的原生输入，不引入第二套 DAG、worker、限流器或执行状态。

## 分块执行报告合并

更新：2026-07-23 01:13:50 +08:00，Codex / GPT-5.6。

批任务结束后，使用已保存的 Trusted Connector 执行报告进行纯本地合并：

    .\scripts\video-knowledge.ps1 asr-chunk-batch-merge <asr-chunk-batch-workflow.json> --execution-report <chunk-1-report.json> --execution-report <chunk-2-report.json>

也可以用 `--batch-status-path <terminal-batch-status.json>` 读取既有批任务终态。两种输入不能混用。该命令：

- 重新校验 workflow、chunk manifest、当前 chunk 文件的字节数和 SHA-256；
- 按 consent ID 归位，因此报告传入顺序不影响结果；
- 复用 `asr_adapter.read_asr_segment_dicts`，不新增第二个 ASR normalizer；
- 按 `artifact_start` 平移 segment 和 word 时间戳；
- 以 segment 中点属于哪个 core 决定 padding 所有权，padding 只提供上下文；
- 仅在“规范化文本完全相同且时间强重叠”时自动去重；
- 相似但不相同的边界文本一律输出 `boundary_conflicts`，不做模糊自动拼接；
- 任一 chunk 失败或缺失时保留其他成功 segment，并以 `degraded` 终态生成 VAD 覆盖缺口和精确局部重跑窗口；
- 输出独立的 JSON、SRT 与 merge report，不修改 canonical transcript。

输出默认位于 workflow 相邻的 `asr-chunk-merge`：

- `asr-chunk-merged-transcript.json`
- `asr-chunk-merged-transcript.srt`
- `asr-chunk-merge-report.json`

合并报告可以直接交给既有缺口切片器：

    .\scripts\video-knowledge.ps1 asr-retry-snippets <original-media> <asr-chunk-merge-report.json> <retry-output-dir>

该适配会读取报告内的嵌套 `asr_quality.retry_plan`，先验证原媒体字节数与 SHA-256，再复用统一 FFmpeg 解析器生成精确 WAV。默认仍只是计划；`--execute` 只执行本地 FFmpeg。每个成功 WAV 仍须单独进入 consent/业务授权和既有 Broker，不能从合并报告直接获得上传权限。

因此完整恢复闭环已经成为：`VAD → chunk manifest → consent/Broker batch → merge report → exact retry snippets → consent/Broker retry → targeted merge`。最后一步继续复用 `asr_targeted_retry_merge`，保留时间戳和未命中 segment，不新增第二套 canonical transcript。

这对应成熟实现的共同边界：重叠窗口解决切词上下文，确定性时间规则解决所有权，强制对齐可作为可选后处理；不能把字符串模糊相似度当作事实改写依据。

## 尚未覆盖

- 尚未用完整视频做分块路线与整段路线的真实 A/B；需要用户对精确 chunk 清单单独授权后才能进行。
- FFmpeg 活动探针能暴露 VAD 可疑盲区，但它不是语音分类器；候选仍需第二语音 VAD 或人工确认，不能静默补入 VAD。
- WhisperX 强制对齐仍是可选后处理，不应成为所有 ASR 的强制成本。

## 离线验证

- focused：20 passed。
- batch workflow compiler focused：6 passed。
- batch workflow、consent v2、业务授权、批调度与 ASR 扩展兼容：106 passed。
- chunk merge focused：7 passed，覆盖乱序、缺块、manifest/chunk 篡改、padding、精确去重、边界冲突、批终态与 CLI。
- merge-to-retry 闭环 focused：10 passed。
- 全部 ASR、consent/batch、业务授权与 CLI 相关扩展回归：164 passed、1 个既有 jieba/pkg_resources warning。
- VAD 活动探针、workflow 硬门、篡改阻断与质量门行为保持 focused：39 passed。
- 全部 ASR 与质量基准扩展回归：207 passed、1 个既有 jieba/pkg_resources warning。
- 扩展 ASR/缺口抽取/定向合并/云端计划/批调度/CLI 合同：95 passed。
- Ruff：All checks passed。
- compileall：通过。
- 全仓：1080 passed、2 failed、1 warning，耗时 343.24 秒。
- 两项失败均不在本轮 ASR 改动面：
  - Google Gemini catalog probe fixture 返回模型名与当前预填目录不一致；
  - vision fast-triage 的旧测试仍期望 Browserbase term conflict 自动进入 semantic indexes。
- 本轮没有修复或回退上述并发改动。

## 开源项目如何处理长音频随机缺段

更新：2026-07-23 02:24:00 +08:00，Codex / GPT-5.6。

只把 provider 超时加长不是主流解法。源码核对显示，成熟实现通常把问题拆成以下几层：

| 项目与固定版本 | 实际机制 | VKP 吸收判断 |
| --- | --- | --- |
| VideoCaptioner 95842ecb5618c0b6a548a336bdfb0eb859bdb501 | 当前可执行常量为 10 分钟一块、10 秒重叠、并发 3；重叠区做文本对齐并恢复绝对时间戳。其 docstring 仍写 8 分钟，故只采纳机制，不照抄默认数值 | 已独立适配为更保守的 VAD 对齐 180 秒块、1.5 秒 padding、确定性 core 所有权；不复制 GPL-3.0 源码 |
| AI-Video-Transcriber ade833b790d482f7a5c0a722c67bc33f71e9d2b5 | faster-whisper + Silero VAD；900ms 静音阈值、300ms speech padding；关闭 previous-text 串联并检查无语音、压缩比和 log-prob | 参数与失败信号作为设计证据；不新增 Silero 运行时，也不照搬全局 previous-text 策略 |
| Transcribe Critic（历史候选，版本证据待恢复） | 历史审查笔记曾记录多 ASR 独立见证、LCS/wdiff 对齐、只裁决差异和逐块 checkpoint，但当前磁盘没有 checkout、全局源码账本条目或独立审查证据 | 不作为当前实现的权威来源；VKP 只保留由仓库自身测试证明的多源仲裁和局部纠错，不把未验证参考稿引入提示或事实层 |
| FunASR 516c4f770496a5cbb89c8e2e447211bbb7b0db71 | FSMN-VAD 配置可覆盖 speech_noise_thres、max_end_silence_time、起止点阈值和最大单段时长 | 直接复用已安装 FSMN-VAD；新增参数化候选复核入口，不安装新模型 |

组合后的生产最佳实践是：

1. 把长音频切成有界请求单元，而不是依赖 provider 宣称的最大时长；
2. 分块必须有重叠或 padding，避免一句话在边界被切断；
3. 每块独立保存输入哈希、输出、终态和检查点，局部失败不能丢掉成功块；
4. 合并优先使用时间戳和明确的 core 所有权；模糊文本相似只提示冲突，不能静默删改；
5. 用 VAD/音频活动/ASR 文字覆盖交叉检查缺口；
6. 只重跑缺口，不重跑整段；
7. 重要内容可引入第二 ASR 见证，但只裁决差异，不能让 LLM 重写全部逐字稿；
8. 完成稳定、内容稳定、延迟稳定分别计量，HTTP 200 不等于内容完整。

## 源码证据对账

- Updated: `2026-07-23 04:21:08 +08:00` by `Codex / GPT-5.6`.
- Corrected: `2026-07-23 04:39:04 +08:00` by `Codex / GPT-5.6`. Rechecked VideoCaptioner `chunked_asr.py`: executable constants are 10-minute chunks, 10-second overlap and concurrency 3; its stale 8-minute docstring is not treated as runtime truth.
- `VideoCaptioner` 已通过 `source-ledger.ps1` 登记到全局源码账本；本地 HEAD、远端 URL 和 GPL-3.0 许可证均已核对。
- `WhisperX` 文档固定版本已改为全局账本和当前 checkout 都能证明的 `5f2f9d4320dd93a7d12f5ba2495eef7e0a5af963`。此前记录的 `2cfd7b7c5c7bba144954364db747319b50e8232b` 不在当前本地对象库，不能继续作为已验证版本。
- `Transcribe Critic` 当前仅有项目内历史文字记录，缺少可复核源码，因此降级为历史候选；重新取得固定源码和许可证证据前，不得据此声称直接复用或已吸收。
- `OpenAI Whisper` 与 `faster-whisper` 的 HEAD、origin、MIT 许可证均与全局源码账本一致，继续作为已验证设计参考。
- `stable-ts` 与 `Silero VAD` 当前没有本地 checkout 或全局账本证据；此前仅见于项目文档的 commit 字符串已降级为未验证历史版本。

## FunASR 严格/宽松双配置证据

funasr_vad_runner 现在直接复用 FunASR 官方的配置覆盖能力，新增：

- --speech-noise-threshold：默认 0.6；降低会提高召回，也会增加音乐/噪声误报；
- --max-end-silence-time-ms：默认 800ms；增大可减少短暂停顿造成的切碎；
- --evidence-profile authoritative 或 candidate-permissive。

建议先保留默认权威运行，再仅为 FFmpeg 活动审计发现的候选区域生成宽松证据。例如宽松候选配置可从 0.35 和 1100ms 起做固定样本校准，但这不是未经测量即可提升为生产默认的参数。

宽松运行输出会固定记录模型、revision、设备和完整 VAD 参数，并强制带有 evidence_profile=candidate-permissive 和 candidate_only=true。

因此同一 FSMN-VAD 的第二遍运行只能缩小人工复核范围，不能被当成独立模型投票，也不能自动改写主 VAD、chunk manifest 或 canonical transcript。若要自动关闭候选盲区，仍需独立语音证据源或人工确认。

本次只增加本地 runner 参数和离线测试，没有执行模型、下载依赖、调用 API 或上传媒体。

验证：focused 2 passed；扩展 ASR/质量基准选择集 230 passed、1 个已知且无关的 vision fast-triage 旧断言失败、1 warning；Ruff、compileall、diff check 通过。

## 严格/宽松配置离线校准

更新：2026-07-23 02:46:00 +08:00，Codex / GPT-5.6。

稳定本地入口：

    .\scripts\video-knowledge.ps1 asr-vad-profile-compare <authoritative-vad.json> <candidate-permissive-vad.json> <activity-audit.json>

该适配器复用 interval_coverage、既有 VAD JSON、活动审计与 SHA-256 内容绑定，不引入 pyannote、第二套 VAD 或新音频算法。它会：

- 验证活动审计确实绑定当前 authoritative VAD；
- 验证两次运行使用相同输入、模型、revision 与最大分段时长；
- 拒绝阈值更严格或结束静音更短的伪 permissive 配置；
- 对每个活动候选计算宽松 VAD 覆盖率；
- 列出宽松 VAD 相对正式 VAD 新增的区间，以及缺少音频活动支持的区间；
- 所有同模型支持仍保持 candidate-only，绝不自动关单。

没有提供人工标签时，同时生成：

    asr-vad-human-labels.template.json

模板精确绑定 authoritative VAD、permissive VAD 和 activity audit 的 SHA-256。人工只填写 speech、non_speech 或 uncertain，再次运行：

    .\scripts\video-knowledge.ps1 asr-vad-profile-compare <authoritative-vad.json> <candidate-permissive-vad.json> <activity-audit.json> --labels-path <filled-labels.json>

报告会计算候选筛选的 confusion counts、precision 和 recall。该指标只描述“VAD 盲区候选筛选”，不能冒充整段音频的总 VAD 精度；报告始终设置 production_default_change_allowed=false。只有在固定样本、明确验收阈值和人工标签都齐全后，才能另行决定是否调整生产默认参数。

本轮校准适配器、runner、活动审计、分块 workflow 与合并链 focused 验证：31 passed；Ruff、compileall、diff check 通过。

## 本地 GPU 固定样本校准

更新：2026-07-23 02:28:38 +08:00，Codex / GPT-5.6。

使用已缓存的 FunASR FSMN-VAD，在 CUDA 上对两个既有固定 WAV 做了真实严格/宽松对比，没有下载模型或调用在线 API：

- sample-1-01：73.57 秒连续讲话。严格 0.6/800ms 与宽松 0.35/1100ms 都输出 8 段，活动覆盖率 99.701%，宽松配置没有新增覆盖。报告状态为 no_candidates，不再生成空人工标签任务。
- sample-20250306-01：84.44 秒，FFmpeg 检出 3 段共约 5.43 秒静音。两组 FSMN-VAD 都输出相同 10 段；以 0.25 秒短缺口门槛发现开头 0.00–0.38 秒一个候选，但宽松 VAD 仍未覆盖，状态 unresolved，必须人工或独立语音证据确认。

产物：

- .local/vad-profile-calibration-20260723/sample-1-01/asr-vad-profile-comparison.json
- .local/vad-profile-calibration-20260723/sample-20250306-01/asr-vad-activity-audit.json
- .local/vad-profile-calibration-20260723/sample-20250306-01/asr-vad-profile-comparison.json
- .local/vad-profile-calibration-20260723/sample-20250306-01/asr-vad-human-labels.template.json

结论：当前固定样本不支持把宽松参数提升为生产默认；它验证了门控能把复核范围压缩到精确的 0.38 秒，而不是重跑 84 秒或完整视频。同一 FSMN-VAD 的宽松第二遍不是独立证据。下一步应先给该 0.38 秒候选标注 speech/non_speech/uncertain，再把相同协议扩到含弱音、背景音乐和多人交叠的固定样本。

零候选状态回归已修复；focused 8 passed，Ruff 与 diff check 通过。

## VKP 自有的批提交前门

更新：2026-07-23 02:38:32 +08:00，Codex / GPT-5.6。

完成度审计发现，asr-chunk-batch-workflow 虽已生成 Broker 原生 arguments，但此前仍需 Agent 手工调用 MCP。现在增加稳定前门：

    .\scripts\video-knowledge.ps1 asr-chunk-batch-submit <workflow.json>

默认只做本地预检：重新读取 manifest、chunk 哈希、consent v2、route revision、活动审计和并发设置，并重新计算 workflow identity。任何输入改变都会在联网前阻断。

显式提交：

    .\scripts\video-knowledge.ps1 asr-chunk-batch-submit <workflow.json> --execute

该入口直接复用项目已有的 mcp.ClientSession、streamablehttp_client 和 submit_consented_model_workflow_tool，只允许 loopback HTTP /mcp 地址。CLI 只发一个控制请求，不读取 API Key、不接收 provider URL、不直接请求供应商，也不新增 retry、fallback、调度器或状态库。远程执行、原子 reservation、并发和持久状态继续由 Trusted Capability Broker 负责。

返回 job_id 后继续使用现有 consented_model_batch_status_tool；终态报告再交给 asr-chunk-batch-merge。这样完整链路由 VKP 自己的稳定入口驱动，不再依赖 Codex 代替项目调用在线 API。

离线验证覆盖 preview、loopback 限制、陈旧 workflow、单次 Broker 控制调用、结构化 MCP 响应和 CLI 默认行为：6 passed；连同 workflow/MCP 合同共 15 passed。

## 共享 Broker 客户端与只读状态入口

更新：2026-07-23 02:49:42 +08:00，Codex / GPT-5.6。

提交后轮询状态也已从 Agent 手工 MCP 调用迁移为 VKP 稳定入口：

    .\scripts\video-knowledge.ps1 asr-chunk-batch-status <job_id>

需要保存终态供合并时：

    .\scripts\video-knowledge.ps1 asr-chunk-batch-status <job_id> --output-path <terminal-status.json>
    .\scripts\video-knowledge.ps1 asr-chunk-batch-merge <workflow.json> --batch-status-path <terminal-status.json>

实现没有复制第二份 MCP 客户端：从现有 scripts/smoke-trusted-capability-broker-http.py 和 asr_chunk_batch_submit 提取 trusted_broker_http_client，统一复用 mcp.ClientSession、streamablehttp_client、loopback URL 门和机器 JSON 响应解析。submit 与 status 都使用该模块。

状态输出保存时保持原始 video_knowledge_pipeline.consented_model_batch.v1 schema，因此既有 merge 可直接消费；没有新 wrapper 真源、轮询状态机或状态数据库。URL 中的 userinfo、query、fragment、非 loopback 地址都会在建立连接前拒绝。

离线合同验证覆盖共享客户端、真实 accepted/job_id 提交回执、只读状态查询、原始状态保存、job_id 绑定、CLI、workflow 和既有批管理器：26 passed；加入既有 merge 后 submit→status→merge 组合回归 34 passed；Ruff 通过。

## 合并后可选的成熟强制对齐

更新：2026-07-23 03:02:39 +08:00，Codex / GPT-5.6。

源码审计确认：

- WhisperX 已有稳定 VKP 入口，适合词级时间戳、说话人和独立 alignment evidence，但它会自己转写，不适合作为“保持当前合并文字不变”的默认对齐器。
- 官方 Qwen3 ForcedAligner 已通过现有 qwen-asr Python 适配器接入，接受已有 transcript_path，运行结果明确是 alignment sidecar，run_asr_plan 不会调用 normalize 或替换主逐字稿。
- stable-ts 的静音抑制和可追踪 regroup 继续作为设计参考；不再实现第三套本地对齐算法。

因此 asr-chunk-batch-merge 新增显式开关：

    .\scripts\video-knowledge.ps1 asr-chunk-batch-merge <workflow.json> --batch-status-path <terminal-status.json> --prepare-alignment-plan

它只复用 plan_asr_run 生成 qwen3-forced-aligner 计划，不执行模型。计划输入精确绑定合并 transcript SHA-256 和原媒体 SHA-256。只有 merge=completed、Bundle 已在 workflow identity 中锁定、原媒体未变化时才允许生成。

默认不生成计划。对齐计划或本地运行时不可用时，merge 仍保持 completed，JSON/SRT 和报告继续写出，alignment_advisory 标记 plan_failed。对齐结果只能作为时间戳 sidecar；canonical_text_replaced_by_alignment 始终为 false。

验证：merge focused 11 passed；既有 ForcedAligner sidecar、Qwen3 时间戳和 WhisperX 主文本边界 3 passed；submit→status→merge→alignment-plan→局部 retry 完整离线合同 40 passed；Ruff 与 CLI help 通过。
## 一次确认的分块 ASR 编排与任务真源

更新：2026-07-23 03:57:04 +08:00，Codex / GPT-5.6。

已确认的 `model_business_authorization.v1` 现在可以直接复用于整组 ASR chunk：

    .\scripts\video-knowledge.ps1 asr-chunk-business-workflow <chunk-manifest.json> <business-authorization.json> --stage-id <cloud-asr-stage> --producer asr_vad_chunking --lineage-input <exact-source-media>

该命令是窄编排层，不创建第二套授权或执行器：

- 对 manifest 中每个已完成 chunk 调用既有 `create_business_child_consent`；
- 每个文件仍锁定绝对路径、字节数、SHA-256、route revision、目的地、一次调用、零重试和费用；
- 操作者不再逐块重复确认，父授权边界内的 child consent 标记为 `parent_business_authorization`；
- 完全相同的 lineage 重跑会幂等复用既有 child consent，即使父授权额度已经全部分配；
- 随后直接复用 `build_asr_chunk_batch_workflow`，不会提交批任务或调用 provider；
- `--no-write` 只预览将要创建的精确 child consent，不写父授权、子 consent 或 workflow；
- Bundle override 必须与父授权绑定的 Bundle 完全一致。

merge 写入时会复用 `register_bundle_run`，把候选 transcript 与 SRT 登记为 `asr_chunk_merge` run。Task Console 与 Workbench 因而继续读取同一个 Bundle/run registry；没有新增状态数据库。degraded/review_required run 会记录失败 chunk、局部 retry 命令和零自动 retry/fallback 边界。

离线验证：业务授权、workflow、submit、status、merge 与 run registry 联合回归 42 passed。
### 批量写入前的累计容量预检

更新：2026-07-23 04:10:02 +08:00，Codex / GPT-5.6。

`asr-chunk-business-workflow` 现在会在写入第一个 child consent 前调用通用 `preflight_business_child_consents`。预检逐项复用正式 child-consent preview 来验证路径、lineage、producer、route 和单文件上限，再复用既有 `_require_capacity` 在内存影子父授权上累计模拟调用数、费用、文件数与总字节数。

因此可预测的第 N 块超限会在任何父授权 admission 或 consent 文件写入前失败。预检本身不写文件、不调用 provider；通过后，实际创建仍逐项使用原有 `bundle_write_lock`、幂等 identity、原子 JSON 与 parent binding。进程级 I/O 中断可能留下未被父 admission 引用的孤立文件，但该文件无法通过 parent-authorized consent 校验，不能执行。

离线联合验证：43 passed；Ruff、compileall 与 diff check 通过。

## 独立 Silero VAD 候选证据

更新：2026-07-23 07:21:21 +08:00，Codex / GPT-5.6。

此前“第二语音 VAD”被保留为未安装候选。重新核对当前运行环境后确认，VKP 已有的 `faster-whisper 1.1.1` 安装包内已经携带 Silero v5 encoder/decoder ONNX，且 `onnxruntime` 可用。因此本轮没有安装依赖、下载模型或复制上游算法，而是直接适配成熟上游 API：

- `faster_whisper.audio.decode_audio`
- `faster_whisper.vad.VadOptions`
- `faster_whisper.vad.get_speech_timestamps`

本地执行：

    .\scripts\video-knowledge.ps1 silero-vad-candidate <media> --execute

与权威 FunASR VAD 交叉核验：

    .\scripts\video-knowledge.ps1 asr-vad-independent-crosscheck <funasr-vad.json> <silero-vad-candidate.json> --activity-audit <asr-vad-activity-audit.json>

行为边界：

- Silero 输出固定为 `candidate-independent` / `candidate_only=true`；
- 记录源媒体 SHA-256、`faster-whisper` 版本、上游 API、两份 ONNX 的路径/字节数/SHA-256 和全部 VAD 参数；
- 默认 preview 不导入或加载模型；`--execute` 只运行当前 Python 环境已安装的本地模型；
- 明确禁止模型下载、网络调用、自动上传、自动重试和 local/cloud fallback；
- 交叉核验只输出“Silero 判断为语音、但 FunASR 未覆盖”的候选窗口；即使 FFmpeg 音频活动也支持，仍只能进入定向 ASR 或人工确认；
- 不修改权威 FunASR VAD、chunk manifest、Timeline 或 canonical transcript。

真实本地 smoke 使用既有 `speech.wav`（158292 bytes）运行成功：Silero v5 返回一个 0.0–3.588375 秒语音区间；两份随包 ONNX 合计约 1.19 MiB。运行没有下载、联网或写入产物。

验证：47 passed，Ruff 通过；覆盖 preview 不加载模型、上游参数透传、样本时间换算、模型 provenance、媒体篡改阻断、独立候选缺口、活动证据支持、CLI 和既有 VAD/质量门/分块合并兼容。
## 时间重叠指标复用审计

- Updated: 2026-07-23 07:42:35 +08:00 by Codex / GPT-5.6.
- ASR 共识窗口使用 temporal IoU；重叠 chunk 的精确文本去重使用“交集 / 较短区间”；逐字稿来源仲裁使用“交集 / 左侧 cue”。三者分母不同，不能共用一个含糊的 overlap ratio。
- 前两项已复用 interval_coverage 的显式原语，后者因 10ms 最小时长与方向性规则不同而保留。
- 当前环境没有 portion 或 intervaltree，为简单数值运算新增依赖没有收益；文本相似度继续复用 Python 标准库 difflib.SequenceMatcher，不切换到分数不兼容的 RapidFuzz。
- 49 项 ASR 分块合并、共识和纠错链测试通过；没有发起在线 ASR。
## SimulStreaming LocalAgreement 边界证据适配

- 更新：2026-07-23 08:15:09 +08:00，Codex / GPT-5.6。
- 固定上游：`ufal/SimulStreaming` commit `077ea37d5ab4ff98bc567e4507f140dc4e5d5ad6`，MIT；本地源码位于 `%WORKSPACE_ROOT%\source-reviews\asr-long-form-wave-20260723\SimulStreaming`。
- 直接吸收点：`LocalAgreement.trim_longest_common_prefix` 的“相邻输出只确认公共前缀”契约。
- VKP 适配：对分块合并中已经由时间强重叠判定为冲突的两段，中文/日文按字符、其他语言按空白词计算公共前缀和 `agreement_over_shorter`，并固定上游 commit/API/license provenance。
- 安全边界：结果始终为 `candidate_only=true`、`automatic_merge_allowed=false`；不改变精确去重、core 所有权、边界人工复核、canonical transcript 或定向重跑规则。
- 拒绝项：未引入 SimulStreaming 的 Whisper/EuroLLM 运行时、TCP 服务、流式 buffer、第二套状态机或重复 provider 调用。它的流式策略解决输出稳定性，不替代 VKP 的 VAD 覆盖缺口检测。
- 验证：LocalAgreement 单元测试覆盖中文、英文、完全相等、空文本；连同 ASR merge、质量门、局部重跑、VAD 和 Silero 交叉核验共 61 项离线测试通过，Ruff 通过。
## WhisperStreaming 时间戳 HypothesisBuffer 适配

- 更新：2026-07-23 08:25:04 +08:00，Codex / GPT-5.6。
- 固定上游：`ufal/whisper_streaming` commit `6da90b44b7e50d79695e68166d2a2c7609c75abb`，MIT；`LICENSE` SHA-256 为 `daafd729865f1acad715b79d2585df23d10263579dccbf0bad87830cd94d4bec`。
- 直接吸收点：`HypothesisBuffer.insert/flush` 先使用时间位置过滤旧词，再只确认连续两次假设的最长公共词前缀。
- VKP 适配：只在现有强时间重叠边界冲突内读取已经平移到绝对时间的 `metadata.words`，按真实 overlap 半开区间裁剪两侧词序列，再输出公共词前缀、较短侧一致率、首词起点差和上游一秒容差证据。
- 降级语义：任一侧缺少词级时间戳时，`status=unavailable`、`usable_for_review_ranking=false`；纯文本 LocalAgreement 仍可展示，但不能冒充时间对齐证据。
- 安全边界：`candidate_only=true`、`automatic_merge_allowed=false`；不改变 exact dedup、core ownership、人工复核、canonical transcript、VAD 覆盖或局部重跑。
- 拒绝项：上游已由 SimulStreaming 取代，因此不部署旧流式服务器、VAC、Whisper backend 或状态缓冲；只适配仍适用于离线重叠输出的 HypothesisBuffer 契约。
- 验证：时间戳裁剪、中文公共词前缀、缺时间戳降级、绝对 offset 合并 fixture，以及相关 VAD/质量门/局部重跑共 63 项离线测试通过；Ruff、py_compile 通过。
## 完整词时间戳优先的 VAD 覆盖审计

- 更新：2026-07-23 08:50:17 +08:00，Codex / GPT-5.6。
- 直接复用现有 `asr_adapter.read_asr_word_timestamps` 统一解析 provider 顶层或 `metadata.words` 词时间戳，不创建第二套响应解析器。
- 只有当有效词时间戳按顺序拼接、经既有 `compact_ascii_cjk` 规范化后与完整 segment 文本严格一致，质量门才使用词级区间审计 VAD 覆盖；这能发现被一个大 segment 起止边界掩盖的内部静音或漏转窗口。
- 缺失、非法或只覆盖部分文本的词时间戳会显式降级为 segment 边界，并分别记录 `word_timestamps_missing_or_invalid` 或 `word_timestamp_text_incomplete`，避免把稀疏时间戳误判成真实缺段。
- 该证据只影响缺口检测、局部重跑候选和 degraded 状态，不自动修改 canonical transcript、不自动发起重试，也不触发 provider、上传或 fallback。
- 既有三个真实长视频的 Groq ASR 产物均没有词级时间戳；三者都在后续复核或同模型 A/B 中发现了缺段或异常窗口，因此旧质量门未报警不能反推“没有缺段”。这项增强改善未来含完整词时间戳的运行，不能追溯性地证明旧产物完整。
- 验证：113 项 ASR pipeline、响应质量、局部重跑、分块合并、LocalAgreement、VAD 与 Silero 相关离线测试通过；Ruff、AST 解析和 scoped diff check 通过。
## Groq 词级时间戳与 LiteLLM transport 修正

- 更新：2026-07-23 09:11:26 +08:00，Codex / GPT-5.6。
- 官方依据：[Groq Speech to Text](https://console.groq.com/docs/speech-to-text) 明确支持 `verbose_json` 和 `timestamp_granularities[]=word|segment`，并建议长音频采用重叠分块、独立转写和重叠合并。
- 上游审计：本机 LiteLLM 1.81.7 的 `GroqSTTConfig.get_supported_openai_params_stt` 未声明 `timestamp_granularities`；2026-07-23 复核上游稳定版 [v1.86.2 同一适配器](https://raw.githubusercontent.com/BerriAI/litellm/v1.86.2/litellm/llms/groq/stt/transformation.py) 仍然缺失。安装文件 SHA-256 为 `e569a2ea043eee7002f208f91a2d330b31e44de70e59521bc57ea995869152d9`。
- 复用决策：沿用项目中 Mistral ASR 已验证的模式，保留 `provider=groq_asr`、Groq 目的地和模型身份，只把 `litellm_provider` 规范化为 LiteLLM 的 `openai` transcription transport；没有新增厂商 HTTP 客户端或复制 LiteLLM 实现。
- 配置契约：Groq profile 自动预填 `asr_timestamp_granularity=word`。该选项与 transport 都进入 deployment 和 route revision；旧 `litellm_provider=groq` 配置只读加载时安全迁移，不需要重新填写 DPAPI API Key，但下一次远程执行必须按新 revision 创建 consent。
- 输出适配：Groq 请求单次返回词级时间戳。LiteLLM Proxy 当前会折叠重复 multipart 数组项，因此不伪称同时获得原生 word+segment；word-only 响应复用既有 Qwen3 forced-alignment 分段逻辑生成 VKP segment，并保留每个词的起止时间。
- 安全边界：没有修改现有 `.local/litellm-config.yaml`、没有启动或重启网关、没有调用 Groq、没有上传音频。操作者下一次正常启动网关时才会从设置渲染新 transport；真实供应商 smoke 仍需单独有效 consent。
- 验证：93 项 provider catalog、onboarding、设置 UI、runtime client、ASR connector normalization 和 response quality 离线测试通过；Ruff、AST 与当前设置只读迁移预览通过。

## Whisper / faster-whisper 词级异常质量信号

2026-07-23 10:04:30 +08:00 | Codex / GPT-5.6

- 直接适配固定上游 openai/whisper@04f449b8a437f1bbd3dba5c9f826aca972e7709a 与 SYSTRAN/faster-whisper@ed9a06cd89a93e47838f564998a6c09b655d7f43 共同实现的 word_anomaly_score / is_segment_anomaly。
- 保留上游阈值：词概率低于 0.15、词时长短于 0.133s、长于 2.0s，只检查前 8 个非标点词；累计分数达到 3 或接近词数时标记异常。
- VKP 的适配边界：只有词时间戳与词概率/score/confidence 都完整时才评估。在线 API 只返回 start/end 而不返回概率时明确记为 not_evaluated，不能把缺失字段按上游内部默认的 0 概率误判成幻觉。
- 命中项为 whisper_word_anomaly 人工复核与精确局部重跑候选；保留原文，不自动删除、替换、重跑、fallback 或提升为事实。
- 离线验证：focused 25 passed；扩展 ASR/VAD/分块/第二证据源回归 198 passed、1 个既有 jieba/pkg_resources warning。
- 对既有 Groq 真实长视频响应只读复核：54 段均无词概率，新增信号 0 anomaly / 54 not_evaluated；原有 degraded 与单个 retry window 不变，没有追溯性改写产物。