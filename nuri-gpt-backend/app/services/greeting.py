"""알림장 인삿말 생성 서비스

날씨/날짜/절기/기념일 맥락을 조립하여 Dify Chatflow로 인삿말을 생성한다.
"""

import asyncio
import json
import logging
import random
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from typing import Dict, Generator, List, Optional

import requests

from app.core.config import get_settings
from app.services.special_day import SpecialDayService
from app.services.weather import WeatherService

logger = logging.getLogger(__name__)

# ── 24절기 테이블 (fallback — API 사용 불가 시에만 활용) ──
_FALLBACK_SOLAR_TERMS = [
    (1, 6, "소한"), (1, 20, "대한"),
    (2, 4, "입춘"), (2, 19, "우수"),
    (3, 6, "경칩"), (3, 21, "춘분"),
    (4, 5, "청명"), (4, 20, "곡우"),
    (5, 6, "입하"), (5, 21, "소만"),
    (6, 6, "망종"), (6, 21, "하지"),
    (7, 7, "소서"), (7, 23, "대서"),
    (8, 7, "입추"), (8, 23, "처서"),
    (9, 8, "백로"), (9, 23, "추분"),
    (10, 8, "한로"), (10, 23, "상강"),
    (11, 7, "입동"), (11, 22, "소설"),
    (12, 7, "대설"), (12, 22, "동지"),
]

# ── 법정기념일/공휴일 (fallback — API 사용 불가 시에만 활용) ──
_FALLBACK_HOLIDAYS = {
    (1, 1): "신정",
    (3, 1): "삼일절",
    (5, 5): "어린이날",
    (6, 6): "현충일",
    (7, 17): "제헌절",
    (8, 15): "광복절",
    (10, 3): "개천절",
    (10, 9): "한글날",
    (12, 25): "크리스마스",
    (5, 1): "근로자의날",
    (5, 8): "어버이날",
    (5, 15): "스승의날",
    (10, 2): "국군의날",
    (4, 19): "4·19혁명 기념일",
    (11, 17): "학생의날",
}

WEEKDAY_KR = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]


