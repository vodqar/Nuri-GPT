"""기상청 단기/중기예보 API를 조회하여 날씨 요약 텍스트를 생성하는 서비스"""

import json
import logging
import os
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

import requests
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.utils.exceptions import ValidationError

logger = logging.getLogger(__name__)

KST = ZoneInfo("Asia/Seoul")

# 단기예보 하늘상태 코드 → 텍스트
SKY_MAP = {"1": "맑음", "3": "구름많음", "4": "흐림"}

# 단기예보 강수형태 코드 → 텍스트
PTY_MAP = {
    "0": None,       # 없음
    "1": "비",
    "2": "비/눈",
    "3": "눈",
    "4": "소나기",
}


class WeatherService:
    """기상청 API를 이용한 날씨 정보 조회 서비스"""

    def __init__(
        self,
        api_key: Optional[str] = None,
    ):
        settings = get_settings()
        self.api_key = api_key or settings.kma_api_key
        self.base_url = (
            "https://apihub.kma.go.kr/api/typ02/openApi/VilageFcstInfoService_2.0"
        )
        self.mid_base_url = (
            "https://apihub.kma.go.kr/api/typ02/openApi/MidFcstInfoService"
        )
        self._grid_map: Optional[Dict] = None

    # ── 시군구 → 좌표/regId 조회 ──────────────────────────

    def _load_grid_map(self) -> Dict:
        if self._grid_map is None:
            json_path = os.path.join(
                os.path.dirname(__file__), "..", "data", "region_grid_map.json"
            )
            with open(json_path, "r", encoding="utf-8") as f:
                self._grid_map = json.load(f)
        return self._grid_map

    def get_region_info(self, region: str) -> Dict:
        """시군구명 → {nx, ny, mid_land_reg_id, mid_temp_reg_id}"""
        grid_map = self._load_grid_map()
        info = grid_map.get(region)
        if not info:
            raise ValidationError(f"지원하지 않는 지역입니다: {region}")
        return info

    # ── 단기예보 base_time 계산 ────────────────────────────

    def _calculate_base_time(self) -> Tuple[str, str]:
        """현재 KST 기준 가장 최근 단기예보 발표 시각 반환 → (base_date, base_time)"""
        now = datetime.now(KST)
        # 발표 시각 경계 (분 단위 고려)
        thresholds = [
            (2310, "2300"), (2010, "2000"), (1710, "1700"),
            (1410, "1400"), (1110, "1100"), (810, "0800"),
            (510, "0500"),  (210, "0200"),
        ]

        hhmm = now.hour * 100 + now.minute

        for threshold, base_time in thresholds:
            if hhmm >= threshold:
                return now.strftime("%Y%m%d"), base_time

        # 02:10 이전 → 전날 2300
        yesterday = now - timedelta(days=1)
        return yesterday.strftime("%Y%m%d"), "2300"

    # ── 중기예보 tmFc 계산 ────────────────────────────────

    def _calculate_tmfc(self) -> str:
        """현재 KST 기준 중기예보 발표 시각 반환 → 'YYYYMMDDHHMM'"""
        now = datetime.now(KST)
        hour = now.hour

        if hour < 6:
            # 06:00 이전 → 전날 1800
            yesterday = now - timedelta(days=1)
            return f"{yesterday.strftime('%Y%m%d')}1800"
        elif hour < 18:
            # 06:00~18:00 → 당일 0600
            return f"{now.strftime('%Y%m%d')}0600"
        else:
            # 18:00 이후 → 당일 1800
            return f"{now.strftime('%Y%m%d')}1800"

    # ── 단기예보 API 호출 ─────────────────────────────────

    def _fetch_vilage_fcst(
        self, nx: int, ny: int, base_date: str, base_time: str
    ) -> Dict:
        """단기예보(getVilageFcst) API 호출"""
        if not self.api_key:
            logger.warning("KMA_API_KEY is not set. Short-term forecast unavailable.")
            return {}

        params = {
            "authKey": self.api_key,
            "numOfRows": "1000",
            "pageNo": "1",
            "dataType": "JSON",
            "base_date": base_date,
            "base_time": base_time,
            "nx": str(nx),
            "ny": str(ny),
        }

        try:
            resp = requests.get(
                f"{self.base_url}/getVilageFcst",
                params=params,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            # API 응답 코드 확인
            header = data.get("response", {}).get("header", {})
            if header.get("resultCode") != "00":
                logger.error(f"KMA short-term API error: {header.get('resultMsg')}")
                return {}

            items = (
                data.get("response", {})
                .get("body", {})
                .get("items", {})
                .get("item", [])
            )
            return {"items": items}

        except Exception as e:
            logger.error(f"Failed to fetch short-term forecast: {e}")
            return {}

    # ── 중기육상예보 API 호출 ─────────────────────────────

    def _fetch_mid_land_fcst(self, reg_id: str, tm_fc: str) -> Dict:
        """중기육상예보(getMidLandFcst) API 호출"""
        if not self.api_key:
            logger.warning("KMA_API_KEY is not set. Mid-term land forecast unavailable.")
            return {}

        params = {
            "authKey": self.api_key,
            "numOfRows": "10",
            "pageNo": "1",
            "dataType": "JSON",
            "regId": reg_id,
            "tmFc": tm_fc,
        }

        try:
            resp = requests.get(
                f"{self.mid_base_url}/getMidLandFcst",
                params=params,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            header = data.get("response", {}).get("header", {})
            if header.get("resultCode") != "00":
                logger.error(f"KMA mid-term land API error: {header.get('resultMsg')}")
                return {}

            items = (
                data.get("response", {})
                .get("body", {})
                .get("items", {})
                .get("item", [])
            )
            if isinstance(items, dict):
                items = [items]
            return {"items": items}

        except Exception as e:
            logger.error(f"Failed to fetch mid-term land forecast: {e}")
            return {}

    # ── 중기기온 API 호출 ─────────────────────────────────

    def _fetch_mid_ta(self, reg_id: str, tm_fc: str) -> Dict:
        """중기기온(getMidTa) API 호출"""
        if not self.api_key:
            logger.warning("KMA_API_KEY is not set. Mid-term temp forecast unavailable.")
            return {}

        params = {
            "authKey": self.api_key,
            "numOfRows": "10",
            "pageNo": "1",
            "dataType": "JSON",
            "regId": reg_id,
            "tmFc": tm_fc,
        }

        try:
            resp = requests.get(
                f"{self.mid_base_url}/getMidTa",
                params=params,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            header = data.get("response", {}).get("header", {})
            if header.get("resultCode") != "00":
                logger.error(f"KMA mid-term temp API error: {header.get('resultMsg')}")
                return {}

            items = (
                data.get("response", {})
                .get("body", {})
                .get("items", {})
                .get("item", [])
            )
            if isinstance(items, dict):
                items = [items]
            return {"items": items}

        except Exception as e:
            logger.error(f"Failed to fetch mid-term temp forecast: {e}")
            return {}

    # ── 단기예보 파싱 ─────────────────────────────────────

    # 시간대 → 오전/오후/저녁 매핑
    TIME_PERIOD_MAP = {
        "0200": "오전", "0500": "오전", "0800": "오전", "1100": "오전",
        "1400": "오후", "1700": "오후",
        "2000": "저녁", "2300": "저녁",
    }

    def _parse_short_term(
        self, data: Dict, target_dates: List[date], today: Optional[date] = None,
    ) -> Dict[str, str]:
        """단기예보 응답 → 여러 날짜의 날씨 요약 {label: summary}

        당일(today)인 경우 3시간 간격 TMP/SKY/PTY를 오전·오후·저녁으로 묶어 출력.
        이외 날짜는 기존대로 대표 날씨 + 최고/최저 기온.
        """
        items = data.get("items", [])
        if not items:
            return {}

        target_strs = {d.strftime("%Y%m%d"): d for d in target_dates}
        today_str = today.strftime("%Y%m%d") if today else None

        # 날짜별 버킷 — 당일은 시간대별 상세, 이외는 종합
        day_buckets: Dict[str, Dict] = {s: {"sky": None, "pty": None, "tmx": None, "tmn": None} for s in target_strs}
        # 당일 시간대별 수집: {period: {sky, pty, tmps: []}}
        period_data: Dict[str, Dict] = {}

        for item in items:
            fd = item.get("fcstDate", "")
            if fd not in day_buckets:
                continue

            cat = item.get("category", "")
            val = item.get("fcstValue", "")
            ft = item.get("fcstTime", "")
            b = day_buckets[fd]

            if cat == "SKY":
                b["sky"] = SKY_MAP.get(val, b["sky"])
                # 당일 시간대별
                if fd == today_str and ft in self.TIME_PERIOD_MAP:
                    period = self.TIME_PERIOD_MAP[ft]
                    period_data.setdefault(period, {"sky": None, "pty": None, "tmps": []})
                    if val != "0":  # SKY 0은 의미 없음
                        period_data[period]["sky"] = SKY_MAP.get(val, period_data[period]["sky"])
            elif cat == "PTY":
                pty_text = PTY_MAP.get(val)
                if pty_text:
                    b["pty"] = pty_text
                if fd == today_str and ft in self.TIME_PERIOD_MAP:
                    period = self.TIME_PERIOD_MAP[ft]
                    period_data.setdefault(period, {"sky": None, "pty": None, "tmps": []})
                    if pty_text:
                        period_data[period]["pty"] = pty_text
            elif cat == "TMP":
                if fd == today_str and ft in self.TIME_PERIOD_MAP:
                    period = self.TIME_PERIOD_MAP[ft]
                    period_data.setdefault(period, {"sky": None, "pty": None, "tmps": []})
                    try:
                        period_data[period]["tmps"].append(float(val))
                    except (ValueError, TypeError):
                        pass
            elif cat == "TMX":
                b["tmx"] = val
            elif cat == "TMN":
                b["tmn"] = val

        result = {}
        for date_str, d in sorted(target_strs.items()):
            b = day_buckets[date_str]
            label = f"{d.month}/{d.day}"

            # 당일: 시간대별 상세 요약
            if date_str == today_str and period_data:
                period_order = ["오전", "오후", "저녁"]
                parts = []
                for p in period_order:
                    if p not in period_data:
                        continue
                    pd = period_data[p]
                    weather = pd["pty"] or pd["sky"]
                    tmp_avg = sum(pd["tmps"]) / len(pd["tmps"]) if pd["tmps"] else None
                    segment = p
                    if weather:
                        segment += f" {weather}"
                    if tmp_avg is not None:
                        segment += f" {tmp_avg:.0f}℃"
                    parts.append(segment)
                # 최고/최저 추가
                if b["tmx"]:
                    parts.append(f"최고 {b['tmx']}℃")
                if b["tmn"]:
                    parts.append(f"최저 {b['tmn']}℃")
                summary = ", ".join(parts)
            else:
                # 비당일: 대표 날씨 + 최고/최저
                weather = b["pty"] or b["sky"] or ""
                parts = []
                if weather:
                    parts.append(weather)
                if b["tmx"]:
                    parts.append(f"최고 {b['tmx']}℃")
                if b["tmn"]:
                    parts.append(f"최저 {b['tmn']}℃")
                summary = ", ".join(parts)

            if summary:
                result[label] = summary

        return result

    # ── 중기예보 파싱 ─────────────────────────────────────

    def _parse_mid_term(
        self, land_data: Dict, ta_data: Dict, delta_days_list: List[int],
        today: date,
    ) -> Dict[str, str]:
        """중기예보 응답 → 여러 날짜의 날씨 요약 {label: summary}"""
        land_items = land_data.get("items", [])
        ta_items = ta_data.get("items", [])

        if not land_items and not ta_items:
            return {}

        result = {}
        for delta in delta_days_list:
            weather = None

            if land_items:
                item = land_items[0]
                if delta <= 7:
                    wf_am = item.get(f"wf{delta}Am")
                    wf_pm = item.get(f"wf{delta}Pm")
                    if wf_pm:
                        weather = wf_pm
                    elif wf_am:
                        weather = wf_am
                else:
                    wf = item.get(f"wf{delta}")
                    if wf:
                        weather = wf

            ta_min = None
            ta_max = None
            if ta_items:
                item = ta_items[0]
                ta_min_val = item.get(f"taMin{delta}")
                ta_max_val = item.get(f"taMax{delta}")
                if ta_min_val is not None:
                    ta_min = str(ta_min_val)
                if ta_max_val is not None:
                    ta_max = str(ta_max_val)

            parts = []
            if weather:
                parts.append(weather)
            if ta_max:
                parts.append(f"최고 {ta_max}℃")
            if ta_min:
                parts.append(f"최저 {ta_min}℃")

            summary = ", ".join(parts)
            if summary:
                d = today + timedelta(days=delta)
                label = f"{d.month}/{d.day}"
                result[label] = summary

        return result

    # ── 공개 메서드 ────────────────────────────────────────

    def get_weather_summary_range(
        self, region: str, center_date: date, days_before: int = 2, days_after: int = 2
    ) -> str:
        """지역+기준일 ±N일 → 날씨 요약 텍스트

        단기·중기 예보를 한 번씩만 호출하고 여러 날짜를 파싱합니다.
        날씨상태, 하늘상태, 기온만 포함 (강수확률 제외).

        반환 예시:
          4/14: 맑음, 최고 22℃, 최저 10℃
          4/15: 구름많음, 최고 20℃, 최저 12℃
          4/16: 비, 최고 18℃, 최저 13℃
          4/17: 흐림, 최고 19℃, 최저 11℃
          4/18: 맑음, 최고 23℃, 최저 14℃
        """
        region_info = self.get_region_info(region)
        today = date.today()

        # ±N일 날짜 목록 (오늘 이후만)
        all_dates = [
            center_date + timedelta(days=d)
            for d in range(-days_before, days_after + 1)
        ]
        valid_dates = [d for d in all_dates if d >= today]
        if not valid_dates:
            return ""

        # 단기/중기 분류
        short_dates = [d for d in valid_dates if 0 <= (d - today).days <= 3]
        mid_deltas = sorted(set((d - today).days for d in valid_dates if 4 <= (d - today).days <= 10))

        day_summaries: Dict[str, str] = {}

        # 단기예보 (한 번 호출 → 여러 날짜 파싱, 당일은 시간대별 상세)
        if short_dates:
            try:
                base_date, base_time = self._calculate_base_time()
                data = self._fetch_vilage_fcst(
                    region_info["nx"], region_info["ny"], base_date, base_time
                )
                day_summaries.update(self._parse_short_term(data, short_dates, today=today))
            except Exception as e:
                logger.error(f"Short-term forecast error: {e}")

        # 중기예보 (한 번 호출 → 여러 delta 파싱)
        if mid_deltas:
            try:
                tm_fc = self._calculate_tmfc()
                land_data = self._fetch_mid_land_fcst(
                    region_info["mid_land_reg_id"], tm_fc
                )
                ta_data = self._fetch_mid_ta(
                    region_info["mid_temp_reg_id"], tm_fc
                )
                day_summaries.update(
                    self._parse_mid_term(land_data, ta_data, mid_deltas, today)
                )
            except Exception as e:
                logger.error(f"Mid-term forecast error: {e}")

        if not day_summaries:
            return ""

        # 날짜 순 정렬 후 줄바꿈으로 조립
        ordered = sorted(day_summaries.items(), key=lambda kv: kv[0])
        return "\n".join(f"{label}: {summary}" for label, summary in ordered)

    def get_weather_summary(self, region: str, target_date: date) -> str:
        """지역+날짜 → 단일일 날씨 요약 텍스트 (하위호환)"""
        return self.get_weather_summary_range(region, target_date, days_before=0, days_after=0)
