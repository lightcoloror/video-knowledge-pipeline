# Qwen Recoverable Window Execution Design

更新时间：2026-08-18 19:11:38 +08:00
规划与验收 Owner：Codex (GPT-5.6 Sol)

## 目标与边界

下一实现任务解决超长媒体在进入 ASR 前先由单个 FFmpeg `segment` 命令生成全部音频块的问题。当前命令在分块阶段整体失败时，尚未开始转录，因而没有窗口级进度可恢复；外层续跑也会再次生成全部窗口。目标是让每个固定窗口独立提取、独立转录、立即写入现有 Qwen checkpoint。一个窗口的提取或转录失败只能形成该窗口的失败记录，不能抹去已完成结果，也不能阻止后续窗口继续。

实现必须继续以 `qwen3_asr_python_runner` checkpoint 为唯一运行状态真源。不得新增顶层 ASR 状态机、Provider、fallback 或守护服务。音频窗口默认放在受控临时目录，处理后删除；checkpoint 只保存边界、状态和结果，不嵌入音频或 context 明文。真实媒体、模型、网络、上传和配置均不属于本任务。

## 方案选择

方案 A 保留整段 `segment` 命令，只在完成后写清单，改动小但无法隔离单窗提取失败，也无法避免续跑重新切完整媒体。方案 B 把固定边界计算与单窗 FFmpeg 提取提升为 `audio_chunk_manifest` 的复用函数，Qwen runner 按尚未完成的 index 惰性调用，并在每窗后原子写现有 checkpoint；这是推荐方案。方案 C 新建跨 FunASR/Qwen 的通用窗口调度器，长期可能统一，但当前会扩大回归面并形成第二套所有权。

## 数据流与失败语义

Runner 先用已注册 ffprobe 获取总时长，再复用固定边界函数生成确定性窗口计划。checkpoint 的执行契约增加窗口计划 revision，但保持旧 checkpoint 兼容。续跑时先加载成功 index，再只为未完成窗口调用单窗提取。提取失败记录 `chunk_extraction_failed`、窗口边界、attempt count 与重试命令，立即 checkpoint 后继续；转录失败沿用现有失败合同。成功窗口在时间戳上叠加实际 `start_seconds`，而不是再次推导或重复叠加 offset。

完成条件仍是所有请求窗口成功且无失败。部分成功输出保持 `degraded/usable`，单窗重试次数遵守既有 `max_chunk_attempts`。任何输入身份、模型、语言、context SHA、窗口大小或计划 revision 漂移都拒绝复用新 checkpoint。

## Codex 验收职责

实现 Agent 提交独立 checkpoint commit 与完成回执后，Codex 只做 diff 审查、契约核对、离线测试复跑和脏工作树隔离检查。验收必须证明：首窗成功后二窗提取失败时首窗仍在 checkpoint；三窗中间失败不阻止第三窗；续跑不重新提取成功窗；全部完成后 `run-asr-plan` 的无模型重建与幂等复用仍通过；时间戳使用窗口绝对起点。未通过任何一项不得进入真实素材 `plan-only` 验收。