class GreetingService:
    """알림장 인삿말 생성 서비스"""

    def __init__(
        self,
        weather_service: Optional[WeatherService] = None,
        special_day_service: Optional[SpecialDayService] = None,
    ):
        self.weather_service = weather_service or WeatherService()
        self.special_day_service = special_day_service

    def _generate_seed_sequence(self) -> List[int]:
        """[1,2,3] 중 1~2개를 무작위 추출하여 순서를 섞고, 마지막에 항상 4를 붙여 반환"""
        count = random.randint(1, 2)
        sequence = random.sample([1, 2, 3], count)
        random.shuffle(sequence)
        sequence.append(4)
        return sequence

    def _extract_answer_text(self, response: requests.Response) -> str:
        content_type = response.headers.get("Content-Type", "")
        answer_text = ""

        if "text/event-stream" in content_type:
            for line in response.iter_lines():
                if not line:
                    continue

                decoded = line.decode("utf-8") if isinstance(line, bytes) else str(line)
                if not decoded.startswith("data: "):
                    continue

                data_str = decoded[6:]

                try:
                    event_data = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                if event_data.get("event") == "error":
                    logger.error(
                        "Greeting Dify error event: code=%s message=%s",
                        event_data.get("code", "N/A"),
                        event_data.get("message", "Unknown error"),
                    )
                    continue

                chunk = ""
                if "answer" in event_data:
                    chunk = event_data["answer"]
                elif "text" in event_data:
                    chunk = event_data["text"]
                elif "data" in event_data and "text" in event_data["data"]:
                    chunk = event_data["data"]["text"]

                if chunk:
                    answer_text += chunk
        else:
            data = response.json()
            if isinstance(data, dict):
                answer_text = data.get("answer", "") or data.get("text", "")

        logger.info(
            "Greeting Dify response parsed | content_type=%s answer_length=%s",
            content_type,
            len(answer_text),
        )
        return answer_text

    # ── 날짜/요일/주차 맥락 ──────────────────────────────

    def _build_date_context(self, target_date: date) -> Dict[str, str]:
        """target_date 기준 날짜/요일/주차 정보"""
        date_info = (
            f"{target_date.year}년 {target_date.month}월 {target_date.day}일"
            f" ({WEEKDAY_KR[target_date.weekday()]})"
        )

        # 주차 계산: ISO 주차 기준
        iso_week = target_date.isocalendar()[1]
        # 해당 월의 첫 날의 ISO 주차
        first_of_month = date(target_date.year, target_date.month, 1)
        first_iso_week = first_of_month.isocalendar()[1]
        # 월 내 주차 (1부터 시작)
        month_week = iso_week - first_iso_week + 1
        # 1일이 일요일이면 ISO 주차가 전년 마지막 주일 수 있음
        if first_of_month.weekday() == 6:  # 일요일
            month_week = iso_week - first_iso_week + 2

        month_week = max(1, month_week)
        month_week_info = f"{target_date.month}월 {month_week}주차"

        return {
            "date_info": date_info,
            "month_week": month_week_info,
        }

    # ── 절기/기념일 맥락 ─────────────────────────────────

    def _build_seasonal_context(self, target_date: date) -> Dict[str, str]:
        """target_date 기준 절기/기념일 정보"""
        if self.special_day_service:
            seasonal_info = self.special_day_service.get_solar_term_range(target_date)
            holiday_info = self.special_day_service.get_holiday(target_date)
            anniversary_info = self.special_day_service.get_anniversary(target_date)
            sundry_day_info = self.special_day_service.get_sundry_day(target_date)
        else:
            seasonal_info = self._get_solar_term_range_fallback(target_date)
            holiday_info = _FALLBACK_HOLIDAYS.get(
                (target_date.month, target_date.day), "해당 없음"
            )
            anniversary_info = "해당 없음"
            sundry_day_info = "해당 없음"

        return {
            "seasonal_info": seasonal_info,
            "holiday_info": holiday_info,
            "anniversary_info": anniversary_info,
            "sundry_day_info": sundry_day_info,
        }

    def _get_solar_term_range_fallback(self, target_date: date) -> str:
        """target_date가 속한 절기 구간 반환 (fallback)"""
        year = target_date.year
        # 해당 날짜 이전의 가장 최근 절기 찾기
        prev_term = None
        next_term = None

        for i, (m, d, name) in enumerate(_FALLBACK_SOLAR_TERMS):
            term_date = date(year, m, d)
            if term_date <= target_date:
                prev_term = (term_date, name)
            if term_date > target_date:
                next_term = (term_date, name)
                break

        # 연도 경계 처리: 12/22(동지) 이후 → 다음 해 소한
        if prev_term is None:
            # 1월 1~5일 → 전년 동지
            prev_term = (date(year - 1, 12, 22), "동지")
        if next_term is None:
            # 12/22 이후 → 다음 해 소한
            next_term = (date(year + 1, 1, 6), "소한")

        return f"{prev_term[1]}({prev_term[0].month}월 {prev_term[0].day}일) ~ {next_term[1]}({next_term[0].month}월 {next_term[0].day}일)"

    # ── Dify Chatflow 호출 ────────────────────────────────

    def _call_dify(self, inputs: Dict[str, str]) -> str:
        """Dify Chatflow API 호출 → 인삿말 텍스트 반환"""
        settings = get_settings()
        dify_key = settings.dify_greeting_api_key or settings.dify_api_key
        dify_url = settings.dify_greeting_api_url or settings.dify_api_url

        if not dify_key:
            logger.error("Dify greeting API key is not configured.")
            return ""

        payload = {
            "inputs": inputs,
            "query": "알림장 인삿말을 생성해주세요.",
            "response_mode": "streaming",
            "conversation_id": "",
            "user": "nuri-gpt-user",
            "auto_generate_name": False,
        }

        headers = {
            "Authorization": f"Bearer {dify_key}",
            "Content-Type": "application/json",
        }

        endpoint = f"{dify_url.rstrip('/')}/chat-messages"

        try:
            logger.info(
                "Greeting Dify request | endpoint=%s input_keys=%s",
                endpoint,
                sorted(inputs.keys()),
            )
            resp = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                stream=True,
                timeout=30,
            )
            resp.raise_for_status()
            answer = self._extract_answer_text(resp)

            if not answer:
                logger.warning("Greeting Dify returned empty answer text.")
            return answer

        except Exception as e:
            logger.error(f"Failed to call Dify greeting API: {e}")
            return ""

    # ── 공개 메서드 ────────────────────────────────────────

    def generate_greeting(
        self,
        region: str,
        target_date: date,
        user_input: Optional[str] = None,
        enabled_contexts: Optional[List[str]] = None,
        name_input: bool = False,
        use_emoji: bool = True,
    ) -> str:
        """지역+날짜 → 알림장 인삿말 생성"""
        # 0. 맥락 활성화 여부 확인 (기본값: 모든 맥락 활성화)
        if enabled_contexts is None:
            enabled_contexts = ["weather", "seasonal", "holiday", "anniversary", "sundry"]

        # 1. 날씨 맥락
        weather_summary = ""
        if "weather" in enabled_contexts:
            try:
                weather_summary = self.weather_service.get_weather_summary_range(
                    region, target_date, days_before=2, days_after=2
                )
                logger.info(
                    "Weather summary result | region=%s target_date=%s summary='%s'",
                    region, target_date, weather_summary,
                )
            except Exception as e:
                logger.warning(f"Weather context failed, continuing without: {e}")
        else:
            logger.info("Weather context skipped (not in enabled_contexts=%s)", enabled_contexts)

        # 2. 날짜/절기/기념일 맥락
        date_ctx = self._build_date_context(target_date)
        seasonal_ctx = self._build_seasonal_context(target_date)

        # 3. Dify Chatflow 호출
        inputs = {
            "date_info": date_ctx["date_info"],
            "month_week": date_ctx["month_week"] if "week" in enabled_contexts or not enabled_contexts else date_ctx["month_week"],
            "weather_context": weather_summary,
            "seasonal_info": seasonal_ctx["seasonal_info"] if "seasonal" in enabled_contexts else "",
            "holiday_info": seasonal_ctx["holiday_info"] if "holiday" in enabled_contexts else "",
            "anniversary_info": seasonal_ctx["anniversary_info"] if "anniversary" in enabled_contexts else "",
            "sundry_day_info": seasonal_ctx["sundry_day_info"] if "sundry" in enabled_contexts else "",
            "user_custom_input": user_input or "",
            "name_input": "true" if name_input else "false",
            "use_emoji": "true" if use_emoji else "false",
            "seed_sequence": json.dumps(self._generate_seed_sequence()),
        }

        # 주차 정보(month_week)는 별도 체크박스가 없으므로 기본 포함하거나, 
        # enabled_contexts에 'week'가 포함되어 있는지 확인 (프론트엔드와 맞춰야 함)
        # 계획서에는 없었으나 일관성을 위해 추가 요구사항(user_custom_input) 반영

        logger.info("Greeting inputs to Dify: %s", inputs)
        greeting = self._call_dify(inputs)
        return greeting

    async def generate_greeting_async(
        self,
        region: str,
        target_date: date,
        user_input: Optional[str] = None,
        enabled_contexts: Optional[List[str]] = None,
        name_input: bool = False,
        use_emoji: bool = True,
    ) -> str:
        """지역+날짜 → 알림장 인삿말 생성 (비동기 병렬 버전)

        날씨 조회와 절기/기념일 조회를 병렬로 실행하여
        전체 응답 시간을 단축한다.
        """
        if enabled_contexts is None:
            enabled_contexts = ["weather", "seasonal", "holiday", "anniversary", "sundry"]

        # 날짜 맥락은 순수 계산이므로 즉시 실행
        date_ctx = self._build_date_context(target_date)

        # 날씨와 절기/기념일을 병렬 실행
        weather_coro = asyncio.to_thread(
            self._get_weather_context, region, target_date, enabled_contexts
        )
        seasonal_coro = asyncio.to_thread(
            self._build_seasonal_context, target_date
        )

        weather_summary, seasonal_ctx = await asyncio.gather(
            weather_coro, seasonal_coro, return_exceptions=True
        )

        # 예외 처리: 병렬 실행 중 하나가 실패해도 나머지는 사용
        if isinstance(weather_summary, Exception):
            logger.warning(f"Weather context failed, continuing without: {weather_summary}")
            weather_summary = ""
        if isinstance(seasonal_ctx, Exception):
            logger.warning(f"Seasonal context failed, continuing without: {seasonal_ctx}")
            seasonal_ctx = {
                "seasonal_info": "",
                "holiday_info": "",
                "anniversary_info": "",
                "sundry_day_info": "",
            }

        # Dify Chatflow 호출
        inputs = self._build_dify_inputs(
            date_ctx, weather_summary, seasonal_ctx,
            enabled_contexts, user_input, name_input, use_emoji,
        )

        logger.info("Greeting inputs to Dify: %s", inputs)
        greeting = await asyncio.to_thread(self._call_dify, inputs)
        return greeting

    def _build_dify_inputs(
        self,
        date_ctx: Dict,
        weather_summary: str,
        seasonal_ctx: Dict,
        enabled_contexts: List[str],
        user_input: Optional[str],
        name_input: bool,
        use_emoji: bool,
    ) -> Dict[str, str]:
        """Dify Chatflow 호출용 inputs 딕셔너리 조립"""
        return {
            "date_info": date_ctx["date_info"],
            "month_week": date_ctx["month_week"],
            "weather_context": weather_summary if isinstance(weather_summary, str) else "",
            "seasonal_info": seasonal_ctx.get("seasonal_info", "") if "seasonal" in enabled_contexts else "",
            "holiday_info": seasonal_ctx.get("holiday_info", "") if "holiday" in enabled_contexts else "",
            "anniversary_info": seasonal_ctx.get("anniversary_info", "") if "anniversary" in enabled_contexts else "",
            "sundry_day_info": seasonal_ctx.get("sundry_day_info", "") if "sundry" in enabled_contexts else "",
            "user_custom_input": user_input or "",
            "name_input": "true" if name_input else "false",
            "use_emoji": "true" if use_emoji else "false",
            "seed_sequence": json.dumps(self._generate_seed_sequence()),
        }

    def _get_weather_context(
        self, region: str, target_date: date, enabled_contexts: List[str]
    ) -> str:
        """날씨 맥락만 조회 (generate_greeting에서 분리)"""
        if "weather" not in enabled_contexts:
            logger.info("Weather context skipped (not in enabled_contexts=%s)", enabled_contexts)
            return ""
        try:
            summary = self.weather_service.get_weather_summary_range(
                region, target_date, days_before=2, days_after=2
            )
            logger.info(
                "Weather summary result | region=%s target_date=%s summary='%s'",
                region, target_date, summary,
            )
            return summary
        except Exception as e:
            logger.warning(f"Weather context failed, continuing without: {e}")
            return ""

    def _call_dify_streaming(self, inputs: Dict[str, str]) -> Generator[str, None, None]:
        """Dify Chatflow API 호출 → SSE 토큰을 yield하는 제너레이터

        각 yield는 Dify SSE 스트림의 answer 청크를 반환한다.
        """
        settings = get_settings()
        dify_key = settings.dify_greeting_api_key or settings.dify_api_key
        dify_url = settings.dify_greeting_api_url or settings.dify_api_url

        if not dify_key:
            logger.error("Dify greeting API key is not configured.")
            return

        payload = {
            "inputs": inputs,
            "query": "알림장 인삿말을 생성해주세요.",
            "response_mode": "streaming",
            "conversation_id": "",
            "user": "nuri-gpt-user",
            "auto_generate_name": False,
        }

        headers = {
            "Authorization": f"Bearer {dify_key}",
            "Content-Type": "application/json",
        }

        endpoint = f"{dify_url.rstrip('/')}/chat-messages"

        try:
            logger.info(
                "Greeting Dify streaming request | endpoint=%s input_keys=%s",
                endpoint,
                sorted(inputs.keys()),
            )
            resp = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                stream=True,
                timeout=120,
            )
            resp.raise_for_status()

            for line in resp.iter_lines():
                if not line:
                    continue
                decoded = line.decode("utf-8") if isinstance(line, bytes) else str(line)
                if not decoded.startswith("data: "):
                    continue

                data_str = decoded[6:]
                try:
                    event_data = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                if event_data.get("event") == "error":
                    logger.error(
                        "Greeting Dify streaming error: code=%s message=%s",
                        event_data.get("code", "N/A"),
                        event_data.get("message", "Unknown error"),
                    )
                    continue

                chunk = ""
                if "answer" in event_data:
                    chunk = event_data["answer"]
                elif "text" in event_data:
                    chunk = event_data["text"]
                elif "data" in event_data and isinstance(event_data.get("data"), dict) and "text" in event_data["data"]:
                    chunk = event_data["data"]["text"]

                if chunk:
                    yield chunk

        except Exception as e:
            logger.error(f"Failed to call Dify greeting API (streaming): {e}")
