# 最终阅读稿与得到大脑格式对齐

更新时间：2026-07-28 18:57:39 +08:00
执行者：Codex / GPT-5.6

## 结论

VKP 最终交付继续使用一个 Markdown 文档，同时包含“智能总结”和“逐字稿”。
本轮没有建立第二套总结生成器，也没有改变 canonical Smart Summary、证据、
逐字稿、时间戳或质量门。最终阅读稿只是对已经通过质量门的内容做确定性展示
投影：

- `分段总结` → `📅 章节概要`
- `高频话术` → `✨ 金句精选`
- `可执行动作清单` → `📋 待办事项`
- `原始转录` → `逐字稿`
- 保留 `待复核点` 和 `说话人1/说话人2`。
- 去除 reader 不需要的生成方式、schema、provider、route、consent、
  来源状态和仲裁状态等运维字段。

## 复用证据

本轮没有重复拉取源码。复用既有固定源码：

- 项目：BiliNote
- 本地源码：
  `%WORKSPACE_ROOT%\tool-source-review\BiliNote`
- 固定 commit：
  `095d772c7d0f2f4ba1e65c36b7ceb1e2db34723d`
- 实际审查文件：
  `backend/app/gpt/prompt_builder.py`
- 吸收点：同一内容真源支持可选择的 note format/style，时间跳转、截图和
  summary 只是展示/提示选项。
- 拒绝项：不复制 BiliNote 的 prompt 文案，不让展示样式成为第二套
  Summary 真源，不修改其当前脏工作树。

## 变更台账

| 变更 | 意图 | 决策 | 理由 | 证据 | 生效范围 |
| --- | --- | --- | --- | --- | --- |
| canonical heading 投影 | 对齐得到大脑的阅读顺序 | 在 `final_reading_note.py` 中解析既有二级标题并确定性重排 | 再调用模型生成一份“得到大脑版”会造成双真源和事实漂移 | VKP `REQUIRED_HEADINGS`；BiliNote note format/style 架构 | 仅最终 Markdown；不改 canonical summary |
| 运维字段清理 | 去除用户不需要的程序内字段 | 仅过滤独立 metadata 行和通用证据边界提示 | `source_arbitrated_transcript`、`arbitrated_or_reviewed`、route 等属于审计层，不属于正文 | 用户给出的得到大脑样稿与明确删除要求 | 仅 reader projection；JSON、审计报告和质量门继续保留 |
| `逐字稿` 标题 | 准确描述已经过仲裁或人工纠正的最终文本 | 最终文档标题从“原始转录”改为“逐字稿” | 最终文本可能包含 human-confirmed 纠正，称为“原始”会误导 | 当前 source arbitration / semantic correction / speaker E2E | 最终人读文档；机器真源文件名不变 |
| 章节、金句、待办顺序 | 对齐用户熟悉的成品结构 | 固定为章节概要 → 金句精选 → 待办事项 | 只改变阅读顺序，不改任何句子 | 用户提供的得到大脑成品格式 | reader projection |
| 待复核和 speaker 保留 | 维持来源忠实与对话可读性 | `待复核点` 不过滤；逐字稿继续显示匿名说话人 | 用户要求还原音频原意并识别不同说话人，不要求外部事实审查 | MOSS speaker contract 与现有 VKP quality gate | reader 与导出回归；不推断姓名/身份 |

## 验证

- `tests/test_final_reading_note.py` +
  `tests/test_speaker_final_reading_export_e2e.py`：`4 passed`
- 两条现有知识导出回归：`2 passed`
- `ruff check --no-cache`：通过
- `compileall`：通过
- `git diff --check`：通过

全部为本地离线测试；没有模型调用、网络请求、上传或生产 Bundle 重写。

## 兼容性边界

1. `exports/smart-summary.codex.md` 及其 required headings 不变，现有质量门
   不受影响。
2. JSON、审计报告、route/consent 与 source provenance 仍完整保留，只是不在
   最终阅读正文中展示。
3. 非 canonical 的旧 summary 会原样保留正文，仅清理明确的独立运维字段。
4. 下游若硬编码查找 `## 原始转录`，应改为消费机器产物或查找新标题
   `## 逐字稿`；本仓库现有最终阅读稿断言已同步迁移。
## 2026-07-29 Logseq 层级块收口

更新时间：2026-07-29 17:40:55 +08:00
执行者：Codex / GPT-5.6

最终读者文档现在遵循本地 `getnote-logseq-sync` 的 Logseq Markdown 合同：

- 根块为 `摘要` 与 `逐字稿`。
- `摘要 → 📑 智能总结 → 录音信息 / 录音总结 / 章节概要 / 金句 / 待办`。
- 每个子层级使用两个空格和新的 `- ` 块，不保留裸 `# / ## / ###` 标题。
- 逐字稿使用 `说话人 + 起始时间` 父块和正文子块；默认不输出
  `collapsed::` 属性，导入 Logseq 后保持默认展开。
- `处理时间`、`来源路径`、`章节修订来源`、`视觉证据状态` 等只保留在
  canonical/审计产物，不进入最终读者文档。

| 变更 | 意图 | 决策 | 理由 | 证据 | 生效范围 |
| --- | --- | --- | --- | --- | --- |
| Logseq block tree | 让最终文档导入 Logseq 后保留层级 | 复用本地 GetNote 同步工具的二空格块约定，确定性投影现有正文 | 普通 Markdown 标题会在 Logseq API/块导入时展平或形成原始 Markdown continuation | `getnote-logseq-sync/tests/fixtures/logseq-format/good/03-section-hierarchy.md`、`08-transcript-timestamps.md` | 仅 `knowledge-note.md` 最终读者投影 |
| 说话人时间块 | 保留对话定位，并让读者自行控制展开状态 | 匿名说话人映射为稳定颜色标记，父块记录起始时间，正文为子块；默认不写 `collapsed::` | Logseq 默认没有该字段即展开；不应由导出器替用户设定折叠状态 | 用户纠正；双说话人 E2E fixture、canonical cue start/speaker | 只读展示；不改 transcript JSON |
| reader 内部字段过滤 | 避免程序审计字段污染正文 | 只在 `基本信息` reader projection 中过滤固定运维键 | 审计字段必须保留，但不应成为用户阅读内容 | 用户明确删除内部字段；canonical JSON/quality report 仍在 | reader projection，不改证据 |

验证：关联离线测试 `38 passed`；定向 Ruff 与 compileall 通过；本地
`check_logseq_file_format.py --matryca` 对两份真实最终文档检查结果为
`2 checked / 0 issues / 0 round-trip failures`。两份文档仅本地重导出，外部模型
调用、上传和 Logseq 写回均为 0。
