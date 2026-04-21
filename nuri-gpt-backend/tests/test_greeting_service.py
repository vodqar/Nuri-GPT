"""GreetingService 단위 테스트"""

import json
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

    @patch.object(GreetingService, "_call_dify", return_value="인삿말 결과")
    def test_name_input_true_passed_to_dify(self, mock_dify, greeting_service, mock_weather_service):
        mock_weather_service.get_weather_summary_range.return_value = ""

        greeting_service.generate_greeting(
            "광주광역시 북구", date(2026, 4, 20), name_input=True
        )

        inputs = mock_dify.call_args[0][0]
        assert inputs["name_input"] == "true"

    @patch.object(GreetingService, "_call_dify", return_value="인삿말 결과")
    def test_name_input_false_passed_to_dify(self, mock_dify, greeting_service, mock_weather_service):
        mock_weather_service.get_weather_summary_range.return_value = ""

        greeting_service.generate_greeting(
            "광주광역시 북구", date(2026, 4, 20), name_input=False
        )

        inputs = mock_dify.call_args[0][0]
        assert inputs["name_input"] == "false"

    @patch.object(GreetingService, "_call_dify", return_value="인삿말 결과")
    def test_use_emoji_false_passed_to_dify(self, mock_dify, greeting_service, mock_weather_service):
        mock_weather_service.get_weather_summary_range.return_value = ""

        greeting_service.generate_greeting(
            "광주광역시 북구", date(2026, 4, 20), use_emoji=False
        )

        inputs = mock_dify.call_args[0][0]
        assert inputs["use_emoji"] == "false"

    @patch.object(GreetingService, "_call_dify", return_value="인삿말 결과")
    def test_use_emoji_true_passed_to_dify(self, mock_dify, greeting_service, mock_weather_service):
        mock_weather_service.get_weather_summary_range.return_value = ""

        greeting_service.generate_greeting(
            "광주광역시 북구", date(2026, 4, 20), use_emoji=True
        )

        inputs = mock_dify.call_args[0][0]
        assert inputs["use_emoji"] == "true"

    @patch.object(GreetingService, "_call_dify", return_value="인삿말 결과")
    def test_seed_sequence_in_dify_inputs(self, mock_dify, greeting_service, mock_weather_service):
        mock_weather_service.get_weather_summary_range.return_value = ""

        greeting_service.generate_greeting(
            "광주광역시 북구", date(2026, 4, 20)
        )

        inputs = mock_dify.call_args[0][0]
        assert "seed_sequence" in inputs
        parsed = json.loads(inputs["seed_sequence"])
        assert 2 <= len(parsed) <= 3
        assert all(n in [1, 2, 3, 4] for n in parsed)
        assert len(parsed) == len(set(parsed))  # no duplicates
        assert parsed[-1] == 4  # always ends with 4


# ── _generate_seed_sequence ────────────────────────────

class TestGenerateSeedSequence:
    def test_length_range(self, greeting_service):
        for _ in range(100):
            seq = greeting_service._generate_seed_sequence()
            assert 2 <= len(seq) <= 3

    def test_valid_elements(self, greeting_service):
        for _ in range(100):
            seq = greeting_service._generate_seed_sequence()
            assert all(n in [1, 2, 3, 4] for n in seq)

    def test_no_duplicates(self, greeting_service):
        for _ in range(100):
            seq = greeting_service._generate_seed_sequence()
            assert len(seq) == len(set(seq))

    def test_always_ends_with_4(self, greeting_service):
        for _ in range(100):
            seq = greeting_service._generate_seed_sequence()
            assert seq[-1] == 4

    def test_4_appears_only_at_end(self, greeting_service):
        for _ in range(100):
            seq = greeting_service._generate_seed_sequence()
            assert 4 not in seq[:-1]


# ── _call_dify_streaming ──────────────────────────────

