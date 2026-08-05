# VKP 网页来源元数据交接

## Update Record

- 2026-07-21 13:00:44 | Codex (GPT-5.6) | Added the local-only page metadata handoff, trust boundary, artifacts, and consumption contract.

## Purpose

VKP does not scrape pages, manage cookies, log in, or download media. `video-download-orchestrator` or another acquisition tool owns those actions. VKP accepts an already-local JSON handoff and normalizes public page context into:

- `source/page-metadata.json`
- `source/page-metadata.md`
- `source-artifacts.json` / `source-artifacts.md` entries
- compact `manifest.page_metadata` plus an exact artifact SHA-256

## Stable entrypoints

```powershell
.\scripts\video-knowledge.ps1 import-page-metadata <webui-bundle> <local-metadata.json>
.\scripts\video-knowledge.ps1 mcp-call import_page_metadata <args.json>
```

Native MCP exposes both `import_page_metadata` and `import_page_metadata_tool` with `bundle_dir`, `metadata_json`, and `write`.

The importer understands direct metadata objects, yt-dlp-style info JSON, VKP/VDO handoff containers, and VDO local `info_json_path`, `description_path`, and `subtitle_paths` sidecars. It never follows `source_url` and never persists cookie/header/API-key fields or remote subtitle/thumbnail URLs.

## Normalized fields

- safe source URL, platform, title, description, author/uploader, publish time
- bounded tags and chapters
- local subtitle and cover artifact paths with existence, byte count, and SHA-256
- input path/schema/hash and normalized-content hash
- fixed trust boundary: untrusted weak context, cannot override transcript or visual evidence

Existing non-empty manifest title/description/author fields are preserved. Missing fields may be backfilled from the normalized handoff.

## Consumers

- Pre-ASR entity lexicon and bounded ASR prompt use title, author, tags, and a short description as hints only.
- Transcript semantic correction sees the artifact as low-weight `page_metadata` evidence.
- Smart Summary input includes a source-context block, artifact hash, chapters, and an explicit no-override rule.
- `source-artifacts.json/md` provides traceability back to the normalized handoff.

## Safety boundary

Page text can contain prompt-like or malicious strings. Consumers must treat it as data, not instructions. It cannot authorize network access, uploads, publication, transcript replacement, or local/cloud fallback. Platform subtitles remain independent evidence and require the existing transcript-source arbitration before promotion.
