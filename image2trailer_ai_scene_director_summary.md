# Image2Trailer: AI Scene Director

## 1. 프로젝트 개요

**Image2Trailer: AI Scene Director**는 한 장의 이미지를 입력하면 AI가 그 이미지를 영화의 한 장면처럼 해석하고, 이를 바탕으로 **영화 장르, 제목, 로그라인, 예고편 대본, 포스터, 음성 내레이션**까지 생성하는 멀티모달 AI 데모이다.

> 한 장의 이미지를 입력하면, AI 감독이 장면을 분석해 영화 예고편 콘셉트로 변환한다.

---

## 2. 핵심 아이디어

일반적인 이미지 캡셔닝은 “이미지에 무엇이 있는지”를 설명하는 데 그친다.  
이 프로젝트는 한 단계 더 나아가 이미지 속 시각적 단서를 바탕으로 **영화적 상상력과 멀티모달 출력을 결합**한다.

입력 이미지 하나를 다음과 같은 결과물로 확장한다.

- 장면 분석
- 주요 객체 탐지
- 영화 장르 추천
- 영화 제목 생성
- 로그라인 생성
- 예고편 대본 생성
- 포스터 이미지 생성
- AI 음성 내레이션 생성

---

## 3. 사용 모델 구성

| 구분 | 모델 | 역할 |
|---|---|---|
| 중심 모델 | **Qwen3.5-Omni** | 이미지 해석, 장르 판단, 스토리 생성, 예고편 대본 생성, 음성 내레이션 생성 |
| 객체 탐지 모델 | **YOLO-World** 또는 **Grounding DINO** | 이미지 속 주요 객체와 영화적 단서 탐지 |
| 이미지 생성 모델 | **Stable Diffusion XL**, **Flux**, 또는 **Qwen-Image** | 영화 포스터 또는 장르별 스타일 이미지 생성 |

최소 3개의 foundation model을 통합하므로 프로젝트 조건을 충족한다.

---

## 4. 모델별 역할 상세

### 4.1 Qwen3.5-Omni

이 프로젝트의 핵심 모델이며, **AI 감독** 역할을 담당한다.

주요 기능:

- 원본 이미지 전체 장면 설명
- 이미지 분위기 분석
- 영화 장르 선택 또는 추천
- 장르별 해석 생성
- 영화 제목 생성
- 로그라인 생성
- 예고편 대본 생성
- 포스터 생성용 프롬프트 작성
- 음성 내레이션 생성 또는 음성 응답

예시:

```text
장르: 미스터리 스릴러
제목: The Last Light
로그라인: 조용한 골목길에서 사라진 사람의 마지막 흔적이 발견된다.
```

---

### 4.2 YOLO-World / Grounding DINO

객체 탐지 모델은 이미지 속에서 영화적 단서가 될 수 있는 요소를 찾는다.

탐지 대상 예시:

- 사람
- 자동차
- 문
- 창문
- 가방
- 조명
- 간판
- 도로
- 건물
- 의자
- 시계
- 거울

탐지 결과는 Qwen3.5-Omni에 전달되어 더 구체적인 장면 해석과 스토리 생성에 활용된다.

예시:

```text
탐지된 객체:
- streetlight
- parked car
- window
- trash can
- narrow road
```

이를 바탕으로 Qwen3.5-Omni는 다음과 같이 해석할 수 있다.

```text
희미한 가로등과 멈춰 있는 자동차는 정적이고 긴장감 있는 분위기를 만든다.
좁은 골목과 어두운 창문은 미스터리 장르에 적합한 시각적 단서다.
```

---

### 4.3 Stable Diffusion XL / Flux / Qwen-Image

이미지 생성 모델은 Qwen3.5-Omni가 만든 장르, 제목, 분위기, 포스터 프롬프트를 바탕으로 영화 포스터를 생성한다.

생성 가능한 결과물:

- 스릴러 포스터
- SF 포스터
- 공포 영화 포스터
- 로맨스 포스터
- 다큐멘터리 스타일 포스터
- 사이버펑크 스타일 포스터

예시 프롬프트:

