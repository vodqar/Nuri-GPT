"""Template API Endpoints

템플릿 CRUD API 엔드포인트
- POST /templates         : 템플릿 생성 (이미지 선택적)
- GET /templates          : 템플릿 목록 조회
- GET /templates/{id}     : 템플릿 상세 조회
- DELETE /templates/{id} : 템플릿 소프트 삭제
- PATCH /templates/{id}  : 템플릿 정보 수정 (이름 등)
- PUT /templates/order   : 템플릿 순서 일괄 변경
"""

import json
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Response, UploadFile, status
from pydantic import BaseModel

from app.core.dependencies import get_current_user, get_storage_service, get_template_repository_with_rls
from app.db.models.template import TemplateCreate, TemplateResponse, TemplateFilter, TemplateUpdate
from app.db.repositories.template_repository import TemplateRepository
from app.services.storage import StorageService

router = APIRouter()

MAX_STRUCTURE_DEPTH = 5


def _validate_structure_json(data: Dict[str, Any], depth: int = 0) -> None:
    """structure_json 최소 유효성 검증.

    - 빈 dict 거부 (최상위)
    - 최대 depth(MAX_STRUCTURE_DEPTH) 초과 시 거부
    """
    if depth == 0 and not data:
        raise ValueError("structure_json은 최소 1개의 항목을 포함해야 합니다.")
    if depth > MAX_STRUCTURE_DEPTH:
        raise ValueError(f"structure_json의 depth는 최대 {MAX_STRUCTURE_DEPTH}단계까지 허용됩니다.")
    for value in data.values():
        if isinstance(value, dict):
            _validate_structure_json(value, depth + 1)


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


@router.post(
    "/",
    response_model=TemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="템플릿 생성",
    description="structure_json과 선택적 이미지로 템플릿을 생성합니다. 이미지가 없는 경우 수동 입력 트랙으로 처리됩니다.",
)
async def create_template(
    template_name: str = Form(..., min_length=1, max_length=100, description="템플릿 이름"),
    structure_json: str = Form(..., description="계층 구조 JSON 문자열"),
    file: Optional[UploadFile] = None,
    current_user: dict = Depends(get_current_user),
    template_repo: TemplateRepository = Depends(get_template_repository_with_rls),
    storage_service: StorageService = Depends(get_storage_service),
):
    """structure_json + 선택적 이미지로 템플릿 DB 등록"""
    from uuid import UUID as _UUID
    from app.utils.file_validator import FileType, validate_file

    user_id = _UUID(current_user["id"])

    try:
        parsed_structure = json.loads(structure_json)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="structure_json이 유효한 JSON 형식이 아닙니다.",
        )

    try:
        _validate_structure_json(parsed_structure)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="템플릿 구조 JSON 파싱에 실패했습니다.",
        )

    file_storage_path: Optional[str] = None
    if file is not None and file.filename:
        valid, error_msg = await validate_file(file, FileType.TEMPLATE)
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_msg or "유효하지 않은 파일입니다.",
            )
        try:
            storage_result = await storage_service.upload_template(file=file, user_id=user_id)
            file_storage_path = storage_result.file_path
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="파일 저장에 실패했습니다.",
            )

    template_data = TemplateCreate(
        user_id=user_id,
        name=template_name,
        template_type="observation_log",
        structure_json=parsed_structure,
        file_storage_path=file_storage_path,
        is_default=False,
    )

    try:
        return await template_repo.create(template_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="템플릿 등록에 실패했습니다.",
        )


@router.get(
    "/",
    response_model=List[TemplateResponse],
    summary="템플릿 목록 조회",
    description="조건에 맞는 사용자의 템플릿 목록을 조회합니다. 기본적으로 활성화된 템플릿만 반환합니다.",
)
async def get_templates(
    response: Response,
    current_user: dict = Depends(get_current_user),
    template_type: str = Query(None, description="템플릿 타입 필터 (예: observation_log)"),
    is_default: bool = Query(None, description="기본 템플릿 여부 필터"),
    is_active: bool = Query(True, description="활성화된 템플릿만 조회 (기본값 True)"),
    template_repo: TemplateRepository = Depends(get_template_repository_with_rls),
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
    result = await template_repo.get_by_filter(filter_params)
    response.headers["Cache-Control"] = "private, max-age=10, stale-while-revalidate=60"
    return result


@router.get(
    "/{template_id}",
    response_model=TemplateResponse,
    summary="템플릿 상세 조회",
    description="ID로 특정 템플릿의 메타데이터와 청사진 등을 조회합니다.",
)
async def get_template(
    template_id: UUID,
    current_user: dict = Depends(get_current_user),
    template_repo: TemplateRepository = Depends(get_template_repository_with_rls),
):
    """특정 템플릿 조회"""
    template = await template_repo.get_by_id(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"템플릿(ID: {template_id})을 찾을 수 없습니다."
        )
    if str(template.user_id) != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="다른 사용자의 템플릿은 조회할 수 없습니다.",
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
    current_user: dict = Depends(get_current_user),
    template_repo: TemplateRepository = Depends(get_template_repository_with_rls),
):
    """템플릿 소프트 삭제"""
    # 존재 확인
    template = await template_repo.get_by_id(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"템플릿(ID: {template_id})을 찾을 수 없습니다."
        )
    if str(template.user_id) != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="다른 사용자의 템플릿은 삭제할 수 없습니다.",
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
    current_user: dict = Depends(get_current_user),
    template_repo: TemplateRepository = Depends(get_template_repository_with_rls),
):
    """템플릿 정보 수정"""
    # 존재 확인
    template = await template_repo.get_by_id(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"템플릿(ID: {template_id})을 찾을 수 없습니다."
        )
    if str(template.user_id) != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="다른 사용자의 템플릿은 수정할 수 없습니다.",
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
    current_user: dict = Depends(get_current_user),
    template_repo: TemplateRepository = Depends(get_template_repository_with_rls),
):
    """템플릿 순서 일괄 변경"""
    # 각 템플릿 존재 + 소유권 확인
    for item in request.orders:
        template = await template_repo.get_by_id(item.id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"템플릿(ID: {item.id})을 찾을 수 없습니다."
            )
        if str(template.user_id) != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="다른 사용자의 템플릿은 수정할 수 없습니다.",
            )

    orders_data = [{"id": str(item.id), "sort_order": item.sort_order} for item in request.orders]
    updated_count = await template_repo.update_order(orders_data)

    return TemplateOrderResponse(updated_count=updated_count)
