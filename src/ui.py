from __future__ import annotations

import gradio as gr
from PIL import Image

from .config import CONFIG
from .pipeline import run_pipeline


VOICE_CLONE_LABEL = "내 목소리 클론"
DEFAULT_VOICE_LABEL = "기본 목소리"
KOREAN_MODE_LABEL = "한국어 모드"
ENGLISH_MODE_LABEL = "영어 모드"


def build_app() -> gr.Blocks:
    with gr.Blocks(title="Image2Trailer: AI Scene Director") as demo:
        gr.Markdown("# Image2Trailer: AI Scene Director")
        gr.Markdown("이미지 1장을 영화 예고편 패키지로 변환하는 라이브 데모입니다.")

        with gr.Row():
            with gr.Column(scale=1):
                image_input = gr.Image(label="원본 이미지 업로드", type="pil")
                poster_reference = gr.Image(label="포스터 레퍼런스 선택", type="pil")
                detector_prompt = gr.Textbox(
                    label="탐지 쿼리",
                    value=CONFIG.detector_prompt,
                    lines=3,
                    placeholder="예: person. car. door. light. shadow.",
                )
                language_mode = gr.Radio(
                    label="출력 언어",
                    choices=[KOREAN_MODE_LABEL, ENGLISH_MODE_LABEL],
                    value=KOREAN_MODE_LABEL,
                )
                voice_mode = gr.Radio(
                    label="음성 모드",
                    choices=[VOICE_CLONE_LABEL, DEFAULT_VOICE_LABEL],
                    value=VOICE_CLONE_LABEL,
                )
                run_button = gr.Button("예고편 생성", variant="primary")
                status = gr.Textbox(label="실행 상태", lines=7, interactive=False)

            with gr.Column(scale=1):
                boxed_image = gr.Image(label="객체 탐지 결과")
                objects = gr.Textbox(label="객체 리스트", lines=6)
                scene_analysis = gr.Textbox(label="장면 분석", lines=6)

            with gr.Column(scale=1):
                poster = gr.Image(label="생성 포스터")
                audio = gr.Audio(label="음성 내레이션", type="filepath")

        with gr.Row():
            genre = gr.Textbox(label="영화 장르")
            title = gr.Textbox(label="영화 제목")

        logline = gr.Textbox(label="로그라인", lines=2)
        script = gr.Textbox(label="예고편 대본", lines=6)

        run_button.click(
            fn=_run,
            inputs=[image_input, poster_reference, detector_prompt, language_mode, voice_mode],
            outputs=[
                boxed_image,
                objects,
                scene_analysis,
                genre,
                title,
                logline,
                script,
                poster,
                audio,
                status,
            ],
        )

    return demo


def _run(
    image: Image.Image | None,
    poster_reference: Image.Image | None,
    detector_prompt: str,
    language_mode: str,
    voice_mode: str,
):
    if image is None:
        raise gr.Error("이미지를 먼저 업로드하세요.")

    output_language = "English" if language_mode == ENGLISH_MODE_LABEL else "Korean"
    tts_voice_mode = "default" if voice_mode == DEFAULT_VOICE_LABEL else "clone"
    result = run_pipeline(
        image,
        poster_reference=poster_reference,
        output_language=output_language,
        detector_prompt=detector_prompt,
        tts_voice_mode=tts_voice_mode,
    )
    return (
        result.boxed_image,
        result.objects,
        result.scene_analysis,
        result.genre,
        result.title,
        result.logline,
        result.script,
        result.poster,
        result.audio_path,
        result.status,
    )
