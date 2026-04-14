"""Usage Repository
"""

from datetime import date
from typing import List, Optional
from uuid import UUID
from supabase import Client
from app.db.models.usage import UserUsageInDB, PlanQuotaInDB


class UsageRepository:
    def __init__(self, client: Client):
        self.client = client
        self.usage_table = "user_usages"
        self.quota_table = "plan_quotas"

    async def get_plan_quota(self, plan_name: str, feature_type: str) -> Optional[PlanQuotaInDB]:
        """특정 플랜의 기능별 할당량 조회"""
        result = self.client.table(self.quota_table) \
            .select("*") \
            .eq("plan_name", plan_name) \
            .eq("feature_type", feature_type) \
            .eq("is_active", True) \
            .execute()

        if not result.data:
            return None
        return PlanQuotaInDB(**result.data[0])

    async def get_user_usage(self, user_id: UUID, usage_date: date, feature_type: str) -> Optional[UserUsageInDB]:
        """사용자의 특정 날짜/기능 사용량 조회"""
        result = self.client.table(self.usage_table) \
            .select("*") \
            .eq("user_id", str(user_id)) \
            .eq("usage_date", usage_date.isoformat()) \
            .eq("feature_type", feature_type) \
            .execute()

        if not result.data:
            return None
        return UserUsageInDB(**result.data[0])

    async def increment_usage(self, user_id: UUID, usage_date: date, feature_type: str, status: str = "success") -> UserUsageInDB:
        """사용량 카운트 증가 (Upsert)"""
        count_field = "success_count" if status == "success" else "fail_count"
        
        # current usage 조회
        current = await self.get_user_usage(user_id, usage_date, feature_type)
        
        if current:
            # Update
            new_val = (current.success_count + 1) if status == "success" else (current.fail_count + 1)
            result = self.client.table(self.usage_table) \
                .update({count_field: new_val, "updated_at": "now()"}) \
                .eq("id", str(current.id)) \
                .execute()
        else:
            # Insert
            data = {
                "user_id": str(user_id),
                "usage_date": usage_date.isoformat(),
                "feature_type": feature_type,
                "success_count": 1 if status == "success" else 0,
                "fail_count": 1 if status == "fail" else 0
            }
            result = self.client.table(self.usage_table).insert(data).execute()

        if not result.data:
            raise ValueError("사용량 업데이트 실패")
            
        return UserUsageInDB(**result.data[0])

    async def get_all_quotas(self) -> List[PlanQuotaInDB]:
        """모든 활성화된 할당량 기준 조회"""
        result = self.client.table(self.quota_table).select("*").eq("is_active", True).execute()
        return [PlanQuotaInDB(**q) for q in result.data]
