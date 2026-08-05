# Local Runtime Guide

Updated: 2026-06-02

This guide is for running the current local lecture extraction workflow with the
patched BiliNote tree and the `lecture-extract` CLI/MCP layer.

## 1. Use The Local CLI

```powershell
cd %WORKSPACE_ROOT%\question-research-poc
.\scripts\research-poc.ps1 smoke-bilinote-lecture
```

The launcher sets `PYTHONPATH=src` and calls `python -m question_research_poc.cli`,
so it does not depend on editable package installation or user site-packages
permissions.

`cmd.exe` equivalent:

```cmd
scripts\research-poc.cmd smoke-bilinote-lecture
```

Editable installation is optional:

```powershell
python -m pip install -e . --no-build-isolation
```

Optional MCP dependencies, only needed for the FastMCP stdio server:

```powershell
python -m pip install -e ".[mcp]" --no-build-isolation
```

## 2. Start Patched BiliNote

The patched BiliNote source tree is expected at:

```text
%WORKSPACE_ROOT%\tool-source-review\BiliNote
```

Dry-run the launcher first:

```powershell
.\scripts\start-bilinote-lecture.ps1 -CheckOnly
```

The dry run verifies the packaged BiliNote lecture patch before checking ports.
Its JSON output includes `patch_status` with `installed`, `missing`, and
`drift` counts. If the target BiliNote tree is missing packaged files or has
drifted, repair it before launch:

```powershell
.\scripts\start-bilinote-lecture.ps1 -InstallPatch
```

`-InstallPatch` installs/repairs the packaged files with backups before starting
the backend and frontend. Use `-SkipPatchCheck` only when intentionally testing
a custom BiliNote tree.

If you already generated a BiliNote UI fixture, include runtime validation in
the dry run. In `-CheckOnly` mode this runs the offline fixture/source contract
check and skips live backend/frontend probes. The contract includes BiliNote
lecture labels, API bindings, and stable `data-testid` anchors used by browser
automation and future agent workflows:

```powershell
.\scripts\start-bilinote-lecture.ps1 -CheckOnly `
  -FixtureDir D:\tmp\bilinote-ui-fixture `
  -ValidateRuntime
```

To generate the fixture as part of the same dry run:

```powershell
.\scripts\start-bilinote-lecture.ps1 -CheckOnly `
  -FixtureDir D:\tmp\bilinote-ui-fixture `
  -CreateFixture `
  -ValidateRuntime
```

Use `-OverwriteFixture` when you intentionally want to regenerate an existing
fixture directory.

Start the backend and frontend:

```powershell
.\scripts\start-bilinote-lecture.ps1
```

Default local URLs:

- Backend: `http://127.0.0.1:8483`
- Frontend: `http://127.0.0.1:3015`

The script checks the recorded/local port state before starting. It also appends
the chosen ports to the shared Obsidian port record when that file is available.

If BiliNote uses a different conda environment:

```powershell
.\scripts\start-bilinote-lecture.ps1 -CondaEnv bili
```

If no BiliNote conda environment exists and your current Python already has the
backend dependencies, skip conda activation:

```powershell
.\scripts\start-bilinote-lecture.ps1 -CondaEnv ""
```

You can also point the launcher at an isolated Python directly:

```powershell
.\scripts\start-bilinote-lecture.ps1 -CondaEnv "" -BackendPythonCommand D:\path\to\.venv\Scripts\python.exe
```

Check or create an isolated BiliNote backend environment:

```powershell
.\scripts\install-bilinote-backend-env.ps1
.\scripts\install-bilinote-backend-env.ps1 -CreateVenv
.\scripts\install-bilinote-backend-env.ps1 -InstallRequirements
```

The helper returns `backend_python` and `launch_command`. Use that Python with
`-BackendPythonCommand` instead of installing BiliNote's pinned requirements
into the global Python environment.

The launcher passes `VITE_API_BASE_URL=http://127.0.0.1:<backend-port>/api` to
the frontend. The `/api` suffix is required by BiliNote's backend health check
and API clients.

After launch, run a strict runtime validation gate through the same launcher:

```powershell
.\scripts\start-bilinote-lecture.ps1 `
  -FixtureDir D:\tmp\bilinote-ui-fixture `
  -ValidateRuntime `
  -RequireLive
```

The output includes `runtime_validation`, `runtime_validation_command`,
`patch_status`, and the backend/frontend URLs. With `-RequireLive`, frontend
validation also checks that the served resources still contain the lecture UI
automation anchors such as `lecture-bundle-import-root`,
`lecture-workspace-panel`, and `lecture-review-panel`.

To run the optional browser DOM smoke test from the launcher after startup:

```powershell
.\scripts\start-bilinote-lecture.ps1 `
  -FixtureDir D:\tmp\bilinote-ui-fixture `
  -ValidateRuntime `
  -ValidateBrowser
```

In `-CheckOnly` mode, `-ValidateBrowser` only returns
`browser_validation_command`; it does not open the frontend or require
Playwright.

For a real browser DOM smoke test after the frontend is running:

```powershell
.\scripts\research-poc.ps1 validate-bilinote-browser D:\tmp\bilinote-ui-fixture `
  --frontend-url http://127.0.0.1:3015
```

This optional check requires an existing local Playwright install. It seeds the
fixture into BiliNote's IndexedDB task storage, opens the frontend, toggles the
course review/workspace panels, and checks the real DOM for the lecture review,
study index, review queue, and workspace anchors. If Playwright is missing, the
command returns `missing_tool` with next actions instead of failing obscurely.

Check or install the optional dependency:

```powershell
.\scripts\install-bilinote-browser-smoke.ps1
.\scripts\install-bilinote-browser-smoke.ps1 -Install
.\scripts\install-bilinote-browser-smoke.ps1 -Install -LegacyPeerDeps
cd %WORKSPACE_ROOT%\tool-source-review\BiliNote\BillNote_frontend
npx playwright install chromium
```

## 3. Prepare ASR Tools

The lecture pipeline can plan and run FunASR/SenseVoice, WhisperX, and
faster-whisper. For agent-safe execution, `asr-runners` treats a tool as
available only when a runnable command is present. A Python module without a CLI
command is reported as `module_available: true` but `runnable: false`.

The CLI also resolves local media tools without requiring a global PATH install.
Set these when using a custom ffmpeg/tesseract bundle:

```powershell
$env:LECTURE_FFMPEG_DIR="D:\path\to\ffmpeg-bin"
$env:FFMPEG_BINARY="D:\path\to\ffmpeg-bin\ffmpeg.exe"
$env:FFPROBE_BINARY="D:\path\to\ffmpeg-bin\ffprobe.exe"
$env:TESSERACT_BINARY="D:\path\to\tesseract\tesseract.exe"
```

Guarded ASR, planned-command, and visual-extractor runners pass the resolved
ffmpeg/ffprobe/tesseract paths into child processes. This lets real peepshow,
vidwise, and imported extractor outputs work on Windows even when ffmpeg is not
globally installed.

ASR normalization is intentionally tolerant of common real runner outputs. It
accepts normal JSON and JSONL files, direct segment arrays, `result` /
`results` / `data` wrappers, Whisper-style `segments`, generic `cues`,
FunASR/SenseVoice `sentence_info`, `timestamp`, `start_ms` / `end_ms`,
`start_time` / `end_time`, `text_postprocessed`, and SenseVoice control tags
such as `<|zh|>`. It also accepts `.srt`, `.vtt`, and plain `.txt` / `.md`
transcripts, so BiliNote exports, manually corrected subtitles, or another
commercial/open-source ASR tool can enter the same pipeline without first being
converted to JSON. The normalized output is always written as
`normalized-transcript.json` plus `normalized-transcript.srt` for the lecture
pipeline.

Use the ASR environment helper to keep these dependencies out of global Python:

```powershell
.\scripts\research-poc.ps1 asr-env-status --output-dir .\asr-env-handoff --write
.\scripts\install-lecture-asr-env.ps1
.\scripts\install-lecture-asr-env.ps1 -VenvDir .\.conda-lecture-asr -CreateCondaEnv -PythonVersion 3.11
.\scripts\install-lecture-asr-env.ps1 -VenvDir .\.conda-lecture-asr -InstallFunASR
.\scripts\research-poc.ps1 mcp-call asr_environment_status .\asr-env-handoff\mcp-asr-environment-status.args.json
```

On this Windows workspace, the verified path is a local conda Python 3.11
environment. Global Python 3.13 can fail while building FunASR dependencies such
as `editdistance`.

`asr-env-status` is the agent-friendly handoff around the same ASR environment
policy. It writes `asr-environment.json`, `asr-environment.md`, `asr-env.ps1`,
and `mcp-asr-environment-status.args.json`, and returns one `next_action` such
as `create_asr_environment`, `recreate_asr_environment`, `install_funasr`,
`repair_asr_command`, or `apply_asr_env`. Apply the env snippet before
planning/running ASR so `plan-asr` writes the ASR environment command path into
`asr-run-plan.json`:

```powershell
$env:LECTURE_ASR_BIN_DIR="%WORKSPACE_ROOT%\question-research-poc\.conda-lecture-asr\Scripts"
$env:LECTURE_FUNASR_COMMAND="%WORKSPACE_ROOT%\question-research-poc\.conda-lecture-asr\Scripts\funasr.exe"
.\scripts\research-poc.ps1 asr-runners
.\scripts\research-poc.ps1 plan-asr .\workspace-project .\lesson.mp4 --preset sensevoice --model iic/SenseVoiceSmall
```

## 4. Generate MCP Config

Print a Codex/Claude-style MCP config snippet:

```powershell
.\scripts\write-mcp-config.ps1
```

Write it to a file:

```powershell
.\scripts\write-mcp-config.ps1 -Output .\lecture-extract.mcp.json
```

The generated server uses:

```text
python -m question_research_poc.mcp_server
```

with `PYTHONPATH` pointed at the local `src` directory.

## 5. Run The Local Smoke Test

Before starting the Web UI, verify the cross-project glue layer:

```powershell
.\scripts\research-poc.ps1 smoke-bilinote-lecture
```

To verify that a real local visual extractor can run end-to-end, use the real
extractor smoke test. With no media path it creates a tiny local MP4 fixture,
runs the selected extractor, imports the ready outputs, builds a lecture
package, and checks the generated WebUI bundle:

```powershell
.\scripts\research-poc.ps1 smoke-real-extractor --extractor peepshow --work-dir .\tmp\real-extractor-smoke --keep
```

For a real lecture slice, pass the media file explicitly:

```powershell
.\scripts\research-poc.ps1 smoke-real-extractor --extractor peepshow --media D:\path\to\lesson-clip.mp4 --work-dir .\tmp\lesson-smoke --keep
```

This command is intentionally small enough for frequent agent checks. It
validates the local media-tool resolver, planned extractor execution, import
readiness, package generation, bundle assets, and review-readiness reporting.
Use `--extractor vidclaude` or `--extractor vidwise` after those tools are
installed locally. The MCP equivalent is:

```powershell
.\scripts\research-poc.ps1 mcp-call smoke_real_extractor D:\path\to\smoke-real-extractor.args.json
```

For a lecture-oriented end-to-end gate, use `smoke-lecture-e2e`. It prepares the
same workspace, optionally runs ASR, runs a visual extractor, imports whatever
planned outputs are ready, and reports coverage/review gaps from the generated
WebUI bundle:

```powershell
.\scripts\research-poc.ps1 smoke-lecture-e2e --extractor peepshow --asr-mode auto --media D:\path\to\lesson-clip.mp4 --work-dir .\tmp\lesson-e2e --keep
```

To find a local candidate clip before running the strict gate, scan one or more
course/download directories:

```powershell
.\scripts\research-poc.ps1 find-lecture-media D:\Downloads D:\Courses `
  --min-duration-seconds 60 `
  --max-duration-seconds 180 `
  --limit 10
```

The result lists probed media metadata and a ready-to-copy
`smoke-lecture-e2e --strict-real-lecture` command for each candidate. Use
`--include-rejected` when diagnosing why files were skipped. The MCP equivalent
is `find_lecture_media`.

For an agent-friendly handoff, generate a real lecture acceptance plan instead
of copying commands by hand:

```powershell
.\scripts\research-poc.ps1 prepare-lecture-acceptance .\tmp\real-lecture-acceptance D:\Downloads D:\Courses `
  --min-duration-seconds 60 `
  --max-duration-seconds 180 `
  --limit 3
```

This writes:

- `real-lecture-acceptance-plan.json`: candidate manifest plus planned runs.
- `real-lecture-acceptance-handoff.md`: human-readable next commands.
- `mcp-smoke-lecture-e2e-candidate-*.args.json`: stable MCP args for
  `smoke_lecture_e2e`.
- `mcp-prepare-lecture-sample-clip-long-candidate-*.args.json`: stable MCP
  args for `prepare_lecture_sample_clip` when scanned videos are too long for
  direct strict validation.

By default, videos rejected as too long are converted into sample-clip preview
suggestions. Tune that with `--sample-start-seconds`,
`--sample-duration-seconds`, `--sample-limit`, or disable it with
`--no-sample-too-long`. The MCP equivalent is `prepare_lecture_acceptance`.

After the plan is written, ask for the next safe action:

```powershell
.\scripts\research-poc.ps1 lecture-acceptance-next .\tmp\real-lecture-acceptance\real-lecture-acceptance-plan.json
```

This prefers a direct `smoke_lecture_e2e` run when a matching 1-3 minute
candidate exists; otherwise it returns the first `prepare_lecture_sample_clip`
suggestion for a too-long video. The MCP equivalent is
`lecture_acceptance_next_action`.

To let an agent advance one preview-safe step, use:

```powershell
.\scripts\research-poc.ps1 lecture-acceptance-advance .\tmp\real-lecture-acceptance\real-lecture-acceptance-plan.json
```

This runs `prepare_lecture_sample_clip` in preview mode for sample suggestions
and returns the generated strict-smoke MCP args. It does not auto-run
`smoke_lecture_e2e`; when strict validation is ready, it returns a blocked
status with the command to run explicitly. Pass `--execute-sample` only when you
want ffmpeg to write the sample clip. When sample execution succeeds, the
acceptance plan is updated with the generated clip as a new
`smoke_lecture_e2e` run, and the handoff Markdown is refreshed. The MCP
equivalent is `lecture_acceptance_advance`.

To let an agent keep advancing preview-safe acceptance steps until it reaches a
manual gate, use the queue helper:

```powershell
.\scripts\research-poc.ps1 lecture-acceptance-advance-queue .\tmp\real-lecture-acceptance\real-lecture-acceptance-plan.json --max-steps 3
```

The queue stops when strict smoke validation is ready, a step is blocked, the
same preview action would repeat without changing the plan, or `--max-steps` is
reached. It is preview-safe by default. Pass `--execute-sample` only when the
agent should let ffmpeg write sample clips. It still does not auto-run
`smoke_lecture_e2e`; that strict real-lecture check remains an explicit human
or agent decision. The MCP equivalent is `lecture_acceptance_advance_queue`.

If the available lecture file is much longer than the desired 1-3 minute
acceptance slice, preview a local ffmpeg clip command first:

```powershell
.\scripts\research-poc.ps1 prepare-lecture-sample-clip D:\Courses\long-lesson.mp4 .\tmp\sample-clips `
  --start-seconds 300 `
  --duration-seconds 120
