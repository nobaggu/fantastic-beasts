# 🐲 신비한 동물사전

> 산해경과 동아시아 신화 속 신비한 동물들을 RAG 기반으로 검색하고 AI가 설명해주는 동물사전

🔗 **라이브 데모**: [https://fantastic-beasts-tau.vercel.app](https://fantastic-beasts-tau.vercel.app)

> ⚠️ 백엔드가 Free 플랜으로 운영 중이라 첫 접속 시 1~2분 로딩이 있을 수 있습니다.

---

## 📸 서비스 화면

| 메인 화면 | 검색 결과 | 동물 상세 |
|:---------:|:---------:|:---------:|
| ![메인](동물사전%20사용/신비한%20동물%20사전%20-%20정면화면.png) | ![검색](동물사전%20사용/검색화면.png) | ![상세](동물사전%20사용/카드%20눌렀을%20때.png) |

---

## 📖 프로젝트 소개

고려대학교 디지털 인문학 수업 결과물을 발전시킨 프로젝트입니다.

산해경, 한국 민간신화, 나무위키 등 문헌에서 수집한 **63개 동물 데이터**를 기반으로, 사용자가 자연어로 질문하면 관련 동물을 벡터 검색으로 찾아 GPT-4o가 설명해주는 서비스입니다.

- "날개 달린 동물 알려줘" → 관련 동물 카드 + AI 설명
- "봉황이 뭐야?" → 상세 설명 + AI 생성 이미지

### 데이터 수집 방법
- **원본 10개**: 수업 과제로 직접 정리한 산해경 동물 데이터
- **크롤링 53개**: 나무위키 크롤링 + GPT-4o-mini로 구조화
- **이미지**: gpt-image-1 (DALL-E)로 동물별 AI 이미지 생성

---

## 🔄 RAG 파이프라인

```
사용자 질문 (예: "불을 다루는 동물")
    ↓
[rag.py - OpenAI text-embedding-3-small]
    ↓
질문을 1536차원 벡터로 변환
    ↓
[코사인 유사도 검색]
    ↓
db.json에서 관련 동물 top-k개 retrieve
    ↓
[llm.py - GPT-4o]
    ↓
고문헌 자료를 컨텍스트로 주입 → 답변 생성
    ↓
사용자에게 답변 + 동물 카드 반환
```

---

## 🛠️ 기술 스택

| 영역 | 기술 |
|------|------|
| Frontend | React 18, Vite |
| Backend | FastAPI, Python 3.11 |
| AI / 검색 | OpenAI GPT-4o, text-embedding-3-small |
| 이미지 생성 | OpenAI gpt-image-1 |
| 데이터 수집 | requests, BeautifulSoup4 (나무위키 크롤링) |
| 배포 | Vercel (프론트), Render (백엔드) |

---

## 📁 폴더 구조

```
fantastic-beasts/
├── 📂 frontend/                  # ⭐ React 프론트엔드
│   └── src/
│       ├── App.jsx               # 메인 컴포넌트 (검색창, 카드 그리드, 모달)
│       └── App.css               # 스타일
│
├── 📂 images/                    # 🖼️ AI 생성 동물 이미지 (63개 PNG)
├── 📂 data/                      # 💾 개별 동물 JSON (크롤링 원본)
│
├── main.py                       # 🚀 FastAPI 서버 (엔드포인트)
├── rag.py                        # 🔍 벡터 검색 파이프라인
├── llm.py                        # 🤖 GPT 연동 및 프롬프트 구성
├── crawl.py                      # 🕷️ 나무위키 크롤러 + GPT 구조화
├── generate_images.py            # 🎨 DALL-E 이미지 생성
├── build_index.py                # 📊 임베딩 인덱스 빌드
├── db.json                       # 📦 전체 동물 데이터베이스 (63개)
├── requirements.txt              # 📦 Python 의존성
├── .env                          # 🔐 API 키 (git 제외)
└── .gitignore
```

---

## 📚 주요 모듈 설명

### 1️⃣ `main.py` - FastAPI 서버
**역할:** API 엔드포인트 제공 및 이미지 정적 파일 서빙

```
GET  /beasts        → 전체 동물 목록 반환
GET  /beasts/{name} → 특정 동물 상세 조회
POST /ask           → RAG 검색 + GPT 답변 생성
GET  /images/{name} → 동물 이미지 파일 서빙
```

### 2️⃣ `rag.py` - 벡터 검색 파이프라인
**역할:** 동물 데이터를 임베딩하고 코사인 유사도로 검색

```python
build_index()          # db.json → 벡터 인덱스 생성 (index.npy)
retrieve(query, top_k) # 질문과 유사한 동물 top-k개 반환
```

- OpenAI `text-embedding-3-small` 모델 사용 (1536차원)
- 코사인 유사도 = 정규화된 벡터의 내적 (numpy 연산)
- 인덱스는 서버 시작 시 메모리에 로드

### 3️⃣ `llm.py` - GPT 연동
**역할:** retrieve된 동물 데이터를 컨텍스트로 GPT-4o 호출

```python
build_prompt(query, context_beasts) # 고문헌 자료 + 질문 → 프롬프트 조합
ask_llm(query, context_beasts)      # GPT-4o 호출 → 답변 반환
```

### 4️⃣ `crawl.py` - 나무위키 크롤러
**역할:** 동물 이름 리스트 → 나무위키 본문 수집 → GPT 구조화 → db.json 저장

```python
fetch_namu(name)        # 나무위키 HTML 파싱 → 본문 텍스트 추출
gpt_extract(name, text) # GPT-4o-mini로 JSON 스키마 변환
```

추출 필드: `animals`(구성 동물), `original`(원문 한자), `translated`(설명), `source`(출처), `comment`(한 줄 감상)

### 5️⃣ `generate_images.py` - 이미지 생성
**역할:** image 필드가 비어있는 동물에 대해 DALL-E 이미지 자동 생성

```python
build_prompt(beast)       # 동물 데이터 → 영문 DALL-E 프롬프트
generate_and_save(beast)  # gpt-image-1 호출 → images/{name}.png 저장
```

프롬프트 스타일: `traditional East Asian ink painting, mystical atmosphere`

---

## 💻 로컬 실행 방법

### 사전 준비
```bash
git clone https://github.com/nobaggu/fantastic-beasts.git
cd fantastic-beasts
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 환경 변수 설정
```bash
# .env 파일 생성
OPENAI_API_KEY=sk-your-key-here
```

### 백엔드 실행
```bash
python build_index.py          # 최초 1회 인덱스 빌드
python -m uvicorn main:app --reload
# → http://localhost:8000
```

### 프론트엔드 실행
```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

> 로컬 실행 시 `frontend/src/App.jsx`의 `const API` 값을 `http://localhost:8000`으로 변경하세요.

---

## 🔐 보안 고려사항

⚠️ **API 키 관리**
- `.env` 파일에 `OPENAI_API_KEY` 저장, git에 커밋 금지 (`.gitignore` 적용)
- Render 배포 시 Environment Variables에서 직접 입력

---

작성일: 2026-06-11
