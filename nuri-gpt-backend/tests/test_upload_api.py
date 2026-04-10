from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.dependencies import get_ocr_service, get_storage_service, get_current_user
from app.main import app
from app.schemas.storage import StorageUploadResponse

client = TestClient(app)


def test_upload_memo_success():
    mock_storage_service = MagicMock()
    mock_storage_service.upload_memo = AsyncMock(
        return_value=StorageUploadResponse(
            file_path="memos/test-user/memo.png",
            file_url=None,
            file_size=123,
            file_name="memo.png",
            bucket="memos",
            created_at=datetime.now(timezone.utc),
        )
    )

    mock_ocr_service = MagicMock()
    mock_ocr_service.extract_text_from_image.return_value = "원본 OCR 텍스트"
    mock_ocr_service.normalize_text.return_value = "정규화 OCR 텍스트"

    mock_current_user = {
        "id": "00000000-0000-0000-0000-000000000001",
        "email": "test@example.com",
        "metadata": {"name": "Test User"}
    }

    app.dependency_overrides[get_storage_service] = lambda: mock_storage_service
    app.dependency_overrides[get_ocr_service] = lambda: mock_ocr_service
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    response = client.post(
        "/api/upload/memo",
        files={"file": ("memo.png", b"fake-image-bytes", "image/png")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["extracted_text"] == "원본 OCR 텍스트"
    assert data["normalized_text"] == "정규화 OCR 텍스트"
    assert data["storage_info"]["bucket"] == "memos"

    mock_storage_service.upload_memo.assert_called_once()
    mock_ocr_service.extract_text_from_image.assert_called_once()
    mock_ocr_service.normalize_text.assert_called_once_with("원본 OCR 텍스트")

    app.dependency_overrides.clear()


def test_upload_memo_text_success():
    mock_ocr_service = MagicMock()
    mock_ocr_service.normalize_text.return_value = "정규화 결과"

    app.dependency_overrides[get_ocr_service] = lambda: mock_ocr_service

    response = client.post(
        "/api/upload/memo/text",
        json={"text": "직접 입력 메모", "child_name": "민수"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["original_text"] == "직접 입력 메모"
    assert data["normalized_text"] == "정규화 결과"
    assert data["child_name"] == "민수"

    mock_ocr_service.normalize_text.assert_called_once_with("직접 입력 메모")

    app.dependency_overrides.clear()
