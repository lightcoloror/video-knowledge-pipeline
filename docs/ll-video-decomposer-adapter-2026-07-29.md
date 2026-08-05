# ll-video-decomposer → VKP 证据化拆解适配实施

- 更新：2026-07-29 12:11:59
- 执行者：Codex / GPT-5.6
- 上游：`liuliu-66-create/ll-video-decomposer`
- 固定 commit：`8b4d57ce0dc8475751c372c8dc49c1088cee1e69`
- 许可证：MIT
- 本地源码：`%WORKSPACE_ROOT%\source-reviews\ll-video-decomposer-20260729`
- VKP contract：`video_knowledge_pipeline.video_decomposition_report.v1`

## 结论

VKP 已实现只读 producer，视频创作仓已有 consumer。双方共享同一个精确 schema，
不存在第二套字段命名。producer 只读取 Bundle 内已有 Timeline、规范逐字稿、Smart
Summary、OCR/视觉/temporal、页面元数据和 companion courseware；不会解码媒体、执行
ASR、调用模型、联网、上传或写入 run registry。

## 变更台账

| 变更 | 状态 | 意图 | 决策 | 理由 | 证据 | 生效范围 |
| --- | --- | --- | --- | --- | --- | --- |
| `video_decomposition_report.v1` producer | **implemented** | 给视频创作线提供稳定、机器可读的证据化拆解输入 | 独立实现 VKP glue contract；必填字段严格锁定为 `report_id/title/source_artifacts/modality_coverage/findings/structure_segments/creative_strategy/report_sha256` | 下游已锁定 schema，另造字段会形成双轨真源 | VKP 6/6 focused；视频创作 consumer validator 已在 VKP 回归中直接调用通过 | `exports/video-decomposition-report.json/.md`，只读派生层 |
| finding 证据等级 | **implemented** | 阻止报告把猜测写成事实 | 采用 `confirmed/inferred/unavailable`；inferred 至少两个证据，且不能覆盖同维度同时间范围的 confirmed；unavailable 只输出缺失证据 | 上游 evidence-and-confidence-rules 已明确分级纪律 | invalid inference、sensitive gap fake fixture 通过 | finding、structure、creative strategy |
| 输入模态能力门 | **implemented** | 让只有音频、逐字稿或缺少链接结果时的能力边界可执行 | 六类模态全部显式声明 available/unavailable；BGM 曲名、作者身份、幕后信息、播放数据无直接证据时固定 unavailable | “有文字”不能推导镜头、人声、音乐和平台数据 | modality schema + consumer validator 回归通过 | 单报告及 Workbench 状态 |
| 单视频五层投影 | **adapted / implemented** | 保留上游五层报告结构，同时避免生成超出证据的完整营销文案 | 五层只保存 finding/segment 引用；可读 Markdown由同一 JSON 渲染 | JSON 是机器合同，Markdown 是可读投影，避免双份事实 | `single_video_layers`、结构片段测试通过 | Bundle exports，不替换 Smart Summary |
| 多视频同尺度比较 | **adapted / implemented** | 支持 2–4 条横表与 5+ 条可读比较 | 2–4 使用宽表；5+ 使用每条视频卡片 + 三列式维度矩阵 | 上游模板明确禁止 5+ 超宽表 | 5 条 fake Bundle 比较回归通过 | 独立 output dir，不回写任一 Bundle |
| 输入 SHA/freshness | **direct VKP reuse / implemented** | 输入变化后让旧拆解自动失效 | 直接复用 `artifact_freshness.build_dependency_snapshot/validate_dependency_snapshot` 与 canonical JSON SHA | VKP 已有成熟依赖快照，不应另写哈希状态机 | 修改 Timeline 后 status=`stale` 回归通过 | report status、Workbench card |
| 规范逐字稿选择 | **direct VKP reuse / implemented** | 避免拆解层读到较旧 ASR | 把 Smart Summary 既有 precedence 暴露为只读 public selector | 逐字稿真源选择只能有一套 | source-arbitrated 优先级由同一函数执行 | path selection only，不创建或修改逐字稿 |
| Workbench 投影 | **implemented** | 让操作者看见报告及是否过期 | 在现有 artifact cards 增加 JSON/Markdown/status；不建新 UI 服务 | Workbench 已是本地统一入口 | fresh→stale card 回归通过 | 现有静态 Workbench |
| 上游媒体/模型运行时 | **rejected** | 防止出现第二套核心管线 | 不吸收 ASR route/cache、FFmpeg 抽帧/抽音、工具扫描、私有 venv、第二状态机/索引、yt-dlp Chrome cookie | VKP 已有 Timeline/Bundle/run registry/ASR/OCR/provider gateway/单一媒体出口 | 代码中 `source_reuse.rejected_upstream_modules` 固定记录 | 全项目硬边界 |