```text
A cinematic mystery thriller movie poster based on a dark urban alley, flickering streetlight, parked car, deep shadows, dramatic contrast, suspenseful atmosphere, title: The Last Light.
```

---

## 5. 전체 파이프라인

```text
Input Image
   ↓
Object Detection
YOLO-World / Grounding DINO
   ↓
Scene & Mood Analysis
Qwen3.5-Omni
   ↓
Genre Selection
Qwen3.5-Omni
   ↓
Trailer Script Generation
Qwen3.5-Omni
   ↓
Poster Prompt Generation
Qwen3.5-Omni
   ↓
Poster Generation
Stable Diffusion XL / Flux / Qwen-Image
   ↓
Voice Narration
Qwen3.5-Omni or TTS
   ↓
Final Trailer Experience
```

---

## 6. 최종 출력물

최종 데모는 다음 결과를 제공한다.

| 출력 항목 | 설명 |
|---|---|
| 원본 이미지 | 사용자가 입력한 이미지 |
| 객체 탐지 결과 | 이미지 위에 bounding box 표시 |
| 장면 요약 | 이미지가 어떤 장면인지 설명 |
| 분위기 분석 | 밝음, 어두움, 긴장감, 따뜻함, 고립감 등 |
| 추천 장르 | 스릴러, SF, 공포, 로맨스, 다큐멘터리 등 |
| 영화 제목 | 이미지 기반으로 생성된 제목 |
| 로그라인 | 영화의 핵심 설정을 한 문장으로 요약 |
| 예고편 대본 | 영화 예고편 내레이션 형식의 짧은 대본 |
| 포스터 이미지 | 생성 모델이 만든 영화 포스터 |
| 음성 내레이션 | 예고편 대본을 읽어주는 AI 음성 |

---

## 7. 데모 화면 구성안

웹 데모는 Gradio 또는 Streamlit으로 구현할 수 있다.

```text
[왼쪽]
- 이미지 업로드
- 원본 이미지
- 객체 탐지 bounding box 시각화

[가운데]
- 장면 분석
- 탐지된 주요 단서
- 선택된 영화 장르
- 영화 제목
- 로그라인

[오른쪽]
- 생성된 영화 포스터
- 예고편 대본
- 음성 내레이션 재생 버튼
```

---

## 8. 사용자 인터랙션 아이디어

사용자가 장르를 직접 선택하면 데모의 재미가 커진다.

예시 장르 옵션:

- Mystery Thriller
- Horror
- Sci-Fi
- Romance
- Documentary
- Fantasy
- Cyberpunk

같은 이미지라도 장르에 따라 결과가 달라진다.

예시: 평범한 교실 사진

| 장르 | 생성 결과 예시 |
|---|---|
| Horror | 매일 밤 칠판의 문장이 바뀌는 교실 |
| Romance | 마지막 수업 뒤 책상 위에 남겨진 편지 |
| Sci-Fi | 교실이 시간 이동 실험실이었다는 설정 |
| Mystery | 사라진 학생의 흔적이 맨 뒷자리에서 발견됨 |
| Documentary | 오래된 교실이 기억하는 세대의 이야기 |

---

## 9. 예시 결과

입력 이미지: 어두운 골목길 사진

```text
Detected Objects:
- streetlight
- parked car
- building
- window
- narrow road

Selected Genre:
Mystery Thriller

Movie Title:
The Last Light

Logline:
A quiet alley becomes the final clue in a citywide disappearance case.

Trailer Narration:
In a city that never sleeps, one street went silent.
Under the last flickering light, a forgotten clue waits to be found.
Every window hides a witness.
Every shadow remembers a name.
This winter, the truth is closer than the dark.

Poster Prompt:
A cinematic mystery thriller movie poster set in a dark urban alley, flickering streetlight, lonely parked car, deep shadows, dramatic contrast, suspenseful atmosphere, title text: The Last Light.
```

---

## 10. 프로젝트의 강점

### 10.1 발표 임팩트가 큼

이미지 하나가 영화 예고편으로 바뀌는 과정은 직관적이고 시각적으로 인상적이다.

