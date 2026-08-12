# YouTube Digest → VKP 选择性吸收实施记录

更新时间：2026-08-12 09:19:10 +08:00
执行工具 / 模型：Codex / GPT-5.6 Sol

## 结论

VKP 已选择性吸收 YouTube Digest 的双语逐字稿交互、稳定 ID 对齐、按视口懒加载翻译、时间戳笔记和章节时间覆盖思想；没有引入浏览器扩展、Supadata、固定 DeepSeek、Provider SDK 或第二套逐字稿真源。

固定上游：`zarazhangrui/youtube-digest` v1.1.5，commit `d03e1f61e017b032159ffd1821cac6e7693ce0c7`，MIT。源码复审与机器提案由工作区 `SOURCE_INVENTORY.json` 中的 `youtube-digest-vkp-review-2026-08-12` 记录定位；公开文档不固化个人绝对路径。

本轮没有复制上游 TypeScript/React 源码。实现复用 VKP 已有 `subtitle_editor`、Moyf 字幕编辑应用壳、Loopback Review Server、translation sidecar、章节事实包与 Smart Summary 质量门，只增加薄投影、校验、UI 适配和测试。

## 变更 YD-VKP-01：稳定 ID 翻译分批合同

- **意图：** 长逐字稿不再把全部译文一次性嵌入页面，同时保证源文与译文不会错位。
- **决策：** 增加 `video_knowledge_pipeline.subtitle_translation_slice.v1`；每批最多 4 个稳定 `segment_id`、最多 1600 个源字符，按请求顺序返回；请求必须绑定当前 projection SHA，旧 projection、重复 ID、未知 ID 和超限批次全部 fail-closed。
- **理由：** 上游按块处理长逐字稿的交互是有效参考，但 VKP 已有带 occurrence lineage 的稳定 ID 和不可变 translation sidecar，不应重新建立索引或调用上游 Provider。
- **证据：** 聚焦测试覆盖 6 段拆成 `[4, 2]`、精确对齐、陈旧 SHA 和超限拒绝；原始源文本 SHA 在正式应用前后保持不变。
- **生效范围：** `subtitle_editor.py` 的只读翻译切片与投影元数据；不调用模型、不生成译文、不修改 canonical transcript。
- **回滚：** 删除切片函数与 HTTP 只读端点；静态 `prepare-subtitle-editor` 仍可把既有译文完整嵌入页面。

## 变更 YD-VKP-02：视口懒加载与陈旧响应取消

- **意图：** 只加载用户正在查看的译文，并防止快速滚动或 Bundle 更新后旧响应污染当前页面。
- **决策：** Loopback 页面初始只嵌入原文和翻译可用性；使用浏览器原生 `IntersectionObserver`、4 项队列、generation token 与 `AbortController` 拉取本地译文。切换模式或重新载入会递增 generation，旧响应即使晚到也不能更新界面。
- **理由：** 复用浏览器原生观察器和 VKP 现有同源 Review Server，避免增加前端框架、缓存服务或 Provider 调用。静态离线页面保留完整译文，确保禁用懒加载时行为不变。
- **证据：** UI/HTTP 回归验证 lazy 页面不内嵌译文、静态页面仍内嵌；端点回显 generation；脚本静态检查包含 observer、abort、generation 和 original/mandarin/bilingual 三种模式。
- **生效范围：** `/subtitle-editor` 与 `/api/subtitle-editor/translations`；仅 loopback GET，只读取已存在的翻译 sidecar。
- **回滚：** 将 `lazy_translation` 设为 false 或移除端点与观察器；正式应用合同不受影响。

## 变更 YD-VKP-03：时间戳笔记 sidecar

- **意图：** 允许用户在播放位置记录“原始引文、润色引文、个人笔记”，同时保留来源与时间证据。
- **决策：** 在字幕编辑草稿中增加 `timestamp_notes`；正式应用前校验 note ID、segment ID、source lineage、媒体边界和原始引文子串，成功后写入 `human-reviewed-timestamp-notes.json`，并登记到 apply receipt/manifest。
- **理由：** 原始引文是证据，润色文本和用户笔记是派生内容，三者必须分离；不能把笔记静默写回 ASR 或 Timeline。
- **证据：** 正例回归验证 sidecar、来源 ID 和 receipt 计数；伪造原始引文被拒绝；草稿仍由 Bundle ID + source hash 隔离的 localStorage 管理。
- **生效范围：** 字幕审核派生 sidecar；原始 ASR、原翻译、Timeline 和 Smart Summary 真源不变。
- **回滚：** 删除 note UI 与 sidecar 输出；既有人工纠正逐字稿和双轨字幕仍可读取。

