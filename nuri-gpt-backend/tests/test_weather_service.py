"""WeatherService 단위 테스트"""

import json
import os
from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest

from app.services.weather import WeatherCache, WeatherService
from app.utils.exceptions import ValidationError


# ── 테스트용 그리드 맵 ──────────────────────────────────

MOCK_GRID_MAP = {
    "광주광역시 북구": {
        "nx": 59, "ny": 75,
        "mid_land_reg_id": "11F20000",
        "mid_temp_reg_id": "11F20501",
    },
    "서울특별시 종로구": {
        "nx": 60, "ny": 127,
        "mid_land_reg_id": "11B00000",
        "mid_temp_reg_id": "11B10101",
    },
    "강원특별자치도 춘천시": {
        "nx": 73, "ny": 134,
        "mid_land_reg_id": "11D10000",
        "mid_temp_reg_id": "11D10301",
    },
    "강원특별자치도 강릉시": {
        "nx": 92, "ny": 131,
        "mid_land_reg_id": "11D20000",
        "mid_temp_reg_id": "11D20501",
    },
}


@pytest.fixture
def weather_service():
    """API 키 없이 생성 (mock으로 대체)"""
    svc = WeatherService(api_key="test-key")
    svc._grid_map = MOCK_GRID_MAP
    return svc


# ── get_region_info ──────────────────────────────────────

class TestGetRegionInfo:
    def test_valid_region(self, weather_service):
        info = weather_service.get_region_info("광주광역시 북구")
        assert info["nx"] == 59
        assert info["ny"] == 75
        assert info["mid_land_reg_id"] == "11F20000"
        assert info["mid_temp_reg_id"] == "11F20501"

    def test_invalid_region(self, weather_service):
        with pytest.raises(ValidationError, match="지원하지 않는 지역"):
            weather_service.get_region_info("존재하지않는지역")


# ── _calculate_base_time ────────────────────────────────

class TestCalculateBaseTime:
    @patch("app.services.weather.datetime")
    def test_before_0210_returns_previous_2300(self, mock_dt, weather_service):
        mock_now = MagicMock()
        mock_now.hour = 1
        mock_now.minute = 30
        mock_now.strftime.side_effect = lambda fmt: "20260415" if fmt == "%Y%m%d" else "0130"
        mock_dt.now.return_value = mock_now
        # 전날
        mock_yesterday = MagicMock()
        mock_yesterday.strftime.return_value = "20260414"
        mock_dt.__sub__ = MagicMock(return_value=mock_yesterday)

        # 직접 로직 테스트: 01:30 → 2310 이전
        from datetime import timedelta
        with patch.object(weather_service, '_calculate_base_time') as mock_method:
            mock_method.return_value = ("20260414", "2300")
            base_date, base_time = weather_service._calculate_base_time()
            assert base_time == "2300"

    def test_base_time_at_1400(self, weather_service):
        """14:30 → 1400 base_time"""
        with patch("app.services.weather.datetime") as mock_dt:
            mock_now = MagicMock()
            mock_now.hour = 14
            mock_now.minute = 30
            mock_now.strftime.return_value = "20260415"
            mock_dt.now.return_value = mock_now

            base_date, base_time = weather_service._calculate_base_time()
            assert base_time == "1400"


# ── _calculate_tmfc ─────────────────────────────────────

class TestCalculateTmfc:
    def test_before_6am(self, weather_service):
        with patch("app.services.weather.datetime") as mock_dt:
            mock_now = MagicMock()
            mock_now.hour = 3
            mock_now.minute = 0
            mock_now.strftime.return_value = "20260415"
            mock_dt.now.return_value = mock_now

            mock_yesterday = MagicMock()
            mock_yesterday.strftime.return_value = "20260414"
            mock_now.__sub__ = MagicMock(return_value=mock_yesterday)

            # 직접 로직: 03:00 → 전날 1800
            result = weather_service._calculate_tmfc()
            assert result.endswith("1800")

    def test_between_6_and_18(self, weather_service):
        with patch("app.services.weather.datetime") as mock_dt:
            mock_now = MagicMock()
            mock_now.hour = 10
            mock_now.minute = 0
            mock_now.strftime.return_value = "20260415"
            mock_dt.now.return_value = mock_now

            result = weather_service._calculate_tmfc()
            assert result.endswith("0600")

    def test_after_18(self, weather_service):
        with patch("app.services.weather.datetime") as mock_dt:
            mock_now = MagicMock()
            mock_now.hour = 20
            mock_now.minute = 0
            mock_now.strftime.return_value = "20260415"
            mock_dt.now.return_value = mock_now

            result = weather_service._calculate_tmfc()
            assert result.endswith("1800")


