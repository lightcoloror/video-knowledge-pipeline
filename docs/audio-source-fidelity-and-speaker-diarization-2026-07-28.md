# 录音原意还原与说话人分离补强

更新时间：2026-07-28 17:49:09 +08:00
执行者：Codex / GPT-5.6

## 结论

VKP 的逐字稿与智能总结现在采用两条彼此独立的规则：

1. **来源忠实（source fidelity）**：目标是还原录音或视频里实际表达的内容，不负责判断讲者的观点在外部世界是否正确。诸如“目前条款设计最优”应保留并标明是讲者的观点；只有音频不清、证据冲突或模型自行添加的内容才进入复核。
2. **说话人分离（speaker diarization）**：对话型录音必须保留每段的时间、匿名说话人簇和文本。`说话人1/说话人2` 是稳定匿名标签；“经纪人/客户”属于可选角色解释，不能替代原始 speaker cluster，也不能猜姓名。

本轮只接入和保全已有 ASR/diarization 结果，没有下载或运行新的模型，没有调用在线 API，也没有上传录音。

## 开源模块复用

| 上游 | 固定版本 | 实际复用 | 拒绝项 |
| --- | --- | --- | --- |
| OpenMOSS/MOSS-Transcribe-Diarize | `eda4b9f13f1574765a80438c9797780a9bd48112` | 直接适配其 `mtd-subtitle` 前门、`segments.json` 的 `start/end/text/speaker` 合同，以及 `[start][Sxx]text[end]`/字幕说话人表示法 | 不复制模型推理；不自动下载模型；不在缺运行时时静默切回别的 ASR |
| Bilinote 字幕入口 | VKP 已固定的既有复用路线 | 继续复用现有字幕解析器；只增加 MOSS 风格 speaker prefix 的薄适配 | 不实现第二套 SRT/VTT 解析器 |
| FunASR/SenseVoice | `516c4f770496a5cbb89c8e2e447211bbb7b0db71` | 保留 provider 已产生的 speaker metadata，并沿现有 VKP 标准化/分块/检查点链传递 | 不把没有 diarization 的普通 ASR 伪装成已分人 |
| WhisperX | `5f2f9d4320dd93a7d12f5ba2495eef7e0a5af963` | 吸收“转写、对齐、说话人证据分层保存”的架构边界 | 不新增 WhisperX 运行时；不让对齐或角色推断覆盖原始逐字稿 |

上游轻量实测：直接加载 MOSS `transcript_parser.py`，输入两段 `[S01]`/`[S02]` 紧凑转写，正确得到两条独立 segment 及其 speaker。完整上游测试暂未运行成功，因为当前全局 Python 环境的 `tokenizers==0.21.1` 与上游 `transformers` 要求的 `>=0.22,<=0.23` 不兼容；真实模型试验仍应放入隔离 Python 3.12 环境。

## 逐项变更记录

