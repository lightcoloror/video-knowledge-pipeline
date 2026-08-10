# moys-asr-workflow 完整字幕编辑器集成

更新时间：2026-08-10 19:16:59 +08:00
执行工具/模型：Codex / GPT-5.6 Sol

## 结果

VKP 以 `Moyf/moys-asr-workflow` v1.3.1、commit
`949bc84058cdae1d9c021c50203e6d2742f9392c` 为固定上游，复用了完整浏览器编辑壳，新增粤语原文与普通话翻译双轨、Bundle lineage、草稿隔离和显式写回。

稳定入口：

```powershell
.\scripts\video-knowledge.ps1 prepare-subtitle-editor <bundle>
.\scripts\start-review-webui.ps1 <bundle>
# 打开输出中的 /subtitle-editor

.\scripts\video-knowledge.ps1 validate-subtitle-review <bundle> --review-json <review.json>
.\scripts\video-knowledge.ps1 apply-subtitle-review <bundle> --review-json <review.json>
```

静态 `subtitle-editor.html` 可离线编辑并保存浏览器草稿；正式写回必须通过 Loopback Review Server，携带同源 CSRF token。旧 `transcript-editor.html` 继续保留。

## 变更记录

### SUBTITLE-EDITOR-01：固定并复用完整编辑壳

- 意图：直接复用成熟的播放器、字幕列表、波形、快捷键、拆分合并、拖动、批量替换、撤销、颜色、贴纸、静音区和导出体验。
- 决策：只引入上游 `web/` 根目录 8 个资源，保留上游实现；模板只增加 `__VKP_ADAPTER_CSS__` 与 `__VKP_ADAPTER_JS__` 两个插槽。
- 理由：避免重新实现已经通过上游测试的编辑与波形算法。
- 证据：固定上游 JavaScript 定向测试 92/92 通过；此前项目/说话人等定向测试合计 145/145。
- 生效范围：`static/moys-subtitle-editor/`；明确排除 launcher、Qwen/FunASR/Soniox、Key 配置、服务器、模型和 FFmpeg 调度。
- 回滚：删除静态目录、新入口和适配器；旧转写编辑器不受影响。

### SUBTITLE-EDITOR-02：双轨只读投影

- 意图：让粤语原文与普通话翻译共享时间边界，同时保留全部来源关系。
- 决策：新增 `video_knowledge_pipeline.subtitle_editor_projection.v1`，使用整数毫秒，保存 segment/source IDs、全局匿名说话人、字级时间戳和 evidence IDs。
- 理由：moys 工程不能成为 VKP 的逐字稿真源；翻译缺失也不能自动补造。
- 证据：幂等、时间转换、媒体时长边界、缺翻译、字级时间戳和全局说话人测试通过。
- 生效范围：`subtitle-editor-project.json` 与浏览器 DATA 投影；原始 ASR、翻译、Timeline 不修改。
- 回滚：停止执行 `prepare-subtitle-editor`。

### SUBTITLE-EDITOR-03：双轨编辑与草稿隔离

- 意图：保留完整应用壳，同时让两轨同步拆分、合并和恢复。
- 决策：VKP adapter 在当前字幕区增加普通话输入框；时间和播放头共用；拆分翻译缺少有效拆分点时标记 `needs_translation_review`；不同 `speaker_global_id` 禁止合并；草稿按 Bundle ID 与 projection SHA 隔离到 localStorage。
- 理由：原文和翻译不能产生互不相干的时间轴；刷新恢复不能伪装成已经正式写回。
- 证据：页面合同、draft/apply 状态、服务端跨说话人负例和 projection drift 测试通过。
- 生效范围：浏览器草稿和 `.mosp` 兼容导出；`.mosp` 不成为真源。
- 回滚：移除 `vkp-adapter.js/css`，上游壳仍可单轨运行。

### SUBTITLE-EDITOR-04：Loopback 安全写回

- 意图：复用现有 Review Server，不建立第二端口或审核状态机。
- 决策：新增 `/subtitle-editor`、project、validate、apply 四个入口；写请求复用 loopback Host、CSRF、Origin、2 MiB 上限，并追加 projection SHA、来源 ID、整数毫秒、Bundle 媒体时长边界和说话人校验。
- 理由：浏览器草稿不是执行授权；旧标签页不能覆盖已经变化的 Bundle。
- 证据：真实本地 HTTP roundtrip 测试覆盖页面、校验、正式应用和 receipt。
- 生效范围：现有 `review_http.py`；不开放远程 Host。
- 回滚：删除四个 route，旧 review/workbench route 保持。

### SUBTITLE-EDITOR-05：人工 sidecar 与下游失效

- 意图：把人工确认结果安全送回逐字稿和字幕导出，同时保留原始证据。
- 决策：正式应用生成 `human-reviewed-subtitle-track.json`、人工纠正逐字稿、双轨 SRT/VTT/ASS、OTIO/FFconcat/kept-ranges 派生计划和 receipt；字幕边界不反写原始 ASR；Smart Summary、最终合并文档和字幕导出标记 stale。
- 理由：人工修改应优先于模型候选，但不能抹掉原始 ASR 时间戳或自动执行剪切。
- 证据：源文件 SHA 保持不变、human_confirmed、缺翻译不生成完整普通话字幕、静音区仅显式 `removed=true` 才进入计划、输出格式和 run registry 测试通过。
- 生效范围：Bundle 派生 sidecar；在线重建仅生成待办，不发起调用。
- 回滚：停止消费人工 sidecar；原始输入仍完整存在。