```

Add `--execute` to actually write the sample clip, and `--overwrite` only when
replacing a previous sample is intended. The result includes source metadata,
the ffmpeg command, a recommended strict `smoke-lecture-e2e` command, and
`recommended_mcp_args` for agent use. It also writes
`mcp-smoke-lecture-e2e-sample.args.json` beside the planned/generated clip and
returns a ready `mcp-call smoke_lecture_e2e ...` command. The MCP equivalent is
`prepare_lecture_sample_clip`.

ASR modes:

- `--asr-mode auto`: run ASR only when the planned ASR runner is available.
- `--asr-mode always`: require ASR readiness; the smoke fails if ASR is missing
  or no normalized transcript becomes ready.
- `--asr-mode never`: skip ASR and validate the visual/import path only.

For real acceptance checks, do not rely on the generated fixture video. Use
`--strict-real-lecture` with an explicit media path. This requires external
media, at least 60 seconds by default, at least one transcript timeline item,
and visual frame evidence:

```powershell
.\scripts\research-poc.ps1 smoke-lecture-e2e `
  --strict-real-lecture `
  --extractor peepshow `
  --asr-mode always `
  --asr-preset sensevoice `
  --media D:\path\to\lesson-clip.mp4 `
  --work-dir .\tmp\lesson-e2e-real `
  --keep
```

The strict gate can be tuned with `--require-real-media`,
`--min-duration-seconds`, `--require-transcript`, and
`--require-visual-assets`. Keep the non-strict mode for quick development smoke
tests; use the strict gate before claiming that a real knowledge lecture video
has been captured end-to-end.

Use `--asr-preset sensevoice`, `--asr-preset funasr`, `--asr-preset whisperx`,
or `--asr-preset faster-whisper` to select the planned ASR command. The MCP
equivalent is:

```powershell
.\scripts\research-poc.ps1 mcp-call smoke_lecture_e2e D:\path\to\smoke-lecture-e2e.args.json
```

During package generation, `lecture-extract` classifies existing transcript,
OCR, frame, and extractor signals into material types such as `text`, `image`,
`code`, `formula`, `table`, `diagram`, and `board`. This is only a glue-layer
classifier: it does not replace vidclaude, peepshow, Docling, MinerU, Marker, or
PaddleOCR. Its job is to route likely code/formula/table/board frames into the
review and visual-structure queues so information that cannot safely be reduced
to plain text remains attached to image evidence.

If you installed the editable console command, this is equivalent:

```powershell
research-poc smoke-bilinote-lecture
```

The script wrapper remains available:

```powershell
python .\scripts\smoke_bilinote_lecture.py
```

This creates a temporary fixture project, builds a lecture package, exports a
BiliNote bundle, calls BiliNote's lecture bundle service directly, saves human
review corrections, refreshes the POC outputs, and exports an Obsidian folder.

Keep artifacts for inspection:

```powershell
.\scripts\research-poc.ps1 smoke-bilinote-lecture --keep
```

Use a non-default BiliNote source tree:

```powershell
.\scripts\research-poc.ps1 smoke-bilinote-lecture --bilinote-root D:\path\to\BiliNote
```

## 5. Typical End-To-End Flow

For a URL source, do not hand-roll a downloader inside this project. Use the
existing local `video-download-orchestrator` integration first. The default is a
dry-run that writes source provenance and an orchestrator manifest without
downloading:

```powershell
.\scripts\research-poc.ps1 prepare-video-source `
  https://www.bilibili.com/video/BV... `
  D:\path\to\downloads
```

Agent/MCP equivalent:

```powershell
.\scripts\research-poc.ps1 mcp-call prepare_video_source D:\path\to\prepare-video-source.args.json
```

When the dry-run plan is acceptable, repeat with `--execute` or MCP
`execute: true`. To continue directly into the normal lecture workspace after a
successful download:

```powershell
.\scripts\research-poc.ps1 prepare-lecture-workspace-from-url `
  .research-question `
  https://www.bilibili.com/video/BV... `
  --title "课程名" `
  --download-output-dir D:\path\to\downloads `
  --output-root D:\path\to\planned-runs `
  --execute
```

This URL entrypoint embeds `source_provenance` in the generated
`lecture-pipeline-plan.json` and `lecture-pipeline-plan.md`, including the
original URL, orchestrator manifest/report paths, provenance files, and the
selected local media path. Without `--execute`, it stops at
`status: download_planned` and leaves `workspace: null`.

For a new lecture video, prepare a workspace before running expensive
extractors:

```powershell
.\scripts\research-poc.ps1 prepare-lecture-workspace .research-question D:\path\to\lesson.mp4 `
  --title "课程名" `
  --topic "课程主题" `
  --asr-preset sensevoice `
  --output-root D:\path\to\planned-runs
```

The workspace writes:

- `lecture-pipeline-plan.json`: structured plan for agents and automation.
- `lecture-pipeline-plan.md`: human-readable checklist and command sheet.
- `lecture-pipeline-status.json` and `lecture-pipeline-status.md`: current
  ready/missing state.
- `lecture-workspace.md`: compact operator handoff with the normal flow,
  extractor commands, status command, run-ready command, and BiliNote handoff.
- `lecture-workspace.html`: static browser dashboard for the same pre-extraction
  workspace, with ready/missing state and copy buttons for extractor, pipeline,
  health, and MCP commands.
- `asr-environment.json` and `asr-environment.ps1`: reusable ASR environment
  export generated from the planned ASR command. Dot-source the PowerShell file
  before guarded ASR execution when the plan uses a local ASR env.
- `extractor_commands`: per-extractor command metadata for vidclaude,
  peepshow, and vidwise. It records the command, planned output directory,
  command source, resolved command path, and command prefix, so humans and
  agents can see whether a route is using a real installed executable, direct
  peepshow `cli.js`, or a fallback command.
- `mcp-status-lecture-pipeline.args.json`,
  `mcp-lecture-project-health.args.json`,
  `mcp-lecture-next-step.args.json`, and
  `mcp-run-ready-lecture-pipeline.args.json`,
  `mcp-run-recommended-route.args.json`,
  `mcp-recommended-route-status.args.json`,
  `mcp-recommended-route-queue.args.json`,
  `mcp-recommended-workspace-advance.args.json`,
  `mcp-recommended-workspace-advance-log.args.json`, and
  `mcp-apply-bilinote-patch.args.json`: stable argument files for agent calls
  through `research-poc mcp-call`. The BiliNote patch args are generated in
  preview mode with backup enabled.

The plan and handoff include:

- ASR command and normalization command.
- ASR environment load command.
- vidclaude, peepshow, and vidwise suggested commands.
- `recommended_routes`: the shared first-run route list for BiliNote, CLI, and
  MCP agents. It ranks installed options as vidclaude main visual timeline,
  peepshow fast frame/OCR coverage, vidwise fallback, and ASR transcript
  companion, with per-route command and MCP args metadata.
- final `run-lecture-pipeline` commands for `vidclaude_only`,
  `peepshow_only`, `vidwise_only`, `asr_transcript_only_template`, and
  `all_extractors`.
- local tool/preflight status.

To inspect the recommended-route queue without executing anything, use:

```powershell
.\scripts\research-poc.ps1 recommended-route-status D:\path\to\planned-runs\lecture-pipeline-plan.json
.\scripts\research-poc.ps1 mcp-call recommended_route_status D:\path\to\planned-runs\mcp-recommended-route-status.args.json
```

`recommended-route-status`, `recommended-route-queue`, and
`run-recommended-route` refresh current local availability for vidclaude,
peepshow, vidwise, and runnable ASR commands before selecting work. If you
install a visual extractor or apply the ASR env after creating the workspace,
refresh this status or click the BiliNote workspace action again; rebuilding
`lecture-pipeline-plan.json` is not required just to pick up the new tool path.

To preview or explicitly execute the whole unfinished route queue, use:

```powershell
.\scripts\research-poc.ps1 recommended-route-queue D:\path\to\planned-runs\lecture-pipeline-plan.json
.\scripts\research-poc.ps1 recommended-route-queue D:\path\to\planned-runs\lecture-pipeline-plan.json --execute --timeout-seconds 3600 --max-steps 4
.\scripts\research-poc.ps1 mcp-call recommended_route_queue D:\path\to\planned-runs\mcp-recommended-route-queue.args.json
```

Queue execution is conservative: it stops on failed/timeout routes, stops when
the same next route remains unready after execution, and defaults to preview
unless `--execute` is present.

To preview or explicitly execute the normal workspace advance, use:

```powershell
.\scripts\research-poc.ps1 recommended-workspace-advance D:\path\to\planned-runs\lecture-pipeline-plan.json
.\scripts\research-poc.ps1 recommended-workspace-advance D:\path\to\planned-runs\lecture-pipeline-plan.json --execute --timeout-seconds 3600 --max-steps 4
.\scripts\research-poc.ps1 mcp-call recommended_workspace_advance D:\path\to\planned-runs\mcp-recommended-workspace-advance.args.json
```

The advance command combines the route queue and ready-output import. Preview
mode reports the route queue and whether `run-ready-lecture-pipeline` can import
anything; execute mode runs the queue first, refreshes readiness, then imports
ready outputs into the BiliNote/WebUI bundle.

Every preview or execution is logged for audit:

```powershell
.\scripts\research-poc.ps1 recommended-workspace-advance-log .research-question
.\scripts\research-poc.ps1 mcp-call recommended_workspace_advance_log D:\path\to\planned-runs\mcp-recommended-workspace-advance-log.args.json
```

The persisted files are:

- `lecture-packages/workspace-advance-runs.jsonl`
- `notes/lecture-workspace-advance-runs.md`

To preview or explicitly execute the current first unfinished recommended route, use:

```powershell
.\scripts\research-poc.ps1 run-recommended-route D:\path\to\planned-runs\lecture-pipeline-plan.json
.\scripts\research-poc.ps1 run-recommended-route D:\path\to\planned-runs\lecture-pipeline-plan.json --route vidclaude --execute --timeout-seconds 3600
.\scripts\research-poc.ps1 mcp-call run_recommended_route D:\path\to\planned-runs\mcp-run-recommended-route.args.json
```

Like the guarded ASR/extractor commands, `run-recommended-route` is preview-only
unless `--execute` is present.
When `--route` is omitted, it re-checks the plan readiness and selects the first
available recommended route whose planned output is not already ready. This lets
operators and agents click the same recommended-route action repeatedly while it
advances through unfinished vidclaude/peepshow/vidwise/ASR work instead of
looping on an already completed extractor. Pass `--route` to force a specific
route for audit or rerun.
If no available unfinished route remains, it returns `status: complete` and
`operation_status: skipped` instead of rerunning rank 1.
The result keeps the nested ASR/extractor operation for debugging, but also
adds flat `status`, `command_name`, `route_name`, `operation_status`,
`route_ready_before`, and `readiness` fields so BiliNote and MCP agents can
display a concise route result and explain whether the selected route already
had output before the run.

Use the matching single-extractor pipeline command if you only ran one visual
extractor. Use `all_extractors` only when all planned output folders exist.
After `normalize-asr`, replace `<normalized-transcript.json>` in
`asr_transcript_only_template` with the returned `json_path` to import a strong
ASR transcript as full cue-level evidence.
When no explicit `--transcript` is supplied, `status-lecture-pipeline` and
`run-ready-lecture-pipeline` scan `transcripts/**/normalized-transcript.json`,
choose the newest modified transcript by default, and report all candidates in
`normalized_transcript_candidates` plus the Markdown status table. Pass
`--transcript` when you intentionally want an older or manually selected file.

When the selected ASR runner is available locally, use the guarded ASR runner
instead of copying the raw ASR command by hand:

```powershell
. D:\path\to\planned-runs\asr-environment.ps1
.\scripts\research-poc.ps1 run-asr-plan D:\path\to\planned-runs\lecture-pipeline-plan.json
.\scripts\research-poc.ps1 run-asr-plan D:\path\to\planned-runs\lecture-pipeline-plan.json --execute --timeout-seconds 3600
.\scripts\research-poc.ps1 asr-run-log .research-question
```

Without `--execute`, the command only previews and logs the planned ASR run. With
`--execute`, it runs the `asr_plan.command` from the plan, searches for the raw
ASR JSON output, and runs `normalize-asr` automatically unless
`--no-normalize` is supplied.

Visual extractors have the same guarded runner shape:

```powershell
.\scripts\research-poc.ps1 run-extractor-plan D:\path\to\planned-runs\lecture-pipeline-plan.json peepshow
.\scripts\research-poc.ps1 run-extractor-plan D:\path\to\planned-runs\lecture-pipeline-plan.json peepshow --execute --timeout-seconds 3600
.\scripts\research-poc.ps1 extractor-run-log .research-question
```

Supported extractor names are `vidclaude`, `peepshow`, and `vidwise`. Execution
is preview-only unless `--execute` is supplied, and every run refreshes pipeline
readiness so the next BiliNote workspace import can show whether that extractor
became ready.
For `peepshow`, generated commands now include `--min` bounded by `--max`, so
small smoke runs such as `--max-frames 3` do not fail with peepshow's default
`--min 4`.

The guarded ASR and visual extractor runners write separate run logs:

- `lecture-packages/asr-command-runs.jsonl`
- `notes/asr-command-runs.md`
- `lecture-packages/extractor-command-runs.jsonl`
- `notes/extractor-command-runs.md`

`lecture-health` includes those logs in its `Runner Logs` section so agent and
UI workflows can tell which runner was tried last before recommending import or
review actions.
The BiliNote workspace panel also shows generic pipeline command history, ASR
run history, and visual extractor run history as separate cards.

After running any extractor, ask the plan what is ready:

```powershell
.\scripts\research-poc.ps1 status-lecture-pipeline D:\path\to\planned-runs\lecture-pipeline-plan.json
```

For the broader project view, use the generated health args:

```powershell
.\scripts\research-poc.ps1 mcp-call lecture_project_health D:\path\to\planned-runs\mcp-lecture-project-health.args.json
```

To let an agent advance the next safe local glue step, use the generated next
args:

```powershell
.\scripts\research-poc.ps1 mcp-call lecture_next_step D:\path\to\planned-runs\mcp-lecture-next-step.args.json
```

