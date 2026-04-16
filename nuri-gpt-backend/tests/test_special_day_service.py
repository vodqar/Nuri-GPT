"""SpecialDayService 단위 테스트"""

from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.services.special_day import (
    SpecialDayCache,
    SpecialDayService,
    YearData,
    _CURRENT_MONTH_TTL,
    _FUTURE_MONTH_TTL,
    _GRACE_PERIOD,
)


# ── 테스트용 픽스처 ──────────────────────────────────────


def _make_year_data(
    holidays=None,
    solar_terms=None,
    anniversaries=None,
    sundry_days=None,
    fetched_at=None,
):
    return YearData(
        holidays=holidays or [],
        solar_terms=solar_terms or [],
        anniversaries=anniversaries or [],
        sundry_days=sundry_days or [],
        fetched_at=fetched_at or datetime.now(),
    )


def _make_api_item(locdate, date_name, date_kind="01", is_holiday="Y"):
    return {
        "locdate": locdate,
        "dateName": date_name,
        "dateKind": date_kind,
        "isHoliday": is_holiday,
    }


@pytest.fixture
def cache():
    return SpecialDayCache()


@pytest.fixture
def special_day_service():
    """API 키 설정된 서비스 (API 호출은 mock으로 대체)"""
    return SpecialDayService(api_key="test-special-day-key")


# ── SpecialDayCache TTL 판정 ──────────────────────────────


class TestSpecialDayCache:
    def test_cache_miss_returns_true(self, cache):
        assert cache.is_expired(2026, datetime(2026, 4, 15)) is True

    def test_current_year_within_ttl(self, cache):
        now = datetime(2026, 4, 15, 12, 0)
        data = _make_year_data(fetched_at=now)
        cache.set(2026, data)

        check_time = now + timedelta(hours=6)
        assert cache.is_expired(2026, check_time) is False

    def test_current_year_expired(self, cache):
        now = datetime(2026, 4, 15, 12, 0)
        data = _make_year_data(fetched_at=now)
        cache.set(2026, data)

        # TTL + grace period 모두 초과해야 expired
        check_time = now + _CURRENT_MONTH_TTL + _GRACE_PERIOD + timedelta(seconds=1)
        assert cache.is_expired(2026, check_time) is True

    def test_current_year_within_grace_period(self, cache):
        now = datetime(2026, 4, 15, 12, 0)
        data = _make_year_data(fetched_at=now)
        cache.set(2026, data)

        # TTL 만료 + grace period 이내
        check_time = now + _CURRENT_MONTH_TTL + timedelta(hours=1)
        assert cache.is_expired(2026, check_time) is False

    def test_current_year_past_grace_period(self, cache):
        now = datetime(2026, 4, 15, 12, 0)
        data = _make_year_data(fetched_at=now)
        cache.set(2026, data)

        # TTL 만료 + grace period 초과
        check_time = now + _CURRENT_MONTH_TTL + _GRACE_PERIOD + timedelta(seconds=1)
        assert cache.is_expired(2026, check_time) is True

    def test_future_year_within_ttl(self, cache):
        now = datetime(2026, 4, 15)
        data = _make_year_data(fetched_at=now)
        cache.set(2027, data)

        check_time = now + timedelta(days=5)
        assert cache.is_expired(2027, check_time) is False

    def test_future_year_expired(self, cache):
        now = datetime(2026, 4, 15)
        data = _make_year_data(fetched_at=now)
        cache.set(2027, data)

        # TTL + grace period 모두 초과해야 expired
        check_time = now + _FUTURE_MONTH_TTL + _GRACE_PERIOD + timedelta(seconds=1)
        assert cache.is_expired(2027, check_time) is True

    def test_get_set_roundtrip(self, cache):
        data = _make_year_data(holidays=[{"test": True}])
        cache.set(2026, data)
        result = cache.get(2026)
        assert result is data
        assert result.holidays == [{"test": True}]

    def test_get_missing_year(self, cache):
        assert cache.get(9999) is None


# ── SpecialDayService API 호출 ────────────────────────────


