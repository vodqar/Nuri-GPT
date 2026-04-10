"""DB 모듈 테스트

Supabase DB 연결 및 리포지토리 테스트
"""

import os
from datetime import datetime
from uuid import UUID, uuid4

import pytest
from pydantic import EmailStr

# 환경 변수가 없으면 테스트 건너뛰기 위한 마커
pytestmark = pytest.mark.skipif(
    not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"),
    reason="SUPABASE_URL과 SUPABASE_KEY 환경 변수가 필요합니다",
)

from app.db.connection import SupabaseManager, get_supabase_client
from app.db.models.log import UserLogCreate
from app.db.models.template import TemplateCreate
from app.db.models.user import SubscriptionPlan, SubscriptionStatus, UserCreate
from app.db.repositories.log_repository import LogRepository
from app.db.repositories.template_repository import TemplateRepository
from app.db.repositories.user_repository import UserRepository


class TestSupabaseConnection:
    """Supabase 연결 테스트"""

    def test_singleton_pattern(self):
        """싱글톤 패턴 테스트"""
        manager1 = SupabaseManager()
        manager2 = SupabaseManager()
        assert manager1 is manager2

    def test_client_initialization(self):
        """클라이언트 초기화 테스트"""
        client = get_supabase_client()
        assert client is not None

    @pytest.mark.asyncio
    async def test_health_check(self):
        """헬스체크 테스트"""
        manager = SupabaseManager()
        result = await manager.health_check()
        assert isinstance(result, bool)


class TestUserModels:
    """User 모델 테스트"""

    def test_user_create(self):
        """UserCreate 모델 테스트"""
        user_data = {
            "email": "test@example.com",
            "name": "테스트 사용자",
            "kindergarten_name": "테스트 유치원",
            "subscription_status": SubscriptionStatus.TRIAL,
            "subscription_plan": SubscriptionPlan.BASIC,
        }
        user = UserCreate(**user_data)
        assert user.email == "test@example.com"
        assert user.name == "테스트 사용자"
        assert user.kindergarten_name == "테스트 유치원"
        assert user.subscription_status == SubscriptionStatus.TRIAL
        assert user.subscription_plan == SubscriptionPlan.BASIC

    def test_user_response(self):
        """UserResponse 모델 테스트"""
        user_id = uuid4()
        now = datetime.utcnow()
        user_data = {
            "id": user_id,
            "email": "test@example.com",
            "name": "테스트 사용자",
            "kindergarten_name": "테스트 유치원",
            "subscription_status": SubscriptionStatus.ACTIVE,
            "subscription_plan": SubscriptionPlan.PREMIUM,
            "subscription_start_date": now,
            "subscription_end_date": now,
            "created_at": now,
            "updated_at": now,
        }
        # UserInDB는 UserResponse의 부모 클래스
        from app.db.models.user import UserInDB
        user = UserInDB(**user_data)
        assert user.id == user_id
        assert user.subscription_status == SubscriptionStatus.ACTIVE


class TestUserRepository:
    """User 리포지토리 테스트"""

    @pytest.fixture
    async def user_repo(self):
        """UserRepository 픽스처"""
        client = get_supabase_client()
        return UserRepository(client)

    @pytest.mark.asyncio
    async def test_get_by_email_not_found(self, user_repo):
        """존재하지 않는 이메일 조회 테스트"""
        result = await user_repo.get_by_email("nonexistent@example.com")
        assert result is None


class TestLogModels:
    """Log 모델 테스트"""

    def test_user_log_create(self):
        """UserLogCreate 모델 테스트"""
        user_id = uuid4()
        log_data = {
            "user_id": user_id,
            "action": "upload_memo",
            "metadata": {"file_name": "test.jpg"},
        }
        log = UserLogCreate(**log_data)
        assert log.user_id == user_id
        assert log.action == "upload_memo"
        assert log.metadata["file_name"] == "test.jpg"


class TestTemplateModels:
    """Template 모델 테스트"""

    def test_template_create(self):
        """TemplateCreate 모델 테스트"""
        user_id = uuid4()
        template_data = {
            "user_id": user_id,
            "name": "관찰일지 템플릿",
            "template_type": "observation_log",
            "xml_structure": {"root": {"element": "value"}},
            "file_storage_path": "templates/test.png",
            "is_default": False,
        }
        template = TemplateCreate(**template_data)
        assert template.name == "관찰일지 템플릿"
        assert template.template_type == "observation_log"
        assert template.is_default is False


class TestDependencies:
    """의존성 주입 테스트"""

    @pytest.mark.asyncio
    async def test_get_supabase_dependency(self):
        """Supabase 의존성 테스트"""
        from app.core.dependencies import get_supabase

        async for client in get_supabase():
            assert client is not None
            break

    @pytest.mark.asyncio
    async def test_get_user_repository_dependency(self):
        """User 리포지토리 의존성 테스트"""
        from app.core.dependencies import get_user_repository

        async for repo in get_user_repository():
            assert isinstance(repo, UserRepository)
            break

    @pytest.mark.asyncio
    async def test_get_log_repository_dependency(self):
        """Log 리포지토리 의존성 테스트"""
        from app.core.dependencies import get_log_repository

        async for repo in get_log_repository():
            assert isinstance(repo, LogRepository)
            break

    @pytest.mark.asyncio
    async def test_get_template_repository_dependency(self):
        """Template 리포지토리 의존성 테스트"""
        from app.core.dependencies import get_template_repository

        async for repo in get_template_repository():
            assert isinstance(repo, TemplateRepository)
            break
