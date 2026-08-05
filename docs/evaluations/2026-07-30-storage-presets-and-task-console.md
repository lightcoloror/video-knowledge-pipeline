# VKP 媒体保留预设与 Task Console 入口

- 记录时间：2026-07-30 22:05:00（Asia/Shanghai）
- 执行工具/模型：Codex / GPT-5
- 删除、移动或归档文件：0

## 意图

把用户确认的保留原则落实为两个清晰入口：

- 默认尽量节省空间，同时完整保留课程内容；
- 可选档案级绝不降质。

## 决策

- 新增用户预设名 `space_saving`，映射到稳定内部策略 `practical_course`。
- 新增用户预设名 `archive_lossless`，映射到稳定内部策略 `archival_lossless`。
- 旧策略名继续接受，避免既有命令和报告失效。
- Task Console 同时显示两个只读审计命令。
- 审计只生成 JSON/Markdown 证据，不自动删除、移动、归档或修改 provenance。

## 理由

内部策略名已经被测试、历史报告和脚本引用，直接重命名会制造兼容性回归。用户预设别名能提供直观界面，同时保持原审计合同稳定。

`space_saving` 允许分辨率、帧率、采样率等非关键技术指标有小幅取舍，但音频讲话、逐字稿、数字/术语、PPT/OCR、场景和引用迁移硬门仍必须通过。`archive_lossless` 对技术质量降低也会阻断。

## 证据

- 实现：
  - `src/video_knowledge_pipeline/media_equivalence_audit.py`
  - `src/video_knowledge_pipeline/task_console.py`
- 回归：
  - `tests/test_media_equivalence_storage_presets.py`
  - `tests/test_media_equivalence_audit.py`
  - `tests/test_task_console_storage_presets.py`
  - `tests/test_task_console.py`
- 媒体审计及预设：`24 passed`
- Task Console 相关：`12 passed, 1 warning`
- Ruff：`All checks passed`

## 生效范围

只影响媒体等价性审计的预设输入和 Task Console 的命令展示。不会：

- 删除任何视频；
- 自动选择保留版；
- 降低课程内容硬门；
- 修改 Bundle、Timeline、逐字稿或智能总结；
- 把质量取舍自动视为人工同意。
