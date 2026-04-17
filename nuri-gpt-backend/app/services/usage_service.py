"""Usage Service
"""

import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from uuid import UUID
from typing import List, Optional

from app.db.repositories.usage_repository import UsageRepository
from app.db.repositories.user_repository import UserRepository
from app.db.models.usage import PlanQuotaInDB, UserUsageResponse, UsageDetail


# ── 준정적 데이터 TTL 캐시 ──

class _TTLCache:
    """간단한 인메모리 TTL 캐시 (수 KB 이하 데이터 전용)"""

    def __init__(self, ttl_seconds: int = 300):
        self._ttl = ttl_seconds
        self._data: Optional[List[PlanQuotaInDB]] = None
        self._expires_at: float = 0.0

    def get(self) -> Optional[List[PlanQuotaInDB]]:
        if self._data is not None and time.monotonic() < self._expires_at:
            return self._data
        return None

    def set(self, data: List[PlanQuotaInDB]) -> None:
        self._data = data
        self._expires_at = time.monotonic() + self._ttl

    def invalidate(self) -> None:
        self._data = None
        self._expires_at = 0.0


_quotas_cache = _TTLCache(ttl_seconds=300)  # 5분 TTL


class UsageService:
    def __init__(self, usage_repo: UsageRepository, user_repo: UserRepository):
        self.usage_repo = usage_repo
        self.user_repo = user_repo
        self.kst = ZoneInfo("Asia/Seoul")

    def get_now_kst(self) -> datetime:
        """현재 KST 시간 반환"""
        return datetime.now(self.kst)

    async def _get_all_quotas_cached(self) -> List[PlanQuotaInDB]:
        """할당량 기준을 TTL 캐시와 함께 조회"""
        cached = _quotas_cache.get()
        if cached is not None:
            return cached
        quotas = await self.usage_repo.get_all_quotas()
        _quotas_cache.set(quotas)
        return quotas

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
        """사용자 사용량 요약 정보 조회

        N+1 제거: 기능별 개별 쿼리 대신 오늘자 전체 사용량을 1회 쿼리로 가져와
        메모리에서 기능별 매핑. quotas는 TTL 캐시 적중.
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다.")

        now_kst = self.get_now_kst()
        today = now_kst.date()

        # 내일 자정 KST 계산
        next_reset = datetime(today.year, today.month, today.day, tzinfo=self.kst).replace(hour=0, minute=0, second=0, microsecond=0)
        next_reset += timedelta(days=1)

        # 모든 Quota 기준 (TTL 캐시)
        quotas = await self._get_all_quotas_cached()
        plan_name = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)

        # 오늘자 전체 사용량 1회 쿼리
        today_usages = await self.usage_repo.get_user_usages_by_date(user_id, today)
        usage_by_feature = {u.feature_type: u for u in today_usages}

        feature_summaries = {}
        for quota in quotas:
            if quota.plan_name != plan_name:
                continue

            usage = usage_by_feature.get(quota.feature_type)
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
