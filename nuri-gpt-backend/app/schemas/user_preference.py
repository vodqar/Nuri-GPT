"""UserPreference Schemas

사용자 설정 API 스키마
"""

from typing import Any, Dict

from pydantic import BaseModel, Field


class PreferencesResponse(BaseModel):
    """사용자 설정 조회 응답 스키마"""
    preferences: Dict[str, Any] = Field(default_factory=dict, description="설정 키-값 맵")


class PreferencesUpdateRequest(BaseModel):
    """사용자 설정 업데이트 요청 스키마"""
    preferences: Dict[str, Any] = Field(..., description="업데이트할 설정 키-값 맵")
