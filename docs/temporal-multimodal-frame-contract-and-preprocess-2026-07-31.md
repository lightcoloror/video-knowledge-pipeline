# VKP Temporal 多模态帧契约与本地预处理优化

- 更新时间：2026-07-31 19:57:35（Asia/Shanghai）
- 执行工具/模型：Codex / GPT-5.6
- 状态：本地实现与离线回归完成；尚未重新调用真实本地 VLM

## 结论

VKP 现在把“系统已知的帧清单”和“模型观察结果”分开处理。输入中的帧数、帧 ID、文件名和时间戳由 VKP 生成；模型只负责逐帧可见内容与跨帧变化。显式本地视觉路线会发送一张带 `F01` 至 `F08` 标记的 2×4 联系表，并附最多两张高清代表帧；在线路线仍保留原有逐帧发送方式，避免改变既有 consent、上传清单和供应商调用行为。

对既有 6 组、每组 8 帧的纯本地预处理 smoke：

- 原始帧：48 张，5,572,671 字节。
- 模型输入：6 张联系表 + 7 张高清代表帧，共 13 张，1,828,478 字节。
- 预处理图片字节减少约 67.19%，但 48 张原始帧均保留 `frame_mapping`，没有丢失时间覆盖。
- `0199` 检出两个视觉状态并保留两张代表帧；其余五组为一个主要视觉状态。
- 证据：[离线 smoke 报告](%WORKSPACE_ROOT%/outputs/vkp-temporal-preprocess-smoke-20260731/report.json)。

## 本地源码账本与源码级复用判断

### 已复用

1. Pillow 11.0.0
   - 本地源码：`%USERPROFILE%\AppData\Local\Programs\Python\Python313\Lib\site-packages\PIL`
   - `ImageChops.py` SHA-256：`859f043d43e5408cee82c11e755f2dae4297d230420c66fa0acce66ba65e3194`
   - 实际复用：`ImageChops.difference`、`ImageStat.Stat`、`ImageFilter.FIND_EDGES`、`ImageOps.contain`、`ImageDraw.text`。
   - 本地运行证据：6 组真实 temporal 帧已成功生成联系表、代表帧、差异指标与映射。

2. VKP 既有 `vlm_preprocess.py`
   - 继续复用原有图片缩放、JPEG 编码、字节统计与临时路径合同。
   - 没有新增第二套图片编码器。

3. VKP 既有 `video_frame_router.py`
   - 继续由现有路由决定 `document_ocr`、`semantic_frame`、`temporal_sequence`。
   - 新模块只处理已经被路由为 temporal 的帧，不改疑难帧选择真源。

4. `codex-storyboard`
   - 本地源码：`%WORKSPACE_ROOT%\source-reviews\video-workflow-wave-20260722\repos\codex-storyboard`
   - 固定 commit：`ac9057dee3a903eb211d8399a439ae9992e7656a`
   - 复用判断：只吸收“编号面板、代表画面和技术预检”的展示合同；其创作任务状态机和 UI 不进入 VKP。

### 未采用

- ImageHash/pHash：官方 GitHub 源码探测受当前 Windows Git 凭据限制，阿里云与清华镜像下载也未稳定完成；本阶段不引入无法完成源码级验证的新依赖。
- OpenCV `img_hash`/quality：本机 OpenCV 4.11.0 没有对应模块，未为一个小功能额外安装 contrib 运行时。
- Storyboard 项目的任务状态机、生成式分镜和 UI：与 VKP Timeline/Bundle/run registry 重复，明确拒绝。

## 变更决策记录

### 1. 帧清单硬约束

- 意图：阻止模型把 8 帧误写成“四帧”或“若干帧”。
- 决策：为每组生成 `expected_frame_count`、`expected_frame_ids` 和不可变 `frame_manifest`；响应必须返回 `observed_frame_count`、`observed_frame_ids`、`per_frame_observations`。
- 理由：帧数、ID、文件名和时间戳是系统事实，不应让模型重新推断。
- 证据：新增回归模拟模型声称“四帧”，结果必须为 `incomplete/frame_count_claim_mismatch`；正确覆盖 `F01..F08` 才通过。
- 生效范围：所有 temporal 结果都会记录 v2 帧契约；严格逐帧覆盖门当前只对显式本地路线启用，避免破坏已有远程结果兼容性。

### 2. 编号联系表与代表帧

