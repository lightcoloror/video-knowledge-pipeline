# Mistral Voxtral 第二 ASR 证据源验收

2026-07-20 22:39:23 +08:00 | Codex / GPT-5

## 范围与授权

- 任务：独立 ASR 第二证据源，不参与提示、热词、路由或事前纠正。
- Provider / 模型：Mistral `voxtral-mini-2602`。
- 目的地：`api.mistral.ai`。
- 精确音频：6,661,057 字节；SHA-256 `4e813d910c798528f3d40124d61ba76b69520ab9ecd2c562effdaaa15eae8484`。
- 调用约束：最多 1 次、零重试、无 fallback、费用防失控上限 0.20 美元。

## 实际结果

- 外部调用：完成 1、失败传输 0、重试 0、fallback 0。
- Connector execution：`model_connector_9272871cd089`。
- 调用正文：完整中文文本，3,871 字符；音频时长 832.4818125 秒。
- Provider 分段：0。网络与输出契约成功，但生产质量门因 `verbose_segments_missing` 拒绝。
- 首次本地 closure：`failed / no_quality_accepted_secondary_segments`。随后新增了仅本地、候选态的全文恢复：在保持质量门失败的前提下，把完整全文按 primary segment 边界做单调文本投影。
- 候选恢复结果：整体相似度 `0.964066`，生成 54 个 `timing_inferred=true` 的候选段；时间戳来源明确标记为 `primary_segment_boundaries`，绝不冒充 Provider 时间戳。
- 隔离共识：54 对 54 段，冲突 1；匿名裁决包包含 8 个差异、5 个差异簇；应用补丁 0，自动提升 0。
- 最终 closure：`degraded / untimed_secondary_text_preserved_as_inferred_candidates`。成功正文被保留，但缺少 Provider 时间戳仍是明确质量缺口。
- canonical transcript 前后 SHA-256 均为 `9ba4f3321f32a5d824b5bb61dd8c67bbe8b5e560f81b339af15bd744ace19ebb`。

执行证据：

- `.local/online-full-video-20260719/3-scheme-principles/asr-second-source-20260720/prepared/01-scheme-principles-full-secondary-asr-mistral-voxtral-mini-2602/model-connector-runs/model_connector_9272871cd089/connector-execution.json`
- `.local/online-full-video-20260719/3-scheme-principles/pipeline/webui-bundle/asr-secondary-evidence/scheme-principles-full-secondary-asr--mistral-voxtral-mini-2602/secondary-asr-evidence-closure.json`
- `.local/online-full-video-20260719/3-scheme-principles/pipeline/webui-bundle/asr-secondary-evidence/scheme-principles-full-secondary-asr--mistral-voxtral-mini-2602/secondary-inferred-timing-transcript.json`
- `.local/online-full-video-20260719/3-scheme-principles/pipeline/webui-bundle/asr-secondary-evidence/scheme-principles-full-secondary-asr--mistral-voxtral-mini-2602/asr-consensus-adjudication-pack.json`

## 仅评估对比

得到大脑参考稿只在模型返回后用于本地评估，未进入任何 provider 请求。

- Mistral 原始全文归一化参考编辑距离：`6.195571%`，编辑距离 249 / 参考 4,019 字符。
- 当前 canonical 的既有结果：`7.887534%`，编辑距离 317。
- Mistral 全文比当前 canonical 少 68 次归一化编辑，约改善 21.45%，但仍未达到严格 `<5%` 目标。
- 本地推断时间候选使评估窗口可用：19 个严格窗口全部未达到 `<5%`；最高误差窗口为 `618–657s` 的 `55.675676%`，最接近门槛的是 `740–775s` 的 `5.454545%`。
- 全文距离不因时间投影而改变；仍需至少减少 49 次归一化编辑才能达到严格 `<5%` 目标。
- 推断时间只用于候选比较，不能安全自动合并进 Timeline。

评估报告：`.local/online-full-video-20260719/3-scheme-principles/pipeline/webui-bundle/exports/transcript-stability-evaluation.getbrain.mistral-inferred-timing.json`。

## 根因与修复

Mistral 的转录端点只有在请求时间戳粒度后才保证返回可对齐分段。VKP 过去只发送 `response_format=verbose_json`，没有发送时间戳粒度。运行时已改为额外发送 `timestamp_granularities[]=segment`，并由 loopback fake Proxy 测试锁定 multipart 字段。

