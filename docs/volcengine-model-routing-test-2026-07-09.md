# 火山 Coding Plan 模型任务路由与实测记录

更新时间：2026-07-09 11:38:00
执行工具：Codex / GPT-5

## 结论

VKP 不应把所有文本任务都交给同一个模型。按本次实测，当前稳定生产路由建议如下：

| VKP 任务 | 默认模型 | 备选模型 | 说明 |
| --- | --- | --- | --- |
| 智能总结最终成稿 | `doubao-seed-2.0-pro` | `minimax-m3` | 豆包 pro 更适合作为通用中文总结默认；minimax-m3 适合长章节备选。 |
| ASR/字幕语义纠错 | `doubao-seed-2.0-pro` | `deepseek-v4-pro` | 普通错词纠正用豆包 pro；多证据冲突或高风险术语用 deepseek-v4-pro 仲裁。 |
| 疑难点初筛 / triage | `doubao-seed-2.0-lite` | `deepseek-v4-flash`, `minimax-m2.7` | 大批量低成本判断是否需要复核。 |
| 多证据冲突仲裁 | `deepseek-v4-pro` | `doubao-seed-2.0-pro`, `deepseek-v4-flash` | ASR、字幕、OCR、多模态证据互相冲突时优先强推理。 |
| 工具名/代码名纠错 | `doubao-seed-2.0-code` | `deepseek-v4-pro`, `glm-latest`, `kimi-k2.6`, `deepseek-v4-flash` | 混合路线优先豆包 code；完全避开豆包时可用 DeepSeek/GLM/Kimi，但 GLM/Kimi 需要 `thinking: {type: disabled}`。 |
| 长章节/长转写结构化 | `minimax-m3` | `doubao-seed-2.0-pro`, `minimax-m2.7` | 长章节更适合用 minimax-m3 做压缩整理；豆包 pro 做最终语言质量。 |

暂不进入默认生产链路：

- `kimi-k2.7-code`：短 prompt 不加 thinking 可以返回；正式证据 prompt 下仍容易 reasoning-only 或输出半截，且 `thinking: {type: disabled}` 会 HTTP 400。

条件进入非豆包工具名纠错链路：

- `glm-latest`：必须传 `thinking: {type: disabled}`。
- `kimi-k2.6`：必须传 `thinking: {type: disabled}`。

## Base URL 边界

必须使用 Coding Plan OpenAI-compatible endpoint：

```text
https://ark.cn-beijing.volces.com/api/coding/v3
```

不要使用：

```text
https://ark.cn-beijing.volces.com/api/v3
```

后者不是 Coding Plan 专用入口，不会消耗 Coding Plan 额度，可能产生额外费用。

## 固化后的非豆包生产路由

VKP 新增只读路由入口，用于让 CLI/MCP/agent 直接读取非豆包工具名纠错路线，不需要从本文档人工复制：

```powershell
.\scripts\video-knowledge.ps1 volcengine-model-routing `
  --route tool_terms_no_doubao `
  --output-dir openclaw-runs\model-tests\routing-current
```

当前 `tool_terms_no_doubao` 路线：

| 阶段 | 模型 | 参数 | 用途 |
| --- | --- | --- | --- |
| 批量初筛 | `deepseek-v4-flash` | 默认 thinking | 低成本草判，快速找值得复核的工具名/代码术语。 |
| 最终仲裁 | `deepseek-v4-pro` | 默认 thinking, `max_tokens=2400` | 高风险错词、最终写回逐字稿前的主仲裁。 |
| 长解释第二意见 | `kimi-k2.6` | `thinking: {type: disabled}` | 需要更好中文解释、更完整表格时作为第二意见。 |
| 独立判断第二意见 | `glm-latest` | `thinking: {type: disabled}` | 用不同模型族做独立复核，辅助发现遗漏。 |

`doubao-seed-2.0-code` 保留在混合路线，但不再作为绝对优先；`kimi-k2.7-code` 暂不进入默认路线。
## 本次实测命令

Preview：

```powershell
.\scripts\video-knowledge.ps1 volcengine-model-task-matrix `
  --output-dir openclaw-runs\model-tests
```

真实文本小样本测试：

```powershell
.\scripts\video-knowledge.ps1 volcengine-model-task-matrix `
  --execute `
  --output-dir openclaw-runs\model-tests\executed-20260709 `
  --timeout-seconds 120
```

注意：执行版只发送小段文本样本，不发送视频、音频、截图或私有帧。

## 实测结果

