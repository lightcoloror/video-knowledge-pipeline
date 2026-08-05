# VKP 拍摄素材结构分析与通用标签器决策

## Update Record

- 2026-07-18 19:42:38 +08:00 | Codex / GPT-5 | 建立镜头切分、语义场景、剧情结构、高光检测和 RAM++ 通用标签器的实现与运行边界；原生整段视频理解保持禁用。
- 2026-07-18 19:59:43 +08:00 | Codex / GPT-5 | 按用户运行策略将 RAM++ 与 CG-DETR 改为 CUDA GPU 必需，不允许 `auto` 静默回退 CPU。

## 1. 决策结论

VKP 在知识类视频之外增加面向拍摄素材的结构分析，但不启用把整段视频交给大型多模态模型的路线。

当前支持链路：

```text
本地视频 / 既有 Bundle
├─ 镜头切分：PySceneDetect，必要时使用既有 FFmpeg fallback
├─ 语义场景切分：转录、停顿、OCR、视觉变化、标签和镜头边界的证据融合
├─ 剧情线/内容结构：由语义场景生成 opening / development / conclusion 等候选结构
├─ 高光检测：Lighthouse + CG-DETR，按文字查询返回时间窗口和显著性分数
└─ 通用图像标签：RAM++，为关键帧生成中英文开放域标签
```

明确不做：

- 不启用原生整段视频 VLM 上传或整段视频理解。
- 不把镜头切分、场景切分、高光检测静默转换成在线模型调用。
- 不自动下载 Lighthouse、RAM++ 源码或权重。
- 不在本地模型失败后自动 fallback 到远程供应商。
- 不把模型候选覆盖 OCR、ASR、人工确认事实或既有 Timeline 真源。

## 2. 为什么不是“连续抽帧后直接问大模型”

不同任务使用不同证据和算法：

| 任务 | 主要输入 | 当前实现 | 结果 |
| --- | --- | --- | --- |
| 镜头切分 | 连续画面的视觉突变 | 既有 `scene_detection_adapter.py` | 精确镜头边界候选 |
| 语义场景切分 | 镜头边界 + ASR/OCR/标签/停顿 | 既有 `semantic_chapter_plan.py` | 语义连续的场景候选 |
| 剧情线/内容结构 | 有序语义场景 | `video_structure.py` | 开场、发展、结尾等结构角色 |
| 高光检测 | 视频特征 + 文字查询 | `highlight_detection_adapter.py` + CG-DETR | 相关时间窗和显著性分数 |
| Temporal 视觉 | 少量连续关键帧 | 既有 temporal frame groups | 局部状态变化和跨帧语义 |

因此，高光不是简单“截一段让大模型总结”。CG-DETR 是 query-dependent moment retrieval / highlight detection 模型；它按查询选择时间窗口。语义场景则是本地证据融合，不要求完整视频交给大模型。

## 3. 高光检测选择

