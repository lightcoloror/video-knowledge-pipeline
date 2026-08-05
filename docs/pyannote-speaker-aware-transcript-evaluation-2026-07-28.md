# pyannote 说话人感知逐字稿稳定性评估

更新时间：2026-07-29 00:01:13 +08:00
执行工具/模型：Codex（GPT-5.6），本地源码审查与离线测试

## 结论

VKP 已增加可选的说话人归属稳定性门。它复用
`pyannote.metrics` 的 Diarization Error Rate（DER）和 Hungarian 最优说话人映射，
用于发现“文字相同但说话人被交换、漏标或多标”的问题。它不会推断真实身份，也不会把
参考稿、说话人姓名或逐字稿正文写入评估报告。

该能力是评估层，不修改原始 ASR，不覆盖说话人标签，不进入提示词、热词、路由或生产
事实。默认保持向后兼容；只有显式启用 `--require-speaker-attribution` 时，缺少可用
说话人证据或缺少可选运行依赖才会使稳定性门失败。

## 上游复用证据

- 项目：`pyannote/pyannote-metrics`
- 固定 commit：`e8000509ee06331ef3e0fec08fa3605af834efbb`
- 本地源码：
  `%WORKSPACE_ROOT%\source-reviews\vkp-speaker-evaluation-20260728\pyannote-metrics`
- 许可证：MIT
- 直接复用的公开合同：
  - `pyannote.metrics.diarization.DiarizationErrorRate`
  - `optimal_mapping` 中基于 Hungarian assignment 的匿名标签对齐
  - `collar=0`、`skip_overlap=False` 的严格评估语义
- 上游官方定向测试：`12 passed`，另有 9 条 UEM 近似提示。
- VKP 没有复制上游算法；只增加输入归一化、匿名化报告、可选依赖和质量门胶水。

## 变更说明

### 1. 说话人 DER 适配器

- 意图：补足“逐字稿文字相同，但说话人归属错误”这一原稳定性评估盲点。
- 决策：调用 `pyannote.metrics` 官方 DER 与最优映射，不自行实现打分算法。
- 理由：说话人标签是任意匿名编号，必须先做全局最优映射，不能直接比较
  `说话人1/说话人2` 字符串。
- 证据：交换匿名标签的 fixture 在最优映射后 DER 为 0；缺少说话人段落在
  `required=True` 时会 fail-closed。
- 生效范围：`speaker_diarization_evaluation.py` 和稳定性评估报告；不影响 ASR、
  语义纠错、摘要或生产转写。

### 2. 稳定性评估门

- 意图：让文本距离、长内容完整性和说话人归属形成彼此独立的质量维度。
- 决策：新增 `--require-speaker-attribution` 和
  `--max-diarization-error-rate`；默认阈值为严格小于 `0.05`。
- 理由：只比较文字会漏掉整段说话人互换；同时不能让未安装可选依赖破坏旧流程。
- 证据：启用必需门时，DER 不通过会使总体状态不稳定；未启用时以
  `not_required`/诊断信息保留，不改变既有结果。
- 生效范围：`transcript-stability-evaluation` 命令及其 JSON 报告。

### 3. GetBrain 说话人时间戳输入

- 意图：直接评估操作者实际收到的“说话人 + 时间戳 + 正文”导出，而不是手工转 JSON。
- 决策：复用 VKP 共享 `parse_transcript`；保留旧 Logseq
  `- 原始转录` 树解析器；Markdown 若两种边界都不具备则拒绝。
- 理由：普通总结 Markdown 的标题和摘要不能冒充逐字稿，否则完整率与 DER 都会产生
  假阳性。
- 证据：真实本地原始 ASR 文本和合并文档均解析为 433 段、2 位匿名说话人；
  summary-only Markdown fixture 会 fail-closed。
- 生效范围：本地评估输入加载；参考内容继续禁止进入生产提示词、热词和路由。

### 4. 可选安装矩阵

- 意图：保持 `core` 安装轻量，同时提供可重复的说话人评估环境。
- 决策：`evaluation` extra 同时包含 `pyannote-metrics>=4.1,<5` 与固定官方
  MeetEval commit；DER 与 speaker-attributed cpCER/tcpCER 共用同一个显式评估环境。
- 理由：四项指标只在基准和质量门中需要，不应成为所有 VKP 运行的强制依赖。
- 证据：全局环境缺依赖时的 fail-closed/非阻断两类 fixture 均通过；隔离环境中的真实
  pyannote 和 MeetEval 调用测试均通过。
- 生效范围：安装元数据与评估命令，不安装模型、不启动服务。

## 本地真实样本验证

对用户提供的本地咨询录音配套原始 ASR 与 GetBrain 合并文档做了一次显式
`legacy_unbound` 评估。只记录聚合指标，不把正文写入报告或仓库：

- 两侧段落：433 / 433
- 两侧匿名说话人数：2 / 2
- 正时长说话人段：426 / 426
- 评估时间轴：3529 秒
- 归一化文本距离：0
- 表面文本距离：0
- 文本长度比：1.0
- 时间长度比：1.0
- DER：0
- confusion / false alarm / missed detection：0 / 0 / 0 秒
- 总体状态：`stable`

这说明这两份文件的逐字稿正文、时间戳和说话人归属相同；它不能证明 ASR 文字本身
相对音频完全正确，也不能验证后来生成的 AI 智能总结。

严格参考绑定创建同时按预期被拒绝，原因是该 GetBrain 文件没有 GetNote ID：
`getnote_id_missing`。生产批量评估仍必须使用
`视频 SHA-256 → GetNote ID → 参考稿 SHA-256` 的精确绑定；本次
`legacy_unbound` 只用于用户明确提供的单次本地对照，没有放宽该硬门。

## 命令

安装可选评估依赖：

```powershell
python -m pip install -e ".[evaluation]"
```

评估并要求说话人门：

```powershell
python -m video_knowledge_pipeline.transcript_stability_evaluation `
  <candidate-transcript> `
  <reference-transcript> `
  <report.json> `
  --reference-binding <reference-binding.json> `
  --require-speaker-attribution `
  --max-diarization-error-rate 0.05
```

## 验证结果

- pyannote 上游官方定向测试：`12 passed`
- MeetEval 上游 cpWER/tcpWER 定向测试：`30 passed, 1 deselected`
- MeetEval deselect 仅为依赖外部 Perl 的 `md-eval` 对照，不属于本适配运行合同。
- VKP 全局环境关联回归：`30 passed, 3 skipped`
- Python 3.12 隔离环境真实 MeetEval 集成：`21 passed`
- 本地用户样本：12,090 / 12,090 字符 token、2 / 2 speakers、cpCER=0、
  tcpCER=0；仅记录聚合指标。

## MeetEval 缺口已关闭

原先的 PyPI `meeteval 0.4.3` 在 Python 3.13 / VS2019 路线因 Windows C++20
编译选项缺失而失败。此问题没有通过自研算法规避，而是固定并真实构建官方 commit
`184ff17eb77fd6db4aba27a9e303a6a3edb09364`；该版本已包含 Windows
`/std:c++20` 修复，并在 Python 3.12 隔离环境通过官方与 VKP 测试。

中文输入复用 VKP 现有归一化并按字符 token 交给官方 cpWER/tcpWER，因此对外明确
称为 cpCER/tcpCER。完整五字段记录、命令、隐私边界和真实样本聚合证据见
`docs/meeteval-speaker-transcription-evaluation-2026-07-29.md`。
