from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


SOURCE_REVIEW_ROOT = Path(
    os.environ.get("VKP_SOURCE_REVIEW_ROOT")
    or Path(__file__).resolve().parents[2] / "tool-source-review"
)

FIXTURES = [
    {
        "id": "talking-head-synthetic",
        "type": "talking_video",
        "audio_source": str(SOURCE_REVIEW_ROOT / "transcribe-critic" / "tests" / "fixtures" / "tao_30s.mp3"),
        "audio_source_project": "transcribe-critic test fixture",
        "cards": [("本地讲话视频 fixture", ["讲话音频：开源测试素材", "目标：ASR 与时间戳", "边界：不要求语义正确"])],
    },
    {
        "id": "slides-screen-synthetic",
        "type": "slides_or_screen_video",
        "audio_source": str(SOURCE_REVIEW_ROOT / "FunASR" / "runtime" / "funasr_api" / "asr_example.wav"),
        "audio_source_project": "FunASR official runtime fixture",
        "cards": [
            ("课程页一：输入", ["本地视频或音频", "来源哈希", "处理配置"]),
            ("课程页二：处理", ["SenseVoice ASR", "抽帧与 OCR", "统一时间线"]),
            ("课程页三：输出", ["审核包", "逐字稿", "知识笔记"]),
        ],
    },
    {
        "id": "mixed-visual-synthetic",
        "type": "mixed_visual_video",
        "audio_source": str(SOURCE_REVIEW_ROOT / "docling" / "tests" / "data" / "audio" / "sample_10s_audio-wav.wav"),
        "audio_source_project": "Docling official test fixture",
        "cards": [
            ("讲师说明", ["先观察整体流程", "再定位疑难片段"]),
            ("操作界面", ["状态：本地处理", "进度：百分之六十", "下一步：复核屏幕文字"]),
            ("结论与风险", ["视觉未执行时不得补故事", "外部调用需要明确批准"]),
        ],
    },
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build non-sensitive offline VKP acceptance fixtures")
    parser.add_argument("output_dir")
    args = parser.parse_args()
    output = Path(args.output_dir).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise SystemExit("ffmpeg and ffprobe are required")

    manifest = {"schema": "video_knowledge_pipeline.offline_fixture_set.v1", "fixtures": []}
    for spec in FIXTURES:
        fixture_dir = output / spec["id"]
        fixture_dir.mkdir(parents=True, exist_ok=True)
        images = []
        for index, (title, bullets) in enumerate(spec["cards"], start=1):
            image_path = fixture_dir / f"card-{index:02d}.png"
            _render_card(image_path, title, bullets, accent=(36 + index * 30, 120, 170))
            images.append(image_path)
        audio_path = Path(spec["audio_source"]).resolve()
        if not audio_path.exists():
            raise FileNotFoundError(audio_path)
        video_path = fixture_dir / f"{spec['id']}.mp4"
        _mux_cards(ffmpeg, ffprobe, images, audio_path, video_path)
        manifest["fixtures"].append(
            {
                "fixture_id": spec["id"],
                "fixture_type": spec["type"],
                "media_path": str(video_path),
                "sha256": _sha256(video_path),
                "duration_seconds": _duration(ffprobe, video_path),
                "source_audio_project": spec["audio_source_project"],
                "source_audio_path": str(audio_path),
                "source_audio_sha256": _sha256(audio_path),
                "quality_reference_required": False,
                "expected_artifacts": [
                    "normalized-transcript.json",
                    "frame-manifest.json",
                    "ocr_or_visual_evidence",
                    "review.html",
                    "exports/knowledge-note.md",
                    "exports/full-transcript.md",
                ],
                "privacy": "open_source_test_audio_plus_synthetic_visuals_local_only",
            }
        )
    manifest_path = output / "fixture-contract.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "manifest": str(manifest_path), "fixture_count": len(manifest["fixtures"])}, ensure_ascii=False))
    return 0


def _font(size: int) -> ImageFont.FreeTypeFont:
    for candidate in (Path("C:/Windows/Fonts/msyh.ttc"), Path("C:/Windows/Fonts/simhei.ttf"), Path("C:/Windows/Fonts/arial.ttf")):
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def _render_card(path: Path, title: str, bullets: list[str], *, accent: tuple[int, int, int]) -> None:
    image = Image.new("RGB", (1280, 720), (245, 247, 250))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1280, 92), fill=accent)
    draw.text((54, 22), title, font=_font(40), fill="white")
    draw.rectangle((54, 142, 1226, 640), outline=(190, 197, 205), width=3)
    for index, bullet in enumerate(bullets, start=1):
        y = 180 + (index - 1) * 130
        draw.ellipse((86, y + 12, 118, y + 44), fill=accent)
        draw.text((145, y), bullet, font=_font(34), fill=(28, 35, 43))
    draw.text((54, 670), "VKP synthetic offline acceptance fixture", font=_font(20), fill=(95, 103, 112))
    image.save(path)


def _mux_cards(ffmpeg: str, ffprobe: str, images: list[Path], audio: Path, output: Path) -> None:
    concat = output.parent / "cards.ffconcat"
    duration = max(0.5, _duration(ffprobe, audio) / max(1, len(images)))
    lines = ["ffconcat version 1.0"]
    for image in images:
        lines.extend([f"file '{image.as_posix()}'", f"duration {duration:.6f}"])
    lines.append(f"file '{images[-1].as_posix()}'")
    concat.write_text("\n".join(lines) + "\n", encoding="utf-8")
    subprocess.run(
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-i", str(audio), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "25", "-c:a", "aac", "-shortest", str(output)],
        check=True,
    )


def _duration(ffprobe: str, path: Path) -> float:
    completed = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True, check=True)
    return round(float(completed.stdout.strip()), 3)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())