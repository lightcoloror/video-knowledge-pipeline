# VKP 统一多模型网关薄适配记录

更新时间：2026-08-05 17:40:00 +08:00
执行者：Codex / GPT-5.6

## 结论

VKP 保留现有 Timeline、Bundle、Provider Catalog、DPAPI secret store、route revision、consent v2、Broker reservation 和执行审计真源。独立共享项目 `model-provider-gateway` 只承接审核 preset、跨平台 secret 引用、显式 route/consent plan、doctor/audit 和消费者合同。VKP 通过可选薄适配器导出配置投影，不复制第二套状态机，也不改变当前生产调用路径。

公开上游：<https://github.com/lightcoloror/model-provider-gateway>
固定提交：`24d6aafca23c4fa836f25ce19d3a5d428d962354`
许可证：`AGPL-3.0-only`

## MPG-VKP-001：可选依赖锁定

- 意图：让 VKP 能显式安装共享网关，而不改变 core/online/local/hybrid 的既有依赖。
- 决策：新增 `shared_gateway` optional extra，锁定公开仓库精确 commit。
- 理由：浮动分支会让 preset、route revision 与 consent 语义在未审核时漂移。
- 证据：共享项目 33/33 双跑、LiteLLM loopback mock parity、Gitleaks/path scan 和 GitHub PUBLIC/AGPL 回读通过。
- 生效范围：仅执行 `pip install -e .[shared_gateway]` 的环境；默认 VKP 安装不变。
- 回滚：删除该 optional extra；VKP 原有网关继续工作。

## MPG-VKP-002：精确 profile 投影

- 意图：复用共享 preset，而不让 OpenAI-compatible 变成任意目的地入口。
- 决策：只在 VKP profile 的 Provider、Base URL、模型、能力和 provider options 与唯一审核 preset 全部精确匹配时导出；legacy、本地、任意 URL、未知模型和 option drift 全部阻断。
- 理由：Provider 名称相同不代表端点、协议、模型或数据边界相同。
- 证据：`tests/test_model_provider_gateway_adapter.py` 覆盖 Gemini 正向、未知模型、任意 URL、legacy、本地和 option drift。
- 生效范围：`model_provider_gateway_adapter.vkp_profile_to_shared`；不读取 DPAPI secret，只保留 `auth_ref`。
- 回滚：停止调用薄适配器；不迁移或删除任何 VKP profile/secret。

## MPG-VKP-003：显式 route 与 fallback

- 意图：让共享消费者获得内容寻址路线，同时保留 VKP 原 route identity。
- 决策：共享 route 在 provenance 中绑定 VKP profile SHA、route id/revision；多 deployment 必须显式 `fallback_enabled=True`，并继续标记 `requires_consent=true`。
- 理由：共享 route revision 与 VKP route revision 的 Schema 不同，必须双向留痕；不能假装二者哈希相等。
- 证据：正向测试验证两次导出 revision 稳定；多 deployment 未显式 fallback 时 fail-closed。
- 生效范围：配置投影和 adapter contract；不执行 provider 调用、不创建 VKP consent、不预留额度。
- 回滚：删除派生投影即可；VKP route、consent 和 Bundle 不受影响。

## 迁移顺序

1. QRP/ARW 先消费只读 `text` adapter contract。
2. Content Studio 再消费 `draft/rewrite`，业务草稿仍由其自身持有。
3. MVP 依次接 `text → vision → tts/asr`，上传仍由其 owner 生成 manifest。
4. VKP 最后选择性把新 profile 的控制面投影到共享包；现有生产执行仍走 VKP Broker/consent。

任何消费者都不得提交 provider URL、API Key 或 headers；新增 Provider、模型、目的地、fallback 成员或限额后必须生成新 route revision 与 consent。
