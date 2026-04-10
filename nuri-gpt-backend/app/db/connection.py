"""Supabase 데이터베이스 연결 관리 모듈

Supabase 클라이언트 생성 및 연결 관리
"""

import os
from typing import Optional

from supabase import Client, create_client
from supabase.lib.client_options import ClientOptions

from app.core.config import get_settings


class SupabaseManager:
    """Supabase 연결을 관리하는 싱글톤 클래스"""

    _instance: Optional["SupabaseManager"] = None
    _client: Optional[Client] = None

    def __new__(cls) -> "SupabaseManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._client is not None:
            return

        settings = get_settings()
        supabase_url = settings.supabase_url
        supabase_key = settings.supabase_key

        if not supabase_url or not supabase_key:
            raise ValueError(
                "Supabase URL과 API 키가 설정되지 않았습니다. "
                "환경 변수 SUPABASE_URL과 SUPABASE_KEY를 확인하세요."
            )

        options = ClientOptions(
            schema="public",
            headers={},
            auto_refresh_token=True,
            persist_session=True,
        )

        self._client = create_client(supabase_url, supabase_key, options)

    @property
    def client(self) -> Client:
        """Supabase 클라이언트 인스턴스 반환"""
        if self._client is None:
            raise RuntimeError("Supabase 클라이언트가 초기화되지 않았습니다.")
        return self._client

    async def health_check(self) -> bool:
        """Supabase 연결 상태 확인"""
        try:
            # 간단한 쿼리로 연결 확인
            response = self._client.table("users").select("count", count="exact").limit(1).execute()
            return True
        except Exception:
            return False


def get_supabase_client() -> Client:
    """Supabase 클라이언트를 반환하는 의존성 함수"""
    manager = SupabaseManager()
    return manager.client


def get_supabase_admin_client() -> Client:
    """service_role 키를 사용하는 관리자 Supabase 클라이언트 반환 (RLS bypass)"""
    settings = get_settings()
    supabase_url = settings.supabase_url
    service_key = settings.supabase_service_key

    if not supabase_url or not service_key:
        raise ValueError(
            "SUPABASE_URL 또는 SUPABASE_SERVICE_KEY가 설정되지 않았습니다."
        )

    return create_client(supabase_url, service_key)
