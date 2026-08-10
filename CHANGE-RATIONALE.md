# Change rationale

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
