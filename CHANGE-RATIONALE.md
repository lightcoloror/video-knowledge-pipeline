# Change rationale

## 2026-08-16 15:21:15 +08:00 | Codex (GPT-5.6 Sol) | generic content clip retrieval and post-cut verification

### CR-20260816-02 — Generalized content clip workflow

- 意图：把采访原声检索泛化为课程解释、教程、视觉/屏幕/声音事件、B-roll、高光和故事节拍的统一能力。
- 决策：复用既有 VideoRAG、moment index、transcript reference window、technical shots、OCR/temporal evidence、旧 script alignment 和 Workbench；新增版本化 profile、四个通用合同、两个薄入口及 clip-only 多模态门。
- 理由：不同内容类型需要不同证据和边界，但不需要第二套索引、FFmpeg、ASR、OCR、Provider 或状态机。
- 证据：固定上游源码已实际读取；moys editor timing 64/64；通用与旧采访 focused 14/14、相关模块 40/40；真实 Bundle 两类通用请求 dry-run 对缺视觉/shot 证据 fail-closed。
- 生效范围：Bundle 派生 candidate/review/alignment/repair artifacts；始终 `publication_allowed=false`。
- 回滚方式：停用新命令并删除派生文件；旧 `script-clip-*`、Timeline、canonical transcript、媒体与上游证据保持不变。
- 详细记录：`docs/content-clip-retrieval-and-alignment-v1-2026-08-16.md`。

## 2026-08-16 13:40:00 +08:00 | Codex (GPT-5.6 Sol) | script-to-interview-clip review closure

### CR-20260816-01 — Local candidate retrieval and post-cut truth gate

- 意图：按已审核脚本定位采访原声，并阻止“源视频说过”被误当成“剪后片段仍完整包含”。
- 决策：复用 VideoRAG、moment index、transcript reference window、transcript parser、Bundle lock、run registry 和 Workbench；新增三个独立合同、两个 CLI/MCP 薄入口和 clip-only ASR 对齐门。
- 理由：现有模块已拥有检索、时间证据和来源 lineage；这里只应增加人工审核编排，不能复制索引、转写或状态机。
- 证据：合成测试覆盖本地候选、hash drift、CLI/MCP/Workbench、相邻说话人半开边界和全部 12 类一致性故障。
- 生效范围：Bundle 派生候选、review TODO、alignment report 和 repair TODO；`publication_allowed=false`。
- 回滚方式：停止调用并删除这些派生文件；源视频、精剪文件、脚本、canonical transcript、Timeline 和 speaker sidecar 均不变。
- 详细记录：`docs/script-clip-alignment-workflow-2026-08-16.md`。

## 2026-08-10 19:16:59 +08:00 | Codex (GPT-5.6 Sol) | real-Bundle subtitle compatibility closure

### CR-20260810-05 — Registered media reuse and ambiguous chunk lineage

- 意图：让真实分块采访 Bundle 能直接进入字幕编辑器，同时不把错误绑定或 ASR 重叠静默写入正式字幕。
- 决策：字幕页与 Review Server 复用 lecture review 既有媒体选择顺序，只解析 manifest/source-package 已登记引用，不扫描邻近目录；重复的分块 segment/source ID 仅在编辑投影中增加确定性 occurrence lineage，原 ID 保留；原始重叠允许进入草稿并标为 `overlap_requires_review`，正式 apply 继续要求时间单调且无重叠。
- 理由：真实 Bundle 把媒体登记在 `lecture-package.json sources[].path`，且分块 ASR 会重启局部 ID、保留少量交叠窗口；直接拒绝无法编辑，自动裁边或猜媒体又会破坏证据。
- 证据：两个真实采访 Bundle `--no-write` 预检分别生成 15 段/0 重叠和 469 段/2 重叠投影；新增 source-package、重复 ID、重叠未修复阻断与修复后通过回归；相关套件 31/31（含 Chrome Playwright 2/2）。
- 生效范围：本地 review media 解析、`subtitle_editor_projection.v1` 的附加 lineage/timing-review 字段和人工字幕正式写回门；原始 ASR、Timeline、媒体、翻译及真实 Bundle 均未修改。
- 回滚方式：恢复只接受 manifest 直连媒体并重新生成投影；原始输入始终保留，已生成的旧草稿会因 projection SHA 变化而拒绝覆盖。

## 2026-08-10 18:42:00 +08:00 | Codex (GPT-5.6 Sol) | moys-asr-workflow subtitle editor integration

### CR-20260810-01 — Fixed upstream editor shell

