"""Usage Service
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from uuid import UUID
from typing import Optional

from app.db.repositories.usage_repository import UsageRepository
from app.db.repositories.user_repository import UserRepository
from app.db.models.usage import UserUsageResponse, UsageDetail


class UsageService:
    def __init__(self, usage_repo: UsageRepository, user_repo: UserRepository):
        self.usage_repo = usage_repo
        self.user_repo = user_repo
        self.kst = ZoneInfo("Asia/Seoul")

    def get_now_kst(self) -> datetime:
        """현재 KST 시간 반환"""
        return datetime.now(self.kst)

    async def check_quota_available(self, user_id: UUID, feature_type: str) -> bool:
        """사용 가능한 할당량이 있는지 확인"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return False

        # 1. 플랜에 따른 기준 할당량 가져오기
        plan_name = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)
        quota = await self.usage_repo.get_plan_quota(plan_name, feature_type)
        if not quota:
            return True  # 제한이 설정되지 않은 기능은 일단 허용

        # 2. 현재 사용량 조회 (KST 날짜 기준)
        now_kst = self.get_now_kst()
        usage = await self.usage_repo.get_user_usage(user_id, now_kst.date(), feature_type)
        
        if not usage:
            return True

        # 3. 일일 제한 확인
        if usage.success_count >= quota.daily_limit:
            return False

        return True

    async def increment_usage(self, user_id: UUID, feature_type: str, status: str = "success"):
        """사용량 증가"""
        now_kst = self.get_now_kst()
        await self.usage_repo.increment_usage(user_id, now_kst.date(), feature_type, status)

    async def get_user_usage_summary(self, user_id: UUID) -> UserUsageResponse:
        """사용자 사용량 요약 정보 조회"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다.")

        now_kst = self.get_now_kst()
        today = now_kst.date()
        
        # 내일 자정 KST 계산
        next_reset = datetime(today.year, today.month, today.day, tzinfo=self.kst).replace(hour=0, minute=0, second=0, microsecond=0)
        from datetime import timedelta
        next_reset += timedelta(days=1)

        # 모든 Quota 기준 가져오기
        quotas = await self.usage_repo.get_all_quotas()
        plan_name = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)
        
        feature_summaries = {}
        for quota in quotas:
            if quota.plan_name != plan_name:
                continue
            
            usage = await self.usage_repo.get_user_usage(user_id, today, quota.feature_type)
            used_count = usage.success_count if usage else 0
            
            feature_summaries[quota.feature_type] = UsageDetail(
                used_today=used_count,
                limit_today=quota.daily_limit,
                next_reset_kst=next_reset
            )

        return UserUsageResponse(
            plan=plan_name,
            features=feature_summaries
        )
