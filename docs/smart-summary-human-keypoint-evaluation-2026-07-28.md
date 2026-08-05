# Smart Summary 人工关键点稳定评估

- 状态：已实现，等待真实人工 gold set
- 执行工具 / 模型：Codex（GPT-5）
- 更新时间：2026-07-28 20:52:50 +08:00
- 生效模块：`smart-summary-quality-check`
- 不在范围：自动生成关键点、修改逐字稿、改写总结、外部事实核验、在线模型调用

## 结论

Smart Summary 质量门不再只给出一个不可解释的字符二元组召回率。它现在读取结构化人工关键点，逐条输出匹配方法、分数、命中摘录、时间范围、证据 ID 和数值证据状态。

词面变化由固定源码版本的 Jieba 与 RapidFuzz 处理；真正的语义同义关系只接受人工提供的 `aliases`。这意味着系统可以容忍标点、分词和语序变化，但不会把“看起来像”当作“意思相同”。

## 变更 1：固定并实际运行成熟开源模块

- 意图：复用成熟的中文分词和字符串检索实现，避免自研第二套模糊匹配算法。
- 决策：
  - Jieba `v0.42.1`，commit `1e20c89b66f56c9301b0feed211733ffaa1bd72a`；
  - RapidFuzz `v3.14.5`，commit `edf9f3c2d016c878dae1511301f8b4a501bba871`。
- 理由：Jieba 已提供准确模式 `lcut(..., HMM=False)`；RapidFuzz 已提供 `process.extractOne`、`fuzz.token_set_ratio` 和 `fuzz.WRatio`，无需复制其索引、剪枝或编辑距离实现。
- 证据：
  - RapidFuzz 官方源码定向测试：10 passed；
  - Jieba 固定源码直接导入并完成中文 `lcut(..., HMM=False)` smoke；
  - 本地运行版本分别为 Jieba `0.42.1`、RapidFuzz `3.14.5`。
- 生效范围：仅本地 Smart Summary 人工 gold-set 召回评估；不改变 ASR、OCR、Timeline、总结正文或 provider gateway。

固定源码：

- `%WORKSPACE_ROOT%\source-reviews\vkp-summary-evaluation-wave-20260728\jieba`
- `%WORKSPACE_ROOT%\source-reviews\vkp-summary-evaluation-wave-20260728\RapidFuzz`

## 变更 2：结构化 gold set 与逐项决策

- 意图：让“人工关键点召回率”可复核、可追踪，而不是只有一个总分。
- 决策：增加 `video_knowledge_pipeline.human_key_points.v2` 输入约定，并输出 `video_knowledge_pipeline.smart_summary_key_point_recall.v2`。
- 理由：字符串列表无法表达同义写法、时间范围和证据来源，也无法解释漏掉的是哪一条。
- 证据：回归覆盖显式 alias、时间范围、evidence IDs、gold-set SHA-256、错误 Schema fail-closed。
- 生效范围：继续兼容旧字符串列表；新字段只增强评估证据，不修改现有用户内容。

推荐的 `exports\human-key-points.json`：

```json
{
  "schema": "video_knowledge_pipeline.human_key_points.v2",
  "key_points": [
    {
      "id": "kp-0001",
      "text": "孩子不带身故责任",
      "aliases": [
        "儿童方案不含身故责任"
      ],
      "time_range": "00:48:00.000 - 00:49:00.000",
      "evidence_ids": [
        "segment-0048"
      ],
      "source_kind": "human_confirmed"
    }
  ]
}
```

`aliases` 是人工确认的语义等价表达，不由模糊匹配自动推断。若没有人工确认，应保持漏检或进入复核，而不是把相似句强行算作命中。

## 变更 3：中文语序匹配与兼容路径

- 意图：识别“先确认需求再制定方案”与“制定方案前先确认需求”这类词序变化。
- 决策：
  1. 先做规范化后的原文 / alias 精确包含；
  2. 再以 Jieba `HMM=False` 分词并用 RapidFuzz `token_set_ratio`，阈值 90；
  3. 再用 RapidFuzz `WRatio`，阈值 88；
  4. 最后保留原有字符二元组召回阈值 0.60，维持旧 gold set 兼容。
- 理由：token-set 能处理词序变化，WRatio 能处理局部编辑差异；字符二元组只作为旧行为兼容，不承担语义判断。
- 证据：中文重排样例命中 `jieba_rapidfuzz_token_set`；只共享“医疗险”等通用词的反例保持不命中。
- 生效范围：只对一个总结内部的人工关键点覆盖率打分；不自动新增或删除总结事实。

## 变更 4：数值冲突继续 fail-closed

- 意图：避免“2 万元”和“5 万元”因为其他文字相似而被判成同一关键点。
- 决策：复用 VKP 现有 `numeric_normalization.number_evidence_map`，人工关键点含有数值时，摘要必须包含同一单位归一化后的数值证据。
- 理由：模糊字符串分数不能覆盖数值差异；数字是总结最需要保守处理的字段之一。
- 证据：回归中的错误金额虽然词面高度相似，仍返回 `numeric_evidence_missing`。
- 生效范围：只阻断关键点命中；不会自行纠正、替换或猜测数字。

## 变更 5：依赖与兼容性

- 意图：所有安装模式得到相同、可复现的质量门结果。
- 决策：将 `jieba>=0.42.1,<1` 与 `rapidfuzz>=3.14.5,<4` 加入基础运行依赖，不放入本地模型或在线网关 extra。
- 理由：Smart Summary 质量检查属于核心业务能力，不能因操作者选择 `core`、`online` 或 `hybrid` 而悄悄换算法。
- 证据：安装矩阵与 Smart Summary、Knowledge Export 回归均通过。
- 生效范围：增加两个不含模型权重的小型 Python 依赖；不安装本地大模型、LiteLLM 服务或数据库。

Jieba 仍会从其 `_compat.py` 发出 `pkg_resources` 弃用警告。这是固定上游的已知兼容性提示，不影响当前输出；后续升级前需重新跑分词 gold set，不能静默替换。

## 验证结果

- RapidFuzz 上游定向测试：10 passed。
- VKP 新增定向与集成测试：13 passed。
- Smart Summary 关联回归：47 passed。
- Knowledge Export 回归：33 passed。
- Ruff：通过。
- AST 解析：通过。
- 真实 Bundle `--no-write`：
  - `每天都有客户主动咨询的秘诀`：保持 `blocked_missing_human_key_points`；
  - `2026年7月24日全国大早会`：保持 `blocked_missing_human_key_points`。

最后两项是预期的 fail-closed 行为：实现已经可用，但尚未提供独立人工关键点 gold set，因此不能把既有总结误报为“已完成人工召回验证”。

## 使用方式

1. 将人工关键点保存到：

```text
<bundle>\exports\human-key-points.json
```

2. 只读预检：

```powershell
.\video-knowledge.ps1 smart-summary-quality-check `
  '<bundle>' `
  --summary-path '<bundle>\exports\smart-summary.codex.md' `
  --require-codex `
  --no-write
```

3. 审核 `quality_metrics.human_key_point_recall.decisions[]`，确认漏检项、匹配方法、证据 ID 和数值证据。

4. 只有人工 gold set 已独立提供且召回率达到现有门槛 `0.85` 时，质量门才允许进入 production-ready 判断。
