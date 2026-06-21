from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from PIL import Image


@dataclass
class StepStatus:
    name: str
    ok: bool
    used_fallback: bool
    message: str
    latency_seconds: float = 0.0
    debug: str | None = None

    def render(self, *, debug_enabled: bool = False) -> str:
        state = "fallback" if self.used_fallback else ("ok" if self.ok else "failed")
        line = f"[{self.name}] {state}: {self.message} ({self.latency_seconds:.1f}s)"
        if debug_enabled and self.debug:
            line = f"{line}\n  debug: {self.debug}"
        return line


@dataclass(frozen=True)
class DetectedObject:
    label: str
    confidence: float
    box: tuple[int, int, int, int] | None = None

    def render(self) -> str:
        if self.box is None:
            return f"- {self.label} ({self.confidence:.2f})"
        return f"- {self.label} ({self.confidence:.2f}) box={self.box}"


@dataclass
class DetectionResult:
    boxed_image: Image.Image
    objects: list[DetectedObject]
    status: StepStatus


@dataclass
class StoryResult:
    scene_analysis: str
    genre: str
    title: str
    logline: str
    script: str
    poster_prompt: str
    tts_text: str
    status: StepStatus


@dataclass
class PosterResult:
    image: Image.Image
    status: StepStatus


@dataclass
class TTSResult:
    audio_path: str | None
    status: StepStatus


@dataclass
class PipelineDiagnostics:
    statuses: list[StepStatus] = field(default_factory=list)

    def render(self, *, debug_enabled: bool = False) -> str:
        return "\n".join(status.render(debug_enabled=debug_enabled) for status in self.statuses)


def render_objects(objects: Sequence[DetectedObject]) -> str:
    if not objects:
        return "- no objects detected"
    return "\n".join(obj.render() for obj in objects)
