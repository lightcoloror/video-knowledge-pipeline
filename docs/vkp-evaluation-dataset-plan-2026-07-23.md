# VKP 视频分析评测数据集与空间预算

## 记录

- 执行者：Codex（GPT-5）
- 时间：2026-07-23 15:58:35（Asia/Shanghai）
- 状态：评测设计已确认；尚未下载公共视频数据

## 结论

VKP 的“拉片结果、ASR 逐字稿、智能总结”没有一个可直接覆盖全链路的公共数据集。采用组合评测：

1. 公共数据集验证通用能力和指标实现。
2. `VKP-Gold-v1` 验证中文知识视频、保险术语、PPT 和生产质量门。
3. 得到大脑产物只作为对照来源，经人工核验后才能进入 goldset，不能直接作为事实真源。

D 盘当前约有 27.4 GiB 可用空间。禁止默认下载 MovieNet、Video-MME、ClipShots、AISHELL-1 等全量媒体。首期新增空间上限设为 10 GiB，并至少保留 10 GiB 系统余量。

## 公共数据集与用途

| 数据集 | 主要用途 | 官方规模或空间 | VKP 决策 |
| --- | --- | --- | --- |
| MovieNet | 场景边界、景别、运镜、动作、地点、剧情段落关联 | annotation 53 MB 压缩/881 MB 解压；meta 537 MB/2.3 GB；关键帧 161 GB；音频特征 89.7 GB；地点特征 11 GB | 首期只取 annotation 与 split，不下载关键帧和特征 |
| ClipShots | 硬切、渐变转场、手持抖动与遮挡 | 官方未披露总字节；完整视频 1–20 分钟，包含训练、测试和渐变集 | 只取测试集小样，不下载训练集 |
| AutoShot/SHOT | 短视频镜头边界 | 853 个完整短视频、11,606 个镜头标注、200 个高质量测试视频 | 首期抽取 20–50 个测试视频 |
| SlideVQA | PPT/OCR、多页证据定位、跨页问答 | 2,619 套、每套 20 页，共约 52,380 张幻灯片；官方未披露总字节 | 首期抽取 50–100 套，预计 0.3–1.0 GB |
| Video-MME | 短中长视频、多帧/字幕/音频综合理解 | 900 个视频、254 小时、2,700 个人工问答；官方未披露总字节 | 首期只取 20–30 个知识/生活/影视样本，预计 2–6 GB |
| AISHELL-1 | 普通话 ASR CER 基准 | 官方压缩包 15 GB，另有 1.2 MB 词典资源，中国镜像可用 | 不下载全量；优先抽取 1–2 小时 eval 音频，预计 0.2–0.5 GB |
| QMSum | 长转写分段、主题摘要、证据 span | 232 场会议、1,808 组 query-summary，纯文本 | 可全量使用，预算小于 0.2 GB |

MovieNet 全部已公开的非原始电影项目合计约 264 GB；再加 AISHELL-1、SlideVQA、Video-MME、ClipShots 和 AutoShot 后，全量组合保守估计为 400–750 GB，且不包含 MovieNet 原始电影。当前 D 盘不能承载。

## VKP-Gold-v1

首期复用已有视频文件，不复制源视频：

- 3 条 PPT 讲课视频；
- 2 条人物讲解或访谈；
- 2 条屏幕录制或软件演示；
- 3 条实拍、转场或运镜素材。

人工标注目标：

- 60–90 分钟逐字稿，逐字校对并标记缺段；
- 200–300 个镜头边界；
- 50–100 个语义场景；
- 100 张 PPT/OCR 疑难帧；
- 30 个章节摘要；
- 约 150 个关键知识点，每项绑定时间区间和 evidence ID；
- sqlite-vec 查询 goldset：至少 30 个 query，每个列出 relevant、required tags 和 adjacent assets。

增量空间预算：

| 产物 | 预算 |
| --- | ---: |
| 16 kHz 音频、局部 ASR 重跑片段 | 0.3–0.8 GB |
| 关键帧、temporal 组、OCR 裁片 | 0.5–1.5 GB |
| 转写、OCR、Timeline、摘要、人工标注 | 0.1–0.5 GB |
| BGE-M3 embedding 与 sqlite-vec 索引 | 0.3–1.0 GB |
| A/B/C 候选结果与临时缓存 | 1.0–2.0 GB |
| 合计 | 2.2–5.8 GB |

## 首期推荐空间方案

在当前 27.4 GiB 余量下采用：

- MovieNet annotation/split：约 0.9 GB；
- QMSum：小于 0.2 GB；
- SlideVQA 小样：0.3–1.0 GB；
- AISHELL eval 小样或自有人工 ASR gold：0.2–0.5 GB；
- ClipShots/AutoShot 小样：1–3 GB；
- Video-MME 暂不下载，先用 VKP 自有视频验证多模态；
- VKP-Gold-v1 派生产物：2.2–5.8 GB。

目标新增占用约 5–10 GB。下载器必须支持：

1. 下载前 dry-run 和空间预算；
2. 精确 manifest、来源、版本、许可和 SHA-256；
3. 按 split/样本 ID 选择，不允许默认全量；
4. 可重建缓存与不可重建人工标注分目录；
5. 低于 10 GiB 可用空间时阻止新下载；
6. 中国大陆镜像优先：OpenDataLab、ModelScope、OpenSLR 中国镜像、百度网盘等；镜像内容仍须绑定官方数据集身份与版本。

## 指标

- 拉片：boundary F1（±0.5 秒与 ±1 秒）、场景合并准确率、景别/运镜 Macro-F1。
- ASR：CER、术语召回、30 秒窗口缺段率、时间戳误差、重复/重叠率。
- 智能总结：关键点召回、事实准确率、无证据陈述率、章节完整率。
- sqlite-vec：Recall@5、Recall@10、filtered recall、adjacent coverage 与查询延迟。
- 整链：质量门通过率、人工修订分钟数、处理时长/视频时长比例。

## 官方来源

- MovieNet：https://movienet.github.io/
- ClipShots：https://github.com/Tangshitao/ClipShots
- AutoShot：https://github.com/wentaozhu/AutoShot
- SlideVQA：https://github.com/nttmdlab-nlp/SlideVQA
- Video-MME：https://github.com/MME-Benchmarks/Video-MME
- AISHELL-1：https://www.openslr.org/33/
- QMSum：https://github.com/Yale-LILY/QMSum

