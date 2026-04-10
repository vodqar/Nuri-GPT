"""DB 모듈 단위 테스트

순수 모듈 테스트 (외부 의존성 없이)
"""

from datetime import datetime
from uuid import UUID, uuid4

import pytest


def test_user_models():
    """User 모델 테스트"""
    from app.db.models.user import (
        SubscriptionPlan,
        SubscriptionStatus,
        UserCreate,
        UserInDB,
        UserUpdate,
    )

    # UserCreate 테스트
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
    assert user.subscription_status == SubscriptionStatus.TRIAL

    # UserUpdate 테스트
    update_data = {"name": "업데이트된 이름"}
    update = UserUpdate(**update_data)
    assert update.name == "업데이트된 이름"

    # UserInDB 테스트
    user_id = uuid4()
    now = datetime.utcnow()
    db_user_data = {
        "id": user_id,
        "email": "test@example.com",
        "name": "테스트 사용자",
        "kindergarten_name": "테스트 유치원",
        "subscription_status": SubscriptionStatus.ACTIVE,
        "subscription_plan": SubscriptionPlan.PREMIUM,
        "created_at": now,
        "updated_at": now,
    }
    db_user = UserInDB(**db_user_data)
    assert db_user.id == user_id
    assert db_user.subscription_status == SubscriptionStatus.ACTIVE


def test_log_models():
    """Log 모델 테스트"""
    from app.db.models.log import UserLogCreate, UserLogFilter, UserLogInDB

    user_id = uuid4()

    # UserLogCreate 테스트
    log_data = {
        "user_id": user_id,
        "action": "upload_memo",
        "metadata": {"file_name": "test.jpg"},
    }
    log = UserLogCreate(**log_data)
    assert log.user_id == user_id
    assert log.action == "upload_memo"
    assert log.metadata["file_name"] == "test.jpg"

    # UserLogFilter 테스트
    filter_data = {
        "user_id": user_id,
        "action": "upload_memo",
        "limit": 50,
        "offset": 10,
    }
    log_filter = UserLogFilter(**filter_data)
    assert log_filter.user_id == user_id
    assert log_filter.limit == 50
    assert log_filter.offset == 10

    # UserLogInDB 테스트
    log_id = uuid4()
    now = datetime.utcnow()
    db_log_data = {
        "id": log_id,
        "user_id": user_id,
        "action": "generate_log",
        "metadata": {},
        "created_at": now,
    }
    db_log = UserLogInDB(**db_log_data)
    assert db_log.id == log_id


def test_template_models():
    """Template 모델 테스트"""
    from app.db.models.template import (
        TemplateCreate,
        TemplateFilter,
        TemplateInDB,
        TemplateUpdate,
    )

    user_id = uuid4()

    # TemplateCreate 테스트
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
    assert template.is_default is False

    # TemplateUpdate 테스트
    update_data = {"name": "수정된 템플릿", "is_default": True}
    update = TemplateUpdate(**update_data)
    assert update.name == "수정된 템플릿"
    assert update.is_default is True

    # TemplateInDB 테스트
    template_id = uuid4()
    now = datetime.utcnow()
    db_template_data = {
        "id": template_id,
        "user_id": user_id,
        "name": "저장된 템플릿",
        "template_type": "daily_log",
        "xml_structure": {},
        "file_storage_path": "templates/saved.png",
        "is_default": True,
        "created_at": now,
        "updated_at": now,
    }
    db_template = TemplateInDB(**db_template_data)
    assert db_template.id == template_id
    assert db_template.is_default is True


def test_repositories_import():
    """리포지토리 클래스 import 테스트"""
    from app.db.repositories.user_repository import UserRepository
    from app.db.repositories.log_repository import LogRepository
    from app.db.repositories.template_repository import TemplateRepository

    # 클래스가 정의되어 있는지 확인
    assert UserRepository is not None
    assert LogRepository is not None
    assert TemplateRepository is not None


def test_schemas_import():
    """스키마 클래스 import 테스트"""
    from app.schemas.user import (
        UserUpdateRequest,
        UserResponse,
    )

    assert UserUpdateRequest is not None
    assert UserResponse is not None


def test_dependencies_import():
    """의존성 주입 함수 import 테스트"""
    from app.core.dependencies import (
        get_supabase,
        get_user_repository,
        get_log_repository,
        get_template_repository,
    )

    assert get_supabase is not None
    assert get_user_repository is not None
    assert get_log_repository is not None
    assert get_template_repository is not None


def test_db_package_imports():
    """DB 패키지 전체 import 테스트"""
    from app.db.models import (
        UserCreate,
        UserResponse,
        UserLogCreate,
        UserLogResponse,
        TemplateCreate,
        TemplateResponse,
        SubscriptionStatus,
        SubscriptionPlan,
    )
    from app.db.repositories import (
        UserRepository,
        LogRepository,
        TemplateRepository,
    )

    assert UserCreate is not None
    assert UserResponse is not None
    assert UserLogCreate is not None
    assert TemplateCreate is not None
    assert UserRepository is not None
    assert LogRepository is not None
    assert TemplateRepository is not None
