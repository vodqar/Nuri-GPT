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
| `test_e2e.py` | 전체 워크플로우 | E2E | 전체 |
```