class TestFetchOperation:
    @patch("app.services.special_day.requests.get")
    def test_fetch_holidays(self, mock_get, special_day_service):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "response": {
                "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE"},
                "body": {
                    "items": {
                        "item": [
                            _make_api_item(20260505, "어린이날", "01", "Y"),
                            _make_api_item(20260505, "대체공휴일", "01", "Y"),
                        ]
                    },
                    "numOfRows": 2,
                    "totalCount": 2,
                },
            }
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        items = special_day_service._fetch_operation("getRestDeInfo", 2026)
        assert len(items) == 2
        assert items[0]["dateName"] == "어린이날"

    @patch("app.services.special_day.requests.get")
    def test_fetch_single_item_returns_list(self, mock_get, special_day_service):
        """단일 item 시 dict로 오는 케이스"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "response": {
                "header": {"resultCode": "00"},
                "body": {
                    "items": {
                        "item": _make_api_item(20260301, "삼일절")
                    },
                    "totalCount": 1,
                },
            }
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        items = special_day_service._fetch_operation("getRestDeInfo", 2026)
        assert isinstance(items, list)
        assert len(items) == 1

    @patch("app.services.special_day.requests.get")
    def test_fetch_api_error_returns_empty(self, mock_get, special_day_service):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "response": {
                "header": {"resultCode": "99", "resultMsg": "ERROR"},
                "body": {"items": {}},
            }
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        items = special_day_service._fetch_operation("getRestDeInfo", 2026)
        assert items == []

    @patch("app.services.special_day.requests.get")
    def test_fetch_network_error_returns_empty(self, mock_get, special_day_service):
        mock_get.side_effect = Exception("Network error")
        items = special_day_service._fetch_operation("getRestDeInfo", 2026)
        assert items == []

    @patch("app.services.special_day.get_settings")
    def test_fetch_no_api_key_returns_empty(self, mock_settings):
        mock_settings.return_value = MagicMock(kma_special_day_api_key=None)
        svc = SpecialDayService(api_key=None)
        items = svc._fetch_operation("getRestDeInfo", 2026)
        assert items == []


# ── SpecialDayService 공개 메서드 ──────────────────────────


class TestGetHoliday:
    def test_holiday_found(self, special_day_service):
        data = _make_year_data(
            holidays=[
                _make_api_item(20260505, "어린이날", "01", "Y"),
            ]
        )
        special_day_service._cache.set(2026, data)

        result = special_day_service.get_holiday(date(2026, 5, 5))
        assert result == "어린이날"

    def test_multiple_holidays_same_date(self, special_day_service):
        data = _make_year_data(
            holidays=[
                _make_api_item(20260101, "신정", "01", "Y"),
                _make_api_item(20260101, "임시공휴일", "01", "Y"),
            ]
        )
        special_day_service._cache.set(2026, data)

        result = special_day_service.get_holiday(date(2026, 1, 1))
        assert "신정" in result
        assert "임시공휴일" in result

    def test_no_holiday(self, special_day_service):
        data = _make_year_data(holidays=[])
        special_day_service._cache.set(2026, data)

        result = special_day_service.get_holiday(date(2026, 4, 14))
        assert result == "해당 없음"

    def test_no_cache(self, special_day_service):
        result = special_day_service.get_holiday(date(2026, 4, 14))
        assert result == "해당 없음"


class TestGetSolarTermRange:
    def test_solar_term_range(self, special_day_service):
        data = _make_year_data(
            solar_terms=[
                _make_api_item(20260405, "청명", "03", "N"),
                _make_api_item(20260420, "곡우", "03", "N"),
                _make_api_item(20260506, "입하", "03", "N"),
            ]
        )
        special_day_service._cache.set(2026, data)

        result = special_day_service.get_solar_term_range(date(2026, 4, 14))
        assert "청명" in result
        assert "곡우" in result

    def test_solar_term_on_exact_date(self, special_day_service):
        data = _make_year_data(
            solar_terms=[
                _make_api_item(20260405, "청명", "03", "N"),
                _make_api_item(20260420, "곡우", "03", "N"),
                _make_api_item(20260506, "입하", "03", "N"),
            ]
        )
        special_day_service._cache.set(2026, data)

        result = special_day_service.get_solar_term_range(date(2026, 4, 20))
        assert "곡우" in result

    def test_no_solar_terms(self, special_day_service):
        data = _make_year_data(solar_terms=[])
        special_day_service._cache.set(2026, data)

        result = special_day_service.get_solar_term_range(date(2026, 4, 14))
        assert result == ""

    def test_no_cache(self, special_day_service):
        result = special_day_service.get_solar_term_range(date(2026, 4, 14))
        assert result == ""

    def test_year_boundary_prev_term(self, special_day_service):
        """1월 초 → 전년 동지를 이전 절기로 사용"""
        data_2026 = _make_year_data(
            solar_terms=[
                _make_api_item(20260106, "소한", "03", "N"),
                _make_api_item(20260120, "대한", "03", "N"),
            ]
        )
        data_2025 = _make_year_data(
            solar_terms=[
                _make_api_item(20251222, "동지", "03", "N"),
            ]
        )
        special_day_service._cache.set(2026, data_2026)
        special_day_service._cache.set(2025, data_2025)

        result = special_day_service.get_solar_term_range(date(2026, 1, 3))
        assert "동지" in result


class TestGetAnniversary:
    def test_anniversary_found(self, special_day_service):
        data = _make_year_data(
            anniversaries=[
                _make_api_item(20260515, "스승의날", "02", "N"),
            ]
        )
        special_day_service._cache.set(2026, data)

        result = special_day_service.get_anniversary(date(2026, 5, 15))
        assert result == "스승의날"

    def test_no_anniversary(self, special_day_service):
        data = _make_year_data(anniversaries=[])
        special_day_service._cache.set(2026, data)

        result = special_day_service.get_anniversary(date(2026, 4, 14))
        assert result == "해당 없음"


class TestGetSundryDay:
    def test_sundry_day_found(self, special_day_service):
        data = _make_year_data(
            sundry_days=[
                _make_api_item(20260610, "단오", "04", "N"),
            ]
        )
        special_day_service._cache.set(2026, data)

        result = special_day_service.get_sundry_day(date(2026, 6, 10))
        assert result == "단오"

    def test_no_sundry_day(self, special_day_service):
        data = _make_year_data(sundry_days=[])
        special_day_service._cache.set(2026, data)

        result = special_day_service.get_sundry_day(date(2026, 4, 14))
        assert result == "해당 없음"


# ── 캐시 갱신 로직 ────────────────────────────────────────


class TestEnsureCache:
    @patch.object(SpecialDayService, "_fetch_year")
    def test_cache_miss_triggers_fetch(self, mock_fetch, special_day_service):
        mock_fetch.return_value = _make_year_data(
            holidays=[_make_api_item(20260505, "어린이날")]
        )

        result = special_day_service._ensure_cache(2026)
        assert result is not None
        mock_fetch.assert_called_once_with(2026)

    @patch.object(SpecialDayService, "_fetch_year")
    def test_cache_hit_no_fetch(self, mock_fetch, special_day_service):
        data = _make_year_data(holidays=[_make_api_item(20260505, "어린이날")])
        special_day_service._cache.set(2026, data)

        result = special_day_service._ensure_cache(2026)
        assert result is data
        mock_fetch.assert_not_called()

    @patch.object(SpecialDayService, "_fetch_year")
    def test_api_failure_returns_stale_cache(self, mock_fetch, special_day_service):
        now = datetime.now()
        stale_data = _make_year_data(
            holidays=[_make_api_item(20260505, "어린이날")],
            fetched_at=now - _CURRENT_MONTH_TTL - timedelta(hours=1),
        )
        special_day_service._cache.set(2026, stale_data)

        # 빈 결과 반환 (API 실패 시뮬레이션)
        mock_fetch.return_value = _make_year_data()

        result = special_day_service._ensure_cache(2026)
        assert result is stale_data


class TestRefresh:
    @patch.object(SpecialDayService, "_fetch_year")
    def test_refresh_forces_update(self, mock_fetch, special_day_service):
        new_data = _make_year_data(
            holidays=[_make_api_item(20260505, "어린이날")]
        )
        mock_fetch.return_value = new_data

        result = special_day_service.refresh(2026)
        assert result is new_data
        mock_fetch.assert_called_once_with(2026)
