# VKP ASR、说话人、embedding 与 quick-health 公开提交审计

- Dispatch：`GITHUB-AUDIT-VKP-20260815-01`
- Work ID：`WL-20260815-163326-723a7b`
- 审计时间：2026-08-15 21:55:08 +08:00
- 执行工具/模型：Codex (GPT-5.6 Sol)
- 审计基线：`2518b118cd9c945535428807af6d1de1f570bbc8`
- 审计代码终点：`0f4dffca1174e97968fb59120de5af6ee567d2d5`
- 状态：公开职责、离线回归、包内容和敏感信息门已通过；非强制推送与远端回读在本文件提交后执行

## 提交拆分

| 提交 | 职责 | 公开边界 |
| --- | --- | --- |
| `0b4cf1a8fd24dac2febe53b3da45392ddc52ee18` | 长媒体 ASR 证据完整性 | 分块 ID、可解码视频时长、原始 ASR lineage 与边界降级门；不含音视频或逐字稿 |
| `cd62ceaacdd693c46be2fb2478ce6cc7be80a10b` | 粤语细节候选与三人匿名说话人候选 | 复用 Qwen3-ASR、FunASR CAM++ 与 SpectralCluster；只提交适配、合成测试和候选合同 |
| `c169f437f5c4c66831ffc443c9ce1a22c94e59b8` | bounded quick health | 只检查静态入口、Schema、配置和工件哈希；不加载 ASR、Torch、CUDA 或 Provider |
| `77978eef62eb9ff1f71e24cfbf20757172da1c25` | 本地 embedding 统一网关候选 | 复用 model-provider-gateway Owner execution；向量、模型、Key 与真实资料不进入回执或 Git |
| `0f4dffca1174e97968fb59120de5af6ee567d2d5` | 审计回归修复 | 复用 VKP 唯一流式文件哈希 owner，并使 Qwen 合成 fixture 显式声明模型已就绪 |

## 源码复用与许可证

| 来源 | 固定版本 | 复用裁决 |
| --- | --- | --- |
| Qwen3-ASR | `7c6daf77a2421100f5fb066495372c00129d39ff`，Apache-2.0 | 复用上游 `language="Cantonese"`、`context` 和 `transcribe` 合同；不复制推理代码或权重 |
| ModelScope FunASR | `1.3.30` / `16cd165ac3946cc8c08bf845331f91fefec8e1a9`，MIT | 复用 CAM++ 输出与 `SpectralCluster`；不重写声纹模型 |
| model-provider-gateway | `6575c8089d5f28ae159a0c01cedfa3320db7d7b3`，AGPL-3.0-only | 复用 Owner manifest、plan、gate、receipt 和 error 合同；不复制 Provider SDK 或 secret 管理 |

`THIRD_PARTY_NOTICES.md` 和外部复用账本已更新。SOURCE_INVENTORY 全局校验为 `error_count=0`；100 条 warning 是全局账本中既有缺失/归档来源提示，不由本次提交引入。

## 验证证据

- clean clone 全量 pytest：`1698 passed / 10 skipped / 0 failed`，耗时 281.72 秒；receipt SHA-256 `d415b37cfe3f05ed32edfa51c7d9f5c932a78a6df85150c8f8e125f5d9606a51`。
- ASR/说话人专项：`125 passed`；embedding/quick-health：`15 passed / 1 skipped`；全量发现项修复专项：`19 passed / 1 skipped`。
- 本轮 25 个 Python 文件：Ruff `All checks passed`；9 个新增文件：Ruff format `already formatted`。
- 仓库全量 Ruff 仍有既存 `925` 项（733 个 F401、162 个 E402 等）；本轮未扩大范围机械改写历史文件，本轮变更文件零新增 Ruff 问题。
- wheel 离线构建通过，大小 `1,937,933` 字节；含 quick-health Schema、CAM++/共享说话人和 embedding adapter；不含 DashScope 候选、媒体、模型、`.local` 或运行输出。
- publication safety 已随 clean clone 全量测试通过；新增行 secret shape `0`、个人绝对路径 `0`。四个文件中的 `.local`/媒体后缀字样仅为安全边界、忽略规则或运行时路径说明，不是被跟踪的产物。
- `git diff --check` 通过；Windows LF→CRLF 提示不是内容错误。

## 明确排除的本地改动

以下内容保留在原工作树，未暂存、未提交、未打入 wheel：

