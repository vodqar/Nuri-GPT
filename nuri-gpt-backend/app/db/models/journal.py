"""Journal Models

관찰일지 데이터 모델
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class JournalBase(BaseModel):
    """관찰일지 기본 모델"""
    user_id: UUID
    group_id: UUID = Field(default_factory=uuid.uuid4)
    version: int = Field(default=1)
    is_final: bool = Field(default=True)
    title: Optional[str] = None
    observation_content: Optional[str] = None
    evaluation_content: Optional[str] = None
    development_areas: Optional[List[str]] = Field(default_factory=list)
    template_id: Optional[UUID] = None
    template_mapping: Optional[Dict[str, Any]] = Field(default_factory=dict)
    semantic_json: Optional[Dict[str, Any]] = Field(default_factory=dict)
    updated_activities: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    source_type: Optional[str] = None
    ocr_text: Optional[str] = None
    additional_guidelines: Optional[str] = None


class JournalCreate(JournalBase):
    """관찰일지 생성 모델"""
    pass


class JournalInDB(JournalBase):
    """데이터베이스에서 조회된 일지 모델"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JournalResponse(JournalInDB):
    """API 응답용 일지 모델"""
    pass


class JournalListResponse(BaseModel):
    """일지 목록 응답"""
    items: List[JournalResponse]
    total: int
    limit: int
    offset: int
