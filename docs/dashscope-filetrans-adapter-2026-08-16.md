# DashScope FileTrans 固定上游适配与授权闭环

> 更新：2026-08-16 17:20:00 +08:00
> 执行工具/模型：Codex (GPT-5.6 Sol)

## 结论

VKP 不复制 DashScope 上传、异步任务轮询或 `.mosp` 转换代码。远程 ASR 候选路线直接调用本地固定的 `moys-asr-workflow` CLI，并在子进程启动前消费 VKP 已验证的 Broker runtime grant。没有匹配的 consent reservation、route revision 或剩余额度时，执行 fail-closed，且不读取音频、不启动上游 CLI、不发起网络请求。

当前状态是 `contract_ready / offline_tested / real_provider_not_executed / registration_pending`。它不能因为本地测试通过就覆盖 canonical transcript，也不构成对真实粤语质量的证明。

## 固定上游

- 项目：`Moyf/moys-asr-workflow`
- 本地源码账本：`moys-asr-workflow`
- 固定 commit：`949bc84058cdae1d9c021c50203e6d2742f9392c`
- 复用入口：`generate_subtitle_qwen_api.py`
- 复用范围：临时 OSS 上传、FileTrans 提交/轮询、Qwen Audio/FunASR 结果转换、字词时间戳及说话人字段。
- 拒绝复制：Provider REST、上传器、轮询器、GUI Key 配置和独立状态机。

## 变更理由

### 1. Broker runtime grant 硬门

- 意图：让“已完成 consent reservation”从注释假设变成可测试的执行条件。
- 决策：adapter 消费既有 `consent_id + route_revision + remaining_calls` grant；不创建第二套授权记录。
- 理由：DashScope FileTrans 会上传完整音频，风险高于本地计划和预览。
- 证据：无 grant 与额度耗尽测试均返回 `consent_required`，fake runner 调用次数为零。
- 生效范围：DashScope FileTrans 子进程执行前门。
- 回滚：移除该 adapter 路线；不放宽为直接远程调用。

### 2. 固定上游 CLI 薄适配

- 意图：复用上游已验证的异步 FileTrans 实现。
- 决策：只构造命令、隔离环境变量、读取 `.mosp` 并归一化为 VKP ASR response；API Key 不进入 argv、日志或产物。
- 理由：上游已覆盖上传凭据、地域、workspace、轮询和输出结构；重复实现会造成协议漂移。
- 证据：上游相关测试 `56 passed`；VKP fake-run 验证命令无 Key、环境中临时注入、结果段落/说话人保留。
- 生效范围：`qwen-audio-3.0-asr-flash-filetrans`、`qwen3-asr-flash-filetrans` 和 `fun-asr` 固定模型集合。
- 回滚：删除 provider preset 与 CLI adapter，不影响其他 ASR。

### 3. 明确请求与错误合同

- 意图：避免把异步 FileTrans 误报为 OpenAI `/audio/transcriptions`。
- 决策：预览显示 `dashscope_async_filetrans / moys_asr_workflow_fixed_cli`；错误区分 consent、Key、上游源码、timeout、Provider 失败和输出缺失；永久禁止自动 fallback。
- 理由：接口、费用和数据上传边界不同，不能用 OpenAI-compatible 名义掩盖。
- 证据：online gateway preview、timeout 和输出归一化回归。
- 生效范围：CLI/MCP 机器可读请求计划与执行回执。
- 回滚：停止公开该候选路线，不映射为其他 Provider。

## 验证

- 上游：`56 passed`。
- VKP adapter + online gateway + trusted connector：`35 passed`。
- Ruff：新增/修改文件通过。
- 真实 Provider 调用：`0`。
- 真实音频上传：`0`。
- 自动重试/fallback：`0`。

## 剩余边界

- 尚未用真实、明确授权的非敏感短音频执行供应商验收。
- 尚未证明粤语字准率优于现有本地路线。
- 正式登记只能标为 `cloud_asr_candidate`，不能标为生产默认或已完成质量晋级。
