---
title: VKP 在线模型异步并行与限流设计
date: 2026-07-21
status: implemented-phase-3-offline
tags:
  - VKP
  - model-gateway
  - concurrency
  - rate-limit
  - consent-v2
updated_by: Codex / GPT-5.6
updated_at: 2026-07-21 22:28:57
---

# VKP 在线模型异步并行与限流设计

## 结论

VKP 分析速度慢并不主要是 Python 或视频编解码本身的硬限制。改造前的主要瓶颈是：长耗时模型调用被包装成同步 MCP 工具、同一 Broker 请求路径近似串行、OCR/视觉等互不依赖阶段没有形成受控 DAG，以及 Provider 配额没有进入统一网关。Phase 2 已用 LiteLLM Router、标准库 DAG 和持久批次状态补齐这些控制面；Phase 3 又把命名生产节点、现有 Bundle/run registry 和 Task Console 接入同一执行器，没有新增工作流状态机。

生产改造采用以下策略：

1. 长任务改为 `submit -> job_id -> status/poll -> terminal artifact`，避免 MCP/Agent 长连接超时造成“上游已执行、调用方却认为失败”的歧义。
2. 批次层仅用静态全局/单目的地硬上限保护 Broker；Provider 的 RPM、TPM、单 deployment 并发、预调用检查和冷却直接交给已采用的 LiteLLM Router 1.81.7，不再维护 VKP 自研 AIMD。
3. 429、5xx、连接中断和超时由批次层分类、持久化并显示，但批次层不自行重试、降档或跨目的地 fallback；LiteLLM 只执行 route revision 中已授权的同池策略。
4. 每个批次必须先验证 consent v2、精确 artifact manifest、route revision、目的地 allowlist、调用次数与费用上限；批次层不能接收任意 Provider URL、API Key 或模型覆盖参数。
5. 本地池与远程池不自动 fallback；跨远程目的地也不能静默 fallback。
6. 所有进度在每个状态变化后原子写入本地 JSON；Broker 重启后不自动重放状态不明的请求，而是标记 `interrupted` 并要求显式处理。
7. 批次汇总只保存状态、时延、错误摘要和执行报告路径，不复制模型正文、图片编码、音频或密钥。

## 证据与瓶颈判断

2026-07-21 的既有真实链路记录显示：

- Groq 完整 ASR 可在约 7 秒完成，说明网络和 Broker 并非所有阶段的主瓶颈。
- Mistral OCR 的 6 个请求顺序执行，总模型时延约 10.4 秒；其中 5 成功、1 次服务器断连。
- 两个 SiliconFlow 视觉请求由调用方并发提交，但模型时延约 61.0 秒和 41.9 秒，墙钟约 109.4 秒，接近两者之和，说明当前同步 Broker/MCP 路径实际近似串行。
- 曾出现 MCP 传输层先报失败、OCR 执行报告却已完整落盘的情况，说明长同步工具会制造不确定终态。

因此优先收益不是无限增加线程，而是先把执行协议改成异步、可轮询、可恢复，再在目的地和任务层做有界并发。

## 并发上限由什么决定

有效并发是以下上限的最小值：

```text
min(
  Broker 全局静态硬上限,
  Broker 单目的地静态硬上限,
  用户提交的批次上限,
  consent 剩余调用与费用上限,
  LiteLLM deployment max_parallel_requests,
  LiteLLM pre-call RPM/TPM 检查与 Provider 实际限制,
  本机网络连接与内存上限
)
```

Broker 端默认硬上限：

- Broker 全局远程并发：4。
- 单目的地最大并发：2。
- 批次层新增重试：0。
- 批次层新增 fallback：否。

调用方只能请求更低的批次并发，不能通过 MCP 参数提高 Broker 硬上限。可通过受控环境变量调整：

- `VKP_MODEL_BATCH_GLOBAL_CONCURRENCY`
- `VKP_MODEL_BATCH_MAX_DESTINATION_CONCURRENCY`

每个 profile 可选登记 `rpm`、`tpm`、`max_parallel_requests`。这些字段直接渲染到 LiteLLM deployment；留空表示不猜测供应商额度。`cooldown_time` 与 `enable_pre_call_checks: true` 也由现有 LiteLLM 配置生成器管理。任一字段改变都会改变 route revision，旧 consent 不能继续匹配。

## 已实施接口

