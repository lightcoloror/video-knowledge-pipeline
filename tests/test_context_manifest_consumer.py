import importlib.util
import json
import os
import shutil
import unittest
import uuid
from pathlib import Path

from scripts.context_manifest_consumer import decide_asr


SELF_MEDIA_ROOT = Path(os.environ.get("SELF_MEDIA_SYSTEM_ROOT", "D:/used-by-codex/self-media-creation-system"))


def load_agent():
    spec = importlib.util.spec_from_file_location(
        "vkp_test_self_media_agent", SELF_MEDIA_ROOT / "scripts" / "self_media_agent.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ContextManifestConsumerTests(unittest.TestCase):
    def test_audio_hash_reuse_and_changed_window_boundary(self):
        root = Path(os.environ.get("TEST_TMP_ROOT", "D:/used-by-codex/outputs/test-temp/vkp-context-consumer")) / ("context-consumer-" + uuid.uuid4().hex)
        root.mkdir(parents=True, exist_ok=True)
        try:
            agent = load_agent()
            request = agent.load_json(
                SELF_MEDIA_ROOT / "fixtures" / "agent-entry" / "context-efficient-rework.request.json"
            )
            capsule = root / "capsule.json"
            capsule.write_text(json.dumps(agent.resolve_request(request), ensure_ascii=False), encoding="utf-8")
            audio = root / "audio.wav"; audio.write_bytes(b"synthetic-audio")
            proxy = root / "proxy-review-plan.json"; proxy.write_text('{"status":"ready"}', encoding="utf-8")
            import hashlib
            digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
            manifest = root / "manifest.json"

            def write_manifest():
                manifest.write_text(json.dumps({
                    "schema_version": "self-media-context-input.v1",
                    "task_id": request["request_id"],
                    "stage": "video",
                    "budget": {"max_inline_bytes": 1000},
                    "artifacts": [
                        {"artifact_id": "source-media", "role": "source_media", "source_role": "source_media", "path": audio.name, "load_mode": "reference", "expected_sha256": digest(audio)},
                        {"artifact_id": "proxy-plan", "role": "proxy_review_plan", "source_role": "proxy-review-plan", "path": proxy.name, "load_mode": "inline", "expected_sha256": digest(proxy)}
                    ]
                }), encoding="utf-8")

            write_manifest()
            handoff = root / "handoff.json"
            agent.prepare_step_handoff(
                capsule, "decide-asr-need", manifest, root / "context-receipt.json", handoff
            )
            first = root / "first.json"
            result = decide_asr(handoff, audio, None, first, [])
            self.assertEqual(result["decision"], "rerun_full_asr")
            reused = decide_asr(handoff, audio, first, root / "second.json", [])
            self.assertEqual(reused["decision"], "reuse_existing_asr")
            audio.write_bytes(b"synthetic-audio-changed")
            write_manifest()
            changed_handoff = root / "changed-handoff.json"
            agent.prepare_step_handoff(
                capsule, "decide-asr-need", manifest, root / "changed-context-receipt.json", changed_handoff
            )
            changed = decide_asr(changed_handoff, audio, root / "second.json", root / "third.json", ["12.0-18.0"])
            self.assertEqual(changed["decision"], "rerun_changed_windows_with_context")
            self.assertEqual(changed["context_padding_seconds"], 2)
            proxy.write_text('{"status":"tampered"}', encoding="utf-8")
            with self.assertRaisesRegex(Exception, "context_receipt_drift"):
                decide_asr(changed_handoff, audio, root / "third.json", root / "drift.json", [])
        finally:
            shutil.rmtree(root, ignore_errors=True)