| 变更 | 意图 | 决策 | 理由 | 证据 | 生效范围 |
| --- | --- | --- | --- | --- | --- |
| `transcript_speakers.py` | 统一 speaker 合同 | 新增薄适配器，把原始 cluster 映射为首现顺序的 `说话人N`，角色单独保存 | MOSS 原生区分 speaker；角色和身份推断不等于 diarization | MOSS parser/subtitle 源码与轻量实测 | 仅序列化、显示和键归一化，不运行模型 |
| `models.py` | 让 speaker 穿过既有管线 | `TranscriptCue` 增加可选 `speaker`、`speaker_role`、`metadata`，默认值保持兼容 | 如果只藏在临时 JSON，清理/合并/导出会丢失说话人 | 旧构造调用无需修改；相关回归通过 | 所有逐字稿 cue；旧无 speaker 产物仍可读 |
| `transcript.py` | 读取 JSON 和字幕里的 speaker | 保留顶层或 metadata speaker；复用原字幕解析器解析 speaker prefix | 避免第二套字幕解析器和重复状态机 | JSON 与 SRT round-trip 回归 | 本地逐字稿解析 |
| `asr_adapter.py` | 标准化时不丢 diarization | 从 MOSS/FunASR 记录提取 speaker，JSON 同时写 raw cluster、显示 label、role；SRT 加匿名标签 | reader 输出需可读，机器产物需保留原 cluster | MOSS 合同回归、SRT round-trip | ASR 归一化产物；不改变 provider 选择 |
| `transcript_postprocess.py` | 清理和分段保持发言边界 | 所有变换传递 speaker；不同 speaker 或“有标签/无标签”边界禁止默认合并 | 跨说话人合并会把客户的话错误归给经纪人 | 同 speaker 可合并、跨 speaker 与半标注边界回归 | 本地后处理；显式变换记录继续保留 |
| `transcript_source_arbitration.py` | 仲裁后仍可追溯发言者 | 把 speaker/role/metadata 原样写入获胜 segment | 文本来源仲裁不拥有说话人重命名权 | arbitration 关联回归通过 | 本地候选仲裁，不执行角色识别 |
| `transcript_semantic_correction.py` | 纠错不能破坏 speaker，也不能做外部事实审查 | replace/split/merge 保留 speaker；跨 speaker merge fail-closed；提示改为 source fidelity | 语义纠错只还原录音，不应改写讲者观点 | 纠错与 ASR 关联回归 115 项通过 | 语义纠错候选、人工确认和模型草稿 |
| 四个用户纠正词 | 固化本次已确认原意，同时避免全局误改 | `根情况来的嘛→根据情况来的嘛`、`活医保→佛医保`、`送了一外险→送了意外险`、`民亚保险→明亚保险`；全都进入 review-only candidate，只有 human-confirmed 才正式应用 | 同形误识别在别的录音里未必成立，不能全局静默替换 | 单段四项人工确认回归，speaker 保持 `S01` | 当前人工确认可写回；未来录音只提示复核 |
| `transcript_agent_readable.py` / `transcript_readable_llm.py` | 人读版和模型输入不丢发言者 | 传递 speaker 并在可读文本前显示匿名标签 | 下游若看不到 speaker，摘要会混淆问答双方 | reader/LLM 回归通过 | 可读逐字稿与受控总结输入 |
| `transcript_quality_gate.py` | 对话录音缺少分人时不能误报合格 | 支持 manifest 自动要求或 CLI 显式要求；检查已标注 segment/时长覆盖及最少 speaker 数 | 时间覆盖完整不代表说话人识别完成 | 无 speaker 必须报 `speaker_diarization_required`；两位完整标注通过 | 对话型录音质量门；单人内容默认不强制 |
| `cli.py` | 给操作者稳定前门 | 增加 `--require-speaker-diarization`、`--min-speaker-count` | 不能依赖内部 Python 调用或隐含配置 | CLI help 实测显示两个参数 | `transcript-quality-gate` |
| Smart Summary 三处提示 | 总结忠实于来源 | 要求将主观/产品观点归因给说话人；外部真伪不是总结任务 | 防止把“未核实”误当成漏转或删掉原意 | prompt contract 回归 | 章节生成、章节工作流、最终知识文档 |
| `knowledge_note_export.py` | 最终逐字稿含 speaker 且不误删对话 | 显示 `说话人N`；去重键从纯文本改为 `(speaker,text)` | 两个人说同一句话不是重复 segment | 两位 speaker 同说“你好”均保留的回归 | 最终人读文档，不改变机器真源 |

## 质量门使用

显式要求一段录音至少识别两位说话人：

```powershell
$env:PYTHONPATH = 'src'
python -m video_knowledge_pipeline.cli transcript-quality-gate `
  'D:\path\to\webui-bundle' `
  --require-speaker-diarization `
  --min-speaker-count 2
