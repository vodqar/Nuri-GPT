from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 설정 관리"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 앱 기본 정보
    app_name: str = Field(default="Nuri-GPT", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")

    # 서버 설정
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # Supabase 설정
    supabase_url: Optional[str] = Field(default=None, alias="SUPABASE_URL")
    supabase_key: Optional[str] = Field(default=None, alias="SUPABASE_KEY")
    supabase_service_key: Optional[str] = Field(default=None, alias="SUPABASE_SERVICE_KEY")
    supabase_jwt_secret: Optional[str] = Field(default=None, alias="SUPABASE_JWT_SECRET")

    # Auth 로컬 검증 설정
    auth_local_verify: bool = Field(default=True, alias="AUTH_LOCAL_VERIFY")

    # Gemini API 설정
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")

    # Dify API 설정
    dify_api_key: Optional[str] = Field(default=None, alias="DIFY_API_KEY")
    dify_api_url: str = Field(default="https://dify.vodqar.com/v1", alias="DIFY_API_URL")

    # Dify 재생성 API 설정 (미설정 시 기본값 사용)
    dify_regenerate_api_key: Optional[str] = Field(default=None, alias="DIFY_REGENERATE_API_KEY")
    dify_regenerate_api_url: Optional[str] = Field(default=None, alias="DIFY_REGENERATE_API_URL")

    # 기상청 단기예보 API (apihub.kma.go.kr — authKey)
    kma_api_key: Optional[str] = Field(default=None, alias="KMA_API_KEY")

    # 기상청 중기예보 API (apis.data.go.kr — serviceKey)
    kma_mid_api_key: Optional[str] = Field(default=None, alias="KMA_MID_API_KEY")

    # 한국천문연구원 특일 정보 API (apis.data.go.kr — serviceKey)
    kma_special_day_api_key: Optional[str] = Field(default=None, alias="KMA_SPECIAL_DAY_API_KEY")

    # Dify 인삿말 생성용 Chatflow
    dify_greeting_api_key: Optional[str] = Field(default=None, alias="DIFY_GREETING_API_KEY")
    dify_greeting_api_url: Optional[str] = Field(default=None, alias="DIFY_GREETING_API_URL")

    # LLM 모델 설정
    llm_vision_model: str = Field(default="gemini-3-flash", alias="LLM_VISION_MODEL")
    llm_vision_temperature: float = Field(default=0.2, alias="LLM_VISION_TEMPERATURE")
    llm_vision_thinking_level: str = Field(default="default", alias="LLM_VISION_THINKING_LEVEL")
    llm_text_model: str = Field(default="gemini-2.5-flash", alias="LLM_TEXT_MODEL")
    llm_text_temperature: float = Field(default=0.2, alias="LLM_TEXT_TEMPERATURE")
    llm_text_thinking_level: str = Field(default="default", alias="LLM_TEXT_THINKING_LEVEL")

    # OCR LLM 설정
    llm_ocr_model: str = Field(default="gemini-3.1-flash-lite-preview", alias="LLM_OCR_MODEL")
    llm_ocr_temperature: float = Field(default=1.0, alias="LLM_OCR_TEMPERATURE")
    llm_ocr_thinking_level: str = Field(default="medium", alias="LLM_OCR_THINKING_LEVEL")

    # CORS 설정
    cors_origins: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
            "http://127.0.0.1:44557",
        ],
        alias="CORS_ORIGINS"
    )

    @property
    def supabase_issuer(self) -> Optional[str]:
        """Supabase JWT iss 클레임값 (URL + /auth/v1)"""
        if self.supabase_url:
            return f"{self.supabase_url}/auth/v1"
        return None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 문자열로 들어온 cors_origins 파싱
        if isinstance(self.cors_origins, str):
            self.cors_origins = [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    """설정 인스턴스를 싱글톤으로 반환"""
    return Settings()