### SUBTITLE-EDITOR-06：受控贴纸与匿名说话人颜色

- 意图：保留贴纸与颜色能力，不开放任意绝对路径浏览，也不把声纹自动命名。
- 决策：只扫描 Bundle 内 `stickers/`（最多 500 个审核静态图片），禁用上游任意文件夹/绝对路径入口；相同 `speaker_global_id` 使用确定性颜色。
- 理由：静态资源必须受 Bundle 根目录约束；说话人颜色是匿名可视提示而非身份断言。
- 证据：页面配置与 safe bundle path 复用，三个全局说话人字段原样进入项目。
- 生效范围：编辑器显示和导出计划。
- 回滚：移除 Bundle `stickers/` 或停用颜色投影。

### SUBTITLE-EDITOR-07：真实分块 Bundle 的媒体与时间 lineage

- 意图：让媒体由 source package 登记、segment ID 按块重启、边界存在重叠的真实采访也能进入人工编辑。
- 决策：复用 lecture review 的 `review_media_reference` 优先级，并新增只解析已登记 manifest/source-package 的路径解析器；重复 ID 在投影中增加 occurrence-scoped `segment_id/source_lineage_ids`，同时保留原 `original_segment_id/source_segment_ids`；重叠段显示为 `overlap_requires_review`，不自动裁剪。
- 理由：按附近文件名猜视频可能绑定错误素材；覆盖原 ID 会切断来源；自动删除分块重叠可能损失讲话。
- 证据：第一真实 Bundle 通过 `lecture-package.json sources[].path` 成功预检 15 段；第二真实 Bundle 从原先第 305 段报错改为生成 469 段投影，识别 88 个重复 ID key 和 2 处需要人工校正的时间重叠；正式 review 未消除重叠时仍 fail-closed。
- 生效范围：本地播放器媒体解析、编辑投影和正式 apply 验证；不写真实 Bundle、不改 canonical transcript。
- 回滚：移除附加解析/lineage 投影，旧 manifest-only Bundle 仍可使用；旧草稿由 projection SHA 漂移门自动阻断。

## 合同与产物

- `video_knowledge_pipeline.subtitle_editor_projection.v1`
- `video_knowledge_pipeline.subtitle_review_notes.v1`
- `video_knowledge_pipeline.human_reviewed_subtitle_track.v1`
- `video_knowledge_pipeline.subtitle_review_apply_receipt.v1`
- `subtitle-editor.html` / `subtitle-editor-project.json`
- `human-corrected-transcript.json/.md`
- `human-reviewed-source.srt/.vtt/.ass`
- `human-reviewed-mandarin.srt/.vtt/.ass`（仅翻译完整时登记）
- `human-reviewed-subtitle.otio.json`
- `human-reviewed-kept-ranges.json`
- `human-reviewed.ffconcat`（只读计划，`execution_authorized=false`）

## 安全与兼容边界

- 原始 ASR、原始翻译、Timeline、原始证据和媒体 SHA 不修改。
- 不调用 Provider、不下载模型、不上传媒体、不执行静音剪切、不发布。
- 静态页面没有 CSRF token，只能保存草稿；正式写回走 loopback 服务。
- 翻译不完整时不登记完整普通话字幕。
- Workbench 优先打开新版，旧版入口仍可单独使用。

## 验证结果

- 上游编辑器/波形 JavaScript：`92 passed / 0 failed`。
- VKP 新合同与 Loopback HTTP（含 source-package、重复分块 ID 和重叠边界）：`12 passed / 0 failed`。
- Workbench、旧编辑器、Review Server、翻译、新鲜度及 Chrome Playwright 关联回归：`31 passed / 0 failed`。
- 本地 Chrome Playwright（合成 Bundle）：`2 passed / 0 failed`；未配置浏览器的公开克隆行为为 `2 skipped`，不下载浏览器。
- Ruff（本轮 Python/测试）和 JavaScript/Python 语法检查：通过。
- 完整离线 pytest：`1650 passed / 2 failed / 6 skipped`。两项失败可单独稳定复现，且对应文件均不在本轮 diff：既有 Global Reduce 在 3000 字预算测试中输出 3006 字；既有说话人文档含 `D:\used-by-codex` 绝对路径，触发公开快照门。本轮不夹带无关修复。
- 全局源码账本：`error_count=0`；另有 100 条既存 warning，未由本轮新增。
- 两个真实采访 Bundle 只读预检：`15 segments / ready / 0 overlap` 与 `469 segments / needs_review / 2 overlaps`；`write=false`，没有改真实产物。

## 源码准入与验证

- `SOURCE_INVENTORY.json` 已登记固定 commit、许可证、本地源码和本文证据路径；状态为 `reviewed_selected / local_trial`。
- 七个未改动的上游静态文件已逐文件 SHA-256 比对，全部与固定源码一致；`editor-template.html` 只增加两个明确的 VKP adapter 插槽。
- 上游 JavaScript 定向测试、VKP 合同/HTTP 回归和相关 Workbench/翻译/说话人回归均离线运行；Playwright 使用本机 Chrome 和纯合成 Bundle 验证可见工具栏、草稿恢复、显式 apply 与 revision 冲突 2/2 通过；不使用 Provider、Key 或真实媒体。
