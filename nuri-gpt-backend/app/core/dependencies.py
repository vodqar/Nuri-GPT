from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client

from app.core.config import Settings, get_settings
from app.db.connection import get_supabase_admin_client, get_supabase_client
from app.db.repositories.journal_repository import JournalRepository
from app.db.repositories.log_repository import LogRepository
from app.db.repositories.template_repository import TemplateRepository
from app.db.repositories.user_repository import UserRepository
from app.db.repositories.user_preference_repository import UserPreferenceRepository
from app.db.repositories.usage_repository import UsageRepository
from app.services.llm import LlmService
from app.services.vision import VisionService
from app.services.ocr import OcrService
from app.services.storage import StorageService
from app.services.usage_service import UsageService
from app.services.greeting import GreetingService
from app.services.special_day import SpecialDayService
from app.core.jwt_verify import JWTVerificationError, extract_user_from_payload, verify_jwt_locally
from app.utils.exceptions import AuthenticationError

# Bearer 토큰 보안 스키마
security = HTTPBearer(auto_error=False)


def get_config() -> Settings:
    """설정 의존성 주입"""
    return get_settings()


async def get_supabase() -> AsyncGenerator[Client, None]:
    """Supabase 클라이언트 의존성 (인증 전용 — anon key)"""
    client = get_supabase_client()
    yield client


async def get_supabase_admin() -> AsyncGenerator[Client, None]:
    """Supabase 관리자 클라이언트 의존성 (데이터 쓰기 — service_role key, RLS bypass)"""
    client = get_supabase_admin_client()
    yield client


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    supabase: Client = Depends(get_supabase),
) -> dict:
    """현재 인증된 사용자 정보 반환

    - AUTH_LOCAL_VERIFY=true(기본): JWT 로컬 서명 검증 후 클레임에서 사용자 추출
    - 검증 실패 또는 설정 미지원: 원격 Supabase Auth API로 fallback
    """
    if not credentials or not credentials.credentials:
        raise AuthenticationError("인증 토큰이 제공되지 않았습니다")

    token = credentials.credentials
    settings = get_settings()

    # 로컬 JWT 검증 시도
    if settings.auth_local_verify and settings.supabase_jwt_secret:
        try:
            payload = verify_jwt_locally(token)
            return extract_user_from_payload(payload)
        except JWTVerificationError as e:
            # 만료/서명 오류는 즉시 거부 (원격도 동일 결과이므로 fallback 불필요)
            if "만료" in str(e) or "서명" in str(e):
                raise AuthenticationError("유효하지 않은 인증 토큰입니다")
            # 기타 오류(iss 불일치 등)는 원격으로 재시도
            print(f"[AUTH] 로컬 검증 실패, 원격 fallback: {e}")

    # 원격 Supabase Auth API fallback
    try:
        user_response = supabase.auth.get_user(token)

        if not user_response or not user_response.user:
            raise AuthenticationError("유효하지 않은 인증 토큰입니다")

        user = user_response.user

        return {
            "id": user.id,
            "email": user.email or "",
            "metadata": user.user_metadata or {},
        }

    except AuthenticationError:
        raise
    except Exception as e:
        print(f"[AUTH] 토큰 검증 오류: {e}")
        raise AuthenticationError("유효하지 않은 인증 토큰입니다")


async def get_user_repository() -> AsyncGenerator[UserRepository, None]:
    """User 리포지토리 의존성"""
    client = get_supabase_admin_client()
    yield UserRepository(client)


async def get_log_repository() -> AsyncGenerator[LogRepository, None]:
    """Log 리포지토리 의존성"""
    client = get_supabase_admin_client()
    yield LogRepository(client)


async def get_template_repository() -> AsyncGenerator[TemplateRepository, None]:
    """Template 리포지토리 의존성"""
    client = get_supabase_admin_client()
    yield TemplateRepository(client)


async def get_journal_repository() -> AsyncGenerator[JournalRepository, None]:
    """Journal 리포지토리 의존성"""
    client = get_supabase_admin_client()
    yield JournalRepository(client)


async def get_usage_repository() -> AsyncGenerator[UsageRepository, None]:
    """Usage 리포지토리 의존성"""
    client = get_supabase_admin_client()
    yield UsageRepository(client)


async def get_usage_service(
    usage_repo: UsageRepository = Depends(get_usage_repository),
    user_repo: UserRepository = Depends(get_user_repository),
) -> AsyncGenerator[UsageService, None]:
    """Usage 서비스 의존성"""
    yield UsageService(usage_repo, user_repo)


def get_storage_service() -> StorageService:
    """Storage 서비스 의존성"""
    return StorageService()


def get_ocr_service() -> OcrService:
    """OCR 서비스 의존성"""
    return OcrService()


def get_llm_service() -> LlmService:
    """LLM 서비스 의존성"""
    # LlmService 내부에서 get_settings()를 호출하여 API 키를 읽어들임
    return LlmService()


def get_vision_service() -> VisionService:
    """Vision 서비스 의존성"""
    return VisionService()


def get_special_day_service() -> SpecialDayService:
    """SpecialDay 서비스 의존성"""
    return SpecialDayService()


async def get_user_preference_repository() -> AsyncGenerator[UserPreferenceRepository, None]:
    """UserPreference 리포지토리 의존성"""
    client = get_supabase_admin_client()
    yield UserPreferenceRepository(client)


def get_greeting_service() -> GreetingService:
    """Greeting 서비스 의존성"""
    special_day = get_special_day_service()
    return GreetingService(special_day_service=special_day)