class TestCallDifyStreaming:
    def test_yields_answer_chunks(self, greeting_service):
        """Dify SSE 응답에서 answer 청크를 yield하는지 확인"""
        sse_lines = [
            'data: {"event": "message", "answer": "안녕"}',
            'data: {"event": "message", "answer": "하세요"}',
            'data: {"event": "message_end", "answer": ""}',
        ]
        mock_resp = MagicMock()
        mock_resp.iter_lines.return_value = sse_lines
        mock_resp.raise_for_status = MagicMock()

        with patch("app.services.greeting.requests.post", return_value=mock_resp), \
             patch("app.services.greeting.get_settings") as mock_settings:
            mock_settings.return_value.dify_greeting_api_key = "test-key"
            mock_settings.return_value.dify_greeting_api_url = "https://dify.test/v1"
            mock_settings.return_value.dify_api_key = None
            mock_settings.return_value.dify_api_url = None

            chunks = list(greeting_service._call_dify_streaming({"date_info": "test"}))
            assert chunks == ["안녕", "하세요"]

    def test_no_key_yields_nothing(self, greeting_service):
        """API 키가 없으면 아무것도 yield하지 않음"""
        with patch("app.services.greeting.get_settings") as mock_settings:
            mock_settings.return_value.dify_greeting_api_key = None
            mock_settings.return_value.dify_api_key = None
            chunks = list(greeting_service._call_dify_streaming({"date_info": "test"}))
            assert chunks == []

    def test_error_event_is_skipped(self, greeting_service):
        """Dify error 이벤트는 yield하지 않고 로깅만 함"""
        sse_lines = [
            'data: {"event": "error", "code": "500", "message": "Server error"}',
            'data: {"event": "message", "answer": "복구됨"}',
        ]
        mock_resp = MagicMock()
        mock_resp.iter_lines.return_value = sse_lines
        mock_resp.raise_for_status = MagicMock()

        with patch("app.services.greeting.requests.post", return_value=mock_resp), \
             patch("app.services.greeting.get_settings") as mock_settings:
            mock_settings.return_value.dify_greeting_api_key = "test-key"
            mock_settings.return_value.dify_greeting_api_url = "https://dify.test/v1"
            mock_settings.return_value.dify_api_key = None
            mock_settings.return_value.dify_api_url = None

            chunks = list(greeting_service._call_dify_streaming({"date_info": "test"}))
            assert chunks == ["복구됨"]


# ── _build_dify_inputs ────────────────────────────────

class TestBuildDifyInputs:
    def test_includes_all_contexts(self, greeting_service):
        date_ctx = {"date_info": "2026년 4월 18일 (금요일)", "month_week": "4월 3주차"}
        weather_summary = "맑음, 최고 22℃"
        seasonal_ctx = {
            "seasonal_info": "청명~곡우",
            "holiday_info": "해당 없음",
            "anniversary_info": "해당 없음",
            "sundry_day_info": "해당 없음",
        }
        inputs = greeting_service._build_dify_inputs(
            date_ctx, weather_summary, seasonal_ctx,
            ["weather", "seasonal", "holiday", "anniversary", "sundry"],
            None, False, True,
        )
        assert inputs["weather_context"] == "맑음, 최고 22℃"
        assert inputs["seasonal_info"] == "청명~곡우"
        assert inputs["name_input"] == "false"
        assert inputs["use_emoji"] == "true"

    def test_disabled_contexts_are_empty(self, greeting_service):
        date_ctx = {"date_info": "2026년 4월 18일 (금요일)", "month_week": "4월 3주차"}
        weather_summary = "맑음"
        seasonal_ctx = {
            "seasonal_info": "청명~곡우",
            "holiday_info": "어린이날",
            "anniversary_info": "해당 없음",
            "sundry_day_info": "해당 없음",
        }
        inputs = greeting_service._build_dify_inputs(
            date_ctx, weather_summary, seasonal_ctx,
            ["weather"],  # weather만 활성화
            "특별 요청", True, False,
        )
        assert inputs["weather_context"] == "맑음"
        assert inputs["seasonal_info"] == ""
        assert inputs["holiday_info"] == ""
        assert inputs["user_custom_input"] == "특별 요청"
        assert inputs["name_input"] == "true"
        assert inputs["use_emoji"] == "false"
