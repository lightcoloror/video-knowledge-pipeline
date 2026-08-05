# local-production-v1 验收与全在线生产切换

2026-07-19 19:12:53 | Codex / GPT-5

更新：2026-07-22 11:05:45 +08:00 | Codex / GPT-5.6
Google 生产质量路线升级为 `gemini-3.6-flash`；兼容性与回滚说明见 `docs/gemini-3-6-flash-refresh-2026-07-22.md`。

## 决策

`local-production-v1` 只保留为离线、隐私敏感、断网和 A/B/C 对照路线。后续批量视频默认使用 `online-production-existing-apis-v1`。两类路由互不自动 fallback；保存配置不授权上传，远程执行仍需精确 artifact 清单、SHA-256、route revision、consent v2、调用次数和费用上限。

## 第一个本地整链验收

视频：`1.首次沟通环节的高频问题.mp4`

- 状态：`completed`
- 完成：`1`
- 失败：`0`
- 转录：79 段，结束时间 `00:17:39.059`
- ebook OCR：32/32；Timeline UTF-8 替换字符 0
- 单帧多模态：9 项
- temporal 多模态：1 项
- Smart Summary：质量门 `passed`；压缩率 `0.299869`；重复率 `0`；未支持数字 `[]`
- 知识导出：`completed`

产物：

- `.local/local-production-e2e-20260719/1-first-communication/webui-bundle/exports/full-transcript.md`
- `.local/local-production-e2e-20260719/1-first-communication/webui-bundle/exports/smart-summary.md`
- `.local/local-production-e2e-20260719/1-first-communication/webui-bundle/exports/knowledge-note.md`
- `.local/local-production-e2e-20260719/1-first-communication/local-vs-getbrain-comparison.json`
- `.local/local-production-e2e-20260719/1-first-communication/local-vs-getbrain-comparison.md`

GetBrain 既有产物仅作参考，不是人工标注真值。

## OCR 稳定性修复

`ebook_markdown_pipeline` 生成的 `book.md` 是正确 UTF-8，但 MCP `read_artifact` 返回文本曾受 Windows 宿主代码页影响，导致 Timeline 中文乱码。

修复策略：

1. 验证 artifact 位于明确的 ebook `output_dir` 内。
2. 文本类 artifact 直接从本地文件按 `utf-8-sig` 读取。
3. 长任务使用 `run-visual-structure-ebook-batches` 短子进程、可恢复批次。
4. 既有成功 OCR 用 `repair-ebook-artifact-text` 从 artifact 修复写回，不重跑 OCR。
5. 同步更新 `timeline.json` 与 manifest 指向的 source package，并写出修复报告。

命令：

```powershell
.\scripts\video-knowledge.ps1 run-visual-structure-ebook-batches <bundle> --execute --batch-size 3
.\scripts\video-knowledge.ps1 repair-ebook-artifact-text <bundle>
```

## 全在线生产预设

已重新应用 `online-production-existing-apis-v1`，复用现有 Windows DPAPI `secret_ref`，不要求重新填写 API Key。

| 任务 | 在线模型 / Provider |
|---|---|
| ASR | Groq `whisper-large-v3-turbo` |
| OCR | Mistral `mistral-ocr-4-0` |
| PPT / 文档视觉 | SiliconFlow `PaddlePaddle/PaddleOCR-VL-1.5` |
| 单帧语义 | SiliconFlow `zai-org/GLM-4.5V` |
| temporal / video segment | Google `gemini-3.6-flash` |
| 文本 / 摘要 / 转录纠错 | Google `gemini-3.6-flash` |

六个池均为单 deployment；远程目的地为 `api.groq.com`、`api.mistral.ai`、`api.siliconflow.cn`、`generativelanguage.googleapis.com`；无跨目的地 fallback。Coding Plan profile 不进入该生产预设。

LiteLLM Proxy：`127.0.0.1:18776`，doctor/status 均为 `ready`，telemetry 关闭。本次切换只改本地控制面，远程请求和上传均为 0。

## 下一次视频的执行门

1. 本地提取最小必要 artifact：音频、疑难帧/temporal 帧、OCR 图片以及文本证据。
2. 生成逐文件大小和 SHA-256 清单；不默认上传完整视频。
3. 固定任务、provider、deployment、目的地、route revision、调用次数和费用上限。
4. 操作者确认后创建 consent v2。
5. 由 Trusted Broker 执行；零静默 fallback，失败保留可重试状态和审计回执。
6. Provider 正文、逐字稿、最终总结和用户可见错误说明使用中文；机器进度/中间结构化字段可使用英文。
