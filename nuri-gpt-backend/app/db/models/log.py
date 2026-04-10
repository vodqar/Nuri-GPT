"""UserLog 모델

사용자 활동 로그 데이터 모델
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class UserAction(str):
    """사용자 액션 상수"""
    UPLOAD_MEMO = "upload_memo"
    UPLOAD_TEMPLATE = "upload_template"
    GENERATE_LOG = "generate_log"
    LOGIN = "login"
    LOGOUT = "logout"
    UPDATE_PROFILE = "update_profile"


class UserLogBase(BaseModel):
    """사용자 로그 기본 모델"""
    user_id: UUID
    action: str = Field(..., min_length=1, max_length=50)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class UserLogCreate(UserLogBase):
    """사용자 로그 생성 모델"""
    pass


class UserLogInDB(UserLogBase):
    """데이터베이스에서 조회된 로그 모델"""
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class UserLogResponse(UserLogInDB):
    """API 응답용 로그 모델"""
    pass


class UserLogFilter(BaseModel):
    """로그 조회 필터 모델"""
    user_id: Optional[UUID] = None
    action: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
