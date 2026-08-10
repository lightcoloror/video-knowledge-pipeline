# ADR：VKP 拍摄素材拉片 v2

- 状态：Accepted / implemented with candidate runtimes
- 决策时间：2026-08-01 20:56:48 +08:00
- 执行工具/模型：Codex / GPT-5.6
- 适用范围：拍摄素材的技术镜头、镜头事实、语义场景、故事节拍、高光候选、风格指纹、仿拍脚本和人工复核
- 不改变：Timeline、canonical transcript、原始 ASR/OCR/视觉证据、run registry、课程章节规划和 provider gateway

## 结论

VKP 的拍摄素材路线固定为：

```text
技术镜头候选
→ 多检测器分歧审计
→ 逐镜头事实
→ 语义场景
→ 证据化故事节拍 / 有界高光计划
→ 风格指纹 / 仿拍脚本候选
→ Workbench 人工校正
→ 哈希绑定的派生投影
```

缺少可验证技术镜头时必须返回 `blocked_missing_technical_shots`。章节、语义场景、Timeline 行和整段媒体都不得再冒充 shot。

## 变更记录

| change_id | 意图 | 决策 | 理由 | 证据 | 生效范围 |
| --- | --- | --- | --- | --- | --- |
| `PFV2-001` | 消除伪镜头 | 新增 `technical_shot_boundaries.v1` 前门；`shot_breakdown.v2` 只消费验证过的技术边界 | 内容章节不是摄影机切点 | 原实现存在 scene → semantic scene → Timeline → whole-video 回退；新缺边界回归 fail-closed | `technical_shot_detection.py`、`shot_breakdown.py` |
| `PFV2-002` | 复用成熟检测器并避免静默降级 | AutoShot、OmniShotCut 运行时锁定源码 commit 和精确权重；PySceneDetect strict 默认关闭 FFmpeg 降级 | 后端漂移和静默 fallback 会污染边界评测 | AutoShot 固定样本 F1 `0.781316`；AutoShot 权重 SHA-256 `3e85290546ce6d32f4a3581ec2cae87aedd2402246a0d46b4d361a330b4b1fa6` | `shot_boundary_runtime.py`、`shot_boundary_worker.py`、`scene_detection_adapter.py` |
| `PFV2-003` | 让多检测器分歧可审计 | 两帧容差聚合；双来源一致仅标 `candidate_agreement`，单来源标 `needs_human_review`，不自动选择 | 相近边界可合并证据，但冲突不能由平均值掩盖 | 离线多来源、媒体 SHA 冲突和容差回归 | `technical_shot_fusion.py` |
| `PFV2-004` | 快速生成逐镜头镜头语言 | 直接调用固定 Auto Scenes 的 DINO 景别模块和 `OpticalFlowAnalyzer.analyze_frames`；模型缺失/CUDA 不可用时 unavailable | 专用模型比通用 VLM 便宜，系统已知事实不应交给 VLM 猜 | Auto Scenes commit `2c34db3...`；光流合成帧真运行；本机 CUDA 可用但 DINO 权重未安装，正确阻断 | `shot_language_auto_scenes.py`、`shot_language_analysis.py` |
| `PFV2-005` | 保证每个事实可追溯 | 字段统一为 `value/status/confidence/evidence_ids/source/missing_evidence`；状态仅 confirmed/inferred/unavailable | 低置信候选不能冒充事实 | 字段证据、低置信、缺模型和人工覆盖回归 | `shot_facts.v1` |
| `PFV2-006` | 用成熟变化点算法构建语义场景 | 直接复用 `ruptures 1.1.10` 的 `Pelt(model="rbf")`；BGE-M3 缺失时 degraded，不自研聚类器 | 变化点检测已有成熟实现 | 源码 commit `a3f8c43...`；清华镜像 wheel；本地合成信号得到 `[8,16]` | `filmed_structure.py` |
| `PFV2-007` | 避免按位置编造故事角色 | 故事节拍只接受场景证据包，允许 `setup/goal/action/change/conflict/result/payoff/unknown`；无证据为 unavailable | 开头/中间/结尾不等同于真实叙事作用 | 位置推断关闭和非法角色回归 | `story_beat_plan.v1`、`video_structure.py` |
| `PFV2-008` | 有界引入高光模型 | Lighthouse CG-DETR 仅处理不超过 150 秒的场景片段；固定 source commit；缺依赖/权重阻断 | 官方 API 的基准上限为 150 秒，整段长视频不适配 | Lighthouse commit `629bc67...`；本机 import 阻断于缺 `clip`，无权重下载、无伪 smoke | `highlight_detection_adapter.py`、`filmed_structure.py` |
| `PFV2-009` | 提供专业边界审核交互 | 直接复用 WaveSurfer.js 7.12.11 Regions 构建产物并嵌入既有 Workbench；草稿进 localStorage，正式应用走 loopback CSRF API | 不应再建播放器或第二审核服务 | 上游 commit `ae8d3cd...`；官方 build 通过、32 suites/459 tests 通过；Windows 路径只做一行 slash 适配 | `shot_review_workbench.py`、`video_workbench.py`、`review_http.py` |
| `PFV2-010` | 防止审核覆盖真源或输入变化后继续生效 | 审核必须 `human_confirmed`，绑定技术边界/镜头事实/融合结果 SHA 和 source revision；只输出 reviewed projection | 原证据与 Timeline 必须不可变 | stale/hash/media identity/边界顺序/loopback 回写回归 | `shot_review.py`、`shot_review_notes.v1` |
| `PFV2-011` | 让拉片结果可执行、可交换 | `shot_breakdown.v2` 增加镜头语言统计、转移矩阵、覆盖率、证据完整率；同时输出 JSON、CSV、普通 Markdown 和 Logseq 层级 Markdown | 风格应由统计解释；下游格式不应靠解析超宽表 | 导出回归；Logseq 文件无 `collapsed:: true` | `shot_breakdown.py`、`shot_breakdown_exports.py` |
| `PFV2-012` | 保证安装后仍能打开审核时间轴 | 将固定 WaveSurfer JS、Regions JS 和许可证声明为 package data | 只在源码树可用不等于安装包可用 | package-data 回归；静态文件 SHA 见下文 | `pyproject.toml`、`static/` |
| `PFV2-013` | 保留 VFR 与分块边界的真实时间 | 已保存预测可携带逐帧 `frame_timestamps_seconds` 与 `time_offset_seconds`；重叠窗口仍交两帧容差融合并保持人工选择 | 用平均 FPS 推导 VFR 或忽略 chunk offset 会让边界漂移；重叠窗口不能直接重复写入 | 精确 VFR 映射、偏移 300 秒、时间戳缺口 fail-closed 和重叠窗口聚合回归 | `technical_shot_detection.py`、`technical_shot_fusion.py` |
| `PFV2-014` | 让固定上游能找到 VKP 已登记的 FFmpeg | AutoShot/OmniShotCut 隔离 worker 复用 `local_tool_subprocess_env()`，只向子进程传递解析后的媒体工具目录 | AutoShot 的 `ffmpeg-python` 只寻找命令名；VKP 能解析 FFmpeg，但此前未传给 worker | 真实 AutoShot 运行先在 `get_frames()` 报 WinError 2；新增子进程环境回归 | `shot_boundary_runtime.py` |
| `PFV2-015` | 避免稀疏课程帧冒充逐镜头代表帧 | 执行镜头语言时校验 `technical_shot_boundaries.v1.media` 的精确 SHA，并复用 `extract_segment_frames` 和 temporal 等距采样，为每个技术镜头抽起/中/末三帧 | WebUI 时间轴可能只保留一张课程证据帧，不能覆盖所有摄影机镜头 | 12 秒四镜头合成片真实生成 12 张帧、4 份联系表；媒体哈希/三帧回归通过 | `shot_language_analysis.py`、`video.py`、`temporal_frame_groups.py` |
| `PFV2-016` | 兼容真实 WebUI Bundle 帧合同 | 镜头语言同时读取 `frame_paths`、`temporal_frame_paths`、temporal group 和受 Bundle 根约束的 `assets[].path`；拒绝 `assets[].source` 外部路径 | 正式 Bundle 使用 copied asset 投影，而旧单元测试只覆盖 `frame_paths` | 真实规范 Bundle 暴露空帧问题；新增仅含 `assets[].path` 的回归 | `shot_language_analysis.py`、`webui_bridge.py` |
| `PFV2-017` | 防止拉片报告把已有模型证据显示为 missing | `field_provenance` 对非 unavailable 的 `shot_facts.v1` 字段记录其原始 source | Workbench 必须区分“无证据”和“有光流候选” | 实测 camera_movement 有 `frame:*` 证据但 provenance 为 missing；新增结构化事实回归 | `shot_breakdown.py` |

