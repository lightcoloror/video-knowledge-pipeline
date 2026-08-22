# 本地 VLM 仲裁工具修复回执（2026-08-22）

- source_issue: `docs/evaluations/2026-08-22-local-vlm-arbitration-tool-issues.md`
- scope: VKP 工具代码与纯合成测试
- real_media_accessed: `false`
- provider_or_model_calls: `0`
- dependency_install_or_download: `0`
- service_started: `false`
- commit_or_push_during_implementation: `not_performed`（后续由操作者单独授权打包推送）

## 1. 稳定入口与 Windows 参数

- 意图：消除开发态入口误判及 PowerShell 逗号参数歧义。
- 决策：README 优先展示 `scripts/video-knowledge.ps1`；语义帧、时序帧和预检同时接受可重复 `--index` 参数，并与 CSV 参数去重合并。
- 理由：wrapper 已是仓库既有稳定入口；重复参数不依赖 shell 对逗号的解释。
- 证据：`tests/test_vision_feedback_contract.py` 的 CLI 契约测试。
- 生效范围：CLI 参数解析与 README；不更改 provider 配置。
- 回滚：移除重复参数和 `_int_csv_and_repeat_arg`，恢复原 CSV-only 入口。

## 2. Provider 预检状态分层

- 意图：区分当前有效 provider 与未使用的远程路由噪声。
- 决策：报告增加 `effective_provider`、配置来源、route usage、`remote_fallback_disabled`、`provider_health_required/verified` 和 `ready_for_confirmed_execution`；保留 `ready_to_execute` 兼容别名。
- 理由：配置与确认值通过不等于端点健康检查通过。
- 证据：既有 vision provider / route preflight 回归套件。
- 生效范围：预检 JSON、Markdown 和命令提示；不发健康请求，除非调用方显式要求。
- 回滚：删除新增字段并继续消费兼容别名。

## 3. VLM 完成、截断、失败与进度

- 意图：禁止顶层成功掩盖截断/失败，并为长批次提供实时状态。
- 决策：批次使用 `ok/partial_failure/failed`；保存 `finish_reason`、响应长度、单帧耗时、完整/截断/失败 indexes；重试使用指数退避；每批写 progress JSON 并输出无敏感信息 heartbeat。
- 理由：模型调用完成不等于输出完整，运行事件数也不等于可导出证据数。
- 证据：`tests/test_vision_feedback_contract.py`、`tests/test_vision_pipeline.py` 及 vision provider 回归。
- 生效范围：单帧和时序视觉执行、run audit、run registry；截断内容仍 fail-closed。
- 回滚：删除 progress helper 和新增计数；保留既有结果文件即可恢复旧消费者行为。

## 4. 视觉证据计数统一

- 意图：统一运行日志、Timeline、导出与验收对“完整/可消费”的定义。
- 决策：新增共享 `visual_evidence.py`，分别输出 model-complete 与 export-consumable index sets；运行审计同时保留事件数、唯一数和差异 indexes。
- 理由：人工接受项可消费但不是模型完成项；截断或 incomplete 项两者都不是。
- 证据：`tests/test_vlm_issue_contracts.py` 与 knowledge export 回归。
- 生效范围：knowledge coverage、knowledge export、视觉 run reconciliation。
- 回滚：恢复各模块原有本地判定函数；Timeline 数据格式不需迁移。

## 5. 写盘状态、质量状态与 freshness

- 意图：区分“文件已写出”和“内容已通过生产质量门”，并显式标记视觉更新后的旧导出。
- 决策：导出返回 `write_status`、`quality_status`、`quality_ready`；视觉写回后写 `knowledge-export-freshness.json=stale` 和恢复命令，重新导出后写 `fresh`，但明确 freshness 不等于质量批准。
- 理由：`exported` 只证明写盘成功；旧总结不会自动吸收新视觉证据。
- 证据：knowledge export 回归和 `_export_status` 契约测试。
- 生效范围：知识导出、视觉后处理回执、run registry；不自动重导出。
- 回滚：忽略或删除 freshness 回执，消费方继续使用 dependency snapshot/production gate。

## 6. 总结路径与结构数字

