# VKP Agent Substitute 逐字稿质量实测

- 时间：2026-07-09 17:59:00
- 源 bundle：`%WORKSPACE_ROOT%\video-knowledge-pipeline\openclaw-runs\getbrain-acquisition-20260708\1-首次沟通环节的高频问题\local-asr-vkp\webui-bundle`
- 临时 bundle：`%WORKSPACE_ROOT%\video-knowledge-pipeline\tmp\agent-substitute-quality-smoke\webui-bundle`
- 云调用：否，本次只跑本地 `agent_substitute` / `agent_name=openclaw`。
- Pipeline return code：`0`

## 指标对比

| 版本 | 存在 | 段数 | 字数 | 标点数 | 标点/千字 | 错词命中 | 正确词命中 |
|---|---:|---:|---:|---:|---:|---|---|
| Before / postprocessed baseline | True | 68 | 5461 | 68 | 12.45 | 买虫:1, 二则一:1, 同意心:1, 明晚八点o:1 | 同理心:1, 更了解客户:1 |
| Before / readable transcript | True | 68 | 5887 | 562 | 95.46 | 买虫:1, 二则一:1 | 同理心:2, 更了解客户:1 |
| Before / source-arbitrated transcript | True | 68 | 5887 | 562 | 95.46 | 买虫:1, 二则一:1 | 同理心:2, 更了解客户:1 |
| Before / corrected transcript | True | 68 | 5887 | 562 | 95.46 | 买虫:1, 二则一:1 | 同理心:2, 更了解客户:1 |
| After / postprocessed baseline | True | 68 | 5730 | 337 | 58.81 | 买虫:1, 二则一:1, 同意心:1, 明晚八点o:1 | 同理心:1, 更了解客户:1 |
| After / readable transcript | True | 68 | 5823 | 428 | 73.5 | 买虫:1, 二则一:1, 同意心:1 | 同理心:1, 明晚八点 OK:1, 更了解客户:1 |
| After / source-arbitrated transcript | True | 68 | 5823 | 428 | 73.5 | 0 | 买重:1, 二择一:1, 同理心:2, 明晚八点 OK:1, 更了解客户:1 |
| After / corrected transcript | True | 68 | 5823 | 428 | 73.5 | 0 | 买重:1, 二择一:1, 同理心:2, 明晚八点 OK:1, 更了解客户:1 |

## 关键样例：00:04:28 - 00:06:42

### Before / postprocessed baseline

```text
[00:04:20.594 - 00:04:36.086] 那第二点呢就是他说十几分钟这个时间是比较短的也降低了客户对陌生人的电话的这个压力那同时展现了一个同理心他是这样说的在尽量不打扰您和孩子休息的前提下这样沟通啊。
[00:04:36.086 - 00:04:49.990] 所以这样的邀约啊客户会觉得比较有温度那第三个呢其实他这段话比较长但是它的排版大家可以看一下哦嗯我想要干嘛主要内容是什么一二三点当然了如果大家。
[00:04:49.990 - 00:05:02.304] 不太会排版也可以直接发语音啊因为声音它会更有温度也更容易成功的邀约那接下来的话他其实就在约时间了大家也可以看一下技巧那客户说。
[00:05:02.304 - 00:05:18.592] 呃客户这时候其实是已经接受了他说二十分钟的话那我需要是明天上午啊明天中午或者晚上那顾问他是这样说的呃我这边的日程安排呢是明天晚上的八点到十点啊中午一点到两点比较方便。
[00:05:18.592 - 00:05:35.872] 啊那您平时带孩子应该也挺忙的您平时哪一个时间段比较方便呢我尽量不打扰了啊你孩子休息呃那如果您呢买过保险也可以找一下之前的保单我可以帮你去做归纳查缺补漏啊看看是否会有一些买虫的。
[00:05:35.872 - 00:05:51.762] 好那我们来分析一下他这一段话术的重点啊首先第一个他采取了一个二则一的方式封闭问题确定具体时间第二个他提出了保单整理它凸显出了自己的服务内容服务范围实际上是很广的。
[00:05:51.762 - 00:06:06.658] 那其实这个时候呢如果客户接受他可以更了解的下一次沟通啊更了解客户他已有的保障那第三点呢他其实强调了一个我的日程营造了一个专家的这种氛围你是要提前预约的。
[00:06:06.658 - 00:06:22.151] 那第四个呢其实也同样的是不断的在展示自己的同意心那孩子是有自己的作息的那宝妈基本上是在孩子休息之后才有时间去处理别的事儿那这一点其实宝妈啊听上去也会比较舒服。
[00:06:22.151 - 00:06:37.048] 那客户是这样回的说嗯那明晚八点o我找一下我的保单啊或者说好的那如果明天您时间有变化提前和我说一下这个时间是专门留给您的啊你看他重点强调了专门留给您。
[00:06:37.048 - 00:06:48.766] 让客户呢有一种被重视的感觉啊那他自己也会不容易爽约那以上的这个方法其实大部分客户他他只要是有保险需求啊他都会容易接受的。
```

