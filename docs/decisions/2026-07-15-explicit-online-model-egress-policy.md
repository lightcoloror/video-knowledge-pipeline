# ADR 补充：在线模型外发默认拒绝与显式授权

- 状态：Accepted
- 决策时间：2026-07-15 12:07:19 +08:00
- 执行者：Codex / GPT-5
- 适用范围：VKP 文本、视觉、ASR、在线 OCR 的远程模型调用与逐文件上传

## 决策

VKP 默认不向任何在线模型外发本地文件。只有以下条件全部成立时，Trusted Capability Broker 才允许执行远程模型任务：

1. 任务显式选择 `remote` 路线，且 route id、route revision、virtual model、全部候选 deployment 与目的地均已锁定；
2. 使用 `video_knowledge_pipeline.model_connector_consent.v2`，旧 v1 只保留状态读取兼容，不允许新的远程执行；
3. 操作者在可见 shell 中明确确认数据外发，确认记录绑定上传清单 SHA-256；
4. consent 同时声明最大调用次数、总费用授权上限和单次费用上限；
5. `upload_manifest` 逐文件列出绝对路径、数据类型、字节数和 SHA-256，执行器不得读取或上传清单外文件；
6. 全部 deployment 同时通过 Broker 目的地 allowlist；Agent 平台仍可进一步拒绝外发。

任一条件缺失、过期、篡改或额度不足时，必须在联网前失败关闭。

## 费用控制语义

- 调用次数和费用额度在 provider 调用前使用同一 consent 文件锁原子 reservation；
- 已知费用响应按实际 `estimated_cost` 核销并释放未使用的预留额度；
- provider 未返回费用时，按操作者批准的单次费用上限保守计入，不假定为零；
- provider 返回费用超过预留时，结果标记 `cost_limit_exceeded_after_response`，不得作为成功产物提升，后续调用继续阻断；
- consent 费用上限是 VKP 的授权与审计硬门，不等同于供应商账单保证；需要绝对账单封顶时，还必须在 LiteLLM/provider 账户侧配置预算限制。

## 永久禁止项

- 自动发送、发布或同步模型结果；
- 上传 `upload_manifest` 未列明的文件；
- 本地池失败后静默切换远程池，或远程池失败后静默切换本地池；
- Agent/MCP 参数提交任意 provider URL、API Key、Bearer Token 或未审查目的地；
- 通过 Secure MCP Tunnel、HTTP bridge 或其他代理绕过平台外发策略。

## 真源与写回

Timeline、Bundle 和 run registry 继续是 VKP 任务与证据真源。远程模型输出仅作为候选 evidence 写回既有 schema；Broker、LiteLLM 或外部供应商都不得另建业务状态真源。

## 代码映射

- `model_connector_consent.py`：consent v2、上传清单、操作者确认、调用/费用 reservation 与核销；
- `trusted_model_connector_policy.py`：执行前 v2 合同、路径根和目的地 allowlist；
- `trusted_model_connector.py`：只读取 consent 清单、费用结果审计和默认拒绝边界；
- `trusted_model_connector_remote_mcp.py`：Secure MCP Tunnel 的受限远程执行入口。

## 验收

- 缺少总费用上限时不能创建已确认 consent；
- 上传清单、操作者确认、route revision、文件 SHA-256 或目的地任一不匹配时零网络请求；
- 调用次数仍有余额但费用额度不足时，reservation 必须失败；
- 未报告费用按单次上限保守占用；
- local-only 故障继续报告零远程请求；
- 自动发布、未列明上传和静默 local/cloud fallback 始终为 false。

## Update Record

### 2026-07-15 12:07:19 | Codex / GPT-5

- Action：把 VKP 在线模型边界从笼统的禁止外发改为默认拒绝、显式受控授权。
- Boundary：本次只修改与验证本地代码；未调用真实外部模型、未上传文件、未发布、未 push。
