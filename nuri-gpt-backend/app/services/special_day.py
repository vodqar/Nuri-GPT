"""한국천문연구원 특일 정보 API 클라이언트

공휴일, 24절기, 기념일, 잡절을 조회하고 차등 TTL 캐시로 관리한다.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional
from urllib.parse import unquote

import requests

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# ── 캐시 TTL 설정 ──
_CURRENT_MONTH_TTL = timedelta(hours=12)
_FUTURE_MONTH_TTL = timedelta(days=7)
_GRACE_PERIOD = timedelta(hours=24)

# ── API 기본 URL ──
_BASE_URL = "http://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService"

# ── 오퍼레이션명 ──
_OP_HOLIDAYS = "getRestDeInfo"
_OP_SOLAR_TERMS = "get24DivisionsInfo"
_OP_ANNIVERSARIES = "getAnniversaryInfo"
_OP_SUNDRY_DAYS = "getSundryDayInfo"


class YearData:
    """연 단위 특일 데이터"""

    __slots__ = ("holidays", "solar_terms", "anniversaries", "sundry_days", "fetched_at")

    def __init__(
        self,
        holidays: List[Dict],
        solar_terms: List[Dict],
        anniversaries: List[Dict],
        sundry_days: List[Dict],
        fetched_at: datetime,
    ):
        self.holidays = holidays
        self.solar_terms = solar_terms
        self.anniversaries = anniversaries
        self.sundry_days = sundry_days
        self.fetched_at = fetched_at


class SpecialDayCache:
    """연 단위 특일 데이터 캐시 (차등 TTL)

    - 당월 데이터: 12시간 TTL → 임시공휴일 12시간 내 반영
    - 미래월 데이터: 7일 TTL
    - API 실패 시 grace period (만료 후 24시간까지 기존 캐시 사용)

    백그라운드 스케줄러 전환 시 refresh() 메서드만 주기적 호출하면 됨.
    """

    def __init__(self) -> None:
        self._store: Dict[int, YearData] = {}

    def is_expired(self, year: int, now: datetime) -> bool:
        """캐시 만료 여부 판정"""
        data = self._store.get(year)
        if data is None:
            return True

        current_month = now.month
        ttl = _CURRENT_MONTH_TTL if current_month == date(year, 1, 1).month else _FUTURE_MONTH_TTL

        # fetched_at이 속한 연도의 당월인지 확인
        # year가 현재 연도이고, 데이터가 이번 달에 해당하면 당월 TTL
        if year == now.year:
            ttl = _CURRENT_MONTH_TTL
        else:
            ttl = _FUTURE_MONTH_TTL

        elapsed = now - data.fetched_at
        if elapsed <= ttl:
            return False

        # grace period: 만료 후 24시간까지는 캐시 유지 (API 실패 대비)
        if elapsed <= ttl + _GRACE_PERIOD:
            logger.info(
                "Special day cache expired but within grace period | year=%s elapsed=%.1fh",
                year,
                elapsed.total_seconds() / 3600,
            )
            return False

        return True

    def get(self, year: int) -> Optional[YearData]:
        return self._store.get(year)

    def set(self, year: int, data: YearData) -> None:
        self._store[year] = data


class SpecialDayService:
    """한국천문연구원 특일 정보 API 클라이언트

    공개 메서드:
    - get_holiday(target_date) → 공휴일명 or "해당 없음"
    - get_solar_term_range(target_date) → 절기 구간 문자열
    - get_anniversary(target_date) → 기념일명 or "해당 없음"
    - get_sundry_day(target_date) → 잡절명 or "해당 없음"
    - refresh(year) → 캐시 강제 갱신 (백그라운드 스케줄러용)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache: Optional[SpecialDayCache] = None,
    ):
        settings = get_settings()
        raw_key = api_key or settings.kma_special_day_api_key
        self._api_key = unquote(raw_key) if raw_key else None
        self._cache = cache or SpecialDayCache()

    # ── API 호출 ──────────────────────────────────────────

    def _fetch_operation(self, operation: str, year: int) -> List[Dict]:
        """단일 오퍼레이션 연 단위 조회 → item 리스트 반환"""
        if not self._api_key:
            logger.warning("KMA_SPECIAL_DAY_API_KEY not set, skipping %s", operation)
            return []

        params = {
            "ServiceKey": self._api_key,
            "solYear": str(year),
            "_type": "json",
            "numOfRows": "200",
        }

        url = f"{_BASE_URL}/{operation}"

        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            header = data.get("response", {}).get("header", {})
            if header.get("resultCode") != "00":
                logger.error(
                    "Special day API error | op=%s code=%s msg=%s",
                    operation,
                    header.get("resultCode"),
                    header.get("resultMsg"),
                )
                return []

            items = (
                data.get("response", {})
                .get("body", {})
                .get("items", {})
                .get("item", [])
            )
            # 단일 item 시 dict로 오는 케이스 처리
            if isinstance(items, dict):
                items = [items]

            logger.info(
                "Special day API fetched | op=%s year=%s count=%s",
                operation,
                year,
                len(items),
            )
            return items

        except Exception as e:
            logger.error("Failed to fetch special day API | op=%s error=%s", operation, e)
            return []

    def _fetch_year(self, year: int) -> YearData:
        """4개 오퍼레이션 모두 조회하여 YearData 생성"""
        now = datetime.now()
        return YearData(
            holidays=self._fetch_operation(_OP_HOLIDAYS, year),
            solar_terms=self._fetch_operation(_OP_SOLAR_TERMS, year),
            anniversaries=self._fetch_operation(_OP_ANNIVERSARIES, year),
            sundry_days=self._fetch_operation(_OP_SUNDRY_DAYS, year),
            fetched_at=now,
        )

    # ── 캐시 관리 ─────────────────────────────────────────

    def _ensure_cache(self, year: int) -> Optional[YearData]:
        """캐시 조회, 만료 시 갱신"""
        now = datetime.now()
        data = self._cache.get(year)

        if data is not None and not self._cache.is_expired(year, now):
            return data

        # 갱신 시도
        new_data = self._fetch_year(year)
        if any([new_data.holidays, new_data.solar_terms, new_data.anniversaries, new_data.sundry_days]):
            self._cache.set(year, new_data)
            return new_data

        # API 실패 → 기존 캐시라도 반환
        if data is not None:
            logger.warning("Special day API failed, using stale cache for year=%s", year)
            return data

        return None

    def refresh(self, year: int) -> YearData:
        """캐시 강제 갱신 (백그라운드 스케줄러 전환 시 이 메서드만 호출)"""
        data = self._fetch_year(year)
        self._cache.set(year, data)
        return data

    # ── 공개 조회 메서드 ──────────────────────────────────

    def _find_by_date(self, items: List[Dict], target_date: date) -> List[Dict]:
        """locdate가 target_date와 일치하는 item 필터링"""
        target_str = target_date.strftime("%Y%m%d")
        return [item for item in items if str(item.get("locdate", "")) == target_str]

    def get_holiday(self, target_date: date) -> str:
        """공휴일 조회 → 공휴일명 or '해당 없음'"""
        data = self._ensure_cache(target_date.year)
        if data is None:
            return "해당 없음"

        matches = self._find_by_date(data.holidays, target_date)
        if not matches:
            return "해당 없음"

        # 여러 공휴일이 같은 날 있을 수 있음 (예: 설날 + 대체공휴일)
        names = [m.get("dateName", "") for m in matches if m.get("dateName")]
        return ", ".join(names) if names else "해당 없음"

    def get_solar_term_range(self, target_date: date) -> str:
        """24절기 구간 조회 → '곡우(4월 20일) ~ 소만(5월 21일)' 형식"""
        year = target_date.year
        data = self._ensure_cache(year)
        if data is None or not data.solar_terms:
            return ""

        # 절기 날짜 파싱 후 정렬
        terms = []
        for item in data.solar_terms:
            locdate_str = str(item.get("locdate", ""))
            name = item.get("dateName", "")
            if len(locdate_str) == 8 and name:
                try:
                    term_date = date(
                        int(locdate_str[:4]),
                        int(locdate_str[4:6]),
                        int(locdate_str[6:8]),
                    )
                    terms.append((term_date, name))
                except ValueError:
                    continue

        if not terms:
            return ""

        terms.sort(key=lambda x: x[0])

        # 이전/다음 절기 찾기
        prev_term = None
        next_term = None

        for term_date, name in terms:
            if term_date <= target_date:
                prev_term = (term_date, name)
            if term_date > target_date and next_term is None:
                next_term = (term_date, name)

        # 연도 경계 처리
        if prev_term is None:
            # 전년 데이터로 동지 찾기
            prev_data = self._ensure_cache(year - 1)
            if prev_data and prev_data.solar_terms:
                for item in prev_data.solar_terms:
                    if item.get("dateName") == "동지":
                        locdate_str = str(item.get("locdate", ""))
                        if len(locdate_str) == 8:
                            try:
                                prev_term = (
                                    date(
                                        int(locdate_str[:4]),
                                        int(locdate_str[4:6]),
                                        int(locdate_str[6:8]),
                                    ),
                                    "동지",
                                )
                            except ValueError:
                                pass
                        break
            if prev_term is None:
                prev_term = (date(year - 1, 12, 22), "동지")

        if next_term is None:
            # 다음 해 데이터로 소한 찾기
            next_data = self._ensure_cache(year + 1)
            if next_data and next_data.solar_terms:
                for item in next_data.solar_terms:
                    if item.get("dateName") == "소한":
                        locdate_str = str(item.get("locdate", ""))
                        if len(locdate_str) == 8:
                            try:
                                next_term = (
                                    date(
                                        int(locdate_str[:4]),
                                        int(locdate_str[4:6]),
                                        int(locdate_str[6:8]),
                                    ),
                                    "소한",
                                )
                            except ValueError:
                                pass
                        break
            if next_term is None:
                next_term = (date(year + 1, 1, 6), "소한")

        return (
            f"{prev_term[1]}({prev_term[0].month}월 {prev_term[0].day}일)"
            f" ~ {next_term[1]}({next_term[0].month}월 {next_term[0].day}일)"
        )

    def get_anniversary(self, target_date: date) -> str:
        """기념일 조회 → 기념일명 or '해당 없음'"""
        data = self._ensure_cache(target_date.year)
        if data is None:
            return "해당 없음"

        matches = self._find_by_date(data.anniversaries, target_date)
        if not matches:
            return "해당 없음"

        names = [m.get("dateName", "") for m in matches if m.get("dateName")]
        return ", ".join(names) if names else "해당 없음"

    def get_sundry_day(self, target_date: date) -> str:
        """잡절 조회 → 잡절명 or '해당 없음'"""
        data = self._ensure_cache(target_date.year)
        if data is None:
            return "해당 없음"

        matches = self._find_by_date(data.sundry_days, target_date)
        if not matches:
            return "해당 없음"

        names = [m.get("dateName", "") for m in matches if m.get("dateName")]
        return ", ".join(names) if names else "해당 없음"
