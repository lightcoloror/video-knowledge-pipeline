# VKP Quick Health 20 秒预算收口

- Dispatch：`VKP-QUICK-HEALTH-BUDGET-20260812-01`
- Work ID：`WL-20260812-122246-2c6ce7`
- 执行工具/模型：Codex (GPT-5.6 Sol)
- 记录时间：`2026-08-12 12:32:18 +08:00`
- 状态：实现与离线验证完成；Registry 修改未授权、未执行

## 结论

新增 `scripts\video-knowledge.ps1 quick-health` 作为 Registry 可用的轻量真实健康入口。它只用 Python 标准库检查项目身份、Python 合同、核心入口、配置 Schema、quick-health Schema 和七个必要工件的实时 SHA-256 快照，不解析本地密钥环境文件，不派生远程目的地，不导入 ASR、Torch、CUDA 或 Provider 栈，也不启动服务。

现有 `asr-env-status` 完整保留，继续负责 Python ASR 环境、命令运行时、模型缓存、Torch/CUDA、FFmpeg 和本地模型准备状态。Quick health 明确输出 `asr_capability_evaluated=false`、`proves_asr_ready=false`，不能被误当成完整 ASR 能力证明。

## 实际耗时证据

### 旧入口

| 阶段 | 实测 |
|---|---:|
| `scripts\video-knowledge.ps1 asr-env-status` | 19,570.38 ms |
| `video_knowledge_pipeline.cli --help` 顶层导入 | 1,016.62 ms |
| 目的地白名单派生 | 139.49 ms |
| `asr_environment` 模块导入 | 135.72 ms |
| `asr_environment_status()` 本体 | 19,029.60 ms |

详细 ASR 本体中的主要耗时：Torch/CUDA 探针 `5,073.52 ms`、默认 ASR 设备探针 `3,090.69 ms`、Qwen3-ASR 1.7B 缓存检查 `5,170.85 ms`、Qwen3-ASR 0.6B 缓存检查 `2,362.59 ms`、MOSS 缓存检查 `2,149.37 ms`。这证明根因是详细能力探测，不是已知功能故障。

### 新入口

五次独立 PowerShell 包装器运行：`149.30 / 92.06 / 90.42 / 94.83 / 100.23 ms`。五次均 `exit=0`、`ok=true`、重模块数为 `0`，快照 SHA-256 均为 `c3158d4f0f1bc6b98e0f9eaa428aa5afe3653c22ab4fd76d8841b8beec6bd65d`。

## 变更理由

### CHG-01：PowerShell 早期分派

- 意图：避免 Registry 健康探针在每次运行时支付完整 ASR 和远程路由准备成本。
- 决策：在环境文件解析和目的地 allowlist 之前识别 `quick-health`，直接调用独立标准库模块。
- 理由：旧入口已逼近并偶尔超过 20 秒预算，而 quick health 不需要密钥、模型或 Provider 信息。
- 证据：旧入口 `19.57 s`；新入口最大 `0.1493 s`。
- 生效范围：只影响新增 `quick-health` 命令；其他 CLI 参数仍进入原完整包装流程。
- 回滚：删除包装器中的 early dispatch；`asr-env-status` 与主 CLI 未被删除。

### CHG-02：版本化 quick-health 合同

- 意图：让注册状态、运行时、可调用性和新鲜度分别可判定，并对损坏输入 fail-closed。
- 决策：新增 `video_knowledge_pipeline.quick_health.v1` 与 JSON Schema；检查 pyproject/package 版本、Python 合同、配置 Schema、CLI/包装器入口及七个工件哈希。
- 理由：单一 `ok` 无法区分“工具入口损坏”和“ASR 模型尚未加载”；实时工件快照又能防止把陈旧缓存当健康。
- 证据：缺目录、损坏配置、Schema 版本漂移、项目身份漂移四类负例均返回 `not_ready`。
- 生效范围：健康检查控制面；不读取业务 Bundle、音视频或模型缓存。
- 回滚：删除模块、Schema 与 console entry；不涉及数据迁移。

### CHG-03：详细 ASR 诊断保持原语义

- 意图：提速不能以删除真实能力检查为代价。
- 决策：保留 `asr-env-status` 原实现和参数；quick health 静态确认其 CLI 路由仍存在，并声明未评估 ASR 能力。
- 理由：模型缓存、CUDA 和命令运行时是诊断信息，但不适合高频 Registry basic health。
- 证据：四项既有 ASR 环境定向回归与六项新增测试合计 `10 passed`。
- 生效范围：`asr-env-status` 仍作为 detailed/diagnostic；建议 Registry basic health 改指 quick health。
- 回滚：Registry 可继续使用旧命令，但会重新承受约 20 秒耗时。

### CHG-04：可打包入口

- 意图：源码检出和 wheel 安装两种使用方式保持一致。
- 决策：增加 `video-knowledge-quick-health` console script，并将 Schema 放入既有 `schemas/*.json` package-data。
- 理由：不能让 quick health 只在开发工作树偶然可用。
- 证据：离线 wheel 构建成功，模块、Schema 和 console entry 均存在。
- 生效范围：Python 包安装入口；不改变 `video-knowledge` 主入口。
- 回滚：删除 pyproject console script；PowerShell 源码入口仍可独立回滚。

## 验证

- 新增 contract/负例/幂等/只读/性能：`6 passed in 0.51s`。
- quick health + 既有 ASR 环境关联回归：`10 passed in 1.30s`，仅有既存 jieba/pkg_resources 弃用警告。
- Ruff：`All checks passed`（`--no-cache`，规避现有 `.ruff_cache` ACL）。
- wheel：离线构建成功；`quick_health.py`、Schema、console entry 全部可见。
- `git diff --check`：通过；只有 Windows LF→CRLF 提示。
- 五次实际包装器：全部小于 `0.15 s`，输出相同快照哈希。
- 运行后驻留进程检查：没有新增 Python 进程。
- JSON 语法与敏感信息/个人路径定向扫描：通过，无匹配。

## 边界与剩余风险

- 未修改 `tool-registry.json`；只生成 `apply_authorized=false` 的最小提案。
- 未启动 8931、MCP、模型网关或 ASR 服务；未下载模型、调用 Provider、上传媒体、读取视频或写业务数据。
- Quick health 证明控制入口完整、当前工件可读且合同相容，不证明本地 ASR、GPU、模型或在线 Provider 可执行。
- 详细 `asr-env-status` 仍约 19 秒；这是保留的诊断成本。后续若优化它，应另做缓存/并行探针设计，不能削弱真实性。
