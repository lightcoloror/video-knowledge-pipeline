# 三个获客视频重跑与质量对比报告

- 生成时间：2026-07-08 11:38:44
- 执行者：Codex / GPT-5
- 范围：3 个从 32 个视频中筛出的获客实战价值最高样本；每个视频比较得到大脑转写结果与本地 SenseVoice/FunASR ASR 结果。得到大脑结果只作为评测标尺和人工参考，不作为 VKP 自动语义纠错的 external transcript 证据源。
- 本轮动作：重跑本地 ASR、重建 local-ASR bundle、重跑语义纠错 pack/closure/impact、尝试方舟 Coding Plan 智能总结 LLM rewrite、刷新导出与质量检查。

## 结论先行

1. 逐字稿层：本地 SenseVoice/FunASR 已成功重跑，覆盖全时长；得到大脑转写仍更适合直接阅读，优势主要在标点、段落和语义压缩。
2. 本地 ASR 的段数显著高于得到大脑，但正文字数更少且几乎没有标点；它覆盖全时长、颗粒度更细，但更像原始机器底稿，会拉低直接阅读体验和总结输入质量。
3. 智能总结层：方舟 Coding Plan 的 `run-smart-summary-llm-rewrite` 本轮未稳定产出可通过门禁的最终总结，主要是 read timeout，另有一次 HTTP 400。
4. 因此本轮结论是：逐字稿层已可对比；最终智能总结层仍未达到得到大脑的稳定可读质量，核心缺口是章节级 LLM 改写/后处理，而不是 ASR 是否能跑。
5. 已修正 smart-summary 质量门禁：无高置信自动纠错时不再阻塞导出，但候选错词仍保留为可选复核风险。

## 本轮执行证据

- ASR 重跑汇总：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\local-asr-run-summary.json`
- bundle 重建汇总：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\asr-vs-getbrain-vkp-build-summary.json`
- 语义纠错重跑汇总：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\rerun-semantic-correction-summary.json`
- LLM rewrite 尝试汇总：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\rerun-smart-summary-llm-rewrite-summary-2.json`

## 逐字稿质量指标

| 视频 | 来源 | 时长 | 段数 | 正文字数 | 平均字/段 | 标点/千字 | 覆盖到 | 逐字稿路径 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 明亚保险人小红书保险获客与客户经营实战分享 | 得到大脑转写输入 | 01:07:26 | 112 | 27392 | 244.6 | 92.69 | 01:07:01 | `%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\从小红书引流300-到成交-一套可复制的获客闭环\webui-bundle\exports\full-transcript.md` |
| 明亚保险人小红书保险获客与客户经营实战分享 | 本地 SenseVoice ASR | 01:07:26 | 1137 | 18837 | 16.6 | 0.0 | 01:07:25 | `%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\从小红书引流300-到成交-一套可复制的获客闭环\local-asr-vkp\webui-bundle\exports\full-transcript.md` |
| 保险经纪人线下活动获客分享——基于趣研学俱乐部的亲子拓客实践 | 得到大脑转写输入 | 01:33:26 | 129 | 42778 | 331.6 | 80.23 | 01:32:12 | `%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\20250306没客户-通过活动来获客-王彩娥\webui-bundle\exports\full-transcript.md` |
| 保险经纪人线下活动获客分享——基于趣研学俱乐部的亲子拓客实践 | 本地 SenseVoice ASR | 01:33:26 | 1000 | 30535 | 30.5 | 0.0 | 01:33:26 | `%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\20250306没客户-通过活动来获客-王彩娥\local-asr-vkp\webui-bundle\exports\full-transcript.md` |
| 明亚领航计划：陌生客户成交转化高频问题及应对技巧 | 得到大脑转写输入 | 00:17:39 | 27 | 8432 | 312.3 | 93.22 | 00:16:19 | `%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\1-首次沟通环节的高频问题\webui-bundle\exports\full-transcript.md` |
| 明亚领航计划：陌生客户成交转化高频问题及应对技巧 | 本地 SenseVoice ASR | 00:17:39 | 323 | 5326 | 16.5 | 0.0 | 00:17:39 | `%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\1-首次沟通环节的高频问题\local-asr-vkp\webui-bundle\exports\full-transcript.md` |

