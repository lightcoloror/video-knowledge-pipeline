# 粤语细节 ASR 与跨片段三说话人对齐（2026-08-11）

更新时间：2026-08-11 05:03:30 +08:00
执行者：Codex (GPT-5.6 Sol)

## 结论

- `cantonese-detail-v1` 的离线 A/B 合同、强制粤语、领域 context 和缺权重硬门已经落地。
- 两段采访已使用本地 GPU CAM++ 重建逐语句声纹候选：短片 9 个样本，长片 83 个样本；未重跑 ASR，原始 ASR SHA-256 保持不变。
- 两段录音联合固定为 3 个匿名说话人后仍有 2 个局部簇纯度不足，21 句只能依赖低纯度局部多数票。第三类主要是极短片段，尚不足以可靠绑定“采访者／客户／家属”。
- 因此所有新声纹结果保持 `candidate_only`，没有覆盖规范化逐字稿、Timeline、普通话翻译或智能总结。
- Qwen3-ASR-1.7B 已从官方 ModelScope 中国大陆入口下载到 `.local/models/Qwen3-ASR-1.7B`；两个权重分片共约 4.70 GB，逐文件 SHA-256 与上游一致。
- 12 个粤语疑难短片已在本地 GPU 上完成 Qwen 候选：12/12 成功、零 fallback、网络关闭；首片约 40 秒，其余 11 片合计约 283 秒。
- SenseVoice 与 Qwen 的 12 段平均规范化字符差异率为 `0.194459`，8 段为高分歧、4 段含数字表述冲突。Qwen 在“尿结石、膀胱结石、质子治疗、开刀”等语义连贯性上明显优于现稿，但没有人工逐字真值，尚不能据此宣布 CER 胜出或覆盖正式逐字稿。

## 变更记录

### CANTONESE-DETAIL-001：Qwen 离线完整性硬门

- 意图：避免把不完整缓存误报为“模型已安装”，或在识别时隐式联网。
- 决策：`qwen3_asr_python_runner` 在导入和加载模型前验证索引中列明的全部权重；缺失时返回 `qwen3_asr_model_not_ready`。
- 理由：本机 Hugging Face 目录只有配置、索引和两个 `.incomplete` 文件，目录存在不等于可离线推理。
- 证据：官方模型树为 4.7 GB，包含 4.22 GB 与 478 MB 两个 safetensors；许可证 Apache-2.0。官方文档明确推荐中国大陆用户使用 `modelscope download --model Qwen/Qwen3-ASR-1.7B`。
- 生效范围：Qwen3-ASR 0.6B、1.7B 与 ForcedAligner 的本地 readiness；不改变 SenseVoice。
- 回滚：恢复原目录存在检查会重新引入隐式下载风险，不建议回滚。

### CANTONESE-DETAIL-002：粤语与领域 context

- 意图：提高粤语、保险、医学、数字和否定词细节识别率。
- 决策：将 `yue` 映射为官方 `Cantonese`，Qwen 使用官方 `context` 参数；A/B manifest 固定语言和去重后的领域词表。
- 理由：官方 Qwen3-ASR 支持粤语及广东／香港口音，并公开支持 context；不能继续把 hotword 作为未审核的私有参数传入。
- 证据：12 个高难本地 WAV 已登记在 `.local/cantonese-detail-v1-20260811/quality-benchmark-manifest.json`，候选只读、不覆盖现稿。
- 生效范围：`quality-benchmark` 的 Qwen 候选；SenseVoice 仍是现有基线。
- 回滚：删除语言/context 字段即可恢复旧候选行为，不影响原稿。

### CANTONESE-DETAIL-003：复用现有 CUDA 环境完成真实短片 A/B

- 意图：验证 Qwen3-ASR-1.7B 对纯粤语采访细节的实际可运行性，而不是只停留在 adapter ready。
- 决策：复用 `.conda-lecture-asr` 中既有 CUDA Torch 与官方 `qwen-asr 0.0.6`，直接加载完整本地模型；每个短片独立子进程、GPU 单并发、零重试、无 0.6B fallback。
- 理由：新建第二套 Torch 环境会重复占用数 GB，且增加 CUDA 兼容风险；当前环境已经满足官方依赖。
- 证据：`quality-benchmark-variant-run.json` 记录 12/12 completed、device=cuda、network_access=disabled、模型路径为本地完整 snapshot。
- 生效范围：本次 12 片候选 A/B 与今后显式选择 `qwen3-asr-1.7b` 的本地计划；不会切换默认 ASR。
- 回滚：删除 `.local/cantonese-detail-v1-20260811/variant-runs` 即可，不影响 Bundle。

### CANTONESE-DETAIL-004：已有 SenseVoice 草稿进入分歧检测

- 意图：避免已有两路文本却错误报告 `compared_count=0`。
- 决策：分歧基线优先使用独立 SenseVoice variant；未重复运行 SenseVoice 时，使用 manifest 中绑定来源路径的 `asr_draft_text`。
- 理由：本轮刻意不重复调用相同 SenseVoice 音频，现稿本身就是已完成的同窗口基线。
- 证据：修复后 `compared_count=12`、平均 edit ratio `0.194459`、高分歧 8、数字冲突 4；Review HTML 同屏提供音频、SenseVoice 与 Qwen 文本。
- 生效范围：评测优先级和人工复核 UI；不会将任何一方视为人工真值。
- 回滚：移除 source-bound draft fallback 会恢复错误的零比较统计，不建议回滚。

### SPEAKER-SAMPLE-001：逐语句 CAM++ 声纹

