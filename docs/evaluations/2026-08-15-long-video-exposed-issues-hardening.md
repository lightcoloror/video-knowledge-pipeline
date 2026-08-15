# 长视频处理暴露问题补强记录（2026-08-15）

- acting_tool_model: `Codex (GPT-5.6 Sol)`
- updated_at: `2026-08-15 17:12:06 +08:00`
- scope: VKP 本地派生证据、视觉门控、逐字稿质量门、智能总结章节 Map 与 CLI 展示
- network/provider calls: `0`
- production bundle mutation: `0`
- push: `authorized; pending this selective Git operation`

## 结论

本轮问题均属于 VKP Owner 范围，不需要跨线程修改其他仓库。ebook 项目已明确把 `9241` 作为当前 HTTP 契约；真正陈旧的是 VKP 自身默认消费配置，因此已在 VKP 内修正，没有把问题错误派发给 ebook Owner。

## CHG-LONGVIDEO-001：OCR 单项原子检查点与自动回填

- 意图：OCR 已成功但批次在 Timeline 写回前中断时，不丢失已完成结果，也不重复调用 OCR。
- 决策：复用 `storage.write_json` 的原子替换能力，在每张图完成后立即写 `result-checkpoint.json`；新一轮视觉结构处理和知识笔记导出前，自动扫描检查点并兼容扫描旧版 `timeline-*/ebook_pipeline/**/*.md`。
- 理由：原实现只在整批结束后统一写回，一次进程中断会造成“磁盘产物存在、Timeline 不知道”的断裂。
- 证据：新增原子检查点、旧 Markdown 恢复、非法索引 fail-closed 三项回归；同一检查点双跑不会重复增加 structured visual。
- 生效范围：Bundle 内 `visual-structure/timeline-*/ebook_pipeline` 派生 OCR 产物、Timeline/source package 的结构化视觉投影和导出前覆盖率；不修改原图、ASR 或其他原始证据。
- 回滚：移除 `reconcile_ebook_pipeline_checkpoints` 调用和检查点写入；既有检查点只是派生 JSON，可安全忽略。

## CHG-LONGVIDEO-002：课件型屏幕录制 OCR-first 门控

- 意图：静态 PPT/屏幕文字不再因为“存在一张帧”就自动升级为多模态语义任务。
- 决策：删除 `frame_available` 作为 semantic score；增加 `auto/general/lecture-slides-v1` 内容预设。课件预设下，screen/slide/document/OCR 内容先走 `document_visual`；只有动作、指向、空间关系、实物、实验等明确非文字证据才走 `semantic_frame`。
- 理由：系统已知的帧存在性不能证明需要 VLM。原规则把所有未分类帧变成 semantic，导致 58 个假性视觉 blocker。
- 证据：回归覆盖普通帧不升级、课件文字走 OCR-first、讲师指向/空间关系仍保留 semantic 候选。
- 生效范围：`run-video-frame-router` 的派生路由及下游风险 triage；不覆盖已导入人工路由，不调用模型，不改变 Timeline 真源语义。
- 回滚：显式使用 `--content-profile general`；如需旧式全量分析，仍可由 `vision-review-triage --mode full` 明确请求。

## CHG-LONGVIDEO-003：ASR 短缺口误报收敛（验证既有实现）

- 意图：区分停顿/切块边缘的小缺口与真正连续讲话缺失。
- 决策：保留并验证现有 `interval_coverage` + 独立 Silero VAD 路线：单个小缺口在覆盖率及累计秒数预算内不阻断；多个短缺口累计超预算或明显连续讲话缺口继续 fail-closed。
- 理由：不能用整个音频时间轴替代语音覆盖，也不能把每个亚阈值边缘都列成重大缺段。
- 证据：`test_asr_integrity_hardening.py` 覆盖三个 1.9 秒缺口累计失败，以及 100 秒语音内 1.9 秒小缺口通过；本轮 focused 回归通过。
- 生效范围：绑定独立 VAD 的 ASR 完整性报告和局部重跑窗口；没有 VAD 时仍为 `not_evaluated`，不会伪造通过。
- 回滚：恢复旧的逐 gap 绝对阈值判断，但会重新引入本次误报问题，不建议。

## CHG-LONGVIDEO-004：语义纠错风险分级（验证既有实现）