- `src/video_knowledge_pipeline/model_provider_catalog.py`
- `src/video_knowledge_pipeline/model_provider_onboarding.py`
- `src/video_knowledge_pipeline/online_model_gateway.py`
- `tests/test_model_provider_catalog.py`
- `tests/test_model_provider_onboarding.py`
- `src/video_knowledge_pipeline/dashscope_filetrans_adapter.py`
- `scripts/run-tests-managed.ps1`
- `agent-tool-manifest.v1.json`
- `tests/test_asr_pipeline.py` 的本机状态记录（无内容 diff）

排除理由：这些分别属于未完成的 Provider/DashScope 路线、本机固定路径 wrapper、未知并发 manifest 或无内容状态；混入会破坏职责拆分或公开可复现性。

## 变更理由与回滚

### AUDIT-ASR-01

- 意图：让长媒体转录在分块、恢复和视频音频尾长不一致时保持可追溯。
- 决策：分块 segment ID 加命名空间，帧抽取采用可解码视频流时长，质量门沿 lineage 找到原始 ASR 并单独报告边界降级。
- 理由：重复 ID 会覆盖下游段落，容器时长会产生越界抽帧，浅层 lineage 会掩盖 degraded 原始回执。
- 证据：专项回归与 clean clone 全量测试通过。
- 生效范围：ASR 派生证据、抽帧时间边界和只读完整性诊断；不改逐字稿正文。
- 回滚：revert `0b4cf1a8fd24dac2febe53b3da45392ddc52ee18`。

### AUDIT-SPEAKER-02

- 意图：提高粤语细节候选质量，并把分块局部说话人投影为跨片段稳定的匿名候选。
- 决策：使用固定 Qwen3-ASR、CAM++ 与 FunASR SpectralCluster；低纯度和未听审结果保持 candidate-only。
- 理由：不能用普通话翻译反猜粤语原文，也不能把声纹相似度冒充真人身份。
- 证据：12/12 本地 Qwen 候选和 92 个声纹样本的既有执行证据；公开回归只使用合成 fixture。
- 生效范围：候选 A/B、匿名三簇和人工复核输入；不覆盖 canonical transcript 或真人角色。
- 回滚：revert `cd62ceaacdd693c46be2fb2478ce6cc7be80a10b`，私有 sidecar 可独立删除。

### AUDIT-HEALTH-03

- 意图：让 Registry 健康检查稳定低于 20 秒，同时保留真实 ASR 诊断。
- 决策：增加标准库 quick-health 早期入口；`asr-env-status` 保持 detailed 语义。
- 理由：频繁静态健康检查不需要加载 Torch/CUDA/模型缓存。
- 证据：五次包装器约 64–103 ms；负例、幂等、Schema、wheel 与全量测试通过。
- 生效范围：健康控制面；不证明模型或 GPU ready。
- 回滚：revert `c169f437f5c4c66831ffc443c9ce1a22c94e59b8`。

### AUDIT-EMBED-04

- 意图：让本地 embedding 复用统一网关语义，且不泄漏向量或本机模型路径。
- 决策：薄 adapter 只接受 synthetic/public fixture，绑定 manifest/route/gate/receipt/hash，禁止重试和 fallback；依赖固定到实际包含 Owner 合同的 Gateway 提交。
- 理由：旧固定提交没有所需模块，clone 用户会导入失败；自建执行协议会形成第二套网关。
- 证据：正负例、输入/模型/维度/route drift、超时和无 fallback 测试通过；wheel 内容已核验。
- 生效范围：本地候选 embedding；不写生产索引、不调用在线 Provider。
- 回滚：revert `77978eef62eb9ff1f71e24cfbf20757172da1c25` 和 `0f4dffca1174e97968fb59120de5af6ee567d2d5`。

## 仍未通过的真实运行与跨平台边界

- Qwen3-ASR 的 12 个高难片段尚无人工盲听真值，`model_switch_allowed=false`。
- 三人匿名说话人候选仍有低纯度分组，不能自动绑定“采访者/客户/家属”或跨视频认定身份。
- embedding 真实隔离 runtime/model 未配置，真实 smoke 按设计跳过；Recall@5/10 未验证。
- quick-health 不证明 ASR、GPU、模型缓存或 Provider ready；详细诊断仍由 `asr-env-status` 承担。
- 本轮只在当前 Windows 环境做真实执行；Linux/macOS 的可选模型运行时尚未做 E2E。
- 不调用真实 Provider、不读取 Key、不上传媒体、不启动常驻服务、不修改 MCP/代理/Docker。