## 上游源码实测

上游并非只读 README。固定源码已本地运行官方测试：将实际源码目录加入
`PYTHONPATH` 后，`python -m unittest discover -s tests -v` 为 `7/7 OK`。上游测试默认
硬编码 `skills/...` 安装布局，在源码根直接运行会找不到模块；这是上游测试打包路径
问题，不影响本次被吸收的 evidence/template 规则。没有运行上游 ASR、FFmpeg、下载器
或 cookie 获取脚本。

## 稳定入口

```powershell
# 单视频 producer
.\scripts\video-knowledge.ps1 video-decomposition-report '<webui-bundle>'

# 检查输入是否仍 fresh
.\scripts\video-knowledge.ps1 video-decomposition-status '<webui-bundle>' --no-write

# 2 条以上同尺度比较
.\scripts\video-knowledge.ps1 video-decomposition-compare `
  '<report-1.json>' '<report-2.json>' `
  --output-dir '<comparison-output>'
```

consumer 基线：

- `%WORKSPACE_ROOT%\ai-video-tools-20260708\mvp-video-pipeline\src\video_creation_pipeline\decomposition_adoption.py`
- 只有 confirmed structure segment 可以进入 `reference_recipe`。
- inferred 只保持 candidate；unavailable 永远不能自动变成创作指令。

## 产物与真源边界

- producer：`exports/video-decomposition-report.json/.md`
- freshness：`exports/video-decomposition-report-status.json/.md`
- MCP 参数：`mcp-video-decomposition-report.args.json`
- 多视频：`video-decomposition-comparison.json/.md`
- 不修改：`timeline.json`、规范逐字稿、原始 ASR/OCR/视觉证据、run registry、Smart Summary。

## 验证

```powershell
python -m pytest -q tests\test_video_decomposition.py `
  --basetemp C:\tmp\vkp-video-decomposition-pytest-20260729-b `
  -p no:cacheprovider
python -m ruff check --no-cache `
  src\video_knowledge_pipeline\video_decomposition.py `
  src\video_knowledge_pipeline\smart_summary_input_pack.py `
  src\video_knowledge_pipeline\video_workbench.py `
  src\video_knowledge_pipeline\cli.py `
  tests\test_video_decomposition.py
