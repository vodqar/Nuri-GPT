"""User Schemas

사용자 관련 API 스키마
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserUpdateRequest(BaseModel):
    """사용자 업데이트 요청 스키마"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    kindergarten_name: Optional[str] = Field(None, max_length=100)
    tone_and_manner: Optional[str] = Field(None, description="원장님 지침 (Tone & Manner)")


class UserResponse(BaseModel):
    """사용자 응답 스키마"""
    id: UUID
    email: EmailStr
    name: str
    kindergarten_name: Optional[str] = None
    tone_and_manner: Optional[str] = None
    subscription_status: str
    subscription_plan: str
    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

