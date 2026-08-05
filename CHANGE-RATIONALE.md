# Change rationale

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
