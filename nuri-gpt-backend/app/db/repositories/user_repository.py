"""User Repository

사용자 CRUD 리포지토리
"""

from typing import List, Optional
from uuid import UUID

from supabase import Client

from app.db.async_wrap import run_sync
from app.db.models.user import UserCreate, UserInDB, UserResponse, UserUpdate


class UserRepository:
    """사용자 데이터 접근 객체"""

    def __init__(self, client: Client):
        self.client = client
        self.table = "users"

    async def create(self, user_data: UserCreate) -> UserResponse:
        """새 사용자 생성"""
        data = user_data.model_dump(exclude_unset=True)
        result = await run_sync(lambda: self.client.table(self.table).insert(data).execute())

        if not result.data:
            raise ValueError("사용자 생성 실패")

        return UserResponse(**result.data[0])

    async def get_by_id(self, user_id: UUID) -> Optional[UserResponse]:
        """ID로 사용자 조회"""
        result = await run_sync(lambda: self.client.table(self.table).select("*").eq("id", str(user_id)).execute())

        if not result.data:
            return None

        return UserResponse(**result.data[0])

    async def get_by_email(self, email: str) -> Optional[UserResponse]:
        """이메일로 사용자 조회"""
        result = await run_sync(lambda: self.client.table(self.table).select("*").eq("email", email).execute())

        if not result.data:
            return None

        return UserResponse(**result.data[0])

    async def update(self, user_id: UUID, user_update: UserUpdate) -> Optional[UserResponse]:
        """사용자 정보 업데이트"""
        data = user_update.model_dump(exclude_unset=True, exclude_none=True)

        if not data:
            return await self.get_by_id(user_id)

        result = await run_sync(lambda: self.client.table(self.table).update(data).eq("id", str(user_id)).execute())

        if not result.data:
            return None

        return UserResponse(**result.data[0])

    async def delete(self, user_id: UUID) -> bool:
        """사용자 삭제"""
        result = await run_sync(lambda: self.client.table(self.table).delete().eq("id", str(user_id)).execute())
        return len(result.data) > 0

    async def update_subscription_status(
        self, user_id: UUID, status: str
    ) -> bool:
        """구독 상태 업데이트"""
        result = await run_sync(lambda: self.client.table(self.table).update({"subscription_status": status}).eq("id", str(user_id)).execute())
        return len(result.data) > 0

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[UserResponse]:
        """모든 사용자 목록 조회"""
        result = await run_sync(lambda: self.client.table(self.table).select("*").range(offset, offset + limit - 1).execute())
        return [UserResponse(**user) for user in result.data]
