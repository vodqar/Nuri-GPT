"""User API Endpoints

사용자 프로필 관리 API
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Response, status
from app.core.dependencies import get_current_user, get_user_repository_with_rls, get_usage_service_with_rls, get_user_preference_repository_with_rls
from app.db.repositories.user_repository import UserRepository
from app.db.repositories.user_preference_repository import UserPreferenceRepository
from app.services.usage_service import UsageService
from app.schemas.user import UserResponse, UserUpdateRequest
from app.schemas.user_preference import PreferencesResponse, PreferencesUpdateRequest
from app.db.models.usage import UserUsageResponse
from app.db.models.user import UserUpdate

router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
    summary="현재 사용자 정보 조회",
    description="JWT 토큰으로 현재 로그인한 사용자의 프로필 정보를 조회합니다.",
)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository_with_rls),
):
    """현재 인증된 사용자 정보 조회"""
    from uuid import UUID
    user_id = UUID(current_user["id"])
    try:
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다.",
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 조회에 실패했습니다.",
        )


@router.get(
    "/me/usage",
    response_model=UserUsageResponse,
    summary="현재 사용자 사용량 조회",
    description="현재 로그인한 사용자의 일일 할당량 및 사용 현황을 조회합니다.",
)
async def get_current_user_usage(
    response: Response,
    current_user: dict = Depends(get_current_user),
    usage_service: UsageService = Depends(get_usage_service_with_rls),
):
    """현재 인증된 사용자 사용량 조회"""
    user_id = UUID(current_user["id"])
    try:
        usage_summary = await usage_service.get_user_usage_summary(user_id)
        response.headers["Cache-Control"] = "private, max-age=10, stale-while-revalidate=60"
        return usage_summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용량 조회에 실패했습니다.",
        )


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="현재 사용자 계정 삭제",
    description="현재 로그인한 사용자의 계정을 삭제합니다.",
)
async def delete_current_user(
    current_user: dict = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository_with_rls),
) -> None:
    """현재 인증된 사용자 계정 삭제"""
    from uuid import UUID
    user_id = UUID(current_user["id"])
    try:
        deleted = await user_repo.delete(user_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다.",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 삭제에 실패했습니다.",
        )

@router.put(
    "/me",
    response_model=UserResponse,
    summary="현재 사용자 정보 업데이트",
    description="현재 로그인한 사용자의 원장님 지침(Tone & Manner) 등 프로필 정보를 업데이트합니다.",
)
async def update_current_user(
    request: UserUpdateRequest,
    current_user: dict = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository_with_rls),
):
    """현재 인증된 사용자 정보 업데이트"""
    from uuid import UUID
    user_id = UUID(current_user["id"])
    update_data = UserUpdate(**request.model_dump(exclude_unset=True))
    
    try:
        updated_user = await user_repo.update(user_id, update_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다.",
            )
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 정보 업데이트에 실패했습니다.",
        )


@router.get(
    "/me/preferences",
    response_model=PreferencesResponse,
    summary="현재 사용자 설정 조회",
    description="현재 로그인한 사용자의 모든 설정값을 조회합니다.",
)
async def get_current_user_preferences(
    current_user: dict = Depends(get_current_user),
    pref_repo: UserPreferenceRepository = Depends(get_user_preference_repository_with_rls),
):
    """현재 인증된 사용자 설정 조회"""
    user_id = UUID(current_user["id"])
    try:
        preferences = await pref_repo.get_all(user_id)
        return PreferencesResponse(preferences=preferences)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="설정 조회에 실패했습니다.",
        )


@router.patch(
    "/me/preferences",
    response_model=PreferencesResponse,
    summary="현재 사용자 설정 업데이트",
    description="현재 로그인한 사용자의 설정값을 upsert합니다. 복수 키 동시 갱신 가능.",
)
async def update_current_user_preferences(
    request: PreferencesUpdateRequest,
    current_user: dict = Depends(get_current_user),
    pref_repo: UserPreferenceRepository = Depends(get_user_preference_repository_with_rls),
):
    """현재 인증된 사용자 설정 upsert"""
    user_id = UUID(current_user["id"])
    try:
        preferences = await pref_repo.upsert_many(user_id, request.preferences)
        return PreferencesResponse(preferences=preferences)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="설정 업데이트에 실패했습니다.",
        )
