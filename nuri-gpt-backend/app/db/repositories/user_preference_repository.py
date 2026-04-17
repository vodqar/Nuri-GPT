"""UserPreference Repository

사용자 설정 CRUD 리포지토리
"""

from typing import Any, Dict, Optional
from uuid import UUID

from supabase import Client

from app.db.async_wrap import run_sync
from app.db.models.user_preference import UserPreferenceInDB


class UserPreferenceRepository:
    """사용자 설정 데이터 접근 객체"""

    def __init__(self, client: Client):
        self.client = client
        self.table = "user_preferences"

    async def get_all(self, user_id: UUID) -> Dict[str, Any]:
        """사용자의 모든 설정 조회 → {key: value, ...}"""
        result = await run_sync(lambda: (
            self.client.table(self.table)
            .select("key, value")
            .eq("user_id", str(user_id))
            .execute()
        ))
        return {row["key"]: row["value"] for row in result.data}

    async def get(self, user_id: UUID, key: str) -> Optional[Any]:
        """특정 설정 키의 값 조회"""
        result = await run_sync(lambda: (
            self.client.table(self.table)
            .select("value")
            .eq("user_id", str(user_id))
            .eq("key", key)
            .execute()
        ))
        if not result.data:
            return None
        return result.data[0]["value"]

    async def upsert(self, user_id: UUID, key: str, value: Any) -> UserPreferenceInDB:
        """단일 설정 upsert"""
        data = {
            "user_id": str(user_id),
            "key": key,
            "value": value,
        }
        result = await run_sync(lambda: (
            self.client.table(self.table)
            .upsert(data, on_conflict="user_id,key")
            .execute()
        ))
        if not result.data:
            raise ValueError(f"설정 저장 실패: {key}")
        return UserPreferenceInDB(**result.data[0])

    async def upsert_many(self, user_id: UUID, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """복수 설정 upsert → {key: value, ...} 반환"""
        if not preferences:
            return await self.get_all(user_id)

        rows = [
            {"user_id": str(user_id), "key": k, "value": v}
            for k, v in preferences.items()
        ]
        result = await run_sync(lambda: (
            self.client.table(self.table)
            .upsert(rows, on_conflict="user_id,key")
            .execute()
        ))
        if not result.data:
            raise ValueError("설정 저장 실패")
        return {row["key"]: row["value"] for row in result.data}

    async def delete(self, user_id: UUID, key: str) -> bool:
        """특정 설정 키 삭제"""
        result = await run_sync(lambda: (
            self.client.table(self.table)
            .delete()
            .eq("user_id", str(user_id))
            .eq("key", key)
            .execute()
        ))
        return len(result.data) > 0
