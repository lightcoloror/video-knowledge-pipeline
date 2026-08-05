# VKP 在线链路网络流量与 Token 优化

- 记录时间：2026-07-22 17:27:19（Asia/Shanghai）
- 执行工具/模型：Codex / GPT-5.6
- 状态：离线实现与同视频请求侧测量完成；32 kbps ASR 的在线质量 A/B 尚待一次新的精确授权

## 结论

本轮不新建第二套媒体或模型调用栈，直接复用现有三个成熟入口：

1. FFmpeg：复用 `media_tools.resolve_media_tool()` 和已有子进程环境，生成 speech-only MP3 候选。参考 [FFmpeg codec documentation](https://www.ffmpeg.org/ffmpeg-codecs.html)。
2. LiteLLM Proxy：继续作为供应商协议、路由、重试和用量真源；VKP 只在统一客户端记录实际发送给 loopback Proxy 的请求/响应 payload 字节。参考 [LiteLLM](https://github.com/BerriAI/litellm)。
3. VKP 已有 semantic correction prioritiser：复用 `_prioritise_candidates_for_llm()` 与 `_compact_candidate_for_llm()`，不再把完整纠错证据包直接发给模型。

## 同一视频实测

样本：`1.客户特点、成交基本原则、获取信任的相关动作`

### 1. ASR 上传流量

| 项目 | 原路线 | 优化候选 | 变化 |
|---|---:|---:|---:|
| 编码 | MP3 64 kbps | MP3 32 kbps | speech-only candidate |
| 采样率/声道 | 16 kHz / mono | 16 kHz / mono | 不变 |
| 时长 | 1066.538938 秒 | 1066.538938 秒 | 不变 |
| 文件字节 | 8,533,633 | 4,266,801 | -4,266,832（-50.00%） |

优化文件及 provenance 位于：

- `.local/online-batch-20260722/1-customer-trust/audio-16k-mono-32k.mp3`
- `.local/online-batch-20260722/1-customer-trust/audio-16k-mono-32k.mp3.provenance.json`

32 kbps 目前仍是 candidate，不替换 64 kbps 生产基线。必须用同一 Groq 模型做一次真实 A/B，比较段数、时间戳、关键术语、数字、内容缺口和延迟后，才能决定是否升级为默认值。

### 2. 转录语义纠错 Token

上一次实际调用直接上传了 302,495 字节完整 pack，Gemini 返回的实际 usage 为：

- prompt tokens：93,521
- completion tokens：9,702
- total tokens：103,223

利用既有 validation 中保存的 66 个候选重建同一批候选后，原有 prioritiser 只选出 25 个具备外部冲突证据的候选，41 个低证据候选延后。历史同视频 gateway pack 为 56,285 字节，相比原上传包 302,495 字节减少 81.39%。

使用本地 `cl100k_base` 只做相对估算（不是 Gemini 计费口径）：

| 项目 | 重建完整候选 | 紧凑候选 | 变化 |
|---|---:|---:|---:|
| 本地估算 tokens | 69,129 | 17,304 | -74.97% |

按同一次 15-call 批处理的实际 120,345 输入 tokens 计算，仅替换这一项后，预计总输入约降到 44,128，约减少 63.34%。准确计费 Token 只能在下一次真实调用的 provider usage 中确认。

### 3. Secure MCP 回传流量

完整执行报告继续写在本地，MCP 默认只返回状态、route identity、usage、cost、质量门和本地报告路径，不回传模型正文。

| 历史执行 | 完整本地报告 | 新 compact receipt | 预计隧道回传减少 |
|---|---:|---:|---:|
| Groq ASR | 1,145,972 B | 1,557 B | 99.86% |
| Gemini 语义纠错 | 83,809 B | 1,569 B | 98.13% |

`return_mode=full` 仍保留为显式兼容选项。默认 `receipt` 不删除本地报告。

## 新增接口

```powershell
.\scripts\video-knowledge.ps1 prepare-cloud-asr-audio <media> `
  --output-path <candidate.mp3> `
  --bitrate-kbps 32 `
  --sample-rate-hz 16000 `
  --channels 1 `
  --execute
```

该命令只运行本地 FFmpeg，不联网。未加 `--execute` 时只返回计划。

`transcript-semantic-correction-llm-draft` 现在额外生成：

- `transcript-semantic-correction-gateway-pack.json`
- `gateway_pack_bytes`
- `source_pack_bytes`
- `input_byte_reduction_ratio`

模型执行 MCP 新增：

- `return_mode=receipt`（默认）
- `return_mode=full`（显式兼容）

统一 runtime result 新增 `network_accounting`。它精确表示 VKP 到本机 LiteLLM Proxy 的 payload 字节；LiteLLM 可能重新序列化，所以不能冒充供应商 TLS wire bytes。

## 验证

离线 focused 回归：首轮 `113 passed`；按最终文件集合复核 `95 passed`。`python -m compileall -q src` 通过。

完整回归：`1067 passed, 2 failed, 1 warning`。两个失败分别来自既有 Gemini catalog 测试夹具仍返回 `gemini-3.5-flash`、以及视觉分流测试使用不存在的帧路径；均不在本轮网络/Token 优化调用链中，未在本轮覆盖并发工作树改动。

测试覆盖：

- 非流式 gateway 响应精确字节计数；
- 多调用执行结果的 network accounting 汇总；
- MCP receipt 不包含正文且显著小于完整报告；
- 语义候选证据截断、候选子集和 pack schema；
- Cloud ASR audio preview 本地且不产生网络调用。

## 尚未闭环

1. 32 kbps 音频尚未发给 Groq；因此质量结论仍是“请求侧优化已验证，识别质量待真实 A/B”。
2. provider TLS 层的 header、HTTP/2、重传字节不在 VKP 精确观测范围；当前精确计量边界是 VKP → loopback LiteLLM payload。
3. 输出 Token 的实际下降要等紧凑 pack 的真实调用 usage；当前只有输入结构与本地 tokenizer 的相对估算。
4. OCR 图片压缩尚未默认启用。OCR 对小字敏感，应先做分辨率/格式质量门后再决定是否压缩。

## Reproducible offline A/B quality gates

The comparator reuses `transcript_stability_evaluation` instead of implementing a second edit-distance stack. It never calls a provider and never promotes a transcript or correction result.

```powershell
$env:PYTHONPATH='src'
python -m video_knowledge_pipeline.input_optimization_benchmark asr `
  <baseline-audio> <optimized-audio> `
  <baseline-transcript.json> <optimized-transcript.json> `
  <baseline-execution.json> <optimized-execution.json> <asr-ab.json> `
  --critical-term Mingya

python -m video_knowledge_pipeline.input_optimization_benchmark semantic `
  <compact-pack.json> <baseline-execution.json> <optimized-execution.json> `
  <semantic-ab.json>

python -m video_knowledge_pipeline.input_optimization_benchmark final `
  <asr-ab.json> <semantic-ab.json> <network-token-ab.json>
```

Production defaults remain unchanged unless the same-route/model A/B passes all content, completion, candidate-integrity, byte-reduction, and provider-reported prompt-token gates.

## 2026-07-22 19:55:00 同视频真实 A/B 终验

- 执行工具/模型：Codex / GPT-5.6
- 对比性质：evaluation-only；没有把 32 kbps 转录或紧凑语义决策写回生产产物
- 在线调用：复用用户已授权且已经完成的两次单调用；本次汇总没有新增联网请求、重试或 fallback
- 最终汇总：`.local/online-batch-20260722/1-customer-trust/webui-bundle/benchmarks/network-token-optimization/network-token-ab-final.json`

### ASR：64 kbps 对 32 kbps

两次调用均为 Groq `whisper-large-v3-turbo`，route revision 完全相同。

| 指标 | 64 kbps 基线 | 32 kbps 候选 | 结果 |
|---|---:|---:|---|
| 上传字节 | 8,533,633 | 4,266,801 | -50.00% |
| provider latency | 8,079 ms | 4,631 ms | -42.68% |
| 规范化字符 | 5,115 | 4,993 | -2.39% |
| 严格全文差异 | - | 8.211% | 未通过 `<5%` 门槛 |
| 去语气词内容差异 | - | 7.953% | 未通过 `<5%` 门槛 |
| review / failed | 1 / 0 | 1 / 0 | 计数没有恶化，但缺口位置改变 |

关键诊断：

- 32 kbps 候选补回了 64 kbps 基线在 111.82–136.62 秒的空白内容。
- 32 kbps 候选又在 167.22–197.22 秒形成约 30 秒空白，而 64 kbps 基线在该处有正文。
- 因此这不是“整体等价、仅分段不同”，而是两次长音频识别各自出现了不同缺段；不能仅凭文件更小、延迟更低就升级默认值。
- 决策：`keep_current_default`。生产继续使用 64 kbps；32 kbps 仅保留为实验候选。后续优化重点应是长音频分块、重叠窗口与缺段检测，而不是继续降低码率。

### 转录语义纠错：完整包对紧凑包

两次调用均为 Gemini `gemini-3.6-flash`，route revision 完全相同。紧凑包只保留已有 prioritiser 选中的 25 个高证据候选。

| 指标 | 完整包 | 紧凑包 | 结果 |
|---|---:|---:|---|
| 上传字节 | 302,495 | 56,285 | -81.39% |
| prompt tokens | 93,521 | 18,743 | -79.96% |
| completion tokens | 9,702 | 4,204 | -56.67% |
| total tokens | 103,223 | 22,947 | -77.77% |
| provider latency | 36,983 ms | 15,955 ms | -56.86% |
| 候选返回 | 历史完整包 | 25 / 25 | 无遗漏、无额外候选 |
| Schema / 质量门 | 未通过 | 全部通过 | 紧凑包可进入默认候选 |

紧凑调用保持了全部 `candidate_id`、逐字一致的 `original_text` 和受输入 pack 约束的 `evidence_ids`，且 `contract_ok`、`quality_gate_passed`、`production_qualified` 均为真。决策：`eligible_for_compact_gateway_default`。

### 流量结论

- 本次两个直接被优化输入合计：8,836,128 B → 4,323,086 B，减少 4,513,042 B（51.08%）。
- 按同视频既有完整在线链路中其余输入不变的去重逻辑投影：9,559,928 B → 5,046,886 B，减少 47.21%。
- 上述数字是应用层 artifact / payload 边界，不包括 TLS header、HTTP/2 framing、TCP 重传和供应商内部重编码，因此不冒充网卡级流量。

### 代码与运行时状态

- `input_optimization_benchmark final` 已修复字符串路径误传给 `read_json(Path)` 的问题；失败质量门现在也能稳定生成最终汇总 JSON，并以退出码 2 表示“不建议整体切换”。
- focused tests：`10 passed`；Ruff：`All checks passed`。
- 当前磁盘代码的 MCP 默认回传模式已经是 compact receipt，但本轮真实调用命中了重启前的旧 Broker 进程，仍返回完整执行报告。要让隧道回传节省在运行时生效，需要另行明确批准重启 Trusted Capability Broker；本轮未重启任何服务。

### 最终采用策略

1. 立即采用紧凑语义 gateway pack 作为转录纠错默认输入候选。
2. 保留 64 kbps 作为完整长音频 ASR 默认；32 kbps 不进入生产。
3. 下一阶段对 ASR 实施“分块 + 小重叠 + 缺段检测 + 仅缺口重跑”，再用同一路由/模型做 A/B；不通过稳定门不切换。
4. Broker 重启前，compact receipt 只属于代码就绪状态，不宣称运行时已经生效。
