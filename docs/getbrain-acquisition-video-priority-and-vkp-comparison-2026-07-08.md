# 32 个获客视频文稿优先级、VKP 智能总结与 ASR 对比报告

更新时间：2026-07-08 10:10:00 | 执行：Codex / GPT-5

## 结论先行

- 最值得优先深挖的 3 条不是简单按关键词最高分选，而是覆盖获客链路的三个关键面：线上引流闭环、线下活动获客、首次沟通转化。
- 本地 SenseVoice/FunASR 已完成 3 条视频的 ASR 重跑，且环境显示 CUDA 可用；ASR 输出能覆盖全片并提供更细粒度时间戳。
- 但就“最终人类可读智能总结”而言，当前本地 ASR 直接输入 VKP 的质量低于得到大脑转写输入：主要问题是重复片段更多、标点和段落化弱、术语纠错未完成。
- 得到大脑原始智能总结仍明显更像成品笔记；VKP 当前优势是证据链、可审计路径、可重跑、能接 OCR/视觉/术语仲裁。注意：本次 VKP 输出没有真实执行 Codex/在线 LLM 改写，只是本地结构化草稿，因此不能代表最终 LLM 改写层质量。

## 本次选择的 3 个重点视频

| 优先级 | 视频 | 获客价值 | 本次处理产物 |
|---:|---|---|---|
| 1 | 从小红书引流300+到成交：一套可复制的获客闭环.mp4 | 线上自媒体获客闭环最完整：平台选择、IP定位、爆款笔记、付费咨询、私域承接、成交复盘都有。 | 得到大脑输入 VKP：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\从小红书引流300-到成交-一套可复制的获客闭环\webui-bundle\exports\smart-summary.md`<br>本地 ASR 输入 VKP：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\从小红书引流300-到成交-一套可复制的获客闭环\local-asr-vkp\webui-bundle\exports\smart-summary.md` |
| 2 | 20250306没客户？通过活动来获客-王彩娥.mp4 | 线下活动获客最实战：适合补齐纯线上获客之外的活动设计、亲子场景、社群承接。 | 得到大脑输入 VKP：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\20250306没客户-通过活动来获客-王彩娥\webui-bundle\exports\smart-summary.md`<br>本地 ASR 输入 VKP：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\20250306没客户-通过活动来获客-王彩娥\local-asr-vkp\webui-bundle\exports\smart-summary.md` |
| 3 | 1.首次沟通环节的高频问题.mp4 | 成交转化环节最关键：从获客进入第一次沟通后的信任、异议和问题链处理。 | 得到大脑输入 VKP：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\1-首次沟通环节的高频问题\webui-bundle\exports\smart-summary.md`<br>本地 ASR 输入 VKP：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\1-首次沟通环节的高频问题\local-asr-vkp\webui-bundle\exports\smart-summary.md` |

## 32 个视频分类与排序

评分只用于粗筛，最终选择同时考虑链路互补性。