```

也可以在 Bundle `manifest.json` 中声明：

```json
{
  "transcript_requirements": {
    "speaker_diarization_required": true,
    "expected_speaker_count": 2
  }
}
```

当 diarization 缺失或覆盖不完整时，报告使用独立状态 `speaker_diarization_required`，不会把它混成 ASR 缺段、术语错误或外部事实问题。

## 验证

- `test_transcript_speaker_source_fidelity.py`：8 passed。
- speaker/subtitle/readable/quality/arbitration 组合：40 passed。
- ASR 与 semantic correction：115 passed，1 个第三方 warning。
- knowledge export/final reading/Smart Summary：55 passed，1 个第三方 warning。
- 合计：213 个相关唯一测试通过；无断言失败。新增 3 项覆盖双人 Bundle 端到端导出、音频 MIME 识别和 diarization 实测人数优先级。
- 修改文件 `git diff --check` 通过；隔离 pycache 的 `compileall` 通过。
- 一次测试命令误写了不存在的 `tests/test_smart_summary_section_workflow.py`，没有收集或执行测试；改用实际测试文件后通过。

## 尚未覆盖的真实风险

1. 当前实现**保留和校验** provider 的 speaker 输出，但不会凭空给没有 speaker 的 SenseVoice 结果补分人。
2. MOSS CLI 和模型当前尚未安装到隔离运行时，仍需一次短脱敏双人录音的 GPU A/B，衡量 DER、speaker confusion、时间戳、速度和显存。
3. 角色 `经纪人/客户` 只能来自上游可靠 metadata 或人工确认；未确认时只显示匿名 `说话人N`。
4. 本轮四项纠正不会对所有录音做不可逆全局替换；未来命中时先生成候选，避免同音词在别的语境中被误改。


## 最终阅读文档端到端补充

更新时间：2026-07-28 18:44:00 +08:00 | Codex / GPT-5.6

| 变更 | 意图 | 决策 | 理由 | 证据 | 生效范围 |
| --- | --- | --- | --- | --- | --- |
| 双人 Bundle 最终导出回归 | 证明 speaker 不只停留在单元模块 | 复用现有 `export_knowledge_note → render_final_reading_note`，不增加第二导出器 | 单元测试无法发现下游去重或标签丢失 | 合成 MOSS 合同 Bundle 经质量门后，在同一 `knowledge-note.md` 中同时出现智能总结区、`说话人1/2` 逐字稿，且无内部来源/仲裁字段 | 离线 contract 测试 |
| 录音内容类型 | 避免 `.ogg` 录音被硬编码为“视频整理” | manifest 的 `content_type/recording_type/expected_content_type` 优先；否则复用既有 `_smart_source_path` 和 Python 标准 `mimetypes` | 不应为一个显示标签重复 FFprobe 或媒体 registry | `.ogg→录音整理`、`.mp4→视频整理`、显式 `客户沟通` 优先的测试 | 最终人读 Markdown metadata |
| 参与人数 | 把 diarization 证据带入“录音信息” | 优先读取质量门 `distinct_speaker_count`，再回退到 manifest 声明 | 摘要模型不能凭文本猜人数 | observed=2、declared=3 时最终采用 2 的测试；双人 E2E 显示“约 2 人” | 最终人读 Markdown metadata；不推断姓名或角色 |

当前增量验证：知识导出/说话人扩展套件 `45 passed, 1 third-party warning`；Smart Summary 安装与 canonical selector `20 passed`；直接 metadata/reader 套件 `5 passed`。全部离线，无模型、网络、上传或生产 Bundle 写入。

## MOSS 隔离源码运行补充

更新时间：2026-07-28 18:32:17 +08:00 | Codex / GPT-5.6

| 变更 | 意图 | 决策 | 理由 | 证据 | 生效范围 |
| --- | --- | --- | --- | --- | --- |
| 固定上游实际测试 | 避免只看 README 或只测自写适配器 | 在 Python 3.12 隔离命名空间中直接执行上游 parser/subtitle/export/postprocess 测试 | 推理依赖未安装不应阻止验证轻量合同 | 上游 `18/18` 通过 | 仅源码证据，不代表模型已可运行 |
| MOSS 原始边界硬门 | 避免默认字幕美化改写机器真源 | 只消费官方 CLI 以 `postprocess=False` 写出的 `segments.json`；增加顺序、ID、start/end、text、speaker 全字段保持测试 | 上游 `normalize_segments` 会排序、合并、拆分和调整时间，适合字幕展示但不适合作为逐字稿真源 | MOSS 定向 `3/3`、完整 ASR pipeline `50/50` | MOSS 归一化；不改变其他 ASR |
| 可执行性预检 | 在模型缺失时明确阻断 | 复用现有 `plan-asr` / `run-asr-plan` 模型缓存门，不新增第二 doctor | 当前真正缺口是依赖和模型，而不是 provider 路由 | 计划识别隔离 CLI 与 CUDA；执行状态为 `asr_model_not_ready`，未进入推理 | 本地 fail-closed；无自动下载、无 fallback |

此前“完整上游测试未运行”的描述仍适用于推理、Torch/Transformers、
进度 streamer 和真实音频测试；轻量 parser/subtitle 部分现已由上述
`18/18` 证据取代。增量加入 1 条 VKP 边界保持测试后，本专题相关唯一
回归累计为 `214` 项。

## FunASR CAM++ 说话人模型就绪硬门

更新时间：2026-07-29 01:28:27 +08:00 | Codex / GPT-5.6

| 字段 | 记录 |
| --- | --- |
| 意图 | 当录音要求区分说话人时，确保“已启用 diarization”真正对应一个本地可用的说话人模型，避免最终逐字稿丢失 `说话人1/2`。 |
| 决策 | 直接复用固定 FunASR commit `516c4f770496a5cbb89c8e2e447211bbb7b0db71` 的 `spk_model=cam++`、`sentence_info[].spk` 与现有 VKP `_resolve_local_model` 缓存解析；`plan-asr` 在显式请求 CAM++ 且本地模型缺失时返回 `available=false` 和 `speaker_model_missing_or_not_downloaded:cam++`，执行器在启动子进程前阻断。 |
| 理由 | FunASR 上游会构建 speaker model、聚类 embedding，并用 `distribute_spk` 写入 `sentence_info`；若只检查主 ASR 模型，缺 CAM++ 时可能在执行期下载或失败，造成伪就绪。VKP 不应复制 diarization 推理，也不应静默下载或退回无说话人输出。 |
| 证据 | 固定源码 `funasr/auto/auto_model.py` 明确在 `spk_model` 模式聚类并写 `sentence_info`，`funasr/utils/speaker_utils.py` 负责分配；本机 SenseVoice、FSMN-VAD、CT-Punc 已缓存，CAM++ 状态为 `missing_or_not_downloaded`；新增缺模型零子进程回归与已缓存模型回归，关联 ASR/人工纠词/最终 reader 共 `63 passed`。 |
| 生效范围 | 仅 FunASR、SenseVoice、Fun-ASR-Nano、Contextual Paraformer 且显式传入 `spk_model` 的本地计划。未启用说话人分离的旧路线行为不变；MOSS、在线 API、外部上传、模型下载、角色/姓名推断均不在本次范围。 |

上游 `speaker_utils.smooth` 会把短于一秒的片段按邻近说话人平滑，因此模型输出仍是候选说话人证据，不等于人工确认的真实身份。最终显示只使用匿名 `说话人N`；本录音四项用户确认纠词只还原音频原意，不做外部事实核查，也不扩散为全局静默词典。

## CAM++ 国内缓存准备前门

更新时间：2026-07-29 02:07:49 +08:00 | Codex / GPT-5.6

| 字段 | 记录 |
| --- | --- |
| 意图 | 让操作者在下载前看清 CAM++ 的来源、精确模型 ID、目标本地 Python 和 GPU 计划，避免把“配置了 `cam++`”误当成模型已就绪。 |
| 决策 | 复用 FunASR 固定源码中的 ModelScope alias，把 VKP 既有 `fsmn-vad`、`ct-punc`、`cam++` 映射集中为单一常量；状态/预览报告显式输出 `hub=modelscope`、官方模型 ID 和 `network_access`。仍由 FunASR 原生 `AutoModel`/ModelScope downloader 负责准备，不新增下载器。 |
| 理由 | FunASR 上游 `name_maps_ms` 已把 `cam++` 锁定为 `iic/speech_campplus_sv_zh-cn_16k-common`，默认 Hub 也是 ModelScope，适合中国大陆访问；重复实现下载、镜像选择或缓存格式会制造双轨状态。 |
| 证据 | 固定源码 `funasr/download/name_maps_from_hub.py` 与 `download_model_from_hub.py`；真实 no-write 状态报告显示隔离 Python、`hub=modelscope`、CAM++ 缺失；真实预览显示 `network_access=disabled`、`--device cuda`，未启动下载；3 条 focused 回归通过。 |
| 生效范围 | `asr-model-cache-status` 与 `prepare-asr-model-cache` 的本地报告和缓存 alias。没有下载模型、没有运行推理、没有读取或上传音频；普通 ASR、MOSS、在线 provider 和角色身份推断不变。 |

安全准备命令分两步。第一步永不联网：

```powershell
$env:PYTHONPATH = 'src'
$env:LECTURE_ASR_PYTHON = (Resolve-Path '.conda-lecture-asr\python.exe').Path
python -m video_knowledge_pipeline.cli prepare-asr-model-cache . `
  --models 'cam++' --device cuda --no-write
```