- 意图：复用成熟字幕播放器、波形、列表、快捷键、拆分合并、撤销、批量替换和导出交互。
- 决策：固定 `Moyf/moys-asr-workflow` v1.3.1 commit `949bc84058cdae1d9c021c50203e6d2742f9392c`，仅引入八个 `web/` 根资源；七个原文件保持逐字节一致，模板仅增加两个 adapter 插槽。
- 理由：避免重写已经过上游测试的编辑算法，同时排除 Provider、Key、ASR、桌面壳和第二套服务器。
- 证据：上游 JavaScript 定向测试 92/92；固定文件 SHA-256 对比 7/7 一致；`SOURCE_INVENTORY.json` 已登记。
- 生效范围：`static/moys-subtitle-editor/` 和独立字幕编辑页。
- 回滚方式：删除该静态目录与新路由；旧 `transcript-editor.html` 保持可用。

### CR-20260810-02 — Evidence-preserving dual-track projection

- 意图：让粤语原文与普通话翻译共享时间边界，并保留 segment lineage、全局匿名说话人、字级时间戳与 evidence IDs。
- 决策：新增 `subtitle_editor_projection.v1`；时间统一为整数毫秒；Bundle 媒体时长进入稳定哈希；缺翻译保持空轨。
- 理由：上游项目文件不能替代 VKP 的 canonical transcript、Timeline 或翻译 sidecar。
- 证据：投影双跑幂等、毫秒转换、媒体边界、缺翻译和全局说话人测试。
- 生效范围：只读编辑投影和浏览器草稿。
- 回滚方式：停止生成 `subtitle-editor-project.json`，原始 Bundle 不受影响。

### CR-20260810-03 — Explicit loopback apply and immutable sources

- 意图：区分自动保存草稿与正式写回，避免旧页面、跨源请求或漂移输入覆盖 Bundle。
- 决策：复用 Review Server 的 loopback Host、CSRF、Origin、请求上限和 `/media` Range；正式应用还校验 projection/source hash、来源顺序、媒体边界、说话人及人工确认；写回工具栏固定锚定上游顶层 `body > h1`，不命中隐藏面板的局部 header。
- 理由：浏览器 localStorage 不是执行授权，字幕边界也不应反写原始 ASR 时间。
- 证据：本地 HTTP roundtrip、损坏 JSON、重复 ID、越界时间、跨说话人合并和 hash drift 负例；Playwright 合成 Bundle 草稿恢复/apply/revision conflict 2/2 通过。
- 生效范围：人工确认字幕 sidecar、双轨字幕和 apply receipt。
- 回滚方式：移除新增 Review Server 路由；原始 ASR、翻译和 Timeline SHA 保持不变。

### CR-20260810-04 — Derived export plans and downstream freshness

- 意图：把人工字幕结果交给后续流程，同时禁止自动剪片或伪造完整翻译。
- 决策：生成 SRT/VTT/ASS、OTIO、FFconcat 和 kept-ranges 派生计划；普通话字幕仅在每个有效段均有文本时生成；静音区仅 `removed=true` 时纳入；Smart Summary、最终合并文档和字幕导出标记 stale。
- 理由：导出计划可复核但不授予执行权限；人工文字变化会使下游语义产物过期。
- 证据：源 SHA 不变、缺翻译、不显式删除静音区、manifest 与 run registry 测试。
- 生效范围：Bundle 派生输出，不调用在线模型，不执行 FFmpeg。
- 回滚方式：停止消费人工 sidecar并重新从 canonical transcript 生成派生产物。

## 2026-08-05 13:51:38 +08:00 | Codex (GPT-5.6) | Public repository compliance closure

### CR-20260805-01 — Third-party attribution

- 意图：让公开使用者能区分 VKP 自有代码、随仓库分发的资产、安装依赖、独立工具、模型和数据。
- 决策：新增 `NOTICE` 与 `THIRD_PARTY_NOTICES.md`；保留 WaveSurfer.js 的随包许可证，并链接 commit 级复用总账。
- 理由：根许可证不能替代第三方许可证，Apache/MIT/BSD 代码、模型权重和数据集也不能混为同一授权。
- 证据：`pyproject.toml`、`SOURCE_INVENTORY.json`、固定源码 LICENSE、`docs/external-code-reuse-ledger-2026-07-04.md`。
- 生效范围：公开源码分发与安装说明；不改变运行时路线或第三方条款。
- 回滚方式：若归属字段有误，修正对应表行并保留上游许可证；不得直接删除必要通知。

### CR-20260805-02 — Security reporting and data boundary

- 意图：避免漏洞和敏感样本通过公开 Issue 再次泄露。
- 决策：新增 `SECURITY.md`，指定 GitHub 私密漏洞报告入口和 VKP 的凭据、外发、模型、媒体边界。
- 理由：公开仓库需要一个不依赖聊天历史的安全报告合同。
- 证据：Trusted Broker/consent 架构、公开仓库脱敏规则和本次 secret/privacy 扫描。
- 生效范围：漏洞报告与贡献者指引；不授权任何模型调用或数据上传。
- 回滚方式：可更新报告渠道，但必须始终保留一个不要求公开敏感细节的入口。

