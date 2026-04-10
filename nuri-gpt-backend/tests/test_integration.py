"""백엔드 통합 테스트 (LLM mock 유지)

비용이 발생하는 LLM 계층은 mock으로 유지하고,
나머지 API 파이프라인 연결은 실제 라우팅 경로 기준으로 검증한다.
"""

from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.dependencies import (
    get_current_user,
    get_journal_repository,
    get_llm_service,
    get_log_repository,
    get_storage_service,
    get_template_repository,
)
from app.db.models.journal import JournalInDB
from app.db.models.log import UserLogInDB
from app.db.models.template import TemplateInDB
from app.main import app
from app.schemas.storage import StorageUploadResponse

client = TestClient(app)


def _build_minimal_image() -> bytes:
    return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'


def test_template_upload_then_generate_pipeline():
    user_id = "00000000-0000-0000-0000-000000000001"
    user_uuid = uuid4()
    template_id = uuid4()
    log_id = uuid4()
    journal_id = uuid4()
    now = datetime.now(timezone.utc)

    mock_current_user = {
        "id": user_id,
        "email": "test@example.com",
        "metadata": {"name": "Test User"}
    }

    mock_storage = MagicMock()
    mock_storage.upload_template = AsyncMock(
        return_value=StorageUploadResponse(
            file_path=f"{user_id}/template.png",
            file_url=None,
            file_size=1024,
            file_name="template.png",
            bucket="templates",
            created_at=now,
        )
    )

    mock_template_repo = MagicMock()
    mock_template_repo.create = AsyncMock(
        return_value=TemplateInDB(
            id=template_id,
            user_id=user_uuid,
            name="통합 테스트 템플릿",
            template_type="observation_log",
            structure_json={"놀이": {"활동": {"내용": ""}}},
            file_storage_path=f"{user_id}/template.png",
            is_default=False,
            created_at=now,
            updated_at=now,
        )
    )

    mock_llm = MagicMock()
    mock_llm.generate_observation_log.return_value = {
        "title": "통합 테스트 일지",
        "observation_content": "아이가 블록을 쌓음",
        "evaluation_content": "소근육 발달이 확인됨",
        "development_areas": ["신체운동"],
    }

    mock_log_repo = MagicMock()
    mock_log_repo.log_action = AsyncMock(
        return_value=UserLogInDB(
            id=log_id,
            user_id=user_uuid,
            action="generate_log",
            metadata={},
            created_at=now,
        )
    )

    mock_journal_repo = MagicMock()
    mock_journal_repo.create = AsyncMock(
        return_value=JournalInDB(
            id=journal_id,
            user_id=user_uuid,
            group_id=uuid4(),
            version=1,
            is_final=True,
            title="통합 테스트 일지",
            observation_content="아이가 블록을 쌓음",
            evaluation_content="소근육 발달이 확인됨",
            development_areas=["신체운동"],
            template_id=None,
            template_mapping={},
            semantic_json={},
            updated_activities=[],
            source_type="generate_log_api_default",
            ocr_text="아이가 블록 놀이를 함",
            additional_guidelines="",
            created_at=now,
            updated_at=now,
        )
    )

    app.dependency_overrides[get_storage_service] = lambda: mock_storage
    app.dependency_overrides[get_template_repository] = lambda: mock_template_repo
    app.dependency_overrides[get_llm_service] = lambda: mock_llm
    app.dependency_overrides[get_log_repository] = lambda: mock_log_repo
    app.dependency_overrides[get_journal_repository] = lambda: mock_journal_repo
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    try:
        image_bytes = _build_minimal_image()
        upload_resp = client.post(
            "/api/upload/template",
            data={"template_name": "통합 테스트 템플릿"},
            files={"file": ("template.png", BytesIO(image_bytes), "image/png")},
        )
        assert upload_resp.status_code == 200
        assert upload_resp.json()["template_id"] == str(template_id)

        gen_resp = client.post(
            "/api/generate/log",
            json={
                "ocr_text": "아이가 블록 놀이를 함",
                "additional_guidelines": "",
                "child_age": 3,
            },
        )
        assert gen_resp.status_code == 200
        assert gen_resp.json()["log_id"] == str(log_id)
        assert gen_resp.json()["journal_id"] == str(journal_id)

    finally:
        app.dependency_overrides.clear()
