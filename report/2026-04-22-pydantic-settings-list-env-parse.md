## pydantic-settings List[str] 환경변수 파싱 실패

### What Happened
백엔드 컨테이너가 `docker compose up` 후 `Restarting` 루프에 빠졌습니다. 로그에는 `pydantic_settings.exceptions.SettingsError: error parsing value for field "cors_origins" from source "EnvSettingsSource"`가 반복 출력되었습니다. `.env.production`의 `CORS_ORIGINS=https://nuri-gpt.vodqar.com` 문자열을 `config.py`의 `List[str]` 필드에 매핑하지 못한 것이 원인이었습니다.

### Root Cause
`app/core/config.py`에서 `cors_origins: List[str] = Field(..., alias="CORS_ORIGINS")`로 선언했습니다. pydantic-settings v2의 `EnvSettingsSource`는 `.env` 파일에서 `List[str]` 필드를 읽을 때 쉼표로 split하지만, **타입 힌팅과 env source의 파싱 규칙이 충돌**할 수 있습니다. 특히 `List[str]`에 단일 문자열 값을 할당할 때, pydantic-settings가 리스트 변환을 시도하다가 `SettingsError`를 발생시키는 케이스가 존재합니다.

또한 `field_validator(mode='before')`를 추가했음에도 Docker 이미지 재빌드 후에도 동일 에러가 반복되어, **env source의 파싱이 validator 이전에 실패**하는 것으로 확인됩니다 — validator는 pydantic 모델 인스턴스화 이후가 아닌 이전 단계에서도 실행될 수 있지만, env source 자체의 파싱 실패는 validator에 도달하지 않습니다.

### Why Not Caught
1. **로컬 개발 환경과의 차이**: 로컬에서는 `.env` 파일에 `CORS_ORIGINS=http://localhost:3000,http://localhost:5173,...`처럼 **쉼표 구분** 값을 사용했습니다. 쉼표가 있으면 pydantic-settings가 자연스럽게 리스트로 split합니다. 프로덕션에서는 단일 값 `https://nuri-gpt.vodqar.com`만 사용해 이 케이스를 발견하지 못했습니다.
2. **Docker 빌드 전 구문 검증만 수행**: `python -m py_compile`은 구문(Syntax)만 검증하므로 런타임 pydantic 검증을 잡지 못했습니다.
3. **단위 테스트 부재**: `config.py`의 `Settings` 객체를 실제 `.env` 파일과 함께 인스턴스화하는 통합 테스트가 없었습니다.

### Preventability
예측 가능했습니다. pydantic-settings의 `List[str]` 필드 동작은 쉼표 구분에 의존하며, 단일 문자열은 엣지 케이스입니다. 프로덕션 환경변수 템플릿(`.env.production.example`)을 작성할 때, 이 값이 단일 URL만 포함할 가능성을 고려했어야 합니다.


### Fix Applied
- `config.py`: `cors_origins: List[str]` → `cors_origins: str`
- `main.py`: `_cors_origins_list = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]` 추가
- 불필요한 `field_validator` 제거
