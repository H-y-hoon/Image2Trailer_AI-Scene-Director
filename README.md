# Image2Trailer: AI Scene Director

Image2Trailer는 이미지 한 장을 입력받아 영화 예고편 패키지로 변환하는 Gradio 기반 AI 데모입니다. 한 장면을 객체 단서로 분석하고, 영화 콘셉트와 대본을 만든 뒤, 포스터 이미지와 음성 내레이션까지 생성합니다.

## 핵심 기능

- 원본 이미지 업로드
- 텍스트 쿼리 기반 객체 탐지와 bounding box 시각화
- 장면 분석, 장르, 영화 제목, 로그라인 생성
- 4줄 예고편 대본 생성
- 영화 포스터 생성
- 한국어 모드 / 영어 모드 선택
- 기본 목소리 / 내 목소리 클론 선택
- 단계별 fallback으로 라이브 데모 중 일부 모델 실패 시에도 UI 흐름 유지

## 파이프라인

```text
Input image
  + detector query
  -> Grounding DINO
  -> object labels, confidence scores, bounding boxes
  -> Gemma 4 Director
  -> scene analysis, genre, title, logline, script, poster prompt, TTS text
  -> Z-Image-Turbo
  -> movie poster image
  -> Qwen3-TTS
  -> narration WAV file
```

## 사용 모델

| 단계 | 모델 | 크기 | 역할 |
| --- | --- | ---: | --- |
| Object detection | `IDEA-Research/grounding-dino-base` | Base급 open-set detector | 사용자가 입력한 텍스트 쿼리와 이미지 영역을 매칭해 객체명, confidence, box를 생성 |
| Scene director | `google/gemma-4-12B-it` | 12B | 원본 이미지와 탐지 결과를 함께 보고 영화적 콘셉트, 제목, 로그라인, 대본, 포스터 프롬프트 생성 |
| Poster generation | `Tongyi-MAI/Z-Image-Turbo` | 6B | Gemma가 만든 포스터 프롬프트를 기반으로 세로형 영화 포스터 생성 |
| Voice clone TTS | `Qwen/Qwen3-TTS-12Hz-0.6B-Base` | 0.6B | reference voice를 사용해 내 목소리 스타일의 내레이션 생성 |
| Default TTS | `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice` | 0.6B | voice clone 없이 기본 화자 내레이션 생성 |

## 프로젝트 구조

```text
.
├── app.py                         # Gradio 앱 진입점
├── requirements.txt               # 기본 UI/mock 실행 의존성
├── requirements-models.txt        # 실제 GPU 모델 실행 의존성
├── src/
│   ├── config.py                  # 모델 ID, GPU, 출력 경로, threshold 설정
│   ├── pipeline.py                # detector -> director -> poster -> tts 실행 흐름
│   ├── ui.py                      # Gradio UI
│   └── adapters/
│       ├── detector_grounding_dino.py
│       ├── director_gemma.py
│       ├── poster_sdxl.py         # 현재 Z-Image-Turbo 로더 포함
│       ├── tts_qwen3.py
│       ├── qwen_tts_worker.py
│       └── fallbacks.py
├── voice_reference/
│   └── yanghoon_ref_txt.example   # voice clone reference text 예시
└── outputs/                       # 실행 결과 생성 위치, git 제외
```

## 환경 요구사항

기본 UI와 fallback 데모만 실행할 경우:

- Python 3.10 이상 권장
- CPU 실행 가능
- GPU 모델 다운로드 불필요

실제 모델을 실행할 경우:

- NVIDIA GPU 권장
- CUDA 사용 가능한 PyTorch 환경
- 라이브 데모 기준 GPU: `CUDA_VISIBLE_DEVICES=3`
- Hugging Face 모델 접근 권한 및 캐시 필요
- `google/gemma-4-12B-it`는 현재 코드에서 `local_files_only=True`로 로드하므로 실행 전에 Hugging Face cache에 모델이 있어야 합니다.

## 설치 및 실행

### 1. 기본 UI / fallback 모드

기본 모드는 실제 GPU 모델을 로드하지 않습니다. Gradio UI와 전체 출력 형태를 빠르게 확인할 때 사용합니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

브라우저에서 출력된 Gradio URL에 접속한 뒤 이미지를 업로드합니다.

### 2. 실제 모델 의존성 설치

CUDA 12.8 서버 기준으로 작성된 의존성입니다. 서버 CUDA/PyTorch 버전이 다르면 `requirements-models.txt`의 torch wheel 버전을 환경에 맞게 조정해야 합니다.

```bash
source .venv/bin/activate
pip install -r requirements-models.txt
```

### 3. Qwen3-TTS 전용 가상환경 설치

Qwen3-TTS는 Gemma 4 실행 환경과 Transformers 버전 요구사항이 다를 수 있어 별도 가상환경에서 subprocess로 실행합니다.

```bash
python3 -m venv .venv_tts
.venv_tts/bin/python -m pip install --upgrade pip
.venv_tts/bin/pip install --extra-index-url https://download.pytorch.org/whl/cu128 torch==2.11.0+cu128 torchaudio==2.11.0+cu128
.venv_tts/bin/pip install qwen-tts soundfile
```

### 4. Voice clone reference 준비

내 목소리 클론을 사용하려면 reference audio와 해당 오디오에서 읽은 문장이 필요합니다.

기본 경로:

```text
voice_reference/yanghoon_ref.wav
voice_reference/yanghoon_ref_txt
```

