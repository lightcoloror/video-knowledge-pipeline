# 火山 Coding Plan 与 SiliconFlow 同系列模型原生对比

更新时间：2026-07-18 11:55:00 +08:00
执行者：Codex / GPT-5

## 决策

VKP 本身不依赖 OpenClaw。固定样本对比默认改用 VKP 原生 OpenAI-compatible 单请求客户端，并复用 `text_llm_gateway.build_openai_compatible_text_body()` 与 Base URL 规范化实现。OpenClaw 只保留为 2026-07-18 首次中断实验的历史证据，不再是 parity 运行时依赖。

## 官方调用依据与边界

- 火山 Coding Plan：按[火山引擎 Coding Plan AI coding client 配置示例](https://developer.volcengine.com/articles/7615528054736945158)锁定 `https://ark.cn-beijing.volces.com/api/coding/v3/chat/completions`。该文明确列出 `baseUrl`、`apiKey`、模型名与 `openai-completions` 协议配置，并说明 `/api/v3` 属于另行按量计费的在线推理；VKP 不会静默替换端点。
- 火山当前[官方 Coding Plan 套餐页](https://www.volcengine.com/activity/codingplan)列出 DeepSeek V4 系列、GLM-5.2、Kimi-K2.7 等当前系列，并声明支持“其他工具”；[其他工具文档入口](https://www.volcengine.com/docs/82379/2188959?lang=zh)作为自定义工具接入依据。页面没有公开声明 VKP 这个产品名，因此真实请求若被拒绝只记录失败。
- SiliconFlow：按[Chat Completions 官方参考](https://docs.siliconflow.cn/en/api-reference/chat-completions/chat-completions)锁定 `https://api.siliconflow.cn/v1/chat/completions`。
- SiliconFlow 的[模型中心](https://www.siliconflow.cn/models)与[价格页](https://www.siliconflow.cn/pricing)提供本轮五个精确 Model ID 的公开证据。
- 两边共用字段只有 `model`、`messages`、`temperature=0`、`max_tokens=1024`、`stream=false`。不发送 Ark `thinking_mode`、SiliconFlow `enable_thinking` 或其他 Provider 专属字段。
- 火山官方文章展示的是 AI coding client 配置示例，不是 VKP 产品认证。原生 VKP 客户端只复用其 URL 与 OpenAI-compatible 请求字段；若 Coding Plan 拒绝自定义客户端，该候选就记录为失败，不回退 `/api/v3`，也不启动 OpenClaw。

## 五组精确映射

| 系列 | Ark Coding Plan | SiliconFlow |
| --- | --- | --- |
| DeepSeek V4 Pro | `deepseek-v4-pro` | `deepseek-ai/DeepSeek-V4-Pro` |
| DeepSeek V4 Flash | `deepseek-v4-flash` | `deepseek-ai/DeepSeek-V4-Flash` |
| GLM-5.2 | `glm-5.2` | `zai-org/GLM-5.2` |
| Kimi K2.7 Code | `kimi-k2.7-code` | `moonshotai/Kimi-K2.7-Code` |
| Kimi K2.6 | `kimi-k2.6` | `Pro/moonshotai/Kimi-K2.6` |

“同系列/同版本名称”不等于已经证明两家是同一底层权重、量化、推理后端或系统提示。只有供应商响应中的精确模型 ID、输出差异和人工补丁审查会进入证据；未报告的后端身份不作推断。

本轮衡量的是“锁定同系列版本别名后，两家供应商默认服务行为是否有差别”。各家的默认推理强度可能不同，这本身属于供应商服务差异。为避免把未获官方支持的字段硬塞给某个模型，本轮不发送供应商专属思考参数；如果后续要做“强制同一非思考模式”的第二阶段，需要逐模型取得两家官方字段支持证据，并使用新的独立授权。

## 原生执行防护

- 每个候选单 deployment、单 route revision、单 consent v2、最多一次调用和 0.02 美元 reservation。
- 直连使用 `http.client.HTTPSConnection`，只发一次 POST；不自动重定向、不重试、无 fallback、无工具调用面。
- 请求模型、请求正文 SHA-256、响应正文 SHA-256、HTTP 状态、request id、响应模型和 usage 会进入审计；Authorization、API Key 和请求正文不写入日志。
- `execute-all` 每完成一个候选就写 `batch-execution.json`；已有精确结果不会重跑。
- 比较报告只保存内容 SHA、规范化 JSON SHA、补丁 SHA、字段相似度和质量门，不复制模型正文。

## OpenClaw 中断实验（历史证据，不作为能力结论）

- 初始批次因 Windows 裸 `openclaw` shim 解析错误，在外发前 0/10 失败。
- 修复 shim 后按用户要求中止：5 个候选确定完成，每个 1 次外部请求；第 6 个只有 reservation、没有结果或审计，按“外发状态不确定”保守处理；其余 4 个未尝试。
- 5 个完成输出均尝试生成 `find`、`exec` 或工具调用标记，没有返回要求的 JSON，全部 15/100、质量门失败。这说明 Agent runtime 扭曲了固定请求，不能据此评价模型本身。
- 历史产物：`.local/coding-plan-siliconflow-parity-20260718-retry1/parity-comparison.json` 与 `.md`。

## 新原生验收

新的权威计划使用独立输出目录和新的精确授权。旧 OpenClaw consent 已消耗或状态不确定，不会被原生计划复用。完成 10 个原生候选后，最终报告必须达到 5/5 pair comparable；任何缺失、HTTP 拒绝、模型身份不同或不满足 JSON/补丁质量门都保留为差异，禁止自动 fallback。

## 原生真实执行结果

更新时间：2026-07-18 13:24:00 +08:00
执行者：Codex / GPT-5

本轮使用用户批准的同一 1,356 字节固定代码样本、十份候选级 consent v2、每个候选一次调用、零重试、零 fallback。终端直连外发曾被 Agent 平台拒绝，但 VKP 持久化白名单没有丢失；最终通过已安装的 Secure MCP Tunnel 与 Trusted Broker 前门执行。Broker capability 证据同时列出 `ark.cn-beijing.volces.com` 与 `api.siliconflow.cn`，transport 为 `secure_mcp_tunnel`。

| 系列 | Ark Coding Plan | SiliconFlow | 当前结论 |
| --- | --- | --- | --- |
| DeepSeek V4 Pro | 20.163 秒，HTTP 200，精确响应模型 `deepseek-v4-pro`，`finish_reason=length`，最终内容为空 | 120.257 秒，单次超时，无响应模型 | 服务行为明显不同；没有两端正文可作语义比较 |
| DeepSeek V4 Flash | 10.051 秒，HTTP 200，精确响应模型 `deepseek-v4-flash`，`finish_reason=length`，最终内容为空 | 120.224 秒，单次超时，无响应模型 | 服务行为明显不同；没有两端正文可作语义比较 |
| GLM-5.2 | 15.693 秒，HTTP 200，精确响应模型 `glm-5.2`，`finish_reason=length`，最终内容为空 | 62.482 秒，HTTP 200，精确响应模型 `zai-org/GLM-5.2`，得到实质代码审查结果 | SiliconFlow 是本轮唯一产生实质答案的候选；仍无法做成对正文比较 |
| Kimi K2.7 Code | 24.433 秒，HTTP 200，精确响应模型 `kimi-k2.7-code`，`finish_reason=length`，最终内容为空 | 120.147 秒，单次超时，无响应模型 | 服务行为明显不同；没有两端正文可作语义比较 |
| Kimi K2.6 | 10.487 秒，HTTP 200，精确响应模型 `kimi-k2.6`，`finish_reason=length`，最终内容为空 | 120.128 秒，单次超时，无响应模型 | 服务行为明显不同；没有两端正文可作语义比较 |

汇总：10/10 候选各执行一次，外部请求总数 10；传输完成 1，失败 9；5/5 Ark 响应都报告精确模型，SiliconFlow 只有完成的 GLM 响应能报告并核验精确模型。提供商响应没有给出可核算金额，实际费用未知；consent 总预留上限严格保持 0.20 美元。所有 consent 均为 `calls_attempted=1`，不能被自动重跑。

SiliconFlow GLM 的补丁方向经人工阅读是合理的：使用 `BEGIN IMMEDIATE` 在读取配额前取得写锁，所有拒绝和异常路径显式回滚，并给出跨进程并发测试。它没有完全遵守固定输出契约：返回了 Markdown JSON 围栏，且 `tradeoffs` 是字符串而不是数组。离线评分器已修正这两类误判，重算为 80/100、严格质量门失败；它仍是本轮内容质量最好的候选，但不能标记为生产契约通过。

## 能否证明两家“同一模型没有差别”

不能。本轮已经证明两家在相同公共请求字段下的**服务行为有明显差别**：Ark 五项都快速返回但默认推理消耗完 1,024 token 后没有最终内容；SiliconFlow 四项排队或推理超过 120 秒，只有 GLM 返回实质内容。由于 0/5 配对同时获得有效正文，本轮不能判断同系列模型的权重、量化、系统提示或最终答案质量是否相同。

后续若要回答内容质量差异，必须新建第二阶段授权，不能复用本轮已耗尽 consent。建议把“公共字段公平对比”和“各供应商最佳可用配置”分成两套：前者继续不使用厂商专属参数；后者依据两家逐模型官方文档分别设置禁用/限制思考与更高输出预算，并清楚标注请求配置已经不同。

权威本地产物：

- `.local/coding-plan-siliconflow-native-parity-20260718/parity-comparison.json`
- `.local/coding-plan-siliconflow-native-parity-20260718/parity-comparison.md`
- `.local/coding-plan-siliconflow-native-parity-20260718/*/execution.json`
- `.local/coding-plan-siliconflow-native-parity-20260718/*/consent.v2.json`

## 第二阶段：真正的内容质量配对

更新时间：2026-07-18 13:50:41 +08:00
执行者：Codex / GPT-5

第一阶段的 `max_tokens=1024` 同时限制推理内容与最终答案。Ark 五个候选都以
`finish_reason=length` 结束，其中四个最终 `content` 为空；SiliconFlow 四个候选在
120 秒内没有完成。因此第一阶段只能证明服务行为不同，不能比较内容质量。

第二阶段增加独立的 `content_quality_v1` 请求档：

- 同一 1,356 字节固定代码样本、同一提示、同一 JSON 输出契约、同一 `temperature=0`。
- `max_tokens=16384`、`stream=true`、单次超时 300 秒。
- 每个候选仍只有一次请求，零外部重试、零 fallback、无工具调用面。
- `max_tokens`、`stream`、`temperature` 和超时被写入 deployment 与 route revision；第一阶段 consent 不能复用。
- 只把最终 `content` 作为答案。`reasoning_content` 不落正文，只记录字符数和终止原因。
- 不发送 `thinking_mode`、`enable_thinking` 或 `thinking_budget`。火山[标准在线推理 Responses 文档](https://www.volcengine.com/docs/82379/1795150)说明 `thinking: {"type":"disabled"}`，但这不是 Coding Plan `/api/coding/v3/chat/completions` 的逐模型字段承诺；SiliconFlow 的[通用 Chat Completions 文档](https://docs.siliconflow.cn/en/api-reference/chat-completions/chat-completions)列出 `enable_thinking` 和 `thinking_budget`，但公开支持列表没有完整覆盖本轮五个新模型。模型中心只确认这些模型具有不同思考模式，没有给出一张覆盖全部候选的请求字段矩阵。未确认字段不会被猜测或硬塞入请求。

离线计划已生成，但尚未创建 consent、读取凭据或联网：

- `.local/coding-plan-siliconflow-content-quality-20260718/parity-plan.json`
- `.local/coding-plan-siliconflow-content-quality-20260718/operator-authorization-request.md`

稳定前门：

```powershell
.\scripts\run-coding-provider-parity.ps1 `
  -Action prepare `
  -RequestProfile content_quality_v1 `
  -OutputDir '%WORKSPACE_ROOT%\video-knowledge-pipeline\.local\coding-plan-siliconflow-content-quality-20260718'
```

只有操作者接受新清单后才创建十份候选级 consent v2。完成后，比较报告会同时记录最终正文质量分、严格契约门、`finish_reason`、`reasoning_chars`、正文长度、模型身份、延迟和字段级相似度；补丁正确性仍需人工审查，单个固定任务不构成通用模型排行榜。

离线验证：第二阶段定向测试 16 项通过；完整测试 838 项通过、1 条既有 `jieba/pkg_resources` 警告；旧第一阶段计划仍可通过稳定前门离线重算并保持 `0/5` 可比较的原始结论。准备过程远程请求数为 0。

## 能力上限档：取消 VKP 输出与思考预算

更新时间：2026-07-18 14:05:45 +08:00
执行者：Codex / GPT-5

用户要求测量不同供应商提供同系列模型时的真实任务能力，不再由 VKP 设置保守输出上限。因此 `content_quality_v1` 的 16,384 token 计划被标记为未执行的保守档，新的权威计划改用 `capability_ceiling_v1`：

- 请求不包含 `max_tokens`，让供应商服务按模型原生策略自然停止。
- 请求不包含 `thinking`、`thinking_mode`、`enable_thinking` 或 `thinking_budget`；不关闭思考，也不压缩思考预算。
- 保留 `stream=true`，使长推理能够持续返回；900 秒是无响应挂死保护，不是 token 或思考限制。
- 保留 `temperature=0`，使同一固定代码任务更可复现；它不限制输出长度。
- 每候选一次、零重试、零 fallback，避免拥堵重试和路由切换污染供应商对比。
- 2.00 美元只是十个 consent reservation 的总防失控硬上限，不进入模型请求，也不会中途截断输出；实际计费仍由供应商返回 usage/账单决定。

这一选择遵循 SiliconFlow [Chat Completions 官方说明](https://docs.siliconflow.cn/en/api-reference/chat-completions/chat-completions)：`max_tokens` 是客户端可选的最大生成量，官方还提示不要把它机械设置为上下文窗口上限。公开[模型中心](https://www.siliconflow.cn/models)确认本轮模型具有不同上下文和思考模式，但没有提供覆盖所有五个精确模型的统一思考字段矩阵。Coding Plan 的公开原生接入资料同样没有给出这五个别名的逐模型 raw request 思考字段表，因此 VKP 不猜字段。

新的离线权威产物：

- `.local/coding-plan-siliconflow-capability-ceiling-20260718/parity-plan.json`
- `.local/coding-plan-siliconflow-capability-ceiling-20260718/operator-authorization-request.md`

`content_quality_v1` 目录保留为审计历史，但不创建 consent、不执行远程调用。

离线验证：能力上限档定向测试 18 项通过；完整测试 840 项通过、1 条既有 `jieba/pkg_resources` 警告；准备结果为 10/10 候选 ready、0 个 blocker、0 次远程请求。


## 能力上限档真实结果（最终）

更新时间：2026-07-18 16:55:00 +08:00
执行者：Codex / GPT-5

本节取代“尚未创建 consent、尚未联网”的准备态描述。十个候选均已各占用一次授权调用并进入终态：8 个获得有效正文，2 个失败；没有重试、fallback、额外模型调用或路由替换。所有成功响应均报告并核验了精确模型 ID。

| 候选 | 终态 | 延迟 | 人工内容结论 |
| --- | --- | ---: | --- |
| DeepSeek V4 Pro / Ark | 成功返回正文 | 75.808 秒 | **补丁无效**：执行 UPSERT 后遗漏 `commit()`，默认 sqlite3 事务可能在连接关闭时回滚；旧自动分已纠正为 70，质量门失败。 |
| DeepSeek V4 Pro / SiliconFlow | 成功返回正文 | 612.721 秒 | 补丁正确：原子条件 UPSERT、成功路径提交、`limit <= 0` 提前拒绝，测试较完整。 |
| DeepSeek V4 Flash / Ark | 成功返回正文 | 39.684 秒 | 补丁正确：`BEGIN IMMEDIATE`、拒绝路径回滚、成功路径提交；本轮正确结果中最快。测试里的 `/tmp` 路径偏 Unix。 |
| DeepSeek V4 Flash / SiliconFlow | 失败 | >900 秒 | SSE 长时间持续活动使旧 socket-idle 超时未触发；观察到运行超过约 86 分钟后人工停止 Broker，并按一次已尝试、零完成保守结算。恢复记录的 6,729.989 秒包含修复与恢复等待，不可当作纯供应商延迟。 |
| GLM-5.2 / Ark | 失败 | 74.411 秒 | HTTP 200，但 `finish_reason=length`、18,403 个 reasoning 字符、最终正文为空。 |
| GLM-5.2 / SiliconFlow | 成功返回正文 | 103.844 秒 | 补丁正确，使用 autocommit 模式配合 `BEGIN IMMEDIATE` 和显式 COMMIT/ROLLBACK；但含 Markdown 围栏且 `tradeoffs` 类型错误。 |
| Kimi K2.7 Code / Ark | 成功返回正文 | 420.698 秒 | 人工复核为正确：`isolation_level="IMMEDIATE"`，条件 UPDATE 与 INSERT fallback，测试可运行；当前启发式原子性检查低估它。 |
| Kimi K2.7 Code / SiliconFlow | 成功返回正文 | 82.679 秒 | 补丁正确，`BEGIN IMMEDIATE`，功能测试较完整；部分 journal 文件检查启发式价值有限。 |
| Kimi K2.6 / Ark | 成功返回正文 | 103.969 秒 | 补丁正确，`BEGIN IMMEDIATE`、完整回滚与进程屏障测试。 |
| Kimi K2.6 / SiliconFlow | 成功返回正文 | 372.026 秒 | 补丁正确，`BEGIN IMMEDIATE`、提交/回滚和跨进程测试完整。 |

### 这一个固定代码任务的结论

按人工补丁正确性优先、再看延迟，本轮建议顺序是：DeepSeek V4 Flash / Ark、Kimi K2.7 Code / SiliconFlow、Kimi K2.6 / Ark、GLM-5.2 / SiliconFlow、Kimi K2.6 / SiliconFlow、Kimi K2.7 Code / Ark、DeepSeek V4 Pro / SiliconFlow。DeepSeek V4 Pro / Ark 因遗漏提交不合格；两个失败项不进入内容排名。这个顺序只适用于该 SQLite 并发配额修复任务，不是通用模型排行榜。

成对结论：DeepSeek V4 Pro 由 SiliconFlow 明显胜出；DeepSeek V4 Flash 只有 Ark 有效；GLM-5.2 只有 SiliconFlow 有效；Kimi K2.7 Code 两端均正确但 SiliconFlow 更快；Kimi K2.6 两端均正确但 Ark 更快。

所有八个成功答案都把 `tradeoffs` 返回为字符串，而固定契约要求数组，因此严格结构质量门均未通过；这属于输出契约问题，不等同于补丁逻辑错误。GLM SiliconFlow 另有禁止的 Markdown 围栏。最终选型必须同时看人工正确性与契约遵循，不能只看自动分。

### 并行、超时与恢复修复

- `capability_ceiling_v1` 通过 Trusted Broker 后台提交，按远程目的地各建一个单工队列：Ark 与 SiliconFlow 可以并行，同一目的地内部串行。这样缩短总墙钟时间，同时保留候选级原子 reservation、调用上限和审计顺序。
- 原生流式读取改为按总墙钟 deadline 检查，而不是只依赖 socket idle timeout；即使 SSE 持续发心跳或 reasoning chunk，也会在总上限到达时终止。
- 新增 `recover-interrupted` 稳定入口，只能把满足严格前置条件的单次中断标记为一次已尝试/费用未报告；它不会再 reservation 或重发请求。
- 自动评分器新增成功路径持久化检查，避免“有写入语句但没有 commit”仍被误判为高质量。

最终权威证据：

- `.local/coding-plan-siliconflow-capability-ceiling-20260718/parity-comparison.json`
- `.local/coding-plan-siliconflow-capability-ceiling-20260718/parity-comparison.md`
- `.local/coding-plan-siliconflow-capability-ceiling-20260718/*/execution.json`
- `.local/coding-plan-siliconflow-capability-ceiling-20260718/*/consent.v2.json`

比较报告状态为 `incomplete` 是预期语义：3/5 成对获得双方有效正文，2/5 只有一端有效；它不表示剩余候选尚未执行。

最终本地验证：Ruff 通过；`python -m compileall -q src` 通过；完整 pytest 845 项通过；PowerShell 稳定包装器语法检查通过；`git diff --check` 通过。