### 10.2 Qwen3.5-Omni 사용 이유가 명확함

Qwen3.5-Omni의 이미지 이해, 텍스트 생성, 음성 응답 능력을 모두 활용할 수 있다.

### 10.3 모델 통합성이 좋음

세 모델이 각각 독립적으로 결과를 내는 것이 아니라 하나의 흐름으로 연결된다.

```text
객체 탐지 결과
→ 장면 해석
→ 영화적 스토리 생성
→ 포스터 생성
→ 음성 내레이션
```

### 10.4 과제 조건에 잘 맞음

- 하나의 이미지를 중심으로 진행
- 최소 3개의 foundation model 사용
- 의미 있는 정보 추출
- 모델 출력 간 통합
- 시각적으로 인상적인 최종 데모 제작 가능

---

## 11. 구현 난이도

| 기능 | 난이도 | 설명 |
|---|---|---|
| 이미지 업로드 | 낮음 | Gradio 또는 Streamlit으로 구현 가능 |
| 객체 탐지 | 중간 | YOLO-World가 상대적으로 구현이 간단함 |
| Qwen3.5-Omni 연동 | 중간 | 로컬 환경 또는 API 사용 여부에 따라 달라짐 |
| 포스터 생성 | 중간~높음 | GPU 환경과 모델 선택에 따라 난이도 차이 있음 |
| 음성 내레이션 | 중간 | Qwen3.5-Omni speech output 또는 별도 TTS 사용 가능 |
| 전체 UI 통합 | 중간 | Gradio 기반 구성이 적합함 |

---

## 12. 현실적인 구현 버전

### 12.1 최소 구현 버전

사용 모델:

```text
Qwen3.5-Omni
+ YOLO-World
+ Stable Diffusion XL
```

출력:

- 원본 이미지
- 탐지된 객체 리스트
- 장면 분석
- 영화 장르
- 영화 제목
- 로그라인
- 예고편 대본
- 포스터 이미지

음성 내레이션은 선택 기능으로 둔다.

---

### 12.2 확장 구현 버전

사용 모델:

```text
Qwen3.5-Omni
+ Grounding DINO
+ Stable Diffusion XL / Flux
+ TTS or Qwen speech output
```

출력:

- 객체 탐지 bounding box 시각화
- 장르별 예고편 대본 생성
- 영화 포스터 생성
- 음성 내레이션
- 사용자 질문 응답
- 장르 재선택 기능

---

## 13. 발표에서 강조할 포인트

발표에서는 다음 흐름을 강조하면 좋다.

1. 단순 이미지 설명이 아니라, 이미지를 영화적 장면으로 재해석했다.
2. 객체 탐지 모델이 이미지 속 시각적 단서를 추출했다.
3. Qwen3.5-Omni가 단서를 바탕으로 장르, 제목, 스토리, 대본을 생성했다.
4. 이미지 생성 모델이 포스터를 만들어 시각적 결과물을 완성했다.
5. 음성 내레이션을 통해 실제 예고편 같은 경험을 제공했다.

---

## 14. 추천 프로젝트 제목

### 기본 제목

```text
Image2Trailer: AI Scene Director
```

### 발표용 제목 후보

```text
Image2Trailer: Turning One Image into a Cinematic AI Trailer
```

```text
AI Scene Director: From a Single Image to a Movie Trailer
```

```text
One Image, One Trailer: Multimodal AI Movie Director
```

---

## 15. 최종 요약

**Image2Trailer: AI Scene Director**는 한 장의 이미지를 입력으로 받아 객체 탐지, 장면 해석, 영화적 스토리 생성, 포스터 생성, 음성 내레이션을 하나의 파이프라인으로 연결하는 멀티모달 AI 프로젝트이다.

핵심 모델 조합:

```text
Qwen3.5-Omni
+ YOLO-World / Grounding DINO
+ Stable Diffusion XL / Flux / Qwen-Image
```

핵심 가치:

> 이미지를 단순히 설명하는 것이 아니라, 하나의 영화 예고편 경험으로 변환한다.