- 意图：避免相对路径错指仓库目录，以及阿拉伯标题序号被当作事实数字。
- 决策：相对 `summary_path` 以 bundle 为基准；质量报告同时记录请求/解析路径；标题序号从事实数字证据中剥离并单列 structural numbers；兼容转义换行的旧测试/旧产物。
- 理由：结构编号不是金额、比例、日期或事实数量。
- 证据：smart summary quality、numbering 与 `tests/test_vlm_issue_contracts.py`。
- 生效范围：smart summary quality check 和默认总结结构。
- 回滚：恢复 cwd 相对解析和原数字扫描；不会改变已有总结文本。

## 7. 验收队列分组

- 意图：不再混淆全量人工复核、转写缺口、OCR 缺口和视觉缺口。
- 决策：验收摘要分别输出 transcript、OCR、semantic visual、temporal visual 计数，并给出有界分组样本及去重样本。
- 理由：四种计数含义和恢复动作不同。
- 证据：`tests/test_vlm_issue_contracts.py` 与 acceptance 回归。
- 生效范围：acceptance JSON/Markdown；原 coverage 计数保留。
- 回滚：消费者忽略 `review_queue` 新字段即可。

## 8. 连续帧标签增量与条件升级

- 意图：先用低成本连续帧标签变化筛选片段，再把动态或歧义片段升级到连续帧多模态理解。
- 决策：复用 RAM++；支持 `representative/continuous` frame mode；平滑单帧漏标与抖动，记录稳定/出现/消失标签，并结合 OCR、镜头/画面变化和 ASR 动作词做升级判断。
- 理由：标签可以说明可能可见的内容，但不能证明动作、顺序、意图或因果。
- 证据：`tests/test_temporal_tag_delta.py`；静态、动态、导入写回和逐帧 RAM++ 均为合成 fixture。
- 生效范围：新增 `temporal_tag_delta` 与 `temporal_multimodal_escalation`；绝不写入 `temporal_visual_understanding`。
- 回滚：从 Timeline 删除这两个字段；ASR、OCR、既有视觉理解和人工事实不受影响。

## 验证记录

- 新增分级与进度测试：`7 passed`。
- 状态/计数/数字/验收契约：`4 passed`。
- 首次相关回归：`152 passed, 1 failed`；唯一失败为测试替身不接受未设置的 `max_tokens`，兼容修复后单项复跑 `1 passed`。
- 最终相关回归：`153 passed, 8 warnings`；warnings 为当前 Python 环境的既有 requests 依赖版本提示。
- 静态检查：本批涉及文件 `ruff --no-cache` 通过；`mcp_server.py` 在忽略 4 个仓库既有未使用 import 后通过；AST 与 `git diff --check` 通过。

## 9. 本地模型位置只读复核

- 意图：确认新增连续标签能力复用现有 RAM++，并避免把 provider 模型 ID 误当作 VKP 管理的权重路径。
- 决策：RAM++ 继续通过 `SOURCE_INVENTORY` 解析源码、checkpoint 和 tokenizer；LM Studio 继续只使用可配置的 loopback endpoint 与模型 ID，VKP 不选择或写入其 C/D 权重目录。
- 理由：模型文件的存储与当前加载状态属于模型运行时；VKP 只负责能力发现、预检和显式调用边界。
- 证据：`general_tagger_status()` 返回 `ready`；`%LOCAL_MODEL_ROOT%\models\recognize-anything\ram_plus_swin_large_14m.pth` 为 3,010,210,801 bytes；BERT tokenizer 与 recognize-anything 源码均存在。LM Studio 的当前下载目录与另一个本地归档目录各有一份 Qwen3-VL GGUF 和 mmproj，文件尺寸一致，两个目录都不是 reparse point；`%USERPROFILE%\.lmstudio\settings.json` 当前 `downloadsFolder` 指向主模型目录。
- 生效范围：本节仅记录 2026-08-22 的只读路径证据；未请求 `127.0.0.1:1234`，因此不声明服务当前加载了哪一份。
- 回滚：删除本节即可；未移动、删除、链接或修改任何模型文件和 LM Studio 配置。

## 未跨越的真实运行门

- 原反馈中的 306、313、363、370 四个真实帧没有在本轮重跑；其旧截断状态不能仅凭代码回归改写为已完成。
- 未读取真实媒体、未调用 provider 或本地模型、未启动 LM Studio、未安装依赖，也未自动重导出真实 bundle。
- 本轮结论是“13 项工具问题已在代码和合成/离线契约层处理”，不是“原真实 bundle 已达到生产质量门”。