### 逐字稿层判断

- **明亚保险人小红书保险获客与客户经营实战分享**：本地 ASR 正文字数相对得到大脑 -8555；标点密度差 -92.69/千字。本地稿覆盖更细、但字数更少且无标点；得到大脑稿更像可阅读转写。
- **保险经纪人线下活动获客分享——基于趣研学俱乐部的亲子拓客实践**：本地 ASR 正文字数相对得到大脑 -12243；标点密度差 -80.23/千字。本地稿覆盖更细、但字数更少且无标点；得到大脑稿更像可阅读转写。
- **明亚领航计划：陌生客户成交转化高频问题及应对技巧**：本地 ASR 正文字数相对得到大脑 -3106；标点密度差 -93.22/千字。本地稿覆盖更细、但字数更少且无标点；得到大脑稿更像可阅读转写。

## 智能总结质量指标

| 视频 | 来源 | quality | 失败项 | LLM 状态 | LLM 错误 | 标记 | 总结长度 | 覆盖到 | 输出路径 |
|---|---:|---:|---|---:|---|---|---:|---:|---|
| 明亚保险人小红书保险获客与客户经营实战分享 | 得到大脑转写输入 | failed | codex_final, balanced_sections | The read operation timed out | The read operation timed out | codex_llm_rewrite_final | 6584 | 01:07:25 | `%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\从小红书引流300-到成交-一套可复制的获客闭环\webui-bundle\exports\smart-summary.md` |
| 明亚保险人小红书保险获客与客户经营实战分享 | 本地 SenseVoice ASR | failed | codex_final, segment_not_asr_dump, balanced_sections | The read operation timed out | The read operation timed out | codex_llm_rewrite_final | 23994 | 01:07:25 | `%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\从小红书引流300-到成交-一套可复制的获客闭环\local-asr-vkp\webui-bundle\exports\smart-summary.md` |
| 保险经纪人线下活动获客分享——基于趣研学俱乐部的亲子拓客实践 | 得到大脑转写输入 | failed | codex_final, balanced_sections | The read operation timed out | The read operation timed out | codex_llm_rewrite_final | 7642 | 01:33:26 | `%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\20250306没客户-通过活动来获客-王彩娥\webui-bundle\exports\smart-summary.md` |
| 保险经纪人线下活动获客分享——基于趣研学俱乐部的亲子拓客实践 | 本地 SenseVoice ASR | failed | codex_final, segment_not_asr_dump, balanced_sections | HTTP Error 400: Bad Request | HTTP Error 400: Bad Request | codex_llm_rewrite_final | 35957 | 01:33:26 | `%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\20250306没客户-通过活动来获客-王彩娥\local-asr-vkp\webui-bundle\exports\smart-summary.md` |
| 明亚领航计划：陌生客户成交转化高频问题及应对技巧 | 得到大脑转写输入 | failed | codex_final, balanced_sections | The read operation timed out | The read operation timed out | codex_llm_rewrite_final | 5088 | 00:17:39 | `%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\1-首次沟通环节的高频问题\webui-bundle\exports\smart-summary.md` |
| 明亚领航计划：陌生客户成交转化高频问题及应对技巧 | 本地 SenseVoice ASR | failed | balanced_sections | The read operation timed out | The read operation timed out | codex_llm_rewrite_final | 4285 | 00:17:39 | `%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\1-首次沟通环节的高频问题\local-asr-vkp\webui-bundle\exports\smart-summary.md` |

### 智能总结层判断

- 得到大脑原始 Logseq 文稿仍是当前最稳定的人类可读参考，路径见下方逐视频产物表。
- VKP 已能稳定生成 `knowledge-note.md`、`full-transcript.md`、`smart-summary.md`，但本轮 `smart-summary.md` 仍没有稳定通过质量门禁。
- 当前失败项主要是 `codex_final`、`balanced_sections`、`segment_not_asr_dump`：分别对应最终改写标记/章节覆盖/ASR 摘抄感。
- 对长视频，必须把 LLM rewrite 改成章节级小包；整包 12k 字仍会 timeout 或 400。

## 三个视频逐项结论

### 1. 明亚保险人小红书保险获客与客户经营实战分享