- 意图：让数字、否定词、人名、机构名和领域术语等高风险候选阻断；普通口语候选不再因缺少 readable-impact 文件全部阻断最终总结。
- 决策：复用当前 `_targeted_semantic_evidence_gate` 与 `no_accepted_decisions` 分支。存在局部 ASR 证据计划的高风险候选继续使总结保持 draft；无接受决定、无残留错误的普通候选作为 optional review。
- 理由：候选数量不是风险；把 225 个候选一律视为同级 blocker 会让纠错工作流无法自动收口。
- 证据：当前代码明确输出 `pending_candidate_count`、`targeted_evidence`、accepted/residual/readable 状态，并保持高风险缺证据 fail-closed。
- 生效范围：Smart Summary 质量门；不会自动替换逐字稿，也不会把未经确认的候选写成事实。
- 回滚：恢复所有 candidate 一律阻断的旧规则，会增加假性失败。

## CHG-LONGVIDEO-005：章节 Map 非主题噪声过滤与 Global Reduce 边界

- 意图：防止会议按钮、会前调试、主持串场和纯排名/业绩播报成为读者章节标题或核心摘要。
- 决策：章节候选和视觉标题加入窄范围、整句匹配的非主题过滤器；长业务句即使含“会议/业绩”等词也保留。章节 Map 明确标记 `chapter_map_is_final_summary=false`、`global_reduce_required=true`。
- 理由：宽泛关键词删除会损失课程内容；只过滤短且完整匹配的 UI/串场句更安全。章节 Map 是事实聚合层，成熟读者总结仍需现有 Global Reduce。
- 证据：回归覆盖 UI/主持句被过滤、真实长业务句保留、章节标题不采用屏幕共享文字。
- 生效范围：派生章节 Map、课程图和全局 Reduce 输入；原始逐字稿、OCR、Timeline 不变。
- 回滚：移除 `NON_TOPIC_PATTERNS` 与 reader policy 元数据；Global Reduce 仍可独立运行。

## CHG-LONGVIDEO-006：CLI 大结果默认简洁输出

- 意图：避免逐字稿、Timeline、输入包等数十万字符 JSON 挤占终端与 Agent 上下文。
- 决策：复用命令已经写盘的产物路径。小于 16,000 字符的结果维持完整 JSON；大结果默认只打印 schema/status/summary/count/path/hash，追加 `--verbose` 才完整展开。
- 理由：既保持脚本对小响应的兼容，又明显降低长视频任务的终端 I/O 和上下文占用。
- 证据：回归覆盖小结果完整、大结果简洁、verbose 完整三种路径。
- 生效范围：VKP CLI stdout；文件产物、MCP 参数、实际执行和回执内容不变。
- 回滚：调用时加入 `--verbose`，或移除 `render_cli_result` 前门。

## CHG-LONGVIDEO-007：ebook 端口契约纠正

- 意图：让 VKP 默认配置与 ebook 当前权威 HTTP 契约一致。
- 决策：把 VKP 的 `ebook_markdown_pipeline_http` 默认端口从过期的 `8765` 改为 `9241`。
- 理由：ebook 的 `config/http.env`、`SERVICE_CONTRACT.md` 和安装文档均把 `9241` 定义为当前端口，并明确 `8765` 仅是历史证据。
- 证据：新增默认 `service_url` 回归，要求 `http://127.0.0.1:9241/call`。
- 生效范围：VKP 默认 HTTP adapter 的命令/报告；本轮实际 OCR 仍可直接使用本地模块，不启动服务。
- 回滚：仅在 ebook 权威配置正式变更后同步修改 VKP 配置；不得凭历史记录改回 `8765`。

## 测试与边界

- managed focused regression：`19 passed`。
- targeted Ruff：新增/修改核心文件（除既有 `knowledge_note_export.py` 两条历史 F841）全部通过。
- `knowledge_note_export.py` 的全文件 Ruff 仍报告两个本轮前已存在的未使用局部变量；本轮没有借机混入无关清理。
- 普通 pytest 的 Windows 临时目录/pycache ACL 仍可能失败；本轮统一使用 `scripts/run-tests-managed.ps1`，ACL gate 通过且无残留子进程。
- 未调用 Provider、未上传媒体、未修改生产 Bundle；GitHub 推送只包含本文列明的选择性修改。
