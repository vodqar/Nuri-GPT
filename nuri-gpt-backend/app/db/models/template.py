"""Template 모델

템플릿 데이터 모델
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TemplateType(str):
    """템플릿 타입 상수"""
    OBSERVATION_LOG = "observation_log"
    DAILY_LOG = "daily_log"


class TemplateBase(BaseModel):
    """템플릿 기본 모델"""
    user_id: UUID
    name: str = Field(..., min_length=1, max_length=100)
    template_type: str = Field(..., min_length=1, max_length=20)
    structure_json: Dict[str, Any] = Field(default_factory=dict, description="추출된 템플릿 계층 구조 JSON")
    file_storage_path: Optional[str] = Field(default=None, max_length=255)
    is_default: bool = False
    sort_order: int = Field(default=0, description="템플릿 표시 순서")
    is_active: bool = Field(default=True, description="템플릿 활성화 여부")
    last_used_at: Optional[datetime] = Field(default=None, description="마지막 사용 시간")


class TemplateCreate(TemplateBase):
    """템플릿 생성 모델"""
    pass


class TemplateUpdate(BaseModel):
    """템플릿 업데이트 모델"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    structure_json: Optional[Dict[str, Any]] = None
    file_storage_path: Optional[str] = Field(None, min_length=1, max_length=255)
    is_default: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0, description="템플릿 표시 순서")
    is_active: Optional[bool] = Field(None, description="템플릿 활성화 여부")
    last_used_at: Optional[datetime] = Field(None, description="마지막 사용 시간")


class TemplateInDB(TemplateBase):
    """데이터베이스에서 조회된 템플릿 모델"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TemplateResponse(TemplateInDB):
    """API 응답용 템플릿 모델"""
    pass


class TemplateFilter(BaseModel):
    """템플릿 조회 필터 모델"""
    user_id: Optional[UUID] = None
    template_type: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = Field(default=True, description="활성화된 템플릿만 조회 (기본값 True)")
