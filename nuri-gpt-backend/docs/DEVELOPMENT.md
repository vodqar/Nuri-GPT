## 🛠 개발 및 디버깅 가이드

### DI 구조 — `app/core/dependencies.py`

모든 서비스·리포지토리는 팩토리 함수로 정의되며 FastAPI `Depends()`로 주입됩니다.

```python
get_config()              → Settings
get_supabase()            → Supabase Client
get_user_repository()     → UserRepository(client)
get_log_repository()      → LogRepository(client)
get_template_repository() → TemplateRepository(client)
get_storage_service()     → StorageService()
get_ocr_service()         → OcrService()
get_llm_service()         → LlmService()
get_vision_service()      → VisionService()
get_special_day_service() → SpecialDayService()
get_greeting_service()    → GreetingService(special_day_service=SpecialDayService())
```

---

### 새 기능 추가 체크리스트

| 작업 | 수정 위치 |
|------|-----------|
| API 엔드포인트 추가 | `app/api/endpoints/` → `main.py`에 라우터 등록 |
| 비즈니스 로직 추가 | `app/services/` |
| DB 모델 추가 | `app/db/models/` + `app/db/repositories/` |
| 요청/응답 스키마 추가 | `app/schemas/` |
| 새 서비스 클래스 추가 | `app/core/dependencies.py`에 팩토리 함수 등록 필수 |
| 패키지 추가 | `requirements.txt`에 버전 범위 명시 (`>=`, `~=`) |

- 외부 API/DB 연결은 반드시 생성자 파라미터로 주입 (DI 패턴)
- 단위 테스트: `unittest.mock`으로 외부 의존성 격리 / 통합 테스트: 실제 API 연동 필요
- 테스트 파일명: `tests/test_<모듈명>.py`

---

### 디버깅 가이드

#### 422 Unprocessable Entity
- Form 필드명 불일치가 주요 원인
1. `app/schemas/` 해당 스키마의 `Field()` 정의와 실제 요청 비교
2. `multipart/form-data`인 경우 `Form(...)` 파라미터명 확인
3. `app/utils/file_validator.py` 확장자/MIME 허용 목록 확인

#### 500 Internal Server Error
1. `app/main.py` 예외 핸들러 로그 확인 (Authentication / Authorization / NotFound / Validation / ExternalAPI)
2. `app/api/endpoints/` → `app/services/` 순서로 예외 발생 지점 추적
3. `.env` 누락 키 확인 (`SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_KEY`, `GEMINI_API_KEY`)

#### DB 연결 실패
1. `.env`의 `SUPABASE_URL`, `SUPABASE_KEY` 확인
2. `app/db/connection.py` 클라이언트 초기화 확인 (`lru_cache` 싱글톤)
3. Supabase 대시보드 프로젝트 상태 확인
4. 리포지토리 테이블명: `users`, `templates`, `logs`

#### Vision LLM 템플릿 처리 오류
1. `app/utils/file_validator.py` 이미지 파일 허용 여부 확인
2. `vision.py`의 `extract_template_structure` 호출 확인 (빈 응답 → API 키/네트워크 의심)
3. `system_instruction` 기준 JSON 반환 포맷 점검

#### Gemini API 호출 실패
1. `.env`의 `GEMINI_API_KEY` 유효성 확인
2. `app/services/ocr.py` 또는 `app/services/llm.py` 로그 확인
3. Gemini API 할당량 및 네트워크 상태 확인

---

### 코드 수정 주의사항

- **결합도 최소화**: 서비스는 외부 의존성을 생성자 주입으로만 수신
- **테스트 격리**: 단위 테스트는 `mock`만으로 실행 가능해야 함
- **스펙**: Python 3.11+, FastAPI 0.104+
- **문서 동기화**: 코드 변경 시 README + handoff 문서 함께 업데이트
- **인증 미구현**: `security.py`는 현재 빈 파일, Generate/Export API는 `MOCK_USER_ID` 사용 중
- **계층 경계 안정화**: 프론트엔드나 API 소비자가 일정한 구조를 기대한다면, 그 구조를 어디서 안정화할지 명확히 하고 숨은 가정으로 남기지 않음
- **제약의 승격**: 작업 후반에야 드러난 구조적 제약은 handoff 메모에서 끝내지 말고 관련 문서의 판단 기준으로 승격

---

## 🚀 개발 서버 시작

> **통합 실행**: 루트 디렉토리에서 `make dev`로 백엔드+프론트엔드 동시 시작 가능. 자세한 내용은 `frontend/docs/SERVER_GUIDE.md` 참조.

### 수동 실행

```bash
# 백엔드 (8001번 포트)
./venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# 프론트엔드는 별도 터미널에서
# cd ../nuri-gpt-frontend/frontend && npm run dev
```

---

## 🧪 테스트

### 실행 명령

