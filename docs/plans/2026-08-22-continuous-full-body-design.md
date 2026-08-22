# VKP 连续正文导出设计

## 用户目标

在现有“智能总结”和“逐字稿”之外增加“正文”模块。用户已选择 A 方案：正文是逐字稿的连续阅读版，只移除时间戳和说话人标签，不摘要、不改写、不漏句。

## 方案决策

- 独立产物固定为 `exports/full-body.md`。
- 最终 `exports/knowledge-note.md` 的阅读顺序固定为“智能总结 → 正文 → 逐字稿”。
- 正文和 `full-transcript.md` 复用同一份最终 cue 来源及相同的连续重复 cue 去重规则。
- 正文只调整空白与段落边界；不补标点、不纠错、不换词、不生成标题。
- 为避免一整篇只有一个超长段落，在不拆分单个 cue 的前提下按目标字符数聚合自然段。
- 当转录完整性门未通过时，正文保留 `review-required` 水印；不得把机器转写伪装成人工校对正文。
- `full-body.md` 进入导出结果、manifest、内容资产索引、运行产物注册和 reader export receipt。
- canonical transcript 存在时，完整逐字稿、连续正文和最终阅读笔记必须由同一回执共同绑定；任一文件缺失或被修改都应阻断 canonical export integrity。

## 被否决方案

- 不采用“将逐字稿改写为文章”的方案：会引入事实漂移和新一轮模型依赖，不符合用户选择的 A 方案。
- 不从渲染后的 `full-transcript.md` 反向解析正文：这会把 Markdown 展示格式变成第二套事实源。
- 不仅把正文嵌入 `knowledge-note.md`：独立文件便于其他工具直接消费，也便于单独做哈希与恢复验证。

## 验收标准

1. 合成 cue 中的每条有效文本按原顺序出现在正文中，除与完整逐字稿一致的连续重复 cue 去重外不丢失。
2. 正文不包含 cue 时间戳和说话人标签。
3. `knowledge-note.md` 中“正文”位于“智能总结”之后、“逐字稿”之前。
4. 导出结果和 manifest 都声明 `full_body_path`，运行注册包含 `full_body`。
5. reader export receipt 记录 `full_body.md` 的 SHA-256；正文被篡改后 canonical integrity 必须失败。
6. 只用 synthetic fixture 验证，不读取真实媒体、不调用本地模型或外部服务。

## 变更记录

- 意图：补齐适合连续阅读和下游正文消费的全文产物。
- 决策：采用确定性 cue 合并，不调用 LLM。
- 理由：保持逐字稿事实完整性，同时消除时间戳/说话人标签造成的阅读中断。
- 证据：现有 `full-transcript.md` 已由 `_full_transcript_source_path` 和 `parse_transcript` 选择最终 cue；现有 reader receipt 已绑定逐字稿与阅读笔记。
- 生效范围：知识笔记导出、阅读笔记展示、导出回执和 canonical 完整性检查。
- 回滚：撤销本次提交即可恢复原有两类阅读产物；不涉及数据迁移或源 transcript 修改。
