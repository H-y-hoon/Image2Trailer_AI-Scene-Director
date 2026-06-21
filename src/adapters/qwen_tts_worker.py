from __future__ import annotations

import json
import sys
from pathlib import Path

import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: qwen_tts_worker.py REQUEST_JSON", file=sys.stderr)
        return 2

    request_path = Path(sys.argv[1])
    request = json.loads(request_path.read_text())
    output_path = Path(request["output_path"])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    has_cuda = torch.cuda.is_available()
    model = Qwen3TTSModel.from_pretrained(
        request["model_id"],
        device_map="cuda:0" if has_cuda else "cpu",
        dtype=torch.bfloat16 if has_cuda else torch.float32,
        attn_implementation=request.get("attn_implementation", "sdpa"),
    )

    ref_audio = request.get("ref_audio") or ""
    ref_text = request.get("ref_text") or ""
    if ref_audio:
        wavs, sample_rate = model.generate_voice_clone(
            text=request["text"],
            language=request.get("language") or "Korean",
            ref_audio=ref_audio,
            ref_text=ref_text or None,
            x_vector_only_mode=not bool(ref_text),
            non_streaming_mode=True,
        )
    else:
        wavs, sample_rate = model.generate_custom_voice(
            text=request["text"],
            language=request.get("language") or "English",
            speaker=request.get("speaker") or "Ryan",
            instruct=request.get("instruction") or "Speak clearly with a cinematic trailer tone.",
        )
    sf.write(output_path, wavs[0], sample_rate)
    print(json.dumps({"output_path": str(output_path), "sample_rate": sample_rate, "samples": len(wavs[0])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