| 任务 | 模型 | 角色 | 结果 | 输出字符 | 判断 |
| --- | --- | --- | --- | ---: | --- |
| 智能总结最终成稿 | `doubao-seed-2.0-pro` | primary | passed | 208 | 可作为默认 smart-summary 文本模型。 |
| 批量疑难点初筛 | `doubao-seed-2.0-lite` | primary | passed | 179 | 适合 triage，输出 JSON 正常。 |
| 多证据冲突仲裁 | `deepseek-v4-pro` | primary | passed | 170 | 适合证据冲突仲裁。 |
| 快速冲突仲裁备选 | `deepseek-v4-flash` | fallback_fast | passed | 150 | 适合低成本快速复核。 |
| 工具名/代码名纠错 | `doubao-seed-2.0-code` | primary | passed | 1185 | 对 Playwright、Chrome DevTools 等工具名纠错表现好。 |
| 工具名/代码名纠错（非豆包） | `deepseek-v4-pro` | fallback_no_doubao | passed | 530 | 需要较高 `max_tokens`；800 token 时会被 reasoning 占满，2400 token 后可输出 Playwright/Chrome/UI-TARS 等纠错表。 |
| 旧代码模型备选 | `doubao-seed-code` | fallback_code | passed | 388 | 可做代码名纠错备选，但新任务优先 2.0-code。 |
| 长章节总结备选 | `minimax-m3` | fallback_long_context | passed | 1319 | 适合长章节结构化和压缩整理。 |
| 轻量长文本备选 | `minimax-m2.7` | fallback_light_long | passed | 751 | 可做低成本长文本初稿。 |
| 通用语义仲裁备选 | `glm-latest` | needs_adapter | failed | 0 | 返回 reasoning-only，未得到最终 content。 |
| 长转写结构化备选 | `kimi-k2.6` | needs_adapter | passed | 251 | 本次通过，但此前出现 reasoning-only，暂不列默认。 |
| 代码/工具链视频备选 | `kimi-k2.7-code` | needs_adapter | failed | 0 | 返回 reasoning-only，未得到最终 content。 |

## 产物路径

- JSON：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\model-tests\executed-20260709\volcengine-model-task-matrix.json`
- Markdown：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\model-tests\executed-20260709\volcengine-model-task-matrix.md`

## 非豆包工具名纠错补测

补测命令：

```powershell
.\scripts\video-knowledge.ps1 volcengine-model-task-matrix `
  --execute `
  --tasks tool_code_terms_deepseek `
  --output-dir openclaw-runs\model-tests\tool-code-terms-deepseek-20260709-rerun `
  --timeout-seconds 180
```

结果：`deepseek-v4-pro` 在 `max_tokens=2400` 时通过，输出 530 字符，命中 `Playwright`、`Chrome`、`UI-TARS`。第一次 `max_tokens=800` 失败，原因是 `reasoning_content` 占满 token，最终 `content` 为空。因此非豆包工具名纠错可以落地，但需要更高 token 预算，适合作为高风险/疑难工具名复核，不适合作为大批量低成本初筛。

第二轮同题候选测试把 `deepseek-v4-pro`、`deepseek-v4-flash`、`glm-latest`、`kimi-k2.6`、`kimi-k2.7-code` 放到同一个工具名纠错样本里。随后根据方舟参数说明，为 GLM/Kimi 2.6 增加 `thinking: {type: disabled}` 后重测：

| 模型 | thinking | 结果 | 输出字符 | 判断 |
| --- | --- | --- | ---: | --- |
| `deepseek-v4-pro` | default | passed | 697 | 稳，适合高风险/最终仲裁。 |
| `deepseek-v4-flash` | default | passed | 448 | 可用，适合低成本初判或批量草判。 |
| `glm-latest` | disabled | passed | 972 | 关闭 thinking 后可稳定写入 `message.content`，可作为非豆包高质量候选。 |
| `kimi-k2.6` | disabled | passed | 743 | 关闭 thinking 后可稳定写入 `message.content`，适合结构化纠错候选。 |
| `kimi-k2.7-code` | default / disabled | failed | 0 / 半截 | 短 prompt 可回；正式证据 prompt 仍不稳定，`thinking: disabled` 会 HTTP 400，暂不进生产路由。 |

这说明 GLM/Kimi 2.6 的问题不是模型不能做工具术语，而是默认深度思考输出落在 `reasoning_content`，需要显式关闭 thinking 才能稳定拿到 `message.content`。Kimi Code 目前更麻烦：禁用 thinking 被接口拒绝，不禁用时正式 prompt 容易 reasoning-only 或输出半截，暂不作为默认。

产物路径：

- `%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\model-tests\tool-code-terms-deepseek-20260709-rerun\volcengine-model-task-matrix.json`
- `%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\model-tests\tool-code-terms-deepseek-20260709-rerun\volcengine-model-task-matrix.md`
- `%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\model-tests\tool-code-terms-no-doubao-candidates-20260709\volcengine-model-task-matrix.json`
- `%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\model-tests\tool-code-terms-no-doubao-candidates-20260709\volcengine-model-task-matrix.md`
## 对 VKP 的落地策略

1. `smart-summary`、章节级 LLM 改写：默认使用 `doubao-seed-2.0-pro`。
2. `transcript semantic correction`：普通候选用 `doubao-seed-2.0-pro`；冲突证据较多时切换 `deepseek-v4-pro`。
3. `vision review triage` / 疑难点初筛：默认 `doubao-seed-2.0-lite`，减少成本。
4. 浏览器自动化、代码、CLI、API、工具名视频：默认 `doubao-seed-2.0-code`；如果要求完全避开豆包，使用 `deepseek-v4-pro`，并要求输入同时包含 ASR、OCR/画面文字、网页/字幕上下文和候选词典。
5. 长视频章节压缩：优先 `minimax-m3` 作为章节压缩备选，再由 `doubao-seed-2.0-pro` 做最终润色。
6. `glm-latest`、`kimi-k2.6` 在火山 Coding Plan 下需要传 `thinking: {type: disabled}`；`kimi-k2.7-code` 暂不进默认生产链路。