## 变更 YD-VKP-04：章节与最终总结时间覆盖硬门

- **意图：** 防止只覆盖后半段、时间戳越界或章节顺序错误的摘要被误报为成熟总结。
- **决策：** 章节事实包增加 `timeline_coverage_quality`，检查输入存在、时间戳范围、章节单调、首尾四分位覆盖；最终 Smart Summary 增加 `timestamp_range` 与 `first_last_timeline_coverage` 两项独立质量门。
- **理由：** 章节和金句提取只有在能回链到逐字稿时间范围时才可靠；模型生成文字不能替代系统已知的时间边界。
- **证据：** 聚焦测试覆盖正常首尾锚点、仅后半段和越界三种情况；失败时状态为 degraded/failed check，不写成事实通过。
- **生效范围：** 章节派生包和 Smart Summary 本地质量检查；不改逐字稿正文，不重新调用在线模型。
- **回滚：** 移除新增检查键即可恢复旧门；现有质量报告消费者对新增字段为向后兼容。

## 明确拒绝与保留边界

- Supadata transcript API：拒绝；VKP 继续使用本地/受控采集与现有 consent/provider gateway。
- 固定 DeepSeek 或任意 Provider SDK：拒绝；翻译与总结继续走统一模型网关和显式授权。
- 整套浏览器扩展、Chrome 注入、账号/Key UI：拒绝；VKP 使用独立 Loopback 字幕页。
- PR #10 的未固定实现：拒绝进入生产基线。
- 时间戳笔记不会自动成为事实证据；只有原始引文和现有 evidence lineage 可回链。
- 懒加载失败只显示 source-only/missing，不触发跨 Provider 或 local/cloud fallback。

## 公共接口

```text
GET /api/subtitle-editor/translations
  ?projection_sha256=<sha256>
  &segment_id=<stable-id>  (最多 4 个，可重复 query key)
  &generation=<integer>
```

正式写回仍使用既有：

```text
POST /api/subtitle-editor/validate
POST /api/subtitle-editor/apply
```

所有写请求继续受 loopback Host、同源 Origin、CSRF、Bundle revision、projection SHA、请求大小、segment lineage 和媒体边界校验。

## 验证

- 新选择性吸收聚焦回归：`5 passed`。
- 字幕、翻译、Smart Summary、Workbench 关联回归：`29 passed`。
- 知识导出、run registry 与字幕 UI 扩展回归：`33 passed / 2 skipped`；两条跳过是本机 Playwright 条件，不是断言失败。
- 完整离线回归：`1664 passed / 7 failed / 6 skipped`。7 项均不在本轮功能路径：4 项是并发中的 Qwen ASR runner 失败、1 项是 Provider 预设数量基线变更、1 项是既有 Global Reduce 预算超出 6 字符、1 项是既有 Moyf 文档绝对路径公开安全门；本轮新增文件未增加失败。
- `node --check src/video_knowledge_pipeline/static/moys-subtitle-editor/vkp-adapter.js`：通过。
- Ruff 定向检查和 `git diff --check`：通过。
- `SOURCE_INVENTORY.json`：YouTube Digest 已从 `reviewed_reference / not_integrated_reference` 更新为 `reviewed_selected / local_trial`；账本校验 `error_count=0`，既存 warning 保留。
- Windows `.pytest_cache` 仍有既存 ACL 警告；使用独立提升权限 basetemp 后测试正常，不属于代码失败。

## 新鲜度与回滚

翻译切片必须绑定 projection SHA；字幕草稿仍绑定 Bundle revision/source hash；正式应用产物通过既有 downstream freshness 机制使 Smart Summary、最终合并文档和字幕导出失效。若回滚本轮代码，既有 canonical transcript、translation sidecar、Timeline 和 Moyf 兼容静态页面均保持可读。
