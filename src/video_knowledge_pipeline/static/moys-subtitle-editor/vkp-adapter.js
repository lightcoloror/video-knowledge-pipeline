/*
 * VKP adapter layered after the unmodified moys-asr-workflow editor.
 * It reuses the upstream playback/waveform/editing algorithms and only adds
 * dual-track lineage, local draft persistence, and explicit VKP apply.
 */
(function installVkpSubtitleAdapter() {
  'use strict';

  const cfg = SERVER_CONFIG && SERVER_CONFIG.vkp;
  if (!cfg) return;

  const originalSegments = Array.isArray(cfg.projection?.segments)
    ? cfg.projection.segments : [];
  const originalBySource = new Map();
  originalSegments.forEach((segment) => {
    (segment.source_segment_ids || []).forEach((id) => originalBySource.set(String(id), segment));
  });

  const draftKey = `vkp:subtitle-editor:${cfg.bundleId}:${cfg.projection.projection_sha256}`;
  let lastDraftJson = '';
  let formallyApplied = false;

  function normalizedSegment(segment, index) {
    const sourceIds = Array.isArray(segment.source_segment_ids) && segment.source_segment_ids.length
      ? segment.source_segment_ids.map(String)
      : [String(segment.segment_id || `segment-${index + 1}`)];
    return {
      segment_id: String(segment.segment_id || `review-${index + 1}`),
      source_segment_ids: sourceIds,
      start_ms: Math.round(Number(segment.start || 0)),
      end_ms: Math.round(Number(segment.end || 0)),
      speaker_global_id: String(segment.speaker_global_id || segment.speaker || ''),
      speaker_role: String(segment.speaker_role || ''),
      source_text: String(segment.text || '').trim(),
      mandarin_text: String(segment.mandarin_text || '').trim(),
      words: Array.isArray(segment.items)
        ? segment.items.map((item) => ({
            text: String(item.text || ''),
            start_ms: Math.round(Number(item.start || 0)),
            end_ms: Math.round(Number(item.end || item.start || 0)),
            ...(item.speaker ? { speaker_global_id: String(item.speaker) } : {}),
          }))
        : [],
      evidence_ids: Array.isArray(segment.evidence_ids) ? segment.evidence_ids.map(String) : [],
      disabled: Boolean(segment.disabled),
      needs_translation_review: Boolean(segment.needs_translation_review),
    };
  }

  function reviewNotes(humanConfirmed) {
    return {
      schema: 'video_knowledge_pipeline.subtitle_review_notes.v1',
      projection_sha256: cfg.projection.projection_sha256,
      source_sha256: cfg.projection.source_sha256,
      segments: DATA.segments.map(normalizedSegment),
      gap_remove: DATA.gap_remove ? JSON.parse(JSON.stringify(DATA.gap_remove)) : null,
      human_confirmed: Boolean(humanConfirmed),
    };
  }

  function setState(text, state) {
    const el = document.getElementById('vkp-review-state');
    if (!el) return;
    el.textContent = text;
    el.dataset.state = state;
  }

  function markDraft() {
    formallyApplied = false;
    setState('草稿已自动保存 · 尚未写回 VKP', 'draft');
  }

  function persistDraft() {
    const json = JSON.stringify(reviewNotes(false));
    if (json === lastDraftJson) return;
    localStorage.setItem(draftKey, json);
    lastDraftJson = json;
    markDraft();
  }

  function restoreDraft() {
    const raw = localStorage.getItem(draftKey);
    if (!raw) return;
    try {
      const draft = JSON.parse(raw);
      if (draft.projection_sha256 !== cfg.projection.projection_sha256) {
        setState('旧草稿与当前 Bundle 冲突，已禁止覆盖', 'conflict');
        return;
      }
      if (!Array.isArray(draft.segments) || !draft.segments.length) return;
      DATA.segments = draft.segments.map((segment) => ({
        start: segment.start_ms,
        end: segment.end_ms,
        text: segment.source_text,
        mandarin_text: segment.mandarin_text || '',
        segment_id: segment.segment_id,
        source_segment_ids: segment.source_segment_ids,
        speaker: segment.speaker_global_id || null,
        speaker_global_id: segment.speaker_global_id || '',
        speaker_role: segment.speaker_role || '',
        evidence_ids: segment.evidence_ids || [],
        items: (segment.words || []).map((word) => ({
          text: word.text,
          start: word.start_ms,
          end: word.end_ms,
          ...(word.speaker_global_id ? { speaker: word.speaker_global_id } : {}),
        })),
        disabled: Boolean(segment.disabled),
        needs_translation_review: Boolean(segment.needs_translation_review),
        _dirty: true,
      }));
      lastDraftJson = raw;
      renderAll();
      setState('已恢复本地草稿 · 尚未写回 VKP', 'draft');
    } catch (error) {
      setState(`草稿损坏：${error.message || error}`, 'error');
    }
  }

  function currentSegment() {
    return Number.isInteger(currentCuePanelIdx) && currentCuePanelIdx >= 0
      ? DATA.segments[currentCuePanelIdx] : null;
  }

  function syncMandarinEditor() {
    const input = document.getElementById('vkp-mandarin-text');
    const warning = document.getElementById('vkp-translation-review');
    if (!input) return;
    const segment = currentSegment();
    input.disabled = !segment;
    if (document.activeElement !== input) input.value = segment?.mandarin_text || '';
    if (warning) {
      warning.hidden = !segment?.needs_translation_review;
      warning.textContent = segment?.needs_translation_review
        ? '此段在原文拆分后仍需人工确认普通话拆分点。' : '';
    }
  }

  function refreshMandarinPreviews() {
    document.querySelectorAll('.cue[data-idx]').forEach((cue) => {
      const index = Number(cue.dataset.idx);
      const segment = DATA.segments[index];
      const anchor = cue.querySelector('.text') || cue.querySelector('.cue-text');
      if (!anchor || !segment) return;
      let preview = cue.querySelector('.vkp-mandarin-preview');
      if (!preview) {
        preview = document.createElement('div');
        preview.className = 'vkp-mandarin-preview';
        anchor.insertAdjacentElement('afterend', preview);
      }
      preview.textContent = segment.mandarin_text || '';
    });
  }

  function installChrome() {
    // Upstream has hidden panel-local <header> elements. Anchor the VKP bar to
    // the top-level title so it never lands inside a closed workspace panel.
    const header = document.querySelector('body > h1') || document.body.firstElementChild;
    const bar = document.createElement('div');
    bar.className = 'vkp-review-bar';
    bar.innerHTML = `
      <strong>VKP 双轨字幕审核</strong>
      <span class="vkp-boundary-note">原始 ASR / Timeline 不会被覆盖；静音区与剪辑导出仅生成计划</span>
      <span class="vkp-spacer"></span>
      <span class="vkp-review-state" id="vkp-review-state" data-state="clean">尚无草稿</span>
      <button type="button" id="vkp-validate-review">校验草稿</button>
      <button type="button" id="vkp-apply-review">保存到 VKP</button>`;
    header.insertAdjacentElement('afterend', bar);
    if (!cfg.csrfToken) {
      bar.querySelector('#vkp-validate-review').disabled = true;
      bar.querySelector('#vkp-apply-review').disabled = true;
      setState('静态页面仅保存草稿；请通过 VKP Review Server 正式写回', 'draft');
    }
    if (cfg.approvedStickerOnly) {
      const rootButton = document.getElementById('sticker-root-btn');
      const rootInput = document.getElementById('sticker-root-input');
      const pickButton = document.getElementById('sticker-root-pick');
      const confirmButton = document.getElementById('sticker-root-confirm');
      if (rootButton) {
        rootButton.disabled = true;
        rootButton.title = 'VKP 仅允许 Bundle 内 stickers/ 目录中的已审核静态资源';
      }
      if (rootInput) {
        rootInput.disabled = true;
        rootInput.placeholder = '仅允许 Bundle/stickers/';
      }
      if (pickButton) pickButton.disabled = true;
      if (confirmButton) confirmButton.disabled = true;
    }

    const source = document.getElementById('cue-panel-text');
    if (source) {
      const sourceLabel = document.createElement('label');
      sourceLabel.className = 'vkp-track-label';
      sourceLabel.textContent = `粤语原文（${cfg.projection.tracks.source.language}）`;
      source.insertAdjacentElement('beforebegin', sourceLabel);
      const wrap = document.createElement('div');
      wrap.className = 'vkp-mandarin-wrap';
      wrap.innerHTML = `
        <label class="vkp-track-label" for="vkp-mandarin-text">普通话翻译（zh-CN）</label>
        <textarea id="vkp-mandarin-text" rows="3" placeholder="翻译轨缺失时保持为空，不会自动伪造"></textarea>
        <div class="vkp-translation-review" id="vkp-translation-review" hidden></div>`;
      source.parentElement.appendChild(wrap);
      const input = wrap.querySelector('textarea');
      input.addEventListener('input', () => {
        const segment = currentSegment();
        if (!segment) return;
        segment.mandarin_text = input.value;
        segment.needs_translation_review = false;
        segment._dirty = true;
        persistDraft();
        refreshMandarinPreviews();
      });
    }
  }

  async function postReview(path, humanConfirmed) {
    persistDraft();
    const response = await fetch(path, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-VKP-Review-Token': String(cfg.csrfToken || ''),
      },
      body: JSON.stringify({
        bundle_revision: cfg.projection.bundle_revision,
        subtitle_review_notes: reviewNotes(humanConfirmed),
      }),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || !payload.ok) throw new Error(payload.error || `HTTP ${response.status}`);
    return payload;
  }

  async function validateDraft() {
    try {
      const result = await postReview(cfg.validateUrl, true);
      setState(`草稿校验通过 · ${result.summary?.reviewed_segments || DATA.segments.length} 段`, 'draft');
    } catch (error) {
      setState(`校验失败：${error.message || error}`, 'error');
    }
  }

  async function applyReview() {
    if (!confirm('正式写回 VKP？原始 ASR 和 Timeline 不会修改，下游总结将标记为待刷新。')) return;
    try {
      const result = await postReview(cfg.applyUrl, true);
      formallyApplied = true;
      localStorage.removeItem(draftKey);
      lastDraftJson = JSON.stringify(reviewNotes(false));
      setState(`已写回 VKP · ${result.summary?.source_text_changes || 0} 处原文修改`, 'applied');
    } catch (error) {
      setState(`写回失败：${error.message || error}`, 'error');
    }
  }

  const upstreamSetCurrentCuePanelIndex = setCurrentCuePanelIndex;
  setCurrentCuePanelIndex = function vkpSetCurrentCuePanelIndex(index) {
    upstreamSetCurrentCuePanelIndex(index);
    syncMandarinEditor();
  };

  const upstreamRenderAll = renderAll;
  renderAll = function vkpRenderAll() {
    upstreamRenderAll();
    syncMandarinEditor();
    refreshMandarinPreviews();
  };

  const upstreamBuildJson = buildJson;
  buildJson = function vkpBuildJson() {
    const payload = JSON.parse(upstreamBuildJson());
    payload.vkp_projection = {
      schema: cfg.projection.schema,
      projection_sha256: cfg.projection.projection_sha256,
      source_sha256: cfg.projection.source_sha256,
    };
    payload.segments.forEach((row, index) => {
      const source = DATA.segments[index] || {};
      row.segment_id = source.segment_id;
      row.source_segment_ids = source.source_segment_ids || [];
      row.mandarin_text = source.mandarin_text || '';
      row.speaker_global_id = source.speaker_global_id || source.speaker || '';
      row.speaker_role = source.speaker_role || '';
      row.evidence_ids = source.evidence_ids || [];
      if (source.needs_translation_review) row.needs_translation_review = true;
    });
    return JSON.stringify(payload, null, 2);
  };

  const upstreamSplitAtCursor = splitAtCursor;
  splitAtCursor = function vkpSplitAtCursor() {
    if (!editingState) return;
    const index = editingState.idx;
    const before = DATA.segments[index];
    const sourceIds = [...(before.source_segment_ids || [before.segment_id])];
    const translation = String(before.mandarin_text || '');
    const translationInput = document.getElementById('vkp-mandarin-text');
    const translationCursor = translationInput?.selectionStart ?? 0;
    if (translation && (translationCursor <= 0 || translationCursor >= translation.length)) {
      before.needs_translation_review = true;
    }
    upstreamSplitAtCursor();
    if (DATA.segments.length < index + 2) return;
    const left = DATA.segments[index];
    const right = DATA.segments[index + 1];
    left.segment_id = `${before.segment_id || sourceIds[0]}:a`;
    right.segment_id = `${before.segment_id || sourceIds[0]}:b`;
    left.source_segment_ids = sourceIds;
    right.source_segment_ids = sourceIds;
    left.speaker = right.speaker = before.speaker || null;
    left.speaker_global_id = right.speaker_global_id = before.speaker_global_id || before.speaker || '';
    left.speaker_role = right.speaker_role = before.speaker_role || '';
    left.evidence_ids = right.evidence_ids = [...(before.evidence_ids || [])];
    if (translation && translationCursor > 0 && translationCursor < translation.length) {
      left.mandarin_text = translation.slice(0, translationCursor).trim();
      right.mandarin_text = translation.slice(translationCursor).trim();
      left.needs_translation_review = right.needs_translation_review = false;
    } else {
      left.mandarin_text = translation;
      right.mandarin_text = '';
      left.needs_translation_review = right.needs_translation_review = Boolean(translation);
    }
    persistDraft();
    renderAll();
  };

  const upstreamMergeSegments = mergeSegments;
  mergeSegments = function vkpMergeSegments(indexes) {
    const sorted = [...new Set(indexes)].sort((a, b) => a - b);
    const segments = sorted.map((index) => DATA.segments[index]).filter(Boolean);
    const speakers = new Set(segments.map((segment) => segment.speaker_global_id || segment.speaker || '').filter(Boolean));
    if (speakers.size > 1) {
      flashHint('不同全局说话人的字幕禁止自动合并');
      return;
    }
    const sourceIds = [...new Set(segments.flatMap((segment) => segment.source_segment_ids || [segment.segment_id]))];
    const mandarinText = segments.map((segment) => segment.mandarin_text || '').filter(Boolean).join(EDITOR_SETTINGS.mergeJoinText || '');
    const evidenceIds = [...new Set(segments.flatMap((segment) => segment.evidence_ids || []))];
    upstreamMergeSegments(sorted);
    const merged = DATA.segments[sorted[0]];
    if (!merged) return;
    merged.segment_id = `human-merge:${sourceIds.join('+')}`;
    merged.source_segment_ids = sourceIds;
    merged.mandarin_text = mandarinText;
    merged.speaker_global_id = segments[0]?.speaker_global_id || segments[0]?.speaker || '';
    merged.speaker_role = segments[0]?.speaker_role || '';
    merged.evidence_ids = evidenceIds;
    merged.needs_translation_review = segments.some((segment) => segment.needs_translation_review);
    persistDraft();
    renderAll();
  };

  installChrome();
  restoreDraft();
  renderAll();
  document.getElementById('vkp-validate-review')?.addEventListener('click', validateDraft);
  document.getElementById('vkp-apply-review')?.addEventListener('click', applyReview);
  document.addEventListener('input', () => window.setTimeout(persistDraft, 0));
  document.addEventListener('change', () => window.setTimeout(persistDraft, 0));
  window.setInterval(() => {
    if (!formallyApplied) persistDraft();
    syncMandarinEditor();
    refreshMandarinPreviews();
  }, 1500);
})();