This tool will not run external extractors or ASR models. It only executes
safe local POC steps such as run-ready import, package build, WebUI export, or
review refresh; extractor runs and human review still return `manual_required`.
At the human-review boundary, `lecture-next` also checks BiliNote patch
readiness through `lecture-health`: if the WebUI bundle is ready but the target
BiliNote tree is missing or has drifted from the packaged lecture patch, the
selected action is `setup_bilinote_patch` instead of `human_review`.
The selected action keeps the copied command in `selected_action.command`, and
the persisted action log stores the same command for later review or rerun.
Preview the repair through the agent-safe CLI path:

```powershell
.\scripts\research-poc.ps1 bilinote-patch-apply
```

Apply it explicitly with backups:

```powershell
.\scripts\research-poc.ps1 bilinote-patch-apply --execute
```
Every call appends `lecture-packages/lecture-action-log.jsonl` and refreshes
`notes/lecture-action-log.md`.

When you do want to run one planned command explicitly, use the command runner:

```powershell
.\scripts\research-poc.ps1 run-planned-lecture-command D:\path\to\planned-runs\lecture-pipeline-plan.json peepshow
.\scripts\research-poc.ps1 run-planned-lecture-command D:\path\to\planned-runs\lecture-pipeline-plan.json peepshow --execute
.\scripts\research-poc.ps1 lecture-command-log .research-question
```

Without `--execute`, the runner only previews the selected command and logs the
preview. With `--execute`, it invokes PowerShell, captures stdout/stderr, and
writes `lecture-packages/lecture-command-runs.jsonl` plus
`notes/lecture-command-runs.md`. MCP exposes the same workflow as
`run_planned_lecture_command` and `lecture_command_log`.

The status command writes both `lecture-pipeline-status.json` and
`lecture-pipeline-status.md`. The Markdown file is the human checklist; the JSON
keeps the same readiness data and `recommended_pipeline_command` for CLI/MCP
automation when at least one planned output is importable.

For the normal path, let the plan drive the final import so you do not need to
copy a long command by hand:

```powershell
.\scripts\research-poc.ps1 run-ready-lecture-pipeline D:\path\to\planned-runs\lecture-pipeline-plan.json
```

This command re-checks readiness, imports only the ready planned outputs, builds
the lecture package, exports the BiliNote/WebUI bundle, and can optionally export
Obsidian notes with `--vault` and `--folder`.

It is safe to run this command repeatedly as extractor outputs arrive. The
pipeline records imported sources in `lecture-packages/import-runs.json`, skips
previously imported sources, and still rebuilds the package/bundle from current
project data.

If an already-imported extractor output was regenerated, use
`--force-reimport` to import it again and overwrite its registry entry:

```powershell
.\scripts\research-poc.ps1 run-ready-lecture-pipeline D:\path\to\planned-runs\lecture-pipeline-plan.json --force-reimport
```

When you need to audit rerun behavior, inspect the import registry:

```powershell
.\scripts\research-poc.ps1 lecture-import-status .research-question
```

This writes `notes/lecture-import-runs.md` and returns JSON with imported
source paths, segment counts, forced-reimport flags, and the default next-run
skip behavior.

Before starting a new lecture run, use the local inventory when you want a
machine-readable preflight over reusable tools rather than a project-specific
health check:

```powershell
.\scripts\research-poc.ps1 local-tool-inventory --output-dir .\tool-inventory --write
.\scripts\research-poc.ps1 mcp-call local_tool_inventory .\tool-inventory\mcp-local-tool-inventory.args.json
```

The command reuses the existing tool matrix, ASR detector, and media-tool
resolver. It reports BiliNote, vidclaude, peepshow, vidwise, content-core,
CaptiOCR, ffmpeg/ffprobe, tesseract, and the ASR runner presets, then returns a
single `next_action` such as `prepare_asr` or `ready_to_run_pipeline`.

When you want the stronger "look at real local code before building" check, run
the open-source reuse audit:

```powershell
.\scripts\research-poc.ps1 open-source-reuse-audit --output-dir .\tool-inventory --write
.\scripts\research-poc.ps1 mcp-call open_source_reuse_audit .\tool-inventory\mcp-open-source-reuse-audit.args.json
```

This report inspects local source mirrors and installed package code for
BiliNote, vidclaude, peepshow, vidwise, content-core, and CaptiOCR. It assigns
each tool a reuse level such as `direct_use`, `light_glue`, or
`architecture_reference`, records source-file evidence, and keeps the
implementation boundary explicit so the next change stays in the orchestration
layer unless deep integration is really justified.

For the ASR part of the route, generate a setup handoff before installing or
running any speech model:

```powershell
.\scripts\research-poc.ps1 plan-asr-setup --output-dir .\tool-inventory --write
.\scripts\research-poc.ps1 mcp-call plan_asr_setup .\tool-inventory\mcp-plan-asr-setup.args.json
```

This reuses `asr-env-status` and writes `asr-setup-plan.json` plus
`asr-setup-plan.md`. The plan is preview-only: it reports whether the current
ASR environment exists, whether its Python version is suitable for
FunASR/SenseVoice/WhisperX, which install command should run first, and which
PowerShell environment variables should be loaded before `plan-asr` or
`run-asr-plan`. If an existing ASR env uses a poor Python version, the setup
plan points at a new `-py311` environment directory instead of implying an
unsafe overwrite.

When deciding how to reuse content-core, inspect the local source as an
architecture reference instead of treating it as a visual-video extractor:

```powershell
.\scripts\research-poc.ps1 content-core-reference --output-dir .\tool-inventory --write
.\scripts\research-poc.ps1 mcp-call content_core_reference .\tool-inventory\mcp-content-core-reference.args.json
```

This writes `content-core-reference.json` and `content-core-reference.md`. The
report checks the real `cli.py`, `mcp/server.py`, and media processor files,
then separates reusable CLI/MCP patterns from the boundary that content-core's
video path is audio extraction plus transcription, not lecture screen/diagram
coverage.

For the highest-level project status view, use:

```powershell
.\scripts\research-poc.ps1 lecture-health .research-question --plan-json D:\path\to\planned-runs\lecture-pipeline-plan.json
```

This writes `notes/lecture-project-health.md`. It checks plan readiness,
import-runs status, package/quality report files, ASR tool availability, WebUI
bundle files, review notes, and action-log status, then returns concrete next
actions and the latest `lecture-next` action when present. It also reports the
recommended-route tool status for BiliNote, vidclaude, peepshow, vidwise,
content-core, and CaptiOCR, including local paths and command hints when a plan
is provided.
The BiliNote row is hash-based: it calls the packaged patch status checker and
reports `installed`, `missing`, and `drift` counts in the tool notes. For a
non-default BiliNote checkout:

```powershell
.\scripts\research-poc.ps1 lecture-health .research-question `
  --bilinote-root D:\path\to\BiliNote `
  --bilinote-patch-root %WORKSPACE_ROOT%\question-research-poc\integrations\bilinote-lecture-patch
```

To execute the next safe local glue step from that health state:

```powershell
.\scripts\research-poc.ps1 lecture-next .research-question --plan-json D:\path\to\planned-runs\lecture-pipeline-plan.json
```

For a non-default BiliNote checkout, pass the same patch-check paths:

```powershell
.\scripts\research-poc.ps1 lecture-next .research-question `
  --plan-json D:\path\to\planned-runs\lecture-pipeline-plan.json `
  --bilinote-root D:\path\to\BiliNote `
  --bilinote-patch-root %WORKSPACE_ROOT%\question-research-poc\integrations\bilinote-lecture-patch
```

Read the persisted action history with:

```powershell
.\scripts\research-poc.ps1 lecture-action-log .research-question
```

After one or more extractors have produced outputs, run the high-level glue
command directly only when you want to override the plan or debug a specific
extractor:

```powershell
.\scripts\research-poc.ps1 run-lecture-pipeline .research-question `
  --title "课程名" `
  --topic "课程主题" `
  --vidclaude-cache D:\path\to\vidclaude-cache `
  --peepshow-output D:\path\to\peepshow-out `
  --webui-output-dir D:\path\to\webui-bundle `
  --vault "%OBSIDIAN_VAULT%" `
  --folder Courses
```

You can provide any one or more of `--vidclaude-cache`, `--peepshow-output`,
`--vidwise-output`, or `--media` plus `--transcript`. The command imports
available extractor outputs, builds the package, exports the BiliNote bundle,
and optionally exports Obsidian notes. Initial pipeline exports are still
drafts; when `--vault` is provided, Obsidian export is skipped unless
`manifest.review_readiness.ready` is already true or you explicitly pass
`--allow-draft-obsidian-export`.

Use the same draft override on `run-ready-lecture-pipeline` or
`recommended-workspace-advance` only when you intentionally want pre-review
Obsidian notes:

```powershell
.\scripts\research-poc.ps1 run-ready-lecture-pipeline D:\path\to\planned-runs\lecture-pipeline-plan.json `
  --vault "%OBSIDIAN_VAULT%" `
  --folder Courses `
  --allow-draft-obsidian-export
