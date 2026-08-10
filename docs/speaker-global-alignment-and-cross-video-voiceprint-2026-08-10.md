# VKP 分块全局说话人与跨视频匿名声纹候选

更新时间：2026-08-10 16:23:22（Asia/Shanghai）
执行工具/模型：Codex / GPT-5.6 Sol

## 结论

VKP 现在能够把一次录音中各 ASR 分块的临时 CAM++ 聚类映射成稳定的
`speaker-global-001`、`speaker-global-002` 等匿名编号。用户显式同意在本机保存生物特征后，
还可把不同视频中的全局说话人中心与本地匿名声纹库比较；输出只能是“疑似同一人 + 相似度”，
不会自动推断姓名或真人身份。角色（如“采访者”“客户”“家属”）只能经人工确认后显式绑定。

## 固定上游与实测证据

- 固定源码：`D:\used-by-codex\source-reviews\FunASR-1.3.30-16cd165`
- 上游版本：FunASR `1.3.30`
- 固定 commit：`16cd165ac3946cc8c08bf845331f91fefec8e1a9`
- 直接参考入口：`funasr.bin.realtime_ws.HybridSpeakerTracker._map_cluster_centers`
- 直接复用的上游行为：向量归一化、余弦相似度、同一活动窗口的 `used_ids` 防坍缩、
  有界增量质心更新，以及 `AutoModel.generate(return_spk_center=True)` 的中心输出合同。
- 上游源码回归：`1 passed, 59 deselected`。
- VKP 手工离线 E2E：两个分块交换本地标签后仍映射成两个稳定全局说话人；公开产物不含向量，
  私有 sidecar 与 checkpoint 保留恢复所需质心。

MOSS-Transcribe-Diarize 与 sherpa-onnx 仍作为候选证据源；本实现不复制它们的推理代码，
也不把尚未完成生产质量门的模型静默切成默认路线。pyannote.metrics 和 MeetEval 继续承担
DER/JER、cpCER/tcpCER 等质量验收，不重新实现评分算法。

## 变更记录

### SG-01：保留并消费 CAM++ 分块质心

- 意图：让同一个真人跨五分钟分块后仍使用同一匿名编号。
- 决策：FunASR 调用显式请求 `return_spk_center=True`，只把每个修正后 `spk` 的中心写入私有
  chunk/checkpoint；公开 ASR 和 Bundle 不保留向量。
- 理由：此前只保留 chunk-local `spk`，丢弃了完成全局对齐所必需的成熟上游证据。
- 证据：固定 FunASR `postprocess` 使中心顺序与 `sentence_info[].spk` 对齐；fake runner 回归验证
  请求参数、numpy-like 序列化与私有字段。
- 生效范围：显式启用 CAM++ 的本地分块 ASR；正文、时间戳、原 `spk` 和默认 ASR 路由不变。
- 回滚：移除 `return_spk_center` 和全局对齐步骤即可恢复旧 chunk-local 行为。

### SG-02：录音内全局匿名编号

- 意图：修复多个分块把三名真人拆成五个或更多临时簇的问题。
- 决策：薄适配 FunASR 的质心映射，并复用 VKP 既有 LocalAgreement/重叠窗口证据作为相邻块锚点；
  每个句段保留 `speaker_local_cluster`，新增 `speaker_global_id`。
- 理由：中心相似度负责跨块身份连续性，重叠文本只作佐证；二者都不能单独证明真人身份。
- 证据：交换 chunk-local 标签的离线样本稳定映射；同一分块两个相似中心不会坍缩成一个全局 ID；
  缺质心或超过人数上限时 fail-closed 为 `unavailable/degraded`。
- 生效范围：派生的 `speaker_global_alignment.v1`、标准化说话人字段和 reader 显示；不改原始证据。
- 回滚：下游会自动回退读取旧 `speaker/spk` 字段，旧 Bundle 保持兼容。

### SG-03：公开/私有产物隔离

- 意图：避免生物特征进入 Git、聊天、Bundle 或在线模型请求。
- 决策：公开 JSON 只含匿名映射、方法与置信度；质心只进入
  `*-speaker-global-alignment.private.json`，并加入 `.gitignore`。
- 理由：声纹 embedding 属于生物特征；跨视频比较必须默认本地、可删除。
- 证据：回归确认公开 JSON 不出现 `center`；私有合同带
  `biometric_data/must_remain_local/must_not_be_committed`。
- 生效范围：全局声纹 sidecar、注册表和 CLI；不改变 provider gateway 或 consent。
- 回滚：删除本地私有 sidecar/注册表即可撤销，无需改 canonical transcript。

### SG-04：跨视频候选匹配与人工角色绑定

- 意图：识别不同片段里“疑似同一位说话人”，同时防止自动认人。
- 决策：只有显式 `enroll` 才写本地匿名声纹库；`match` 排除同一来源 revision 与自身匹配，
  仅返回候选相似度；`bind-role` 需要明确确认，`delete` 支持逐条删除。
- 理由：自匹配会制造 100% 假阳性；相似声纹不等于已确认身份；角色来自用户复核而非模型猜测。
- 证据：重复 enrollment 幂等、同来源无匹配、第二来源候选匹配、未确认角色绑定和删除均 fail-closed。
- 生效范围：用户指定的本地 registry；不自动跨视频扫描、不上传、不写真人姓名。
- 回滚：删除 registry 或指定 voiceprint；角色字段不影响原 ASR 与 Timeline。

## CLI

```powershell
python -m video_knowledge_pipeline.cli speaker-global-align `<chunked-output.json>`

python -m video_knowledge_pipeline.cli speaker-voiceprint enroll `
  --private-alignment `<alignment.private.json>` `
  --registry `<local-voiceprints.private.json>` `
  --source-id `<anonymous-run-id>` `
  --confirm-local-biometric-storage

python -m video_knowledge_pipeline.cli speaker-voiceprint match `
  --private-alignment `<another-alignment.private.json>` `
  --registry `<local-voiceprints.private.json>`

python -m video_knowledge_pipeline.cli speaker-voiceprint bind-role `
  --registry `<local-voiceprints.private.json>` `
  --voiceprint-id `<voiceprint-id>` `
  --role-label `采访者` `
  --confirm-role-binding

python -m video_knowledge_pipeline.cli speaker-voiceprint delete `
  --registry `<local-voiceprints.private.json>` `
  --voiceprint-id `<voiceprint-id>` `
  --confirm-delete
```

## 当前两段采访的迁移边界

已有采访运行是在本变更之前生成的，其 chunk JSON 没有 `spk_embedding_center`，因此不能仅凭五个旧标签
安全推回三个真人。要获得稳定的三个全局匿名编号，需要在空闲 GPU 上使用同一 CAM++ 模型重新提取分块质心，
或执行新的分块 ASR；成功块可走 checkpoint，不需要上传或调用在线模型。未经该证据，不会把五簇强行合并成三人。

## 后续真实验收

1. 对这两段采访执行一次本地 CAM++ 质心补采并生成全局 sidecar。
2. 人工只确认全局编号与“采访者/客户/家属”的角色绑定。
3. 用固定样本统计 DER、JER、误拆分率、误合并率和 cpCER/tcpCER。
4. 跨视频仅比较用户选定的本地文件；注册表默认不出机、不进版本库。