只有操作者明确批准下载后，才在同一命令增加 `--execute --allow-download`。下载完成仍需先做短脱敏双人录音 GPU A/B；CAM++ 输出只形成匿名候选 speaker，不自动推断姓名、客户或经纪人角色。

## CAM++ GPU A/B 验收矩阵

更新时间：2026-07-29 02:19:49 +08:00 | Codex / GPT-5.6

| 字段 | 记录 |
| --- | --- |
| 意图 | 模型准备后能立即在同一短音频上比较“SenseVoice 文字基线”和“SenseVoice + CAM++ 匿名说话人”，而不是直接把新分人结果投入生产。 |
| 决策 | 扩展现有 `asr-ab-sample-plan/run/compare`，增加 `sensevoice_full_punc_campp`；该变体固定 `--device cuda --spk-model cam++`，继续复用同一采样器、FunASR runner、归一化器和报告，不新增 runner。 |
| 理由 | 同一模型、同一音频、同一 ITN/VAD/标点参数只改变 CAM++，才能隔离 speaker diarization 的实际收益和代价；另建脚本会绕开既有模型门、检查点和“不提升候选稿”边界。 |
| 证据 | 真正 CLI 预览生成 CUDA/CAM++ 命令并报告 `candidate_only=true`、`promotes_transcript=false`；缺 CAM++ 时在 `run_asr_plan` 前阻断；报告新增 speaker 数、已标注段数、已标注时长和时长覆盖率；关联回归 `92 passed / 3 optional skipped`。 |
| 生效范围 | 本地有界样本 A/B 和评估报告。不会下载模型、运行音频、覆盖逐字稿、猜测角色或上传；真实启用仍需 ModelScope 准备许可和短双人录音评测。 |