| 排名 | 分类 | 分数 | 视频 | 时长 | 命中依据 |
|---:|---|---:|---|---|---|
| 1 | 小红书/视频号/自媒体获客 | 2536 | 从小红书引流300+到成交：一套可复制的获客闭环.mp4 | 01:07:26 | 小红书:41、视频号:3、自媒体:2、获客:34、引流:33、成交:24、转化:23、活动:10 |
| 2 | 小红书/视频号/自媒体获客 | 2040 | 6 自媒体拓客秘籍（小红书、视频号）.mp4 | 00:41:08 | 小红书:65、视频号:44、自媒体:24、获客:14、引流:21、私域:7、流程:5、案例:12 |
| 3 | 活动/线下/社群获客 | 1996 | 202409202024年保险人在小红书实现“高效获客、持续变现”!-刘昶贤.mp4 | 01:02:08 | 小红书:41、获客:16、引流:33、成交:2、转化:7、活动:83、线下:10、私域:2 |
| 4 | 活动/线下/社群获客 | 1886 | 20250306没客户？通过活动来获客-王彩娥.mp4 | 01:33:26 | 小红书:1、视频号:2、自媒体:2、获客:11、引流:2、成交:10、转化:15、活动:103 |
| 5 | 活动/线下/社群获客 | 1839 | 20231222用客户的服务链接客户，引爆你的获客量！-石文玉.mp4 | 01:01:51 | 获客:14、引流:4、成交:5、转化:4、活动:110、线下:3、流程:5、案例:1 |
| 6 | 首次沟通/转化/成交 | 1832 | 251104线上获客与团财险实战攻略.mp4 | 00:48:46 | 小红书:27、获客:36、引流:6、成交:28、转化:14、活动:7、线下:5、高频问题:2 |
| 7 | 获客心法/拓客路径 | 1487 | 2025.9.17互联网&线下双轨制获客.mp4 |  | 小红书:20、获客:36、成交:9、转化:2、活动:4、线下:21、话术:5、案例:11 |
| 8 | 活动/线下/社群获客 | 1402 | 20250509如何在小红书获客-王燕燕.mp4 | 00:57:55 | 小红书:27、自媒体:1、获客:8、引流:18、成交:9、活动:35、线下:8、私域:5 |
| 9 | 产品/核保/规则支撑 | 1320 | 2025.12.22我的拓客之路，心法+技法.mp4 | 02:50:14 | 小红书:2、自媒体:5、获客:4、引流:10、成交:26、转化:5、活动:9、线下:4 |
| 10 | 首次沟通/转化/成交 | 1134 | 2025年02期：从心出发--保险新人的松弛感和获客思路.mp4 | 00:39:14 | 小红书:3、视频号:4、获客:7、成交:36、转化:2、活动:7、线下:1、话术:4 |
| 11 | 活动/线下/社群获客 | 934 | 三类活动,批量获客.mp4 | 01:08:06 | 小红书:1、获客:2、引流:3、成交:1、活动:58、线下:11、流程:5、案例:5 |
| 12 | 首次沟通/转化/成交 | 928 | 1.客户特点、成交基本原则、获取信任的相关动作.mp4 | 00:17:47 | 小红书:1、视频号:1、自媒体:2、获客:2、成交:22、转化:4、线下:5、问题链:3 |
| 13 | 首次沟通/转化/成交 | 928 | 2.陌客营销技巧流程与问题链.mp4 | 00:27:27 | 小红书:3、视频号:1、获客:4、成交:3、活动:1、话术:1、问题链:4、首次沟通:12 |
| 14 | 首次沟通/转化/成交 | 919 | 1.首次沟通环节的高频问题.mp4 | 00:17:39 | 小红书:1、获客:1、成交:13、转化:4、话术:10、问题链:1、高频问题:8、首次沟通:5 |
| 15 | 首次沟通/转化/成交 | 849 | 获客不必谈恋爱-曹志华.mp4 | 01:00:14 | 视频号:12、获客:13、引流:9、成交:13、线下:5、私域:2、流程:8、案例:3 |
| 16 | 首次沟通/转化/成交 | 791 | 23年3月15日专题早会 学会拓客，让成交更进一步 匡林艳.mp4 | 00:32:06 | 小红书:7、视频号:5、自媒体:5、成交:33、案例:17、客户:67、信任:2、需求:4 |
| 17 | 首次沟通/转化/成交 | 748 | 2.方案讲解和成交环节高频问题.mp4 | 00:17:17 | 自媒体:1、获客:1、成交:7、转化:3、线下:1、话术:12、高频问题:9、首次沟通:1 |
| 18 | 获客心法/拓客路径 | 727 | 2025年06期：从资源空窗到拓客破局-我的经纪人成长之路.mp4 | 00:52:43 | 引流:2、成交:20、转化:2、活动:3、线下:10、私域:9、话术:2、实战:5 |
| 19 | 获客心法/拓客路径 | 714 | 持续深耕，被动获客.mp4 | 00:42:38 | 小红书:3、视频号:5、自媒体:25、获客:2、成交:10、转化:10、线下:1、案例:3 |
| 20 | 活动/线下/社群获客 | 708 | 财富流沙盘：三步轻松获客.mp4 | 00:46:59 | 获客:2、引流:4、成交:2、转化:4、活动:53、线下:4、流程:6、案例:2 |
| 21 | 工具/系统/后台操作 | 687 | 251230明亚app功能介绍-获客及客经.mp4 | 00:41:43 | 小红书:1、视频号:1、自媒体:5、获客:23、成交:2、活动:6、线下:2、客户:103 |
| 22 | 活动/线下/社群获客 | 664 | 读书会：最“慢”的经营，最快的链接.mp4 | 01:01:58 | 小红书:7、视频号:2、获客:2、引流:2、成交:3、转化:6、活动:33、线下:1 |
| 23 | 产品/核保/规则支撑 | 646 | 【月缴单分享】2024.1.22拓客新模式，月缴保单的魅力.mp4 | 00:39:42 | 视频号:2、成交:20、转化:3、线下:4、案例:6、复盘:4、客户:93、信任:7 |
| 24 | 产品/核保/规则支撑 | 600 | 3.方案制作原则与讲解要点.mp4 | 00:13:54 | 成交:12、线下:2、话术:6、实战:1、流程:5、案例:9、客户:102、信任:4 |
| 25 | 产品/核保/规则支撑 | 367 | 2024-12-6 关于规范宣传推广获客业务操作的通知-业务管理部于淼.mp4 | 00:20:12 | 获客:20、流程:8、客户:55、需求:5 |
| 26 | 产品/核保/规则支撑 | 318 | （0112）成长及拓客方法-三四线城市成长及拓客之路.mp4 | 00:45:52 | 成交:3、转化:2、活动:2、客户:71、需求:11 |
| 27 | 产品/核保/规则支撑 | 307 | 250825【团财专题】雇责从拓客到理赔.mp4 | 00:34:56 | 获客:1、转化:1、线下:1、流程:21、案例:9、客户:36、信任:3、需求:5 |
| 28 | 获客心法/拓客路径 | 302 | 【团财拓客】2025.8.27团财高绩.mp4 | 00:30:27 | 获客:7、成交:3、转化:3、活动:2、线下:5、流程:3、案例:2、客户:25 |
| 29 | 产品/核保/规则支撑 | 256 | 9.26【广东团财手册助力您拓客和增员-刘育清】.mp4 | 00:21:10 | 获客:1、成交:2、线下:2、流程:5、复盘:1、客户:42、信任:2、需求:15 |
| 30 | 首次沟通/转化/成交 | 225 | 【高客专家委员发布】2025.6.16.mp4 | 00:18:31 | 成交:16、实战:2、流程:7、客户:12、信任:2、需求:2 |
| 31 | 工具/系统/后台操作 | 179 | 玄学获客秘籍：25年冲刺，26年开局.mp4 | 01:00:37 | 获客:4、线下:2、客户:37、信任:2、需求:1、社群:1 |
| 32 | 产品/核保/规则支撑 | 162 | 2024-12-18 宣传推广获客业务规则介绍-业管处焦姣.mp4 | 00:18:42 | 获客:9、流程:3、客户:39、需求:2 |

