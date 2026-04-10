from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class HealthCheckResponse(BaseModel):
    """헬스체크 응답 모델"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "app_name": "Nuri-GPT",
                "version": "0.1.0",
                "timestamp": "2024-01-01T00:00:00",
                "uptime_seconds": 3600.0
            }
        }
    )

    status: str = Field(default="healthy", description="서버 상태")
    app_name: str = Field(default="Nuri-GPT", description="애플리케이션 이름")
    version: str = Field(default="0.1.0", description="애플리케이션 버전")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="체크 시각 (UTC)")
    uptime_seconds: Optional[float] = Field(default=None, description="서버 가동 시간 (초)")
