# VKP 统一多模型网关薄适配记录

更新时间：2026-08-05 23:10:00 +08:00
执行者：Codex / GPT-5.6

## 结论

VKP 保留 Timeline、Bundle、Provider Catalog、DPAPI secret store、route revision、business authorization、consent v2、Broker reservation 和执行审计真源。独立共享项目 `model-provider-gateway` 提供审核 preset、跨平台 secret 引用、显式 route/consent、canonical text/vision execution request/result 和原子 ledger。VKP 的薄适配器只投影配置并在已有 Broker reservation 之后生成 canonical request，不直接解析 secret、不直接执行 Provider，也不创建第二套业务授权。

公开上游：<https://github.com/lightcoloror/model-provider-gateway>
固定执行层提交：`c5f3ec49644453e0cddb56350e3b243b49e0f7da`
许可证：`AGPL-3.0-only`

## MPG-VKP-001：可选依赖锁定

- 意图：让 VKP 显式消费共享执行合同，而不改变 core/online/local/hybrid 的默认依赖。
- 决策：`shared_gateway` optional extra 锁定公开仓库精确提交。
- 理由：浮动分支会让 preset、route revision、consent 和执行 Schema 未经审核漂移。
- 证据：共享项目最终 53/53 双跑、LiteLLM text/vision loopback roundtrip、build 和脱敏扫描通过。
- 生效范围：仅执行 `pip install -e .[shared_gateway]` 的环境；默认 VKP 安装不变。
- 回滚：移除 optional extra 或改回已审核旧提交；VKP 原网关继续工作。

## MPG-VKP-002：精确 profile 与 route 投影

- 意图：复用共享 preset，而不把 OpenAI-compatible 变成任意目的地入口。
- 决策：Provider、Base URL、模型、能力和 provider options 必须与唯一审核 preset 完全匹配；legacy、本地、任意 URL、未知模型和 option drift 全部阻断。多 deployment 仍要求显式 fallback scope。
- 理由：协议兼容不等于目的地和数据边界获批。
- 证据：focused tests 覆盖 Gemini 正向、未知模型、任意 URL、legacy、本地、option drift 和未显式 fallback。
- 生效范围：`vkp_profile_to_shared`、`vkp_route_to_shared`；只保留 `auth_ref`，不读取 DPAPI 值。
- 回滚：停止生成共享投影；不迁移或删除任何 VKP profile、route 或 secret。

## MPG-VKP-003：Broker owner gate

- 意图：共享 canonical executor 不能绕过 VKP 已有生产控制面。
- 决策：新增 `vkp_execution_request_to_shared`，只接受已有投影、exact consent 和 64 位 Broker reservation receipt hash；多成员 route 必须显式选择 profile。函数只生成 `execution_request.v1`，不执行 transport。
- 理由：共享包可以统一协议与回执，但只有 VKP 知道 business authorization、Bundle lineage 和 Broker reservation 是否成立。
- 证据：10/10 focused adapter tests；正向请求保留 provider/model/route/consent/input hash 和 owner receipt，缺 receipt 在执行前 fail-closed。
- 生效范围：VKP text/vision 的未来薄适配入口；ASR/OCR 仍由 VKP 生产网关持有并在共享 Wave 1 中 blocked。
- 回滚：停止调用该函数，继续使用 VKP 现有 Broker/runtime client；已有 Bundle 和 consent 不变。

## MPG-VKP-004：无直接 Provider SDK

- 意图：防止消费者在接入共享包后新增平行 Provider SDK 或静默 fallback。
- 决策：VKP 适配器不调用 `execute_model_request`，不解析 env/keyring/DPAPI，不接受任意 URL/header/raw JSON；实际执行仍必须在 VKP Broker reservation 内由 owner 选择。
- 理由：共享执行 API 是协议前门，不是业务授权替代品。
- 证据：适配器返回 canonical request 时 `provider_execution_performed=false`；shared adapter v2 把 VKP text/visual 标记为 `control_policy=vkp_broker`，ASR/OCR 标记 blocked。
- 生效范围：共享 Wave 1；不改变当前生产路线，也不自动迁移旧 profile。
- 回滚：移除薄适配器可选入口；VKP 原调用链保持原样。

## 消费者迁移顺序

1. 先安装固定 `shared_gateway` extra 并读取 adapter v2。
2. VKP 仍先完成 business authorization、consent 与 Broker reservation。
3. 只对 exact profile/route 生成共享投影；多成员 route 显式选定单一 deployment。
4. 使用 `vkp_execution_request_to_shared` 生成 canonical request；不得从调用方提交 URL、Key、headers 或 fallback。
5. owner 执行器消费 result receipt；Timeline、Bundle、逐字稿和审核状态仍由 VKP 管理。

本轮未调用真实 Provider、未读取 Key、未上传文件、未启动长期服务。
