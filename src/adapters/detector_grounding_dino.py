from __future__ import annotations

from time import perf_counter

from PIL import Image, ImageDraw

from ..config import DemoConfig
from .base import DetectedObject, DetectionResult, StepStatus
from .fallbacks import fallback_detection


class GroundingDinoDetector:
    def __init__(self, config: DemoConfig) -> None:
        self.config = config
        self._processor = None
        self._model = None
        self._device = None

    def detect(self, image: Image.Image, prompt: str | None = None) -> DetectionResult:
        if not self.config.use_real_models:
            return fallback_detection(image, "real models disabled")

        start = perf_counter()
        try:
            query = _normalize_prompt(prompt or self.config.detector_prompt)
            return self._detect_real(image, start, query)
        except Exception as exc:  # presentation mode must continue.
            result = fallback_detection(image, "Grounding DINO failed")
            result.status.debug = repr(exc)
            result.status.latency_seconds = perf_counter() - start
            return result

    def _detect_real(self, image: Image.Image, start: float, query: str) -> DetectionResult:
        import torch
        from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor

        source = image.convert("RGB")
        if self._processor is None or self._model is None:
            self._processor = AutoProcessor.from_pretrained(self.config.detector_model_id)
            self._model = AutoModelForZeroShotObjectDetection.from_pretrained(
                self.config.detector_model_id
            )
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            self._model.to(self._device)
            self._model.eval()

        inputs = self._processor(images=source, text=query, return_tensors="pt")
        inputs = {key: value.to(self._device) for key, value in inputs.items()}

        with torch.no_grad():
            outputs = self._model(**inputs)

        target_sizes = torch.tensor([source.size[::-1]], device=self._device)
        results = self._processor.post_process_grounded_object_detection(
            outputs,
            inputs.get("input_ids"),
            threshold=self.config.detector_box_threshold,
            text_threshold=self.config.detector_text_threshold,
            target_sizes=target_sizes,
        )[0]

        objects = _objects_from_results(results)
        boxed = _draw_boxes(source, objects)
        return DetectionResult(
            boxed_image=boxed,
            objects=objects,
            status=StepStatus(
                name="detector",
                ok=True,
                used_fallback=False,
                message=f"Grounding DINO detected {len(objects)} objects for query: {query}",
                latency_seconds=perf_counter() - start,
            ),
        )


def _normalize_prompt(prompt: str) -> str:
    terms = []
    for raw in prompt.replace("\n", ".").replace(",", ".").split("."):
        term = " ".join(raw.split())
        if term:
            terms.append(term)
    if not terms:
        terms = ["person", "face", "light", "building", "road"]
    return ". ".join(terms) + "."


def _objects_from_results(results) -> list[DetectedObject]:
    labels = results.get("text_labels")
    if labels is None:
        labels = results.get("labels", [])
    scores = results.get("scores", [])
    boxes = results.get("boxes", [])
    objects: list[DetectedObject] = []
    for label, score, box in zip(labels, scores, boxes):
        if hasattr(score, "item"):
            score = score.item()
        if hasattr(box, "tolist"):
            box = box.tolist()
        xyxy = tuple(int(round(value)) for value in box)
        objects.append(DetectedObject(label=str(label), confidence=float(score), box=xyxy))
    return objects


def _draw_boxes(image: Image.Image, objects: list[DetectedObject]) -> Image.Image:
    boxed = image.copy()
    draw = ImageDraw.Draw(boxed)
    for obj in objects:
        if obj.box is None:
            continue
        box = _clamp_box(obj.box, image.size)
        if box is None:
            continue
        x1, y1, x2, y2 = box
        label = f"{obj.label} {obj.confidence:.2f}"
        _safe_rectangle(draw, (x1, y1, x2, y2), outline=(255, 210, 60), width=4)
        label_width = min(max(1, image.width - x1), max(160, len(label) * 9))
        label_top = max(0, min(image.height - 1, y1 - 28))
        label_bottom = max(label_top + 1, min(image.height, y1))
        _safe_rectangle(draw, (x1, label_top, x1 + label_width, label_bottom), fill=(20, 20, 20))
        draw.text((x1 + 6, max(0, label_bottom - 24)), label, fill=(255, 255, 255))
    return boxed


def _safe_rectangle(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], **kwargs) -> None:
    x1, y1, x2, y2 = box
    left, right = sorted((int(x1), int(x2)))
    top, bottom = sorted((int(y1), int(y2)))
    if right <= left or bottom <= top:
        return
    draw.rectangle((left, top, right, bottom), **kwargs)


def _clamp_box(box: tuple[int, int, int, int], size: tuple[int, int]) -> tuple[int, int, int, int] | None:
    width, height = size
    x1, y1, x2, y2 = box
    x1 = max(0, min(width - 1, x1))
    y1 = max(0, min(height - 1, y1))
    x2 = max(0, min(width - 1, x2))
    y2 = max(0, min(height - 1, y2))
    left, right = sorted((x1, x2))
    top, bottom = sorted((y1, y2))
    if right <= left or bottom <= top:
        return None
    return left, top, right, bottom