模型准备后执行同一样本的两个变体：

```powershell
$env:PYTHONPATH = 'src'
python -m video_knowledge_pipeline.cli asr-ab-sample-run `
  'D:\path\to\trial-workspace' `
  'D:\path\to\short-two-speaker.wav' `
  --duration-seconds 300 `
  --execute-sample `
  --execute-local `
  --variants 'sensevoice_full_punc,sensevoice_full_punc_campp'
```

随后直接复用既有第三方指标前门，不复制 DER/cpCER/tcpCER：

```powershell
python -m video_knowledge_pipeline.transcript_stability_evaluation `
  'D:\path\to\sensevoice_full_punc_campp\normalized-transcript.json' `
  'D:\path\to\human-reference.json' `
  'D:\path\to\campp-stability.json' `
  --reference-binding 'D:\path\to\reference-binding.json' `
  --media-path 'D:\path\to\short-two-speaker.wav' `
  --require-speaker-attribution `
  --require-speaker-transcription
```

参考稿只用于评估，不进入 ASR prompt、热词、纠错或生产真源。

## 双人固定样本与说话人参考时间窗

更新时间：2026-07-29 02:43:15 +08:00 | Codex / GPT-5.6

| 字段 | 记录 |
| --- | --- |
| 意图 | 把用户明确提供的本地双人录音与得到大脑时间轴裁成完全相同的固定窗口，为 CAM++ GPU A/B 保留可评测的匿名 speaker、边界和文本；避免 text-only excerpt 让 DER/cpCER/tcpCER 失去依据。 |
| 决策 | 新增薄适配命令 `transcript-reference-window`，直接复用 `transcript.parse_transcript`、`TranscriptCue`、现有 human-confirmed semantic correction applier、原子 JSON 写入和 SHA-256；只做边界裁剪、时间戳归零、已确认词形应用和 provenance 记录，不复制解析器、替换器、分人算法或评测算法。 |
| 理由 | 既有 `asr-ab-compare --start-seconds/--end-seconds` 只拼接文字，无法保留 speaker 时间轴；直接手工裁稿又容易破坏 source segment ID、顺序和哈希绑定。 |
| 证据 | 时间窗 focused 回归 7 条、与来源保真联合回归 15 条全部通过；真实首 300 秒窗口包含 39 段、2 个匿名说话人、段数 20/19，FFmpeg 抽取样本时长精确为 300 秒。精确 source-SHA 清单在窗口内应用 4 项人工确认替换，旧词命中归零；窗口外的“明亚保险”决定仍保留在同一清单。复用固定 pyannote 环境的自同一性 DER 为 0；复用固定 MeetEval/Python 3.12 环境的 cp/tcp token error rate 均为 0。以上只证明时间窗、人工决定和评测运行时合同可用，不代表 CAM++ 质量。 |
| 生效范围 | 本地评测专用 JSON 与 `asr-ab-sample-plan/run`；参考正文不进入终端回执、prompt、热词、路由、纠错或生产逐字稿。没有下载模型、运行 ASR、调用网络或上传。 |

稳定前门：

```powershell
.\scripts\video-knowledge.ps1 transcript-reference-window `
  '<reference-transcript>' '<trial-workspace>\reference-window.json' `
  --start-seconds 0 --end-seconds 300 `
  --human-corrections-json '<trial-workspace>\human-confirmed-source-corrections.json'
```

