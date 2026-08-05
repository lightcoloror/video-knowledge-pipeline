# VKP 在线模型评测结果索引

## 2026-07-18 20:16:26 | Codex (GPT-5)

- Action: 将本地真实调用评测整理为可安全版本化、可推送的结果集。
- Scope: 免费/试用候选任务适配、火山 Coding Plan Stage B、Ark 与 SiliconFlow 同系列能力上限对比。
- Evidence status: 真实调用后的人工复核与规范化指标；单样本结论均为候选证据，不自动改变生产路由。

## 结果入口

| 评测 | 调用规模 | 主要覆盖 | 结果文件 |
|---|---:|---|---|
| 免费/试用候选任务适配 | 27 次，24 成功、3 次 HTTP 429 | ASR、OCR、PPT 版式、单帧、temporal、证据提取、摘要、纠错 | [2026-07-17-free-trial-task-fit.md](2026-07-17-free-trial-task-fit.md) |
| 火山 Coding Plan Stage B | 43 次，43 成功 | 视觉聊天 OCR、单帧语义、双帧 temporal、证据摘要、转录纠错 | [2026-07-17-volcengine-stage-b.md](2026-07-17-volcengine-stage-b.md) |
| Ark 与 SiliconFlow 同系列能力上限 | 10 次，8 个有效内容、2 个失败 | 固定 SQLite 并发代码任务；DeepSeek、GLM、Kimi 配对 | [上级完整报告](../coding-plan-siliconflow-native-parity-2026-07-18.md) |
| 结构化机器摘要 | 上述三组 | 聚合计数、候选结论、限制条件 | [model-evaluation-summary.v1.json](model-evaluation-summary.v1.json) |

其他已版本化的调用证据：

- [在线模型目录验证](../online-model-catalog-verification-2026-07-16.md)
- [在线模型调用方法审计](../online-model-call-method-audit-2026-07-17.md)
- [Ark / SiliconFlow 同模型早期配对](../ark-siliconflow-same-model-parity-2026-07-17.md)

## 安全边界

仓库只保存以下内容：聚合计数、模型名、任务名、规范化延迟、人工质量判断、失败类型和候选排名。

以下原始证据继续留在 `.local/`，不进入 Git：consent 文件、调用 reservation、secret reference、route revision、Windows 绝对路径、完整请求/响应、图片临时编码以及模型思考过程。推送版结果不能用于重放远程调用，也不包含任何凭据。

## 解释边界

- 单样本胜出不等于稳定生产最优；必须增加更多视频、口音、版式与领域样本。
- HTTP 成功只证明路线可调用；只有通过任务 schema 与人工质量门才可进入候选池。
- 供应商未返回费用时，报告标记为 `unknown`，不从预留上限推断实际费用。
- 模型、供应商路由或 route revision 变化后，旧结论只能作为历史参考，并需要新的 consent 才能真实调用。
- Kimi K3、全新通用图像标签器、镜头/场景/高光模型尚未包含在这些远程固定样本结果中。
