# 超长视频快速内容分段使用说明

- 更新时间：2026-08-18 16:52:01 +08:00
- 执行工具/模型：Codex (GPT-5.6 Sol)

## 使用流程

```powershell
# 1. 只生成计划，不剪视频
.\scripts\video-knowledge.ps1 long-video-fast-segment-plan <webui-bundle> `
  --media-path <source.mp4> `
  --profile auto

# 2. 打开 exports/long-video-fast-segment-plan.md，对照原片时间码审核；
#    在 long-video-fast-segment-review.todo.json 中逐项填写 keep 或 drop，
#    再填写 operator_confirmation。

# 3. 正式应用人工决定，但仍不剪视频
.\scripts\video-knowledge.ps1 apply-long-video-fast-segment-review `
  <webui-bundle> <review-json>

# 4. 预览 FFmpeg 新副本命令，默认不执行
.\scripts\video-knowledge.ps1 render-long-video-fast-segment <webui-bundle>

# 5. 明确执行，只写新副本
.\scripts\video-knowledge.ps1 render-long-video-fast-segment <webui-bundle> `
  --output-path <new-output.mp4> --execute
```

## 产物

- `exports/long-video-fast-segment-plan.json|md`：候选、证据、时间码和预览范围。
- `long-video-fast-segment-review.todo.json`：人工逐项决定。
- `exports/long-video-fast-segment-approved.json`：哈希绑定的正式人工决定。
- `edit.decisions.json`、`delete_segments.json`、`cut.segments.json`：复用现有剪辑交接合同。
- `exports/long-video-fast-segment-filter.txt`：确定性 FFmpeg filter script。
- `exports/long-video-fast-segment-render-qa.json`：输出时长验真。
- `exports/media-execution/ffmpeg-render-execution-receipt.json`：现有单一 FFmpeg 出口回执。

## 变更理由

| 项目 | 意图 | 决策 | 理由 | 证据 | 生效范围 | 回滚 |
|---|---|---|---|---|---|---|
| 内容判定 | 快速缩短长视频 | VAD/ASR 粗筛，OCR/镜头保护视觉内容 | 单一模态会误删 | 现有 VAD、Timeline、technical shots | 候选计划 | 删除计划模块 |
| 安全门 | 防止 Agent 直接删片 | 每项明确确认，pending 阻断 | “有文件”不等于可剪 | reviewed artifact 门经验 | review apply | 保留旧 video-edit 流程 |
| 渲染 | 输出可交付副本 | 明确 `--execute`、CPU 精确重编码、无 fallback | 精确边界优先于无损关键帧近似 | shared FFmpeg receipt | 新输出文件 | 删除渲染入口及派生文件 |
| 恢复 | 支持超长任务重跑 | 输入/计划/审核/输出哈希绑定，输出存在拒绝覆盖 | 避免断点后重复覆盖 | dependency snapshot + receipts | 单 Bundle | 删除派生回执后重建 |

## 已知限制

- “无信息闲聊”具有强主观性，首版只保留 Schema 类型，不自动生成删除候选。
- 重说检测只标记“可能重复”，不选择哪一遍更好。
- 无音频视频暂不进入首版精确渲染；计划仍可生成，但执行会 fail-closed。
- 真实超长视频速度与节省比例仍需固定样本 benchmark。
