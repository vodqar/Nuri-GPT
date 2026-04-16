# 알림장 인삿말 생성기 — 백엔드 날씨 맥락 주입 구현

백엔드에서 기상청 단기예보 API를 호출하여 날씨 맥락을 수집·요약하고, 날짜/절기/기념일 등의 맥락과 함께 Dify Chatflow의 `inputs` 변수로 주입하여 알림장 인삿말을 생성하는 기능을 구현한다.

---

## 데이터 흐름

```
Frontend (시군구 선택 + 생성 버튼)
  → POST /api/greeting/generate { region: "광주광역시 북구" }
    → Backend:
        1. region_grid_map.json에서 nx, ny 조회
        2. WeatherService: 기상청 getVilageFcst 호출 → 당일 날씨 요약
        3. ContextBuilder: 날짜/요일/월해/주차/절기/기념일 조립
        4. Dify Chatflow 호출 (inputs에 모든 맥락 주입)
    → Frontend: 인삿말 텍스트 표시
```

---

## Step 1: 환경변수 및 설정 추가

**파일**: `app/core/config.py`, `.env.example`

`Settings` 클래스에 추가:
```python
# 기상청 API 설정
kma_api_key: Optional[str] = Field(default=None, alias="KMA_API_KEY")

# Dify 인삿말 생성용 Chatflow 설정
dify_greeting_api_key: Optional[str] = Field(default=None, alias="DIFY_GREETING_API_KEY")
dify_greeting_api_url: Optional[str] = Field(default=None, alias="DIFY_GREETING_API_URL")
```

`.env.example`에 추가:
```env
# 기상청 단기예보 API 키
KMA_API_KEY=your-kma-api-key

# Dify 인삿말 생성용 Chatflow (미설정 시 기본값 사용)
DIFY_GREETING_API_KEY=your-dify-greeting-api-key
DIFY_GREETING_API_URL=https://dify.vodqar.com/v1
```

**검증**: `get_settings()` 로딩 시 새 필드가 누락 없이 인식되는지 확인

---

## Step 2: 시군구→격자좌표 매핑 데이터 생성

**입력**: `download/Weather_API/동네예보지점좌표(위경도)_202601.csv`
**출력**: `app/data/region_grid_map.json`

CSV에서 **3단계(읍면동)가 비어있는 행**만 추출 = 시군구 대표 좌표.

변환 스크립트로 1회 실행하여 JSON 생성:
```json
{
  "광주광역시 북구": {"nx": 59, "ny": 75},
  "광주광역시 동구": {"nx": 60, "ny": 74},
  "서울특별시 종로구": {"nx": 60, "ny": 127},
  ...
}
```

키 포맷: `"{1단계} {2단계}"` (예: "광주광역시 북구")
- 2단계도 비어있으면 `"{1단계}"` (예: "세종특별자치시")

**검증**: JSON 파일에 전국 시군구 약 260개 항목 포함, 광주광역시 북구 → nx=59, ny=75 확인

---

## Step 3: WeatherService 구현

**파일**: `app/services/weather.py`

### 클래스 구조

```python
class WeatherService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_settings().kma_api_key
        self.base_url = "https://apihub.kma.go.kr/api/typ02/openApi/VilageFcstInfoService_2.0"
        self._grid_map: Optional[Dict[str, Dict]] = None  # lazy load

    # 시군구 → nx, ny 조회
    def get_grid_coords(self, region: str) -> Tuple[int, int]

    # 현재 시각 기준 가장 최근 base_time 계산
    def _calculate_base_time(self) -> Tuple[str, str]  # (base_date, base_time)

    # 기상청 단기예보 API 호출 (getVilageFcst)
    def _fetch_vilage_fcst(self, nx: int, ny: int, base_date: str, base_time: str) -> Dict

    # 당일 날씨 데이터 추출 + 자연어 요약
    def get_weather_summary(self, region: str) -> str
```

### base_time 계산 규칙

현재 시각(KST) 기준으로 가장 최근 발표 시각 산출:
- 02:10 이전 → 전날 2300
- 02:10~05:10 → 0200
- 05:10~08:10 → 0500
- 08:10~11:10 → 0800
- 11:10~14:10 → 1100
- 14:10~17:10 → 1400
- 17:10~20:10 → 1700
- 20:10~23:10 → 2000
- 23:10 이후 → 2300

### API 호출 파라미터

```
GET {base_url}/getVilageFcst
  ?authKey={api_key}
  &numOfRows=1000        # 당일+4일 전체 (최대 742건/발표)
  &pageNo=1
  &dataType=JSON
  &base_date={YYYYMMDD}
  &base_time={HHMM}
  &nx={nx}
  &ny={ny}
```

### 응답 파싱 — 당일 추출 항목

