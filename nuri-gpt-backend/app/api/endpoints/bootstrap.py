"""Bootstrap API Endpoint

앱 초기 부팅 시 필요한 데이터를 1 RTT로 병렬 조회
- GET /api/users/me/bootstrap : user + templates + usage
"""

import asyncio
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from app.core.dependencies import (
    get_current_user,
    get_template_repository_with_rls,
    get_usage_service_with_rls,
    get_user_repository_with_rls,
)
from app.core.rate_limiter import limiter
from app.db.models.template import TemplateFilter, TemplateResponse
from app.db.models.usage import UserUsageResponse
from app.db.repositories.template_repository import TemplateRepository
from app.db.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse
from app.services.usage_service import UsageService

router = APIRouter()


class BootstrapData(BaseModel):
    """앱 부팅용 통합 응답"""

    user: UserResponse
    templates: List[TemplateResponse] = Field(default_factory=list)
    usage: UserUsageResponse


@router.get(
    "/bootstrap",
    response_model=BootstrapData,
    summary="앱 부팅 데이터 일괄 조회",
    description="user + templates + usage를 asyncio.gather로 병렬 조회하여 1 RTT로 통합 반환합니다.",
)
@limiter.limit("30/minute")
async def get_bootstrap(
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository_with_rls),
    template_repo: TemplateRepository = Depends(get_template_repository_with_rls),
    usage_service: UsageService = Depends(get_usage_service_with_rls),
):
    """앱 초기 부팅 데이터 병렬 조회"""
    user_id = UUID(current_user["id"])

    # 3개 독립 쿼리를 병렬 실행
    user, templates, usage = await asyncio.gather(
        user_repo.get_by_id(user_id),
        template_repo.get_by_filter(
            TemplateFilter(user_id=user_id, is_active=True)
        ),
        usage_service.get_user_usage_summary(user_id),
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다.",
        )

    response.headers["Cache-Control"] = "private, max-age=10, stale-while-revalidate=60"
    return BootstrapData(user=user, templates=templates, usage=usage)
