# 平台官方/半官方视频转文字入口线索

更新时间：2026-07-04 20:20:00 | Codex / GPT-5

## 来源

- 本地归档入口：`%WORKSPACE_ROOT%\tmp\wcf-bilibili-opus-1198975017350594565\243319994b91c9f5\index.html`
- 推荐 Markdown：`%WORKSPACE_ROOT%\tmp\wcf-bilibili-opus-1198975017350594565\243319994b91c9f5\preferred_markdown.md`
- 结构化 JSON：`%WORKSPACE_ROOT%\tmp\wcf-bilibili-opus-1198975017350594565\243319994b91c9f5\structured.json`
- 原始 URL：`https://www.bilibili.com/opus/1198975017350594565`
- 标题：`完全免费！各大平台官方视频转文字＋AI 视频总结方法，知道的人太少了…`

## 抓取质量

Web Content Fetcher 报告显示：

- `Extraction quality: suspect_shell`
- `Login redirect detected: True`
- `Overall content completeness: suspect_incomplete`
- `Quality gate: failed`
- 推荐动作为 `rerun_with_manual_review`

因此这份材料只作为候选线索，不作为最终事实来源。图片和正文看起来基本抓到了核心段落，但存在登录壳、重复导航、图片引用重复等噪音。

## 文章提到的入口

| 平台 | 入口/工具 | 文章说法 | 对 VKP 的意义 |
| --- | --- | --- | --- |
| B站 | 官方 AI 小助手 | 先把视频加入“稍后再看”，再从首页进入稍后再看播放，可能触发 AI 小助手总结 | 可作为人工获取平台摘要的候选入口，但文章称暂不支持导出文案，不能作为自动化主链路 |
| B站/多平台 | GET笔记 APP | 可做视频总结和文案提取，文章称当时免费 | 可作为外部对照组和人工参考；不作为 VKP 自动纠错的 external transcript 证据源 |
| 多平台 | 通义听悟 | 可在线提取视频文案 | 可作为云端 transcript/summary 对照来源，但涉及上传音视频，必须人工确认 |
| 抖音 | 抖音精选 APP | 视频右上角有 AI 功能，可总结或输出逐字稿 | 适合人工补充平台自带字幕/总结，不适合 VKP 自动化绕平台限制 |
| 视频号 | 腾讯元宝 | 将元宝添加为微信联系人后转发视频号，可总结或提取文案 | 仅适合人工操作；VKP 不自动操作微信或联系人 |
| 小红书 | 点点 APP | 复制小红书视频链接到点点，可总结或提取文案 | 可作为人工候选入口；自动化需另行确认边界 |


## 参考分层

这些入口可以新增为参考，但应分成四类，不能混成“可直接复用工具”：

| 层级 | 工具/入口 | 适合做什么 | 不适合做什么 | VKP 接入优先级 |
| --- | --- | --- | --- | --- |
| 平台内人工取证 | B站 AI 小助手、抖音精选 AI | 人工打开原平台，获取平台自己的总结/逐字稿截图或文本 | 自动抓取、绕登录、绕平台限制 | 中 |
| 外部转写/总结对照 | 通义听悟、GET笔记 | 用户手动导出 transcript/summary 后导入 VKP 做对比 | 默认上传私有视频、替代本地 ASR | 高 |
| 私域转发型助手 | 腾讯元宝处理视频号 | 人工转发后获得候选摘要/文案 | 自动操作微信联系人、批量转发 | 低 |
| 第三方 App 入口 | 点点等 App | 某些平台内容的手动补充来源 | 作为稳定 API 或自动化主链路 | 低 |

## 是否值得纳入 VKP

值得纳入，但只纳入为“参考来源”和“外部 sidecar 输入”，不纳入为默认执行工具。

推荐状态：

- `B站 AI 小助手`：加入参考。它最适合校验 B站视频的章节/摘要，但文章说不支持导出文案，所以主要靠人工复制或截图。
- `GET笔记`：加入参考。适合作为多平台 transcript/summary 对照组，但免费状态和导出质量需要定期复核。
- `通义听悟`：加入参考。适合长音视频转写对照，但涉及上传音视频，必须显式人工确认。
- `抖音精选 AI`：加入参考。适合抖音内容的人工作证据补充。
- `腾讯元宝`：谨慎加入。它需要微信转发/联系人路径，不适合作为 VKP 自动化动作。
- `点点`：谨慎加入。可作为小红书外部摘要候选，但稳定性和导出格式未知。

## 建议的数据结构

导入这些外部结果时，统一写成 sidecar：

```json
{
  "schema": "video_knowledge_pipeline.external_ai_note.v1",
  "source_name": "tongyi_tingwu",
  "source_type": "external_ai_note_for_benchmark",
  "source_url_or_note": "manual export",
  "created_by": "human",
  "requires_review": true,
  "allowed_to_override_asr": false,
  "allowed_as_semantic_correction_evidence": false,
  "allowed_to_override_visual": false,
  "content": {
    "transcript": "",
    "summary": "",
    "chapters": []
  },
  "evidence": {
    "exported_file": "",
    "screenshots": [],
    "operator_note": ""
  }
}
```

VKP 后续只做三件事：

1. 对齐：把外部 transcript/summary 对齐到本地 ASR timeline，仅用于评测和人工参考。
2. 比较：找出术语、数字、章节、结论差异，帮助定位 VKP 的弱项。
3. 提醒：把差异进入人工 review 或评测报告，不直接进入自动 semantic correction，不直接覆盖。

## 对 VKP 的策略影响

1. VKP 可以支持“外部 transcript / 外部摘要 / 平台 AI 摘要”作为 benchmark/reference sidecar 输入，但不能把 GET笔记/得到大脑这类外部 AI 结果当作自动纠错证据。
2. 这些外部结果必须标注来源和可信度，例如：`source_type=platform_ai_summary`、`source_fact_status=candidate`、`requires_review=true`。
3. 外部平台摘要不能直接覆盖本地证据链，也不能自动参与 semantic correction，只能参与评测和人工对比：
   - 和本地 ASR 对齐，发现专有名词差异。
   - 和 OCR/多模态结果对比，发现漏掉的屏幕信息。
   - 和 smart-summary 对比，评估 VKP 总结是否漏掉章节。
4. 涉及上传音视频到云端、转发到聊天联系人、使用平台登录态的入口，必须人工确认。
5. VKP 不应绕登录、验证码、平台限制，也不应把这些平台工具变成默认自动执行步骤。

## 建议新增能力

后续可以补一个轻量入口：`import-external-video-ai-note`。

输入：

- 外部 transcript 文件：txt/srt/json/markdown
- 外部摘要文件：markdown/json
- 来源字段：B站 AI 小助手、GET笔记、通义听悟、抖音精选、元宝、点点、其他
- 是否人工确认：true/false

输出：

- `external-ai-notes/<source>.json`
- timeline 对齐候选
- 术语差异报告
- smart-summary 对比报告

默认行为：只导入和对比，不覆盖 ASR/OCR/多模态结果。

## 当前不做的事

- 不自动登录平台。
- 不自动转发视频给微信/元宝。
- 不自动上传私有视频到通义听悟或第三方 APP。
- 不把平台 AI 总结当作已验证事实。