| category | 의미 | 추출 방식 |
|----------|------|-----------|
| TMX | 일 최고기온 | fcstDate == 오늘 인 항목 |
| TMN | 일 최저기온 | fcstDate == 오늘 인 항목 |
| SKY | 하늘상태 | 1→맑음, 3→구름많음, 4→흐림 |
| PTY | 강수형태 | 0→없음, 1→비, 2→비/눈, 3→눈, 4→소나기 |
| POP | 강수확률 | fcstDate == 오늘 인 항목 중 최대값 |

### 요약 출력 포맷

```
"맑음, 최고 22℃, 최저 14℃, 강수확률 10%"
"비, 최고 18℃, 최저 12℃, 강수확률 80%"
"구름많음, 최고 20℃, 최저 13℃, 강수확률 30%"
```

PTY가 0이 아니면 SKY 대신 PTY 기반 날씨 표현 사용 (비/눈이면 "비"가 하늘상태보다 우선).

### 에러 처리

- API 키 누락 → `ExternalAPIError("기상청 API 키가 설정되지 않았습니다")`
- API 호출 실패 → 로깅 후 빈 날씨 맥락 반환 (인삿말 생성은 차단하지 않음)
- 시군구 매핑 없음 → `ValidationError("지원하지 않는 지역입니다")`

**검증**: mock 기상청 응답으로 `get_weather_summary()` 단위 테스트 통과

---

## Step 4: GreetingService 구현

**파일**: `app/services/greeting.py`

### 클래스 구조

```python
class GreetingService:
    def __init__(self, weather_service: Optional[WeatherService] = None):
        self.weather_service = weather_service or WeatherService()

    # 날짜/요일/월해/주차 맥락 생성
    def _build_date_context(self) -> Dict[str, str]

    # 절기/기념일 맥락 생성
    def _build_seasonal_context(self) -> Dict[str, str]

    # 전체 맥락 조립 + Dify Chatflow 호출
    def generate_greeting(self, region: str) -> str
```

### `_build_date_context()` 출력

```python
{
    "date_info": "2026년 4월 16일 (목요일)",
    "month_week": "4월 3주차",
}
```

주차 계산: 해당 월의 1일이 무슨 요일인지 기준으로, 1일이 월요일이면 1주차 시작, 아니면 첫 월요일까지를 1주차로 간주 (유치원 실무 기준).

### `_build_seasonal_context()` 출력

```python
{
    "seasonal_info": "청명(4월 4일) ~ 곡우(4월 20일)",  # 현재 절기 구간
    "holiday_info": "해당 없음",                         # 오늘이 법정기념일이면 표시
}
```

- **절기**: 24절기 날짜 테이블 하드코딩 (매년 날짜 거의 동일, ±1일 오차는 인삿말에 무해)
- **법정기념일**: 약 15개 공휴일/기념일 하드코딩 (날짜 고정형 + 대체공휴일 제외)

### `generate_greeting()` 전체 흐름

```python
def generate_greeting(self, region: str) -> str:
    # 1. 날씨 맥락
    weather_summary = self.weather_service.get_weather_summary(region)

    # 2. 날짜/절기/기념일 맥락
    date_ctx = self._build_date_context()
    seasonal_ctx = self._build_seasonal_context()

    # 3. Dify Chatflow 호출
    inputs = {
        "date_info": date_ctx["date_info"],
        "month_week": date_ctx["month_week"],
        "weather_context": weather_summary,
        "seasonal_info": seasonal_ctx["seasonal_info"],
        "holiday_info": seasonal_ctx["holiday_info"],
    }

    dify_key = settings.dify_greeting_api_key or settings.dify_api_key
    dify_url = settings.dify_greeting_api_url or settings.dify_api_url

    payload = {
        "inputs": inputs,
        "query": "알림장 인삿말을 생성해주세요.",
        "response_mode": "blocking",  # 인삿말은 짧으므로 blocking으로 충분
        "conversation_id": "",
        "user": "nuri-gpt-user",
        "auto_generate_name": False,
    }

    # 기존 LlmService의 SSE 파싱 로직 재사용 (streaming도 지원 가능하나 V1은 blocking)
    ...
```

**검증**: mock WeatherService + mock Dify 응답으로 `generate_greeting()` 단위 테스트

---

## Step 5: API 엔드포인트 + 스키마

### 스키마: `app/schemas/greeting.py`

```python
class GreetingRequest(BaseModel):
    region: str = Field(..., description="시군구 지역명 (예: '광주광역시 북구')")

class GreetingResponse(BaseModel):
    greeting: str = Field(..., description="생성된 알림장 인삿말")
```

### 엔드포인트: `app/api/endpoints/greeting.py`