新增 MCP 工具：

- `submit_consented_model_batch_tool`
  - 输入：`consent_paths[]`、`write`、不高于 Broker 限制的全局/单目的地并发请求，以及可选的 `depends_on[]` 索引图。
  - 输出：`job_id`、`status_path`、初始汇总。
  - 不接受 Provider 配置、URL、密钥或 route revision 覆盖。
  - DAG 校验和就绪节点调度复用 Python 标准库 `graphlib.TopologicalSorter`；并行 worker 复用 `concurrent.futures.ThreadPoolExecutor`。
- `consented_model_batch_status_tool`
  - 只读返回持久进度、逐项结果、目的地控制器状态和终态。
- `submit_consented_model_workflow_tool`
  - 输入：现有 Bundle 路径和命名节点 `[{id, consent_path, depends_on[]}]`。
  - 只把命名依赖转换为通用批次执行器已有的索引 DAG；不实现第二套 scheduler、状态机或 Provider 客户端。
  - 节点绑定到 Bundle 后，状态自动登记到现有 `run-artifact-registry.json`；Task Console 读取同一个持久批次摘要。
  - 只允许已经存在、已经逐文件授权的 consent。若下游输入包必须由上游结果生成，应先完成上游批次、在本地生成新输入包，再单独创建/确认下游 consent；此人工授权屏障不能被 DAG 自动跨越。


设置 UI 新增只读批次监控：

- `/api/model-batches` 只返回 job、任务名、目的地、计数、时序和 LiteLLM 限流归属；不返回 consent path、输入正文、artifact 内容或密钥。
- 显示 queued/running/completed/failed、429、5xx/超时、dependency blocked。
- Provider profile 可显式保存 RPM、TPM 和单 deployment 最大并发。

持久产物：

```text
.local/model-connector-batches/<job_id>/batch-execution.json
```

产物 Schema：`video_knowledge_pipeline.consented_model_batch.v1`。

终态规则：

- 全部成功：`completed`
- 部分成功：`degraded`
- 全部失败：`failed`
- Broker 重启且存在状态不明项：`interrupted`，不自动重放

## Phase 3：生产薄适配与现有 UI 复用

- 批次节点现在有稳定 `node_id`，生产调用方可用 `ocr-0001`、`semantic-frame-0001`、`temporal-0001`、`summary-section-01` 等名称表达真实依赖，不再要求人工维护不可读的裸索引。
- 命名图仍由 `TopologicalSorter` 做循环校验和 ready-node 释放；`submit_workflow()` 只是 ID→索引转换胶水。
- Bundle 绑定要求现有 `manifest.json` 与 `timeline.json`，并复用 `register_bundle_run()` 写入已有 run registry。模型输入、consent path 和密钥不会复制进 registry。
- `task-console.json/html` 复用脱敏 `list_consented_model_batches()`，按 Bundle 过滤并显示节点、目的地、成功/失败/依赖阻断、当前剩余调用、剩余费用上限和最早到期时间。
- Consent 余额从本地 consent 的 `scope/usage` 读取，只返回汇总；不返回 consent path、artifact 内容、模型正文或凭据。
- 第一阶段原自研 AIMD 已在 Phase 2 删除；本阶段没有引入 Celery、RQ、Activepieces runtime 或新的监控服务。VKP 特有代码只保留 consent、精确哈希、Bundle 绑定和审计胶水。

### 第一阶段复用审计

- Provider 的 RPM、TPM、并发、预调用检查与 cooldown：直接复用 LiteLLM Router 1.81.7；VKP 不实现令牌桶、AIMD 或动态降档算法。
- DAG 循环校验和 ready-node 释放：直接复用 Python `graphlib.TopologicalSorter`。
- worker、完成等待与静态硬门：直接复用 `concurrent.futures` 和 `threading.BoundedSemaphore`；硬门只允许调用方降低并发，不能超过 Broker 上限。
- 状态写入与恢复：复用 VKP 既有 `storage.read_json/write_json`、Bundle `register_bundle_run()` 和 Task Console，不创建第二套数据库、队列或监控服务。
- 真正执行：继续委托现有 `execute_consented_model_task()`，由 consent v2、route revision、逐文件哈希和原子 calls/cost reservation 约束。
- 审计扫描未发现运行时代码残留自研 AIMD、token bucket、leaky bucket 或 adaptive-concurrency 控制器。