同时修复了 Broker 启动入口：显式 `ModelSettingsPath` 现在同时驱动目的地 allowlist 与运行时路由解析，避免 consent v2 被默认设置中的另一条 route 错误校验。

官方依据：

- [Mistral Audio Transcriptions API](https://docs.mistral.ai/api/endpoint/audio/transcriptions)
- [Mistral Offline Transcription](https://docs.mistral.ai/studio-api/audio/speech_to_text/offline_transcription)

当前 LiteLLM 通用 OpenAI-compatible 转录适配器不会可靠转发 Mistral 专有 `context_bias`。因此本次只修复标准分段时间戳；热词偏置需后续使用明确的 Mistral 薄适配器或经验证的 LiteLLM 原生支持，不能静默假定 `prompt` 等价于 `context_bias`。

## Canonical 与导出一致性

- 这次第二证据源没有直接替换 canonical；已有人工确认的 `MIAAPP -> 明亚APP` 与 `cell -> Excel` 仍是唯一正式语义改写。
- 语义纠正验收现已锁定 canonical、`full-transcript.md`、`knowledge-note.md` 与 Smart Summary 输入包的 SHA-256。一处哈希不一致时状态必须是 `needs_canonical_export_refresh`，不能误报 `accepted`。
- 当前生产 Bundle 已本地刷新验收证明：accepted decision 2、review required 0、canonical integrity passed；该刷新没有调用模型或上传文件。

## 剩余缺口

修复后的真实时间戳返回仍需新的精确 consent 才能验证。本次唯一授权调用已经消费，未进行第二次外部调用。默认 Broker、Secure MCP Tunnel 和 LiteLLM Proxy 均已恢复原生产配置。

本机已有 `%LOCAL_MODEL_ROOT%\models\Qwen3-ForcedAligner-0.6B`，但当前 VKP Python 环境缺少可用的 `qwen_asr` 运行时及其依赖组合。本轮没有安装依赖或下载模型。恢复该本地运行时后，可把“借 primary 边界投影”升级为独立声学强制对齐证据。

## 验证

- 新增候选恢复 focused：`49 passed`。
- 完整离线回归：`965 passed, 1 warning`；警告为既有 `jieba/pkg_resources` 弃用提示。
- Python Ruff、PowerShell parser、`compileall` 与 `git diff --check` 通过。
## 2026-07-21 08:28:41 +08:00 后续生产闭环更新 | Codex / GPT-5

本节全部为本地处理；没有再次调用 Mistral 或任何在线模型。

- semantic closure 改为从稳定的 richer upstream transcript 构建 canonical，避免回退到早期、内容较少的 normalized transcript。
- 累计人工/证据确认决定已写入 decision ledger，共 12 项；`MIAAPP -> 明亚APP` 与 `cell -> Excel` 均保留。
- 当前 canonical SHA-256：`b5e13ce402cdc192627eb4a44dbf7eb9105a79f35557640dbfbbf5dafda7b11a`。
- semantic 状态：`impact_passed`；acceptance：`accepted`；residual：0。
- closure 现为幂等写入：内容等价时 `canonical_write_status=unchanged`，不改写 canonical JSON/SRT/Markdown。
- knowledge export 与 semantic repair 不再重复启动 transcript evidence pipeline、重建已验证 pack；旧版缺少 identity 字段时继续走明确的 legacy fallback，真实哈希或原文冲突仍会阻断。
- 当前得到大脑 evaluation-only 指标：编辑距离 305 / 4,019，归一化参考编辑距离 `7.588952%`；提示词泄漏 0，未检测到长段缺失。该指标不是人工金标 CER，且仍未达到严格 `<5%` 目标。
- 修复后完整离线回归：`981 passed, 1 warning`；`compileall -q src` 与 `git diff --check` 通过。警告仍为既有 `jieba/pkg_resources` 弃用提示。

剩余质量缺口：要达到 `<5%`，至少还需减少 105 次归一化编辑，并优先补回 233 字的长度差。Mistral 和 Qwen 证据只能用于候选与交叉支持；得到大脑参考稿继续严格限定为 evaluation-only，不能反向进入提示、热词、路由或纠正决定。
