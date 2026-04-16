# Handoff Document — 알림장 인삿말 생성기 백엔드 구현

*Last Updated: 2026-04-16*

---

## 🎯 Goal

알림장 배포일 기준 날씨를 조회하기 위해 단기예보(당일~+3일)와 중기예보(+4~+10일)를 분기 처리하고, 날짜/절기/기념일 맥락과 함께 Dify Chatflow `inputs`에 주입하여 인삿말을 생성하는 백엔드 시스템 구현.

---

## ✅ Current Progress

### 완료된 작업 (8단계 전부 완료)

1. **환경변수 및 설정 추가** — `config.py`에 `KMA_API_KEY`, `KMA_MID_API_KEY`, `DIFY_GREETING_API_KEY/URL` 추가, `.env.example` 업데이트
2. **시군구→좌표 매핑 데이터 생성** — `app/data/region_grid_map.json` (270개 시군구, nx/ny + mid_land_reg_id/mid_temp_reg_id 통합)
   - 강원특별자치도 영서/영동 분기, 전북특별자치도 매핑 포함
   - 변환 스크립트: `scripts/generate_region_map.py`
3. **WeatherService 구현** — `app/services/weather.py`
   - 단기예보(getVilageFcst) + 중기예보(getMidLandFcst/getMidTa) 분기
   - base_time/tmFc 계산, 응답 파싱, 요약 텍스트 생성
4. **GreetingService 구현** — `app/services/greeting.py`
   - 날씨 + 날짜/요일/주차 + 24절기 + 법정기념일 맥락 조립 → Dify Chatflow 호출
5. **API 엔드포인트 + 스키마** — `POST /api/greeting/generate` (region + target_date)
6. **단위 테스트** — 27개 테스트 전부 통과
7. **기존 테스트 회귀 확인** — 신규 코드로 인한 회귀 없음
8. **문서 업데이트** — `API_REFERENCE.md`, `ARCHITECTURE.md`, `DEVELOPMENT.md` 업데이트

---

## 🔧 What Worked

- CSV(UTF-8 BOM) → JSON 변환 스크립트로 270개 시군구 매핑 자동 생성
- 강원특별자치도(구 강원도), 전북특별자치도(구 전라북도) 명칭 변경 대응
- 날씨 API 장애 시 graceful fallback (빈 날씨 맥락으로 인삿말 생성 계속)

---

## ⚠️ What Didn't Work / Gotchas

- CSV 인코딩이 euc-kr이 아닌 UTF-8 BOM이었음 → `utf-8-sig` 필요
- 기상청 단기예보 API 키(authKey)와 중기예보 API 키(serviceKey)는 서로 다른 포털에서 발급
- `이어도`는 해상 구역이라 중기예보 regId 매핑 불가 (현재 빈 값)
- 기존 테스트 14개 실패는 신규 코드와 무관 (기존 이슈)
- **중기예보 API 엔드포인트 오구현**: `apis.data.go.kr` + `serviceKey`로 구현했으나, 실제는 단기와 동일한 `apihub.kma.go.kr` + `authKey`. 이미 수정 완료, `KMA_MID_API_KEY` 불필요
- **Dify Chatflow 타임아웃**: `blocking` 모드 + 10초 타임아웃으로 호출 시 지속 타임아웃. Chatflow 게시 상태 확인 및 타임아웃 상향(30초+) 필요. 상세: `report/2026-04-16-dify-chatflow-timeout.md`

---

## 📋 Next Steps

- **프론트엔드 UI**: `features/greeting/` 컴포넌트 구현 — 시군구 선택 + 날짜 선택 + 생성 버튼
- **Dify Chatflow 생성**: Dify 대시보드에서 인삿말 생성용 Chatflow 수동 생성 필요
- **할당량 연동**: UsageService 연동 — 인삿말 생성 시 할당량 차감 로직 추가
- **캐싱**: 같은 base_time/tmFc 내 중복 API 호출 방지 캐싱 레이어
- **과거 날씨**: 과거 일자 실제 날씨 조회 (별도 API 필요)
- **.env 실제 값 설정**: `KMA_API_KEY`, `KMA_MID_API_KEY`, `DIFY_GREETING_API_KEY` 실제 키 입력 필요

---

## 🏷️ Key Files

| 파일 | 역할 |
|------|------|
| `nuri-gpt-backend/app/services/weather.py` | 기상청 단기/중기예보 조회 + 파싱 |
| `nuri-gpt-backend/app/services/greeting.py` | 인삿말 생성 (날씨+날짜+절기→Dify) |
| `nuri-gpt-backend/app/data/region_grid_map.json` | 270개 시군구 좌표/regId 매핑 |
| `nuri-gpt-backend/app/api/endpoints/greeting.py` | POST /api/greeting/generate 엔드포인트 |
| `nuri-gpt-backend/app/schemas/greeting.py` | GreetingRequest/GreetingResponse 스키마 |
| `nuri-gpt-backend/app/core/config.py:42-50` | KMA/Dify Greeting 환경변수 설정 |
| `nuri-gpt-backend/scripts/generate_region_map.py` | CSV→JSON 변환 스크립트 |
| `nuri-gpt-backend/tests/test_weather_service.py` | WeatherService 단위 테스트 (17개) |
| `nuri-gpt-backend/tests/test_greeting_service.py` | GreetingService 단위 테스트 (10개) |

---

## 📐 Architecture Summary

```
Frontend → POST /api/greeting/generate { region, target_date }
  → GreetingService.generate_greeting()
    → WeatherService.get_weather_summary()
      - Δ 0~3일: 단기예보 (getVilageFcst)
      - Δ 4~10일: 중기예보 (getMidLandFcst + getMidTa)
      - Δ >10일: 빈 문자열
    → _build_date_context() → 날짜/요일/주차
    → _build_seasonal_context() → 절기/기념일
    → Dify Chatflow (inputs에 모든 맥락 주입)
  → Frontend: 인삿말 텍스트 표시
```
