"""Template API Endpoints

템플릿 CRUD API 엔드포인트
- GET /templates          : 템플릿 목록 조회
- GET /templates/{id}     : 템플릿 상세 조회
- DELETE /templates/{id} : 템플릿 소프트 삭제
- PATCH /templates/{id}  : 템플릿 정보 수정 (이름 등)
- PUT /templates/order   : 템플릿 순서 일괄 변경
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.core.dependencies import get_current_user, get_template_repository
from app.db.repositories.template_repository import TemplateRepository
from app.db.models.template import TemplateResponse, TemplateFilter, TemplateUpdate

router = APIRouter()


class TemplateOrderItem(BaseModel):
    """템플릿 순서 항목"""
    id: UUID
    sort_order: int


class TemplateOrderRequest(BaseModel):
    """템플릿 순서 변경 요청"""
    orders: List[TemplateOrderItem]


class TemplateOrderResponse(BaseModel):
    """템플릿 순서 변경 응답"""
    updated_count: int


@router.get(
    "/",
    response_model=List[TemplateResponse],
    summary="템플릿 목록 조회",
    description="조건에 맞는 사용자의 템플릿 목록을 조회합니다. 기본적으로 활성화된 템플릿만 반환합니다.",
)
async def get_templates(
    current_user: dict = Depends(get_current_user),
    template_type: str = Query(None, description="템플릿 타입 필터 (예: observation_log)"),
    is_default: bool = Query(None, description="기본 템플릿 여부 필터"),
    is_active: bool = Query(True, description="활성화된 템플릿만 조회 (기본값 True)"),
    template_repo: TemplateRepository = Depends(get_template_repository),
):
    """조건에 맞는 템플릿 목록 조회"""
    from uuid import UUID
    user_id = UUID(current_user["id"])
    filter_params = TemplateFilter(
        user_id=user_id,
        template_type=template_type,
        is_default=is_default,
        is_active=is_active
    )
    return await template_repo.get_by_filter(filter_params)


@router.get(
    "/{template_id}",
    response_model=TemplateResponse,
    summary="템플릿 상세 조회",
    description="ID로 특정 템플릿의 메타데이터와 청사진 등을 조회합니다.",
)
async def get_template(
    template_id: UUID,
    template_repo: TemplateRepository = Depends(get_template_repository),
):
    """특정 템플릿 조회"""
    template = await template_repo.get_by_id(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"템플릿(ID: {template_id})을 찾을 수 없습니다."
        )
    return template


@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="템플릿 삭제",
    description="템플릿을 소프트 삭제합니다 (is_active=False). 실제 데이터는 유지됩니다.",
)
async def delete_template(
    template_id: UUID,
    template_repo: TemplateRepository = Depends(get_template_repository),
):
    """템플릿 소프트 삭제"""
    # 존재 확인
    template = await template_repo.get_by_id(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"템플릿(ID: {template_id})을 찾을 수 없습니다."
        )

    success = await template_repo.soft_delete(template_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="템플릿 삭제에 실패했습니다."
        )


@router.patch(
    "/{template_id}",
    response_model=TemplateResponse,
    summary="템플릿 정보 수정",
    description="템플릿의 이름 등 정보를 수정합니다.",
)
async def update_template(
    template_id: UUID,
    update_data: TemplateUpdate,
    template_repo: TemplateRepository = Depends(get_template_repository),
):
    """템플릿 정보 수정"""
    # 존재 확인
    template = await template_repo.get_by_id(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"템플릿(ID: {template_id})을 찾을 수 없습니다."
        )

    updated = await template_repo.update(template_id, update_data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="템플릿 수정에 실패했습니다."
        )
    return updated


@router.put(
    "/order",
    response_model=TemplateOrderResponse,
    summary="템플릿 순서 일괄 변경",
    description="여러 템플릿의 표시 순서를 일괄 변경합니다.",
)
async def update_template_order(
    request: TemplateOrderRequest,
    template_repo: TemplateRepository = Depends(get_template_repository),
):
    """템플릿 순서 일괄 변경"""
    # 각 템플릿 존재 확인
    for item in request.orders:
        template = await template_repo.get_by_id(item.id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"템플릿(ID: {item.id})을 찾을 수 없습니다."
            )

    orders_data = [{"id": str(item.id), "sort_order": item.sort_order} for item in request.orders]
    updated_count = await template_repo.update_order(orders_data)

    return TemplateOrderResponse(updated_count=updated_count)
