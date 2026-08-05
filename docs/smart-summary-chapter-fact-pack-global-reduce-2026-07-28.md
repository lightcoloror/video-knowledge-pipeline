# VKP Smart Summary 章节事实包与证据化 Global Reduce

更新时间：2026-07-28 20:20:27 +08:00
执行者：Codex / GPT-5.6

## 结论

VKP 现有 `smart-summary-section-workflow.json` 继续作为章节证据真源，
`smart-summary-section-llm-revisions.json` 继续作为章节改写真源。本轮没有新增第二套
总结状态机，而是在 Global Reduce 前新增一个确定性、内容寻址的只读投影：

`exports/smart-summary-chapter-fact-pack.json`

每章现在显式携带：

- `time_range`
- `facts[].evidence_ids`
- `facts[].source_kinds`
- `facts[].fact_status`
- 完整 `evidence_refs`
- `eligible_evidence_ids` 与 `review_only_evidence_ids`
- Workflow、Revisions、Course Map 的 SHA-256 lineage

`review_gap_not_fact` 只能进入“待复核点 / 低置信内容”。如果模型把其中的原文候选
提升到其他确定性栏目，`review_gap_not_promoted` 本地质量门会使 Reduce 失败。
这里检查的是“来源证据状态”，不是判断讲者保险观点在外部世界是否真实。

## 固定上游与源码级复用

| 项目 | 本地源码 / 固定 commit | 实际阅读与运行 | 决策 |
| --- | --- | --- | --- |
| LlamaIndex `TreeSummarize` | `%WORKSPACE_ROOT%\reference-repos\bookwiki-mainline\llama_index` @ `d8d7ffbb119a481147856392bba5bca549283030` | 完整阅读 `llama-index-core/llama_index/core/response_synthesizers/tree_summarize.py` 与对应 `tests/indices/response/test_tree_summarize.py`；本机已安装 `llama-index-core 0.14.10` 的 `TreeSummarize + MockLLM` 离线 smoke 通过 | 吸收“叶节点事实包 → repack → 递归 Reduce → 单一最终节点”的架构边界；不把 LlamaIndex 引入 VKP 生产依赖 |
| VKP Section Workflow | repository-native | 已有 citations、semantic correction evidence、时间范围、候选/复核状态 | 直接复用为事实包来源，不复制证据抽取器 |
| VKP Global Reduce | repository-native | 已有章节完整性、均衡压缩、晚段不丢失、候选复用与质量形状门 | 只增加证据投影、重打包和输出硬门 |

固定上游精确测试在当前环境收集前被缺少的 `pytest-asyncio` 与 `tinytag` 阻断；
没有为了本轮自动安装依赖。该阻断与 VKP 测试分开记录，不能写成“上游精确测试通过”。
本机已安装版本的最小 smoke 仅证明接口可运行，不冒充固定 commit 的完整测试。

直接导入 LlamaIndex 生产模块被拒绝，原因是：

1. VKP 已有 provider gateway、章节 Workflow、Bundle 和恢复状态；
2. 为接入 LlamaIndex LLM 抽象还需新增一层模型适配和依赖版本约束；
3. 这会产生第二个路由/回调边界，却不会增加新的事实证据；
4. 复用其 repack/recursive Reduce 架构、保留 VKP 既有真源更小、更可维护。

## 变更五字段记录