```python
@router.post("/generate", response_model=GreetingResponse)
async def generate_greeting(
    request: GreetingRequest,
    current_user: dict = Depends(get_current_user),
    greeting_service: GreetingService = Depends(get_greeting_service),
):
    greeting = greeting_service.generate_greeting(region=request.region)
    return GreetingResponse(greeting=greeting)
```

### 라우터 등록: `app/main.py`

```python
from app.api.endpoints.greeting import router as greeting_router
app.include_router(greeting_router, prefix="/api/greeting", tags=["Greeting"])
```

### DI 등록: `app/core/dependencies.py`

```python
def get_greeting_service() -> GreetingService:
    return GreetingService()
```

**검증**: `POST /api/greeting/generate` 엔드포인트 Swagger에 노출, 인증 필요 확인

---

## Step 6: 단위 테스트

### `tests/test_weather_service.py`

| 테스트 케이스 | 내용 |
|--------------|------|
| `test_get_grid_coords_valid` | "광주광역시 북구" → nx=59, ny=75 |
| `test_get_grid_coords_invalid` | 존재하지 않는 지역 → ValidationError |
| `test_calculate_base_time` | 시간대별 올바른 base_time 산출 |
| `test_get_weather_summary_sunny` | SKY=1, PTY=0 → "맑음, 최고 22℃, ..." |
| `test_get_weather_summary_rainy` | PTY=1 → "비, 최고 18℃, ..." |
| `test_get_weather_summary_api_failure` | API 오류 시 빈 문자열 반환 (생성 차단 안 함) |

### `tests/test_greeting_service.py`

| 테스트 케이스 | 내용 |
|--------------|------|
| `test_build_date_context` | 날짜/요일/주차 포맷 검증 |
| `test_build_seasonal_context_no_holiday` | 기념일 없을 시 "해당 없음" |
| `test_build_seasonal_context_with_holiday` | 어린이날 등 기념일 있을 시 표시 |
| `test_generate_greeting_full` | 전체 흐름: 날씨+날짜+절기 → Dify 호출 |
| `test_generate_greeting_weather_failure` | 날씨 API 장애 시에도 인삿말 생성 (빈 날씨 맥락) |

모든 테스트는 `unittest.mock`으로 기상청 API, Dify API 격리.

**검증**: `venv/bin/pytest tests/test_weather_service.py tests/test_greeting_service.py -v` 통과

---

## Step 7: 기존 테스트 회귀 확인

```bash
venv/bin/pytest -q
```

기존 전체 테스트가 새 모듈 추가로 인해 깨지지 않는지 확인.

---

## Step 8: 문서 업데이트

| 문서 | 업데이트 내용 |
|------|-------------|
| `docs/API_REFERENCE.md` | `POST /api/greeting/generate` 엔드포인트 추가 |
| `docs/ARCHITECTURE.md` | GreetingService 모듈 의존성 다이어그램에 추가 |
| `docs/DEVELOPMENT.md` | GreetingService DI 팩토리, 테스트 구조 추가 |
| `.env.example` | KMA_API_KEY, DIFY_GREETING_API_KEY/URL 추가 |

하단에 `*Last Updated: 2026-04-16*` 기록.

---

## 파일 생성/수정 요약

| 작업 | 파일 | 신규/수정 |
|------|------|-----------|
| 설정 추가 | `app/core/config.py` | 수정 |
| 환경변수 예시 | `.env.example` | 수정 |
| 매핑 데이터 | `app/data/region_grid_map.json` | 신규 |
| 날씨 서비스 | `app/services/weather.py` | 신규 |
| 인삿말 서비스 | `app/services/greeting.py` | 신규 |
| API 스키마 | `app/schemas/greeting.py` | 신규 |
| API 엔드포인트 | `app/api/endpoints/greeting.py` | 신규 |
| DI 등록 | `app/core/dependencies.py` | 수정 |
| 라우터 등록 | `app/main.py` | 수정 |
| 단위 테스트 | `tests/test_weather_service.py` | 신규 |
| 단위 테스트 | `tests/test_greeting_service.py` | 신규 |
| 문서 | `docs/API_REFERENCE.md` | 수정 |
| 문서 | `docs/ARCHITECTURE.md` | 수정 |
| 문서 | `docs/DEVELOPMENT.md` | 수정 |

---

## 범위 외 (이번 구현에서 제외)

- **프론트엔드 UI**: `features/greeting/` 컴포넌트 — 별도 작업
- **Dify Chatflow 생성**: Dify 대시보드에서 수동 생성, 백엔드는 API 키만 환경변수로 대기
- **할당량 연동**: 인삿말 생성의 UsageService 연동 — 후속 작업
- **4일치 확장 날씨**: 현재 당일만 요약, 향후 주간 날씨 인삿말 확장 가능
- **캐싱**: 기상청 API 응답 캐싱 (같은 base_time 내 중복 호출 방지) — 후속 작업