### CR-20260805-03 — Customer-derived fixture de-identification

- 意图：不在公开源码中保留真实客户录音标题和录音级人工纠词。
- 决策：从生产候选词表移除四条录音专用纠词；把测试和审计文档中的同一案例替换为合成双人项目访谈与合成纠词。
- 理由：这些内容没有姓名或电话，但仍是客户/保险场景派生数据；测试只需要验证时间戳、说话人和来源绑定，不需要真实词面。
- 证据：公开根提交隐私扫描定位到来源保真测试、最终 reader E2E 和相关审计文档；本地 human-confirmed 产物不受影响。
- 生效范围：公开源码、测试夹具和文档；不修改本地 Bundle、canonical transcript 或用户确认结果。
- 回滚方式：仅可换成另一组合成夹具；不得恢复真实客户词面。

### CR-20260805-04 — Local-only and generated artifact ignore rules

- 意图：防止未知空文件、本机计划、凭据、模型、媒体和生成逐字稿被误提交。
- 决策：扩展 `.gitignore`，精确忽略当前四个 owner-local 文件，并覆盖常见密钥、音频、模型权重和生产输出名。
- 理由：这些文件可重建、仅用于本机调度或属于敏感运行数据；用户明确要求不删除、不提交未知未跟踪文件。
- 证据：`git status --short`、文件大小/SHA 分类和 `tests/test_publication_safety.py`。
- 生效范围：Git 跟踪候选；不删除、不移动、不修改被忽略文件。
- 回滚方式：需要发布某个合成 fixture 时，用明确路径例外并先通过 publication safety 测试。

### CR-20260805-05 — Publication regression gates

- 意图：防止后续提交重新带入密钥、客户样本、模型、媒体或缺失归属文件。
- 决策：扩展 `tests/test_publication_safety.py`，只扫描 Git 跟踪快照并对合规文件和 vendored license 建硬门。
- 理由：一次性人工扫描不能保护后续提交。
- 证据：当前快照 765 个文本 blob 的零 secret 命中；私有历史仅发现已知绝对路径，无 token/key/证件号/手机号命中。
- 生效范围：离线测试与公开提交；不读取 `.local`、媒体目录或用户凭据。
- 回滚方式：只允许用更严格或等价的扫描器替代，不能无替代删除门禁。

## 2026-08-15 23:31:04 +08:00 | Codex (GPT-5.6 Sol) | Clone-portable VKP

### CR-20260815-01 — Canonical portable Python front door

- 意图：让公开克隆在 Windows/Linux/macOS 合同下发现并校验 VKP，而不要求 PowerShell、本机端口、模型或相邻仓库。
- 决策：新增 `video-knowledge-portable` Python CLI、`agent-tool-manifest.v1`、本地 Schemas、合成 Bundle fixture 和哈希绑定 smoke receipt；PowerShell 只保留为可选 Windows wrapper。
- 理由：发现、合成合同验收和真实 ASR/Provider readiness 是不同事实，不能由一个本机脚本混为“已可用”。
- 证据：portable/quick-health 定向回归 18/18；doctor 与 smoke 双跑幂等；输出不含主机绝对路径。
- 生效范围：只读 discovery、静态 doctor、合成 material-manifest 与本地 receipt 验证。
- 回滚：删除 portable 入口、manifest/Schemas/fixture；原 CLI、MCP、Bundle、Timeline 和 PowerShell wrapper 不变。

### CR-20260815-02 — Semantic Gateway compatibility and portable secret references

- 意图：消除与某个 Gateway Git SHA 和 Windows DPAPI 的不必要运行耦合。
- 决策：共享 Gateway 依赖改为 `>=0.3,<0.4`，再校验 `model_provider_gateway.adapter_contract.v2`、VKP Broker policy、capability/consent/safety 语义；跨平台 secret 仅声明 env/keyring 引用，DPAPI 标为 Windows legacy adapter。
- 理由：提交号用于 provenance；真正影响安全执行的是协议、Schema、能力和授权语义。
- 证据：兼容和不兼容 adapter 负例、exact shared contract bundle SHA 验证、无 secret 读取断言。
- 生效范围：可选 Gateway mock 与共享包安装；不改 VKP Broker/consent 真源，不授权在线调用或 fallback。
- 回滚：恢复旧 optional dependency 声明；不会改变本地 Bundle 或凭据存储。

### CR-20260815-03 — Source-reviewed uv and Task orchestration