## 固定上游与复现状态

| 上游 | 固定版本 | 许可证 | 本地复现 | VKP 状态 |
| --- | --- | --- | --- | --- |
| PySceneDetect | `c1fcb79b...` | BSD-3-Clause | 既有适配器和回归 | 显式快速路线 |
| AutoShot | `77c82ff826a9301bb173d9be786297a49d73d081` | MIT | 既有 GPU 盲测；权重已锁 SHA | 拍摄素材默认候选 |
| OmniShotCut | `23ad6fb41b296fb9258b0e7825125a914573b906` | MIT | 源码 import 通过；未下载 checkpoint | candidate；只处理分歧/渐变短片 |
| Auto Scenes | `2c34db3520e1319292bb456a0e610a0ef195e78b` | 以本地 LICENSE 为准 | 光流真运行；DINO 权重缺失 | 光流 adapted；景别 runtime pending |
| ruptures | `v1.1.10` / `a3f8c437edf7d54c1a8f90aaa72638363a011765` | BSD-2-Clause | PELT RBF 真运行 | direct reuse |
| Lighthouse | `v1.2` / `629bc6790c66ff2a682f0dbb3e8ab2c0c8ff814f` | Apache-2.0 | 固定源码已核验；缺 `clip` 和 checkpoint | candidate/runtime pending |
| WaveSurfer.js | `7.12.11` / `ae8d3cd32ebb27273051935c01fc6e4001cde3af` | BSD-3-Clause | build 通过；459/459 tests | direct static reuse |

