from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import List, Tuple

from PIL import Image, ImageDraw

from ..config import CONFIG
from .base import DetectedObject, DetectionResult, PosterResult, StepStatus, StoryResult, TTSResult


def fallback_detection(image: Image.Image, reason: str) -> DetectionResult:
    start = perf_counter()
    boxed = image.convert("RGB").copy()
    draw = ImageDraw.Draw(boxed)
    width, height = boxed.size
    boxes = [
        ("main subject", 0.91, (0.12, 0.18, 0.58, 0.78)),
        ("cinematic clue", 0.83, (0.56, 0.25, 0.91, 0.62)),
        ("background detail", 0.76, (0.08, 0.68, 0.42, 0.92)),
    ]
    objects: List[DetectedObject] = []
    for label, confidence, rel in boxes:
        box = _relative_box(rel, width, height)
        x1, y1, x2, y2 = box
        draw.rectangle((x1, y1, x2, y2), outline=(255, 210, 60), width=4)
        draw.rectangle((x1, max(0, y1 - 28), x1 + 220, y1), fill=(20, 20, 20))
        draw.text((x1 + 6, max(0, y1 - 24)), f"{label} {confidence:.2f}", fill=(255, 255, 255))
        objects.append(DetectedObject(label=label, confidence=confidence, box=box))

    return DetectionResult(
        boxed_image=boxed,
        objects=objects,
        status=StepStatus(
            name="detector",
            ok=True,
            used_fallback=True,
            message=f"Mock detector used: {reason}",
            latency_seconds=perf_counter() - start,
        ),
    )


def fallback_story(reason: str) -> StoryResult:
    start = perf_counter()
    title = "The Last Signal"
    genre = "Mystery Thriller"
    logline = (
        "A single image exposes the final trace of a disappearance that the city "
        "was never meant to remember."
    )
    script = (
        "In a city full of noise, one signal went silent.\n"
        "A face, a shadow, a clue left in plain sight.\n"
        "Every detail points to a story someone tried to erase.\n"
        "This winter, the truth develops from a single frame."
    )
    return StoryResult(
        scene_analysis=(
            "The image is treated as a suspenseful cinematic frame. The visible "
            "subject becomes the emotional anchor, while background details are "
            "used as clues that imply a larger hidden story."
        ),
        genre=genre,
        title=title,
        logline=logline,
        script=script,
        poster_prompt=(
            "A cinematic mystery thriller movie poster, dramatic contrast, "
            "deep shadows, a single glowing signal, tense atmosphere."
        ),
        tts_text=script,
        status=StepStatus(
            name="director",
            ok=True,
            used_fallback=True,
            message=f"Mock story used: {reason}",
            latency_seconds=perf_counter() - start,
        ),
    )


def fallback_poster(title: str, genre: str, reason: str) -> PosterResult:
    start = perf_counter()
    poster = Image.new("RGB", (768, 1024), (15, 18, 22))
    draw = ImageDraw.Draw(poster)
    for y in range(1024):
        tone = int(18 + y * 0.045)
        draw.line((0, y, 768, y), fill=(tone, max(18, tone - 8), max(28, tone + 16)))
    draw.rectangle((64, 90, 704, 835), outline=(240, 210, 120), width=3)
    draw.rectangle((94, 120, 674, 805), outline=(80, 130, 160), width=2)
    draw.ellipse((218, 265, 550, 597), outline=(235, 235, 235), width=5)
    draw.line((130, 710, 638, 350), fill=(255, 216, 95), width=6)
    return PosterResult(
        image=poster,
        status=StepStatus(
            name="poster",
            ok=True,
            used_fallback=True,
            message=f"Mock poster used: {reason}",
            latency_seconds=perf_counter() - start,
        ),
    )


def fallback_tts(reason: str) -> TTSResult:
    start = perf_counter()
    Path(CONFIG.output_dir, "audio").mkdir(parents=True, exist_ok=True)
    return TTSResult(
        audio_path=None,
        status=StepStatus(
            name="tts",
            ok=True,
            used_fallback=True,
            message=f"No audio file generated: {reason}",
            latency_seconds=perf_counter() - start,
        ),
    )


def _relative_box(rel: Tuple[float, float, float, float], width: int, height: int) -> tuple[int, int, int, int]:
    return (
        int(rel[0] * width),
        int(rel[1] * height),
        int(rel[2] * width),
        int(rel[3] * height),
    )
