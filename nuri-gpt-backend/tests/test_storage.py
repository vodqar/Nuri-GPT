"""Storage 모듈 단위 테스트

순수 모듈 테스트 (외부 의존성 없이)
"""

from datetime import datetime
from io import BytesIO
from uuid import UUID, uuid4

import pytest
from fastapi import UploadFile


def test_file_validator_imports():
    """파일 유효성 검증 모듈 import 테스트"""
    from app.utils.file_validator import (
        ALLOWED_EXTENSIONS,
        ALLOWED_MIME_TYPES,
        FILE_SIZE_LIMITS,
        FileExtensionNotAllowedError,
        FileMimeTypeNotAllowedError,
        FileSizeExceededError,
        FileType,
        FileValidationError,
        format_file_size,
        get_bucket_name,
        get_file_extension,
        validate_file,
    )

    assert FileType is not None
    assert FileType.TEMPLATE.value == "template"
    assert FileType.MEMO.value == "memo"


def test_file_size_limits():
    """파일 크기 제한 상수 테스트"""
    from app.utils.file_validator import FILE_SIZE_LIMITS, FileType

    # 50MB, 20MB 제한 확인
    assert FILE_SIZE_LIMITS[FileType.TEMPLATE] == 50 * 1024 * 1024
    assert FILE_SIZE_LIMITS[FileType.MEMO] == 20 * 1024 * 1024


def test_allowed_extensions():
    """허용 확장자 테스트"""
    from app.utils.file_validator import ALLOWED_EXTENSIONS, FileType

    assert ".png" in ALLOWED_EXTENSIONS[FileType.TEMPLATE]
    assert ".jpg" in ALLOWED_EXTENSIONS[FileType.MEMO]
    assert ".jpeg" in ALLOWED_EXTENSIONS[FileType.MEMO]
    assert ".png" in ALLOWED_EXTENSIONS[FileType.MEMO]


def test_get_file_extension():
    """파일 확장자 추출 함수 테스트"""
    from app.utils.file_validator import get_file_extension

    assert get_file_extension("test.png") == ".png"
    assert get_file_extension("test.jpg") == ".jpg"
    assert get_file_extension("test.JPG") == ".jpg"  # 소문자 변환
    assert get_file_extension("path/to/file.png") == ".png"
    assert get_file_extension("no_extension") == ""


def test_get_bucket_name():
    """bucket 이름 반환 함수 테스트"""
    from app.utils.file_validator import get_bucket_name, FileType

    assert get_bucket_name(FileType.TEMPLATE) == "templates"
    assert get_bucket_name(FileType.MEMO) == "memos"


def test_format_file_size():
    """파일 크기 포맷 함수 테스트"""
    from app.utils.file_validator import format_file_size

    assert format_file_size(100) == "100.00 B"
    assert format_file_size(1024) == "1.00 KB"
    assert format_file_size(1024 * 1024) == "1.00 MB"
    assert format_file_size(50 * 1024 * 1024) == "50.00 MB"  # 템플릿 제한


def test_storage_schemas_imports():
    """Storage 스키마 import 테스트"""
    from app.schemas.storage import (
        FileInfoResponse,
        FileListResponse,
        StorageDeleteResponse,
        StorageDownloadResponse,
        StorageUploadResponse,
    )

    assert StorageUploadResponse is not None
    assert StorageDownloadResponse is not None
    assert StorageDeleteResponse is not None
    assert FileInfoResponse is not None
    assert FileListResponse is not None


def test_storage_upload_response_schema():
    """업로드 응답 스키마 테스트"""
    from app.schemas.storage import StorageUploadResponse

    response = StorageUploadResponse(
        file_path="user-id/file-uuid.hwpx",
        file_url="https://storage.example.com/file",
        file_size=1024,
        file_name="template.hwpx",
        bucket="templates",
        created_at=datetime.utcnow(),
    )

    assert response.file_path == "user-id/file-uuid.hwpx"
    assert response.file_size == 1024
    assert response.bucket == "templates"


