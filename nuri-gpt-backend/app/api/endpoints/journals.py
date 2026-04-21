"""Journal API Endpoints

관찰일지 조회 엔드포인트
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.core.dependencies import get_current_user, get_journal_repository_with_rls
from app.db.models.journal import JournalListResponse, JournalResponse
from app.db.repositories.journal_repository import JournalRepository

router = APIRouter()


@router.get("", response_model=JournalListResponse)
async def list_journals(
    response: Response,
    current_user: dict = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    journal_repository: JournalRepository = Depends(get_journal_repository_with_rls),
) -> JournalListResponse:
    """현재 사용자의 관찰일지 목록 조회 (그룹별 최신 버전만, 최신순)"""
    from uuid import UUID
    user_id = UUID(current_user["id"])
    journals = await journal_repository.get_latest_by_group(
        user_id=user_id, limit=limit, offset=offset
    )

    response.headers["Cache-Control"] = "private, max-age=5, stale-while-revalidate=30"
    return JournalListResponse(
        items=journals,
        total=len(journals),
        limit=limit,
        offset=offset,
    )


@router.get("/{journal_id}", response_model=JournalResponse)
async def get_journal(
    journal_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    journal_repository: JournalRepository = Depends(get_journal_repository_with_rls),
) -> JournalResponse:
    """특정 관찰일지 상세 조회"""
    journal = await journal_repository.get_by_id(journal_id)

    if not journal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"일지(ID: {journal_id})를 찾을 수 없습니다.",
        )

    if str(journal.user_id) != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="다른 사용자의 일지는 조회할 수 없습니다.",
        )

    return journal


@router.get("/group/{group_id}", response_model=List[JournalResponse])
async def get_journal_group_history(
    group_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    journal_repository: JournalRepository = Depends(get_journal_repository_with_rls),
) -> List[JournalResponse]:
    """특정 그룹의 전체 재생성 이력(버전 내역) 조회"""
    journals = await journal_repository.get_by_group_id(group_id)

    if journals and str(journals[0].user_id) != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="다른 사용자의 일지는 조회할 수 없습니다.",
        )

    return journals


@router.delete("/group/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_journal_group(
    group_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    journal_repository: JournalRepository = Depends(get_journal_repository_with_rls),
) -> None:
    """재생성 기록(그룹) 전체 일괄 삭제"""
    # 소유권 확인: 그룹 내 일지가 현재 사용자 것인지 검증
    journals = await journal_repository.get_by_group_id(group_id)
    if not journals:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"그룹(ID: {group_id})을 찾을 수 없거나 삭제할 항목이 없습니다.",
        )
    if str(journals[0].user_id) != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="다른 사용자의 일지는 삭제할 수 없습니다.",
        )

    deleted_count = await journal_repository.delete_by_group_id(group_id)

    if deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"그룹(ID: {group_id})을 찾을 수 없거나 삭제할 항목이 없습니다.",
        )
