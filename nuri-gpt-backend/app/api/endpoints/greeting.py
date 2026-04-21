"""Greeting API Endpoints

알림장 인삿말 생성 엔드포인트
"""

import asyncio
import json
import logging

from typing import List
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import StreamingResponse

from app.core.dependencies import get_current_user, get_greeting_service, get_user_preference_repository
from app.db.repositories.user_preference_repository import UserPreferenceRepository
from app.schemas.greeting import GreetingRequest, GreetingResponse
from app.services.greeting import GreetingService
from app.core.rate_limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/regions", response_model=List[str])
async def get_regions():
    """사용 가능한 시군구 지역 목록을 반환합니다."""
    import json
    import os
    from app.core.config import get_settings
    
    # region_grid_map.json 경로 (app/data/region_grid_map.json)
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "region_grid_map.json")
    
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            region_map = json.load(f)
            return sorted(list(region_map.keys()))
    except Exception as e:
        logger.error(f"Failed to load regions: {e}")
        return []

@router.post("/generate", response_model=GreetingResponse, status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def generate_greeting(
    request: Request,
    greeting_request: GreetingRequest,
    current_user: dict = Depends(get_current_user),
    greeting_service: GreetingService = Depends(get_greeting_service),
    pref_repo: UserPreferenceRepository = Depends(get_user_preference_repository),
) -> GreetingResponse:
    """시군구 지역과 알림장 배포 일자를 기반으로 인삿말을 생성합니다."""
    # 병렬 비동기 버전 사용 (날씨+절기 병렬 수집)
    greeting = await greeting_service.generate_greeting_async(
        region=greeting_request.region,
        target_date=greeting_request.target_date,
        user_input=greeting_request.user_input,
        enabled_contexts=greeting_request.enabled_contexts,
        name_input=greeting_request.name_input,
        use_emoji=greeting_request.use_emoji,
    )

    # 생성 성공 시 유저의 greeting.preferred_region 설정 저장
    if greeting:
        try:
            from uuid import UUID
            user_id = UUID(current_user["id"])
            await pref_repo.upsert(user_id, "greeting.preferred_region", greeting_request.region)
        except Exception as e:
            logger.warning(f"Failed to save preferred region, greeting still returned: {e}")

    return GreetingResponse(greeting=greeting)


@router.post("/generate/stream", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def generate_greeting_stream(
    request: Request,
    greeting_request: GreetingRequest,
    current_user: dict = Depends(get_current_user),
    greeting_service: GreetingService = Depends(get_greeting_service),
    pref_repo: UserPreferenceRepository = Depends(get_user_preference_repository),
):
    """시군구 지역과 알림장 배포 일자를 기반으로 인삿말을 SSE 스트리밍으로 생성합니다."""
    async def event_generator():
        try:
            # Phase 1: 진행 상태 전송 — 날씨+절기 병렬 수집
            yield f"data: {json.dumps({'event': 'progress', 'stage': 'weather'}, ensure_ascii=False)}\n\n"

            if greeting_request.enabled_contexts is None:
                enabled_contexts = ["weather", "seasonal", "holiday", "anniversary", "sundry"]
            else:
                enabled_contexts = greeting_request.enabled_contexts

            # 날짜 맥락은 즉시 계산
            date_ctx = greeting_service._build_date_context(greeting_request.target_date)

            # 날씨와 절기를 병렬 수집
            weather_coro = asyncio.to_thread(
                greeting_service._get_weather_context,
                greeting_request.region, greeting_request.target_date, enabled_contexts,
            )
            seasonal_coro = asyncio.to_thread(
                greeting_service._build_seasonal_context, greeting_request.target_date,
            )

            weather_summary, seasonal_ctx = await asyncio.gather(
                weather_coro, seasonal_coro, return_exceptions=True
            )

            if isinstance(weather_summary, Exception):
                logger.warning(f"Weather context failed in stream: {weather_summary}")
                weather_summary = ""
            if isinstance(seasonal_ctx, Exception):
                logger.warning(f"Seasonal context failed in stream: {seasonal_ctx}")
                seasonal_ctx = {
                    "seasonal_info": "",
                    "holiday_info": "",
                    "anniversary_info": "",
                    "sundry_day_info": "",
                }

            yield f"data: {json.dumps({'event': 'progress', 'stage': 'context'}, ensure_ascii=False)}\n\n"

            # Dify inputs 조립 (공통 메서드 재사용)
            inputs = greeting_service._build_dify_inputs(
                date_ctx, weather_summary, seasonal_ctx,
                enabled_contexts, greeting_request.user_input, greeting_request.name_input, greeting_request.use_emoji,
            )

            # Phase 2: Dify 스트리밍을 비동기로 릴레이
            # _call_dify_streaming은 동기 제너레이터(requests.stream)이므로
            # next() 호출을 run_in_executor로 옮겨 이벤트 루프 블로킹 방지
            full_text = ""
            stream_iter = iter(greeting_service._call_dify_streaming(inputs))
            loop = asyncio.get_running_loop()
            while True:
                chunk = await loop.run_in_executor(None, next, stream_iter, None)
                if chunk is None:
                    break
                full_text += chunk
                yield f"data: {json.dumps({'event': 'token', 'text': chunk}, ensure_ascii=False)}\n\n"

            if not full_text:
                yield f"data: {json.dumps({'event': 'error', 'message': '인삿말 생성에 실패했습니다. (빈 응답)'}, ensure_ascii=False)}\n\n"
            else:
                yield f"data: {json.dumps({'event': 'done', 'greeting': full_text}, ensure_ascii=False)}\n\n"

            # preferred_region 저장
            if full_text:
                try:
                    from uuid import UUID
                    user_id = UUID(current_user["id"])
                    await pref_repo.upsert(user_id, "greeting.preferred_region", greeting_request.region)
                except Exception as e:
                    logger.warning(f"Failed to save preferred region in stream: {e}")

        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            yield f"data: {json.dumps({'event': 'error', 'message': '인삿말 생성 중 오류가 발생했습니다.'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