```

- focused：`6 passed`；同时覆盖 2–4 条 `wide_table` 与 5+ 条 `cards_and_matrix`。
- associated：`21 passed`（producer、Workbench、shot breakdown、CLI contract）。
- cross-repo：focused test 直接调用视频创作 consumer validator，contract/hash/source
  artifact 校验通过；消费端自身 `test_decomposition_adoption.py` 为 `6/6 OK`。
- Ruff、`py_compile`、targeted `git diff --check`：通过。
- source ledger：本条 `0` issue；全局校验仍有其他项目既存 `12` errors / `107` issues，未由本轮扩散。

## 剩余真实缺口

1. 尚未在一个正式生产 Bundle 上生成报告并由操作者复核五层可读性；本轮只做离线 fake fixtures。
2. author/metrics/BGM 等 direct-evidence 自动提取仍保守地保持 unavailable；后续只有在现有
   page metadata、可靠识曲或用户材料出现明确字段时才能开放 confirmed。
3. 多视频比较完成了 5 条 fake report 验收，尚缺真实 2–4 与 5+ 样本人工可读性评审。
4. consumer 已能生成 adoption/reference recipe，但本轮没有真实剪辑或发布执行。

## 真实 Bundle 语义保守化验收（2026-07-29 13:12:23）

- 执行者：Codex / GPT-5.6
- 网络/模型/API 调用：`0`
- 真源写入：`0`；只刷新 `exports/video-decomposition-report.*` 和独立比较产物。

### 变更的来龙去脉

| 变更 | 意图 | 决策 | 理由 | 证据 | 生效范围 |
| --- | --- | --- | --- | --- | --- |
| 定位与内容价值文本选择 | 防止把“生成方式/基本信息”或试音当成内容洞察 | 直接复用 `smart_summary_codex._section_text`，定位优先取“核心主题/课程主线”，内容价值优先取“一句话概览”；本模块只做一行 Markdown 清理 | Smart Summary 已有成熟 section 边界解析，重复写 Markdown parser 会形成第二套规则 | 两条真实生产 Bundle 与三条旧 Bundle 均不再输出 `生成方式`、`基本信息`、`能听得见`、`测试测试` 作为定位 | 仅派生报告 claim；不改 Smart Summary、Timeline 或逐字稿 |
| Hook/Payoff fail-closed | 阻止“第一行=Hook、最后一行=Payoff”的假阳性 | 没有显式 Hook/Payoff 分析或人工确认时固定为 `unavailable`；仅有时间顺序不构成语义作用证据 | 上游 `evidence-and-confidence-rules.md` 要求直接证据；真实首行是试音/等待，位置规则不等于语义判断 | 新回归覆盖试音开场与礼貌收尾；5/5 真实报告 Hook/Payoff 均保守为 unavailable | finding 与 creative strategy；不会生成未证实 reusable framework |
| 正文节点命名 | 保留可回看能力但不冒充语义章节 | 现有均匀时间样本改称“时间证据锚点”，并明确“不等同于已确认语义章节” | 这些片段有真实时间戳和原文，但没有转折/作用分析 | 5 个真实 Bundle 均保留 5 个可回看锚点；消费者仍只读取 confirmed 原始片段 | `structure_segments` 标签和 body_structure 说明；不改 consumer schema |
| 源码账本状态保护 | 防止真实验收后误升为稳定工具 | 保持 `review_status=reviewed_selected`、`integration_status=local_trial`，只更新下一步边界 | producer 已通过真实只读验证，但专业 Hook/Payoff、创作采纳和人工评审尚未完成，不应写成 stable/integrated tool | 更新前备份 SHA `4bbaa1bc3bd6…`；500 条 entry 逐项比较，非目标 entry 变化 `0` | `SOURCE_INVENTORY.json` 中 ll-video-decomposer 单条 `next_action` |

### 真实验收结果

| Bundle | source artifacts | confirmed / inferred / unavailable | freshness | 输入 SHA 变化 |
| --- | ---: | ---: | --- | ---: |
| 每天都有客户主动咨询的秘诀 | 92 | 9 / 1 / 8 | fresh | 0 |
| 2026年7月24日全国大早会 | 202 | 10 / 1 / 8 | fresh | 0 |
| 首次沟通环节的高频问题 | 55 | 8 / 1 / 9 | fresh | 0 |
| 20250306 没客户？通过活动来获客 | 5 | 8 / 0 / 9 | fresh | 0 |
| 从小红书引流300+到成交 | 3 | 8 / 0 / 9 | fresh | 0 |

比较产物：

- 两条：`%WORKSPACE_ROOT%\outputs\vkp-video-decomposition-real-validation-20260729\two-report-comparison`，`layout=wide_table`，2 卡片，21 维。
- 五条：`%WORKSPACE_ROOT%\outputs\vkp-video-decomposition-real-validation-20260729\five-report-comparison`，`layout=cards_and_matrix`，5 卡片，21 维。
- 逐 Bundle 验证：`%WORKSPACE_ROOT%\outputs\vkp-video-decomposition-real-validation-20260729\real-bundle-validation.json`。
- SOURCE_INVENTORY 更新前备份：`%WORKSPACE_ROOT%\outputs\vkp-video-decomposition-real-validation-20260729\SOURCE_INVENTORY.before-ll-video-final-4bbaa1bc3bd6.json`。

### 前文剩余缺口的状态修正

1. “尚未在正式 Bundle 验收”已关闭：5 条真实 Bundle 全部 fresh，输入证据 SHA 无变化。
2. “缺真实 2–4 与 5+ 比较”已关闭：2 条和 5 条布局均已落盘验证。
3. 仍保留：Hook、Payoff、作用解释需要显式语义证据或人工确认；目前不能用位置规则补写。
4. 仍保留：时间证据锚点不是语义章节；若以后需要专业拉片 Body，应消费已验证的章节/场景作用证据，而不是在本 producer 内再造分段模型。
5. 仍保留：consumer 的真实创作采纳、剪辑或发布不属于本轮；自动发布继续禁止。