### After / corrected transcript

```text
[00:04:20.594 - 00:04:36.086] 那第二点呢，就是他说十几分钟这个时间是比较短的也降低了客户对陌生人的电话的这个压力，那同时展现了一个同理心他是这样说的，在尽量不打扰您和孩子休息的前提下，这样沟通，啊。
[00:04:36.086 - 00:04:49.990] 所以，这样的邀约啊，客户会觉得比较有温度，那第三个呢，其实他这段话比较长但是它的排版大家可以看一下，哦，嗯我想要干嘛主要内容是什么一二三点，当然了，如果大家。
[00:04:49.990 - 00:05:02.304] 不太会排版也可以直接发语音啊，因为声音它会更有温度也更容易成功的邀约，那接下来的话，他，其实就在约时间了，大家也可以看一下技巧，那客户说。
[00:05:02.304 - 00:05:18.592] 呃客户这时候其实是已经接受了他说二十分钟的话那我需要是明天上午，啊明天中午或者晚上那顾问他是这样说的：呃我这边的日程安排呢是明天晚上的八点到十点，啊中午一点到两点比较方便。
[00:05:18.592 - 00:05:35.872] 啊那您平时带孩子应该也挺忙的，您平时哪一个时间段比较方便呢，我尽量，不打扰了啊，你孩子休息，呃那，如果您呢买过保险也可以找一下之前的保单我可以帮你去做归纳查缺补漏，啊看看是否会有一些买重的。
[00:05:35.872 - 00:05:51.762] 好，那我们来分析一下他这一段话术的重点啊首先，第一个，他采取了一个二择一的方式，封闭问题确定具体时间，第二个，他提出了保单整理，它凸显出了自己的服务内容服务范围实际上是很广的。
[00:05:51.762 - 00:06:06.658] 那其实，这个时候呢，如果客户接受，他可以，更了解的下一次沟通啊更了解客户他已有的保障，那第三点呢，他其实强调了一个我的日程，营造了一个专家的这种氛围你是要提前预约的。
[00:06:06.658 - 00:06:22.151] 那第四个呢，其实也同样的是不断的在展示自己的同理心那孩子是有自己的作息的，那宝妈基本上是在孩子休息之后才有时间去处理别的事儿，那这一点其实宝妈，啊听上去也会比较舒服。
[00:06:22.151 - 00:06:37.048] 那客户是这样回的说：嗯那明晚八点 OK，我找一下我的保单，啊或者说好的那如果明天，您时间有变化提前和我说一下，这个时间是专门留给您的，啊，你看他重点强调了专门留给您。
[00:06:37.048 - 00:06:48.766] 让客户呢有一种被重视的感觉啊，那他自己也会不容易爽约，那以上的这个方法其实大部分客户他，他只要是有，保险需求，啊他都会，容易接受的。
```

## 结论

- 相对 postprocessed baseline，corrected transcript 标点密度从 12.45 提升到 73.5 / 千字。
- 但相对旧 readable/corrected 输出，标点密度从 95.46 降到 73.5 / 千字，说明本地 agent substitute 的标点断句仍弱于旧版 readable 改写层。
- 高置信错词修复：同意心->同理心、二则一->二择一、买虫->买重
- 相对旧 corrected 输出，已跟踪错词总命中从 2 降到 0；主要质量提升来自证据冲突/语义纠错链路，而不是标点层。
- transcript-quality-gate：`passed`，ok=`True`。
- pipeline 状态摘要：`completed`。
- 这次验证没有调用云 LLM；提升主要来自本地 agent substitute 的断句/标点和保守语义纠错，不能等同于真正在线 LLM 的深度改写。

## Pipeline 输出尾部

