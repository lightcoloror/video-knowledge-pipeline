# VKP 公开克隆跨平台入口与边界（2026-08-15）

Updated: 2026-08-15 23:31:04 +08:00 by Codex (GPT-5.6 Sol)

## 结论

VKP 现在有一个不依赖 PowerShell 的标准 Python 发现入口和一个只消费合成 Bundle 的离线 smoke。它验证“代码、Schema、manifest、哈希、material-manifest 适配和可选 Gateway loopback mock”是否一致，但不把这种一致性伪装成模型、ASR 或在线 Provider 已可用。

```text
agent-tool-manifest.v1.json
  -> video-knowledge-portable doctor
  -> bundled synthetic Bundle
  -> existing material-manifest.v1 adapter
  -> portable-smoke-receipt.v1 + artifact hashes
  -> validate-smoke
```

所有 metadata 都是 `notTrustedAsInstruction` / `none_metadata_only`。它不提供执行授权。

## 单命令入口

首次准备隔离环境：

```bash
uv sync --project portability
```

此步骤可能访问 Python 包索引。准备完成后，以下入口强制离线且不再同步依赖：

```bash
uv run --project portability --offline --no-sync video-knowledge-portable doctor
uv run --project portability --offline --no-sync video-knowledge-portable smoke --output-dir .local/portable-smoke
uv run --project portability --offline --no-sync video-knowledge-portable validate-smoke --run-root .local/portable-smoke
```

没有 uv 或 Task 时仍可使用：

```bash
python -m video_knowledge_pipeline.portable doctor
python -m video_knowledge_pipeline.quick_health
```

要在本机额外验证外部分发合同包，可设置 `VKP_PORTABLE_CONTRACT_BUNDLE`，或直接向 doctor 传入 `--contract-bundle <file> --require-contract-bundle`。默认不猜测工作区 sibling 路径；缺少外部合同包只影响显式 contract import，不影响仓内 metadata discovery。

`Taskfile.yml` 只是上述命令的薄编排层；没有远程 include，也不使用不安全模式。

## 兼容性与来源

| 项目 | 决策 | 证据 |
|---|---|---|
| portable contract bundle | 固定 Schema/版本/内容 SHA，而非依赖工作区 sibling | SHA-256 `e7315a36f66687ab1f807dfc908ed21932d5eee543bbb2775b74d2c50ca4d0b0` |
| model-provider-gateway | `>=0.3,<0.4` + `adapter_contract.v2` + Broker/consent/security 语义 | exact commit 仅保留为 provenance，不是运行硬门 |
| uv | 复用隔离项目与离线运行语义，不自研包管理器 | source-reviewed `f1a42680ff5272232d65748acf338b19778dde24` |
| go-task | 复用本地 Taskfile 命令编排，不自研任务运行器 | source-reviewed `1868ad29698bb336ba76f54bbd9d711c2fa08e8d` |
| secret reference | env/keyring 跨平台；DPAPI 仅 Windows legacy | Gateway 0.3 contract/source tests；doctor 不读取 secret |

本次不新增 Provider SDK、ASR、视频处理、状态机或长期服务。

## 平台真值

| 平台 | 当前状态 | 可以声称什么 | 不能声称什么 |
|---|---|---|---|
| Windows | `verified_current_host` | Python doctor、合成 smoke、哈希验证已本机运行 | 不证明本地模型或在线 Provider 可用 |
| Linux | `static_contract_and_ci_matrix_only` | 路径/Schema/CI workflow 已生成 | 在 GitHub workflow 真正执行前不能称 real runner passed |
| macOS | `not_run` | manifest 宣告合同支持 | 没有运行证据 |

`--platform linux` 只改变目标标签；运行证据始终按实际主机生成，防止在 Windows 上伪造 Linux 验收。

## 能力真值

| 能力 | portable doctor 状态 | 边界 |
|---|---|---|
| manifest discovery | ready | 仅发现，不授权执行 |
| synthetic video understanding | ready_offline_fixture | 只使用合成 Timeline/逐字稿/帧占位文件 |
| Gateway mock | compatible 或 blocked_optional_dependency | ephemeral loopback；不调用 Provider |
| local ASR | optional_runtime_not_evaluated | 由详细 ASR doctor 另行判断 |
| Cantonese ASR | candidate_only_human_truth_missing | 不晋级正式路线 |
| embedding | candidate_only_runtime_not_verified | 不晋级生产索引 |
| speaker identity | anonymous_candidates_only | 不允许真人身份推断 |
| online Provider | blocked_missing_explicit_consent | 不读取 Key、不上传 |
| TTS / digital avatar | paused_not_promoted | 用户暂停，不恢复 |

## 失败恢复

- manifest/Schema/版本/哈希漂移：doctor 返回 `not_ready`，修复相应文件或重新安装同一版本；不自动覆盖。
- smoke 产物缺失或哈希漂移：`validate-smoke` 失败。删除该合成 smoke 目录后可重建；不会影响业务 Bundle。
- Git checkout 行尾漂移：所有 lock-bound 文本由仓库 `.gitattributes` 固定为 LF；不要通过忽略或规范化哈希绕过真实 byte drift。
- 可选 Gateway 缺失：默认保留 `blocked_optional_dependency`；只有显式 `--require-gateway-mock` 才阻断。
- portable contract bundle 缺失：metadata discovery 可继续；显式要求 contract import 时 fail-closed。
- pytest Windows ACL：定向测试使用项目旁唯一目录并严格清理，不降低断言或静默跳过。

## 变更的意图 / 决策 / 理由 / 证据 / 生效范围

完整记录见根目录 `CHANGE-RATIONALE.md` 的 `CR-20260815-01` 至 `CR-20260815-05`。本次生效范围只包含公开克隆发现、合成 smoke、薄编排、Schema 和测试；不修改真实 Bundle、Timeline、ASR、Provider gateway、consent、MCP、代理、Docker 或计划任务。

## 回滚

移除 `video-knowledge-portable` console entry、`portable.py`、portable Schemas/fixture、manifest/lock、Taskfile、portable uv project 和 CI workflow即可。已有 `video-knowledge`、`video-knowledge-mcp`、PowerShell wrapper、Bundle 与授权体系保持独立，不需要数据迁移。