- 视频：`%MEDIA_ROOT%\从小红书引流300+到成交：一套可复制的获客闭环.mp4`
- 得到大脑 Logseq 文稿：`%LOGSEQ_GRAPH%\pages\GET笔记录音卡 - 2026-07-08 - 明亚保险人小红书保险获客与客户经营实战分享.md`
- 得到大脑输入版 bundle：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\从小红书引流300-到成交-一套可复制的获客闭环\webui-bundle`
- 本地 ASR 版 bundle：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\从小红书引流300-到成交-一套可复制的获客闭环\local-asr-vkp\webui-bundle`
- 逐字稿判断：本地 ASR 完整可用，但更像原始底稿；得到大脑更适合直接读。
- 智能总结判断：得到大脑输入版 quality=failed；本地 ASR 版 quality=failed。失败项需靠章节级 LLM 改写和 ASR 后处理解决。

### 2. 保险经纪人线下活动获客分享——基于趣研学俱乐部的亲子拓客实践

- 视频：`%MEDIA_ROOT%\20250306没客户？通过活动来获客-王彩娥.mp4`
- 得到大脑 Logseq 文稿：`%LOGSEQ_GRAPH%\pages\GET笔记录音卡 - 2026-07-08 - 保险经纪人线下活动获客分享——基于趣研学俱乐部的亲子拓客实践.md`
- 得到大脑输入版 bundle：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\20250306没客户-通过活动来获客-王彩娥\webui-bundle`
- 本地 ASR 版 bundle：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\20250306没客户-通过活动来获客-王彩娥\local-asr-vkp\webui-bundle`
- 逐字稿判断：本地 ASR 完整可用，但更像原始底稿；得到大脑更适合直接读。
- 智能总结判断：得到大脑输入版 quality=failed；本地 ASR 版 quality=failed。失败项需靠章节级 LLM 改写和 ASR 后处理解决。

### 3. 明亚领航计划：陌生客户成交转化高频问题及应对技巧

- 视频：`%MEDIA_ROOT%\1.首次沟通环节的高频问题.mp4`
- 得到大脑 Logseq 文稿：`%LOGSEQ_GRAPH%\pages\GET笔记录音卡 - 2026-07-07 - 明亚领航计划：陌生客户成交转化高频问题及应对技巧.md`
- 得到大脑输入版 bundle：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\1-首次沟通环节的高频问题\webui-bundle`
- 本地 ASR 版 bundle：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\1-首次沟通环节的高频问题\local-asr-vkp\webui-bundle`
- 逐字稿判断：本地 ASR 完整可用，但更像原始底稿；得到大脑更适合直接读。
- 智能总结判断：得到大脑输入版 quality=failed；本地 ASR 版 quality=failed。失败项需靠章节级 LLM 改写和 ASR 后处理解决。

## 对 VKP 的下一步修正建议

1. 把 `run-smart-summary-llm-rewrite` 改成章节级小包：每章 2k-4k 字独立改写，最后再汇总，避免长输入 read timeout。
2. 修 PowerShell wrapper：argparse 错误不应返回 rc=0；否则自动化会误判执行成功。
3. 本地 ASR 后处理默认启用：标点恢复、断句重分段、术语/人名/产品名语义纠错，再进入 smart-summary。
4. 对得到大脑已有文稿的场景，VKP 只把它作为质量对比和人工参考；自动纠错证据仍来自自带字幕/本地抓取字幕、网页上下文、青龙打标器、OCR/多模态证据和在线 LLM 语义仲裁，本地 ASR 仍是主 transcript 起点。
5. 质量对比保留两个独立分数：`transcript_readability` 和 `summary_reusability`，避免只看是否生成文件。

## 当前验收状态

- ASR 重跑：完成。
- local-ASR bundle 重建：完成。
- 语义纠错 pack/closure/impact：完成，但无高置信自动改词，候选保留为可选复核。
- 方舟 LLM 智能总结 rewrite：尝试完成，但 provider 响应不稳定，未产生稳定最终总结。
- 正式结论：逐字稿质量可比较；智能总结质量目前仍不如得到大脑稳定，需要改成章节级 LLM rewrite 后再验收。
