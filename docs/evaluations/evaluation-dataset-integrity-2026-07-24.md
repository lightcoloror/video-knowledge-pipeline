# VKP 评测数据集完整性与可用性收口

更新时间：2026-07-24 15:56:31 +08:00
执行工具/模型：Codex GPT-5.6

## 方法与边界

使用新增的本地 evaluation_dataset_manifest 对 %VKP_DATASET_ROOT% 进行流式 SHA-256
清单计算。全过程：

- 只读外接盘；未下载、解压、删除、上传或调用模型；
- 不写入任何生产 Bundle、Timeline、逐字稿或智能总结；
- 完整清单身份：e93366df63fc7b4f08f1b96a04401cd9e2c6ee714b14bb1d0c43d02f99615ca5。

这份身份覆盖本次纳入的三个数据集条目、路径、字节数、SHA-256 和状态。

## 当前结论

| 数据集 | 当前状态 | 可立即用途 | 不足 |
| --- | --- | --- | --- |
| AutoShot | benchmark_completed | 已有 167 视频 GT-present 子集和 32 视频 GPU 盲测；可整理为场景/镜头边界基线 | 32 视频结论不等于全量 200 测试视频结论 |
| ClipShots | archive_complete_not_extracted | 标注可读；三分卷已完整哈希 | 视频未解压，不能开始边界评测 |
| AISHELL-1 ModelScope subset | metadata_only | 可用于许可、split 和下载来源核验 | 没有音频 payload，不能计算 CER/WER |

## ClipShots 分卷证据

| 文件 | 字节数 | SHA-256 |
| --- | ---: | --- |
| ClipShots-a | 18,874,368,000 | 0df5fd54d060bfc887592906930dd82c0790061dde3b6bce4c105f0c3484169e |
| ClipShots-b | 18,874,368,000 | 94b40264fc23f60bd6570e2a8f3f9a96916953223936131cc81eeef1fd7d0ef5 |
| ClipShots-c | 10,555,027,769 | 22d90b831570385afb94477b705d5588978f0f867425565993f51fb657d128ed |

三分卷为连续 gzip/tar 内容，不是三个独立压缩包。后续解压必须在新目录中以
a + b + c 的顺序重组，并先保留原始分卷；不得覆盖 raw\ClipShots 的标注仓库。

## AutoShot 已有证据

- 32 视频 GPU 推理报告：
  %VKP_DATASET_ROOT%\subsets\AutoShot-GT-present-167\autoshot-gpu-inference-pilot-32.json
  （e77f68132add6d9fc7f5af45e8031522252f4ff7c0841caf0c8b5d163edf3ba0）。
- 抽样清单：
  %VKP_DATASET_ROOT%\subsets\AutoShot-GT-present-167\pilot-32-manifest.json
  （0e29c68c1fd86bd437c8e93092f2048bac330b7db2920c352a9964533384e71a）。
- 既有本地结果：AutoShot F1 约 0.78837；PySceneDetect blind F1 约
  0.6699；TransNet 约 0.7246。这些仅为固定 32 视频样本的候选基线，
  不自动改变 VKP 默认 PySceneDetect 路线。

## 后续动作

1. 先把 AutoShot 报告转为 VKP 候选场景边界评测附件；不运行新模型。
2. ClipShots 解压前先确认外接盘保留至少约两倍解压空间，并取得用户对大规模
   解压的明确许可。
3. AISHELL-1 必须补齐音频后才开始 ASR CER/WER；在此之前不得称为 ASR
   测试集已就绪。
