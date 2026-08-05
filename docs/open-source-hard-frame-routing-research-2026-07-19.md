# VKP 疑难帧门控与开源实现研究

- 状态：implemented
- 研究日期：2026-07-19
- 执行工具/模型：Codex（GPT-5）
- 适用模块：`vision_review_triage`、`targeted_visual_evidence`
- 边界：本研究与实现不调用在线模型，不上传帧，不改变 consent 或目的地白名单。

## 结论

VKP 之前已经具备疑难帧业务策略，核心信号包括：

- 视觉路线存在但分析缺失；
- OCR 空、低信息或结构缺失；
- ASR/OCR 数字、英文术语或命名实体冲突；
- 指示语、操作语；
- Qinglong 标签与质量问题。

多数开源项目解决的是“从长视频中少取一些代表帧”，并不直接回答“本地 OCR 完成后，这一帧是否仍值得交给多模态模型”。因此本次没有替换 VKP 现有路由，而是在其前后补两类能力：

1. 廉价的镜头变化、重复页和 OCR 置信度门；
2. 固定预算下的相关性、覆盖度和多样性审计。

## 开源项目具体做法

### PySceneDetect

官方实现：

- `ContentDetector` 对相邻帧的 hue、saturation、luma 差异加权，可选 edge 差异；
- `AdaptiveDetector` 在滚动窗口中使用内容差异比值，并设置最小内容变化，减少摄像机运动造成的误切；
- 新版还提供 histogram 与 perceptual hash 检测器。

VKP 复用：

- 已有 `scene_detection_adapter.py`，默认 AdaptiveDetector、可选 ContentDetector；
- 本次只读取 `exports/scene-detection.json` 的边界，不重写镜头检测；
- timeline 项内出现边界时，提高 temporal 候选分数。

来源：

- https://github.com/Breakthrough/PySceneDetect
- https://www.scenedetect.com/docs/latest/api/detectors.html

### VideOCR

本地研究源码：

- `%WORKSPACE_ROOT%\tmp\open-video-tools-source\VideOCR`

具体做法：

- 对字幕区域而非整帧计算 SSIM；
- SSIM 高于阈值时，在 OCR 前跳过重复帧；
- OCR 结果低于置信度阈值时不直接采用；
- 对相邻 OCR 文本使用模糊相似度/编辑距离合并重复字幕。

VKP 吸收：

- 使用“主内容区域变化”而非整帧变化；
- 默认遮蔽右下角讲师小窗，防止讲师动作把静态 PPT 误判为动态；
- OCR 置信度低于 0.85 时继续本地补强；
- 相邻页面用 dHash 或 OCR 文本相似度折叠为代表帧。

差异：

- VKP 当前不新增 `fast_ssim` 依赖，第一版使用 Pillow 灰度平均绝对差；
- 输出明确标记算法与阈值，未来可以在不改变门控 schema 的情况下替换成 SSIM。

### VideoContext-Engine

本地研究源码：

- `%WORKSPACE_ROOT%\tmp\open-video-tools-source\VideoContext-Engine\VideoContextEngine_v3.19.py`

具体做法：

- 大约每秒取一帧；
- 计算 HSV 直方图并用相关性比较相邻帧；
- 超过变化阈值并满足最小时长时切场景，超出最大时长则强制切段；
- 每个场景均匀抽取 1 到 5 张关键帧，再把每个场景送给 VLM。

VKP 吸收：

- 镜头内均匀覆盖可用于 temporal 组的代表帧预算。

不照搬：

- “每个场景都调用 VLM”对于讲课/PPT 视频成本过高；
- VKP 必须在场景切分后继续经过 OCR、冲突和收益门。

### AKS

官方仓库：

- https://github.com/ncTimTang/AKS

具体做法：

- 在固定视频 token/帧预算下，把选择建模为“与任务提示相关”与“覆盖整个视频”两项的联合优化；
- 自适应近似选择信息量最大的关键帧。

VKP 吸收：

- 最终候选排序保留任务相关性与时间覆盖；
- 预算是上限，不是触发上传的授权。

### Q-Frame

官方仓库：

- https://github.com/xiaomi-research/q-frame

具体做法：

- 使用 CLIP 文本—图像相似度做 query-aware 选择；
- 用 Gumbel-Max 提高离散选择效率；
- 把帧分配为高、中、低分辨率，控制视觉 token。

VKP 吸收：

- 单帧语义与 temporal 多帧使用不同图像预算；
- 当前先输出 `estimated_images`，不引入新的 CLIP 运行时。

### VideoTree

官方仓库：

- https://github.com/Ziyang412/VideoTree

具体做法：

- 先低密度抽帧和聚类，形成层次树；
- 根据问题相关性展开少量节点；
- 只把展开后的局部信息交给 LLM 推理。

VKP 吸收：

- “先低成本证据、再按不确定性展开”的渐进式思想；
- ebook/OCR → crop OCR → tile → 单帧多模态 → temporal 多模态。

### LongVU

官方仓库：

- https://github.com/Vision-CAIR/LongVU

具体做法：

- 使用 DINOv2 相似度删除冗余帧；
- 再用文本引导保留与问题有关的高分辨率 token；
- 根据帧间依赖进一步压缩空间 token。

VKP 暂不吸收：

- DINOv2/CLIP 会新增本地模型与显存要求；
- 当前门控的目标是低成本、可审计和不依赖额外大模型；
- 将来如轻量门控召回率不足，可把 embedding gate 作为显式可选 profile。

## VKP 最终门控顺序

1. 读取既有 Timeline、OCR、ASR、Qinglong、质量问题和 PySceneDetect 边界。
2. 对 temporal 帧组做本地主内容区域变化检查，遮蔽右下角讲师小窗。
3. 高置信且结构完整的简单页面停止在本地 OCR。
4. 低置信或结构缺失的页面继续 ebook/crop OCR/tile。
5. 复杂关系版式、非文本信息或跨来源冲突升级为单帧多模态。
6. 只有主内容真实变化或存在场景边界时，才升级为 temporal 多模态。
7. 相邻重复页面保留一个代表帧，其他候选记录 `duplicate_of_index` 且估算调用数为零。
8. 本地证据执行后再次 triage；只有剩余候选进入 preflight。
9. preflight/consent/allowlist 仍是联网前的唯一授权链；门控不能授权上传。

## 实现映射

- `src/video_knowledge_pipeline/vision_escalation_gate.py`
  - OCR 置信度；
  - 复杂版式和非文本信号；
  - 场景边界匹配；
  - 主内容变化；
  - dHash/OCR 文本近重复；
  - 调用与图像数估算。
- `src/video_knowledge_pipeline/vision_review_triage.py`
  - 复用原有分数和 route；
  - 生成 v2 审计字段；
  - 应用重复候选抑制。
- `src/video_knowledge_pipeline/targeted_visual_evidence.py`
  - 本地 OCR/版式阶段后重新 triage；
  - 分开记录 pre-local 与 post-local 数量。

## 已知限制

- Pillow 灰度差不是 SSIM，对渐变、摄像机抖动和局部动画的鲁棒性较弱；
- 右下角讲师遮罩是默认经验区域，非右下角画中画可能仍需显式布局元数据；
- 复杂版式判断目前是结构字段、标签和文本信号，不是学习型分类器；
- dHash 只用于候选去重，不用于删除原始帧、Timeline 或证据；
- 任何读取失败都会返回 `not_available`，不会自动联网或静默 fallback。
