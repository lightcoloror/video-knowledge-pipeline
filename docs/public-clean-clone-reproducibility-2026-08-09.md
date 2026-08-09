# VKP 公开克隆可复现性收敛（2026-08-09）

执行者：Codex（GPT-5.6）
时间：2026-08-09

## 目标与基线

公开提交 `c92bd7505348f6c9cc0482c4538283f7411ece5a` 的第二批 clean-clone 基线为 `1486 passed / 112 failed / 5 skipped`。本轮只处理公开克隆的离线可复现性，不下载模型、不启动服务、不调用 Provider，也不依赖兄弟仓库。

## 变更记录

### REPRO-01：LiteLLM 缺失时 fail-closed

- 意图：让最小 core 安装可以运行状态、CLI 和离线测试，而不是在检测可选 Proxy 时崩溃。
- 决策：复用 Python `importlib.util.find_spec`，增加可选模块安全探测；父包缺失时返回 `blocked`，并给出 `optional_dependency_missing:litellm`。
- 理由：基线 112 个失败中有 102 个直接来自 `ModuleNotFoundError: litellm`，另有级联失败。
- 证据：独立 clean-clone 首轮复现；定向回归覆盖父包缺失。
- 生效范围：`model-gateway doctor/status` 的依赖诊断；不改变在线执行、路由或 consent。
- 回滚：恢复 `model_gateway.py` 的原模块探测并删除对应回归测试。

### REPRO-02：公开安装与测试 extras

- 意图：让克隆用户无需猜测构建后端和测试依赖。
- 决策：声明 setuptools build backend，并新增 `test`、`dev` extras；保留现有 `core/local/online/hybrid/evaluation` 分层。
- 理由：原 `pyproject.toml` 没有显式 build-system，也没有与公开测试契约对应的 extra；MCP/Pillow 在收集阶段才暴露为缺失。
- 证据：第二批 clean-clone 报告及 `tests/test_install_matrix.py`。
- 生效范围：安装元数据和 README；不把 LiteLLM、模型权重或本地 GPU 运行时加入 core。
- 回滚：删除 build-system 与 test/dev extras，不影响业务产物格式。

### REPRO-03：可选依赖和固定源码显式 skip/block

- 意图：区分“核心回归失败”和“未安装可选能力”。
- 决策：Hugging Face cache scanner、Lighthouse 源码与 ruptures smoke 在依赖不存在时显式 skip；生产 `ruptures` 路线只接受固定 `1.1.10`，已审查 vendor/source 不完整时拒绝隐式切换。
- 理由：公开克隆不应要求存在工作区外的固定源码目录，也不应因缺少模型缓存扫描器而 import error。
- 证据：9 个残余失败中的 5 个属于可选依赖、固定源码或环境能力缺失。
- 生效范围：本地场景结构、MOSS cache readiness、Lighthouse smoke；核心管线保持可运行。
- 回滚：恢复固定兄弟路径断言；这会重新引入公开克隆偶然本机成功问题。

### REPRO-04：测试隔离而不放宽生产安全门

- 意图：使测试只验证目标行为，不绕过文件根目录、端口、调用额度和无自动下载门。
- 决策：provider parity fixture 显式绑定临时 project root；gateway 端口测试显式模拟 LiteLLM 已安装；OmniShotCut 缺权重测试使用合成源码目录；Windows multiprocessing IPC 不可创建时显式 skip。
- 理由：这些失败来自外部 basetemp 或受管 Windows IPC，不代表应放宽生产 allowed-root、reservation 或 checkpoint 规则。
- 证据：独立 clean-clone 的 9 项失败栈及定向回归。
- 生效范围：离线测试；生产安全策略不变。
- 回滚：还原对应测试夹具，不影响运行时代码。

### REPRO-05：拼音后端降级合同

- 意图：保证显式术语别名在没有 `pypinyin` 时仍可纠错，同时不伪称拼音相似能力可用。
- 决策：测试固定 `unavailable_explicit_alias_only`，继续验证精确别名候选；不把 `pypinyin` 提升为 core 依赖。
- 理由：精确别名不依赖拼音；只有模糊音近匹配需要该可选库。
- 证据：clean-clone 中候选生成正确，只有后端名称旧断言失败。
- 生效范围：实体词库离线测试与能力说明；无自动改写范围扩张。
- 回滚：将 `pypinyin` 加入 core 并恢复强制断言，但会扩大最小安装。

## 边界

- 所有验证使用合成 fixture、loopback 或本地文件。
- 没有真实 Provider、Key、媒体上传、模型下载、服务启动或 consent 生成。
- 可选能力缺失只允许 `blocked`/`skipped`，不得自动跨 Provider 或 local/cloud fallback。
- 并发中的拉片 v2 文件不属于本轮 checkpoint；本轮只选择性提交可复现性变更。