def test_storage_download_response_schema():
    """다운로드 응답 스키마 테스트"""
    from app.schemas.storage import StorageDownloadResponse

    expires = datetime.utcnow()
    response = StorageDownloadResponse(
        signed_url="https://storage.example.com/signed-url",
        expires_at=expires,
        file_path="user-id/file-uuid.hwpx",
        bucket="templates",
    )

    assert "signed-url" in response.signed_url
    assert response.file_path == "user-id/file-uuid.hwpx"


def test_storage_delete_response_schema():
    """삭제 응답 스키마 테스트"""
    from app.schemas.storage import StorageDeleteResponse

    response = StorageDeleteResponse(
        success=True,
        file_path="user-id/file-uuid.hwpx",
        bucket="templates",
    )

    assert response.success is True
    assert response.file_path == "user-id/file-uuid.hwpx"


def test_file_info_response_schema():
    """파일 정보 응답 스키마 테스트"""
    from app.schemas.storage import FileInfoResponse

    now = datetime.utcnow()
    response = FileInfoResponse(
        file_path="user-id/file-uuid.jpg",
        file_name="memo.jpg",
        file_size=2048,
        bucket="memos",
        content_type="image/jpeg",
        created_at=now,
        updated_at=now,
    )

    assert response.file_name == "memo.jpg"
    assert response.content_type == "image/jpeg"
    assert response.file_size == 2048


def test_file_list_response_schema():
    """파일 목록 응답 스키마 테스트"""
    from app.schemas.storage import FileListResponse, FileInfoResponse

    now = datetime.utcnow()
    items = [
        FileInfoResponse(
            file_path="user-id/file1.png",
            file_name="template1.png",
            file_size=1024,
            bucket="templates",
            created_at=now,
        ),
        FileInfoResponse(
            file_path="user-id/file2.png",
            file_name="template2.png",
            file_size=2048,
            bucket="templates",
            created_at=now,
        ),
    ]

    response = FileListResponse(
        items=items,
        total=2,
        bucket="templates",
        prefix="user-id/",
    )

    assert len(response.items) == 2
    assert response.total == 2
    assert response.prefix == "user-id/"


def test_storage_service_import():
    """Storage 서비스 import 테스트"""
    from app.services.storage import StorageService

    assert StorageService is not None


def test_storage_service_bucket_constants():
    """Storage 서비스 bucket 상수 테스트"""
    from app.services.storage import StorageService

    assert StorageService.BUCKET_TEMPLATES == "templates"
    assert StorageService.BUCKET_MEMOS == "memos"


def test_storage_service_generate_file_path():
    """파일 경로 생성 테스트"""
    from app.services.storage import StorageService
    from app.utils.file_validator import FileType

    service = StorageService()
    user_id = uuid4()

    path = service._generate_file_path(user_id, FileType.TEMPLATE, ".png")

    # 경로 형식 검증: user_id/uuid.png
    parts = path.split("/")
    assert len(parts) == 2
    assert parts[0] == str(user_id)
    assert parts[1].endswith(".png")
    assert len(parts[1]) == 40  # uuid (36) + .png (4)


def test_storage_service_get_bucket_name():
    """bucket 이름 반환 테스트"""
    from app.services.storage import StorageService
    from app.utils.file_validator import FileType

    service = StorageService()

    assert service._get_bucket_name(FileType.TEMPLATE) == "templates"
    assert service._get_bucket_name(FileType.MEMO) == "memos"


@pytest.mark.asyncio
async def test_validate_file_valid_template():
    """유효한 이미지 템플릿 파일 검증 테스트"""
    from app.utils.file_validator import validate_file, FileType

    # 실제 PNG 매직넘버 포함
    content = b"\x89PNG\r\n\x1a\n" + b"fake image content"
    file = UploadFile(
        filename="template.png",
        file=BytesIO(content),
        headers={"content-type": "image/png"},
    )

    valid, error = await validate_file(file, FileType.TEMPLATE)
    assert valid is True
    assert error is None


