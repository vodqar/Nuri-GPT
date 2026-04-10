import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.db.models.template import TemplateResponse
from app.db.models.log import UserLogResponse
from app.db.models.journal import JournalResponse
from app.core.dependencies import get_llm_service, get_log_repository, get_template_repository, get_journal_repository, get_current_user

client = TestClient(app)

@pytest.fixture
def mock_current_user():
    """Mock authenticated user for tests"""
    return {
        "id": "00000000-0000-0000-0000-000000000001",
        "email": "test@example.com",
        "metadata": {"name": "Test User"}
    }

@pytest.fixture
def mock_llm_service():
    service = MagicMock()
    service.generate_observation_log.return_value = {
        "title": "관찰일지 제목",
        "observation_content": "관찰 내용",
        "evaluation_content": "평가",
        "development_areas": ["신체운동"]
    }
    service.generate_journal_content.return_value = {
        "CELL_001": "2023년 4월 13일",
        "CELL_002": "자유놀이 관찰 내용..."
    }
    service.generate_updated_activities.return_value = [
        {"target_id": "t_20", "updated_text": "수정된 간식 내용"},
        {"target_id": "t_31", "updated_text": "수정된 실내놀이 내용"},
    ]
    return service

@pytest.fixture
def mock_log_repo():
    repo = MagicMock()
    repo.log_action = AsyncMock(return_value=UserLogResponse(
        id=uuid4(),
        user_id=uuid4(),
        action="generate_log",
        metadata={},
        created_at="2024-01-01T00:00:00Z"
    ))
    return repo

@pytest.fixture
def mock_template_repo():
    repo = MagicMock()
    mock_template = TemplateResponse(
        id=uuid4(),
        user_id=uuid4(),
        name="테스트 템플릿",
        template_type="observation_log",
        xml_structure={},
        tags=["{{format:date_날짜}}", "{{format:longtext_내용}}"],
        file_storage_path="path",
        is_default=False,
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
        structure_json={"날짜": "{{format:date}}", "내용": "{{format:longtext}}"}
    )
    repo.get_by_id = AsyncMock(return_value=mock_template)
    repo.update_last_used_at = AsyncMock(return_value=True)
    return repo

@pytest.fixture
def mock_journal_repo():
    repo = MagicMock()
    repo.create = AsyncMock(return_value=JournalResponse(
        id=uuid4(),
        user_id=uuid4(),
        group_id=uuid4(),
        version=1,
        is_final=True,
        title="테스트 제목",
        observation_content="테스트 내용",
        evaluation_content=None,
        development_areas=[],
        template_id=None,
        template_mapping={},
        semantic_json={},
        updated_activities=[],
        source_type="generate_log_api_default",
        ocr_text="",
        additional_guidelines=None,
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
    ))
    return repo