```text
      "arbitrated_no_change_count": 0,
        "applied_correction_count": 3,
        "changed_segment_count": 3
      }
    },
    {
      "name": "corrected_transcript_alias",
      "status": "completed",
      "ok": true,
      "summary": {
        "status": "completed",
        "ok": true
      }
    },
    {
      "name": "agent_readable_transcript_rewrite",
      "status": "agent_substitute_executed",
      "ok": true,
      "summary": {
        "status": "agent_substitute_executed",
        "ok": true
      }
    },
    {
      "name": "transcript_quality_gate",
      "status": "passed",
      "ok": true,
      "summary": {
        "status": "passed",
        "ok": true
      }
    },
    {
      "name": "export_knowledge_note",
      "status": "unknown",
      "ok": false,
      "summary": {}
    }
  ],
  "artifacts": {
    "pipeline_json": "%WORKSPACE_ROOT%\\video-knowledge-pipeline\\tmp\\agent-substitute-quality-smoke\\webui-bundle\\transcript-evidence-correction-pipeline.json",
    "pipeline_markdown": "%WORKSPACE_ROOT%\\video-knowledge-pipeline\\tmp\\agent-substitute-quality-smoke\\webui-bundle\\transcript-evidence-correction-pipeline.md",
    "postprocessed_transcript_json": "%WORKSPACE_ROOT%\\video-knowledge-pipeline\\tmp\\agent-substitute-quality-smoke\\webui-bundle\\postprocessed-transcript.json",
    "llm_readable_transcript_json": "%WORKSPACE_ROOT%\\video-knowledge-pipeline\\tmp\\agent-substitute-quality-smoke\\webui-bundle\\llm-readable-transcript.json",
    "evidence_conflict_index_json": "%WORKSPACE_ROOT%\\video-knowledge-pipeline\\tmp\\agent-substitute-quality-smoke\\webui-bundle\\evidence-conflict-index.json",
    "evidence_conflict_llm_pack_json": "%WORKSPACE_ROOT%\\video-knowledge-pipeline\\tmp\\agent-substitute-quality-smoke\\webui-bundle\\evidence-conflict-llm-pack.json",
    "source_arbitrated_transcript_json": "%WORKSPACE_ROOT%\\video-knowledge-pipeline\\tmp\\agent-substitute-quality-smoke\\webui-bundle\\source-arbitrated-transcript.json",
    "corrected_transcript_json": "%WORKSPACE_ROOT%\\video-knowledge-pipeline\\tmp\\agent-substitute-quality-smoke\\webui-bundle\\corrected-transcript.json",
    "agent_readable_transcript_json": "%WORKSPACE_ROOT%\\video-knowledge-pipeline\\tmp\\agent-substitute-quality-smoke\\webui-bundle\\agent-readable-transcript.json",
    "transcript_quality_gate_json": "%WORKSPACE_ROOT%\\video-knowledge-pipeline\\tmp\\agent-substitute-quality-smoke\\webui-bundle\\transcript-quality-gate.json",
    "full_transcript": "%WORKSPACE_ROOT%\\video-knowledge-pipeline\\tmp\\agent-substitute-quality-smoke\\webui-bundle\\exports\\full-transcript.md",
    "smart_summary": "%WORKSPACE_ROOT%\\video-knowledge-pipeline\\tmp\\agent-substitute-quality-smoke\\webui-bundle\\exports\\smart-summary.md",
    "mcp_args": "%WORKSPACE_ROOT%\\video-knowledge-pipeline\\tmp\\agent-substitute-quality-smoke\\webui-bundle\\mcp-transcript-evidence-correction-pipeline.args.json"
  },
  "next_actions": [
    "Use exports/full-transcript.md and exports/smart-summary.md as local agent-substitute outputs (openclaw), or rerun with --execute-llm for online arbitration."
  ],
  "operator_boundary": {
    "local_source_arbitration_can_write": true,
    "online_llm_requires_execute_llm": true,
    "agent_substitute_default": true,
    "agent_substitute_name": "openclaw",
    "agent_substitute_local_only": true,
    "agent_substitute_supported_agents": [
      "codex",
      "workbuddy",
      "opencode",
      "hermes_agent",
      "openclaw",
      "custom_local_agent"
    ],
    "codex_substitute_legacy_alias": true,
    "readable_llm_requires_execute_readable_llm": false,
    "readable_llm_promote_requires_promote_readable_llm": false,
    "auto_apply_requires_auto_apply_high_confidence": false,
    "does_not_modify_raw_asr_or_subtitle_sources": true,
    "provider_config_runtime_only": true,
    "low_confidence_or_high_risk_conflicts_require_review": true
  },
  "updated_at": "2026-07-09T17:59:00"
}

```
