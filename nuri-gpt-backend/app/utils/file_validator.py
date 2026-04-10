"""파일 유효성 검증 유틸리티 모듈

파일 업로드 전 유효성 검증
"""

import os
from enum import Enum
from typing import Optional, Tuple

from fastapi import UploadFile, HTTPException


class FileType(Enum):
    """지원하는 파일 타입"""
    TEMPLATE = "template"
    MEMO = "memo"


# 파일 크기 제한 (bytes)
FILE_SIZE_LIMITS = {
    FileType.TEMPLATE: 50 * 1024 * 1024,    # 50MB
    FileType.MEMO: 20 * 1024 * 1024,      # 20MB
}

HWPX_MIME_HINT_KEYWORDS = ("zip", "hwp", "hwpx")

# 허용 확장자
ALLOWED_EXTENSIONS = {
    FileType.TEMPLATE: {".jpg", ".jpeg", ".png"},
    FileType.MEMO: {".jpg", ".jpeg", ".png"},
}

# MIME 타입 매핑
ALLOWED_MIME_TYPES = {
    FileType.TEMPLATE: {
        "image/jpeg",
        "image/png",
        "image/jpg",
    },
    FileType.MEMO: {
        "image/jpeg",
        "image/png",
        "image/jpg",
    },
}

# MIME 타입에서 확장자 추론 매핑
MIME_TO_EXT = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
}


class FileValidationError(Exception):
    """파일 유효성 검증 에러"""
    pass


class FileSizeExceededError(FileValidationError):
    """파일 크기 초과 에러"""
    pass


class FileExtensionNotAllowedError(FileValidationError):
    """허용되지 않는 파일 확장자 에러"""
    pass


class FileMimeTypeNotAllowedError(FileValidationError):
    """허용되지 않는 MIME 타입 에러"""
    pass


async def validate_file(
    file: UploadFile,
    file_type: FileType,
    max_size: Optional[int] = None
) -> Tuple[bool, Optional[str]]:
    """
    파일 유효성 검증

    Args:
        file: 검증할 파일
        file_type: 파일 타입 (TEMPLATE, MEMO, EXPORT)
        max_size: 최대 파일 크기 (None이면 기본값 사용)

    Returns:
        (성공 여부, 에러 메시지)
    """
    if max_size is None:
        max_size = FILE_SIZE_LIMITS.get(file_type, 10 * 1024 * 1024)

    # 파일명 확인
    if not file.filename:
        return False, "파일명이 없습니다."

    # 확장자 검증
    ext = os.path.splitext(file.filename)[1].lower()
    allowed_exts = ALLOWED_EXTENSIONS.get(file_type, set())

    # 확장자가 없고 MIME 타입이 있는 경우, MIME에서 확장자 추론
    if not ext and file.content_type:
        inferred_ext = MIME_TO_EXT.get(file.content_type.lower())
        if inferred_ext:
            ext = inferred_ext

    if ext not in allowed_exts:
        return False, f"허용되지 않는 파일 확장자입니다. ({', '.join(allowed_exts)}만 가능)"

    # MIME 타입 검증 (있는 경우)
    if file.content_type:
        allowed_mimes = ALLOWED_MIME_TYPES.get(file_type, set())
        content_type = file.content_type.lower()

        if content_type not in allowed_mimes:
            return False, "허용되지 않는 파일 형식입니다."

    # 파일 크기 검증 (간접적으로)
    # 실제 크기는 파일을 읽어야 알 수 있으므로,
    # StorageService에서 업로드 전에 검증
    return True, None


def get_file_extension(filename: str) -> str:
    """파일명에서 확장자 추출"""
    return os.path.splitext(filename)[1].lower()


def get_bucket_name(file_type: FileType) -> str:
    """파일 타입에 따른 bucket 이름 반환"""
    bucket_map = {
        FileType.TEMPLATE: "templates",
        FileType.MEMO: "memos",
    }
    return bucket_map.get(file_type, "files")


def format_file_size(size_bytes: int) -> str:
    """바이트를 사람이 읽기 쉬운 형식으로 변환"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"
