# MeetEval 说话人级逐字稿文字稳定性评估

更新时间：2026-07-29 00:01:13 +08:00
执行工具/模型：Codex（GPT-5.6），本地固定源码审查、Windows 构建与离线测试

## 结论

VKP 已把 MeetEval 的成熟 cpWER/tcpWER 实现接入逐字稿稳定性评估。中文场景不按
空格切词，而是把现有 Unicode 归一化后的正文拆成字符 token，因此报告中的两个指标
应读作：

- `cp_token_error_rate`：最小说话人排列后的字符错误率，即 cpCER；
- `tcp_token_error_rate`：带时间约束与 collar 的字符错误率，即 tcpCER。

这补足了两类原有盲点：整体文字完全相同，但文字被归给错误说话人；说话人总时长正确，
但局部文字与时间归属不一致。它与 pyannote DER 是三个独立维度：

1. 原有 normalized text distance 检查全局正文；
2. pyannote DER 检查谁在何时说话；
3. MeetEval cpCER/tcpCER 检查谁在何时说了哪些字。

该能力只用于本地评估，不改原始 ASR、人工纠错、摘要、说话人标签或生产路由。报告只写
聚合计数和匿名映射，不写逐字稿正文、token、姓名或原始 speaker label。

## 固定上游与真实运行证据

- 项目：`fgnt/meeteval`
- 仓库：`https://github.com/fgnt/meeteval.git`
- 固定 commit：`184ff17eb77fd6db4aba27a9e303a6a3edb09364`
- 本地源码：
  `%WORKSPACE_ROOT%\source-reviews\vkp-speaker-evaluation-20260728\meeteval`
- 许可证：MIT
- 隔离环境：Python 3.12
- 直接调用：
  - `meeteval.wer.wer.cp.cp_word_error_rate`
  - `meeteval.wer.wer.time_constrained.tcp_word_error_rate`
- 上游定向测试：`30 passed, 1 deselected`
- 唯一 deselect：依赖外部 Perl 的 `test_md_eval_22`；不属于 cpWER/tcpWER Python
  运行合同，也没有为此增加 Perl 运行时。

PyPI `meeteval 0.4.3` 的旧 sdist 在本机 Python 3.13 / VS2019 路线缺少 Windows
C++20 编译选项。固定的官方 main commit 已在 `setup.py` 为 Windows 使用
`/std:c++20`，在 Python 3.12 隔离环境真实构建并通过测试。因此 `evaluation`
optional extra 锁定该 commit，而不是伪装成旧 PyPI 版本可用。

## 变更的五字段记录

### 1. MeetEval 指标适配

- **意图**：发现整体文字和说话人时间轴看似正常、但具体文字被分配给错误说话人的问题。
- **决策**：直接调用上游 cpWER/tcpWER；VKP 只负责把已有 speaker/timestamp/text
  转成上游公开输入合同，以及把结果匿名化。
- **理由**：最小排列、编辑距离、时间约束和 speaker 数量差异处理都是成熟算法，不应在
  VKP 重新实现。
- **证据**：官方 30 条相关测试通过；交换匿名 speaker label 的 VKP fixture 在最优映射
  后 cpCER/tcpCER 均为 0。
- **生效范围**：`speaker_transcription_evaluation.py` 与本地稳定性报告；不影响任何
  生产逐字稿或模型调用。

### 2. 中文字符 token

- **意图**：让没有天然空格边界的中文对话得到可解释、可重复的文字差异指标。
- **决策**：复用 VKP 已有 Unicode/NFKC、大小写与标点归一化，然后按内容字符计分；
  输出明确标记 `token_unit=normalized_character`。
- **理由**：直接把整句中文交给按空格切词的 WER 会把一整句当成一个 token，结果失真；
  另建分词器又会引入模型、词典和版本漂移。
- **证据**：人工确认词例“佛医保”“送了意外险”“根据情况来的嘛”“明亚保险”均按字符
  输入测试；报告不泄漏这些 token。