纠词清单必须绑定参考源 SHA-256，且每条都必须是 exact `segment_index`、
`action=replace`、`apply_scope=segment`、`human_confirmed=true`。未确认、全局、
结构变换或 SHA 不匹配均在写出参考窗前阻断。该规则只还原录音原意，不检查
保险陈述的外部事实真假，也不推断“客户/经纪人”角色。

本次来源 Markdown 没有 `getnote-id`，因此没有伪造 ID，也没有放宽批量生产的
`视频 SHA-256 → GetNote ID → 参考稿 SHA-256` 硬门。生成的窗口仅用于用户明确
提供的这一次本地对照，当前严格绑定状态仍是 `legacy_unbound`。实际 CAM++ 候选
出来后，仍需分别运行固定 pyannote DER 与 MeetEval cpCER/tcpCER，并把缺失
GetNote ID 明确保留为评测边界。

## 双人任务的文字就绪与说话人就绪分离

更新时间：2026-07-29 03:14:11 +08:00 | Codex / GPT-5.6

| 字段 | 记录 |
| --- | --- |
| 意图 | 防止“普通 ASR 文字已经出来”被误报成“带说话人逐字稿可以生产使用”。 |
| 决策 | `asr-ab-compare` 直接复用 `parse_transcript`、`cue_speaker` 和现有 A/B speaker coverage metrics；若有界参考窗明确包含两名及以上匿名说话人，则所有 spoken segment 都有标签且 speaker 数达到参考下限，才允许产生 production recommendation。 |
| 理由 | 用户明确要求区分并标注说话人；文字相似度、标点和时间覆盖均无法证明 speaker attribution 已完成。 |
| 证据 | 同一 300 秒本地样本真实运行 `SenseVoiceSmall + FSMN-VAD + CT-Punc + CUDA` 成功：20 段、1483 字、参考相似度 0.8027，但 `speaker_count=0`、speaker duration ratio=0；刷新后的比较状态为 `primary_text_ready_speaker_diarization_pending`，生产推荐为 `blocked_until_speaker_diarization_ready`。新增 2 条门控回归；ASR A/B focused 18/18、完整 ASR 管线加新门控 60/60 通过。 |
| 生效范围 | 仅 A/B 评测与生产推荐状态。普通单讲师参考不自动要求分人；参考稿不进入 prompt、热词、纠错或生产真源；没有推断客户/经纪人角色，没有联网、上传或覆盖生产逐字稿。 |

当前真实产物：

- `.local/campp-two-speaker-trial-20260729/transcripts/asr-ab-sample/asr-ab-sample-run.json`
- `.local/campp-two-speaker-trial-20260729/transcripts/asr-ab-sample/asr-ab-comparison.json`
- `.local/campp-two-speaker-trial-20260729/transcripts/transcript_e5f7e2ba9797/normalized-transcript.json`

以上“CAM++ 仍缺失”是 2026-07-29 03:14:11 的历史 checkpoint，已由下节真实
GPU 试验取代；保留它是为了说明模型准备前后的状态变化，不能再作为当前状态读取。

## FunASR 1.3.30 + CAM++ 真实双人 GPU 试验

更新时间：2026-07-29 08:32:08 +08:00 | Codex / GPT-5.6

