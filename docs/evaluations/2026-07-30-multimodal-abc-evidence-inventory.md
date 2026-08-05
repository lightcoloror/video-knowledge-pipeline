# VKP 多模态 A/B/C 固定样本证据盘点

- 记录时间：2026-07-30 21:20:00（Asia/Shanghai）
- 执行工具/模型：Codex / GPT-5
- 样本：`temporal-6x8-fixed-20260719`
- 本轮边界：仅整理既有本地执行证据；没有调用模型、上传文件或修改生产路由。

## 意图

确认三条视觉路线是否已经在同一组 6×8 temporal 帧样本上完成可比测试，避免把不同样本或不同任务的本地运行误记为 Lane C。

## 决策

- Lane A（VKP legacy 视觉适配器）：已捕获。
- Lane B（LiteLLM Proxy 远程池）：已捕获。
- Lane C（本地 OpenAI-compatible 多模态）：未捕获。
- 当前 A/B/C 比较状态必须保持 `incomplete`；在 Lane C 使用同一 48 帧、同一任务和同一评分规则完成前，不得宣称三路线质量比较已闭环。

## 理由

现有本地 Qwen3-VL 记录使用了其他 temporal 样本，不能与 A/B 的固定样本直接比较。替换样本会同时改变画面难度、OCR 密度和时序变化，导致质量、延迟和失败恢复结论失真。

## 证据

- Lane A：`.local/model-gateway-abc-20260730/lane-a-legacy.json`
  - `ok=true`
  - `status=completed`
  - `call_count=6`
  - `evidence_count=6`
  - `quality_gate=pending_human_review`
- Lane B：`.local/model-gateway-abc-20260730/lane-b-proxy-remote.json`
  - `ok=true`
  - `status=completed`
  - `call_count=6`
  - `evidence_count=6`
  - `latency_ms=58056`
  - `quality_gate=pending_human_review`
- Lane C：`.local/model-gateway-abc-20260730/lane-c-proxy-local.json`
  - 文件不存在。
  - 2026-07-30 核对时 LM Studio 的 `127.0.0.1:1234` 未监听，因此没有启动或伪造本地执行。
- 离线比较：
  - `.local/model-gateway-abc-20260730/model-gateway-abc-comparison.json`
  - `status=incomplete`
  - `schema_compatible=false`，原因仅为 Lane C 缺失。

## 生效范围

本记录只约束 `temporal-6x8-fixed-20260719` 固定样本的 A/B/C 验收结论，不否定其他样本上的本地 Qwen3-VL 成功记录，也不改变任何模型路由、consent 或生产默认值。

## 剩余验收门

1. 操作者启动 LM Studio，并加载支持多图的本地视觉模型。
2. 使用同一 48 帧和同一 temporal 提示运行 Lane C；不得使用在线 fallback。
3. 捕获 `lane-c-proxy-local.json`。
4. 对 A/B/C 做匿名人工评分，至少包含 OCR/画面事实、帧间变化、结构化输出、幻觉、延迟和人工修正成本。
5. 重新运行离线 `compare`，只有三条 lane 均加载且 schema 合法时才能转为完整比较。