- **生效范围**：中文/无空格逐字稿的说话人文字评估；原始文本和现有总体文本距离不变。

### 3. 显式稳定性门

- **意图**：让批量基准可以要求说话人文字归属必须稳定，同时不破坏旧流程。
- **决策**：新增 `--require-speaker-transcription`、独立 cp/tcp 阈值和时间 collar；
  默认不强制，显式启用时缺依赖、缺 speaker、缺正时长或超阈值均 fail-closed。
- **理由**：评估依赖不应成为 core 强依赖；但用户明确要求说话人标签时，也不能把
  `runtime_not_ready` 静默当作通过。
- **证据**：fake runtime、缺依赖、缺 speaker、时间边界、真实 MeetEval 和整体 gate
  均有离线回归。
- **生效范围**：`transcript-stability-evaluation` CLI/JSON；不触发 diarization、
  ASR、下载、网络或 fallback。

### 4. 隐私与来源忠实边界

- **意图**：评估真实客户沟通稿而不把敏感正文复制进报告、文档或源码账本。
- **决策**：只输出行数、speaker 数、token 数、错误计数、匿名 optimal mapping 和
  阈值；参考稿继续禁止进入 prompt、热词或路由。
- **理由**：评估参考是真值候选，不是生产纠错来源；speaker 编号也不是现实身份。
- **证据**：回归明确断言报告不含输入 token、正文和原 speaker label。
- **生效范围**：所有 speaker transcription evaluation 产物。

## 用户样本离线核验

用户提供的原始双说话人 ASR 与 GetBrain 合并 Markdown 只读解析后，使用显式
`--allow-legacy-unbound --require-speaker-transcription` 做单次对照：

- 正文 token：12,090 / 12,090
- 匿名说话人数：2 / 2
- 最优映射数：2
- cpCER：0
- tcpCER：0
- cp/tcp 错误数：0 / 0
- 整体 normalized text distance：0
- 状态：`stable`

这只证明两份本地文件的文字及其说话人/时间归属一致，不能证明它们相对录音绝对正确，
也不评价智能总结。由于参考文件没有 GetNote ID，本次绑定状态是 `legacy_unbound`；
生产批量评估仍必须使用
`视频 SHA-256 → GetNote ID → 参考稿 SHA-256` 的精确参考绑定。

用户确认的四项纠正仍遵守既有规则：原始 ASR 保留，只有
`human_confirmed` 决定可以正式写回；目标是还原音频原意，不做外部世界事实核查。

## 使用方式

安装可选评估依赖：

```powershell
python -m pip install -e ".[evaluation]"
```

同时要求说话人时间归属和说话人文字归属：

```powershell
python -m video_knowledge_pipeline.transcript_stability_evaluation `
  <candidate-transcript> `
  <reference-transcript> `
  <report.json> `
  --reference-binding <reference-binding.json> `
  --require-speaker-attribution `
  --require-speaker-transcription `
  --max-diarization-error-rate 0.05 `
  --max-cp-speaker-character-error-rate 0.05 `
  --max-tcp-speaker-character-error-rate 0.05 `
  --speaker-transcription-collar-seconds 1.0
```

阈值语义为严格小于。生产基准应同时保留总体文本距离、DER、cpCER 和 tcpCER，不能用
其中一个指标替代另外三个。

## 后续缺口

- 当前真实样本是同源导出对照，尚未覆盖“不同 ASR 引擎 + 说话人分离”盲测。
- 应在既定短/中/长/超长 8–12 条样本中记录 DER、cpCER、tcpCER、缺段率和人工复核
  时间，再决定批量阈值。
- 当前最后一段的结束时间仍可能未知；tcpCER 只计算正时长 token 行，并在报告中显式
  记录参与行数。
- 不推断“说话人1/2”对应客户、经纪人或真实姓名；角色命名仍须人工确认。