WaveSurfer 固定资产：

- `wavesurfer.min.js`：SHA-256 `a943cbe71700ae910d1c6db28fc56e06327f2a890e93fa22e4d736aa2f5797da`
- `regions.min.js`：SHA-256 `fa36e84bd0f22e332e5ac4d0264967e350375fa00418bc18d095bb0e0116e16d`
- `LICENSE`：SHA-256 `f82930c7b02344417df75b0fc16d9d7d59cfb833babd6c23b7987a309ac27452`

源码准入登记状态：已先通过稳定 `source-ledger.ps1 find` 核对，四个新增上游均无既有登记；随后按固定 commit 尝试注册时，被全局 `SOURCE_INVENTORY.json` 中 12 条与本轮无关的既存路径校验错误原子阻断，未绕过前门、未写入半成品。项目 ADR 与复用账本已保留固定来源，待全局账本 owner 修复既存错误后重试登记。

## 明确拒绝

- 不采用 Auto Scenes `VideoSceneMerger`，不拼接、不删除原视频，不引入第二套 FFmpeg。
- 不复制 Proprietary `video-breakdown` 源码。
- 不采用许可证不明的 Kandinsky camera classifier。
- 不采用 WaveSurfer 8 beta、Vidi 9B 或整段视频 VLM。
- 不按中间帧主体相似度自动合并镜头。
- 不自动下载模型、不 CPU fallback、不在线 fallback、不上传整段视频、不自动发布。

## 兼容性

- 课程默认仍走 `course-v1` 章节结构。
- `filmed-v1` 是显式拍摄素材预设。
- 旧 Bundle 不迁移 Timeline；重新生成派生层即可。
- 旧 PySceneDetect 结果只有 backend、boundary kind 和来源可验证时才允许读取。
- 本地模型的显式任务门控不是 fallback；远程疑难镜头仍须 route、consent 和逐文件 SHA 清单。

## 当前尚未越过的晋级门

- OmniShotCut checkpoint、Auto Scenes DINO 权重、Lighthouse 依赖与权重均未下载，故三者的真实 GPU 质量 smoke 尚未完成。
- 100 个高分歧镜头的匿名景别/运镜复核需要人工 goldset。
- 尚未证明景别 Macro-F1 ≥0.75、运镜 Macro-F1 ≥0.70、主体/摄影机运动混淆 ≤10%。
- 尚未完成三条用户域视频的完整拉片生产验收和“人工复核节省 ≥30%”计时。

这些缺口会保持 `candidate/runtime_pending`，不能因代码入口存在而标记为生产可用。

## 2026-08-08 本地生产链增量验收

- 执行工具/模型：Codex / GPT-5.6
- 记录时间：2026-08-08 17:19:04 +08:00
- 意图：从“合同和测试存在”推进到“本地媒体能真正生成逐镜头派生产物”。
- 决策：先对用户域拍摄课程运行 AutoShot；外置盘硬件失败后停止访问 E 盘，改用 12 秒无敏感合成片验证 PySceneDetect、逐镜头抽帧、Auto Scenes 光流、拉片报告和 filmed-v1 结构。
- 理由：真实硬件/文件系统故障不能伪装成模型失败，也不能通过反复读盘扩大风险；合成片只验证执行合同，不替代真实质量评测。
- 证据：
  - E 盘权重和视频均返回 Windows `WinError 483` / “设备硬件出现致命错误”；AutoShot 没有完成模型加载，不能记为 GPU 质量失败。
  - 合成片 SHA-256：`5dc2a332b1925b9036c15801d9a1289507a3d5950fba1854fc7a2a60f0fb2097`。
  - PySceneDetect 严格路线在 `3/6/9` 秒生成 3 个边界、4 个技术镜头，无 fallback。
  - `shot_facts.v1` 对 4 个镜头生成逐镜头帧；静态镜头为 `static`，动态测试图为低置信 `tracking=0.5267` 并保留 missing-evidence 门。
  - `shot_breakdown.v2` 参考帧门和运镜门已通过；`video_structure.v1` 从 blocked 推进为 degraded，明确剩余 BGE-M3、DINO 景别、本地故事证据和 Lighthouse 权重缺口。
  - 拉片专项回归 `40 passed`，`compileall` 与定向 Ruff 通过；完整 pytest 运行超过约 9 分钟仍无终态输出后被人工终止，未出现断言失败，但不能记为完整回归通过。
- 生效范围：拉片本地执行和派生证据；不修改 Timeline、canonical transcript、原始媒体或 provider gateway。
- 回滚：撤销 `PFV2-014` 至 `PFV2-017` 对应源码提交并重新生成派生产物；原始 Bundle/媒体无需回滚。
