"""GreetingService 단위 테스트"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app.services.greeting import GreetingService


@pytest.fixture
def mock_weather_service():
    return MagicMock()


@pytest.fixture
def mock_special_day_service():
    svc = MagicMock()
    svc.get_holiday.return_value = "해당 없음"
    svc.get_solar_term_range.return_value = "청명(4월 5일) ~ 곡우(4월 20일)"
    svc.get_anniversary.return_value = "해당 없음"
    svc.get_sundry_day.return_value = "해당 없음"
    return svc


@pytest.fixture
def greeting_service(mock_weather_service):
    return GreetingService(weather_service=mock_weather_service)


@pytest.fixture
def greeting_service_with_api(mock_weather_service, mock_special_day_service):
    return GreetingService(
        weather_service=mock_weather_service,
        special_day_service=mock_special_day_service,
    )


class TestExtractAnswerText:
    def test_streaming_response(self, greeting_service):
        response = MagicMock()
        response.headers = {"Content-Type": "text/event-stream; charset=utf-8"}
        response.iter_lines.return_value = [
            'data: {"event":"message","answer":"안녕하세요"}',
            'data: {"event":"message","answer":"! 반갑습니다."}',
        ]

        result = greeting_service._extract_answer_text(response)

        assert result == "안녕하세요! 반갑습니다."

    def test_blocking_response(self, greeting_service):
        response = MagicMock()
        response.headers = {"Content-Type": "application/json"}
        response.json.return_value = {"answer": "따뜻한 하루 보내세요."}

        result = greeting_service._extract_answer_text(response)

        assert result == "따뜻한 하루 보내세요."


# ── _build_date_context ─────────────────────────────────

class TestBuildDateContext:
    def test_monday(self, greeting_service):
        # 2026-04-20은 월요일
        ctx = greeting_service._build_date_context(date(2026, 4, 20))
        assert "2026년 4월 20일" in ctx["date_info"]
        assert "월요일" in ctx["date_info"]
        assert "4월" in ctx["month_week"]

    def test_sunday(self, greeting_service):
        ctx = greeting_service._build_date_context(date(2026, 5, 3))
        assert "일요일" in ctx["date_info"]


# ── _build_seasonal_context ─────────────────────────────

class TestBuildSeasonalContext:
    def test_no_holiday(self, greeting_service):
        # 4월 14일은 법정기념일 아님
        ctx = greeting_service._build_seasonal_context(date(2026, 4, 14))
        assert ctx["holiday_info"] == "해당 없음"
        assert "청명" in ctx["seasonal_info"]
        assert ctx["anniversary_info"] == "해당 없음"
        assert ctx["sundry_day_info"] == "해당 없음"

    def test_with_holiday(self, greeting_service):
        # 5월 5일은 어린이날
        ctx = greeting_service._build_seasonal_context(date(2026, 5, 5))
        assert ctx["holiday_info"] == "어린이날"

    def test_childrens_day(self, greeting_service):
        ctx = greeting_service._build_seasonal_context(date(2026, 5, 5))
        assert ctx["holiday_info"] == "어린이날"

    def test_solar_term_range(self, greeting_service):
        # 4월 20일은 곡우 당일
        ctx = greeting_service._build_seasonal_context(date(2026, 4, 20))
        assert "곡우" in ctx["seasonal_info"]


class TestBuildSeasonalContextWithApi:
    """SpecialDayService 주입 시 API 기반 경로 테스트"""

    def test_uses_special_day_service(self, greeting_service_with_api, mock_special_day_service):
        ctx = greeting_service_with_api._build_seasonal_context(date(2026, 4, 14))
        mock_special_day_service.get_holiday.assert_called_once_with(date(2026, 4, 14))
        mock_special_day_service.get_solar_term_range.assert_called_once_with(date(2026, 4, 14))
        mock_special_day_service.get_anniversary.assert_called_once_with(date(2026, 4, 14))
        mock_special_day_service.get_sundry_day.assert_called_once_with(date(2026, 4, 14))

    def test_api_holiday_result(self, greeting_service_with_api, mock_special_day_service):
        mock_special_day_service.get_holiday.return_value = "어린이날"
        ctx = greeting_service_with_api._build_seasonal_context(date(2026, 5, 5))
        assert ctx["holiday_info"] == "어린이날"

    def test_api_anniversary_result(self, greeting_service_with_api, mock_special_day_service):
        mock_special_day_service.get_anniversary.return_value = "스승의날"
        ctx = greeting_service_with_api._build_seasonal_context(date(2026, 5, 15))
        assert ctx["anniversary_info"] == "스승의날"

    def test_api_sundry_day_result(self, greeting_service_with_api, mock_special_day_service):
        mock_special_day_service.get_sundry_day.return_value = "단오"
        ctx = greeting_service_with_api._build_seasonal_context(date(2026, 6, 10))
        assert ctx["sundry_day_info"] == "단오"


# ── generate_greeting (전체 흐름) ──────────────────────

class TestGenerateGreeting:
    @patch.object(GreetingService, "_call_dify", return_value="안녕하세요! 오늘도 화이팅!")
    def test_full_flow(self, mock_dify, greeting_service, mock_weather_service):
        mock_weather_service.get_weather_summary_range.return_value = "4/18: 맑음, 최고 22℃"

        result = greeting_service.generate_greeting(
            "광주광역시 북구", date(2026, 4, 20)
        )

        assert result == "안녕하세요! 오늘도 화이팅!"
        mock_weather_service.get_weather_summary_range.assert_called_once_with(
            "광주광역시 북구", date(2026, 4, 20), days_before=2, days_after=2
        )
        # Dify에 전달된 inputs 확인
        call_args = mock_dify.call_args
        inputs = call_args[0][0]
        assert inputs["weather_context"] == "4/18: 맑음, 최고 22℃"
        assert "2026년 4월 20일" in inputs["date_info"]
        assert "anniversary_info" in inputs
        assert "sundry_day_info" in inputs

    @patch.object(GreetingService, "_call_dify", return_value="인삿말 결과")
    def test_weather_failure_still_generates(self, mock_dify, greeting_service, mock_weather_service):
        mock_weather_service.get_weather_summary_range.side_effect = Exception("API error")

        result = greeting_service.generate_greeting(
            "광주광역시 북구", date(2026, 4, 20)
        )

        assert result == "인삿말 결과"
        call_args = mock_dify.call_args
        inputs = call_args[0][0]
        assert inputs["weather_context"] == ""

    @patch.object(GreetingService, "_call_dify", return_value="인삿말 결과")
    def test_no_weather_context(self, mock_dify, greeting_service, mock_weather_service):
        mock_weather_service.get_weather_summary_range.return_value = ""

        result = greeting_service.generate_greeting(
            "광주광역시 북구", date(2026, 4, 20)
        )

        assert result == "인삿말 결과"
        call_args = mock_dify.call_args
        inputs = call_args[0][0]
        assert inputs["weather_context"] == ""