@pytest.mark.asyncio
async def test_validate_file_invalid_extension():
    """유효하지 않은 확장자 검증 테스트"""
    from app.utils.file_validator import validate_file, FileType

    file = UploadFile(
        filename="template.pdf",  # 허용되지 않는 확장자
        file=BytesIO(b"content"),
        headers={"content-type": "application/pdf"},
    )

    valid, error = await validate_file(file, FileType.TEMPLATE)
    assert valid is False
    assert "확장자" in error


@pytest.mark.asyncio
async def test_validate_file_valid_image():
    """유효한 이미지 파일 검증 테스트"""
    from app.utils.file_validator import validate_file, FileType

    # 실제 JPEG 매직넘버 포함
    content = b"\xff\xd8\xff\xe0" + b"fake image content"
    file = UploadFile(
        filename="memo.jpg",
        file=BytesIO(content),
        headers={"content-type": "image/jpeg"},
    )

    valid, error = await validate_file(file, FileType.MEMO)
    assert valid is True
    assert error is None


@pytest.mark.asyncio
async def test_validate_file_blob_with_mime_inference():
    """blob 파일명 + MIME 타입으로 확장자 추론 테스트"""
    from app.utils.file_validator import validate_file, FileType

    # 프론트엔드 FormData에서 파일명 없이 Blob 전송 시
    # 실제 JPEG 매직넘버 포함
    content = b"\xff\xd8\xff\xe0" + b"fake image content"
    file = UploadFile(
        filename="blob",  # 확장자 없음
        file=BytesIO(content),
        headers={"content-type": "image/jpeg"},
    )

    valid, error = await validate_file(file, FileType.MEMO)
    assert valid is True, f"Expected valid but got error: {error}"
    assert error is None


@pytest.mark.asyncio
async def test_validate_file_invalid_mime_type():
    """유효하지 않은 MIME 타입 검증 테스트"""
    from app.utils.file_validator import validate_file, FileType

    file = UploadFile(
        filename="memo.gif",  # 허용되지 않는 확장자
        file=BytesIO(b"content"),
        headers={"content-type": "image/gif"},
    )

    valid, error = await validate_file(file, FileType.MEMO)
    assert valid is False


def test_file_size_limit_exceeded():
    """파일 크기 제한 초과 테스트"""
    from app.utils.file_validator import (
        FILE_SIZE_LIMITS,
        FileSizeExceededError,
        FileType,
    )

    # 20MB 초과하는 메모 파일
    large_content = b"x" * (21 * 1024 * 1024)

    # 크기 비교 검증
    assert len(large_content) > FILE_SIZE_LIMITS[FileType.MEMO]


def test_storage_exceptions():
    """Storage 예외 클래스 테스트"""
    from app.utils.file_validator import (
        FileValidationError,
        FileSizeExceededError,
        FileExtensionNotAllowedError,
        FileMimeTypeNotAllowedError,
    )

    # 예외 계층 구조 검증
    assert issubclass(FileSizeExceededError, FileValidationError)
    assert issubclass(FileExtensionNotAllowedError, FileValidationError)
    assert issubclass(FileMimeTypeNotAllowedError, FileValidationError)

    # 예외 발생 테스트
    try:
        raise FileSizeExceededError("크기 초과")
    except FileValidationError as e:
        assert "크기 초과" in str(e)



def test_file_info_without_optional_fields():
    """선택 필드 없는 파일 정보 테스트"""
    from app.schemas.storage import FileInfoResponse

    now = datetime.utcnow()
    response = FileInfoResponse(
        file_path="user-id/file.png",
        file_name="file.png",
        file_size=1024,
        bucket="templates",
        created_at=now,
        # content_type, updated_at 없음
    )

    assert response.content_type is None
    assert response.updated_at is None
