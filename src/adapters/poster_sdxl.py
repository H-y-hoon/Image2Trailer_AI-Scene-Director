from __future__ import annotations

from time import perf_counter

from PIL import Image

from ..config import DemoConfig
from .base import PosterResult, StepStatus
from .fallbacks import fallback_poster


class FastPosterGenerator:
    def __init__(self, config: DemoConfig) -> None:
        self.config = config
        self._pipe = None

    def generate(
        self,
        title: str,
        genre: str,
        prompt: str,
        logline: str = "",
        reference_image: Image.Image | None = None,
    ) -> PosterResult:
        if not self.config.use_real_models:
            return fallback_poster(title, genre, "real models disabled")

        start = perf_counter()
        try:
            return self._generate_real(title, genre, prompt, logline, reference_image, start)
        except Exception as exc:
            result = fallback_poster(title, genre, "poster generator failed")
            result.status.debug = repr(exc)
            result.status.latency_seconds = perf_counter() - start
            return result

    def _generate_real(
        self,
        title: str,
        genre: str,
        prompt: str,
        logline: str,
        reference_image: Image.Image | None,
        start: float,
    ) -> PosterResult:
        import torch
        from diffusers import AutoPipelineForText2Image, ZImagePipeline

        if self._pipe is None:
            dtype = torch.bfloat16 if _is_z_image_model(self.config.poster_model) and torch.cuda.is_available() else torch.float16 if torch.cuda.is_available() else torch.float32
            if _is_z_image_model(self.config.poster_model):
                self._pipe = ZImagePipeline.from_pretrained(
                    self.config.poster_model,
                    torch_dtype=dtype,
                    low_cpu_mem_usage=False,
                )
            else:
                self._pipe = AutoPipelineForText2Image.from_pretrained(
                    self.config.poster_model,
                    torch_dtype=dtype,
                    variant="fp16" if torch.cuda.is_available() else None,
                )
            if torch.cuda.is_available():
                self._pipe = self._pipe.to("cuda")

        poster_prompt = _compose_poster_prompt(title, genre, prompt, reference_image)
        generator = None
        if torch.cuda.is_available():
            generator = torch.Generator(device="cuda").manual_seed(42)
        raw_image = self._pipe(
            prompt=poster_prompt,
            num_inference_steps=self.config.poster_steps,
            guidance_scale=self.config.poster_guidance_scale,
            width=self.config.poster_width,
            height=self.config.poster_height,
            generator=generator,
        ).images[0]
        ref_msg = " with reference prompt hint" if reference_image is not None else ""
        return PosterResult(
            image=raw_image.convert("RGB"),
            status=StepStatus(
                name="poster",
                ok=True,
                used_fallback=False,
                message=f"Generated poster with {self.config.poster_model}{ref_msg}",
                latency_seconds=perf_counter() - start,
            ),
        )


def _is_z_image_model(model_id: str) -> bool:
    return "z-image" in model_id.lower()



def _compose_poster_prompt(
    title: str,
    genre: str,
    prompt: str,
    reference_image: Image.Image | None = None,
) -> str:
    style_hint = _reference_style_hint(reference_image)
    clean_title = _clean_title_for_prompt(title)
    return (
        f"{prompt}. Theatrical one-sheet movie poster for a {genre} film. "
        f"The poster must include the exact large readable movie title text: \"{clean_title}\". "
        "Place the title naturally as part of the generated poster design, with cinematic key art, "
        "central subject, negative space, strong silhouette, high contrast, vertical composition. "
        "No billing block, no extra words, no watermark. "
        f"{style_hint}"
    ).strip()


def _clean_title_for_prompt(title: str) -> str:
    cleaned = " ".join(title.replace('"', "'").split())
    return cleaned or "UNTITLED"


def _reference_style_hint(reference_image: Image.Image | None) -> str:
    if reference_image is None:
        return ""
    palette = _extract_palette(reference_image)
    names = [_nearest_color_name(rgb) for rgb in palette[:4]]
    names = [name for i, name in enumerate(names) if name and name not in names[:i]]
    if not names:
        return ""
    return "Reference-inspired palette: " + ", ".join(names) + "."


def _extract_palette(image: Image.Image | None) -> list[tuple[int, int, int]]:
    if image is None:
        return []
    sample = image.convert("RGB")
    sample.thumbnail((96, 96))
    quantized = sample.quantize(colors=6, method=Image.Quantize.MEDIANCUT).convert("RGB")
    colors = quantized.getcolors(maxcolors=96 * 96) or []
    ranked = sorted(colors, key=lambda item: item[0], reverse=True)
    result: list[tuple[int, int, int]] = []
    for _, rgb in ranked:
        r, g, b = rgb
        brightness = (r + g + b) / 3
        saturation = max(rgb) - min(rgb)
        if brightness < 28 or brightness > 236 or saturation < 18:
            continue
        result.append(rgb)
    return result[:5]


def _nearest_color_name(rgb: tuple[int, int, int]) -> str:
    named = {
        "black": (18, 18, 18),
        "crimson red": (160, 30, 42),
        "deep blue": (28, 58, 126),
        "teal": (30, 128, 130),
        "gold": (218, 174, 70),
        "amber": (210, 118, 42),
        "emerald green": (44, 132, 84),
        "cold silver": (176, 184, 188),
        "ivory": (226, 218, 194),
        "violet": (105, 70, 150),
    }
    return min(named, key=lambda name: sum((rgb[i] - named[name][i]) ** 2 for i in range(3)))
