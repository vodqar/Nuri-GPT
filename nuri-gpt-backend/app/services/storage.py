"""Supabase Storage 서비스 모듈

파일 업로드/다운로드/삭제 로직
"""

import io
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import UploadFile

from supabase import Client

from app.db.connection import get_supabase_client, get_supabase_admin_client
from app.schemas.storage import (
    FileInfoResponse,
    FileListResponse,
    StorageDeleteResponse,
    StorageDownloadResponse,
    StorageUploadResponse,
)
from app.utils.file_validator import (
    FILE_SIZE_LIMITS,
    FileExtensionNotAllowedError,
    FileMimeTypeNotAllowedError,
    FileSizeExceededError,
    FileType,
    get_file_extension,
    validate_file,
)


class StorageService:
    """Supabase Storage 작업을 처리하는 서비스"""

    # Bucket 이름 상수
    BUCKET_TEMPLATES = "templates"
    BUCKET_MEMOS = "memos"
    BUCKET_EXPORTS = "exports"

    def __init__(self, client: Optional[Client] = None, admin_client: Optional[Client] = None):
        self._client = client
        self._admin_client = admin_client
        self._client_provided = client is not None

    @property
    def client(self) -> Client:
        """Supabase 클라이언트 (lazy initialization)"""
        if self._client is None:
            self._client = get_supabase_client()
        return self._client

    @property
    def admin_client(self) -> Client:
        """service_role 클라이언트 (RLS bypass, 업로드/삭제 전용)"""
        if self._admin_client is None:
            self._admin_client = get_supabase_admin_client()
        return self._admin_client

    def _generate_file_path(self, user_id: UUID, file_type: FileType, extension: str) -> str:
        """UUID 기반 파일 경로 생성"""
        file_uuid = uuid.uuid4()
        return f"{user_id}/{file_uuid}{extension}"

    def _get_bucket_name(self, file_type: FileType) -> str:
        """파일 타입에 따른 bucket 이름 반환"""
        bucket_map = {
            FileType.TEMPLATE: self.BUCKET_TEMPLATES,
            FileType.MEMO: self.BUCKET_MEMOS,
        }
        return bucket_map.get(file_type, "files")

    async def _check_bucket_exists(self, bucket_name: str) -> bool:
        """bucket 존재 여부 확인"""
        try:
            buckets = self.client.storage.list_buckets()
            return any(b.name == bucket_name for b in buckets)
        except Exception:
            return False

    async def _ensure_bucket_exists(self, bucket_name: str) -> None:
        """bucket이 없으면 생성"""
        try:
            if not await self._check_bucket_exists(bucket_name):
                self.client.storage.create_bucket(
                    bucket_name,
                    options={"public": False}  # 비공개 bucket
                )
        except Exception:
            # 이미 존재하거나 권한 문제 시 무시
            pass

    async def _validate_file_size(self, content: bytes, file_type: FileType) -> None:
        """파일 크기 검증"""
        max_size = FILE_SIZE_LIMITS.get(file_type, 10 * 1024 * 1024)
        if len(content) > max_size:
            raise FileSizeExceededError(
                f"파일 크기가 제한을 초과했습니다. "
                f"최대 {max_size / 1024 / 1024}MB까지 가능합니다."
            )

    async def upload_file(
        self,
        file: UploadFile,
        user_id: UUID,
        file_type: FileType,
    ) -> StorageUploadResponse:
        """
        파일을 Storage에 업로드

        Args:
            file: 업로드할 파일
            user_id: 사용자 ID
            file_type: 파일 타입 (TEMPLATE, MEMO)

        Returns:
            StorageUploadResponse: 업로드 결과

        Raises:
            FileValidationError: 파일 유효성 검증 실패
            Exception: Storage 업로드 실패
        """
        # 파일 유효성 검증
        valid, error_msg = await validate_file(file, file_type)
        if not valid:
            raise FileExtensionNotAllowedError(error_msg or "파일 검증 실패")

        # 파일 내용 읽기
        content = await file.read()

        # 파일 크기 검증
        await self._validate_file_size(content, file_type)

        # bucket 이름 및 파일 경로 생성
        bucket_name = self._get_bucket_name(file_type)
        extension = get_file_extension(file.filename or "")
        file_path = self._generate_file_path(user_id, file_type, extension)

        # bucket 존재 확인/생성
        await self._ensure_bucket_exists(bucket_name)

        try:
            # 파일 업로드 (service_role로 RLS bypass)
            result = self.admin_client.storage.from_(bucket_name).upload(
                file_path,
                content,
                file_options={
                    "content-type": file.content_type or "application/octet-stream",
                    "upsert": "false",  # httpx boolean encode error 방지
                }
            )

            # 공개 URL 가져오기 (bucket이 public인 경우)
            file_url = None
            try:
                file_url = self.client.storage.from_(bucket_name).get_public_url(file_path)
            except Exception:
                pass  # 비공개 bucket인 경우 무시

            return StorageUploadResponse(
                file_path=file_path,
                file_url=file_url,
                file_size=len(content),
                file_name=file.filename or "unknown",
                bucket=bucket_name,
                created_at=datetime.utcnow(),
            )

        except Exception as e:
            raise Exception("파일 업로드에 실패했습니다.")

    async def upload_template(
        self,
        file: UploadFile,
        user_id: UUID,
    ) -> StorageUploadResponse:
        """HWPX 템플릿 파일 업로드"""
        return await self.upload_file(file, user_id, FileType.TEMPLATE)

    async def upload_memo(
        self,
        file: UploadFile,
        user_id: UUID,
    ) -> StorageUploadResponse:
        """수기 메모 이미지 업로드"""
        return await self.upload_file(file, user_id, FileType.MEMO)

    async def upload_export(
        self,
        file_content: bytes,
        user_id: UUID,
        original_filename: str = "output.hwpx",
    ) -> StorageUploadResponse:
        """
        생성된 HWPX 파일 업로드 (바이트 직접 업로드)

        Args:
            file_content: 파일 내용 (bytes)
            user_id: 사용자 ID
            original_filename: 원본 파일명

        Returns:
            StorageUploadResponse: 업로드 결과
        """
        file_type = FileType.EXPORT

        # 파일 크기 검증
        await self._validate_file_size(file_content, file_type)

        # bucket 이름 및 파일 경로 생성
        bucket_name = self._get_bucket_name(file_type)
        extension = get_file_extension(original_filename)
        file_path = self._generate_file_path(user_id, file_type, extension)

        # bucket 존재 확인/생성
        await self._ensure_bucket_exists(bucket_name)

        try:
            # 파일 업로드 (service_role로 RLS bypass)
            result = self.admin_client.storage.from_(bucket_name).upload(
                file_path,
                file_content,
                file_options={
                    "content-type": "application/octet-stream",
                    "upsert": "false",
                }
            )

            return StorageUploadResponse(
                file_path=file_path,
                file_url=None,
                file_size=len(file_content),
                file_name=original_filename,
                bucket=bucket_name,
                created_at=datetime.utcnow(),
            )

        except Exception as e:
            raise Exception("파일 업로드에 실패했습니다.")

    async def get_signed_url(
        self,
        bucket: str,
        file_path: str,
        expires_in: int = 3600,
    ) -> StorageDownloadResponse:
        """
        서명된 다운로드 URL 생성

        Args:
            bucket: bucket 이름
            file_path: 파일 경로
            expires_in: URL 만료 시간 (초, 기본 1시간)

        Returns:
            StorageDownloadResponse: 다운로드 URL 정보
        """
        try:
            signed_url = self.client.storage.from_(bucket).create_signed_url(
                file_path,
                expires_in
            )

            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

            return StorageDownloadResponse(
                signed_url=signed_url.get("signedURL", signed_url),
                expires_at=expires_at,
                file_path=file_path,
                bucket=bucket,
            )
        except Exception as e:
            raise Exception("다운로드 URL 생성에 실패했습니다.")

    async def download_file(
        self,
        bucket: str,
        file_path: str,
    ) -> bytes:
        """
        파일 직접 다운로드 (바이트 반환)

        Args:
            bucket: bucket 이름
            file_path: 파일 경로

        Returns:
            bytes: 파일 내용
        """
        try:
            result = self.client.storage.from_(bucket).download(file_path)
            return result
        except Exception as e:
            raise Exception("파일 다운로드에 실패했습니다.")

    async def delete_file(
        self,
        bucket: str,
        file_path: str,
    ) -> StorageDeleteResponse:
        """
        파일 삭제

        Args:
            bucket: bucket 이름
            file_path: 파일 경로

        Returns:
            StorageDeleteResponse: 삭제 결과
        """
        try:
            result = self.admin_client.storage.from_(bucket).remove([file_path])

            return StorageDeleteResponse(
                success=True,
                file_path=file_path,
                bucket=bucket,
            )
        except Exception as e:
            raise Exception("파일 삭제에 실패했습니다.")

    async def get_file_info(
        self,
        bucket: str,
        file_path: str,
    ) -> Optional[FileInfoResponse]:
        """
        파일 정보 조회

        Args:
            bucket: bucket 이름
            file_path: 파일 경로

        Returns:
            FileInfoResponse: 파일 정보 (없으면 None)
        """
        try:
            # 파일 목록에서 검색
            path_parts = Path(file_path).parts
            if len(path_parts) > 1:
                prefix = f"{path_parts[0]}/"
                files = self.client.storage.from_(bucket).list(prefix)
            else:
                files = self.client.storage.from_(bucket).list()

            for file_info in files:
                if file_info.get("name") == Path(file_path).name:
                    return FileInfoResponse(
                        file_path=file_path,
                        file_name=file_info.get("name", Path(file_path).name),
                        file_size=file_info.get("metadata", {}).get("size", 0),
                        bucket=bucket,
                        content_type=file_info.get("metadata", {}).get("mimetype"),
                        created_at=datetime.fromisoformat(
                            file_info.get("created_at", datetime.utcnow().isoformat())
                        ),
                        updated_at=datetime.fromisoformat(
                            file_info.get("updated_at", datetime.utcnow().isoformat())
                        ) if file_info.get("updated_at") else None,
                    )

            return None
        except Exception:
            return None

    async def list_files(
        self,
        bucket: str,
        prefix: Optional[str] = None,
        limit: int = 100,
    ) -> FileListResponse:
        """
        파일 목록 조회

        Args:
            bucket: bucket 이름
            prefix: 검색 접두사 (폴더 경로 등)
            limit: 최대 조회 개수

        Returns:
            FileListResponse: 파일 목록
        """
        try:
            files = self.client.storage.from_(bucket).list(prefix)

            items = []
            for file_info in files[:limit]:
                items.append(
                    FileInfoResponse(
                        file_path=f"{prefix or ''}{file_info.get('name')}",
                        file_name=file_info.get("name", "unknown"),
                        file_size=file_info.get("metadata", {}).get("size", 0),
                        bucket=bucket,
                        content_type=file_info.get("metadata", {}).get("mimetype"),
                        created_at=datetime.fromisoformat(
                            file_info.get("created_at", datetime.utcnow().isoformat())
                        ),
                        updated_at=datetime.fromisoformat(
                            file_info.get("updated_at", datetime.utcnow().isoformat())
                        ) if file_info.get("updated_at") else None,
                    )
                )

            return FileListResponse(
                items=items,
                total=len(items),
                bucket=bucket,
                prefix=prefix,
            )
        except Exception as e:
            raise Exception("파일 목록 조회에 실패했습니다.")

    async def get_user_files(
        self,
        user_id: UUID,
        file_type: FileType,
        limit: int = 100,
    ) -> FileListResponse:
        """
        특정 사용자의 파일 목록 조회

        Args:
            user_id: 사용자 ID
            file_type: 파일 타입
            limit: 최대 조회 개수

        Returns:
            FileListResponse: 파일 목록
        """
        bucket_name = self._get_bucket_name(file_type)
        prefix = f"{user_id}/"
        return await self.list_files(bucket_name, prefix, limit)
