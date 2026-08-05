# 模型网关容量预算诊断

- 更新时间：2026-07-30 21:10:00
- 执行工具 / 模型：Codex（GPT-5.6）
- 状态：诊断已实现，供应商实际容量值仍待配置

## 变更说明

- 意图：在批量任务启动前显式发现未配置的并发、RPM 与 TPM 预算，避免只有撞到 429、超时或队列堆积后才知道路线没有容量约束。
- 决策：直接复用 LiteLLM 已有的 `rpm`、`tpm`、`max_parallel_requests` 与 cooldown 能力；VKP 只增加机器可读诊断，不另建一套限流器。
- 理由：LiteLLM 已经负责真实运行时限流与冷却。重复实现会造成双重状态和不一致；但缺少配置时，旧回执无法区分“有意无限制”和“尚未配置”。
- 证据：只读审计当前 `.local/model-api-settings.json`，31 个已配置 profile 均未设置 `rpm`、`tpm`、`max_parallel_requests`。新增回归与既有网关测试合计 `20 passed`。
- 生效范围：`model-gateway render-config/doctor` 返回的诊断字段；不修改用户设置、不猜测供应商额度、不联网、不改变 `ready_for_start`、路由或 fallback。

## 新增回执字段

- `capacity_policy_ready`：所有被渲染 deployment 是否都具备三项容量预算。
- `capacity_warnings[]`：逐 deployment 返回 profile、route、能力、执行位置、缺失字段和建议动作。

缺少容量预算目前是警告而不是启动阻断。这样保留旧配置兼容性，同时让 Task Console、设置 UI 和自动批处理可以明确显示“网关可启动，但容量策略未完成”。

## 验证

```powershell
$env:PYTHONPATH='src'
python -m pytest -q -p no:cacheprovider `
  tests\test_model_gateway_capacity_diagnostics.py `
  tests\test_model_gateway.py `
  --basetemp C:\tmp\vkp-model-gateway-capacity-20260730
```

结果：`20 passed in 10.65s`。

## 剩余工作

1. 设置 UI 显示三项容量字段、来源和最后核验时间。
2. 由供应商官方控制台或文档填写真实额度；不得由 VKP 猜测。
3. 执行回执继续记录实际并发、RPM/TPM、429、p50/p95、重试、流量、token 与费用，校验配置是否符合真实表现。
4. 对没有公开 TPM/RPM 的供应商，允许显式标为 `unknown` 并使用人工设定的保守并发值，但不能静默视为生产就绪。