首选薄适配为 [LINE Lighthouse](https://github.com/line/lighthouse) 的 `CGDETRPredictor`：

```python
from lighthouse.models import CGDETRPredictor

predictor = CGDETRPredictor(checkpoint, device=device, feature_name="clip")
video = predictor.encode_video(media_path)
prediction = predictor.predict(query, video)
```

VKP 只复用官方推理契约，不复制训练框架。输出规范化为：

- `pred_relevant_windows` → `start`、`end`、`score`、`query`；
- `pred_saliency_scores` → 显著性分数证据；
- 所有结果均为 `candidate_only=true`、`human_review_required=true`。

运行限制：

- Lighthouse 官方说明当前基准的最大视频时长约为 150 秒；VKP 对更长素材返回 `scene_clip_required_for_long_video`，先按本地镜头/语义场景裁成短片再检测。
- VKP 真实执行要求 CUDA GPU；`auto` 只用于自动选择 CUDA，不会回退到 CPU。CUDA 不可用时返回 `cuda_unavailable_gpu_required`。SlowFast/PANN 特征仍需操作者明确配置对应权重和更高显存/算力。
- 权重由操作者管理并锁定 SHA-256；适配器不下载权重。

## 4. 通用标签器选择

青龙既有 CL/WD 标签器继续作为兼容证据源，但新默认选择 [Recognize Anything / RAM++](https://github.com/xinyu1205/recognize-anything)：

- 面向通用现实图像，而非以动漫人物属性为主要词表；
- 支持常见类别、长尾类别和开放集标签；
- 官方推理可返回英文和中文标签；
- 能覆盖人物、场所、物体、动作、拍摄环境、办公/课堂/户外等拍摄素材。

默认模型标识为 `ram_plus_swin_large_14m`。每条证据保留：

- Timeline index 与时间范围；
- 中英文标签；
- 模型与 checkpoint SHA-256；
- 帧路径和精确 SHA-256；
- `candidate_only` 与 `human_review_required`。

同一帧若在不同 Timeline 时间段复用，仍分别生成时间证据，不按路径去重。

RAM++ 的真实执行同样要求 CUDA GPU；不自动使用 CPU，也不因 CUDA 不可用而转向远程模型。

## 5. 稳定入口

CLI：

```powershell
.\scripts\video-knowledge.ps1 media-capability-status
.\scripts\video-knowledge.ps1 video-structure <webui-bundle> --media-path <video>
.\scripts\video-knowledge.ps1 highlight-detection <webui-bundle> --query "人物完成关键动作" --media-path <scene-clip>
.\scripts\video-knowledge.ps1 general-tagger-status
.\scripts\video-knowledge.ps1 run-general-tagger <webui-bundle>
```

上述模型任务默认是 preview。真实本地执行仍需显式传入精确源码/权重路径与 `--execute`。已由其他受控工具生成的高光 JSON 可以通过 `--predictions-json` 只读导入。

MCP 工具：

- `video_structure`
- `highlight_detection`
- `general_tagger_status`
- `run_general_tagger`

设置 UI 会显示本地结构能力和选定模型，但“显示能力”不等于“已安装运行时”。

## 6. 产物与真源

所有产物继续落入既有 Bundle：

- `exports/scene-detection.json`
- `exports/semantic-chapter-plan.json`
- `exports/video-structure.json`
- `exports/highlight-detection.json`
- `exports/general-tagger.json`
- 对应 Markdown、MCP args 和 manifest 摘要

Timeline、Bundle、manifest/run registry 继续是真源。高光、结构角色和标签均是候选证据；进入剪辑决策、Smart Summary 或内容发布前必须经过现有质量门和人工复核。

## 7. 当前完成度与剩余运行条件

已完成：

- 本地能力目录、CLI、MCP、设置 UI；
- 结构产物组合与 manifest 写回；
- Lighthouse CG-DETR 本地薄适配和保存结果导入；
- RAM++ 本地薄适配、双语标签和 Timeline 候选证据写回；
- 原生整段视频理解禁用策略；
- fake backend / saved prediction / 安全边界自动测试。

未在开发阶段执行：

- 未安装 Lighthouse 或 Recognize Anything；
- 未下载 checkpoint；
- 未调用任何在线 API；
- 未对真实长视频运行高光或 RAM++ 推理。

首次真实 smoke 需操作者另行准备固定源码和 checkpoint，记录 SHA-256，并选择一个短场景片段。真实 smoke 的结果只用于模型质量验证，不自动改变默认生产决策。

## 2026-07-18 RAM++ 本地 GPU 验收

- 执行者：Codex（GPT-5）
- 记录时间：2026-07-18 21:07:55
- 源码：官方仓库固定提交 7cb804a8609e9f4b1a50b7f31436d2df40bb9481，通过 ghfast.top 镜像下载；源码归档 SHA-256 为 d576b201ab22f2b0feb805911e7a95766ac4651faa26374356198e5f9d556e9e。
- 模型：ram_plus_swin_large_14m.pth，通过 hf-mirror.com 镜像下载，3,010,210,801 字节；官方 SHA-256 497c178836ba66698ca226c7895317e6e800034be986452dbd2593298d50e87d 已精确通过。
- tokenizer：google-bert/bert-base-uncased 四个本地文件已逐文件记录 SHA-256；正式推理不再依赖在线别名解析。
- 设备：NVIDIA GeForce RTX 5070 Ti Laptop GPU；PyTorch 2.11.0+cu128，CUDA runtime 12.8。
- 运行：模型装载 3.631 秒，峰值显存 1,995,930,624 字节；暖机后固定样本单帧约 44–46 ms，首帧 288.9 ms。
- 阈值：VKP 对上游逐类阈值增加 0.75 下限，降低通用词表的过度打标风险。
- 真实前门：run-general-tagger 在既有课程 Bundle 上以 CUDA 完成 3/3 帧、零远程调用、零写回 smoke；同时兼容 frame_paths、evidence_frame_paths 和 integrated_visual.evidence_frame_paths。
- 质量：PPT 办公图识别到计算器、电脑、键盘、桌子、手和人物；课程实景识别到人物、海报、标志、站立和文本；低信息图形页保持稀疏的“线条、文本”标签。
- 边界：RAM++ 只提供通用图像标签，不取代 OCR、ASR 或整段视频理解；结果仍是 candidate evidence，需人工审核。
- 完整机器可读证据：docs/model-evaluation-results/ram-plus-gpu-smoke-2026-07-18.json。
## 2026-07-23 Native video capability correction

- 2026-07-23 20:53:37 +08:00 | Codex (GPT-5)
- native_video_segment is no longer deferred. A consented Gemini route uses the Gemini Files API to upload the exact approved local video, request analysis, and delete the temporary provider file. Other providers are not silently substituted: unsupported native-video capability returns an explicit provider-capability result. Local temporal evidence remains available as an independent complementary route.