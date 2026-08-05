# 旧模型配置安全导入

## 用途

`video-knowledge-model-gateway import-legacy` 将经过核验的旧 VKP 模型配置迁移为 `local_model_api_settings.v2`，用于避免在设置 UI 中重复手工录入已有的文本与视觉路线。

导入默认只预览：

```powershell
video-knowledge-model-gateway import-legacy --bundle-dir <webui-bundle>
```

只有显式加入 `--execute` 才会写入：

```powershell
video-knowledge-model-gateway import-legacy --bundle-dir <webui-bundle> --execute
```

## 当前支持的来源

- `<bundle>\volcengine-provider-public.json`：只接受 `volcengine_coding_plan` 且目的地为 `ark.cn-beijing.volces.com`。
- `<bundle>\local-vlm-serving-smoke.json`：只接受 loopback `local_qwen_vl` profile。
- `.local\model-connector.env`：只读取认可的 Ark 密钥变量名，值不进入输出。
- `.local\vision.env`：用于识别并明确排除当前不在 Broker allowlist 中的 Agnes 配置。

也可重复传入 `--env-file <path>` 指定项目根目录内的环境文件。Bundle 与环境文件解析后的实际路径必须保持在项目根目录内。

## 安全规则

- 目标设置与 secrets 必须为空；若已存在不同配置，导入器返回 `target_settings_not_empty` 或 `target_secrets_not_empty`，不覆盖操作者修改。
- 对完全相同的已导入配置返回 `already_imported`，不重复写入。
- 密钥在写文件前由 Windows DPAPI 加密；设置、报告和 CLI JSON 只记录 `secret_ref`、变量名与“是否存在”，不记录值。
- settings 与 secrets 分别原子替换；任一写入失败时恢复两份目标文件的原状态。
- 旧 v1 consent、Bundle 中的 consent 文件和过期授权从不导入、刷新或复用。
- 导入只保存配置，不启动 LiteLLM、本地模型或 Broker，不创建 consent，不调用模型，也不授予数据外发权限。
- ASR 与 OCR 不从含混的旧预设中猜测供应商或端口，继续由用户显式配置。

## 本机首次导入结果（2026-07-15）

- profile：`2`（`remote-ark`、`local-qwen-vl`）。
- route pool：`3`（远程 text、远程 vision、本地 vision）。
- task binding：`7`。
- 默认位置：文本与视觉保持 `remote`；本地 Qwen-VL 仅作为显式本地池，服务在线状态未由导入器推断。
- secret ID：仅 `remote-ark`，保存为 DPAPI ciphertext。
- 排除：Agnes、旧 `model-settings.json` 快照、2 份旧 consent。
- 待配置：在线/本地 ASR 与在线 OCR。
- 产物：`.local\model-api-settings.json`、`.local\model-api-secrets.json`、`.local\model-api-legacy-import-report.json`。

## Update Record

### 2026-07-15 09:46:59 | Codex / GPT-5

- Action：新增预览优先、空目标限定、DPAPI 密钥持久化、旧 consent 排除和失败回滚的安全导入路径，并完成本机首次导入。
- Boundary：未启动服务、未调用模型、未上传 artifact、未创建 consent、未写端口记录或 Obsidian。