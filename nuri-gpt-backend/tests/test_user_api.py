import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.user import UserResponse
from app.core.dependencies import get_user_repository, get_current_user

client = TestClient(app)


@pytest.fixture
def mock_user_repo():
    repo = MagicMock()
    mock_user = UserResponse(
        id=uuid4(),
        email="teacher@example.com",
        name="테스트 교사",
        kindergarten_name="누리유치원",
        tone_and_manner="따뜻하고 구체적으로 작성",
        subscription_status="active",
        subscription_plan="basic",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    repo.get_by_id = AsyncMock(return_value=mock_user)
    return repo


@pytest.fixture
def mock_current_user():
    return {
        "id": "00000000-0000-0000-0000-000000000001",
        "email": "test@example.com",
        "metadata": {"name": "Test User"}
    }

def test_get_user(mock_user_repo, mock_current_user):
    app.dependency_overrides[get_user_repository] = lambda: mock_user_repo
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    response = client.get("/api/users/me")

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "teacher@example.com"
    assert data["tone_and_manner"] == "따뜻하고 구체적으로 작성"

    mock_user_repo.get_by_id.assert_called_once()
    app.dependency_overrides.clear()


def test_get_user_not_found(mock_current_user):
    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=None)
    app.dependency_overrides[get_user_repository] = lambda: repo
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    response = client.get("/api/users/me")

    assert response.status_code == 404
    assert "사용자" in response.json()["detail"]

    app.dependency_overrides.clear()


def test_update_user(mock_user_repo, mock_current_user):
    updated_user = mock_user_repo.get_by_id.return_value.model_copy(
        update={
            "tone_and_manner": "간결하고 객관적으로 작성",
            "kindergarten_name": "업데이트 유치원",
        }
    )
    mock_user_repo.update = AsyncMock(return_value=updated_user)

    app.dependency_overrides[get_user_repository] = lambda: mock_user_repo
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    response = client.put(
        "/api/users/me",
        json={
            "tone_and_manner": "간결하고 객관적으로 작성",
            "kindergarten_name": "업데이트 유치원",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["tone_and_manner"] == "간결하고 객관적으로 작성"
    assert data["kindergarten_name"] == "업데이트 유치원"
    mock_user_repo.update.assert_called_once()

    app.dependency_overrides.clear()


def test_update_user_not_found(mock_current_user):
    repo = MagicMock()
    repo.update = AsyncMock(return_value=None)
    app.dependency_overrides[get_user_repository] = lambda: repo
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    response = client.put(
        "/api/users/me",
        json={"tone_and_manner": "지침 업데이트"},
    )

    assert response.status_code == 500
    assert "사용자 업데이트 실패" in response.json()["detail"]

    app.dependency_overrides.clear()
