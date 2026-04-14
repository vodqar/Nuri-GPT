# Nuri-GPT (누리GPT)

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)
![React](https://img.shields.io/badge/React-19-61DAFB.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-Ready-3178C6.svg)



https://github.com/user-attachments/assets/a4f65300-6e5d-43e5-94dc-6ecadf1798d2



**AI 기반 보육일지 자동 생성 에이전트 시스템**

누리GPT는 어린이집 보육교사들의 관찰일지 작성 업무를 자동화하여 행정 부담을 줄이고 보육의 질을 높일 수 있도록 돕는 AI 서비스입니다. 수기 메모를 인식하고, 기존에 사용하던 일지 양식을 분석하여 평가제 기준에 맞는 관찰일지를 자동으로 생성합니다.

---

## 🚧 현재 진행 상황 (Status: Paused)

현재 프로젝트는 대부분의 핵심 기능 개발을 완료한 후, 프론트엔드 UI/UX 이슈로 인하여 **임시 중단**된 상태입니다. 

### ✅ 완료된 핵심 기능
- **회원 관리**: 사용자 로그인 및 세션 관리
- **템플릿 커스텀화**: 기존 문서 양식을 이미지로 업로드 시 AI가 필드와 구조를 분석하여 재사용 가능한 템플릿 형태로 저장
- **AI 관찰일지 생성 시스템**: 
  - 저장된 템플릿을 불러와 각 필드에 교사가 짧은 메모(수기 텍스트 또는 이미지)를 입력하면 LLM이 일지를 자동 완성
  - **Aggressive Mode (적극적 추론 모드)**: 교사가 기억나지 않아 비워둔 필드를 활성화 시, LLM이 문맥을 유추하여 강제로 내용을 채워주는 스마트 기능
- **상호작용형 AI 편집**: 결과물 검토 중 마음에 들지 않는 필드가 있다면 해당 칸에 코멘트를 달아 LLM이 부분적으로만 재생성(Regenerate)하도록 지시 가능
- **기록 관리 및 재작업**: 생성된 일지의 히스토리 조회 기능 및 조회 화면에서 이전 일지를 기반으로 다시 재생성 가능
- **계정 및 할당량 관리**: 사용자 프로필 정보 조회 및 서비스 이용량(일간/주간 할당량) 시각화 UI 구현

### 🛑 프로젝트 임시 중단 사유
보육교사마다, 어린이집마다 사용하는 일지의 양식이 수없이 다양하여 **데이터 입력 화면(UI)의 렌더링 방식에서 근본적인 어려움**에 부딪혔습니다.
1. **과도하게 길어지는 입력 폼**: AI가 복잡한 양식의 이미지를 JSON 형태의 완벽한 구조체로 추출해 내는 것은 성공했습니다. 하지만 추출된 데이터가 너무 많을 경우, 프론트엔드 화면에서 수직 구조(1 Key 당 1 Input)로 렌더링되면서 교사가 입력해야 할 폼의 스크롤이 지나치게 길어져 오히려 혼란과 불편을 야기했습니다.
2. **복잡한 WYSIWYG 에디터 구현의 한계**: 이를 해결하기 위해 기존 문서 양식(가로/세로 표 병합 등)의 고유 레이아웃을 웹 브라우저 상에 그대로 유지하면서 마치 워드/한글 문서를 편집하듯 입력할 수 있는 직관적인 경험을 제공하고자 했습니다. 하지만 동적이고 제각각인 JSON 데이터를 원본과 똑같은 구조의 UI로 매핑하여 화면에 뿌려주는 작업의 기술적 난이도가 매우 높아 부득이하게 개발을 중단하게 되었습니다.

---

## 🎯 주요 기술 기능 (Key Tech Features)

1. **템플릿 분석 (Vision AI)**
   - 기존에 사용 중인 빈 보육일지 양식(이미지, HWPX 등)을 업로드하면 AI가 구조를 자동으로 분석하고 매핑합니다.
2. **수기 메모 인식 (Vision OCR)**
   - 교사가 작성한 수기 메모 이미지를 업로드하면 텍스트로 자동 변환(정규화)합니다.
3. **관찰일지 자동 생성 (LLM)**
   - 팩트 기반의 입력 데이터를 바탕으로 보건복지부 평가제 가이드라인에 부합하는 일지를 생성합니다. (Zero-Hallucination 지향)
4. **일지 내보내기 (Export)**
   - 생성된 일지를 검토/수정한 후 원래의 HWPX 양식에 맞춰 문서를 다운로드할 수 있습니다.

---

## 📂 프로젝트 구조 (Project Structure)

Nuri-GPT는 프론트엔드와 백엔드가 분리된 모노레포(Monorepo) 구조로 구성되어 있습니다.

- **`nuri-gpt-backend/`**: FastAPI 기반의 파이썬 백엔드 서버 (AI 연동, DB 처리, API 제공)
- **`nuri-gpt-frontend/frontend/`**: React + Vite 기반의 프론트엔드 웹 애플리케이션

---

## 🛠 기술 스택 (Tech Stack)

### Backend
- **Framework**: FastAPI, Uvicorn
- **Database**: Supabase (PostgreSQL, Storage)
- **AI/LLM**: Google Gemini (Vision & Text)
- **Validation**: Pydantic v2
- **Testing**: pytest

### Frontend
- **Framework**: React 19, Vite
- **Language**: TypeScript
- **Styling**: Tailwind CSS v4
- **State Management**: Zustand
- **Form/Validation**: React Hook Form, Zod
- **API Mocking**: MSW (Mock Service Worker)

---

## 🚀 시작하기 (Getting Started)

### 1. Backend 환경 설정 및 실행

```bash
# 백엔드 디렉토리 이동
cd nuri-gpt-backend

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# 환경변수 설정 (.env 파일 생성)
cp .env.example .env
# .env 파일에 Supabase 및 Gemini API Key 등을 입력하세요.

# 로컬 서버 실행
uvicorn app.main:app --reload
```
- API 문서 (Swagger UI): `http://localhost:8000/docs`

### 2. Frontend 환경 설정 및 실행

```bash
# 프론트엔드 디렉토리 이동
cd nuri-gpt-frontend/frontend

# 패키지 설치
npm install

# 개발 서버 실행 (Vite + MSW)
npm run dev
```
- 프론트엔드 앱 접속: `http://localhost:5173` (포트 변경 가능)

---

## 📝 라이선스 (License)
This project is private and confidential.
