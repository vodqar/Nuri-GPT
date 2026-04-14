# Nuri-GPT Backend

## 프로젝트 개요

**목적**: 보육교사의 관찰일지 작성 AI 자동화

| 항목 | 내용 |
|------|------|
| 초기 타겟 | 어린이집 보육교사 (B2C) |
| 확장 타겟 | 누리과정 유치원 교사 |
| 수익 모델 | 월 구독형 |

**설계 원칙**
- **Zero-Hallucination**: 교사 입력 팩트만 사용, 추론 금지
- **멀티모달 입력**: 수기 메모 이미지 또는 직접 텍스트
- **양식 유연성**: Vision AI로 빈 템플릿 구조 자동 분석
- **평가제 준수**: 보건복지부 평가제 기준 문장 생성

***

## 핵심 기능

| 기능 | 설명 | 출력 |
|------|------|------|
| Vision OCR | Gemini Flash로 수기 메모 이미지 → 텍스트 변환 및 정규화 | 정제된 텍스트 |
| 관찰일지 생성 | 팩트 + 평가제 가이드라인 결합 프롬프트 → JSON 구조화 출력 | `title`, `observation_content`, `evaluation_content`, `development_areas` |
| 빈 템플릿 분석 | Gemini Vision으로 양식 이미지의 선/병합 셀 분석 → 계층 구조 추출 | `structure_json` |
| 할당량 관리 | 요금제별 일일/주간 사용량 제한 및 성공 시에만 차감 정책 (KST 기준) | `user_usages`, `plan_quotas` |
| 데이터 관리 | Supabase(PostgreSQL): 사용자/템플릿/로그; Storage 버킷: `memos`, `templates`, `exports` | — |

***

## 기술 스택

| 레이어 | 기술 | 용도 |
|--------|------|------|
| Framework | FastAPI 0.104+ | 비동기 API |
| Language | Python 3.11+ | 타입 힌팅 |
| ASGI Server | Uvicorn | 고성능 비동기 서버 |
| Database | Supabase (PostgreSQL) | 사용자/템플릿/로그 |
| Storage | Supabase Storage | 이미지 파일 |
| AI/LLM | Google Gemini (Vision & Text) | 구조 분석 + 일지 생성 |
| Validation | Pydantic v2 + pydantic-settings | 스키마 및 환경 변수 |
| Testing | pytest + pytest-asyncio | 단위/통합 테스트 |

**주요 패키지** (`requirements.txt`)
```
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
pydantic>=2.10.0
pydantic-settings>=2.1.0
supabase~=2.4.6
httpx>=0.27.0
google-generativeai>=0.8.0
Pillow>=10.0.0
python-multipart>=0.0.6
```

***

## 설치 및 실행

**1. 환경 설정**
```bash
cd nuri-gpt-backend && python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**2. 환경 변수**

`.env.example` 복사 후 편집 (`cp .env.example .env`):

| 변수 | 예시 값 | 비고 |
|------|---------|------|
| `SUPABASE_URL` | `https://xxx.supabase.co` | 필수 |
| `SUPABASE_KEY` | `your-anon-key` | 필수 |
| `SUPABASE_SERVICE_KEY` | `your-service-role-key` | 필수 |
| `GEMINI_API_KEY` | `your-gemini-api-key` | 필수 |
| `LLM_VISION_MODEL` | `gemini-3.1-flash` | |
| `LLM_TEXT_MODEL` | `gemini-2.5-flash` | |
| `LLM_OCR_MODEL` | `gemini-3.1-flash-lite-preview` | |
| `LLM_*_THINKING_LEVEL` | `default` | `none` \| `default` \| `medium` \| `high` |
| `LLM_*_TEMPERATURE` | `0.2` (OCR: `1.0`) | |
| `DEBUG` | `True` | Swagger/ReDoc 활성화 조건 |
| `HOST` / `PORT` | `0.0.0.0` / `8000` | |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173,http://localhost:5174` | 미설정 시 기본: `localhost:3000`, `localhost:5173`, `localhost:5174`, `127.0.0.1:5173`, `127.0.0.1:5174` |

**3. 서버 실행**
```bash
uvicorn app.main:app --reload
```

**4. API 문서** (`DEBUG=True` 시 활성화)

| 문서 | URL |
|------|-----|
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| PoC 테스트 페이지 | http://localhost:8000/poc |

***
*Last updated: 2026-04-15*

***
