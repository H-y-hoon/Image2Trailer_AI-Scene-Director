import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class DemoConfig:
    target_latency_minutes: str = "2-3"
    demo_mode: str = os.getenv("DEMO_MODE", "presentation")
    use_real_models: bool = _env_bool("USE_REAL_MODELS", False)
    target_gpu: str = os.getenv("CUDA_VISIBLE_DEVICES", "3")
    director_model: str = os.getenv("DIRECTOR_MODEL", "google/gemma-4-12B-it")
    detector_model: str = os.getenv("DETECTOR_MODEL", "Grounding DINO")
    detector_model_id: str = os.getenv("DETECTOR_MODEL_ID", "IDEA-Research/grounding-dino-base")
    detector_prompt: str = os.getenv(
        "DETECTOR_PROMPT",
        "person. face. car. streetlight. window. door. sign. road. building. "
        "bag. clock. mirror. shadow. light.",
    )
    detector_box_threshold: float = float(os.getenv("DETECTOR_BOX_THRESHOLD", "0.25"))
    detector_text_threshold: float = float(os.getenv("DETECTOR_TEXT_THRESHOLD", "0.25"))
    poster_model: str = os.getenv("POSTER_MODEL", "Tongyi-MAI/Z-Image-Turbo")
    poster_width: int = int(os.getenv("POSTER_WIDTH", "512"))
    poster_height: int = int(os.getenv("POSTER_HEIGHT", "768"))
    poster_steps: int = int(os.getenv("POSTER_STEPS", "9"))
    poster_guidance_scale: float = float(os.getenv("POSTER_GUIDANCE_SCALE", "0.0"))
    poster_model_optional: str = os.getenv("POSTER_MODEL_OPTIONAL", "Tongyi-MAI/Z-Image-Turbo")
    tts_model: str = os.getenv("TTS_MODEL", "Qwen3-TTS 0.6B Base VoiceClone")
    tts_model_id: str = os.getenv("TTS_MODEL_ID", "Qwen/Qwen3-TTS-12Hz-0.6B-Base")
    tts_fallback_model_id: str = os.getenv("TTS_FALLBACK_MODEL_ID", "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice")
    tts_python: str = os.getenv("TTS_PYTHON", ".venv_tts/bin/python")
    tts_language: str = os.getenv("TTS_LANGUAGE", "Korean")
    tts_speaker: str = os.getenv("TTS_SPEAKER", "Ryan")
    tts_ref_audio: str = os.getenv("TTS_REF_AUDIO", "voice_reference/yanghoon_ref.wav")
    tts_ref_text: str = os.getenv("TTS_REF_TEXT", "voice_reference/yanghoon_ref_txt")
    tts_voice_instruction: str = os.getenv(
        "TTS_VOICE_INSTRUCTION",
        "한국어 영화 예고편 내레이터처럼 낮고 선명하게, 긴장감 있게 말하세요.",
    )
    tts_timeout_seconds: int = int(os.getenv("TTS_TIMEOUT_SECONDS", "180"))
    output_language: str = "English title/logline/poster prompt; Korean script/narration"
    ui_language: str = "Korean"
    fallback_enabled: bool = True
    output_dir: str = os.getenv("OUTPUT_DIR", "outputs")
    adapter_timeout_seconds: int = int(os.getenv("ADAPTER_TIMEOUT_SECONDS", "180"))
    director_max_new_tokens: int = int(os.getenv("DIRECTOR_MAX_NEW_TOKENS", "512"))
    director_temperature: float = float(os.getenv("DIRECTOR_TEMPERATURE", "0.7"))
    director_top_p: float = float(os.getenv("DIRECTOR_TOP_P", "0.9"))

    @property
    def debug_enabled(self) -> bool:
        return self.demo_mode == "debug"


CONFIG = DemoConfig()
