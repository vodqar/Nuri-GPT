from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.dependencies import get_journal_repository_with_rls, get_current_user
from app.db.models.journal import JournalResponse
from app.main import app

client = TestClient(app)


MOCK_USER_ID = "00000000-0000-0000-0000-000000000001"

def _journal_response(user_id=None) -> JournalResponse:
    now = datetime.now(timezone.utc)
    return JournalResponse(
        id=uuid4(),
        user_id=user_id or uuid4(),
        group_id=uuid4(),
        version=1,
        is_final=True,
        title="테스트 일지",
        observation_content="관찰 내용",
        evaluation_content="평가 내용",
        development_areas=["신체운동"],
        template_id=None,
        template_mapping={},
        semantic_json={},
        updated_activities=[],
        source_type="generate_log_api_default",
        ocr_text="원문",
        additional_guidelines=None,
        created_at=now,
        updated_at=now,
    )

@pytest.fixture
def mock_current_user():
    return {
        "id": MOCK_USER_ID,
        "email": "test@example.com",
        "metadata": {"name": "Test User"}
    }

def test_list_journals_success(mock_current_user):
    repo = MagicMock()
    journal = _journal_response()
    repo.get_latest_by_group = AsyncMock(return_value=[journal])

    app.dependency_overrides[get_journal_repository_with_rls] = lambda: repo
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    response = client.get("/api/journals?limit=10&offset=0")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["limit"] == 10
    assert data["items"][0]["id"] == str(journal.id)

    repo.get_latest_by_group.assert_called_once()
    # user_id는 JWT에서 추출되므로 호출 확인만
    call_kwargs = repo.get_latest_by_group.call_args.kwargs
    assert call_kwargs["limit"] == 10
    assert call_kwargs["offset"] == 0

    app.dependency_overrides.clear()


def test_get_journal_success(mock_current_user):
    repo = MagicMock()
    from uuid import UUID
    journal = _journal_response(user_id=UUID(MOCK_USER_ID))
    repo.get_by_id = AsyncMock(return_value=journal)

    app.dependency_overrides[get_journal_repository_with_rls] = lambda: repo
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    response = client.get(f"/api/journals/{journal.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(journal.id)
    assert data["title"] == "테스트 일지"

    repo.get_by_id.assert_called_once_with(journal.id)

    app.dependency_overrides.clear()


def test_get_journal_not_found(mock_current_user):
    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=None)

    app.dependency_overrides[get_journal_repository_with_rls] = lambda: repo
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    response = client.get(f"/api/journals/{uuid4()}")

    assert response.status_code == 404
    assert "찾을 수 없습니다" in response.json()["detail"]

    app.dependency_overrides.clear()


def test_get_journal_group_history_success(mock_current_user):
    repo = MagicMock()
    from uuid import UUID
    journal1 = _journal_response(user_id=UUID(MOCK_USER_ID))
    journal2 = _journal_response(user_id=UUID(MOCK_USER_ID))
    journal2.version = 2
    repo.get_by_group_id = AsyncMock(return_value=[journal2, journal1])

    app.dependency_overrides[get_journal_repository_with_rls] = lambda: repo
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    group_id = uuid4()
    response = client.get(f"/api/journals/group/{group_id}")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["version"] == 2

    repo.get_by_group_id.assert_called_once_with(group_id)

    app.dependency_overrides.clear()


def test_delete_journal_group_success(mock_current_user):
    repo = MagicMock()
    from uuid import UUID
    journal = _journal_response(user_id=UUID(MOCK_USER_ID))
    repo.get_by_group_id = AsyncMock(return_value=[journal])
    repo.delete_by_group_id = AsyncMock(return_value=3)

    app.dependency_overrides[get_journal_repository_with_rls] = lambda: repo
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    group_id = uuid4()
    response = client.delete(f"/api/journals/group/{group_id}")

    assert response.status_code == 204

    repo.delete_by_group_id.assert_called_once_with(group_id)

    app.dependency_overrides.clear()


def test_delete_journal_group_not_found(mock_current_user):
    repo = MagicMock()
    repo.get_by_group_id = AsyncMock(return_value=[])
    repo.delete_by_group_id = AsyncMock(return_value=0)

    app.dependency_overrides[get_journal_repository_with_rls] = lambda: repo
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    group_id = uuid4()
    response = client.delete(f"/api/journals/group/{group_id}")

    assert response.status_code == 404
    assert "찾을 수 없거나 삭제할 항목이 없습니다" in response.json()["detail"]

    repo.delete_by_group_id.assert_not_called()

    app.dependency_overrides.clear()