- 意图：提供跨平台、单命令、可审计的安装与离线验证入口。
- 决策：复用 uv 的 project/environment 语义与 go-task 的本地 Taskfile；只有 `bootstrap` 可解析依赖，doctor/smoke/validate 强制 `--offline --no-sync`。不使用 remote include 或 `--insecure`。
- 理由：避免重新实现包管理和任务运行器，也避免“离线 smoke”暗中联网。
- 证据：uv commit `f1a42680ff5272232d65748acf338b19778dde24`、Task commit `1868ad29698bb336ba76f54bbd9d711c2fa08e8d` 的本地源码复审；Taskfile/CI 静态负例。
- 生效范围：开发/CI 编排；uv 与 Task 不随 VKP wheel 分发。
- 回滚：直接使用 Python console/module 命令；生产运行链不受影响。

### CR-20260815-04 — Windows ACL-safe focused tests

- 意图：避免把本机 pytest 全局临时目录的损坏 ACL 误报为 VKP 逻辑失败。
- 决策：portable 定向测试使用唯一、项目旁、显式清理的短生命周期目录，不更改 pytest 全局配置或生产路径。
- 理由：提升权限 pytest 启动器无输出挂起；项目旁目录的创建、读写和删除均可验证且不需要跳过断言。
- 证据：原始错误为 pytest session cleanup `WinError 5`；改造后 18/18 在普通权限下 4.04 秒通过。
- 生效范围：`test_portable.py` 和 `test_quick_health.py` 的合成副本/漂移测试。
- 回滚：当 Windows pytest 临时目录 ACL 稳定后可恢复 `tmp_path`；断言和生产代码无需变化。

### CR-20260815-05 — Cross-platform byte-stable lock artifacts

- 意图：保证 Windows `core.autocrlf`、Linux 和 CI checkout 得到相同的 lock-bound 文件字节。
- 决策：对每个 `portable-contract.lock.v1` artifact 设置精确 `text eol=lf`，并将 `.gitattributes` 自身纳入锁和回归。
- 理由：首次 Windows clean clone 将 LF 转成 CRLF，doctor 因真实 SHA 漂移正确 fail-closed；放宽哈希会掩盖供应链漂移。
- 证据：原工作树 manifest SHA `345504...`，首次 clean clone SHA `072568...`；增加 checkout policy 后要求 clean clone doctor 恢复 ready。
- 生效范围：11 个 portable lock-bound 文本文件的 Git checkout 字节；不修改运行时业务数据或用户全局 Git 配置。
- 回滚：只能以等价的规范化 checkout/内容寻址机制替代；不能单独移除而保留 byte-level lock。

### CR-20260815-06 — Explicit external contract bundle discovery

- 意图：让 clean clone 不依赖开发者机器上的 `public-repos` sibling 目录。
- 决策：生产 doctor 继续只接受显式 `--contract-bundle`；测试通过 `VKP_PORTABLE_CONTRACT_BUNDLE` 注入精确外部快照，未配置时明确 skip。
- 理由：外部 portable contract 是可选分发依赖，不应从目录布局猜测；缺少它不能表现为 import error 或偶然本机成功。
- 证据：第二次 clean clone 的仓内 doctor/smoke 已通过，唯一失败是旧测试的 sibling path；显式传入现有快照可校验固定 SHA。
- 生效范围：外部合同的测试发现方式；仓内 manifest、Schema、smoke 和运行授权语义不变。
- 回滚：可改用包资源或用户选择的下载缓存，但不得恢复固定工作区绝对/相邻路径。

## 2026-08-16 17:20:00 +08:00 | Codex (GPT-5.6 Sol) | DashScope FileTrans consent closure

### CR-20260816-01 — Fixed upstream FileTrans adapter behind Broker reservation

- 意图：复用 `moys-asr-workflow` 的成熟 DashScope 异步 FileTrans 实现，同时禁止从通用 `online-model-api --execute` 绕过 VKP consent。
- 决策：保留固定上游 CLI 作为唯一 Provider 执行器；新增公共薄函数消费既有 Broker runtime grant，adapter 在启动子进程前强制匹配 `consent_id + route_revision + call allowance`，无匹配授权时返回 `consent_required` 且零远程请求。
- 理由：原 adapter 只在 docstring 中假设调用方已预留 consent，实际没有执行层硬门；重新实现上传、轮询和结果转换又会复制上游成熟代码。
- 证据：上游 commit `949bc84058cdae1d9c021c50203e6d2742f9392c` 的 Qwen Audio/FunASR/GUI workflow 离线回归 `56 passed`；VKP adapter、online gateway 与 trusted connector 回归 `35 passed`；无授权、额度耗尽和 timeout 负例均未调用真实 Provider。
- 生效范围：仅 `provider=dashscope_filetrans` 的远程 ASR 候选路线；不改变本地 ASR、OpenAI-compatible ASR、原始逐字稿或自动 fallback 规则。
- 回滚方式：移除 DashScope provider preset/adapter 分支与 runtime grant wrapper；其他 ASR 路线和 Broker 状态不变。
