from __future__ import annotations

from dataclasses import dataclass, field

from PIL import Image

from .adapters.base import PipelineDiagnostics, StepStatus, render_objects
from .adapters.detector_grounding_dino import GroundingDinoDetector
from .adapters.director_gemma import GemmaDirector
from .adapters.poster_sdxl import FastPosterGenerator
from .adapters.tts_qwen3 import QwenTTS
from .config import CONFIG, DemoConfig


@dataclass
class TrailerResult:
    boxed_image: Image.Image
    objects: str
    scene_analysis: str
    genre: str
    title: str
    logline: str
    script: str
    poster: Image.Image
    audio_path: str | None
    status: str
    step_statuses: list[StepStatus] = field(default_factory=list)


def run_pipeline(
    image: Image.Image,
    poster_reference: Image.Image | None = None,
    output_language: str = "Korean",
    tts_voice_mode: str = "clone",
    detector_prompt: str | None = None,
    config: DemoConfig = CONFIG,
) -> TrailerResult:
    source = image.convert("RGB")
    reference = poster_reference.convert("RGB") if poster_reference is not None else None

    detector = GroundingDinoDetector(config)
    director = GemmaDirector(config)
    poster_generator = FastPosterGenerator(config)
    tts = QwenTTS(config)

    detection = detector.detect(source, prompt=detector_prompt)
    del detector
    _release_cuda_cache()

    story = director.generate(source, detection.objects, output_language=output_language)
    del director
    _release_cuda_cache()

    poster = poster_generator.generate(
        story.title,
        story.genre,
        story.poster_prompt,
        story.logline,
        reference,
    )
    del poster_generator
    _release_cuda_cache()

    audio = tts.synthesize(story.tts_text, voice_mode=tts_voice_mode, language=output_language)
    del tts
    _release_cuda_cache()

    diagnostics = PipelineDiagnostics(
        statuses=[detection.status, story.status, poster.status, audio.status]
    )

    return TrailerResult(
        boxed_image=detection.boxed_image,
        objects=render_objects(detection.objects),
        scene_analysis=story.scene_analysis,
        genre=story.genre,
        title=story.title,
        logline=story.logline,
        script=story.script,
        poster=poster.image,
        audio_path=audio.audio_path,
        status=diagnostics.render(debug_enabled=config.debug_enabled),
        step_statuses=diagnostics.statuses,
    )


def _release_cuda_cache() -> None:
    try:
        import gc
        import torch
    except Exception:
        return
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