```

The manual step-by-step form is still available when debugging an individual
extractor import.

Detect extractor output folders before importing:

```powershell
research-poc detect-extractor-output D:\path\to\maybe-output --project .research-question --topic "课程主题"
research-poc mcp-call detect_extractor_output D:\path\to\probe-args.json
```

The probe recognizes minimum import signatures for vidclaude, peepshow, and
vidwise output directories. It does not modify project data; it reports
`kind`, `confidence`, required missing files, and a ready import command when a
project is provided. Use `--output-json` to persist the probe result for agents
or handoff notes.

When you want the glue layer to detect and run the existing pipeline in one
step, use:

```powershell
research-poc run-detected-lecture-pipeline .research-question D:\path\to\maybe-output D:\path\to\another-output --title "课程名" --topic "课程主题"
```

This command reuses `detect-extractor-output`, selects the first importable
output per extractor kind, and then calls the existing `run-lecture-pipeline`
logic. It still uses the same import registry, package builder, WebUI bundle
exporter, draft Obsidian export gate, and MCP handoff files.

Import extractor output:

```powershell
research-poc import-vidclaude .research-question D:\path\to\vidclaude-cache --topic "课程主题"
research-poc import-peepshow .research-question D:\path\to\peepshow-out --topic "课程主题"
```

Build the lecture package:

```powershell
research-poc build-lecture-package .research-question --title "课程名"
```

This also writes the non-summary navigation outline, local search index, and
study index:

- `lecture-packages/lecture-outline.json`
- `notes/lecture-outline.md`
- `lecture-packages/lecture-search-index.json`
- `notes/lecture-search-index.md`

- `lecture-packages/lecture-study-index.json`
- `notes/lecture-study-index.md`

The outline groups contiguous full timeline items into chapter-like navigation
sections by source video, larger time gaps, and obvious heading cues. It is not
a summary: every outline entry keeps its timestamp, source segment IDs,
transcript/OCR snippets, review status, material types, and visual-retention
recommendation. Rebuild it explicitly after manual package JSON edits:

```powershell
research-poc build-lecture-outline .research-question
research-poc mcp-call build_lecture_outline D:\path\to\outline.args.json
```

The search index is a deterministic local keyword index over timeline
transcripts, OCR/visual text, structured formula/table/code blocks, material
types, and extractor signals. It is meant for quick human lookup and stable
Agent calls:

```powershell
research-poc build-lecture-search-index .research-question
research-poc search-lecture .research-question "收益率" --limit 5
research-poc mcp-call search_lecture D:\path\to\search.args.json
```

The study index groups the full timeline into concept/definition, procedure,
example, formula, table, code, keep-image, and review-queue buckets while
preserving timestamps and source segment IDs. Its Markdown output embeds key
frames and adds a small review checklist to each entry, so Obsidian can be used
for later study-card or chapter-note cleanup without losing the original
evidence location. Rebuild it explicitly after manual package JSON edits:

```powershell
research-poc build-lecture-study-index .research-question
research-poc mcp-call build_lecture_study_index D:\path\to\study-index.args.json
```

The same command also writes draft study cards:

- `lecture-packages/lecture-study-cards.json`
- `notes/lecture-study-cards.md`

These are evidence cards, not final AI-authored flashcards. They keep each
timeline item's raw transcript, OCR/visual text, structured visual blocks, key
frames, source IDs, and a blank human `final_card` field for later cleanup.
Each card also carries `evidence.visual_retention`, rendered in Markdown as
`视觉保留判断`, so humans can see whether a visual should be kept as an image,
reviewed before text-only reduction, or treated as a text-only candidate.
The same `visual_retention` object is now written onto each package timeline
item, copied into WebUI `timeline.json`, and shown in the BiliNote review panel,
so image-retention decisions stay visible before and after export.

Check likely missing-information gaps before importing into BiliNote:

```powershell
research-poc audit-lecture-package .research-question
```

This writes `notes/lecture-quality-report.md` and
`lecture-packages/lecture-quality-audit.json`. Use the report to prioritize
segments where transcript, OCR/visual text, or key frames may be missing.
The same report also includes `时间覆盖盲区`: gaps between merged timeline
segments, including leading/trailing uncovered ranges when the source duration
is known. Treat those gaps as candidates for denser extraction or manual
inspection before considering a lecture fully captured.
When a WebUI bundle is exported, `manifest.json -> time_gap_recapture` turns
those blank ranges into ffmpeg midpoint-frame commands. Use them to capture a
quick inspection frame for each uncovered range before deciding whether to
rerun vidclaude/peepshow with denser settings or create manual timeline entries.
Obsidian `review-queue.md` uses the same risk score, so the highest-risk gaps
appear first rather than merely following timeline order.

Export a BiliNote handoff bundle:

```powershell
research-poc export-webui-bundle .research-question --output-dir D:\path\to\webui-bundle
```

The WebUI bundle is self-contained for copied key frames: available
`frame_paths` are copied into `assets/`; `note.md`, `study-index.md`,
`study-cards.md`, and `review.html` use bundle-local `assets/...` references, and
`assets/asset-manifest.json` records copied and missing frame paths. This lets
BiliNote review and agent handoff keep working even if the original extractor
cache is later moved. If a source frame becomes available later, use
`research-poc repair-bundle-assets D:\path\to\webui-bundle` or the generated
`mcp-repair-bundle-assets.args.json` to recopy missing bundle assets without
rerunning video extraction. In the patched BiliNote review UI, the same repair
is exposed as `修复资产` when the task board sees `关键帧不可用`. Successful
asset repair also writes the repaired bundle-local frame paths back to the
source `lecture-package.json`, so a later Obsidian export copies from stable
bundle assets instead of returning to the original extractor cache path.

In BiliNote:

1. Open the frontend URL.
2. To start from a local media file, use `从本地视频创建课程抽取工作区`, paste the
   video path, confirm the title, ASR preset/model, language, max frame count,
   and sampling fps, then click `创建`. BiliNote will call the local
   `prepare-lecture-workspace` glue command and open the created workspace as a
   task. Use `保守` for quick trial plans, `标准` for ordinary lessons, or
   `密集` for long or visually dense lectures; manual max frame/fps edits remain
   available. ASR preset/model, language, max frame count, and sampling fps are
   remembered locally in the browser for the next workspace creation; media
   path, title, and output root are still entered per video.
3. If a workspace already exists, use `导入课程抽取工作区` and select the
   `planned-runs` directory created by `prepare-lecture-workspace`.
4. Open `抽取工作区` to inspect ready/missing state, extractor commands, pipeline
   commands, MCP calls, and planned output paths. The MCP calls section includes
   recommended route/status/queue, workspace advance/log, guarded ASR/extractor
   runs, and the preview-first `apply_bilinote_patch` entry when the generated
   workspace contains the matching MCP args files.
   The local tool preflight area summarizes recommended-route tasks as cards:
   next route, runnable count, ready count, and missing-tool count, so the UI can
   act like a task board instead of only a command list.
   Missing local dependencies are also shown as `缺失工具任务` with the relevant
   reason and a copyable install/check hint for ffmpeg, visual extractors, and
   ASR tools.
   The next-step section can also call the BiliNote patch action directly:
   `预览 BiliNote patch` is read-only, while `修复 BiliNote patch` explicitly runs
   the packaged patch installer with backups enabled.
   Workspace import also shows the current BiliNote patch readiness counts
   (`installed`, `missing`, `drift`, `total`) so the operator can see whether
   the UI shell is ready before running review.
   Use the top-level `刷新` button to re-read the current workspace after running
   extractor commands outside BiliNote, after a timeout, or after waiting for a
   long external process to finish.
   The top of the panel shows the current next step, whether a recommended
   pipeline command is runnable, and whether the planned BiliNote bundle is
   already importable.
   Once the bundle is importable, use `导入知识包` in the same panel to open it as
   a normal BiliNote review task without returning to the manual import form.
   The panel also shows ASR readiness: selected preset, ffmpeg/tool availability,
   expected raw ASR output, and whether a normalized transcript is already ready.
   Use ASR `预览` to record the guarded ASR plan, or `运行并归一化` to run the
   selected local ASR runner and refresh workspace status after normalization.
   The ASR environment card also surfaces the embedded `asr-env-status`
   health check, including whether the ASR command/module is ready, the next
   environment action, and a copy button for `mcp-asr-environment-status`.
   It also shows the ASR setup plan generated by `plan-asr-setup`: current
   status, target venv directory, next setup command, ordered setup steps, and
   copy buttons for `mcp-plan-asr-setup`, JSON, and Markdown handoff files.
   When a normalized transcript path exists, use `复制 ASR 导入命令` to copy the
   transcript-only import command with the real file path filled in.
   The same workspace panel includes `本地工具预检`, which surfaces the plan's
   ffmpeg, ASR runner, and visual extractor availability so you can choose the
   already-installed route before running expensive commands. It also shows a
   `推荐首跑` route derived from installed tools, current plan, and current
   readiness: vidclaude first when available and unfinished, then peepshow,
   vidwise fallback, and ASR as the strong transcript companion. Routes whose
   planned output already exists are labeled `ready`, and the recommended card
   prefers the first available unfinished route. Each recommended route has copy,
   preview, and run controls wired to the guarded ASR/extractor runners; run
   buttons stay disabled for routes whose local tool is missing.
   Use `运行设置` to set the ASR/extractor runner timeout in seconds. The value is
   remembered locally in the browser and is passed to recommended routes, ASR
   preview/run, extractor preview/run, and planned pipeline command execution.
   If a backend runner times out, the guarded ASR runner, visual extractor
   runner, and generic planned-command runner now return a structured result with
   `status: timeout`, `returncode: null`, preserved stdout/stderr tails, and a
   persisted command-log entry instead of surfacing an unhandled Python
   exception. BiliNote keeps the current workspace or bundle context for
   follow-up inspection. The recent result panel highlights timeout separately
   and suggests checking command history/outputs or increasing the runner
   timeout before retrying.
   ASR execution also reports `command_not_found` when the planned executable
   cannot be launched and `output_missing` when the ASR command exits
   successfully but no JSON transcript is found. Recommended route queues stop
   on these ASR states, as well as `blocked`, `failed`, `normalize_failed`, and
   `timeout`, so the operator can inspect the run log instead of continuing a
   route that has not produced usable transcript evidence.
   For `vidclaude` / `peepshow` / `vidwise`, use the extractor `预览` / `运行`
   buttons to call the guarded extractor runner. Pipeline/health commands still
   use the generic planned-command runner. After preview/execution, BiliNote
   receives the refreshed workspace and updates the ready/missing state plus the
   command history in the panel. Use `预览下一步` / `执行下一步` to delegate to
   `lecture-next`, which only runs safe local glue steps selected by health. Fill
   the Obsidian vault/folder fields in the same panel before running next-step
   actions that may export or refresh notes. The panel shows recent safe-next
   action history, ASR run history, and visual extractor run history separately
   from generic pipeline command history.
5. After `run-ready-lecture-pipeline` creates the bundle, use `导入课程知识包`.
6. Select the `webui-bundle` directory.
7. Open `课程复核`.
8. Review and correct transcript, OCR/visual observations, and key frames.
9. Use the coverage audit summary to check transcript, visual text, key frame,
   review, correction, structured-visual, formula/table/code counts, and time
   coverage gaps before deciding the package is complete.
10. Use `待复核` to focus unchecked segments, `已修正` to inspect segments where transcript/OCR text has been changed, `缺口` to focus quality-audit issues from `lecture-quality-report.md`, or the `公式`/`表格`/`代码` material filters to audit visual structures that are easy to lose in text-only extraction. The structured-material review strip shows reviewed/total counts and can jump to the next unconfirmed formula, table, or code segment. Formula/table/code items without imported `structured_visual` are flagged as `structured_visual_without_structure`, even if OCR text already exists.
11. Check the review readiness gate before final export. It reports unchecked
   timeline items, unchecked structured material, unreviewed risk items, and
   visual/frame gaps. Click a gate metric to clear the search box, apply the
   matching filters, and jump to the first matching problem segment. `保存并刷新`
   will ask for confirmation if the gate still has unresolved risks; `保存`
   remains available for draft review notes.
   The imported bundle also exposes `review_tasks`; BiliNote renders this as
   `复核处理任务`, a compact task board covering quality gaps, pending human
   confirmation, key-frame recapture, time-gap recapture, OCR backfill, and
   structured visual extraction. Click a review task to focus the closest
   relevant queue; frame recapture, time-gap recapture, OCR backfill, and
   structured visual extraction tasks also scroll directly to their matching
   repair panel below the task board. When `manifest.json -> repair_status`
   marks a repair path as `updated` or `not_needed`, BiliNote no longer counts
   that path as an open repair task even if the original plan still has items.
12. If `关键帧补采样计划` appears, copy one or all ffmpeg commands to capture
   missing key frames for the flagged timeline items. The commands are generated
   from `manifest.json -> frame_recapture`; they are not executed automatically.
   Use `刷新计划` to re-read the current plan, or `执行补帧` to explicitly run the
   local `run-frame-recapture --execute` workflow through the BiliNote backend.
   Successful runs backfill the generated frame into the WebUI timeline and the
   source lecture package when available, then show success/failure/backfill
   counts in the review panel. Rerun package/WebUI export if you need to rebuild
   all derived notes after the backfill.
13. If `时间盲区补采样计划` appears, copy one or all ffmpeg commands to sample
   the midpoint of uncovered timeline ranges. These frames are for inspection:
   if a gap frame contains new lecture content, rerun extraction with denser
   sampling or fill the gap form in BiliNote to add a manual timeline entry
   before final export. Manual gap entries are saved through `review-notes.json`
   with `manualTimelineItem: true`, written back to the source package, and are
   idempotent by `sourceSegmentIds` / `manualTimelineId` so repeated refreshes do
   not duplicate the same gap entry. If the midpoint frame command has already
   produced an image, keep `保留盲区中点帧` checked so the manual timeline item
   carries that frame into the source package, refreshed WebUI bundle, and
   Obsidian visual assets. Manual gap entries also carry an `evidence` block
   with the original gap range, midpoint, source video key, sampled frame path,
   and creation method; BiliNote shows it as `证据链`, and Markdown/Obsidian
   exports render the same provenance before the transcript.
14. If `OCR 回填` reports candidates, first use `刷新/导入` with an optional
   external OCR JSON path to backfill manually corrected OCR results, or use
   `本地 OCR` to explicitly call local CaptiOCR/Tesseract for available key
   frames. Set the OCR language and CaptiOCR root in the same block; BiliNote
   remembers those values locally for the next review session. External JSON
   should contain items such as
   `{"index": 1, "text": "画面文字"}`. Successful runs update `timeline.json`,
   `manifest.coverage`, and the source `lecture-package.json` when available.
   The same CaptiOCR resolver is used by `local-tool-inventory`,
   `lecture-health`, and `run-ocr-backfill`: it checks `LECTURE_CAPTIOCR_ROOT`
   first, then local mirrors such as
   `%WORKSPACE_ROOT%\tool-source-review\captiocr`. Use the environment variable
   when your checkout lives elsewhere, so CLI, MCP, and BiliNote agree on the
   same OCR helper path.
   Every `run-ocr-backfill` preview/import/run also writes
   `ocr-backfill-input-template.json` into the WebUI bundle and records the path
   in `manifest.ocr_backfill.input_template_json`. The template keeps timeline
   index, timestamp, image path, current visual text, material types, and blank
   `text` / `notes` fields, so CaptiOCR/Tk, another OCR tool, a human reviewer,
   or an agent can fill one stable JSON file and pass it back with `--input-json`.
   Since 2026-06-03 09:03:54 (Codex GPT-5), the same run also writes
   `ocr-backfill-handoff.md` and `ocr-backfill-handoff.json`. The handoff
   records CaptiOCR resolver evidence, runner availability, the MCP command,
   import schema, unresolved timeline indexes, and the exact frame paths that
   still need screen-text transcription. Use this as the human/Tk/OCR/agent
   transfer file when the first OCR pass is incomplete.
15. If `结构化视觉` reports formula/table/code candidates, copy its JSON template
   or tool commands and process the referenced screenshots with Docling, MinerU,
   Marker, PaddleOCR, or manual correction. Import results with JSON rows such
   as `{"index": 1, "type": "table", "markdown": "| A | B |"}`. This backfills
   `structured_visual` and `visual_text` into the WebUI timeline and source
   package when available, and clears `structured_visual_without_structure`
   quality risks for those items. Imported structured results are shown as a separate
   `结构化视觉结果` block in the active timeline item and are exported into
   Obsidian `transcript.md` / `screen-text.md` / `timeline.md` /
   `visual-assets.md` / `structured-materials.md` / `evidence-map.md`.
   WebUI bundle export and every `run-visual-structure` preview/import write
   `visual-structure-input-template.json` into the bundle and record it as
   `manifest.visual_structure.input_template_json`. The template keeps each
   formula/table/code candidate's timeline index, screenshot path, current
   visual text, existing structured entries, blank `markdown` / `notes` fields,
   and example Docling, Marker/MinerU, and PaddleOCR output shapes. Use that
   file as the handoff contract for external layout/OCR tools, human cleanup, or
   MCP-driven import.
   Since 2026-06-03 09:09:51 (Codex GPT-5), every preview/import also writes
   `visual-structure-handoff.md` and `visual-structure-handoff.json`. The
   handoff records available Docling/Marker/MinerU/PaddleOCR paths, per-frame
   commands, MCP import command, unresolved timeline indexes, and the exact
   screenshots that need formula/table/code/diagram recovery. Use this file when
   a human, external parser, or AI agent must decide whether material can be
   downgraded to text or must remain as Markdown tables, LaTeX, code blocks, or
   preserved images.
   For one-off correction, use the active item `人工结构化视觉` editor directly:
   paste LaTeX, a Markdown table, or a code block, choose the type, then save.
   BiliNote writes the manual entry back as `structured_visual` with source
   `manual_review`, appends it into `visual_text`, refreshes coverage, and the
   next `保存并刷新` carries it into the source package, WebUI bundle, and
   Obsidian export.
16. Use `重新读取` when external commands, manual `timeline.json` edits, OCR
   imports, or late-running backfills have changed the current bundle on disk
   and you want the native review panel to reload it without creating a new
   BiliNote task.
17. Use `保存` to persist review notes into the bundle, or `保存并刷新` to also run
   the local `refresh-lecture-review` workflow and reload the refreshed bundle.
   Fill the Obsidian vault path before `保存并刷新` when you also want refreshed
   course notes exported to Obsidian. BiliNote remembers the last vault/folder
   values locally for the next course review. The default vault is
   `%OBSIDIAN_VAULT%`; clear the field when you
   only want to refresh POC/WebUI outputs. Before refreshing outputs, BiliNote
   saves the current review notes, runs the machine `audit-bundle-readiness`
   gate, reloads `manifest.review_readiness`, and asks for confirmation if
   blockers remain. This keeps the human UI and MCP/CLI agent gate on the same
   readiness decision. Obsidian export copies available key-frame files into
   the course folder `assets/` directory, rewrites exported Markdown to use
   relative `assets/...` links, and writes `assets/asset-manifest.json` with
   copied and missing frame paths so the knowledge base does not depend on
   temporary extractor directories. WebUI bundles and Obsidian course exports
   also write `transcript.md` as the full spoken/subtitle layer,
   `screen-text.md` as the full screen-text/OCR layer,
   `structured-materials.md` to concentrate formula/table/code, structured
   visual, and keep-image items in one reviewable note, and `evidence-map.md`
   to trace each timeline item back to transcript/OCR/frame/source evidence.
   WebUI bundles and Obsidian course exports also write `source-artifacts.json`
   / `source-artifacts.md`, which index the original
   vidclaude/peepshow/vidwise output files kept for traceability. The patched
   BiliNote backend loads the same index into the bundle payload, and the native
   review panel exposes copy buttons for both index paths.
   Obsidian course exports also write `obsidian-export.json`, a machine-readable
   page manifest for CLI/MCP agents. It labels each Markdown page as navigation,
   full-information, review, study, visual, or traceability, and exposes stable
   entrypoints such as `full_speech_text`, `full_screen_text`, `evidence_map`,
   and `source_artifacts_json`.
   Each Obsidian course export writes `obsidian-export-status.json/md`
   automatically after generating `obsidian-export.json`. Use
   `research-poc obsidian-export-status <course-folder-or-obsidian-export.json>`
   or MCP `obsidian_export_status` to revalidate that the manifest pages and
   agent entrypoints still exist after moving, syncing, or editing the exported
   course folder. The status check also reads `assets/asset-manifest.json` and
   `source-artifacts.json` so missing key frames are treated as blockers and
   missing original extractor artifacts are surfaced as traceability risks. Add
   `--write` to refresh `obsidian-export-status.json/md` beside the manifest.
   Each Obsidian course export also writes
   `mcp-obsidian-export-status.args.json`, so agents can run the status check
   with `research-poc mcp-call obsidian_export_status <that-args-file>` without
   constructing arguments by hand. The export also writes
   `mcp-export-lecture-obsidian.args.json`; when status validation reports
   missing pages, core entrypoints, or visual assets, its `next_action` points
   back to MCP `export_lecture_obsidian` with that args file. When the next
   action is directly callable, `obsidian-export-status.md` includes a
   `下一步命令` PowerShell block for copy/paste or agent handoff.
   When the issue is a traceability warning, such as missing optional original
   extractor artifacts, the report renders `下一步参考文件` with
   `source-artifacts.md/json` instead of inventing a repair command.
   WebUI bundle `README.md` includes the same post-Obsidian-export status-check
   handoff so a reviewer can validate the final course folder after running
   `refresh_lecture_review_outputs`.
   The exported course `index.md` links `[[obsidian-export-status|导出状态]]`
   so human reviewers can open the status report from the course homepage.

Refresh POC outputs after BiliNote review:

```powershell
research-poc refresh-lecture-review .research-question D:\path\to\webui-bundle\review-notes.json
```

The bundle README and `manifest.json -> post_review.refresh_command` contain the
exact command for that bundle. For agents, use the generated
`mcp-refresh-lecture-review.args.json`:

```powershell
research-poc mcp-call refresh_lecture_review_outputs D:\path\to\webui-bundle\mcp-refresh-lecture-review.args.json
```

If the referenced review file does not exist yet, this shared refresh workflow
creates a no-op `{"reviews": []}` review file, returns
`default_review_notes_created: true`, and continues refreshing downstream
outputs. This removes a manual file-creation step for ready bundles without
silently approving them: Obsidian export still reruns the same readiness gate.

The same bundle now writes repair-call argument files for agent-assisted
follow-up work:

```powershell
research-poc mcp-call run_frame_recapture_plan D:\path\to\webui-bundle\mcp-run-frame-recapture.args.json
research-poc mcp-call run_ocr_backfill D:\path\to\webui-bundle\mcp-run-ocr-backfill.args.json
research-poc mcp-call run_visual_structure_plan D:\path\to\webui-bundle\mcp-run-visual-structure.args.json
research-poc mcp-call repair_bundle_assets D:\path\to\webui-bundle\mcp-repair-bundle-assets.args.json
research-poc mcp-call refresh_bundle_repair_status D:\path\to\webui-bundle\mcp-refresh-repair-status.args.json
research-poc mcp-call audit_bundle_readiness D:\path\to\webui-bundle\mcp-audit-bundle-readiness.args.json
research-poc mcp-call audit_knowledge_coverage D:\path\to\webui-bundle\mcp-audit-knowledge-coverage.args.json
research-poc mcp-call bundle_next_action D:\path\to\webui-bundle\mcp-bundle-next-action.args.json
research-poc mcp-call bundle_source_artifacts D:\path\to\webui-bundle\mcp-bundle-source-artifacts.args.json
```

Use `research-poc audit-knowledge-coverage D:\path\to\webui-bundle` when the
question is "which knowledge channels are still under-covered?" rather than
"is this ready for final export?". It reads the same bundle files and writes
`knowledge-coverage.json` / `knowledge-coverage.md`, covering speech,
OCR/screen text, visual frames, formula/table/code structure, time-axis gaps,
and original extractor artifacts.
`bundle-next-action` refreshes this audit when `refresh=true` and checks it
after machine repair/readiness blockers but before final export. That means a
bundle that is otherwise ready can still be routed to OCR, frame recapture, or
visual-structure repair when the no-loss coverage map shows a direct content
gap. Source-artifact traceability gaps are kept as `weak` rather than hard
export blockers.

Use `research-poc bundle-source-artifacts D:\path\to\webui-bundle` or the MCP
equivalent when an agent only needs to inspect original extractor traceability.
It is read-only by default. Pass `--refresh --write` only when you need to
rebuild `source-artifacts.json` / `source-artifacts.md` from
`manifest.sources`.

`run_visual_structure_plan` accepts the simple internal format
`{"items":[{"index":1,"type":"table","markdown":"..."}]}`, but it also
normalizes common outputs from existing layout/OCR tools. A single-candidate
bundle can import tool JSON without an explicit index; the runner assigns the
only candidate's timeline index. Supported shapes include:

- Docling-style or generic `tables` with `table_cells` / `cells`.
- Marker/MinerU-style `blocks`, `children`, `para_blocks`, or `content_list`.
- PaddleOCR/PP-Structure-style rows with `type` and `res.html` / `res.text`.
- Direct `markdown`, `text`, `latex`, `table_markdown`, `structured_text`, or
  `html` fields.

This keeps Docling, MinerU, Marker, and PaddleOCR as external specialized tools
while `lecture-extract` only performs schema normalization and backfill into the
timeline/package.

The patched BiliNote review panel exposes the same path under
`复核处理任务 -> 结构化视觉`. The `模板` button copies both the internal
`items` shape and examples for Docling-style tables, Marker/MinerU blocks, and
PaddleOCR `res.html` / `res.text`. Paste the resulting tool JSON path into the
input and click `导入 JSON`; when the bundle has a single structured-visual
candidate, the JSON can omit `index`.

These files default to preview/import-safe settings. Set `execute: true` inside
the relevant JSON only when you intentionally want the local runner to execute.
Each export and repair runner also updates `manifest.json -> repair_status`,
which summarizes frame recapture, time-gap inspection, OCR backfill, and
structured visual extraction with `status`, `count`, `last_run`,
`last_backfill`, and the next agent-call hint. The patched BiliNote review panel
shows this under `复核处理任务 -> 修复状态回流`, so a human reviewer can see
whether each repair path is still pending, requires manual judgment, has run
without updating, failed, or already backfilled data. Each repair status card
also has an `MCP` copy button for the exact `research-poc mcp-call ...` command
for that repair path. If you manually edit `manifest.json` / `timeline.json` or
import repair results outside the built-in runners, run
`research-poc refresh-repair-status D:\path\to\webui-bundle` or the
`refresh_bundle_repair_status` MCP call above to recalculate only the status
block without rebuilding the full lecture package. In the patched BiliNote UI,
the `复核处理任务` board also has `同步状态`, which calls the same local
`refresh-repair-status` workflow through the BiliNote backend and reloads the
current bundle.

For AI-agent handoff, prefer the single next-action entry first:

```powershell
research-poc bundle-status-report D:\path\to\webui-bundle
research-poc mcp-call bundle_status_report D:\path\to\webui-bundle\mcp-bundle-status-report.args.json
research-poc bundle-next-action D:\path\to\webui-bundle
research-poc mcp-call bundle_next_action D:\path\to\webui-bundle\mcp-bundle-next-action.args.json
research-poc bundle-advance D:\path\to\webui-bundle
research-poc mcp-call bundle_advance D:\path\to\webui-bundle\mcp-bundle-advance.args.json
research-poc bundle-advance-log D:\path\to\webui-bundle
research-poc mcp-call bundle_advance_log D:\path\to\webui-bundle\mcp-bundle-advance-log.args.json
research-poc bundle-advance-queue D:\path\to\webui-bundle --max-steps 4
research-poc mcp-call bundle_advance_queue D:\path\to\webui-bundle\mcp-bundle-advance-queue.args.json
research-poc prepare-review-session D:\path\to\webui-bundle
research-poc mcp-call prepare_review_session D:\path\to\webui-bundle\mcp-prepare-review-session.args.json
```

`bundle-status-report` writes `bundle-status.json` / `bundle-status.md` as a
compact dashboard for humans, BiliNote UI, and agents. It reuses existing bundle
state instead of adding a new workflow: next action, review readiness, knowledge
coverage, source-artifact summary, human-readable entrypoints, MCP args files,
latest `bundle-advance` record, and any Obsidian export artifacts found in that
record. Use it first when an agent needs to decide whether to repair, review,
export, or inspect missing evidence.
Since 2026-06-03 09:16:40 (Codex GPT-5), the same report also exposes
`repair_handoffs` for generated OCR/structured-visual repair files such as
`ocr-backfill-handoff.md/json` and `visual-structure-handoff.md/json`. The
patched BiliNote `Bundle 状态` panel renders these as a `Repair handoff` block
with ready/missing state and copy buttons, so a human or agent can jump from the
UI status dashboard to the exact OCR/layout handoff instead of hunting through
the bundle directory.

`prepare-review-session` also embeds the source-artifact summary, index paths,
`mcp-bundle-source-artifacts.args.json`, and missing artifact samples into
`review-session.json` / `review-session.md`, so a human or agent can audit
traceability from the same handoff file used for blockers and review targets.
The patched BiliNote `Agent 下一步 -> 复核会话` block renders the same data
under `原始证据追溯` and can copy the source-artifact MCP args path.

It refreshes repair/readiness status by default, then returns one safe
`next_action`: run a machine repair path such as structured-visual extraction,
continue human review for blockers/time gaps, or refresh/export when the bundle
is ready. The command never executes heavy repair tools by itself; it returns
the matching MCP tool, args JSON, and command for the next step. `bundle-advance`
uses that decision to advance one preview/import-safe step. It can now also
route hard knowledge-coverage blockers to the existing repair tools: screen-text
gaps call `run_ocr_backfill`, visual-frame gaps call `run_frame_recapture_plan`,
and formula/table/code structure gaps call `run_visual_structure_plan`. It does
not run ffmpeg/OCR execution or final output refresh unless you explicitly pass
`--execute` or `--refresh-outputs`.
When the bundle is already ready and `bundle-advance --refresh-outputs` is used,
the ready/export path reads `mcp-refresh-lecture-review.args.json` and calls the
same shared refresh workflow above. Missing `review-notes.json` therefore gets
the same no-op review-file fallback, but the export gate is not bypassed:
refreshed WebUI/Obsidian export still reruns `review_readiness`, and remaining
blockers return `obsidian_export_blocked`.
Every `bundle-advance` call appends `bundle-advance-runs.jsonl` and refreshes
`bundle-advance-runs.md`, so later humans or agents can inspect what was tried,
where it stopped, and what the next action became.
`bundle-advance-queue` repeats the same conservative advance step until one of
four stop conditions: a human/manual blocker, a repeated same next action
(`stalled`), readiness/export state, or `--max-steps`.
In the patched BiliNote review UI, the same decision is available as
`Agent 下一步 -> 判断下一步`; it calls the BiliNote backend
`/lecture_bundle/next_action`, updates the current bundle, and exposes a copy
button for the returned CLI/MCP command. Use `定位任务` to jump from the returned
next action to the matching review filter, repair status board, OCR backfill,
frame recapture, time-gap inspection, structured-visual panel, or final
save/refresh controls. Use `推进一步` for the same conservative `bundle-advance`
behavior from the UI; it only performs preview/import-safe progress by default.
Use `推进队列` to run the same bounded, stalled-aware conservative queue from
the UI. It stops on human/manual blockers, repeated next actions, readiness, or
the configured step limit.
Use `推进历史` to read the same persisted advance log from BiliNote.

`prepare-review-session` writes `review-session.json` and `review-session.md`
beside the WebUI bundle. The session handoff includes the local `review.html`
file URL, the expected `review-notes.json` path, current readiness blockers,
the next CLI/MCP action, post-review refresh MCP args, and a
`review_targets` list derived from `timeline.json` plus readiness samples. Each
target keeps the timeline index, time range, reasons such as `pending_review`,
`structure_gap`, or `asset_gap`, quality issues, material types, evidence
excerpt, asset paths, and a suggested UI filter. Use it when a human reviewer or
an AI agent needs one stable entry point instead of manually opening
`manifest.json`, `timeline.json`, and multiple generated args files.
New WebUI bundles also include `mcp-prepare-review-session.args.json`, and the
patched BiliNote review panel exposes the same path through `Agent 下一步 ->
复核会话`. That button creates the session handoff through the BiliNote backend,
opens the standalone `review.html` when the browser allows local file URLs, and
keeps the next machine/human action plus the first review targets visible in the
same panel. BiliNote `load_lecture_bundle` also reads an existing
`review-session.json` back into the loaded bundle as `review_session`, so a
refresh, task reload, or later return to the same course keeps the review target
handoff visible without regenerating the session.

Before final export or agent handoff, run:

```powershell
research-poc audit-bundle-readiness D:\path\to\webui-bundle
```

This writes `manifest.json -> review_readiness` with `ready`, `blockers`,
`warnings`, `counts`, sample timeline indexes, and `next_action`. It mirrors the
BiliNote readiness gate in a CLI/MCP-friendly format, so an agent can decide
whether to keep repairing/reviewing or proceed to refreshed WebUI/Obsidian
export. The gate also blocks on `asset_gap`: a timeline item with a key-frame
asset marked `copied=false` or a bundle-local asset path that no longer exists.
In the patched BiliNote UI, the same check appears as `机器收口检查` with a
`检查收口` button; it calls the BiliNote backend, runs
`audit-bundle-readiness`, writes the refreshed `review_readiness`, and reloads
the current bundle. The local UI gate also exposes `关键帧不可用` as a focusable
review metric.

Refresh and export Obsidian in one step:

```powershell
research-poc refresh-lecture-review .research-question D:\path\to\webui-bundle\review-notes.json --vault "%OBSIDIAN_VAULT%" --folder Courses
```

When `--vault` is provided, this command first refreshes the WebUI bundle and
then checks `manifest.review_readiness`. If blockers remain, Obsidian export is
skipped and the JSON result includes `obsidian_export_blocked`. Use
`--allow-blocked-export` only after a human explicitly accepts the remaining
blockers:

```powershell
research-poc refresh-lecture-review .research-question D:\path\to\webui-bundle\review-notes.json --vault "%OBSIDIAN_VAULT%" --folder Courses --allow-blocked-export
```

The MCP equivalent is `allow_blocked_export: true` on
`refresh_lecture_review_outputs`. BiliNote only sets this after the reviewer
confirms the machine readiness warning. This is separate from
`allow_draft_obsidian_export`, which applies only to pre-review pipeline
imports.

## 6. MCP Tools

Check available MCP-compatible tools:

```powershell
research-poc mcp-tools
research-poc-mcp --list-tools
```

Important tools for agents:

- `detect_asr_runners`
- `plan_asr_run`
- `normalize_asr_output`
- `run_asr_plan`
- `asr_run_log`
- `run_extractor_plan`
- `extractor_run_log`
- `prepare_lecture_workspace`
- `plan_lecture_pipeline`
- `status_lecture_pipeline`
- `lecture_import_status`
- `lecture_project_health`
- `lecture_next_step`
- `lecture_action_log`
- `run_planned_lecture_command`
- `lecture_command_log`
- `recommended_route_status`
- `recommended_route_queue`
- `recommended_workspace_advance`
- `recommended_workspace_advance_log`
- `run_recommended_route`
- `run_ready_lecture_pipeline`
- `run_lecture_pipeline`
- `build_lecture_package`
- `audit_lecture_package`
- `import_lecture_review`
- `refresh_lecture_review_outputs`
- `export_lecture_obsidian`
- `export_webui_bundle`
- `run_frame_recapture_plan`
- `run_ocr_backfill`
- `run_visual_structure_plan`
- `refresh_bundle_repair_status`
- `audit_bundle_readiness`
- `audit_knowledge_coverage`
- `smoke_real_extractor`
- `smoke_lecture_e2e`
- `smoke_bilinote_lecture`

## 7. Verification Log

### 2026-06-02 09:31:26 | Codex (GPT-5)

- Re-ran the patched BiliNote frontend production build after a previous
  transient Vite `build-html` error. `npm run build` completed successfully
  without changing `vite.config.ts`.
- Verified frontend types with `npx tsc --noEmit`.
- Verified the lecture extraction project with `python -m pytest -q`: 120
  tests passed.
- Verified the local MCP config with
  `scripts/write-mcp-config.ps1 -Client codex -Validate`: 55 tools.
- Verified the installed BiliNote lecture patch with
  `scripts/install-bilinote-lecture-patch.ps1 -Check -FailOnDrift`: 12/12
  files installed, 0 drift.

### 2026-06-02 09:36:20 | Codex (GPT-5)

- Added strict real-lecture gates to `smoke-lecture-e2e` and MCP
  `smoke_lecture_e2e`: explicit real-media requirement, minimum media duration,
  transcript presence, visual asset presence, and a convenience
  `--strict-real-lecture` mode.
- Targeted regression passed for real lecture smoke orchestration, required ASR
  failure reporting, strict fixture rejection, and CLI/MCP argument forwarding:
  4 tests passed.

### 2026-06-02 09:41:47 | Codex (GPT-5)

- Added `find-lecture-media` and MCP `find_lecture_media` to scan local files or
  directories for video candidates suitable for strict real-lecture validation.
- The finder reuses `probe_video()`/ffprobe, filters by duration, records probe
  failures when requested, and emits a ready strict `smoke-lecture-e2e` command
  for each candidate.
- Actual local project scan found no qualifying real lecture media: only short
  generated fixtures and invalid placeholder MP4 files were present. This keeps
  the next acceptance run honest; it needs an external/downloaded course clip.

### 2026-06-02 09:47:51 | Codex (GPT-5)

- Added `prepare-lecture-acceptance` and MCP `prepare_lecture_acceptance`.
- The command scans candidate media, writes
  `real-lecture-acceptance-plan.json`,
  `real-lecture-acceptance-handoff.md`, and per-candidate
  `mcp-smoke-lecture-e2e-candidate-*.args.json` files.
- Actual project-local run wrote a no-candidate handoff under
  `tmp/real-lecture-acceptance`, confirming the empty-result path is
  reproducible and ready for a real download/course directory.

### 2026-06-02 09:53:08 | Codex (GPT-5)

- Added `prepare-lecture-sample-clip` and MCP
  `prepare_lecture_sample_clip`.
- The command reuses local ffmpeg resolution, defaults to preview mode, and only
  writes a clip when `--execute` is passed.
- Output includes source/clip metadata, the ffmpeg command, a recommended strict
  `smoke-lecture-e2e` command, and `recommended_mcp_args`.
- Actual preview against the local 2-second fixture succeeded and generated the
  expected sample path and strict smoke command without writing a clip.

### 2026-06-02 09:57:00 | Codex (GPT-5)

- Updated `prepare-lecture-sample-clip` so preview/execution also writes
  `mcp-smoke-lecture-e2e-sample.args.json` beside the planned/generated sample
  clip.
- The command now returns `mcp_args_path` and a ready
  `mcp-call smoke_lecture_e2e ...` command, reducing manual JSON copying before
  strict validation.
- Actual preview confirmed the args file path and MCP command are emitted.

### 2026-06-02 10:01:35 | Codex (GPT-5)

- Enhanced `prepare-lecture-acceptance` so videos rejected as `too_long` now
  become sample-clip preview suggestions instead of dead-end rejections.
- The plan writes per-video
  `mcp-prepare-lecture-sample-clip-long-candidate-*.args.json` files and adds a
  "Long Video Sample Suggestions" section to the handoff Markdown.
- Actual command run with a deliberately tiny max-duration threshold generated
  sample suggestions and MCP args from local fixture videos, proving the
  long-video handoff path works without executing ffmpeg.

### 2026-06-02 10:07:05 | Codex (GPT-5)

- Added `lecture-acceptance-next` and MCP
  `lecture_acceptance_next_action`.
- The helper reads `real-lecture-acceptance-plan.json`, prefers a direct
  `smoke_lecture_e2e` run when available, otherwise returns the first
  `prepare_lecture_sample_clip` suggestion.
- It writes `mcp-lecture-acceptance-next-action.args.json` beside the plan so
  agents can re-query the next action without rebuilding the acceptance plan.
- Actual run against the too-long fixture acceptance plan returned
  `sample_clip_needed` and the expected `prepare_lecture_sample_clip` MCP
  command.

### 2026-06-02 10:13:54 | Codex (GPT-5)

- Added `lecture-acceptance-advance` and MCP
  `lecture_acceptance_advance`.
- The helper advances one preview-safe acceptance step: it runs
  `prepare_lecture_sample_clip` in preview mode for sample suggestions and
  blocks on direct strict-smoke actions instead of launching ASR/extractor work.
- Actual run against the too-long fixture acceptance plan returned `advanced`
  with a sample-clip preview result and generated strict-smoke MCP args.

### 2026-06-02 10:18:42 | Codex (GPT-5)

- Enhanced `lecture-acceptance-advance` so a successful `--execute-sample` run
  promotes the generated clip into the acceptance plan as a new
  `smoke_lecture_e2e` strict-smoke run.
- The promotion refreshes `real-lecture-acceptance-plan.json` and
  `real-lecture-acceptance-handoff.md`, so the next `lecture-acceptance-next`
  call returns `ready_for_strict_smoke`.
- Actual run created a 1-second sample from the local fixture and verified that
  the next action changed from `sample_clip_needed` to `ready_for_strict_smoke`.

### 2026-06-02 10:26:00 | Codex (GPT-5)

- Added `lecture-acceptance-advance-queue` and MCP
  `lecture_acceptance_advance_queue`.
- The queue repeatedly advances preview-safe acceptance steps until strict
  smoke validation is ready, a step is blocked, the action would repeat without
  changing the plan, or `--max-steps` is reached.
- It does not auto-run `smoke_lecture_e2e`; strict real-lecture validation
  remains an explicit gate.
- Targeted queue regression passed: 4 tests passed. Full project regression
  passed with `python -m pytest -q`: 138 tests passed.
- MCP config validation passed with
  `scripts/write-mcp-config.ps1 -Client codex -Validate`: 61 tools.
- Actual preview run against the local 2-second fixture produced a sample-clip
  preview and stopped with `stop_reason: stalled`, confirming the default queue
  path does not write clips or launch strict smoke.

### 2026-06-02 10:36:10 | Codex (GPT-5)

- Added `prepare-review-session` and MCP `prepare_review_session`.
- The command writes `review-session.json`, `review-session.md`, and
  `mcp-prepare-review-session.args.json` beside a WebUI lecture bundle.
- The session handoff contains the local `review.html` file URL,
  `review-notes.json` target path, current readiness blockers, next CLI/MCP
  action, and post-review refresh MCP args.
- Actual command run against `tmp/bilinote-ui-fixture/webui-bundle` returned a
  valid file URL and surfaced `run_visual_structure_plan` as the next machine
  repair action while keeping human review blockers visible.
- Full project regression passed with `python -m pytest -q`: 138 tests passed.
- MCP config validation passed with
  `scripts/write-mcp-config.ps1 -Client codex -Validate`: 62 tools.

### 2026-06-02 12:31:05 | Codex (GPT-5)

- Wired `prepare-review-session` into the packaged and installed BiliNote
  integration.
- Added the BiliNote backend service/router endpoint
  `/api/lecture_bundle/review_session`, frontend API binding
  `prepareLectureReviewSession`, and a `复核会话` button in the existing
  `Agent 下一步` panel.
- WebUI bundles now write `mcp-prepare-review-session.args.json`, expose
  `mcp_review_session_args` in `manifest.json`, and list the
  `prepare_review_session` MCP call in `README.md`.
- Actual BiliNote frontend production build passed with `npm run build`.
- Full project regression passed with `python -m pytest -q`: 138 tests passed.
- BiliNote patch status passed against the installed local BiliNote tree:
  12/12 files installed, 0 drift.
- MCP config validation passed with
  `scripts/write-mcp-config.ps1 -Client codex -Validate`: 62 tools.

### 2026-06-02 13:24:13 | Codex (GPT-5)

- Added `detect-extractor-output` and MCP `detect_extractor_output`.
- The probe recognizes vidclaude, peepshow, and vidwise output folders from
  their minimum import signatures, reports missing files, and emits a safe
  import command when a project/topic is provided.
- Actual run against `tmp/real-tool-smoke-workspace/peepshow-out` identified a
  ready peepshow output and wrote
  `tmp/real-tool-smoke-workspace/extractor-output-probe.json`.
- Full project regression passed with `python -m pytest -q`: 140 tests passed.
- MCP config validation passed with
  `scripts/write-mcp-config.ps1 -Client codex -Validate`: 63 tools.

### 2026-06-02 13:30:35 | Codex (GPT-5)

- Added `run-detected-lecture-pipeline` and MCP
  `run_detected_lecture_pipeline`.
- The command probes extractor output directories, selects the first importable
  vidclaude/peepshow/vidwise output per kind, then reuses the existing
  `run_lecture_pipeline` path for import registry, package build, WebUI bundle
  export, and optional Obsidian export gating.
- Actual run against `tmp/real-tool-smoke-workspace/peepshow-out` imported the
  detected peepshow output, built a package, and exported
  `tmp/detected-pipeline-real/webui-bundle`.
- Full project regression passed with `python -m pytest -q`: 141 tests passed.
- MCP config validation passed with
  `scripts/write-mcp-config.ps1 -Client codex -Validate`: 64 tools.

### 2026-06-02 13:42:00 | Codex (GPT-5)

- Wired `run-detected-lecture-pipeline` into the packaged and installed
  BiliNote integration.
- Added the BiliNote backend endpoints
  `/api/lecture_bundle/extractor_probe` and
  `/api/lecture_bundle/detected_pipeline`, frontend API bindings
  `detectLectureExtractorOutputs` and `runDetectedLecturePipeline`, and the
  import-panel UI section `探测外部抽取结果并生成课程包`.
- The new UI accepts a project directory, one or more vidclaude/peepshow/vidwise
  output directories, a title, optional topic, and optional WebUI output
  directory. The `探测` button reports detected tool kind, importability,
  confidence, missing files, next status, and the recommended import command
  before `生成` imports the returned bundle into the review task list.
- Actual service run against `tmp/real-tool-smoke-workspace/peepshow-out`
  generated and loaded
  `tmp/bilinote-detected-service-real/webui-bundle` with one timeline item.
- Actual probe service run against the same peepshow output returned
  `kind=peepshow`, `importable=true`, and confidence 120.
- Added a BiliNote service fixture regression that creates a minimal peepshow
  output folder and verifies `detect_lecture_extractor_outputs` returns a
  `peepshow` candidate with an `import-peepshow` command.
- BiliNote frontend production build passed with `npm run build`.
- Full project regression passed with `python -m pytest -q`: 141 tests passed.
- BiliNote patch status passed against the installed local BiliNote tree:
  12/12 files installed, 0 drift.
- MCP config validation passed with
  `scripts/write-mcp-config.ps1 -Client codex -Validate`: 64 tools.

### 2026-06-02 14:18:00 | Codex (GPT-5)

- Extended `detect-extractor-output` and MCP `detect_extractor_output` with
  `--title`, `--webui-output-dir`, and `--handoff-dir`.
- The detector now writes a handoff JSON, handoff Markdown, and
  `mcp-run-detected-lecture-pipeline.args.json` when enough context is present
  to run the full detected pipeline.
- The returned `recommended_pipeline` includes the MCP tool name, MCP args, and
  the full `run-detected-lecture-pipeline` CLI command, so humans can copy it
  while agents can call the same workflow without reparsing UI text.
- BiliNote packaged and installed probe endpoints now pass title and optional
  WebUI output directory through to the detector, and the import panel exposes
  `lecture-extractor-probe-pipeline-command` for the full pipeline command.
- Targeted extractor probe regression passed:
  `python -m pytest tests/test_question_research_poc.py -q -k extractor_output`
  returned 2 passed.
- Targeted BiliNote regression passed:
  `python -m pytest tests/test_question_research_poc.py -q -k bilinote`
  returned 18 passed.
- BiliNote frontend production build passed with `npm run build`.
- Full project regression passed with `python -m pytest -q`: 141 tests passed.
- BiliNote patch status passed against the installed local BiliNote tree:
  12/12 files installed, 0 drift.
- MCP config validation passed with
  `scripts/write-mcp-config.ps1 -Client codex -Validate`: 64 tools.

### 2026-06-02 14:46:00 | Codex (GPT-5)

- Added `source-artifacts.json` beside each imported video source under
  `videos/<video_id>/`.
- `import-vidclaude` now records original `meta.json`, `transcript.json`,
  `timeline.json`, `evidence.md`, and frame directory availability, while
  keeping the copied `*-vidclaude-evidence.md` path for review.
- `import-peepshow` now records original `manifest.json`, `report.html`, frame
  directory, and OCR JSON availability, while keeping the copied
  `*-peepshow-report.html` path for review.
- `import-vidwise` now records original video, transcript JSON, SRT, guide, and
  frame directory availability.
- Lecture packages now carry these source artifacts in each `sources[]` row and
  render the available original/copy paths in package Markdown, Obsidian course
  index, and standalone review HTML.
- BiliNote native `课程复核` now shows an `原始抽取物` panel from
  `manifest.sources`, with copy controls and the contract anchor
  `lecture-source-artifacts-panel`.
- Targeted importer/package/UI-fixture regression passed:
  `python -m pytest tests/test_question_research_poc.py -q -k import_vid` and
  targeted peepshow/package/fixture tests passed.
- BiliNote frontend production build passed with `npm run build`.
- Full project regression passed with `python -m pytest -q`: 141 tests passed.
- BiliNote patch status passed against the installed local BiliNote tree:
  12/12 files installed, 0 drift.
- MCP config validation passed with
  `scripts/write-mcp-config.ps1 -Client codex -Validate`: 64 tools.

### 2026-06-02 15:02:00 | Codex (GPT-5)

- Promoted source-artifact traceability into the real smoke/acceptance gates.
- Added `summarize_manifest_source_artifacts` so smoke checks can verify that a
  WebUI bundle manifest carries at least one available source artifact and that
  the expected visual extractor tool is represented.
- `smoke-real-extractor` now reports `missing_source_artifacts` when the bundle
  imports and renders but no longer points back to the original peepshow,
  vidclaude, or vidwise outputs.
- `smoke-lecture-e2e` applies the same source-artifact check whenever a visual
  extractor route is required, making strict real lecture acceptance cover
  traceability in addition to transcript, visual assets, timeline, and review
  readiness.
- Targeted smoke regression passed:
  `python -m pytest tests/test_question_research_poc.py -q -k smoke`
  returned 12 passed.
- Full project regression passed with `python -m pytest -q`: 142 tests passed.
- BiliNote patch status passed against the installed local BiliNote tree:
  12/12 files installed, 0 drift.
- MCP config validation passed with
  `scripts/write-mcp-config.ps1 -Client codex -Validate`: 64 tools.

### 2026-06-02 15:18:00 | Codex (GPT-5)

- Added source-artifact traceability to normal bundle readiness, not only real
  smoke gates.
- `audit-bundle-readiness` / MCP `audit_bundle_readiness` now includes
  `source_artifacts` plus counts for `source_count`, `sources_with_artifacts`,
  and `source_artifact_count`.
- If a bundle has sources but some source rows do not carry available
  `source_artifacts`, readiness now emits a non-blocking
  `missing_source_artifacts` warning. This keeps export possible while making
  traceability gaps visible before final Obsidian refresh.
- BiliNote native `机器收口检查` now renders readiness warnings, including the
  new source-artifact warning, under the UI contract anchor
  `lecture-readiness-warnings`.
- Targeted readiness regression passed:
  `python -m pytest tests/test_question_research_poc.py -q -k readiness`
  returned 4 passed.
- BiliNote frontend production build passed with `npm run build`.
- Full project regression passed with `python -m pytest -q`: 143 tests passed.
- BiliNote patch status passed against the installed local BiliNote tree:
  12/12 files installed, 0 drift.
- MCP config validation passed with
  `scripts/write-mcp-config.ps1 -Client codex -Validate`: 64 tools.

### 2026-06-02 16:40:00 | Codex (GPT-5)

- Added `bundle-source-artifacts` and MCP `bundle_source_artifacts`.
- The command reads the WebUI bundle `source-artifacts.json` traceability index,
  returns available/missing original extractor artifacts, includes a Markdown
  preview, and reports the next safe action for missing or unwritten indexes.
- It is read-only by default. `--refresh --write` rebuilds
  `source-artifacts.json` / `source-artifacts.md` from `manifest.sources` and
  updates manifest pointers when needed.
- WebUI bundles now write `mcp-bundle-source-artifacts.args.json`, expose
  `mcp_source_artifacts_args` in `manifest.json`, and list the MCP call in the
  bundle README.
- Targeted regression passed:
  `python -m pytest tests/test_question_research_poc.py -q -k "export_webui_bundle_writes_manifest_timeline_and_assets or mcp_tool_definitions_include_lecture_workflow"`
  returned 2 passed.
- Full project regression passed with `python -m pytest -q`: 145 tests passed.
- MCP config validation passed with
  `scripts/write-mcp-config.ps1 -Client codex -Validate`: 65 tools.

### 2026-06-02 17:20:00 | Codex (GPT-5)

- Added `audit-knowledge-coverage` and MCP `audit_knowledge_coverage`.
- WebUI bundles now write `knowledge-coverage.json`,
  `knowledge-coverage.md`, and `mcp-audit-knowledge-coverage.args.json`.
- The report audits no-loss coverage across speech, OCR/screen text, visual
  frames, structured visual material, time-axis gaps, and original extractor
  source artifacts, then points back to existing repair/source tools instead of
  running new models.
- Wired the same report into `bundle-next-action` and `prepare-review-session`,
  so agent handoffs see coverage blockers before final export.
- BiliNote `课程复核` now loads and displays the report under
  `知识覆盖审计` with the UI anchor `lecture-knowledge-coverage-panel`.
- Targeted fixture/bundle regression passed: 3 tests passed.
- Full project regression passed with `python -m pytest -q`: 145 tests passed.
- BiliNote frontend production build passed with `npm run build`.
- MCP config validation passed with
  `scripts/write-mcp-config.ps1 -Validate`: 66 tools.

### 2026-06-02 18:40:00 | Codex (GPT-5)

- Adjusted `bundle-next-action` priority to refresh `knowledge_coverage` and
  check hard coverage blockers before final export, while preserving higher
  priority repair/readiness blockers such as missing bundle assets.
- Fixed structured-visual coverage so only formula/table/code or already
  structured visual items are counted as expected structured-visual targets.
- `prepare-review-session` now embeds a `knowledge_coverage` summary, channel
  list, blockers, report paths, MCP args, and next coverage action.
- BiliNote `Agent 下一步 -> 复核会话` now renders this as
  `知识覆盖审计` with the UI anchor
  `lecture-review-session-knowledge-coverage`.
- Targeted readiness/fixture regression passed: 6 tests passed.
- Full project regression passed with `python -m pytest -q`: 145 tests passed.
- BiliNote frontend production build passed with `npm run build`.
- MCP config validation passed with
  `scripts/write-mcp-config.ps1 -Validate`: 66 tools.

### 2026-06-02 20:36:00 | Codex (GPT-5)

- Added `bundle-status-report` and MCP `bundle_status_report`.
- WebUI bundles now write `mcp-bundle-status-report.args.json` and expose
  `bundle-status.md` / `bundle-status.json` manifest pointers.
- The report aggregates existing bundle state without adding a new extraction
  path: next action, review readiness, knowledge coverage, source artifacts,
  human entrypoints, MCP args entrypoints, latest advance log, and Obsidian
  artifacts when present.
- Bundle README generation now lists `bundle-status.md` and the
  `bundle_status_report` MCP call.
- Targeted regression passed:
  `python -m pytest tests\test_question_research_poc.py -q -k "mcp_tool_definitions or export_webui_bundle"`
  returned 4 passed.
- Full project regression passed with `python -m pytest -q`: 155 tests passed.
- MCP config validation passed with
  `scripts\write-mcp-config.ps1 -Validate`: 73 tools.

### 2026-06-02 22:20:00 | Codex (GPT-5)

- Exposed `bundle-status.md` / `bundle-status.json` through the packaged
  BiliNote lecture patch.
- BiliNote backend `lecture_bundle.load_lecture_bundle` now reads
  `bundle_status`, `bundle_status_markdown`, `bundle_status_path`, and
  `bundle_status_json_path` from the WebUI bundle when present.
- BiliNote frontend `LectureReviewPanel` now renders a compact
  `Bundle 状态` panel with the stable UI anchor
  `lecture-bundle-status-panel`, showing next action, readiness, knowledge
  coverage, source-artifact, and Obsidian status summaries.
- `create_bilinote_ui_fixture` now writes `bundle-status.*`, and the fixture
  contract checks the new status-panel anchor.
- Installed the updated packaged patch into
  `%WORKSPACE_ROOT%\tool-source-review\BiliNote`; patch status is 12/12
  installed, 0 drift.
- Targeted regression passed:
  `python -m pytest tests\test_question_research_poc.py -q -k "create_bilinote_ui_fixture or export_webui_bundle"`
  returned 5 passed.
- Full project regression passed with `python -m pytest -q`: 155 tests passed.
- BiliNote frontend production build passed with `npm run build`.
- MCP config validation passed with
  `scripts\write-mcp-config.ps1 -Validate`: 73 tools.

### 2026-06-02 22:28:00 | Codex (GPT-5)

- Added a BiliNote backend route for refreshing the compact bundle status
  report: `POST /api/lecture_bundle/status_report`.
- BiliNote service `refresh_lecture_bundle_status_report` now calls the local
  `lecture-extract` CLI command `bundle-status-report`, then reloads the bundle
  so the UI receives updated `bundle_status` data.
- BiliNote frontend service now exposes `refreshLectureBundleStatusReport`.
- The `Bundle 状态` panel now has a `同步状态` button that refreshes
  `bundle-status.md` / `bundle-status.json`, reloads the bundle in task state,
  and updates the last next-action summary.
- Installed the updated packaged patch into
  `%WORKSPACE_ROOT%\tool-source-review\BiliNote`; patch status is 12/12
  installed, 0 drift.
- Targeted regression passed:
  `python -m pytest tests\test_question_research_poc.py -q -k "create_bilinote_ui_fixture or validate_bilinote"`
  returned 7 passed.
- Full project regression passed with `python -m pytest -q`: 155 tests passed.
- BiliNote frontend production build passed with `npm run build`.
- MCP config validation passed with
  `scripts\write-mcp-config.ps1 -Validate`: 73 tools.

### 2026-06-02 22:34:00 | Codex (GPT-5)

- Adjusted the BiliNote `Agent 下一步` export button to use the existing
  `bundle_advance` ready path instead of the post-review save/refresh path.
- `刷新导出` in `BundleNextActionPanel` now calls
  `advanceLectureBundle(..., refreshOutputs: true)`, preserving the CLI/MCP
  semantics of `bundle-advance --refresh-outputs`.
- The refreshed result updates the current task bundle, stores the latest
  next-action result, captures the advance-log record, and exposes Obsidian
  artifacts through the same advance-log/status-report path used by agents.
- The save-oriented `保存并刷新` workflow still uses
  `refreshLectureBundleReview`, so saved human review notes and agent-ready
  export refresh remain separate UI actions.
- Installed the updated packaged patch into
  `%WORKSPACE_ROOT%\tool-source-review\BiliNote`; patch status is 12/12
  installed, 0 drift.
- Targeted regression passed:
  `python -m pytest tests\test_question_research_poc.py -q -k "create_bilinote_ui_fixture or validate_bilinote"`
  returned 7 passed.
- Full project regression passed with `python -m pytest -q`: 155 tests passed.
- BiliNote frontend production build passed with `npm run build`.
- MCP config validation passed with
  `scripts\write-mcp-config.ps1 -Validate`: 73 tools.

### 2026-06-02 22:49:00 | Codex (GPT-5)

- Added BiliNote backend refresh routes for two existing lecture-extract audit
  tools:
  `POST /api/lecture_bundle/knowledge_coverage/audit` calls
  `audit-knowledge-coverage`, and `POST /api/lecture_bundle/source_artifacts`
  calls `bundle-source-artifacts`.
- BiliNote frontend service now exposes `auditLectureKnowledgeCoverage` and
  `refreshLectureSourceArtifacts`.
- The `知识覆盖审计` panel now has a `同步审计` button, and the `原始抽取物`
  panel now has a `同步证据` button. Both reload the current task bundle after
  the local CLI writes refreshed JSON/Markdown outputs.
- This keeps human review, UI state, CLI, and MCP audit artifacts aligned
  without adding new extraction logic.
- Installed the updated packaged patch into
  `%WORKSPACE_ROOT%\tool-source-review\BiliNote`; patch status is 12/12
  installed, 0 drift.
- Targeted regression passed:
  `python -m pytest tests\test_question_research_poc.py -q -k "create_bilinote_ui_fixture or validate_bilinote"`
  returned 7 passed.
- Full project regression passed with `python -m pytest -q`: 155 tests passed.
- MCP config validation passed with
  `scripts\write-mcp-config.ps1 -Validate`: 73 tools.
- BiliNote frontend production build passed with `npm run build`; only the
  existing lottie `eval` and large-chunk warnings remain.

### 2026-06-02 22:55:00 | Codex (GPT-5)

- Strengthened the BiliNote `原始抽取物` panel so missing source artifacts are
  visible instead of only showing available evidence files.
- The panel now renders when a source-artifact index exists even if no artifact
  is currently available, shows a `缺失证据` section from
  `source-artifacts.json` / `missing`, and provides `复制缺失清单`.
- This makes traceability failures actionable during human review and prevents
  "no available rows" from hiding extractor-output gaps.
- Installed the updated packaged patch into
  `%WORKSPACE_ROOT%\tool-source-review\BiliNote`; patch status is 12/12
  installed, 0 drift.
- Targeted regression passed:
  `python -m pytest tests\test_question_research_poc.py -q -k "create_bilinote_ui_fixture or validate_bilinote"`
  returned 7 passed.
- Full project regression passed with `python -m pytest -q`: 155 tests passed.
- MCP config validation passed with
  `scripts\write-mcp-config.ps1 -Validate`: 73 tools.
- BiliNote frontend production build passed with `npm run build`; only the
  existing lottie `eval` and large-chunk warnings remain.

### 2026-06-02 23:01:00 | Codex (GPT-5)

- Added an explicit next-action hint inside the BiliNote `缺失证据` block.
- When source artifacts are missing, the panel now shows `检查缺失原始抽取物`,
  explains that the reviewer should sync evidence, inspect original extractor
  output directories, then rerun vidclaude / peepshow / vidwise or reimport
  outputs if needed.
- The same block exposes `复制证据 MCP` for
  `mcp-bundle-source-artifacts.args.json`, so an agent can call the existing
  `bundle_source_artifacts` path instead of inventing a repair workflow.
- Installed the updated packaged patch into
  `%WORKSPACE_ROOT%\tool-source-review\BiliNote`; patch status is 12/12
  installed, 0 drift.
- Targeted regression passed:
  `python -m pytest tests\test_question_research_poc.py -q -k "create_bilinote_ui_fixture or validate_bilinote"`
  returned 7 passed.
- Full project regression passed with `python -m pytest -q`: 155 tests passed.
- MCP config validation passed with
  `scripts\write-mcp-config.ps1 -Validate`: 73 tools.
- BiliNote frontend production build passed with `npm run build`; only the
  existing lottie `eval` and large-chunk warnings remain.

### 2026-06-02 23:08:00 | Codex (GPT-5)

- Made the BiliNote `缺失证据` block copy a stable absolute MCP args path
  instead of only copying the relative manifest filename.
- Added frontend helpers `resolveBundlePath` and `isAbsolutePathLike`; relative
  bundle manifest entries such as `mcp-bundle-source-artifacts.args.json` now
  resolve under `bundle.bundle_dir` before being copied.
- This makes `复制证据 MCP` usable by an external agent without requiring it to
  guess the active bundle directory.
- Installed the updated packaged patch into
  `%WORKSPACE_ROOT%\tool-source-review\BiliNote`; patch status is 12/12
  installed, 0 drift.
- Targeted regression passed:
  `python -m pytest tests\test_question_research_poc.py -q -k "create_bilinote_ui_fixture or validate_bilinote"`
  returned 7 passed.
- Full project regression passed with `python -m pytest -q`: 155 tests passed.
- MCP config validation passed with
  `scripts\write-mcp-config.ps1 -Validate`: 73 tools.
- BiliNote frontend production build passed with `npm run build`; only the
  existing lottie `eval` and large-chunk warnings remain.

### 2026-06-02 23:14:00 | Codex (GPT-5)

- Added `复制证据命令` to the BiliNote `缺失证据` block.
- The button copies a complete
  `.\scripts\research-poc.ps1 mcp-call bundle_source_artifacts '<abs args path>'`
  command, while `复制证据 MCP` still copies the absolute args file path.
- Added a shared frontend helper `mcpCallCommand` and reused it for repair and
  post-review MCP command generation, reducing duplicated command formatting.
- This makes the source-artifact repair/audit path directly executable by a
  human or agent without extra command reconstruction.
- Installed the updated packaged patch into
  `%WORKSPACE_ROOT%\tool-source-review\BiliNote`; patch status is 12/12
  installed, 0 drift.
- Targeted regression passed:
  `python -m pytest tests\test_question_research_poc.py -q -k "create_bilinote_ui_fixture or validate_bilinote"`
  returned 7 passed.
- Full project regression passed with `python -m pytest -q`: 155 tests passed.
- MCP config validation passed with
  `scripts\write-mcp-config.ps1 -Validate`: 73 tools.
- BiliNote frontend production build passed with `npm run build`; only the
  existing lottie `eval` and large-chunk warnings remain.

### 2026-06-02 23:20:00 | Codex (GPT-5)

- Enhanced the core `bundle-source-artifacts` CLI/MCP return shape.
- `next_action` now includes `mcp_tool`, `mcp_args_path`, and a complete
  `.\scripts\research-poc.ps1 mcp-call bundle_source_artifacts '<args path>'`
  command for all source-artifact states: ready, write-index, missing-artifact,
  and no-source-artifact.
- This lets an agent call `bundle_source_artifacts`, inspect `next_action`, and
  immediately obtain a stable executable follow-up command instead of
  reconstructing the MCP command from text hints.
- Targeted regression passed:
  `python -m pytest tests\test_question_research_poc.py -q -k "export_webui_bundle or create_bilinote_ui_fixture or validate_bilinote"`
  returned 10 passed.
- Full project regression passed with `python -m pytest -q`: 155 tests passed.
- MCP config validation passed with
  `scripts\write-mcp-config.ps1 -Validate`: 73 tools.
- BiliNote patch status remains 12/12 installed, 0 drift.

### 2026-06-02 23:27:00 | Codex (GPT-5)

- Enhanced `audit-knowledge-coverage` / MCP `audit_knowledge_coverage`
  `coverage.next_action` to include executable MCP fields.
- The coverage `next_action` now always includes `mcp_tool`, an absolute
  `mcp_args_path`, and a full
  `.\scripts\research-poc.ps1 mcp-call <tool> '<args path>'` command.
- When coverage is blocked or weak, the command points at the first selected
  repair/audit tool, such as `run_ocr_backfill` or
  `run_visual_structure_plan`; when coverage is ready, it falls back to
  `audit_knowledge_coverage` itself.
- This makes coverage audits directly actionable for agents, matching the
  source-artifact next-action behavior.
- Targeted regression passed:
  `python -m pytest tests\test_question_research_poc.py -q -k "export_webui_bundle or create_bilinote_ui_fixture or validate_bilinote"`
  returned 10 passed.
- Full project regression passed with `python -m pytest -q`: 155 tests passed.
- MCP config validation passed with
  `scripts\write-mcp-config.ps1 -Validate`: 73 tools.
- BiliNote patch status remains 12/12 installed, 0 drift.

### 2026-06-02 23:32:22 | Codex (GPT-5)

- Enhanced `audit-bundle-readiness` / MCP `audit_bundle_readiness`
  `review_readiness.next_action` to include executable MCP fields.
- The readiness next action now includes `mcp_tool`, an absolute
  `mcp_args_path`, a full
  `.\scripts\research-poc.ps1 mcp-call <tool> '<args path>'` command, and a
  `human_required` flag for manual review blockers.
- Readiness blockers now route to existing tools instead of plain text hints:
  pending human review routes to `prepare_review_session`, missing bundle
  assets route to `repair_bundle_assets`, frame/time gaps route to
  `run_frame_recapture_plan`, visual-structure gaps route to
  `run_visual_structure_plan`, pending repair paths route to
  `bundle_next_action`, and ready export routes to
  `refresh_lecture_review_outputs`.
- Targeted regression passed:
  `python -m pytest tests\test_question_research_poc.py -q -k "export_webui_bundle or audit_bundle_readiness or create_bilinote_ui_fixture or validate_bilinote"`
  returned 12 passed.
- Full project regression passed with `python -m pytest -q`: 155 tests passed.
- MCP config validation passed with
  `scripts\write-mcp-config.ps1 -Validate`: 73 tools.
- BiliNote patch status remains 12/12 installed, 0 drift.

### 2026-06-02 23:38:21 | Codex (GPT-5)

- Connected real smoke validation results back to the existing compact bundle
  status report instead of creating another status format.
- `smoke-real-extractor` and `smoke-lecture-e2e` now include
  `checks.bundle_status` when a WebUI bundle is produced. The embedded report
  carries the current bundle status, next action, MCP tool, MCP args path, and
  executable command generated by `bundle_status_report`.
- The bundle-status lookup is defensive: partial smoke fixtures record
  `status: unavailable` with an error message, while complete real bundles give
  the agent a direct post-smoke handoff into review, repair, coverage, or export
  actions.
- Targeted real-smoke regression passed:
  `python -m pytest tests\test_question_research_poc.py -q -k "real_extractor_smoke or real_lecture_smoke or smoke_lecture_e2e"`
  returned 6 passed.
- Full project regression passed with `python -m pytest -q`: 155 tests passed.
- MCP config validation passed with
  `scripts\write-mcp-config.ps1 -Validate`: 73 tools.
- BiliNote patch status remains 12/12 installed, 0 drift.

### 2026-06-02 23:43:27 | Codex (GPT-5)

- Enhanced `bundle-status-report` / MCP `bundle_status_report` with an
  executable MCP command sheet.
- The report now includes `mcp_commands`, mapping bundle manifest MCP args such
  as `mcp_advance_queue_args`, `mcp_review_session_args`, and
  `mcp_knowledge_coverage_args` to their MCP tool names, absolute args paths,
  existence checks, and ready-to-copy `mcp-call` commands.
- `bundle-status.md` now renders a `MCP 命令` section, so the compact bundle
  dashboard is usable as both a human status page and an agent command sheet.
- This reuses the existing bundle manifest args written by `export_webui_bundle`
  and does not add a new workflow path.
- Targeted regression passed:
  `python -m pytest tests\test_question_research_poc.py -q -k "export_webui_bundle or bundle_status_report or real_extractor_smoke or real_lecture_smoke"`
  returned 8 passed.
- Full project regression passed with `python -m pytest -q`: 155 tests passed.
- MCP config validation passed with
  `scripts\write-mcp-config.ps1 -Validate`: 73 tools.
- BiliNote patch status remains 12/12 installed, 0 drift.

### 2026-06-02 23:49:43 | Codex (GPT-5)

- Exposed the `bundle_status.mcp_commands` command sheet inside the packaged
  BiliNote `Bundle 状态` panel.
- The panel now renders a compact `MCP 命令` section under
  `lecture-bundle-status-mcp-commands`, showing each command's MCP tool,
  ready/missing-args state, and a copyable full `mcp-call` command.
- Added `复制命令表` so a human reviewer can copy the current command sheet from
  the Web UI without opening `bundle-status.md` or reconstructing commands.
- Reused the existing `bundle_status_report` output and `mcpCallCommand`
  formatting; no new backend workflow was added.
- Installed the updated packaged patch into
  `%WORKSPACE_ROOT%\tool-source-review\BiliNote`; patch status is 12/12
  installed, 0 drift.
- Targeted BiliNote/status regression passed:
  `python -m pytest tests\test_question_research_poc.py -q -k "create_bilinote_ui_fixture or validate_bilinote or bundle_status_report or export_webui_bundle"`
  returned 10 passed.
- Full project regression passed with `python -m pytest -q`: 155 tests passed.
- BiliNote frontend production build passed with `npm run build`; only the
  existing lottie `eval` and large-chunk warnings remain.
- MCP config validation passed with
  `scripts\write-mcp-config.ps1 -Validate`: 73 tools.

### 2026-06-02 23:58:09 | Codex (GPT-5)

- Added Obsidian-side agent handoff artifacts to keep the final knowledge base
  connected to the CLI/MCP workflow after export.
- `export-lecture-obsidian` now writes `agent-handoff.md` as a normal Obsidian
  page plus `agent-handoff.json` as a machine-readable entrypoint.
- The handoff records export status, core full-information pages, traceability
  pages, recommended read order, agent entrypoints, and ready-to-copy MCP calls
  for `export_lecture_obsidian` and `obsidian_export_status`.
- `index.md`, `obsidian-export.json`, and `agent_entrypoints` now reference the
  new handoff page/json, so agents can continue from inside the exported vault
  without rediscovering project paths.
- Targeted Obsidian/bundle regression passed:
  `python -m pytest tests\test_question_research_poc.py -q -k "export_lecture_obsidian or obsidian_export_status or refresh_lecture_review_outputs_exports_obsidian"`
  returned 3 passed, and
  `python -m pytest tests\test_question_research_poc.py -q -k "bundle_advance or export_webui_bundle or call_mcp_tool_build_and_export"`
  returned 5 passed.
- Full project regression passed with `python -m pytest -q`: 155 tests passed.
- MCP config validation passed with
  `scripts\write-mcp-config.ps1 -Validate`: 73 tools.
- BiliNote patch status remains 12/12 installed, 0 drift.

### 2026-06-03 09:36:53 | Codex (GPT-5)

- Shifted validation back to real open-source tool I/O instead of adding more
  handoff/status surface.
- Peepshow real output was imported from
  `%WORKSPACE_ROOT%\video-tool-lab\peepshow-ocr-out` with
  `import-peepshow`, then built into a lecture package and WebUI bundle under
  `tmp\real-open-source-tool-check`. Result: 3 real OCR/frame segments entered
  the unified timeline; frame assets and source artifacts were preserved. The
  run also showed the expected limitation: this peepshow output had no audio
  transcript, so transcript coverage must come from ASR or another extractor.
- CaptiOCR was tested against the same real peepshow frame. Its source code
  imported cleanly from
  `%WORKSPACE_ROOT%\tool-source-review\captiocr`, but the upstream constants
  hard-code `C:\Program Files\Tesseract-OCR\tesseract.exe`. Added a minimal
  Tesseract runtime resolver so `run-ocr-backfill --execute` can reuse a
  Tesseract executable found on PATH, plus `LECTURE_TESSERACT_CMD` /
  `LECTURE_TESSDATA_PREFIX` when needed. With the existing
  `%WORKSPACE_ROOT%\video-tool-lab\.venv`, CaptiOCR successfully OCRed
  `frame_0001.jpg` and backfilled `visual_text` in
  `tmp\real-captiocr-backfill`.
- Vidclaude real cache was imported from
  `%WORKSPACE_ROOT%\video-tool-lab\.vidcache\ac262a62c8b5` with
  `import-vidclaude`, then built into a lecture package under
  `tmp\real-vidclaude-tool-check`. Result: transcript, speech/scene signals,
  frames, evidence copy, and source artifacts entered the unified timeline.
  Limitation recorded: this cache's `ocr.json` was empty, so visual text remains
  a downstream OCR/structured-visual task.
- Docling command is present on PATH. Marker command is not currently on PATH,
  although prior Marker outputs exist under
  `%WORKSPACE_ROOT%\marker-verify-run-escalated`. These remain next real
  structure-parser validation targets rather than new glue-code targets.
- Fixed a real integration bug exposed by the CaptiOCR run: empty
  `source_package` values must not be treated as `Path('.')`. The same guard was
  applied to OCR backfill, frame recapture, and visual-structure backfill.
- Targeted regression passed:
  `python -m pytest tests\test_question_research_poc.py -q -k "ocr_backfill or tesseract_runtime_resolver"`
  returned 3 passed.
- Full project regression passed with `python -m pytest -q`: 157 tests passed.
- MCP config validation passed with
  `scripts\write-mcp-config.ps1 -Validate`: 73 tools.

### 2026-06-03 09:52:00 | Codex (GPT-5)

- Continued the real-tool-first pass and avoided adding new handoff/status
  layers. The only new glue is for importing outputs from existing tools into
  the current timeline.
- Verified the real Marker historical output under
  `%WORKSPACE_ROOT%\marker-verify-run-escalated\book_for_ai`. The actual
  reusable result is Marker's sibling Markdown file, not the layout-only
  `blocks.json` tree. `run-visual-structure` now accepts `.md` / `.markdown`
  directly and, when given Marker `blocks.json`, imports the first sibling
  Markdown file as structured visual evidence. The real run updated
  `tmp\real-marker-structure\timeline.json` with `structured_visual` plus
  `visual_text` copied from Marker Markdown.
- Rechecked Docling as a command-line candidate. `docling` is present, but the
  current Python environment fails before help with a dependency conflict:
  `tokenizers>=0.22.0,<=0.23.0 required, found tokenizers==0.21.1`. Treat
  Docling as installed-but-broken until its environment is repaired explicitly;
  do not build more wrapper code around the broken command.
- Rechecked structure-parser command availability. `marker`, `marker_single`,
  `mineru`, and `paddleocr` are not currently available on PATH. Marker remains
  reusable through existing real output; MinerU and PaddleOCR still need either
  a located local install or an explicit install/setup pass before validation.
- Confirmed current real-output evidence:
  `tmp\real-open-source-tool-check\webui-bundle\timeline.json` contains 3
  peepshow OCR/frame items; `tmp\real-vidclaude-tool-check\lecture-packages\lecture-package.json`
  contains 4 vidclaude transcript/frame timeline items with source artifacts;
  `tmp\real-captiocr-backfill\timeline.json` contains CaptiOCR text backfilled
  from a real candidate frame; `tmp\real-marker-structure\timeline.json`
  contains Marker Markdown backfilled as structured visual content.
- Targeted regression passed:
  `python -m pytest tests\test_question_research_poc.py -q -k "visual_structure or tesseract_runtime_resolver or ocr_backfill"`
  returned 6 passed.
- Full project regression passed with `python -m pytest -q`: 158 tests passed.
- MCP config validation passed with
  `scripts\write-mcp-config.ps1 -Validate`: 73 tools.

## 8. Current Boundaries

- The launcher assumes BiliNote backend dependencies already exist in the chosen
  conda environment.
- The current BiliNote patch is packaged locally under
  `integrations/bilinote-lecture-patch` with a manifest-driven checker/installer.
  It is still not an upstream BiliNote PR.
- Corrected transcript/OCR text is written back into the active timeline while
  preserving `original_transcript` and `original_visual_text`.
- Coverage audits count both text corrections and missing visual/OCR text that
  was later filled by a human reviewer.
- Quality audits are heuristic review queues. They surface likely omissions but
  do not prove the video was exhaustively understood.