```bash
# 전체 테스트
pytest -q

# 특정 모듈
pytest tests/test_upload.py tests/test_generate.py -v

# E2E 통합 테스트
pytest tests/test_e2e.py -v

# DB 테스트
pytest tests/test_db_unit.py tests/test_db.py -v

# 커버리지 (결과: htmlcov/index.html)
pytest --cov=app --cov-report=html
```

### 테스트 구조

| 파일 | 대상 | 유형 | 외부 의존성 |
|------|------|------|------------|
| `test_main.py` | FastAPI 진입점 | 단위 | 없음 |
| `test_db_unit.py` | DB 리포지토리 | 단위 | mock |
| `test_db.py` | DB 리포지토리 | 통합 | Supabase |
| `test_storage.py` | Storage 서비스 | 단위+통합 | Supabase Storage |
| `test_ocr.py` | OCR 서비스 | 단위 | mock (Gemini) |
| `test_llm.py` | LLM 서비스 | 단위 | mock (Gemini) |
| `test_template_upload.py` | Vision Template Upload API | 단위+통합 | mock (Gemini) |
| `test_generate.py` | Generate API | 통합 | mock services |
| `test_generate_api.py` | Generate/Regenerate API | 단위 | mock services |
| `test_e2e.py` | 전체 워크플로우 | E2E | 전체 |
| `test_weather_service.py` | WeatherService (단기/중기 분기) | 단위 | mock (기상청 API) |
| `test_greeting_service.py` | GreetingService (날씨+날짜+절기→Dify) | 단위 | mock (Weather, SpecialDay, Dify) |
| `test_special_day_service.py` | SpecialDayService (특일 API+캐시) | 단위 | mock (한국천문연구원 API) |

---

### 변경 이력

#### 2026-04-14 — 재생성 응답 파싱 로직 수정

- **`app/services/llm.py`** `generate_regenerated_activities()` 응답 파싱 개선
  - Dify 시스템 프롬프트에 Jinja `is_regeneration` 분기 추가 이후, 응답 형식이 `{"updated_activities": [...]}` 리스트 형식으로 올 수 있음
  - 기존: 평면 `{target_id: text}` dict 형식만 처리 → silent fallback 발생 가능
  - 수정: `updated_activities` 리스트 형식 우선 처리, 평면 dict는 레거시 호환으로 유지
- **`tests/test_generate_api.py`** 재생성 테스트 강화
  - `test_regenerate_log_success`: `is_aggressive`, `child_age` 파라미터 전달 여부 검증 추가
  - `test_regenerate_log_list_format_response`: 리스트 형식 응답 파싱 케이스 신규 추가

*Last Updated: 2026-04-16*

#### 2026-04-16 — 특일 정보 API 연동

- **`app/services/special_day.py`** SpecialDayService + SpecialDayCache 신규 추가
  - 한국천문연구원 특일 정보 OpenAPI (4개 오퍼레이션) 연동
  - 차등 TTL 캐시: 당월 12시간 / 미래월 7일, grace period 24시간
  - API 키 미설정 또는 장애 시 하드코딩 fallback
  - `refresh(year)` 메서드로 백그라운드 스케줄러 전환 고려
- **`app/services/greeting.py`** 하드코딩 → `_FALLBACK_*` 전환, SpecialDayService 주입
  - Dify inputs에 `anniversary_info`, `sundry_day_info` 키 추가
- **`app/core/dependencies.py`** `get_special_day_service()` DI 팩토리 추가
- **`app/core/config.py`** `KMA_SPECIAL_DAY_API_KEY` 설정 추가
- **`tests/test_special_day_service.py`** 신규 — 캐시 TTL, API 파싱, fallback 테스트

#### 2026-04-16 — 알림장 인삿말 생성기 백엔드 구현

- **`app/services/weather.py`** WeatherService 신규 추가
  - 기상청 단기예보(getVilageFcst) + 중기예보(getMidLandFcst/getMidTa) 분기 처리
  - Δ 0~3일 → 단기예보, Δ 4~10일 → 중기예보, Δ >10 → 빈 문자열
  - 시군구→nx/ny/mid_regId 매핑 (`app/data/region_grid_map.json`, 270개 시군구)
- **`app/services/greeting.py`** GreetingService 신규 추가
  - 날씨 + 날짜/요일/주차 + 24절기 + 법정기념일 맥락 조립 → Dify Chatflow 호출
  - 날씨 API 장애 시에도 인삿말 생성 (빈 날씨 맥락으로 fallback)
  - Dify 응답은 `streaming`/`blocking` 모두 파싱 가능하도록 처리하고, 요청 input key 및 응답 길이 로깅으로 디버깅 가능성 보강
- **`app/api/endpoints/greeting.py`** `POST /api/greeting/generate` 엔드포인트 신규
- **`app/schemas/greeting.py`** GreetingRequest/GreetingResponse 스키마 신규
- **`app/core/dependencies.py`** `get_greeting_service()` DI 팩토리 추가
- **`app/core/config.py`** KMA_API_KEY, KMA_MID_API_KEY, DIFY_GREETING_API_KEY/URL 설정 추가