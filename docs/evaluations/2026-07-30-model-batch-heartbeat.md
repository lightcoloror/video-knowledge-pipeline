# VKP 在线模型批处理 heartbeat 补强

- 记录时间：2026-07-30 21:35:00（Asia/Shanghai）
- 执行工具/模型：Codex / GPT-5
- 外部调用：0

## 意图

区分“模型调用耗时较长但仍正常运行”和“执行器或进程已经失去进展”，避免只依赖最终超时或用户观察终端输出。

## 决策

直接扩展既有 `consented_model_batch` 持久化状态，不建立第二套监控服务：

- 每个运行项记录 `heartbeat_at`、`heartbeat_at_unix_ms`、`heartbeat_count` 和 `heartbeat_state`。
- 默认每 15 秒刷新一次。
- 超过三个 heartbeat 周期没有更新才标记为 stale。
- 批处理摘要公开 `heartbeat_alive` 与 `heartbeat_stale`。
- 完成、失败或进程中断时停止 heartbeat，并写明终止状态。
- heartbeat 不触发重试、fallback 或模型调用，也不复制模型正文。

## 理由

现有批处理已经是执行状态和审计真源。把 heartbeat 写入同一个原子 JSON artifact，能够复用 Task Console、Broker 状态查询和 run registry；另建后台监控服务会引入第二状态机和更多恢复问题。

阈值采用“间隔 × 3”，避免一次磁盘抖动、GC 或线程调度延迟把慢调用误判为卡死。默认 15 秒只是本地观测频率，不改变供应商超时。

## 证据

- 实现：`src/video_knowledge_pipeline/consented_model_batch.py`
- 回归：`tests/test_consented_model_batch_heartbeat.py`
- 关联回归：
  - `tests/test_consented_model_batch.py`
  - `tests/test_consented_model_batch_observability.py`
- 定向及关联回归结果：`39 passed, 1 warning`
- 兼容性回归证明旧批处理归档中的 `rate_limited` 等历史汇总不会因 heartbeat 动态计算而丢失。
- Ruff：`All checks passed`
- `compileall` 在 60 秒内因当前磁盘读取延迟超时；上述 pytest 已实际导入并执行修改后的模块，因此没有语法导入错误。

## 生效范围

只影响 VKP consent-locked 在线模型批处理的状态记录与只读状态查询。不会改变：

- provider 路由；
- consent/reservation；
- LiteLLM 的 RPM、TPM 或并发限制；
- 调用次数和费用；
- 自动重试/fallback 策略；
- Timeline、Bundle、逐字稿或 Smart Summary 内容。

## Task Console

现有 Task Console 已显示：

- 正在运行且 heartbeat 正常的数量；
- heartbeat 已过期、需检查执行器的数量；
- P50/P95 延迟；
- 网关请求/响应字节。

对应回归：`tests/test_task_console_model_batch_observability.py`，与工作流关联测试合计 `5 passed`。

仍待后续明细视图显示每个 item 的最近 heartbeat 时间与累计次数；底层 status artifact 已具备这些字段。