`voice_reference/*.wav`, `*.m4a`, `*.mp3` 파일과 실제 reference text 파일은 개인정보 또는 개인 데이터가 될 수 있으므로 git에 올리지 않도록 ignore 처리되어 있습니다. 재현할 때는 예시 파일을 복사한 뒤 실제 녹음 문장으로 바꾸고, reference audio를 같은 경로에 배치합니다.

```bash
cp voice_reference/yanghoon_ref_txt.example voice_reference/yanghoon_ref_txt
# voice_reference/yanghoon_ref.wav 파일을 직접 배치
```

다른 경로를 쓰려면 `TTS_REF_AUDIO`, `TTS_REF_TEXT` 환경 변수로 지정합니다.

### 5. 실제 모델 모드 실행

```bash
USE_REAL_MODELS=1 DEMO_MODE=debug CUDA_VISIBLE_DEVICES=3 .venv/bin/python app.py
```

발표처럼 fallback을 조용히 유지하려면 `DEMO_MODE=presentation`을 사용합니다.

```bash
USE_REAL_MODELS=1 DEMO_MODE=presentation CUDA_VISIBLE_DEVICES=3 .venv/bin/python app.py
```

## 주요 환경 변수

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `USE_REAL_MODELS` | `False` | `1`, `true`, `yes`, `on`이면 실제 모델 어댑터 사용 |
| `DEMO_MODE` | `presentation` | `debug`이면 fallback debug 메시지를 UI에 표시 |
| `CUDA_VISIBLE_DEVICES` | `3` | 실제 모델 실행 GPU |
| `DIRECTOR_MODEL` | `google/gemma-4-12B-it` | 장면 디렉터 모델 |
| `DETECTOR_MODEL_ID` | `IDEA-Research/grounding-dino-base` | 객체 탐지 모델 |
| `DETECTOR_PROMPT` | `person. face. ...` | 기본 탐지 쿼리 |
| `DETECTOR_BOX_THRESHOLD` | `0.25` | Grounding DINO box threshold |
| `DETECTOR_TEXT_THRESHOLD` | `0.25` | Grounding DINO text threshold |
| `POSTER_MODEL` | `Tongyi-MAI/Z-Image-Turbo` | 포스터 생성 모델 |
| `POSTER_WIDTH` | `512` | 포스터 너비 |
| `POSTER_HEIGHT` | `768` | 포스터 높이 |
| `POSTER_STEPS` | `9` | 이미지 생성 inference step 수 |
| `POSTER_GUIDANCE_SCALE` | `0.0` | 포스터 생성 guidance scale |
| `TTS_MODEL_ID` | `Qwen/Qwen3-TTS-12Hz-0.6B-Base` | voice clone TTS 모델 |
| `TTS_FALLBACK_MODEL_ID` | `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice` | 기본 목소리 TTS 모델 |
| `TTS_PYTHON` | `.venv_tts/bin/python` | TTS subprocess Python |
| `TTS_REF_AUDIO` | `voice_reference/yanghoon_ref.wav` | voice clone reference audio |
| `TTS_REF_TEXT` | `voice_reference/yanghoon_ref_txt` | reference audio에서 읽은 문장 |
| `OUTPUT_DIR` | `outputs` | 생성 결과 저장 경로 |

## UI 사용 방법

1. `원본 이미지 업로드`에 이미지를 넣습니다.
2. 필요하면 `포스터 레퍼런스 선택`에 참고 포스터 이미지를 넣습니다. 현재 구현에서는 색감 힌트로만 사용합니다.
3. `탐지 쿼리`에 찾고 싶은 객체를 입력합니다. 예: `person. flower. butterfly. building. light.`
4. `출력 언어`에서 한국어 모드 또는 영어 모드를 선택합니다.
5. `음성 모드`에서 내 목소리 클론 또는 기본 목소리를 선택합니다.
6. `예고편 생성`을 누르면 객체 탐지, 장면 분석, 포스터, 음성 내레이션이 순서대로 생성됩니다.

## 출력물

- 객체 탐지 결과 이미지
- 객체 리스트
- 장면 분석
- 장르
- 영화 제목
- 로그라인
- 예고편 대본
- 생성 포스터
- 음성 내레이션 WAV 파일
- 단계별 실행 상태

생성된 파일은 기본적으로 `outputs/` 아래에 저장되며 git에는 포함하지 않습니다.

## Fallback 정책

라이브 데모 중 한 모델이 실패해도 전체 UI가 멈추지 않도록 각 단계는 독립 fallback을 가집니다.

- detector 실패: mock bounding box와 mock object list 사용
- director 실패: mock story 사용
- poster 실패: mock poster 사용
- TTS 실패: 오디오 없이 상태 메시지 표시

`DEMO_MODE=debug`에서는 실패 원인이 UI 상태창에 함께 표시됩니다.

## 주의사항

- 이 저장소에는 개인 voice reference audio를 포함하지 않습니다.
- Gemma 모델은 로컬 Hugging Face cache에 있어야 합니다.
- 첫 실행 시 모델 다운로드와 로딩으로 시간이 오래 걸릴 수 있습니다.
- Z-Image-Turbo의 제목 텍스트 렌더링은 모델 생성 결과이므로 글자가 항상 완벽하게 보장되지는 않습니다.
- 실제 GPU 메모리 사용량은 입력 이미지, 모델 캐시 상태, PyTorch/CUDA 버전에 따라 달라질 수 있습니다.