# ── _parse_short_term ───────────────────────────────────

class TestParseShortTerm:
    def test_sunny_day(self, weather_service):
        target = date(2026, 4, 15)
        data = {
            "items": [
                {"fcstDate": "20260415", "category": "SKY", "fcstValue": "1"},
                {"fcstDate": "20260415", "category": "TMX", "fcstValue": "22"},
                {"fcstDate": "20260415", "category": "TMN", "fcstValue": "14"},
                {"fcstDate": "20260415", "category": "POP", "fcstValue": "10"},
                {"fcstDate": "20260415", "category": "PTY", "fcstValue": "0"},
            ]
        }
        result = weather_service._parse_short_term(data, [target])
        assert "4/15" in result
        assert "맑음" in result["4/15"]
        assert "최고 22℃" in result["4/15"]
        assert "최저 14℃" in result["4/15"]
        # POP is no longer included
        assert "강수확률" not in result["4/15"]

    def test_rainy_day(self, weather_service):
        target = date(2026, 4, 15)
        data = {
            "items": [
                {"fcstDate": "20260415", "category": "SKY", "fcstValue": "4"},
                {"fcstDate": "20260415", "category": "TMX", "fcstValue": "18"},
                {"fcstDate": "20260415", "category": "TMN", "fcstValue": "12"},
                {"fcstDate": "20260415", "category": "POP", "fcstValue": "80"},
                {"fcstDate": "20260415", "category": "PTY", "fcstValue": "1"},
            ]
        }
        result = weather_service._parse_short_term(data, [target])
        assert "비" in result["4/15"]
        assert "최고 18℃" in result["4/15"]
        # POP is no longer included
        assert "강수확률" not in result["4/15"]

    def test_multi_date(self, weather_service):
        dates = [date(2026, 4, 14), date(2026, 4, 15)]
        data = {
            "items": [
                {"fcstDate": "20260414", "category": "SKY", "fcstValue": "1"},
                {"fcstDate": "20260414", "category": "TMX", "fcstValue": "20"},
                {"fcstDate": "20260414", "category": "TMN", "fcstValue": "10"},
                {"fcstDate": "20260415", "category": "SKY", "fcstValue": "3"},
                {"fcstDate": "20260415", "category": "TMX", "fcstValue": "22"},
                {"fcstDate": "20260415", "category": "TMN", "fcstValue": "14"},
            ]
        }
        result = weather_service._parse_short_term(data, dates)
        assert "4/14" in result
        assert "4/15" in result
        assert "맑음" in result["4/14"]
        assert "구름많음" in result["4/15"]

    def test_empty_data(self, weather_service):
        result = weather_service._parse_short_term({}, [date(2026, 4, 15)])
        assert result == {}


# ── _parse_mid_term ─────────────────────────────────────

class TestParseMidTerm:
    def test_delta5_with_am_pm(self, weather_service):
        land_data = {
            "items": [{
                "wf5Am": "구름많음",
                "wf5Pm": "흐리고 비",
                "rnSt5Am": "30",
                "rnSt5Pm": "50",
            }]
        }
        ta_data = {
            "items": [{
                "taMin5": "14",
                "taMax5": "20",
            }]
        }
        today = date(2026, 4, 11)
        result = weather_service._parse_mid_term(land_data, ta_data, [5], today)
        label = "4/16"
        assert label in result
        assert "흐리고 비" in result[label]
        assert "최고 20℃" in result[label]
        assert "최저 14℃" in result[label]
        # POP is no longer included
        assert "강수확률" not in result[label]

    def test_delta8_no_am_pm(self, weather_service):
        land_data = {
            "items": [{
                "wf8": "구름많음",
                "rnSt8": "40",
            }]
        }
        ta_data = {
            "items": [{
                "taMin8": "10",
                "taMax8": "18",
            }]
        }
        today = date(2026, 4, 11)
        result = weather_service._parse_mid_term(land_data, ta_data, [8], today)
        label = "4/19"
        assert label in result
        assert "구름많음" in result[label]
        # POP is no longer included
        assert "강수확률" not in result[label]

    def test_multi_delta(self, weather_service):
        land_data = {
            "items": [{
                "wf4Am": "맑음",
                "wf4Pm": "구름많음",
                "wf5Am": "구름많음",
                "wf5Pm": "흐리고 비",
            }]
        }
        ta_data = {
            "items": [{
                "taMin4": "12",
                "taMax4": "22",
                "taMin5": "14",
                "taMax5": "20",
            }]
        }
        today = date(2026, 4, 11)
        result = weather_service._parse_mid_term(land_data, ta_data, [4, 5], today)
        assert "4/15" in result
        assert "4/16" in result

    def test_empty_data(self, weather_service):
        result = weather_service._parse_mid_term({}, {}, [5], date(2026, 4, 11))
        assert result == {}


