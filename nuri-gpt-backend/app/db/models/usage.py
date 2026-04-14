"""Quota 및 Usage 모델
"""

from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class PlanQuotaBase(BaseModel):
    plan_name: str
    feature_type: str
    daily_limit: int
    weekly_limit: Optional[int] = None
    monthly_limit: Optional[int] = None
    is_active: bool = True


class PlanQuotaInDB(PlanQuotaBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserUsageBase(BaseModel):
    user_id: UUID
    usage_date: date
    feature_type: str
    success_count: int = 0
    fail_count: int = 0


class UserUsageCreate(UserUsageBase):
    pass


class UserUsageInDB(UserUsageBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UsageDetail(BaseModel):
    used_today: int
    limit_today: int
    next_reset_kst: datetime


class UserUsageResponse(BaseModel):
    plan: str
    features: dict[str, UsageDetail]