| 字段 | 记录 |
| --- | --- |
| 意图 | 验证 VKP 能否在完全本地、不依赖当前 Agent 多模态能力的情况下，为该双人录音生成匿名说话人逐字稿，并把用户确认的“佛医保 / 送了意外险 / 根据情况来的嘛 / 明亚保险”作为本录音来源保真决定，而非外部事实判断。 |
| 决策 | 直接复用 FunASR `1.3.30` 的 SenseVoice + FSMN-VAD + CT-Punc + CAM++，继续使用 VKP 既有采样、检查点、标准化、pyannote DER 和 MeetEval cpCER/tcpCER；不复制聚类、VAD、对齐或指标算法。修复 VKP 适配层把数值 `spk=0` 当空值的兼容缺陷。 |
| 理由 | 本地固定源码旧版 `1.3.9` 在真实样本复现 `float > NoneType`；上游 `1.3.30` 已包含句级时间戳/说话人分配修复。只有“分出两人 + 文字归属正确 + 时间归属正确”同时达标，才可正式使用。 |
| 证据 | 固定本地 review repo 仍保持 commit `516c4f770496a5cbb89c8e2e447211bbb7b0db71`；另从同一 repo 获取并审查 release snapshot `16cd165ac3946cc8c08bf845331f91fefec8e1a9`（FunASR `1.3.30`），存于 `%WORKSPACE_ROOT%\source-reviews\FunASR-1.3.30-16cd165`。上游定向测试 13/13 通过；真实 300 秒 CUDA 运行 1/1 chunk 成功。修复后 CAM++ 候选为 168 段、2 个匿名说话人、168/168 有文字分段带标签，参考文字相似度 0.8036；人审三处来源保真纠正后，DER=0.24396667、cpCER=0.36036036、tcpCER=0.52852853，仍未达到既有 0.05 生产门。 |
| 生效范围 | `sensevoice_full_punc_campp` 仅保留为本地评测候选；A/B 报告的 `production_recommendation` 固定为 `blocked_until_speaker_quality_evaluation_passes`，另以 `speaker_evaluation_candidate` 显示 CAM++。不推断客户/经纪人身份，不上传音频，不覆盖正式逐字稿；参考稿因缺 GetNote ID 仍为 `legacy_unbound`，不得进入 prompt、热词或纠错真源。 |

真实证据：

- `.local/campp-two-speaker-trial-20260729/transcripts/asr-ab-sample/asr-ab-sample-run.json`
- `.local/campp-two-speaker-trial-20260729/transcripts/asr-ab-sample/asr-ab-comparison.json`
- `.local/campp-two-speaker-trial-20260729/campp-human-confirmed-pyannote-production-gate.json`
- `.local/campp-two-speaker-trial-20260729/campp-human-confirmed-meeteval-production-gate.json`
- `.local/campp-two-speaker-trial-20260729/human-confirmed-source-corrections.json`
- `.local/campp-two-speaker-trial-20260729/campp-human-confirmed-candidate-window.json`

候选窗口通过精确候选 SHA-256 绑定应用了 3 项当前窗口内的人审决定：
“根据情况来的嘛”1 处、“佛医保”2 处；“送了意外险”在 CAM++ 原稿中已正确，
未做无意义替换；“明亚保险”位于本 0–300 秒窗口之外，仍只保留在整段录音确认清单，
未伪造到样本中。纠正后旧词命中归零，168 段顺序、时间戳和匿名 speaker 均保持。

结论：VKP 已能本地输出带 `说话人1/说话人2` 的候选逐字稿，但该模型/参数在此样本
上的 speaker attribution 质量不足，不能声称已经达到得到大脑的正式效果。下一轮应
优先调 CAM++ 聚类/分段参数或评测 MOSS/Sherpa-ONNX 候选，不应掩盖指标或用角色猜测
修饰结果。

## MOSS 同窗候选接入（2026-07-29 09:32:03，Codex / GPT-5.6）

| 字段 | 记录 |
| --- | --- |
| 意图 | 在同一个精确 300 秒双人窗口中比较 MOSS 原生说话人逐字稿与 CAM++，避免换样本造成假优劣。 |
| 决策 | 把 `moss_transcribe_diarize` 接入现有 A/B plan/run/compare；执行继续委托既有 `plan_asr_run` / `run_asr_plan`，评分继续委托 pyannote.metrics 与 MeetEval；多个完整标签候选不得自动选第一个。 |
| 理由 | MOSS 已有成熟 `mtd-subtitle` 和 `segments.json` 合同；VKP 只需胶水和质量门。CAM++ 真实结果已经证明“168/168 有标签”仍可能有高 speaker confusion。 |
| 证据 | 上游固定源码 `eda4b9f...` 三组合同测试 18/18；全部 MOSS focused 回归 12/12、最终关联套件 88 passed / 3 optional skipped；真实稳定 CLI preview 发现本地 launcher，但阻断于 `missing_python_dependency:transformers` 和模型未准备，未执行推理。 |
| 生效范围 | 本地 5 分钟候选 A/B、就绪状态与报告；不安装依赖/模型、不下载、不联网、不上传、不 fallback、不推断角色、不提升逐字稿。 |

## MOSS 缓存内容硬门与本录音保真合同确认

