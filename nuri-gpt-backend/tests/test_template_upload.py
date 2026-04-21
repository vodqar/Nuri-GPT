import json
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.db.models.template import TemplateResponse
from app.schemas.storage import StorageUploadResponse
from app.core.dependencies import get_template_repository, get_storage_service, get_vision_service, get_current_user, get_usage_service

client = TestClient(app)

# Minimal valid PNG bytes for magic number validation
_MINIMAL_PNG = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
# Minimal valid JPEG bytes
_MINIMAL_JPEG = b'\xff\xd8\xff\xe0' + b'\x00\x10JFIF' + b'\x00' * 10 + b'fake image content'

@pytest.fixture
def mock_template_repo():
    repo = MagicMock()
    mock_template = TemplateResponse(
        id=uuid4(),
        user_id=uuid4(),
        name="테스트 템플릿",
        template_type="observation_log",
        structure_json={"area": "놀이"},
        file_storage_path="templates/test_uuid/test.jpg",
        is_default=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    repo.create = AsyncMock(return_value=mock_template)
    return repo

@pytest.fixture
def mock_storage_service():
    service = MagicMock()
    upload_res = StorageUploadResponse(
        file_path="templates/test_uuid/test.jpg",
        file_name="test.jpg",
        file_size=1024,
        content_type="image/jpeg",
        bucket="templates",
        created_at=datetime.now(timezone.utc)
    )
    service.upload_template = AsyncMock(return_value=upload_res)
    return service
    
@pytest.fixture
def mock_vision_service():
    service = MagicMock()
    service.extract_template_structure.return_value = {
        "area": "놀이"
    }
    return service

@pytest.fixture
def mock_current_user():
    return {
        "id": "00000000-0000-0000-0000-000000000001",
        "email": "test@example.com",
        "metadata": {"name": "Test User"}
    }

def test_upload_template_with_vision(mock_template_repo, mock_storage_service, mock_vision_service, mock_current_user):
    mock_usage_service = MagicMock()
    mock_usage_service.check_quota_available = AsyncMock(return_value=True)
    mock_usage_service.increment_usage = AsyncMock()

    app.dependency_overrides[get_template_repository] = lambda: mock_template_repo
    app.dependency_overrides[get_storage_service] = lambda: mock_storage_service
    app.dependency_overrides[get_vision_service] = lambda: mock_vision_service
    app.dependency_overrides[get_usage_service] = lambda: mock_usage_service
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    
    response = client.post(
        "/api/upload/template",
        data={
            "template_name": "테스트 일지"
        },
        files={"file": ("test.jpg", _MINIMAL_JPEG, "image/jpeg")}
    )
        
    if response.status_code != 200:
        print("RESPONSE JSON:", response.json())
    assert response.status_code == 200
    data = response.json()
    assert data["template_name"] == "테스트 템플릿"
    assert data["structure_json"] == {"area": "놀이"}
    
    # Verify vision was called
    mock_vision_service.extract_template_structure.assert_called_once_with(_MINIMAL_JPEG, "image/jpeg")
    
    # Verify repo create was called
    repo_call_args = mock_template_repo.create.call_args[0][0]
    assert repo_call_args.structure_json == {"area": "놀이"}
    
    app.dependency_overrides.clear()


def test_analyze_template_returns_structure_json_only(mock_vision_service, mock_current_user):
    mock_usage_service = MagicMock()
    mock_usage_service.check_quota_available = AsyncMock(return_value=True)
    mock_usage_service.increment_usage = AsyncMock()

    app.dependency_overrides[get_vision_service] = lambda: mock_vision_service
    app.dependency_overrides[get_usage_service] = lambda: mock_usage_service
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    response = client.post(
        "/api/upload/template/analyze",
        files={"file": ("test.png", _MINIMAL_PNG, "image/png")}
    )

    if response.status_code != 200:
        print("RESPONSE JSON:", response.json())
    assert response.status_code == 200
    data = response.json()
    assert "structure_json" in data
    assert data["structure_json"] == {"area": "놀이"}
    assert "template_id" not in data

    mock_vision_service.extract_template_structure.assert_called_once_with(_MINIMAL_PNG, "image/png")

    app.dependency_overrides.clear()


def test_create_template_without_image(mock_template_repo, mock_storage_service, mock_current_user):
    """POST /templates — 이미지 없이 structure_json만으로 저장 (수동 트랙)"""
    app.dependency_overrides[get_template_repository] = lambda: mock_template_repo
    app.dependency_overrides[get_storage_service] = lambda: mock_storage_service
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    structure = {"놀이": {"실내놀이": ""}}

    response = client.post(
        "/api/templates/",
        data={
            "template_name": "수동 템플릿",
            "structure_json": json.dumps(structure, ensure_ascii=False),
        },
    )

    if response.status_code != 201:
        print("RESPONSE JSON:", response.json())
    assert response.status_code == 201

    repo_call_args = mock_template_repo.create.call_args[0][0]
    assert repo_call_args.structure_json == structure
    assert repo_call_args.file_storage_path is None

    app.dependency_overrides.clear()


def test_create_template_with_image(mock_template_repo, mock_storage_service, mock_current_user):
    """POST /templates — 이미지 포함 저장 (이미지 기반 트랙)"""
    app.dependency_overrides[get_template_repository] = lambda: mock_template_repo
    app.dependency_overrides[get_storage_service] = lambda: mock_storage_service
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    structure = {"놀이": {"실내놀이": ""}}

    response = client.post(
        "/api/templates/",
        data={
            "template_name": "이미지 템플릿",
            "structure_json": json.dumps(structure, ensure_ascii=False),
        },
        files={"file": ("test.jpg", _MINIMAL_JPEG, "image/jpeg")},
    )

    if response.status_code != 201:
        print("RESPONSE JSON:", response.json())
    assert response.status_code == 201

    mock_storage_service.upload_template.assert_called_once()

    app.dependency_overrides.clear()


def test_create_template_empty_structure_json_rejected(mock_template_repo, mock_storage_service, mock_current_user):
    """POST /templates — 빈 structure_json은 422 반환"""
    app.dependency_overrides[get_template_repository] = lambda: mock_template_repo
    app.dependency_overrides[get_storage_service] = lambda: mock_storage_service
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    response = client.post(
        "/api/templates/",
        data={
            "template_name": "빈 구조",
            "structure_json": json.dumps({}),
        },
    )

    assert response.status_code == 422

    app.dependency_overrides.clear()
