"""UserPreference 모델

사용자 설정 데이터 모델 (범용 key-value)
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class UserPreferenceBase(BaseModel):
    """사용자 설정 기본 모델"""
    key: str = Field(..., max_length=100, description="설정 키 (예: 'greeting.preferred_region')")
    value: Any = Field(..., description="설정 값 (JSONB)")


class UserPreferenceCreate(UserPreferenceBase):
    """사용자 설정 생성 모델"""
    user_id: UUID


class UserPreferenceInDB(BaseModel):
    """데이터베이스에서 조회된 사용자 설정 모델"""
    user_id: UUID
    key: str
    value: Any
    updated_at: datetime

    class Config:
        from_attributes = True