## 分类说明

- **小红书/视频号/自媒体获客**：2 条。代表视频：从小红书引流300+到成交：一套可复制的获客闭环.mp4；6 自媒体拓客秘籍（小红书、视频号）.mp4
- **活动/线下/社群获客**：7 条。代表视频：202409202024年保险人在小红书实现“高效获客、持续变现”!-刘昶贤.mp4；20250306没客户？通过活动来获客-王彩娥.mp4；20231222用客户的服务链接客户，引爆你的获客量！-石文玉.mp4；20250509如何在小红书获客-王燕燕.mp4；三类活动,批量获客.mp4
- **首次沟通/转化/成交**：9 条。代表视频：251104线上获客与团财险实战攻略.mp4；2025年02期：从心出发--保险新人的松弛感和获客思路.mp4；1.客户特点、成交基本原则、获取信任的相关动作.mp4；2.陌客营销技巧流程与问题链.mp4；1.首次沟通环节的高频问题.mp4
- **获客心法/拓客路径**：4 条。代表视频：2025.9.17互联网&线下双轨制获客.mp4；2025年06期：从资源空窗到拓客破局-我的经纪人成长之路.mp4；持续深耕，被动获客.mp4；【团财拓客】2025.8.27团财高绩.mp4
- **产品/核保/规则支撑**：8 条。代表视频：2025.12.22我的拓客之路，心法+技法.mp4；【月缴单分享】2024.1.22拓客新模式，月缴保单的魅力.mp4；3.方案制作原则与讲解要点.mp4；2024-12-6 关于规范宣传推广获客业务操作的通知-业务管理部于淼.mp4；（0112）成长及拓客方法-三四线城市成长及拓客之路.mp4
- **工具/系统/后台操作**：2 条。代表视频：251230明亚app功能介绍-获客及客经.mp4；玄学获客秘籍：25年冲刺，26年开局.mp4

