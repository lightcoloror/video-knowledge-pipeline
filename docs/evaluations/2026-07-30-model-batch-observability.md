# 在线模型批次延迟与流量可观察性

- 更新时间：2026-07-30 20:48:00
- 执行工具 / 模型：Codex（GPT-5.6）
- 状态：批次持久化回执已补强，heartbeat 仍待实现

## 变更依据

- 意图：区分“慢但最终完成”“速率限制失败”“服务端瞬时失败”和“运行进程失联”，同时量化每批输入流量。
- 决策：复用既有 `compact_model_execution_receipt`、LiteLLM 限流和 consent batch DAG；批次层只聚合已经脱敏的延迟、loopback gateway 字节和 source artifact 字节，不新建 telemetry 数据库或第二套限流器。
- 理由：模型运行客户端已经记录每次请求/响应大小，Broker 已提供脱敏紧凑回执。旧批次状态没有保存这些字段，也没有 p50/p95，因此 Task Console 无法判断任务究竟是慢、拥塞还是输入过大。
- 证据：新增 focused 回归并与现有批次、内存边界测试一起运行，结果 `16 passed`；Ruff 与 compileall 通过。
- 生效范围：受 consent 保护的后台模型批次状态；不记录提示正文、模型正文、API Key 或精确 provider wire bytes，不增加重试、fallback 或外发范围。

## 新增批次证据

- 每个 item：
  - `latency_ms`
  - `network_accounting`
  - `usage`
  - `cost_control`
- 批次 summary：
  - `latency_sample_count`
  - `latency_p50_ms`
  - `latency_p95_ms`
  - `gateway_request_bytes`
  - `gateway_response_bytes`
  - `source_artifact_bytes`

上述网络字节范围是 VKP 到本地 loopback gateway 的可核验 payload，不冒充 TLS/HTTP2 后真实 provider wire bytes。

## 验证

```powershell
$env:PYTHONPATH='src'
python -m pytest -q -p no:cacheprovider `
  tests\test_consented_model_batch_observability.py `
  tests\test_consented_model_batch.py `
  tests\test_consented_model_batch_memory.py `
  --basetemp C:\tmp\vkp-model-batch-observability-20260730
```

结果：`16 passed in 1.40s`。

## 剩余缺口

1. 长时间单次模型调用期间还没有周期 heartbeat；当前只有 item 开始、完成和终态更新时间。
2. 设置 UI 还应显示容量预算是否完整、p50/p95、429 和批次字节汇总。
3. token 是否可得取决于供应商响应；缺失时必须显示 `unknown`，不能估算成精确费用。
