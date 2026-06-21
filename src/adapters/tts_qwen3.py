from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from time import perf_counter

from ..config import DemoConfig
from .base import StepStatus, TTSResult
from .fallbacks import fallback_tts


class QwenTTS:
    def __init__(self, config: DemoConfig) -> None:
        self.config = config

    def synthesize(self, text: str, voice_mode: str = "clone", language: str | None = None) -> TTSResult:
        if not self.config.use_real_models:
            return fallback_tts("real models disabled")

        start = perf_counter()
        try:
            return self._synthesize_real(
                text,
                start,
                _normalize_voice_mode(voice_mode),
                _normalize_tts_language(language or self.config.tts_language),
            )
        except Exception as exc:
            result = fallback_tts("Qwen3-TTS failed")
            result.status.debug = repr(exc)
            result.status.latency_seconds = perf_counter() - start
            return result

    def _synthesize_real(
        self,
        text: str,
        start: float,
        voice_mode: str,
        language: str,
    ) -> TTSResult:
        cleaned = _trim_for_tts(text, language)
        worker = Path(__file__).with_name("qwen_tts_worker.py")
        tts_python = Path(self.config.tts_python)
        if not tts_python.is_absolute():
            tts_python = Path.cwd() / tts_python
        if not tts_python.exists():
            raise FileNotFoundError(f"TTS Python not found: {tts_python}")

        audio_dir = Path(self.config.output_dir) / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        stamp = int(time.time() * 1000)
        output_path = audio_dir / f"qwen3_tts_{stamp}.wav"
        request_path = audio_dir / f"qwen3_tts_{stamp}.json"
        use_voice_clone = voice_mode == "clone"
        ref_audio = _resolve_existing_path(self.config.tts_ref_audio) if use_voice_clone else None
        ref_text_path = _resolve_existing_path(self.config.tts_ref_text) if use_voice_clone else None
        ref_text = ref_text_path.read_text(encoding="utf-8").strip() if ref_text_path else ""
        request = {
            "model_id": self.config.tts_model_id if ref_audio else self.config.tts_fallback_model_id,
            "text": cleaned,
            "language": language,
            "speaker": self.config.tts_speaker,
            "instruction": self.config.tts_voice_instruction,
            "output_path": str(output_path),
            "attn_implementation": "sdpa",
            "ref_audio": str(ref_audio) if ref_audio else "",
            "ref_text": ref_text,
            "voice_mode": voice_mode,
        }
        request_path.write_text(json.dumps(request, ensure_ascii=False))

        env = os.environ.copy()
        env["CUDA_VISIBLE_DEVICES"] = self.config.target_gpu
        env.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
        completed = subprocess.run(
            [str(tts_python), str(worker), str(request_path)],
            cwd=Path.cwd(),
            env=env,
            text=True,
            capture_output=True,
            timeout=self.config.tts_timeout_seconds,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(_tail(completed.stderr or completed.stdout))
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError("Qwen3-TTS subprocess finished without a WAV file")
        try:
            request_path.unlink()
        except OSError:
            pass

        return TTSResult(
            audio_path=str(output_path),
            status=StepStatus(
                name="tts",
                ok=True,
                used_fallback=False,
                message=_status_message(self.config, request),
                latency_seconds=perf_counter() - start,
                debug=_tail(completed.stdout) or None,
            ),
        )


def _normalize_voice_mode(value: str) -> str:
    return "default" if str(value).strip().lower() in {"default", "기본 목소리"} else "clone"


def _normalize_tts_language(value: str) -> str:
    lowered = str(value).strip().lower()
    return "English" if lowered in {"english", "en", "영어", "영어 모드"} else "Korean"


def _trim_for_tts(text: str, language: str) -> str:
    cleaned = " ".join((text or "").split())
    if cleaned:
        return cleaned[:700]
    if language == "English":
        return "In a single image, the story begins."
    return "한 장의 이미지에서 이야기가 시작됩니다."


def _resolve_existing_path(value: str) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path if path.exists() else None


def _status_message(config: DemoConfig, request: dict[str, str]) -> str:
    language = request.get("language") or "Korean"
    if request.get("ref_audio"):
        return f"Generated {language} voice clone narration with {request['model_id']}"
    if request.get("voice_mode") == "clone":
        return f"Voice clone reference missing; generated {language} fallback narration with {request['model_id']}/{config.tts_speaker}"
    return f"Generated {language} default narration with {request['model_id']}/{config.tts_speaker}"


def _tail(value: str, limit: int = 1200) -> str:
    value = value.strip()
    if len(value) <= limit:
        return value
    return value[-limit:]