## 安全与兼容性

- 执行仍委托现有 `execute_consented_model_task()`；consent 的原子 calls/cost reservation 没有复制或旁路。
- 批次幂等键绑定 consent ID、精确上传清单哈希、route revision、路径和 write 模式，不使用会随调用次数变化的 consent 文件整体哈希。
- 单个 consent 必须锁定一个远程目的地；同一目的地下可有多个已授权 deployment，但首版不接受跨目的地 fallback 路线进行并行调度。
- 现有同步 `execute_consented_model_task_tool` 保留，旧调用方不受影响。
- 既有特殊 provider parity 后台队列暂不删除；后续可在真实回归后迁移到通用批次管理器。

## 验证

离线验证不调用真实 API，也不上传任何文件：

- Focused 回归：`64 passed in 18.11s`。
- 最终 focused 重跑：`64 passed in 17.20s`；批次文件锁专项：`15 passed in 1.08s`。
- 完整离线回归：`1027 passed, 2 failed, 1 warning in 266.88s`。两项失败均来自未纳入本 checkpoint 的 `vision_review_triage.py` 并行改动及其旧 fixture：新实现要求 frame path 指向真实文件，旧测试只写了不存在的相对路径。本轮批次、网关、路由、UI 测试在完整套件中均通过。
- 跨目的地并行、单目的地硬上限、幂等不重放、429 无重试/无 fallback 均通过。
- DAG 循环在调用前拒绝；上游失败只阻断后代，独立分支继续。
- LiteLLM YAML 已验证包含 `rpm`、`tpm`、`max_parallel_requests`、`cooldown_time`、`enable_pre_call_checks: true` 和 `num_retries: 0`。
- 配额变化刷新 route revision 的测试通过。
- 设置 HTTP/UI 与脱敏批次列表测试通过；fixture 中伪造的 consent 路径和模型输入未出现在响应。
- Phase 3 focused 回归：`61 passed in 21.46s`；覆盖命名生产 DAG、未知依赖前置拒绝、Bundle run registry、Task Console 脱敏余额、MCP schema 和原有批次/设置 UI。
- 最终扩展 focused 回归：`79 passed in 23.74s`；覆盖批次、内存恢复、命名 workflow、MCP、LiteLLM 配置、设置 UI 和 Task Console。
- 全量套件原样运行：`1032 passed, 2 failed, 1 warning in 260.60s`；两项失败均属于并发脏工作树中的既知视觉门控 fixture，不涉及本 checkpoint。
- 精确 deselect 上述两项既知失败后重跑：`1032 passed, 2 deselected, 1 warning in 238.23s`；本轮复用改造无新增失败。
- 首次测试因 Windows 受限临时目录权限产生 fixture setup error；改用项目 `.local` 并以获准的操作者权限重跑后全部通过，这不是业务测试失败。

## 后续阶段

1. 复用 LiteLLM callback/response-header cooldown 能力补充实时剩余时间估计；不在 VKP 内再造令牌桶或 AIMD。
2. 完整 `pytest` 连续两次通过后，再选择一组已授权小样本做 1/2/4 并发阶梯测量；真实 API 测量必须另获精确授权。
3. 真实测量稳定后，评估把旧 provider parity 专用后台队列迁移到通用批次管理器，避免长期维护两套状态机。

## 更新记录

- 2026-07-21 19:45:33 — Codex GPT-5：记录结论并实施第一阶段异步批次、目的地并发控制、降档/冷却、幂等与持久进度。
- 2026-07-21 20:53:27 — Codex / GPT-5.6：按复用优先决策删除批次层自研 AIMD；Provider 限流改由 LiteLLM 1.81.7 Router 的 RPM/TPM/并发/预检查/冷却承担；DAG 改用 Python `graphlib.TopologicalSorter`，并接入脱敏设置 UI。
- 2026-07-21 22:03:35 — Codex / GPT-5.6：将生产命名节点薄适配到同一 DAG，复用现有 run registry 与 Task Console 展示 Bundle 绑定批次和 consent 剩余额度；未新增工作流运行时。
- 2026-07-21 22:28:57 — Codex / GPT-5.6：完成第一阶段残留自研扫描，确认限流、DAG、worker、持久状态和操作界面均落在成熟组件或既有 VKP 真源上；完成无新增失败的全量离线回归。