## ASR 重跑结果

本次 ASR 使用本项目本地 SenseVoice/FunASR 路线，未上传云端。环境检查产物：
- `%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\asr-environment.json`
- `%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\asr-environment.md`
- ASR 运行汇总：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\local-asr-run-summary.json`

| 视频 | 得到大脑段数 | 本地 ASR 段数 | 得到大脑字数 | 本地 ASR 字数 | 标点密度 GB/ASR | 重复窗口 GB/ASR | 判断 |
|---|---:|---:|---:|---:|---|---|---|
| 从小红书引流300+到成交：一套可复制的获客闭环.mp4 | 90 | 1138 | 21065 | 18947 | 9.16 / 0.0 | 0 / 0 | ASR 可用作本地兜底和时间戳证据，但直接生成总结前需要去重、标点恢复、术语语义纠错。 |
| 20250306没客户？通过活动来获客-王彩娥.mp4 | 110 | 1000 | 33495 | 30591 | 7.96 / 0.0 | 0 / 0 | ASR 可用作本地兜底和时间戳证据，但直接生成总结前需要去重、标点恢复、术语语义纠错。 |
| 1.首次沟通环节的高频问题.mp4 | 22 | 323 | 6124 | 5332 | 9.16 / 0.0 | 0 / 0 | ASR 可用作本地兜底和时间戳证据，但直接生成总结前需要去重、标点恢复、术语语义纠错。 |

## 智能总结质量对比

| 视频 | 得到大脑原始智能总结 | VKP：得到大脑转写输入 | VKP：本地 ASR 输入 | 质量判断 |
|---|---:|---:|---:|---|
| 从小红书引流300+到成交：一套可复制的获客闭环.mp4 | 4798 字<br>`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\从小红书引流300-到成交-一套可复制的获客闭环\getbrain-smart-summary.md` | 12494 字<br>`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\从小红书引流300-到成交-一套可复制的获客闭环\webui-bundle\exports\smart-summary.md` | 11523 字<br>`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\从小红书引流300-到成交-一套可复制的获客闭环\local-asr-vkp\webui-bundle\exports\smart-summary.md` | 得到大脑原文更像可直接阅读成品；VKP 得到大脑输入版保留证据结构但仍有模板痕迹；VKP 本地 ASR 版因 ASR 分段碎、重复多，摘要质量最低。 |
| 20250306没客户？通过活动来获客-王彩娥.mp4 | 3314 字<br>`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\20250306没客户-通过活动来获客-王彩娥\getbrain-smart-summary.md` | 15023 字<br>`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\20250306没客户-通过活动来获客-王彩娥\webui-bundle\exports\smart-summary.md` | 12858 字<br>`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\20250306没客户-通过活动来获客-王彩娥\local-asr-vkp\webui-bundle\exports\smart-summary.md` | 得到大脑原文更像可直接阅读成品；VKP 得到大脑输入版保留证据结构但仍有模板痕迹；VKP 本地 ASR 版因 ASR 分段碎、重复多，摘要质量最低。 |
| 1.首次沟通环节的高频问题.mp4 | 1962 字<br>`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\1-首次沟通环节的高频问题\getbrain-smart-summary.md` | 12264 字<br>`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\1-首次沟通环节的高频问题\webui-bundle\exports\smart-summary.md` | 10137 字<br>`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\1-首次沟通环节的高频问题\local-asr-vkp\webui-bundle\exports\smart-summary.md` | 得到大脑原文更像可直接阅读成品；VKP 得到大脑输入版保留证据结构但仍有模板痕迹；VKP 本地 ASR 版因 ASR 分段碎、重复多，摘要质量最低。 |

### 观察

- 得到大脑的优势：自动段落化、标题化、概括性强，能把保险获客课程整理成较自然的培训笔记。\n- 本次 VKP 对比的限制：刚才实际未执行真实 Codex/在线 LLM 改写层；项目之前把 `smart-summary.codex.md` 的本地 scaffold 误标成 `codex_llm_rewrite_substitute`，现已修正为 `local_scaffold_not_llm` / `needs_llm_rewrite`。
- VKP 的优势：每个输出都有 bundle、timeline、full transcript、audit、content material card，可以继续接视觉、OCR、术语仲裁和人工审核；适合做可追溯的个人知识资产。
- 本地 ASR 的当前问题：SenseVoice 能跑通且速度可接受，但裸输出进入总结会放大重复、无标点、术语错词和分段碎片问题。
- 因此本项目下一步最该补的是：ASR 后处理闭环，而不是单纯多跑 ASR。具体包括去重、标点恢复、术语语义纠错，并用自带字幕/本地抓取字幕、网页上下文、青龙打标器、OCR/视觉证据和在线 LLM 进行仲裁后再生成 corrected transcript。得到大脑只作为评测标尺和人工参考，不进入自动仲裁证据链。

## 产物索引

### 从小红书引流300+到成交：一套可复制的获客闭环.mp4

- 得到大脑智能总结：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\从小红书引流300-到成交-一套可复制的获客闭环\getbrain-smart-summary.md`
- 得到大脑 transcript JSON：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\从小红书引流300-到成交-一套可复制的获客闭环\getbrain-normalized-transcript.json`
- VKP 得到大脑输入版 bundle：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\从小红书引流300-到成交-一套可复制的获客闭环\webui-bundle`
- VKP 得到大脑输入版 smart-summary：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\从小红书引流300-到成交-一套可复制的获客闭环\webui-bundle\exports\smart-summary.md`
- 本地 ASR transcript JSON：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\从小红书引流300-到成交-一套可复制的获客闭环\local-asr-sensevoice\transcripts\transcript_a2f0473120e4\normalized-transcript.json`
- VKP 本地 ASR 输入版 bundle：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\从小红书引流300-到成交-一套可复制的获客闭环\local-asr-vkp\webui-bundle`
- VKP 本地 ASR 输入版 smart-summary：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\从小红书引流300-到成交-一套可复制的获客闭环\local-asr-vkp\webui-bundle\exports\smart-summary.md`

