# Nuri-GPT (누리GPT)

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)
![React](https://img.shields.io/badge/React-19-61DAFB.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-Ready-3178C6.svg)



https://github.com/user-attachments/assets/a4f65300-6e5d-43e5-94dc-6ecadf1798d2



**AI 기반 보육일지 자동 생성 에이전트 시스템**

누리GPT는 어린이집 보육교사들의 관찰일지 작성 업무를 자동화하여 행정 부담을 줄이고 보육의 질을 높일 수 있도록 돕는 AI 서비스입니다. 수기 메모를 인식하고, 기존에 사용하던 일지 양식을 분석하여 평가제 기준에 맞는 관찰일지를 자동으로 생성합니다.

---

## 🚀 현재 진행 상황 (Status: In Progress)

### ✅ 구현 완료 기능

| 분류 | 기능 | 설명 |
|------|------|------|
| **인증** | 회원 관리 | Supabase Auth 기반 로그인/회원가입, JWT 로컬 검증, 로그인 유지(Remember Me) |
| **템플릿** | 양식 분석 · 커스텀화 | 빈 일지 양식 이미지 업로드 → Vision AI가 구조를 JSON으로 추출, 드래그 앤 드롭 정렬 지원 |
| **일지 생성** | 관찰일지 자동 작성 | 교사 메모(텍스트/수기 이미지 OCR) + 템플릿 구조 → Dify RAG Chatflow가 평가제 기준에 맞는 일지 자동 완성 |
| **일지 생성** | Aggressive Mode | 교사가 비워둔 필드를 LLM이 문맥을 유추하여 채워주는 적극적 추론 모드 |
| **일지 생성** | 코멘트 기반 재생성 | 결과물 검토 중 특정 필드에 수정 코멘트 작성 → 해당 부분만 LLM이 부분 재생성 |
| **도구** | 알림장 인삿말 생성 | 지역+날짜 기반으로 날씨·절기·공휴일·기념일 맥락을 자동 수집하여 인삿말 문구 생성 |
| **관리** | 기록 관리 · 재작업 | 생성 히스토리 조회, 버전 관리, 이전 일지를 기반으로 재생성 |
| **관리** | 할당량 관리 | 요금제별 일간/주간 AI 사용량 제한 및 시각화 (Success-only 차감 정책) |
| **관리** | 계정 설정 | 사용자 프로필 및 범용 설정(User Preferences) 관리 |

### 🔧 진행 중인 과제

보육교사마다, 어린이집마다 사용하는 일지의 양식이 매우 다양하여 **데이터 입력 화면(UI) 렌더링 방식의 고도화**를 진행 중입니다. AI가 추출한 복잡한 양식 구조를 원본 레이아웃에 가깝게 웹에서 편집할 수 있는 인터페이스를 설계하고 있습니다.

---

## 🎯 주요 기술 특징

### 1. 템플릿 분석 (Vision AI)
기존에 사용 중인 빈 보육일지 양식 이미지를 업로드하면 Gemini Vision이 셀 병합·계층 구조를 포함한 문서 레이아웃을 JSON으로 자동 추출합니다.

### 2. 수기 메모 인식 (Vision OCR)
교사가 작성한 수기 메모 이미지를 업로드하면 텍스트로 자동 변환·정규화합니다. 이미지 크롭·회전 유틸리티를 내장하고 있습니다.

### 3. 일지 생성 · 재생성 (Dify RAG Chatflow)
일지 자동 생성과 코멘트 기반 재생성 모두 **Dify Chatflow**를 통해 수행됩니다. RAG 파이프라인에 평가제 가이드라인 지식을 결합하여, 팩트 기반 전문 일지를 생성합니다. 최초 생성과 재생성은 별도의 Chatflow로 분리 운영할 수 있습니다.

### 4. 알림장 인삿말 생성 (Dify RAG Chatflow)
기상청 단기/중기예보 API와 한국천문연구원 특일 정보 API에서 날씨·공휴일·절기·기념일·잡절 정보를 자동 수집한 뒤, Dify Chatflow에 맥락으로 전달하여 계절감 있는 인삿말을 생성합니다. 지역 설정은 User Preferences에 자동 저장됩니다.

### 5. 성능 최적화
JWT 로컬 검증, Bootstrap 엔드포인트(1 RTT 통합 조회), Cache-Control 헤더, DB 복합 인덱스, TanStack Query 캐시 등을 활용하여 데이터 로딩 지연을 최소화합니다.

---

## 📂 프로젝트 구조

프론트엔드와 백엔드가 분리된 모노레포(Monorepo) 구조입니다.

```
Nuri-GPT/
├── nuri-gpt-backend/          # FastAPI 백엔드 (AI 연동, DB, API)
│   ├── app/
│   │   ├── api/endpoints/     # REST API 라우터
│   │   ├── core/              # 설정, 인증, DI
│   │   ├── db/repositories/   # DB CRUD 추상화
│   │   ├── services/          # 비즈니스 로직 (LLM, OCR, Vision, Weather, Greeting 등)
│   │   └── schemas/           # Pydantic 스키마
│   └── tests/
└── nuri-gpt-frontend/frontend/ # React 프론트엔드
    └── src/
        ├── features/          # Feature-First 도메인 모듈
        │   ├── auth/          #   인증
        │   ├── observation/   #   관찰일지 (템플릿·생성·히스토리)
        │   ├── greeting/      #   알림장 인삿말
        │   └── settings/      #   계정 설정
        ├── components/        # 공용 UI 컴포넌트
        ├── services/          # API 통신, 쿼리 키
        ├── store/             # Zustand 전역 상태
        └── hooks/             # 공용 훅
```

---

## 🛠 기술 스택

### Backend

| 레이어 | 기술 | 용도 |
|--------|------|------|
| Framework | FastAPI + Uvicorn | 비동기 REST API |
| Database | Supabase (PostgreSQL + Storage) | 사용자·템플릿·일지·할당량 관리 |
| AI/LLM | Dify RAG Chatflow | 일지 생성·재생성·인삿말 생성 |
| AI/Vision | Google Gemini (Vision & OCR) | 템플릿 구조 분석, 수기 메모 인식 |
| External API | 기상청 단기/중기예보, 천문연구원 특일정보 | 날씨·절기·공휴일 맥락 수집 |
| Auth | Supabase Auth + PyJWT 로컬 검증 | JWT 인증, 세션 관리 |
| Validation | Pydantic v2 | 스키마 및 환경 변수 관리 |

### Frontend

| 레이어 | 기술 | 용도 |
|--------|------|------|
| Framework | React 19 + Vite | UI 라이브러리, 고속 빌드 |
| Language | TypeScript | 정적 타입 |
| Styling | Tailwind CSS v4 | 반응형 UI |
| State (서버) | TanStack Query | API 캐싱, prefetch, 자동 무효화 |
| State (클라이언트) | Zustand | 인증, 사용자 설정 |
| Form | React Hook Form + Zod | 폼 상태 & 스키마 검증 |
| Network | Axios | API 통신 (인터셉터 기반 에러 처리) |
| Mocking | MSW | 백엔드 없이 독립 개발 |

---

## ⚙️ 환경 변수

백엔드 `.env.example`을 참고하여 `.env` 파일을 구성합니다.

| 변수 | 설명 | 필수 |
|------|------|:----:|
| `SUPABASE_URL` / `SUPABASE_KEY` / `SUPABASE_SERVICE_KEY` | Supabase 프로젝트 연결 | ✅ |
| `SUPABASE_JWT_SECRET` | JWT 로컬 검증용 시크릿 | ✅ |
| `GEMINI_API_KEY` | Google Gemini API 키 | ✅ |
| `DIFY_API_KEY` / `DIFY_API_URL` | Dify Chatflow (일지 생성) | ✅ |
| `DIFY_REGENERATE_API_KEY` | Dify Chatflow (재생성, 미설정 시 기본 키 사용) | |
| `DIFY_GREETING_API_KEY` / `DIFY_GREETING_API_URL` | Dify Chatflow (인삿말 생성) | |
| `KMA_API_KEY` | 기상청 단기예보 API 키 | |
| `KMA_MID_API_KEY` | 기상청 중기예보 API 키 | |
| `KMA_SPECIAL_DAY_API_KEY` | 한국천문연구원 특일 정보 API 키 | |
| `LLM_*_MODEL` / `LLM_*_TEMPERATURE` | LLM 모델 및 파라미터 설정 | |

---

## 📝 라이선스 (License)

This project is licensed under the MIT License.
