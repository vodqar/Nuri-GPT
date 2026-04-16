"""알림장 인삿말 생성 API 스키마"""

from typing import List, Optional

from datetime import date

from pydantic import BaseModel, Field


class GreetingRequest(BaseModel):
    region: str = Field(..., description="시군구 지역명 (예: '광주광역시 북구')")
    target_date: date = Field(..., description="알림장 배포 일자 (YYYY-MM-DD)")
    user_input: Optional[str] = Field(None, description="사용자 직접 입력 요구사항")
    enabled_contexts: List[str] = Field(default_factory=list, description="활성화할 맥락 리스트 (weather, seasonal, holiday, anniversary, sundry)")


class GreetingResponse(BaseModel):
    greeting: str = Field(..., description="생성된 알림장 인삿말")
