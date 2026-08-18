# Handoff

## Header
- Message-ID: 20260818191138-62ca97
- From: codex-vkp-owner
- To: vkp-implementation-agent
- Date: 2026-08-18T19:11:38+08:00
- Subject: Implement recoverable per-window execution for ultra-long Qwen ASR
- References: VKP-ASR-PLAN-CHECKPOINT-RESUME-20260818-01

## Body

Implement priority 2 from the authoritative VKP continuation: replace Qwen's all-at-once audio segmentation with deterministic lazy per-window extraction while keeping the existing Qwen checkpoint as the only state owner.

Read the attached plan reference and acceptance contract before acting. Preserve the dirty worktree and start from commit `31b7e437aaf86fce17e265dbcd16a4ff38f9de00`. Use only synthetic fixtures. Do not run real media, models, Providers, network, uploads, configuration changes, or push.

One window extraction/transcription failure must be checkpointed and must not remove completed results or prevent later windows. Resume must skip extraction for successful windows. Return one selective commit and one independent completion receipt for Codex review; completion is not acceptance until Codex records an acceptance decision.

## Attachments

- inputs/plan-reference.md
- inputs/acceptance-contract.json

## Status

completed
