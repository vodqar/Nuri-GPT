"""Log Repository

사용자 활동 로그 CRUD 리포지토리
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from supabase import Client

from app.db.models.log import UserLogCreate, UserLogFilter, UserLogResponse


class LogRepository:
    """사용자 로그 데이터 접근 객체"""

    def __init__(self, client: Client):
        self.client = client
        self.table = "user_logs"

    async def create(self, log_data: UserLogCreate) -> UserLogResponse:
        """새 로그 생성"""
        data = log_data.model_dump(mode="json")
        result = self.client.table(self.table).insert(data).execute()

        if not result.data:
            raise ValueError("로그 생성 실패")

        return UserLogResponse(**result.data[0])

    async def log_action(
        self, user_id: UUID, action: str, metadata: Optional[Dict[str, Any]] = None
    ) -> UserLogResponse:
        """사용자 액션 로깅 (간편 메서드)"""
        log_data = UserLogCreate(
            user_id=user_id,
            action=action,
            metadata=metadata or {},
        )
        return await self.create(log_data)

    async def get_by_id(self, log_id: UUID) -> Optional[UserLogResponse]:
        """ID로 로그 조회"""
        result = self.client.table(self.table).select("*").eq("id", str(log_id)).execute()

        if not result.data:
            return None

        return UserLogResponse(**result.data[0])

    async def get_by_user(
        self, user_id: UUID, limit: int = 100, offset: int = 0
    ) -> List[UserLogResponse]:
        """사용자의 로그 목록 조회"""
        result = (
            self.client.table(self.table)
            .select("*")
            .eq("user_id", str(user_id))
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return [UserLogResponse(**log) for log in result.data]

    async def get_by_filter(self, filter_params: UserLogFilter) -> List[UserLogResponse]:
        """필터 조건으로 로그 조회"""
        query = self.client.table(self.table).select("*")

        if filter_params.user_id:
            query = query.eq("user_id", str(filter_params.user_id))

        if filter_params.action:
            query = query.eq("action", filter_params.action)

        if filter_params.start_date:
            query = query.gte("created_at", filter_params.start_date.isoformat())

        if filter_params.end_date:
            query = query.lte("created_at", filter_params.end_date.isoformat())

        result = (
            query.order("created_at", desc=True)
            .range(filter_params.offset, filter_params.offset + filter_params.limit - 1)
            .execute()
        )
        return [UserLogResponse(**log) for log in result.data]

    async def delete_by_user(self, user_id: UUID) -> bool:
        """사용자의 모든 로그 삭제"""
        result = self.client.table(self.table).delete().eq("user_id", str(user_id)).execute()
        return len(result.data) > 0
