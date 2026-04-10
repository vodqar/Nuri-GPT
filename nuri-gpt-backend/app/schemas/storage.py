"""Storage Schemas

파일 업로드/다운로드 API 스키마
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field




class StorageUploadResponse(BaseModel):
    """파일 업로드 응답 스키마"""
    file_path: str = Field(..., description="Storage 내 파일 경로")
    file_url: Optional[str] = Field(None, description="공개 URL (있는 경우)")
    file_size: int = Field(..., ge=0, description="파일 크기 (bytes)")
    file_name: str = Field(..., description="원본 파일명")
    bucket: str = Field(..., description="저장된 bucket 이름")
    created_at: datetime = Field(..., description="생성 시간")


class StorageDownloadResponse(BaseModel):
    """파일 다운로드 응답 스키마"""
    signed_url: str = Field(..., description="서명된 다운로드 URL")
    expires_at: datetime = Field(..., description="URL 만료 시간")
    file_path: str = Field(..., description="파일 경로")
    bucket: str = Field(..., description="bucket 이름")


class StorageDeleteResponse(BaseModel):
    """파일 삭제 응답 스키마"""
    success: bool = Field(..., description="삭제 성공 여부")
    file_path: str = Field(..., description="삭제된 파일 경로")
    bucket: str = Field(..., description="bucket 이름")


class FileInfoResponse(BaseModel):
    """파일 정보 응답 스키마"""
    file_path: str = Field(..., description="파일 경로")
    file_name: str = Field(..., description="원본 파일명")
    file_size: int = Field(..., ge=0, description="파일 크기 (bytes)")
    bucket: str = Field(..., description="bucket 이름")
    content_type: Optional[str] = Field(None, description="MIME 타입")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: Optional[datetime] = Field(None, description="수정 시간")


class FileListResponse(BaseModel):
    """파일 목록 응답 스키마"""
    items: list[FileInfoResponse] = Field(..., description="파일 목록")
    total: int = Field(..., ge=0, description="총 파일 수")
    bucket: str = Field(..., description="bucket 이름")
    prefix: Optional[str] = Field(None, description="검색 접두사")


