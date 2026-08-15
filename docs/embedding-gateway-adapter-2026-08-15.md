# VKP 本地 embedding 统一网关薄适配（2026-08-15）

- 更新时间：2026-08-15 21:12:46 +08:00
- 执行工具/模型：Codex (GPT-5.6 Sol)
- 上游控制面：`lightcoloror/model-provider-gateway`，固定审计提交 `6575c8089d5f28ae159a0c01cedfa3320db7d7b3`
- 状态：`candidate_only`；真实本地 runtime smoke 仍需显式配置隔离 Python 与模型目录

## EMBEDDING-001：复用统一 Owner execution 合同

- 意图：让 VKP 的本地 embedding 候选使用与 text/vision 相同的 manifest、route/gate、receipt 和错误语义。
- 决策：新增极薄 `embedding_gateway_adapter`，直接消费现有 `model-provider-gateway` 的 `owner_capability_plan.v1`、`owner_input_manifest.v1`、`owner_capability_gate.v1`、`owner_capability_receipt.v1` 和 `owner_runtime_run_report.v1`；不实现第二套模型协议。
- 理由：共享网关已经负责输入哈希、能力门、无重试与无 fallback 约束，VKP 只需要保留候选证据和下游边界。
- 证据：源码账本登记 Gateway 当前语义基线；专项合成测试覆盖幂等、route/receipt/hash/dimension drift、超时及未授权 fallback。
- 生效范围：合成或公开文本 fixture 的本地 embedding 候选；不启用在线 Provider，不改变 Timeline、规范化逐字稿、Smart Summary 或生产索引。
- 回滚：删除适配器、专项测试和本文件即可；既有 VKP Provider gateway 与 Bundle 不受影响。

## EMBEDDING-002：私有向量与公开回执分离

- 意图：避免将可检索向量、模型缓存或本机路径误提交为公开事实。
- 决策：公开 VKP 回执只保存维度、数量、模型/运行时绑定和向量文件哈希，不内嵌向量；输入仅允许 `synthetic_fixture` 或 `public_fixture`。
- 理由：embedding 是候选索引证据，不应覆盖 VKP 真源，也不应扩大资料处理边界。
- 证据：验证器拒绝内嵌向量、输入哈希漂移、维度漂移、自动 fallback 和不匹配的 Owner receipt。
- 生效范围：`video_knowledge_pipeline.embedding_candidate_receipt.v1`；真实模型文件、向量文件与执行目录继续留在 `.local`/外部运行目录。
- 回滚：停止调用 `run_embedding_candidate`；不会删除或迁移任何既有索引。

## 未越过的运行门

1. 仓库回归只验证合成 Owner execution 合同；没有读取真实 Key、调用云 Provider 或上传资料。
2. 真实本地 smoke 只有在显式提供 `MPG_EMBEDDING_PYTHON` 与 `MPG_EMBEDDING_MODEL_PATH` 时运行，否则测试按设计 skip。
3. 本适配器不宣称 Recall@5/10、跨平台模型可用性或生产检索质量已经通过。