更新时间：2026-07-29 10:06:33 +08:00 | Codex / GPT-5.6

| 字段 | 记录 |
| --- | --- |
| 意图 | 防止空缓存目录被误报为 MOSS 已安装，同时把用户最新确认的文字与说话人要求固定在同一回归中。 |
| 决策 | 直接复用 `huggingface_hub.scan_cache_dir` 检查有效 revision，再按 MOSS 固定源码真实加载合同校验配置、processor、tokenizer、remote-code 文件和完整权重分片；原意修复继续走 recording-scoped human-confirmed 决定，不转成全局静默词典。 |
| 理由 | 模型就绪必须以离线可加载内容为准；逐字稿质量则必须同时满足文字来源忠实和匿名说话人归属，不能用外部事实判断改写讲话内容。 |
| 证据 | 空 snapshot、缺权重分片、Git LFS pointer 三类均被拒绝；真实本机扫描报告无 MOSS 模型且零联网。关联套件 93 passed / 3 optional skipped，明确验证四处纠正、`说话人1/说话人2` 导出和“source fidelity，不做 external-world fact judgment”。 |
| 生效范围 | MOSS 本地 readiness 与本录音的人审写回。四项正式决定是“佛医保”“送了意外险”“根据情况来的嘛”“明亚保险”；其他录音仍只生成候选。说话人标签必须保留，但不得猜测客户/经纪人或真实姓名。 |

## CAM++ 已知说话人数诊断上限

更新时间：2026-07-29 11:07:11 +08:00 | Codex / GPT-5.6

| 字段 | 记录 |
| --- | --- |
| 意图 | 判断当前 CAM++ 双人结果的主要瓶颈究竟是“说话人数估计错误”，还是后续聚类、边界与文字归属错误；避免仅凭最终恰好得到两个 cluster 就误判原因。 |
| 决策 | 直接复用 FunASR `1.3.30` 上游 `ClusterBackend` 的 `merge_thr` 与 `AutoModel.generate(preset_spk_num=...)`，在 VKP 本地 runner 和分块 wrapper 中只增加参数透传；新增 `sensevoice_full_punc_campp_oracle_2` 固定样本诊断变体，但把它标为 `evaluation_only_known_speaker_count`，只进入 `speaker_diagnostic_variants`，永远不能满足生产 speaker gate。 |
| 理由 | 已知人数属于使用 ground-truth 的诊断上限，不是可从普通生产输入可靠获得的参数。若把它与自动路线混在一起，会造成数据泄漏，并把评测技巧误报为产品能力。 |
| 证据 | 固定上游源码 `%WORKSPACE_ROOT%\source-reviews\FunASR-1.3.30-16cd165`，commit `16cd165ac3946cc8c08bf845331f91fefec8e1a9`；上游最小聚类 smoke 在 `merge_thr=0.74`、`preset_spk_num=2` 下得到两个 cluster。真实同一 300 秒 CUDA 样本完成 168 段、2 个匿名说话人、168/168 有标签；但 DER=`0.24396667`，与自动 CAM++ 完全相同，cpCER=`0.36261261`、tcpCER=`0.53078078`，还略差于自动路线的 `0.36036036` / `0.52852853`。这证明该样本的主要瓶颈不是人数估计，而是聚类归属、分段和时间边界。 |
| 生效范围 | 仅本地固定样本 A/B、诊断报告和参数透传；不改变默认 CAM++、不自动读取参考人数、不推断角色、不覆盖正式逐字稿、不下载模型、不联网、不上传、不 fallback。生产推荐仍为 `blocked_until_speaker_quality_evaluation_passes`。 |

真实诊断证据：

- `.local/campp-two-speaker-trial-20260729/transcripts/asr-ab-sample/asr-ab-sample-run.json`
- `.local/campp-two-speaker-trial-20260729/transcripts/asr-ab-sample/asr-ab-comparison.json`
- `.local/campp-two-speaker-trial-20260729/campp-oracle-two-pyannote-production-gate.json`
- `.local/campp-two-speaker-trial-20260729/campp-oracle-two-meeteval-production-gate.json`

因此下一步不应继续把“已知为两人”当成调参捷径。更有价值的比较是：固定同一音频窗口，
分别评估 CAM++ 的聚类阈值、VAD/句界边界，以及 MOSS/Sherpa-ONNX 的独立候选；所有路线
仍必须同时通过文字来源忠实、pyannote DER 和 MeetEval cpCER/tcpCER。