def test_generate_log_default(mock_llm_service, mock_log_repo, mock_template_repo, mock_journal_repo, mock_current_user):
    app.dependency_overrides[get_llm_service] = lambda: mock_llm_service
    app.dependency_overrides[get_log_repository] = lambda: mock_log_repo
    app.dependency_overrides[get_template_repository] = lambda: mock_template_repo
    app.dependency_overrides[get_journal_repository] = lambda: mock_journal_repo
    app.dependency_overrides[get_journal_repository] = lambda: mock_journal_repo
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    response = client.post(
        "/api/generate/log",
        json={"ocr_text": "관찰 내용 테스트", "child_age": 3}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "관찰일지 제목"
    assert data["observation_content"] == "관찰 내용"
    assert "log_id" in data
    
    mock_llm_service.generate_observation_log.assert_called_once()
    
    app.dependency_overrides.clear()


def test_generate_log_empty_ocr_text_fails(mock_llm_service, mock_log_repo, mock_template_repo, mock_journal_repo, mock_current_user):
    app.dependency_overrides[get_llm_service] = lambda: mock_llm_service
    app.dependency_overrides[get_log_repository] = lambda: mock_log_repo
    app.dependency_overrides[get_template_repository] = lambda: mock_template_repo
    app.dependency_overrides[get_journal_repository] = lambda: mock_journal_repo
    app.dependency_overrides[get_journal_repository] = lambda: mock_journal_repo
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    response = client.post(
        "/api/generate/log",
        json={"ocr_text": "", "child_age": 3},
    )

    assert response.status_code == 422

    app.dependency_overrides.clear()


def test_generate_log_llm_failure(mock_log_repo, mock_template_repo, mock_journal_repo, mock_current_user):
    mock_llm_service = MagicMock()
    mock_llm_service.generate_observation_log.side_effect = RuntimeError("API Limit Exceeded")

    app.dependency_overrides[get_llm_service] = lambda: mock_llm_service
    app.dependency_overrides[get_log_repository] = lambda: mock_log_repo
    app.dependency_overrides[get_template_repository] = lambda: mock_template_repo
    app.dependency_overrides[get_journal_repository] = lambda: mock_journal_repo
    app.dependency_overrides[get_journal_repository] = lambda: mock_journal_repo
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    response = client.post(
        "/api/generate/log",
        json={"ocr_text": "아이가 블록을 쌓음", "child_age": 3},
    )

    assert response.status_code == 500
    assert "LLM 생성 서비스 예외" in response.json()["detail"]

    app.dependency_overrides.clear()


def test_generate_log_llm_empty_response(mock_log_repo, mock_template_repo, mock_journal_repo, mock_current_user):
    mock_llm_service = MagicMock()
    mock_llm_service.generate_observation_log.return_value = {
        "title": "",
        "observation_content": "",
        "evaluation_content": "",
        "development_areas": [],
    }

    app.dependency_overrides[get_llm_service] = lambda: mock_llm_service
    app.dependency_overrides[get_log_repository] = lambda: mock_log_repo
    app.dependency_overrides[get_template_repository] = lambda: mock_template_repo
    app.dependency_overrides[get_journal_repository] = lambda: mock_journal_repo
    app.dependency_overrides[get_journal_repository] = lambda: mock_journal_repo
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    response = client.post(
        "/api/generate/log",
        json={"ocr_text": "단답형", "child_age": 3},
    )

    assert response.status_code == 500
    assert "빈 응답" in response.json()["detail"]

    app.dependency_overrides.clear()

def test_generate_log_with_template(mock_llm_service, mock_log_repo, mock_template_repo, mock_journal_repo, mock_current_user):
    app.dependency_overrides[get_llm_service] = lambda: mock_llm_service
    app.dependency_overrides[get_log_repository] = lambda: mock_log_repo
    app.dependency_overrides[get_template_repository] = lambda: mock_template_repo
    app.dependency_overrides[get_journal_repository] = lambda: mock_journal_repo
    app.dependency_overrides[get_journal_repository] = lambda: mock_journal_repo
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    template_id = str(uuid4())
    response = client.post(
        "/api/generate/log",
        json={"ocr_text": "관찰 내용 테스트", "template_id": template_id, "child_age": 3}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "template_mapping" in data
    assert data["template_mapping"]["CELL_001"] == "2023년 4월 13일"
    assert data["template_mapping"]["CELL_002"] == "자유놀이 관찰 내용..."
    assert "log_id" in data
    
    mock_llm_service.generate_journal_content.assert_called_once()
    
    app.dependency_overrides.clear()


def test_generate_log_with_semantic_json(mock_llm_service, mock_log_repo, mock_template_repo, mock_journal_repo, mock_current_user):
    app.dependency_overrides[get_llm_service] = lambda: mock_llm_service
    app.dependency_overrides[get_log_repository] = lambda: mock_log_repo
    app.dependency_overrides[get_template_repository] = lambda: mock_template_repo
    app.dependency_overrides[get_journal_repository] = lambda: mock_journal_repo
    app.dependency_overrides[get_journal_repository] = lambda: mock_journal_repo
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    response = client.post(
        "/api/generate/log",
        json={
            "ocr_text": "추가 메모",
            "child_age": 3,
            "semantic_json": {
                "document_type": "일일보육일지",
                "date": "2026년 3월 21일",
                "activities": [
                    {
                        "category": "일상생활",
                        "sub_category": "간식",
                        "target_id": "t_20",
                        "current_text": "기존 간식",
                    },
                    {
                        "category": "놀이",
                        "sub_category": "실내놀이",
                        "target_id": "t_31",
                        "current_text": "기존 실내놀이",
                    },
                ],
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "updated_activities" in data
    assert data["updated_activities"][0]["target_id"] == "t_20"
    assert data["updated_activities"][0]["updated_text"] == "수정된 간식 내용"

    mock_llm_service.generate_updated_activities.assert_called_once()

    app.dependency_overrides.clear()


def test_regenerate_log_success(mock_llm_service, mock_log_repo, mock_journal_repo, mock_current_user):
    """코멘트 기반 재생성 API 테스트 - 성공 케이스"""
    mock_llm_service.generate_regenerated_activities.return_value = [
        {"target_id": "t_20", "updated_text": "간식 코멘트 반영 내용"},
        {"target_id": "t_31", "updated_text": "실내놀이 원본 유지"},
    ]
    
    app.dependency_overrides[get_llm_service] = lambda: mock_llm_service
    app.dependency_overrides[get_log_repository] = lambda: mock_log_repo
    app.dependency_overrides[get_journal_repository] = lambda: mock_journal_repo
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    response = client.post(
        "/api/generate/regenerate",
        json={
            "original_semantic_json": {
                "document_type": "일일보육일지",
                "date": "2026년 3월 21일",
                "activities": [
                    {
                        "category": "일상생활",
                        "sub_category": "간식",
                        "target_id": "t_20",
                        "current_text": "기존 간식",
                    },
                ],
            },
            "current_activities": [
                {"target_id": "t_20", "updated_text": "원본 간식 내용"},
                {"target_id": "t_31", "updated_text": "원본 실내놀이 내용"},
            ],
            "comments": [
                {"target_id": "t_20", "comment": "간식 내용을 더 구체적으로 작성해주세요"},
            ],
            "additional_guidelines": "",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "updated_activities" in data
    assert len(data["updated_activities"]) == 2
    assert data["updated_activities"][0]["target_id"] == "t_20"
    assert data["updated_activities"][0]["updated_text"] == "간식 코멘트 반영 내용"
    assert "log_id" in data

    mock_llm_service.generate_regenerated_activities.assert_called_once()
    
    # Verify log_action was called with correct action name
    mock_log_repo.log_action.assert_called_once()
    call_kwargs = mock_log_repo.log_action.call_args.kwargs
    assert call_kwargs["action"] == "regenerate_journal_from_semantic"

    app.dependency_overrides.clear()


def test_regenerate_log_empty_activities(mock_llm_service, mock_log_repo, mock_journal_repo, mock_current_user):
    """재생성 API 테스트 - 빈 current_activities (422 예상)"""
    app.dependency_overrides[get_llm_service] = lambda: mock_llm_service
    app.dependency_overrides[get_log_repository] = lambda: mock_log_repo
    app.dependency_overrides[get_journal_repository] = lambda: mock_journal_repo
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    response = client.post(
        "/api/generate/regenerate",
        json={
            "original_semantic_json": {
                "document_type": "일일보육일지",
                "date": "2026년 3월 21일",
                "activities": [],
            },
            "current_activities": [],
            "comments": [],
            "additional_guidelines": "",
        },
    )

    assert response.status_code == 422

    app.dependency_overrides.clear()


def test_regenerate_log_missing_target_id_fallback(mock_llm_service, mock_log_repo, mock_journal_repo, mock_current_user):
    """재생성 API 테스트 - LLM 응답에 누락된 target_id가 있는 경우 fallback"""
    # LLM이 t_31을 누락하고 반환
    mock_llm_service.generate_regenerated_activities.return_value = [
        {"target_id": "t_20", "updated_text": "수정된 내용"},
    ]
    
    app.dependency_overrides[get_llm_service] = lambda: mock_llm_service
    app.dependency_overrides[get_log_repository] = lambda: mock_log_repo
    app.dependency_overrides[get_journal_repository] = lambda: mock_journal_repo
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    response = client.post(
        "/api/generate/regenerate",
        json={
            "original_semantic_json": {
                "document_type": "일일보육일지",
                "date": "2026년 3월 21일",
                "activities": [
                    {"category": "일상생활", "sub_category": "간식", "target_id": "t_20", "current_text": "기존"},
                    {"category": "놀이", "sub_category": "실내놀이", "target_id": "t_31", "current_text": "기존"},
                ],
            },
            "current_activities": [
                {"target_id": "t_20", "updated_text": "원본 t_20"},
                {"target_id": "t_31", "updated_text": "원본 t_31"},
            ],
            "comments": [{"target_id": "t_20", "comment": "수정 요청"}],
            "additional_guidelines": "",
        },
    )

    assert response.status_code == 200
    data = response.json()
    
    # 응답에 누락된 target_id가 포함되었는지 확인
    assert len(data["updated_activities"]) == 2
    target_ids = {act["target_id"] for act in data["updated_activities"]}
    assert target_ids == {"t_20", "t_31"}
    
    # t_31은 원본 값으로 보존되었는지 확인
    t_31_activity = next(act for act in data["updated_activities"] if act["target_id"] == "t_31")
    assert t_31_activity["updated_text"] == "원본 t_31"

    app.dependency_overrides.clear()
