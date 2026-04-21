import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.db.models.template import TemplateResponse, TemplateFilter
from app.core.dependencies import get_template_repository_with_rls, get_current_user

client = TestClient(app)

MOCK_USER_ID_STR = "00000000-0000-0000-0000-000000000001"
MOCK_USER_ID = uuid4()  # will be overwritten below

@pytest.fixture
def mock_template_repo():
    from uuid import UUID
    uid = UUID(MOCK_USER_ID_STR)
    repo = MagicMock()
    mock_template_1 = TemplateResponse(
        id=uuid4(),
        user_id=uid,
        name="템플릿 1",
        template_type="observation_log",
        structure_json={"보육일지": {"놀이": {"활동": {"내용": ""}}}},
        file_storage_path="templates/test/1.png",
        is_default=True,
        sort_order=0,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    mock_template_2 = TemplateResponse(
        id=uuid4(),
        user_id=uid,
        name="템플릿 2",
        template_type="daily_log",
        structure_json={"일지": {"내용": ""}},
        file_storage_path="templates/test/2.png",
        is_default=False,
        sort_order=1,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    # get_by_filter mock
    repo.get_by_filter = AsyncMock(return_value=[mock_template_1, mock_template_2])
    
    # get_by_id mock
    repo.get_by_id = AsyncMock(return_value=mock_template_1)
    
    # soft_delete mock
    repo.soft_delete = AsyncMock(return_value=True)
    
    # update mock
    repo.update = AsyncMock(return_value=mock_template_1)
    
    # update_order mock
    repo.update_order = AsyncMock(return_value=2)
    
    return repo

@pytest.fixture
def mock_current_user():
    return {
        "id": "00000000-0000-0000-0000-000000000001",
        "email": "test@example.com",
        "metadata": {"name": "Test User"}
    }

def test_get_templates(mock_template_repo, mock_current_user):
    app.dependency_overrides[get_template_repository_with_rls] = lambda: mock_template_repo
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    
    response = client.get("/api/templates/")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "템플릿 1"
    assert data[1]["name"] == "템플릿 2"
    
    # 검증: repo가 필터와 함께 호출되었는지
    mock_template_repo.get_by_filter.assert_called_once()
    filter_arg = mock_template_repo.get_by_filter.call_args[0][0]
    assert str(filter_arg.user_id) == mock_current_user["id"]
    
    app.dependency_overrides.clear()

def test_get_template_by_id(mock_template_repo, mock_current_user):
    app.dependency_overrides[get_template_repository_with_rls] = lambda: mock_template_repo
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    
    template_id = str(uuid4())
    response = client.get(f"/api/templates/{template_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "템플릿 1"
    
    mock_template_repo.get_by_id.assert_called_once()
    
    app.dependency_overrides.clear()

def test_get_template_not_found(mock_current_user):
    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=None)
    app.dependency_overrides[get_template_repository_with_rls] = lambda: repo
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    
    response = client.get(f"/api/templates/{uuid4()}")
    
    assert response.status_code == 404
    assert "템플릿" in response.json()["detail"] or "not found" in response.json()["detail"].lower()
    
    app.dependency_overrides.clear()


# ============================================
# 새 API 테스트
# ============================================

def test_delete_template(mock_template_repo, mock_current_user):
    """템플릿 소프트 삭제 테스트"""
    app.dependency_overrides[get_template_repository_with_rls] = lambda: mock_template_repo
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    
    template_id = str(uuid4())
    response = client.delete(f"/api/templates/{template_id}")
    
    assert response.status_code == 204
    mock_template_repo.soft_delete.assert_called_once()
    
    app.dependency_overrides.clear()


def test_delete_template_not_found(mock_current_user):
    """존재하지 않는 템플릿 삭제 테스트"""
    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=None)
    app.dependency_overrides[get_template_repository_with_rls] = lambda: repo
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    
    response = client.delete(f"/api/templates/{uuid4()}")
    
    assert response.status_code == 404
    
    app.dependency_overrides.clear()


def test_patch_template(mock_template_repo, mock_current_user):
    """템플릿 이름 변경 테스트"""
    app.dependency_overrides[get_template_repository_with_rls] = lambda: mock_template_repo
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    
    template_id = str(uuid4())
    response = client.patch(
        f"/api/templates/{template_id}",
        json={"name": "새 템플릿 이름"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "템플릿 1"  # mock이 반환하는 값
    
    mock_template_repo.update.assert_called_once()
    
    app.dependency_overrides.clear()


def test_patch_template_not_found(mock_current_user):
    """존재하지 않는 템플릿 수정 테스트"""
    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=None)
    app.dependency_overrides[get_template_repository_with_rls] = lambda: repo
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    
    response = client.patch(
        f"/api/templates/{uuid4()}",
        json={"name": "새 이름"}
    )
    
    assert response.status_code == 404
    
    app.dependency_overrides.clear()


def test_put_template_order(mock_template_repo, mock_current_user):
    """템플릿 순서 일괄 변경 테스트"""
    app.dependency_overrides[get_template_repository_with_rls] = lambda: mock_template_repo
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    
    template_id_1 = str(uuid4())
    template_id_2 = str(uuid4())
    
    response = client.put(
        "/api/templates/order",
        json={
            "orders": [
                {"id": template_id_1, "sort_order": 1},
                {"id": template_id_2, "sort_order": 2}
            ]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["updated_count"] == 2
    
    mock_template_repo.update_order.assert_called_once()
    
    app.dependency_overrides.clear()


def test_put_template_order_not_found(mock_current_user):
    """존재하지 않는 템플릿 순서 변경 테스트"""
    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=None)
    app.dependency_overrides[get_template_repository_with_rls] = lambda: repo
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    
    response = client.put(
        "/api/templates/order",
        json={
            "orders": [
                {"id": str(uuid4()), "sort_order": 1}
            ]
        }
    )
    
    assert response.status_code == 404
    
    app.dependency_overrides.clear()
