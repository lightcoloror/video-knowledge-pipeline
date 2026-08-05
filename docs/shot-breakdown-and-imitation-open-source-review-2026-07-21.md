# VKP 拉片、风格指纹与仿拍脚本开源项目源码审查

- 更新时间：2026-07-21 09:25:00
- 执行工具/模型：Codex / GPT-5.6
- 审查方式：固定 commit 的本地浅克隆与关键源码逐文件审查；未安装依赖、未下载模型、未执行在线 API。
- 源码目录：`%WORKSPACE_ROOT%\source-reviews\shot-breakdown-wave-20260721`
- VKP 边界：Timeline、Bundle、run registry、Workbench、ASR/OCR、镜头检测和 provider gateway 继续作为唯一真源；外部结果只能成为 candidate evidence。

## 结论

VKP 现有“镜头切分、语义场景、剧情结构、标签、ASR/OCR、temporal 视觉”已经覆盖拉片的底层证据，但缺少稳定的创作交接层。本轮独立实现了：

1. `shot_breakdown.v1`：逐镜头时间、内容、景别、运镜、构图、色彩、音频、标签与字段 provenance。
2. `style_fingerprint.v1`：镜头时长分布、cuts/min、镜头语言与场景/剪辑角色分布、证据完整度。
3. `imitation_script.v1`：按镜头输出仿拍草案、单一主运镜、邻接连续性、提示词字段顺序和禁止虚构约束。
4. `shot_imitation_readiness.v1`：参考帧、内容证据、景别、主运镜等逐项硬门；只表示“可供人工复核”，不表示可自动生成。

命令：

```powershell
.\scripts\video-knowledge.ps1 shot-breakdown <webui-bundle> `
  --reference-analysis-json <可选的已保存逐镜头分析.json>
