# VKP 在线模型调用方式与 Stage B 结果影响审计

- 状态：completed
- 审计时间：2026-07-17 20:55:17（Asia/Shanghai）
- 执行工具/模型：Codex / GPT-5
- 范围：火山方舟 Coding Plan Stage B 固定样本 43 次调用、统一模型运行时、固定套件 runner
- 边界：本次审计和修复没有调用在线模型、没有上传图片/文本、没有读取或输出密钥、没有切换默认路线

## 结论

Stage B 确实调用了每个候选所指定的准确模型。调用链使用内容寻址 virtual model，每个候选只有一个 deployment，重试为 0，未发生 fallback；图片按输入顺序进入同一条 user message，并在 VKP 内存中转换成完整 MIME data URL。不存在因路由串线而“测到别的模型”的证据。

调用方式对结果有三类不同影响：

1. **仅影响报告，不影响模型能力**
   - temporal 聚合器读取了 task gateway 外层，而延迟、usage、provider、deployment 位于 runtime_result 内层，导致旧报告中 temporal latency 为 0、usage 为空。
   - LiteLLM 启动时尝试下载远程 cost map，TLS 超时后回退到本地副本。它不改变模型请求或回答，但会制造长时间只有 warning 的假象。
2. **可能影响输出契约稳定性**
   - 旧 Stage B 只在 prompt 中要求 strict JSON，没有 route 锁定 response_format=json_object。
   - 这不会自动提升视觉理解，但会降低 JSON 语法漂移；字段拼写、字段含义和证据完整性仍必须由 VKP 契约与质量门验证。
3. **可能真实影响模型表现或延迟**
   - 旧 Stage B 的临时 M3 路线没有继承 thinking_mode=disabled。对支持该扩展的 Coding Plan 模型，这会影响推理行为、延迟和 reasoning 输出形态。
   - 旧 Stage B 没有 route 锁定 max_tokens，使用供应商默认上限。现有短输出没有观察到截断，因此它不是本次字段别名或漏检手部变化的已证实根因，但对更长 OCR/temporal 输出存在风险。

## 已实现修复

### 1. Temporal 运行时解包

trusted_model_connector.py 现在统一从 runtime_result 读取：

- content
- status
- deployment
- provider
- latency_ms
- usage
- estimated_cost
- error

旧 Stage B 产物不会被伪造或反向改写；新的执行会记录真实聚合指标。

### 2. 三层结果状态

新增 model_output_contracts.py，将结果分为：

- transport_ok：请求是否正常到达并得到成功响应；
- contract_ok：JSON/文本格式、必填字段和字段类型是否符合契约；
- quality_gate_passed：证据冲突、必需术语、最小纠错、temporal 状态变化等任务质量门是否通过。

HTTP 200 不再等价于生产可用。

### 3. 显式别名规范化

输出契约允许列明字段别名，例如：

- uncertainity → uncertainty
- non-text_visuals → non_text_visuals

每次规范化都会记录在 applied_aliases，别名与规范字段内容冲突时判为 contract_failed，不会静默覆盖。

### 4. 任务质量门

固定样本和后续生产契约可表达：

- 摘要必须同时保留相互冲突的证据词，而不是擅自选边；
- 逐字稿纠错只允许列明的 source/replacement，额外改写判为 overcorrection；
- temporal 每组必须返回非空 state_changes；
- 禁止 <think> 等不应进入产物的标记；
- OCR/语义视觉必须满足列明字段与类型。

### 5. Route 锁定调用参数

火山 Coding Plan profile 新增允许但非必填的：

- response_format
- max_tokens
- 既有 thinking_mode

固定套件准备器会：

- 对 Coding Plan 的 JSON 用例默认锁定 response_format=json_object；
- 对 minimax-m3 默认锁定 thinking_mode=disabled；
- 合并用例/候选的 request_options（例如 max_tokens）；
- 将这些参数写入 deployment 和 route revision。

参数变化会生成新的 route revision，必须重新创建 consent；旧 consent 不能误匹配新调用方法。

### 6. LiteLLM 本地 cost map

VKP LiteLLM 子进程环境设置：

- LITELLM_TELEMETRY=False
- LITELLM_LOCAL_MODEL_COST_MAP=True

因此不再在启动时访问 GitHub raw cost map；未知的新模型费用继续明确记为 unknown，不伪造费用。

## 对既有 Stage B 排名的解释

- OCR 和多数语义结果仍可作为候选证据，因为实际模型和图片请求正确。
- temporal 的内容可评审，但旧 latency=0 不可用于速度排名。
- M3 的旧结果代表“未锁定禁思考”的调用方法，不能直接等同于修复后的 M3 配置。
- 只靠 prompt 产出的 JSON 不能证明契约合格；需要用新增三层 validator 重新离线评估。
- 旧结果不会被覆盖。若要比较调用方式修复前后，需要新的 route revision、新 consent 和用户单独批准的最小复测。

## 代码与测试证据

核心文件：

- src/video_knowledge_pipeline/trusted_model_connector.py
- src/video_knowledge_pipeline/model_output_contracts.py
- src/video_knowledge_pipeline/model_candidate_suite.py
- src/video_knowledge_pipeline/model_candidate_benchmark.py
- src/video_knowledge_pipeline/model_runtime_client.py
- src/video_knowledge_pipeline/model_gateway.py
- scripts/run-model-candidate-fixed-suite.ps1

离线测试覆盖：

- task-gateway 嵌套 temporal 指标；
- JSON 字段别名及冲突；
- 摘要证据冲突；
- 最小纠错/过度纠错；
- temporal 非空状态变化；
- transport/contract/quality 三层状态；
- route 锁定 M3 禁思考、JSON 模式和 max tokens；
- 本地 LiteLLM cost-map 环境。

## 最终离线验证

- Stage B 保存响应：`43/43` transport 成功；离线质量门为 OCR `7/7`、语义视觉 `7/7`（2 个显式别名）、temporal `6/7`、证据摘要 `6/11`、最小纠错 `1/11`。
- 离线报告：`.local/volcengine-model-matrix-20260717/prepared-stage-b-pruned-after-stage-a/offline-contract-review-20260717/model-candidate-benchmark.json`。
- 报告 SHA-256：`8ed839530fc9aac1cdcdbb0abf054b4ce23da3afc06afab8231841aaa4691948`。
- 聚焦回归：`87 passed`。
- 完整回归：`811 passed, 1 warning`；warning 为 jieba 对 pkg_resources 的既有弃用提示。
- `python -m compileall -q src`：通过。
- PowerShell AST：`0` 错误。
- `git diff --check`：通过。
- 变更密钥模式扫描：`0` 命中。
- 本轮实现与复核未调用在线模型、未上传任何 artifact、未读取或输出 secret、未改变生产默认路由。

checkpoint commit 在上述证据写入后创建；不 push。