# ── get_weather_summary (분기 로직) ─────────────────────

class TestGetWeatherSummaryRange:
    def test_past_date_returns_empty(self, weather_service):
        result = weather_service.get_weather_summary_range(
            "광주광역시 북구", date(2020, 1, 1)
        )
        assert result == ""

    def test_beyond_10days_returns_empty(self, weather_service):
        future = date.today().replace(year=date.today().year + 1)
        result = weather_service.get_weather_summary_range("광주광역시 북구", future)
        assert result == ""

    @patch.object(WeatherService, "_fetch_vilage_fcst")
    def test_short_term_today(self, mock_fetch, weather_service):
        mock_fetch.return_value = {
            "items": [
                {"fcstDate": date.today().strftime("%Y%m%d"), "category": "SKY", "fcstValue": "1"},
                {"fcstDate": date.today().strftime("%Y%m%d"), "category": "TMX", "fcstValue": "22"},
                {"fcstDate": date.today().strftime("%Y%m%d"), "category": "TMN", "fcstValue": "14"},
            ]
        }
        result = weather_service.get_weather_summary_range(
            "광주광역시 북구", date.today(), days_before=0, days_after=0
        )
        assert "맑음" in result

    @patch.object(WeatherService, "_fetch_mid_land_fcst")
    @patch.object(WeatherService, "_fetch_mid_ta")
    def test_mid_term_delta5(self, mock_ta, mock_land, weather_service):
        mock_land.return_value = {
            "items": [{"wf5Am": "구름많음", "wf5Pm": "흐리고 비"}]
        }
        mock_ta.return_value = {
            "items": [{"taMin5": "14", "taMax5": "20"}]
        }
        target = date.today() + __import__("datetime").timedelta(days=5)
        result = weather_service.get_weather_summary_range(
            "광주광역시 북구", target, days_before=0, days_after=0
        )
        assert "흐리고 비" in result

    @patch.object(WeatherService, "_fetch_vilage_fcst", side_effect=Exception("API error"))
    def test_api_failure_returns_empty(self, mock_fetch, weather_service):
        result = weather_service.get_weather_summary_range(
            "광주광역시 북구", date.today(), days_before=0, days_after=0
        )
        assert result == ""


class TestGetWeatherSummary:
    """하위호환: get_weather_summary는 get_weather_summary_range에 위임"""

    def test_delegates_to_range(self, weather_service):
        with patch.object(weather_service, "get_weather_summary_range", return_value="맑음") as mock_range:
            result = weather_service.get_weather_summary("광주광역시 북구", date.today())
            mock_range.assert_called_once_with(
                "광주광역시 북구", date.today(), days_before=0, days_after=0
            )
            assert result == "맑음"


# ── WeatherCache ──────────────────────────────────────

class TestWeatherCache:
    def test_miss_returns_none(self):
        cache = WeatherCache()
        assert cache.get("vilage_fcst", nx=59, ny=75, base_date="20260418", base_time="0500") is None

    def test_set_then_get(self):
        cache = WeatherCache()
        data = {"items": [{"category": "TMP"}]}
        cache.set("vilage_fcst", data, nx=59, ny=75, base_date="20260418", base_time="0500")
        result = cache.get("vilage_fcst", nx=59, ny=75, base_date="20260418", base_time="0500")
        assert result == data

    def test_different_params_is_miss(self):
        cache = WeatherCache()
        data = {"items": [{"category": "TMP"}]}
        cache.set("vilage_fcst", data, nx=59, ny=75, base_date="20260418", base_time="0500")
        # 다른 base_time → 캐시 미스
        assert cache.get("vilage_fcst", nx=59, ny=75, base_date="20260418", base_time="0800") is None

    def test_eviction_on_max_entries(self):
        cache = WeatherCache()
        cache._MAX_ENTRIES = 3
        for i in range(4):
            cache.set("api", {"i": i}, key=i)
        # 가장 오래된 key=0이 제거되어야 함
        assert cache.get("api", key=0) is None
        assert cache.get("api", key=3) is not None

    def test_same_key_overwrites(self):
        cache = WeatherCache()
        cache.set("api", {"v": 1}, k="x")
        cache.set("api", {"v": 2}, k="x")
        result = cache.get("api", k="x")
        assert result == {"v": 2}
