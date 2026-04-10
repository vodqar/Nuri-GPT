# Nuri-GPT 프로젝트 요약 (Project Summary)

## 1. 프로젝트 개요
**Nuri-GPT**는 보육교사의 업무 부담을 줄이기 위해 AI를 활용하여 **관찰일지 작성을 자동화**하는 솔루션입니다. 수기 메모를 디지털 텍스트로 변환하고, 어린이집의 다양한 양식(템플릿)을 분석하여 맞춤형 일지를 생성합니다.

- **주요 타겟**: 어린이집 및 유치원 보육교사
- **핵심 가치**: Zero-Hallucination(입력 팩트 기반), 멀티모달 입력(이미지/텍스트), 양식 유연성

## 2. 기술 스택 (Tech Stack)

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **AI/LLM**: Google Gemini (Vision, Text, OCR), Dify (Chatflow)
- **Database/Storage**: Supabase (PostgreSQL, Storage)
- **Validation**: Pydantic v2

### Frontend
- **Framework**: React 19 + Vite
- **Styling**: Tailwind CSS v4
- **State Management**: Zustand
- **Form Handling**: React Hook Form + Zod

## 3. 핵심 기능 (Core Features)
- **Vision OCR**: 수기 메모 이미지를 정제된 텍스트로 변환.
- **관찰일지 생성**: 입력된 팩트와 평가제 가이드라인을 결합하여 구조화된(JSON) 일지 생성.
- **템플릿 분석**: 빈 양식 이미지를 분석하여 데이터 삽입 위치 및 계층 구조 추출.
- **관찰일지 자동 저장**: 생성된 일지를 데이터베이스(`observation_journals`)에 자동 기록.
- **HWPX 내보내기**: 생성된 결과를 한글(HWP) 호환 양식으로 다운로드.

## 4. 현재 진행 상황 (Current Status)

### ✅ 완료된 사항 (2026-03-28 기준)
- **자동 저장 시스템**: `/api/generate/log` 호출 시 일지가 DB에 자동 저장됨.
- **Journal API**: 저장된 일지 목록 조회 및 상세 조회를 위한 API 엔드포인트 구현.
- **백엔드 구조화**: Repository 패턴을 적용하여 데이터 접근 로직 분리.

### 🛠 진행 중 / 예정 사항
- **재생성 파이프라인 완성**: Dify Chatflow를 활용하여 사용자의 수정 코멘트를 반영한 부분 재생성 기능 구현.
- **프론트엔드 연동**: 저장된 일지 목록을 화면에 표시하고 불러오는 기능 UI 구현.
- **보안 강화**: 현재 테스트용 `MOCK_USER_ID`를 실제 인증 시스템과 연동.

## 5. 주요 디렉토리 구조
- `nuri-gpt-backend/`: FastAPI 기반 백엔드 서버 및 AI 연동 로직
- `nuri-gpt-frontend/`: React 기반 프론트엔드 애플리케이션
- `prompts/`: 관찰일지 생성 및 분석을 위한 LLM 프롬프트 관리
- `docs/`: API 레퍼런스, 아키텍처 등 프로젝트 문서화

---
*마지막 업데이트: 2026-04-01*
