"""User API Endpoints

사용자 프로필 관리 API
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import get_current_user, get_user_repository
from app.db.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse, UserUpdateRequest
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
    user_repo: UserRepository = Depends(get_user_repository),
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
            detail=f"사용자 조회 실패: {str(e)}",
        )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="사용자 정보 조회",
    description="사용자 프로필 정보(원장님 지침 포함)를 조회합니다. (본인만 조회 가능)",
)
async def get_user(
    user_id: UUID,
    current_user: dict = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """특정 사용자 정보 조회 (본인 확인)"""
    # 본인 확인
    if str(user_id) != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="다른 사용자의 정보는 조회할 수 없습니다.",
        )
    
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
            detail=f"사용자 조회 실패: {str(e)}",
        )


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="현재 사용자 계정 삭제",
    description="현재 로그인한 사용자의 계정을 삭제합니다.",
)
async def delete_current_user(
    current_user: dict = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
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
            detail=f"사용자 삭제 실패: {str(e)}",
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
    user_repo: UserRepository = Depends(get_user_repository),
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용자 업데이트 실패: {str(e)}",
        )


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="사용자 정보 업데이트",
    description="사용자의 원장님 지침(Tone & Manner) 등 프로필 정보를 업데이트합니다. (본인만 수정 가능)",
)
async def update_user(
    user_id: UUID,
    request: UserUpdateRequest,
    current_user: dict = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """특정 사용자 정보 업데이트 (본인 확인)"""
    # 본인 확인
    if str(user_id) != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="다른 사용자의 정보는 수정할 수 없습니다.",
        )
    
    update_data = UserUpdate(**request.model_dump(exclude_unset=True))
    
    try:
        updated_user = await user_repo.update(user_id, update_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다.",
            )
        return updated_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용자 업데이트 실패: {str(e)}",
        )