| 变更 | 意图 | 决策 | 理由 | 证据 | 生效范围 |
| --- | --- | --- | --- | --- | --- |
| 章节事实包投影 | 让全局总结能回链到章节证据 | 从现有 Workflow citations 与 semantic correction items 投影 `smart_summary_chapter_fact_pack.v1` | 章节 Markdown 本身没有显式 `evidence_id/source_kind`，Global Reduce 会丢失 lineage | 新增两组 fact-pack 回归；两个真实 Bundle 均识别全部章节和证据引用 | Smart Summary Global Reduce 输入与审计产物；不改逐字稿、Timeline 或章节真源 |
| Evidence status 隔离 | 防止疑似内容成为确定事实 | 分开 `candidate_evidence`、`review_gap_not_fact`、`legacy_unbound`；review-only ID 不进入 eligible 集合 | 低置信候选和缺证据内容不能因模型改写而升级 | 测试证明 `gap-0001`、`semcorr-0002` 不进入事实 eligible ID；缺证据数字保持 review-only | Global Reduce 的事实资格与提示边界 |
| Review-gap 输出硬门 | 不只依赖模型遵循提示 | 检测 review-only fact/ref 的原文是否出现在“待复核点”之前；出现即质量失败 | 提示约束不是确定性保证 | 2 个输出门回归：确定栏目出现时失败，仅在待复核栏目时通过 | Reduce candidate 安装前质量门；不做外部事实核查 |
| Section evidence group repack | 降低长课程重复 token，不删证据 | 每章生成一个内容寻址的 evidence set；facts 引用组 ID，组再列出精确成员 ID | 11 章 × 13 facts 重复 8 个长 ID 会把提示推到 9 万字符以上 | 极端 11 章夹具在 60,000 字符预算内保留全部章节；真实 11 章 Bundle 为 57,945 字符 | 仅 Reduce prompt；完整成员仍保存在事实包 |
| 紧凑 JSON 与均衡压缩 | 复用 TreeSummarize repack 思路并保持晚段 | prompt 使用 compact JSON；超预算时仍沿用现有逐章均衡头尾保留 | pretty JSON 的空白不是内容，不能挤占模型上下文 | 原有晚段不丢失回归继续通过；真实 6 章 Bundle 无压缩 39,314 字符 | Global Reduce prompt，不改变模型或费用授权 |
| 内容寻址 lineage | 防止旧事实包静默匹配新章节 | revision 绑定 Workflow、Revisions、Course Map SHA-256 和事实包内容 | 章节或证据变化后旧 Reduce 输入必须可识别为不同版本 | revision 为稳定 64 位 SHA-256；manifest 登记 schema/revision/summary | Bundle 本地审计与 freshness 识别 |
| 讲者原意边界 | 避免把摘要变成外部事实裁判 | Prompt 明确 `candidate_evidence` 只代表来源内证据；主观评价归因给讲者 | 用户目标是还原录音/视频原意，而非核查保险结论真伪 | prompt 与 operator boundary 回归均覆盖“不做外部事实裁判” | Smart Summary 生成语义；不改 ASR 文本 |

## 机器可读合同

简化结构：

```json
{
  "schema": "video_knowledge_pipeline.smart_summary_chapter_fact_pack.v1",
  "revision": "<sha256>",
  "sections": [
    {
      "section_id": "chapter-0001",
      "time_range": "00:00:00.000 - 00:07:08.430",
      "evidence_status": "evidence_bound",
      "facts": [
        {
          "fact_type": "key_points",
          "text": "...",
          "time_range": "...",
          "evidence_ids": ["chapter-0001:eligible-evidence-set"],
          "source_kinds": ["asr", "visual"],
          "fact_status": "candidate_evidence"
        }
      ],
      "evidence_refs": [
        {
          "evidence_id": "chapter-0001:eligible-evidence-set",
          "source_kind": "evidence_group",
          "member_evidence_ids": ["moment-0001", "rag-visual-evidence-..."]
        }
      ]
    }
  ]
}
```

完整事实包保留 snippet、来源路径和所有成员。传给模型的紧凑视图删除重复的
`fact_id` 和格式空白，但不删除章节、事实文本、时间范围、证据组、成员 ID 或状态。

## 验证

离线回归：

```powershell
python -m pytest -q `
  tests/test_smart_summary_global_reduce_fact_pack.py `
  tests/test_smart_summary_global_reduce_repack_budget.py `
  tests/test_smart_summary_global_reduce_review_gap_gate.py `
  tests/test_phase17_reuse_closure.py
```

结果：`18 passed`。

扩展 Smart Summary 回归：

```powershell
python -m pytest -q `
  tests/test_smart_summary_llm_rewrite.py `
  tests/test_quality_finalize.py `
  tests/test_smart_summary_quality_evidence.py `
  tests/test_smart_summary_global_reduce_fact_pack.py `
  tests/test_smart_summary_global_reduce_repack_budget.py `
  tests/test_smart_summary_global_reduce_review_gap_gate.py `
  tests/test_phase17_reuse_closure.py
```

结果：`42 passed`。

真实 Bundle 结构 smoke 使用 `execute=False, write=False`，没有模型调用或生产写入：

| Bundle | 章节 | 证据引用（含组） | Reduce 输入 | 状态 |
| --- | ---: | ---: | ---: | --- |
| `每天都有客户主动咨询的秘诀` | 6/6 | 65 | 39,314 chars | `planned`，预算内，未压缩章节 |
| `2026年7月24日全国大早会` | 11/11 | 99 | 57,945 chars | `planned`，预算内，未压缩章节 |

## 兼容性与剩余边界

- 旧 Workflow 没有 citations 时不会伪造证据；章节状态为 `legacy_unbound`，只能作为
  review-only 输入。preview 保持兼容，不会静默跨模型或跨路由 fallback。
- 事实与 citation 当前是“章节级候选绑定”，不是逐句法庭级证明；合同显式记录
  `evidence_scope=section_level_group`，不能宣称一条 citation 精确证明整章每个字。
- `review_gap_not_promoted` 目前是确定性精确文本门；大幅同义改写仍需现有数字一致性、
  术语证据和人工关键点质量门共同约束。
- 没有人工关键点 gold set 时，自动检查通过仍不能等同于生产内容合格。
- 本轮没有网络、上传、模型调用、模型下载、provider 切换、生产 Bundle 写入或 push。
