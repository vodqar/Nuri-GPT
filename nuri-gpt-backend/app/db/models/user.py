"""User 모델

사용자 데이터 모델
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    """사용자 역할 열거형"""
    ADMIN = "admin"
    ORG_MANAGER = "org_manager"
    USER = "user"


class SubscriptionStatus(str, Enum):
    """구독 상태 열거형"""
    TRIAL = "trial"
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class SubscriptionPlan(str, Enum):
    """구독 플랜 열거형"""
    BASIC = "basic"
    PREMIUM = "premium"


class UserBase(BaseModel):
    """사용자 기본 모델"""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    kindergarten_name: Optional[str] = Field(None, max_length=100)
    preferred_region: Optional[str] = Field(None, description="선호하는 지역명 (예: '서울특별시 강남구')")
    tone_and_manner: Optional[str] = Field(None, description="원장님 지침 (Tone & Manner)")
    role: UserRole = UserRole.USER


class UserCreate(UserBase):
    """사용자 생성 모델"""
    id: Optional[UUID] = None  # Supabase Auth에서 생성된 UUID
    subscription_status: SubscriptionStatus = SubscriptionStatus.TRIAL
    subscription_plan: SubscriptionPlan = SubscriptionPlan.BASIC
    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None


class UserUpdate(BaseModel):
    """사용자 업데이트 모델"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    kindergarten_name: Optional[str] = Field(None, max_length=100)
    preferred_region: Optional[str] = None
    tone_and_manner: Optional[str] = None
    role: Optional[UserRole] = None
    subscription_status: Optional[SubscriptionStatus] = None
    subscription_plan: Optional[SubscriptionPlan] = None
    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None


class UserInDB(UserBase):
    """데이터베이스에서 조회된 사용자 모델"""
    id: UUID
    subscription_status: SubscriptionStatus
    subscription_plan: SubscriptionPlan
    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserResponse(UserInDB):
    """API 응답용 사용자 모델"""
    pass