- 意图：降低本地 8B VLM 的图片编码和注意力开销，同时保留时序顺序。
- 决策：本地路线生成 2×4 联系表，每格烧录 `Fxx + 时间戳`；根据 Pillow 差异与清晰度选最多两张高清代表帧。
- 理由：联系表让小模型一次看清数量与顺序；高清代表帧补偿联系表中文字缩小的问题。
- 证据：6 组真实帧由 48 张降为 13 张模型输入，字节减少约 67.19%；全部 48 帧仍有映射。
- 生效范围：仅 `execution_location=local` 的 temporal 路线；远程路线不变。

### 3. 去重但不删证据

- 意图：避免连续静态 PPT 重复占用推理资源。
- 决策：用 Pillow 的灰度差异、变化像素比例和边缘方差形成视觉状态簇；代表帧按清晰度选择，原帧只映射、不删除。
- 理由：这些是成熟、已安装、可审计的图像原语；无需引入新的 pHash/SSIM 运行时。
- 证据：真实组 `0199` 被分成两个状态，其余组保持一个状态；联系表仍显示每个原始时间点。
- 生效范围：仅本地临时 probe 目录和运行审计，不修改 Bundle 原始帧。

### 4. OCR 与 VLM 职责分离

- 意图：减少细小文字、数字和术语的视觉幻觉。
- 决策：提示词明确 OCR 负责标题、正文、数字、表格、术语；VLM 负责动作、空间关系和跨帧变化。无 `frame_id/evidence_frame_paths` 时不得补写细节。
- 理由：已有 OCR 是文字事实源，多模态应补充视觉语义而不是重复低可靠抄字。
- 证据：提示词可读性与必填字段有回归测试；旧乱码提示已替换。
- 生效范围：temporal 分析提示与结果质量门，不改变 OCR 产物。

### 5. 幻觉与一致性质量门

- 意图：错误结果不得进入正式 Timeline 作为合格证据。
- 决策：检查解析失败、缺失 temporal 内容、缺 evidence path、帧数声称冲突、观测帧数/ID 不一致、逐帧观察缺失；失败标记 `validation_status=incomplete`。
- 理由：格式正确不等于语义一致；帧级闭环是可自动验证的最低门槛。
- 证据：4 条新增契约测试通过，相关 temporal/vision 回归通过。
- 生效范围：写回 `temporal_visual_understanding`；不覆盖原始帧、OCR 或 ASR。

### 6. 性能观测

- 意图：区分慢在预处理、模型调用还是输入体积。
- 决策：运行结果记录 `preprocess_ms`、`model_call_ms`、provider latency、total、原始/代表/发送图片数与字节数。
- 理由：只有总耗时无法指导下一轮优化。
- 证据：离线 smoke 已提供图片数和字节基线；正式 runner 已写入 timing 汇总。
- 生效范围：temporal 运行报告与 manifest 审计字段；不含密钥、裸 Base64 或图片内容。

## 兼容性与边界

- 不改变远程 consent 的 artifact 清单，不自动增加或切换供应商。
- 不上传、不调用真实外部模型；本轮只有本地图片读取和离线测试。
- 旧 v1 导入仍可被规范化；严格帧门只在本地新执行结果启用。
- 原始 8 帧、Timeline、OCR、ASR、Bundle 与 run registry 仍是真源。
- 联系表和代表帧是可重建临时 probe，不是新的证据真源。

## 验证

```powershell
py -3.13 -m pytest -q tests\test_temporal_frame_contract.py
py -3.13 -m pytest -q tests\test_temporal_gateway_execution_identity.py tests\test_vision_pipeline.py tests\test_vision_providers.py
py -3.13 -m ruff check src\video_knowledge_pipeline\temporal_frame_preprocess.py src\video_knowledge_pipeline\temporal_visual_analyzer.py tests\test_temporal_frame_contract.py
```

- 新增契约：4 passed。
- 关联 temporal/vision 回归：完成且无失败。
- Ruff：All checks passed。

## 尚未闭环

- 还没有用 LM Studio 对相同 6 组重新做真实生成，因此目前证明了输入缩减和质量门，不宣称视觉内容质量已经提升。
- 当前 adapter 未稳定暴露首 Token 延迟、输入/输出 Token 和 GPU 峰值；本轮只记录可可靠取得的预处理与请求总耗时。
- 若后续加入 pHash/SSIM，应先完成固定源码、许可证、本地测试和依赖矩阵，再替换当前 Pillow 指标，不应并存第二套生产门。