```

产物：

- `exports/shot-breakdown.json|md`
- `exports/style-fingerprint.json`
- `exports/imitation-script.json|md`
- `exports/shot-imitation-readiness.json`
- `runs/shot-breakdown/run.json`

命令不会解码视频、启动模型、调用网络或修改 Timeline。

## 模块级审查与处置

| 项目 | 固定 commit | 许可证证据 | 值得复用的模块/代码 | VKP 处置 | 状态 |
| --- | --- | --- | --- | --- | --- |
| `keng1304/video-breakdown` | `a8188e148ed07381ee91915d78da3462474c016a` | MIT | `structure/schema.py` 的 CameraMotion、Composition、ColorProfile、AudioSync、DirectorFingerprint；`fingerprint/statistics.py` 的节奏统计；`perception/*` 的字段划分 | 独立实现逐镜头事实、风格指纹和可选 saved-analysis import；没有复制推理代码 | **已实现/适配** |
| `wassermanproductions/scriptbreak` | `c457f02ec2f0f34bb31af5289af90dd9216297b5` | Apache-2.0 | `mcp/scriptbreak-mcp.mjs` 的 `size/angle/move/lens/desc`、look bible、覆盖审计、提示词顺序、每镜头一个主运镜 | 独立实现 imitation-script 字段、prompt order 与 coverage audit；不引入桌面 UI/MCP 服务 | **已实现/适配** |
| `Forget-C/Jellyfish` | `a9678194ddf2d9be3ccbe78d4287d87d5089e123` | Apache-2.0 | `shot_preparation_state.py`、`shot_video_readiness.py`、`shot_video_prompt_pack.py` 的聚合准备态、逐项 check、相邻镜头连续性、构图锚点、屏幕方向 | 独立实现只读 readiness 和邻接连续性；拒绝其数据库、provider、任务状态机 | **已实现/适配** |
| `OYYH-Apple/video-storyboard-generator` | `4ccbe8abd80b9a44da43024aec11b2aa41b2bbb4` | MIT | 景别/构图/声音字段、短镜头逻辑检查、Seedance 风格 prompt 字段 | 只吸收字段词汇和人工检查思想；15 秒不是自动切分规则 | **已适配** |
| `soCzech/TransNetV2` | `85cef72af9a916bdfd7cc94a670c9cdfbf12d1ed` | MIT | `inference/transnetv2.py` 的逐帧概率与 `predictions_to_scenes` 输出契约 | 保留为可选镜头边界 saved-prediction/外部 detector 候选；不替换 PySceneDetect，不自动加载 TensorFlow/PyTorch 权重 | **候选** |
| `wentaozhu/AutoShot` | `77c82ff826a9301bb173d9be786297a49d73d081` | MIT | `utils.py` 的 F1/Precision/Recall/阈值评测；短视频 SHOT 数据域；模型融合帧相似度与色彩直方图 | 只吸收评测维度和短视频域基线；研究代码无稳定库入口，不进入生产运行时 | **候选/评测** |
| `bytedance/Shot2Story` | `ae26ac3d2f9e9a91a7fd0653bfb6a2b3cb250308` | README：代码 Apache-2.0；文本标注 CC BY-NC-SA 4.0 | 单镜头详细描述、多镜头 summary、帧 token + ASR、检索任务定义 | 只吸收拉片质量评测任务；数据非商业限制且运行时重，不进入生产依赖 | **候选/评测** |
| `movienet/movienet-tools` | `d3f66b2534320b583b607e639995fb1f156ecf21` | 仓库未发现清晰许可证 | shot/place/action/keyframe/audio 的影片级结构任务 | 仅作为 taxonomy/benchmark 参考；许可证未核实，禁止复制代码 | **拒绝代码复用** |
| `linyqh/NarratoAI` | `0a5dcf5f21f7f40ca77bc38ea6d1d3fd52e32c26` | MIT | `documentary/frame_analysis_service.py` 的批次逐帧数量约束、排序与 batch result | 只吸收“每批逐帧完整、批次排序、失败显式化”的验收思想；拒绝固定间隔抽帧、第二套 FFmpeg/ASR/provider/剪辑管线 | **适配验收思想/拒绝运行时** |
| `Encorebao/video-pilot` | `eaf7434a26c0ce235c4097439c11ad1fa5232b62` | 见既有复用账本 | 版本化 taxonomy、镜头类型感知质量解释 | 已在 `scene_taxonomy.py` 独立实现，本轮直接复用，不重做 | **既有已实现** |
| `PySceneDetect` | VKP 既有固定源码 | BSD-3-Clause | 本地镜头边界检测 | 继续作为默认 detector；fallback 必须显式记录 | **既有已实现** |
| `modelscope/FunClip` | `39afd187a63960a6c1e7301e52c8551f5d6cdec4` | MIT | ASR 驱动剪辑 | VKP 已有 ASR/剪辑交接链，新增接入会重复真源 | **拒绝重复实现** |
| `harry0703/MoneyPrinterTurbo` | 本轮只做远程源码/README 复核 | MIT | 主题到成片、素材获取、TTS、字幕、provider | 属于下游生成系统，不是参考片拉片；不引入其供应商与生成管线 | **拒绝** |
| `HL-hanlin/VideoDirectorGPT` | README 复核 | 未进入代码审查 | 声称可做视频导演生成 | README 明示 code coming soon，无可复用实现 | **拒绝** |

## 关键源码判断

### video-breakdown

- Camera analyzer 在 RAFT ONNX 不可用时静默退回 Farneback。VKP 禁止复制这种运行时降级；任何实现变更必须把 backend 和 fallback 写进 provenance。
- 相机运动使用平均光流与近似 homography，主体运动会污染镜头运动；虽然计算 residual flow，但分类未真正基于 residual。因此运镜只能是 candidate evidence。
- 景别取最大人物 bbox，不能泛化到产品、风景或无人物素材。
- keyframe selector 使用中帧和相邻差异峰值，可能选到转场/异常帧。VKP 应继续使用已有 hard-frame 与质量门。
- prompt formatter 对多个 temporal segment 重复同一基础提示，不等于动作拆解。本轮没有复制。

### Jellyfish / ScriptBreak

- 值得复用的是“聚合准备度”，不是它们的数据库或生成服务。
- VKP readiness 只检查已有证据，不能读取 API Key、provider 默认值或启动生成任务。
- continuity 必须保留相邻镜头 ID、屏幕方向/视线复核要求，但不能凭规则断言具体左右关系。
- ScriptBreak 的 look/character/location/prop bible 适合将来作为人工确认的创作资产层；当前不应从参考片自动虚构人物身份或地点。

### TransNetV2 / AutoShot

- 两者可以补 PySceneDetect 在复杂转场、短视频剪辑上的召回，但会引入 GPU/模型权重与额外依赖。
- 正确接入点是统一 `candidate_shot_boundary` saved-prediction contract，比较边界 F1、Precision、Recall、容差和下游人工修正量。
- 在固定本地样本胜出之前，不能替换默认 detector，也不能在 PySceneDetect 失败时静默自动启动模型。

## 已实施安全边界

- 所有字段带 `field_provenance`；缺证据保持 `unknown`/`needs_human_input`。
- imported reference analysis 只读取本地 JSON，并记录精确 artifact SHA-256；不运行上游模型。
- readiness 终态是 `ready_for_human_imitation_script_review_not_generation`。
- 仿拍脚本固定 `publication_allowed=false`、`media_generation_allowed=false`。
- Workbench 将 run 的 `needs_review` 显示为 action required。
- 不修改原 Timeline，不新增第二套 Timeline、FFmpeg、ASR、OCR、provider、状态机或审核服务。

## 测试证据

```powershell
python -m pytest -q -p no:cacheprovider `
  --basetemp %WORKSPACE_ROOT%\tmp\pytest-shot-breakdown `
  tests/test_shot_breakdown.py `
  tests/test_video_structure_and_general_tagger.py `
  tests/test_video_workbench.py
```

结果：focused `12 passed`；完整离线回归 `984 passed, 1 warning`。

覆盖：saved analysis 导入、字段 provenance、风格统计、未知项阻断、准备度、禁止生成/发布、CLI、MCP args、run registry、Workbench。

## 后续候选，不在本轮冒进实现

1. 建立 `candidate_shot_boundary.v1` 通用导入契约，允许 TransNetV2/AutoShot saved predictions 与 PySceneDetect 盲比。
2. 在真实拍摄素材上加入镜头运动、构图、色彩和音频分析器；每个 analyzer 必须单独声明实现、模型/commit、设备和 fallback。
3. 增加 Workbench 逐镜头表单，人工确认景别、主运镜、轴线、角色/场景 bible 后再交给视频创作工具。
4. 质量指标增加：边界人工修正量、unknown 字段率、连续性误报率、仿拍脚本可执行性，不以“字段填满”作为质量。
## 2026-07-23 saved prediction 适配更新

- Updated: 2026-07-23 08:03:13 +08:00 by Codex / GPT-5.6.
- 本节取代上文“建立 candidate_shot_boundary.v1”为未实现候选的旧状态。
- 直接消费 TransNetV2 和 AutoShot 的 predictions_to_scenes saved 输出，不复制边界转换算法，不加载 TensorFlow/PyTorch，不下载权重。
- 新增 source_format=transnetv2_scenes / autoshot_scenes；支持 JSON frame pair 或 start_frame/end_frame 对象，按显式 fps 转为秒。
- 输出沿用现有 scene candidate evidence、首批样张门、Bundle/run registry 和人工复核链，但候选 schema 为 video_knowledge_pipeline.candidate_shot_boundary.v1。
- 每项记录固定上游项目/commit/API、输入 SHA-256、fps、threshold、原始 scene/frame 坐标和 cache identity。
- 乱序、重叠、负数、非整数帧或缺失 fps 在写入前失败；Timeline 不变，export_eligible=false。
- PySceneDetect 仍为默认 detector；没有 silent fallback、模型执行、网络调用或权重下载。
- 状态：TransNetV2 与 AutoShot 均为“saved-prediction 契约已适配；真实拍摄素材盲测待完成”，不是运行时已部署。
- 验证：focused 9 passed；PySceneDetect、视频结构、拉片和候选证据相关回归 32 passed；Ruff、py_compile、diff check 通过。
