"""CSV → region_grid_map.json 변환 스크립트

3단계(읍면동)가 비어있는 행 = 시군구 대표 좌표를 추출하여
단기예보용 nx, ny + 중기예보용 regId를 통합한 JSON을 생성한다.

사용법:
    python scripts/generate_region_map.py
"""

import csv
import json
import os

CSV_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "download", "Weather_API",
    "동네예보지점좌표(위경도)_202601.csv"
)
OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "app", "data", "region_grid_map.json"
)

# ── 중기예보 육상예보구역코드 (10개 광역 구역) ──
LAND_REG_MAP = {
    "서울특별시": "11B00000",
    "인천광역시": "11B00000",
    "경기도": "11B00000",
    "강원도": None,  # 영서/영동 분기 필요
    "강원특별자치도": None,  # 영서/영동 분기 필요
    "대전광역시": "11C20000",
    "세종특별자치시": "11C20000",
    "충청남도": "11C20000",
    "충청북도": "11C10000",
    "광주광역시": "11F20000",
    "전라남도": "11F20000",
    "전라북도": "11F10000",
    "전북특별자치도": "11F10000",
    "대구광역시": "11H10000",
    "경상북도": "11H10000",
    "부산광역시": "11H20000",
    "울산광역시": "11H20000",
    "경상남도": "11H20000",
    "제주특별자치도": "11G00000",
}

# 강원도 영동 지역 시군구
GANGWON_YEONGDONG = {"강릉시", "속초시", "동해시", "삼척시", "고성군", "양양군"}

# ── 중기예보 기온예보구역코드 (시도별 대표 도시) ──
TEMP_REG_MAP = {
    "서울특별시": "11B10101",
    "인천광역시": "11B20201",
    "경기도": "11B20601",  # 수원
    "강원특별자치도": None,  # 영서/영동 분기 필요
    "대전광역시": "11C20401",
    "세종특별자치시": "11C20404",
    "충청남도": "11C20101",  # 서산
    "충청북도": "11C10301",  # 청주
    "광주광역시": "11F20501",
    "전라남도": "21F20801",  # 목포
    "전라북도": "11F10201",  # 전주
    "전북특별자치도": "11F10201",  # 전주
    "대구광역시": "11H10701",
    "경상북도": "11H10501",  # 안동
    "부산광역시": "11H20201",
    "울산광역시": "11H20101",
    "경상남도": "11H20301",  # 창원
    "제주특별자치도": "11G00201",
}

# 강원도 기온코드 (영서/영동 분기)
GANGWON_TEMP_YEONGSEO = "11D10301"  # 춘천
GANGWON_TEMP_YEONGDONG = "11D20501"  # 강릉
GANGWON_LAND_YEONGSEO = "11D10000"
GANGWON_LAND_YEONGDONG = "11D20000"


def get_land_reg_id(sido: str, sigungu_name: str) -> str:
    """시도+시군구명 → 중기육상예보구역코드"""
    if sido in ("강원도", "강원특별자치도"):
        if sigungu_name in GANGWON_YEONGDONG:
            return GANGWON_LAND_YEONGDONG
        return GANGWON_LAND_YEONGSEO
    return LAND_REG_MAP.get(sido, "")


def get_temp_reg_id(sido: str, sigungu_name: str) -> str:
    """시도+시군구명 → 중기기온예보구역코드"""
    if sido in ("강원도", "강원특별자치도"):
        if sigungu_name in GANGWON_YEONGDONG:
            return GANGWON_TEMP_YEONGDONG
        return GANGWON_TEMP_YEONGSEO
    return TEMP_REG_MAP.get(sido, "")


def main():
    result = {}

    with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)

        for row in reader:
            if len(row) < 7:
                continue

            level1 = row[2].strip()   # 1단계 (시도)
            level2 = row[3].strip()   # 2단계 (시군구)
            level3 = row[4].strip()   # 3단계 (읍면동)
            nx = int(row[5].strip())
            ny = int(row[6].strip())

            # 3단계가 비어있는 행만 = 시군구 대표 좌표
            if level3:
                continue
            if not level1:
                continue

            # 키 포맷: "{1단계} {2단계}" 또는 "{1단계}" (2단계 비어있으면)
            if level2:
                key = f"{level1} {level2}"
                sigungu_name = level2
            else:
                key = level1
                sigungu_name = ""

            result[key] = {
                "nx": nx,
                "ny": ny,
                "mid_land_reg_id": get_land_reg_id(level1, sigungu_name),
                "mid_temp_reg_id": get_temp_reg_id(level1, sigungu_name),
            }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(result)}개 시군구 매핑 생성 → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
