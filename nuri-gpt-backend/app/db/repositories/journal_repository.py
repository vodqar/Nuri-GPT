"""Journal Repository

관찰일지 CRUD 리포지토리
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from supabase import Client

from app.db.models.journal import JournalCreate, JournalResponse


class JournalRepository:
    """관찰일지 데이터 접근 객체"""

    def __init__(self, client: Client):
        self.client = client
        self.table = "observation_journals"

    async def create(self, journal_data: JournalCreate) -> JournalResponse:
        """새 관찰일지 생성"""
        data = journal_data.model_dump(mode="json")
        result = self.client.table(self.table).insert(data).execute()

        if not result.data:
            raise ValueError("관찰일지 생성 실패")

        return JournalResponse(**result.data[0])

    async def get_by_id(self, journal_id: UUID) -> Optional[JournalResponse]:
        """ID로 일지 조회"""
        result = self.client.table(self.table).select("*").eq("id", str(journal_id)).execute()

        if not result.data:
            return None

        return JournalResponse(**result.data[0])

    async def get_by_user(
        self, user_id: UUID, limit: int = 100, offset: int = 0
    ) -> List[JournalResponse]:
        """사용자의 일지 목록 조회 (최신순)"""
        result = (
            self.client.table(self.table)
            .select("*")
            .eq("user_id", str(user_id))
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return [JournalResponse(**journal) for journal in result.data]

    async def delete(self, journal_id: UUID) -> bool:
        """일지 삭제"""
        result = self.client.table(self.table).delete().eq("id", str(journal_id)).execute()
        return len(result.data) > 0

    async def get_latest_by_group(
        self, user_id: UUID, limit: int = 100, offset: int = 0
    ) -> List[JournalResponse]:
        """그룹별 최신 버전만 조회 (목록용)"""
        result = (
            self.client.table(self.table)
            .select("*")
            .eq("user_id", str(user_id))
            .eq("is_final", True)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return [JournalResponse(**journal) for journal in result.data]

    async def get_by_group_id(self, group_id: UUID) -> List[JournalResponse]:
        """특정 그룹의 전체 히스토리 조회 (버전 내역)"""
        result = (
            self.client.table(self.table)
            .select("*")
            .eq("group_id", str(group_id))
            .order("version", desc=True)
            .execute()
        )
        return [JournalResponse(**journal) for journal in result.data]

    async def delete_by_group_id(self, group_id: UUID) -> int:
        """그룹 일괄 삭제, 삭제된 레코드 수 반환"""
        result = (
            self.client.table(self.table)
            .delete()
            .eq("group_id", str(group_id))
            .execute()
        )
        return len(result.data)
