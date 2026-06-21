from __future__ import annotations

import json
import re
from time import perf_counter

from PIL import Image

from ..config import DemoConfig
from .base import DetectedObject, StepStatus, StoryResult
from .fallbacks import fallback_story


class GemmaDirector:
    def __init__(self, config: DemoConfig) -> None:
        self.config = config
        self._processor = None
        self._model = None

    def generate(
        self,
        image: Image.Image,
        objects: list[DetectedObject],
        output_language: str = "Korean",
    ) -> StoryResult:
        if not self.config.use_real_models:
            return fallback_story("real models disabled")

        start = perf_counter()
        try:
            return self._generate_real(image, objects, start, _normalize_output_language(output_language))
        except Exception as exc:
            result = fallback_story("Gemma director failed")
            result.status.debug = repr(exc)
            result.status.latency_seconds = perf_counter() - start
            return result

    def _generate_real(
        self,
        image: Image.Image,
        objects: list[DetectedObject],
        start: float,
        output_language: str,
    ) -> StoryResult:
        import torch
        from transformers import AutoModelForMultimodalLM, AutoProcessor

        source = image.convert("RGB")
        if self._processor is None or self._model is None:
            self._processor = AutoProcessor.from_pretrained(
                self.config.director_model,
                local_files_only=True,
            )
            self._model = AutoModelForMultimodalLM.from_pretrained(
                self.config.director_model,
                dtype="auto",
                device_map="auto",
                local_files_only=True,
            )
            self._model.eval()

        object_summary = _format_objects(objects)
        prompt = _build_prompt(object_summary, output_language)
        messages = [
            {
                "role": "system",
                "content": "You are an AI scene director for a live movie trailer demo. Return only valid JSON.",
            },
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": source},
                    {"type": "text", "text": prompt},
                ],
            },
        ]
        inputs = self._processor.apply_chat_template(
            messages,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
            add_generation_prompt=True,
            enable_thinking=False,
        ).to(self._model.device)
        input_len = inputs["input_ids"].shape[-1]

        with torch.inference_mode():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=max(self.config.director_max_new_tokens, 768),
                do_sample=True,
                temperature=self.config.director_temperature,
                top_p=self.config.director_top_p,
            )

        raw = self._processor.decode(outputs[0][input_len:], skip_special_tokens=False)
        parsed = _parse_response(self._processor, raw)
        data = _extract_json(parsed)
        return StoryResult(
            scene_analysis=data["scene_analysis"],
            genre=data["genre"],
            title=data["title"],
            logline=data["logline"],
            script=data["script"],
            poster_prompt=data["poster_prompt"],
            tts_text=data.get("tts_text") or data["script"],
            status=StepStatus(
                name="director",
                ok=True,
                used_fallback=False,
                message=f"Gemma 4 director generated {output_language} trailer concept",
                latency_seconds=perf_counter() - start,
            ),
        )


def _format_objects(objects: list[DetectedObject]) -> str:
    if not objects:
        return "No reliable detector objects were found. Use the image itself as the primary evidence."
    lines = []
    for obj in objects[:12]:
        if obj.box is None:
            lines.append(f"- {obj.label} ({obj.confidence:.2f})")
        else:
            lines.append(f"- {obj.label} ({obj.confidence:.2f}) at box {obj.box}")
    return "\n".join(lines)


def _normalize_output_language(value: str) -> str:
    lowered = str(value).strip().lower()
    return "English" if lowered in {"english", "en", "영어", "영어 모드"} else "Korean"


def _build_prompt(object_summary: str, output_language: str) -> str:
    return f"""
Analyze the uploaded image as a cinematic movie-trailer scene.
Detected visual clues:
{object_summary}

Output language mode: {output_language}.

Return one compact JSON object with exactly these keys:
- scene_analysis: 1-2 {output_language} sentences describing the scene and mood.
- genre: one short {output_language} movie genre.
- title: an original {output_language} movie title, 2-5 words if English or a short natural title if Korean.
- logline: one {output_language} sentence.
- script: 4 short {output_language} trailer narration lines separated by newline characters.
- poster_prompt: one English text-to-image prompt under 45 words for a vertical cinematic movie poster. Include the exact title text in the selected output language.
- tts_text: {output_language} narration text to speak, same language as script.

Constraints:
- Return JSON only. No markdown. No commentary.
- Keep it concise for a 2-3 minute live demo.
- Do not mention AI, JSON, detectors, or bounding boxes in the creative output.
- Keep poster_prompt in English even when output_language is Korean.
""".strip()


def _parse_response(processor, raw: str) -> str:
    try:
        parsed = processor.parse_response(raw)
    except Exception:
        return raw
    if isinstance(parsed, dict):
        return str(parsed.get("content") or parsed)
    return str(parsed)


def _extract_json(text: str) -> dict[str, str]:
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    elif not text.startswith("{"):
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError(f"Gemma response did not contain JSON: {text[:500]}")
        text = match.group(0)

    data = json.loads(text)
    required = ["scene_analysis", "genre", "title", "logline", "script", "poster_prompt"]
    missing = [key for key in required if not str(data.get(key, "")).strip()]
    if missing:
        raise ValueError(f"Gemma JSON missing keys: {missing}")
    return {key: str(value).strip() for key, value in data.items()}