### 20250306没客户？通过活动来获客-王彩娥.mp4

- 得到大脑智能总结：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\20250306没客户-通过活动来获客-王彩娥\getbrain-smart-summary.md`
- 得到大脑 transcript JSON：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\20250306没客户-通过活动来获客-王彩娥\getbrain-normalized-transcript.json`
- VKP 得到大脑输入版 bundle：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\20250306没客户-通过活动来获客-王彩娥\webui-bundle`
- VKP 得到大脑输入版 smart-summary：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\20250306没客户-通过活动来获客-王彩娥\webui-bundle\exports\smart-summary.md`
- 本地 ASR transcript JSON：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\20250306没客户-通过活动来获客-王彩娥\local-asr-sensevoice\transcripts\transcript_f861db297868\normalized-transcript.json`
- VKP 本地 ASR 输入版 bundle：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\20250306没客户-通过活动来获客-王彩娥\local-asr-vkp\webui-bundle`
- VKP 本地 ASR 输入版 smart-summary：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\20250306没客户-通过活动来获客-王彩娥\local-asr-vkp\webui-bundle\exports\smart-summary.md`

### 1.首次沟通环节的高频问题.mp4

- 得到大脑智能总结：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\1-首次沟通环节的高频问题\getbrain-smart-summary.md`
- 得到大脑 transcript JSON：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\1-首次沟通环节的高频问题\getbrain-normalized-transcript.json`
- VKP 得到大脑输入版 bundle：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\1-首次沟通环节的高频问题\webui-bundle`
- VKP 得到大脑输入版 smart-summary：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\1-首次沟通环节的高频问题\webui-bundle\exports\smart-summary.md`
- 本地 ASR transcript JSON：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\1-首次沟通环节的高频问题\local-asr-sensevoice\transcripts\transcript_42fdc6b98598\normalized-transcript.json`
- VKP 本地 ASR 输入版 bundle：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\1-首次沟通环节的高频问题\local-asr-vkp\webui-bundle`
- VKP 本地 ASR 输入版 smart-summary：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\1-首次沟通环节的高频问题\local-asr-vkp\webui-bundle\exports\smart-summary.md`

## 后续建议

1. 对这 3 条先做 ASR 后处理：去重、标点恢复、保险/获客术语语义纠错，生成 `corrected-transcript` 后再跑智能总结。
2. 对最终入选的视频再跑 ebook/OCR 和疑难点多模态复核，把课件上的工具名、流程图、数据表补进 evidence。
3. 真正要超过得到大脑摘要质量，需要启用 LLM 改写层：Codex 先代替在线 LLM，后续可切方舟/OpenAI-compatible 文本模型。
