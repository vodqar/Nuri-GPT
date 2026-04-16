"""Greeting API Endpoints

알림장 인삿말 생성 엔드포인트
"""

import logging

from typing import List
from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_current_user, get_greeting_service, get_user_repository
from app.db.repositories.user_repository import UserRepository
from app.db.models.user import UserUpdate
from app.schemas.greeting import GreetingRequest, GreetingResponse
from app.services.greeting import GreetingService

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
async def generate_greeting(
    request: GreetingRequest,
    current_user: dict = Depends(get_current_user),
    greeting_service: GreetingService = Depends(get_greeting_service),
    user_repo: UserRepository = Depends(get_user_repository),
) -> GreetingResponse:
    """시군구 지역과 알림장 배포 일자를 기반으로 인삿말을 생성합니다."""
    greeting = greeting_service.generate_greeting(
        region=request.region,
        target_date=request.target_date,
        user_input=request.user_input,
        enabled_contexts=request.enabled_contexts,
        name_input=request.name_input,
        use_emoji=request.use_emoji,
    )

    # 생성 성공 시 유저의 preferred_region 업데이트
    if greeting:
        from uuid import UUID
        user_id = UUID(current_user["id"])
        await user_repo.update(
            user_id, 
            UserUpdate(preferred_region=request.region)
        )

    return GreetingResponse(greeting=greeting)
