# VKP 疑难帧多模态门控准确性审计（2026-07-19）

- 执行工具/模型：Codex（GPT-5），Code 工作流
- 审计时间：2026-07-19 15:53:15（Asia/Shanghai）
- Bundle：`openclaw-runs/getbrain-acquisition-20260708/1-首次沟通环节的高频问题/full-vkp-quality-20260713/webui-bundle`
- 执行边界：只读复算 Bundle 与本地图片差分；未调用在线模型、未上传、未改写 Bundle。
- 证据状态：本地像素差分与已写回 Timeline 为机器/既有人工复核证据；不是覆盖 223 项的全量人工真值。

## 结论

修正后的策略比 v1 和初版 v2 更接近“只把真正受益的画面交给多模态”：

1. 不再假设讲师窗口固定在右下角。
2. 只有显式归一化 presenter/PIP/overlay 区域才会被确定性遮罩；位置和尺寸可逐项变化。
3. 无区域元数据时只输出自适应局部运动证据，不自动把局部变化认作讲师。
4. 广域动态变化或 PySceneDetect 边界可进入 temporal；局部运动还必须同时有点击、切换、步骤或演示语义。
5. 没有连续帧证据的候选不再直接进入 temporal 模型，而是进入本地补采样队列。
6. “尚未做 visual understanding”只是缺口，不再被当作模型收益证据；OCR 缺失优先进入本地 ebook/document visual。
7. 近重复页保留连续帧、ASR/OCR 冲突、OCR 内容和收益信号更强的代表，不再机械保留最早一帧。

## 三版结果

| 版本 | semantic 模型候选 | temporal 模型候选 | 本地结构优先 | 本地补采样 | 估计模型调用 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 持久化 v1 | 176 | 24 | 0 | 未建模 | 200 |
| 初版 v2 | 30 | 11 | 6 | 未单列 | 41 |
| 修正版 v2 | 7 | 0 | 29 | 10 | 7 |

相对 v1，估计模型候选由 200 降为 7，减少 96.5%。相对初版 v2，由 41 降为 7，减少 82.9%。这不是单纯按数量裁剪：修正版把 29 个 OCR/结构缺口留在本地，把 10 个无足够连续证据的时序提示留给本地补采样。

初版 v2 的 11 个 temporal 候选全部是 `frame_change_evidence.status=not_available`，因此不能证明需要多帧模型。修正版在本次 Bundle 中没有发现已被本地证据确认的动态 temporal 候选，返回 temporal 0 项，而不是凭旧 route 或操作词猜测。

## 原 6 组 temporal 的一致性核对

既有 Timeline 中 6 组 `temporal_visual_understanding` 均明确记录：主幻灯片静态，变化仅为讲师自然动作，或页面本身是静态流程/诊断图。其中 index 201 还与 199 重复。

| Index | 本地最大整帧差分 | 修正版动作 | 与既有复核结论 |
| ---: | ---: | --- | --- |
| 6 | 0.000784 | semantic multimodal：核对“王飞/王菲”ASR-OCR 姓名冲突 | 一致；不再误用 temporal |
| 80 | 0.000954 | local document visual | 一致；静态案例流程页 |
| 112 | 0.000924 | local document visual | 一致；静态诊断图 |
| 135 | 0.001142 | local document visual | 一致；静态步骤页 |
| 199 | 0.001580 | local document visual | 一致；静态倒推流程页 |
| 201 | 0.000638 | duplicate of 199，抑制 | 一致；既有复核明确判为重复 |

以这 6 组已有逐组复核作为小样本精度代理，修正版对“是否需要 temporal 多模态”的判断为 6/6 一致。index 6 没被整体丢弃，而是降为单帧语义复核，因为它确实能纠正讲师姓名冲突。

## 最终 7 个多模态候选的正向理由

- 19、22：聊天布局 + 讲述明确指向屏幕 + OCR 缺失。
- 147、151：空间关系/连线 + 讲述明确指向屏幕 + OCR 缺失。
- 179：图示与聊天布局并存，OCR 文字不足以表达关系。
- 6、98：ASR 与 OCR 数字/名称冲突，需要视觉仲裁。

没有任何候选只因为“还没分析”而入选。

## 仍需补采样的 10 项

当前 `temporal_recapture_indexes` 为：

`1,7,44,45,88,90,98,119,172,179`

这些项只能先在本地生成连续帧。补采样后再次运行 triage：

- 广域变化、场景边界，或局部变化同时伴随操作语义：可进入 temporal；
- 静态、显式讲师/PIP 区域内变化：抑制 temporal；
- 局部变化但没有操作语义：不自动当讲师，也不自动调用模型。

## 兼容性与局限

- schema 仍为 `video_knowledge_pipeline.vision_review_triage.v2`，保留 v1 字段并新增 `temporal_recapture_indexes`、`temporal_recapture_candidates`、`local_prerequisite_action`。
- 审核队列行为有意收紧：OCR 缺失先走本地结构恢复，远程视觉重试队列只保留已有模型失败项或正向收益证据。
- 本轮 native `view_image` 受 Windows 沙箱 split writable roots 错误阻断；没有改用 Computer Use。画面核对使用用户已提供的 0006 八帧、六组已写回逐帧分析以及本地像素差分。
- 尚未对 223 项建立独立人工标注真值，因此 96.5% 是调用缩减，不是精确率提升百分比；“更准确”的直接证据目前是原 6 组的 6/6 一致与最终候选均具备正向理由。

## 最终验证

- Focused 门控、补采样与审核队列回归：`23 passed, 30 deselected`。
- 完整离线回归：`874 passed, 1 warning`；warning 为既有 `jieba` 对 `pkg_resources` 的弃用提示。
- `python -m compileall -q src`：通过。
- Ruff：本次相关源码及新增/直接相关测试通过。
- `supplemental_frame_sampling` 已消费 `temporal_recapture_candidates`，并在同一项同时存在结构恢复需求时优先保留本地连续帧补采样动作。
- 复核时间：2026-07-19 16:25:14（Asia/Shanghai）；执行工具/模型：Codex（GPT-5），Code 工作流。