- 意图：降低“把一个局部簇的多段语音拼起来”造成的跨人污染。
- 决策：继续直接调用固定 FunASR 1.3.30 CAM++，但每个已选 source segment 单独提取 embedding，再按局部簇计算中心；私有 sidecar 同时保存逐语句 embedding。
- 理由：原拼接中心无法暴露同一局部簇是否混入多个人；逐语句样本可以计算纯度并精确回写被采样的句子。
- 证据：短片从 5 个局部簇抽取 9 个样本，长片从 22 个局部簇抽取 83 个样本，均在 RTX 5070 Ti Laptop GPU 上完成。
- 生效范围：新建的本地 biometric `.private.json`、候选匿名 speaker sidecar；不改 ASR 正文。
- 回滚：删除对应输出目录即可；原始 Bundle 不受影响。

### SPEAKER-SAMPLE-002：同一采访联合三类聚类

- 意图：让两个相邻视频片段中的同一匿名说话人使用同一编号。
- 决策：仅在操作者确认“同一参与者集合”且提供人数 3 时，复用 FunASR `SpectralCluster` 对 92 个语句样本联合聚类；精确样本按 embedding 结果标注，其他句子使用局部样本时长加权多数票。
- 理由：跨任意视频降低声纹阈值会误认真人；同一次采访可使用更强但显式的参与者集合约束。
- 证据：输出 3 个匿名类，但 27 个局部簇中 2 个低于 0.67 纯度，长片 493 句中 21 句为低置信多数票，必须保留人工复核边界。
- 生效范围：`shared_session_speaker_alignment.v1` 候选、角色复核包和私有声纹中心。
- 回滚：删除 shared-session 输出；旧逐字稿和旧匿名簇仍在。

### TRANSCRIPT-QUALITY-001：源完整性不再假阳性

- 意图：ASR 原始回执为 degraded 或存在分块边界冲突时，不得继续显示 passed。
- 决策：沿 `source_path` 追溯到机器可读 raw ASR，并读取 chunk quality、boundary review 和独立 VAD；缺 VAD 时只报告未验证。
- 理由：时间轴覆盖整段不代表每句话都被识别。
- 证据：短片当前为 `warning / speech_coverage=unverified`；长片为 `failed`，明确含 `asr_chunk_boundary_review_required` 和 3 个边界复核项。
- 生效范围：只读质量报告；不修改正文。
- 回滚：恢复单跳 lineage 会重新隐藏 raw ASR 质量，不建议回滚。

## 真实产物

- A/B manifest：`.local/cantonese-detail-v1-20260811/quality-benchmark-manifest.json`
- A/B 机器报告：`.local/cantonese-detail-v1-20260811/quality-benchmark.json`
- A/B 人工复核页：`.local/cantonese-detail-v1-20260811/quality-benchmark-review.html`
- Qwen 执行回执：`.local/cantonese-detail-v1-20260811/quality-benchmark-variant-run.json`
- 本地 Qwen 模型：`.local/models/Qwen3-ASR-1.7B`
- 短片逐语句 CAM++：`<VKP_LOCAL_OUTPUT>/vkp-cantonese-detail-20260811/utterance-v2/01-sidecar`
- 长片逐语句 CAM++：`<VKP_LOCAL_OUTPUT>/vkp-cantonese-detail-20260811/utterance-v2/02-sidecar`
- 联合三类候选：`<VKP_LOCAL_OUTPUT>/vkp-cantonese-detail-20260811/utterance-v2/shared-session`
- 人工角色复核：`<VKP_LOCAL_OUTPUT>/vkp-cantonese-detail-20260811/utterance-v2/shared-session/speaker-role-review.local.json`

上述路径仅说明本机运行产物类别；真实媒体、声纹向量、模型缓存和本机绝对路径均不进入公开仓库。

## 尚未越过的生产门

1. 12 段 Qwen 候选已完成，但人工逐字真值仍为 0/12；必须优先听审高分歧 8 段和数字冲突 4 段。
2. 只有人工盲审证明 Qwen 在细节、数字和术语上明显胜出后，才重跑两段完整采访；不会因文本更流畅直接覆盖原稿。
3. 三个匿名说话人仍需听审低纯度片段后绑定角色；当前不允许凭文本猜测自动命名。
4. 角色和粤语原文确认后，才能重新生成普通话翻译字幕与智能总结。

## 验证

- Ruff（禁用受 ACL 影响的缓存）：通过。
- Python AST：12 个修改文件通过。
- 聚焦 pytest：4 项无临时目录的基线选择与分歧回归通过；新增完整 fixture 回归在本机仍受 Windows `basetemp` ACL 阻断，真实 12 片集成报告已验证相同行为。
- 真实 GPU：短片 9/9、长片 83/83 CAM++ embedding 完成；联合聚类 92/92 完成。
- Qwen 真实 GPU：12/12 完成；SenseVoice 与正式原始 ASR 没有重跑、没有覆盖、没有联网、没有 CPU fallback。

## 2026-08-15 公开提交复审

- 复审时间：2026-08-15 21:12:46 +08:00；执行工具/模型：Codex (GPT-5.6 Sol)。
- 意图：只公开通用代码、合成回归和可复现边界，不公开真实采访、声纹向量、模型缓存或运行目录。
- 决策：将真实输出位置改为 `<VKP_LOCAL_OUTPUT>` 占位符；保留聚合指标和候选状态，不提交 `.local`/`outputs` 产物。
- 理由：声纹属于生物特征，真实逐字稿与媒体也不属于公开源码职责。
- 证据：隔离 Windows 测试入口重跑 ASR/说话人关联集合 `125 passed`；新增文件 Ruff 与格式检查通过。
- 生效范围：公开文档和通用候选适配器；不改变两段采访的本地 Bundle 或人工复核结论。
- 回滚：回退本次公开代码提交；本地运行产物独立保存，不受 Git 回滚影响。
