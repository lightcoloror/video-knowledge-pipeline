# Canonical 逐字稿审核页刷新回归

- 更新时间：2026-07-30 19:45:00
- 执行工具 / 模型：Codex（GPT-5.6）
- 状态：最小修复已实现，focused 回归通过

## 变更说明

- 意图：避免完整审核刷新后，canonical 逐字稿文件仍存在，但审核页暂时显示“逐字稿为 0”的假缺失。
- 决策：完整 `refresh-lecture-review` 导出结束后，复用既有 `refresh_bundle_review_html`，将 canonical transcript 绑定后的审核页作为最终投影；不新增渲染器或第二套状态机。
- 理由：完整 Bundle 导出与只刷新审核页职责不同。人工审核必须最后读取稳定的 `source-arbitrated-transcript`，而不是陈旧 Timeline 展示字段。
- 证据：
  - 三个真实 Bundle 已使用 `refresh-review-html` 刷新，Timeline alignment issue 均为 0。
  - 新增 focused 回归 `tests/test_lecture_workflow_canonical_review_refresh.py`，结果为 `1 passed`。
  - 修改文件与测试文件的 Ruff、compileall 均通过。
- 生效范围：审核 HTML 投影和命令返回的 `review_html_refresh` 回执；不修改 canonical transcript、Timeline 真源、模型路由、授权或网络行为。

## 复用关系

本次直接复用：

- `video_knowledge_pipeline.webui_bridge.refresh_bundle_review_html`
- 既有 source-arbitrated transcript 绑定逻辑
- 既有 `refresh-lecture-review` 完整导出流程

没有增加新的审核服务、HTML 渲染器、Timeline 或状态机。

## 真实 Bundle 验证

- `.local/online-full-video-20260719/3-scheme-principles/pipeline/webui-bundle`
- `.local/online-batch-20260721/2-scheme-explanation-closing/webui-bundle`
- `.local/online-batch-20260722/1-customer-trust/webui-bundle`

三者刷新命令均成功，审核页面包含人工关键点控件；人工金标准仍需审核者明确勾选并正式写回，系统不会自行把候选摘要升级为 goldset。

## 验证命令

```powershell
$env:PYTHONPATH='src'
python -m pytest -q -p no:cacheprovider `
  tests\test_lecture_workflow_canonical_review_refresh.py `
  --basetemp C:\tmp\vkp-lecture-workflow-canonical-review-20260730

$env:RUFF_CACHE_DIR='C:\tmp\vkp-ruff-cache'
$env:PYTHONPYCACHEPREFIX='C:\tmp\vkp-pycache'
python -m ruff check `
  src\video_knowledge_pipeline\lecture_workflow.py `
  tests\test_lecture_workflow_canonical_review_refresh.py
python -m compileall -q `
  src\video_knowledge_pipeline\lecture_workflow.py `
  tests\test_lecture_workflow_canonical_review_refresh.py
```

## 尚未闭环

扩大到 `test_bundle_workflow.py` 和 `test_review_session.py` 的关联测试在当前机器并发高负载下超过三分钟，被执行环境终止；没有产生断言失败。应在现有高负载任务结束后重跑，不能把本次超时当作通过。
