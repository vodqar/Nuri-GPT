"""JWT 로컬 검증 단위 테스트

verify_jwt_locally / extract_user_from_payload / get_current_user 동작 검증
"""

import time
from unittest.mock import MagicMock, patch

import jwt as pyjwt
import pytest

from app.core.jwt_verify import (
    JWTVerificationError,
    extract_user_from_payload,
    verify_jwt_locally,
)
from app.utils.exceptions import AuthenticationError

# 테스트용 공통 상수
FAKE_JWT_SECRET = "test-secret-that-is-at-least-32-characters-long!!"
FAKE_SUPABASE_URL = "https://test-project.supabase.co"
FAKE_ISSUER = f"{FAKE_SUPABASE_URL}/auth/v1"
FAKE_USER_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
FAKE_EMAIL = "teacher@example.com"


def _make_token(
    secret: str = FAKE_JWT_SECRET,
    sub: str = FAKE_USER_ID,
    email: str = FAKE_EMAIL,
    exp_offset: int = 3600,
    aud: str = "authenticated",
    iss: str = FAKE_ISSUER,
    extra_claims: dict | None = None,
    algorithm: str = "HS256",
) -> str:
    """테스트용 Supabase 호환 JWT 생성"""
    now = int(time.time())
    payload = {
        "sub": sub,
        "email": email,
        "aud": aud,
        "iss": iss,
        "exp": now + exp_offset,
        "iat": now,
        "role": "authenticated",
        "user_metadata": {"name": "테스트교사"},
    }
    if extra_claims:
        payload.update(extra_claims)
    return pyjwt.encode(payload, secret, algorithm=algorithm)


# ── verify_jwt_locally 테스트 ──


def test_verify_valid_token():
    """유효한 토큰은 검증 성공하고 클레임을 반환한다"""
    token = _make_token()
    mock_settings = MagicMock()
    mock_settings.supabase_jwt_secret = FAKE_JWT_SECRET
    mock_settings.supabase_issuer = FAKE_ISSUER

    with patch("app.core.jwt_verify.get_settings", return_value=mock_settings):
        payload = verify_jwt_locally(token)

    assert payload["sub"] == FAKE_USER_ID
    assert payload["email"] == FAKE_EMAIL
    assert payload["aud"] == "authenticated"


def test_verify_expired_token_raises():
    """만료된 토큰은 JWTVerificationError를 발생시킨다"""
    token = _make_token(exp_offset=-10)
    mock_settings = MagicMock()
    mock_settings.supabase_jwt_secret = FAKE_JWT_SECRET
    mock_settings.supabase_issuer = FAKE_ISSUER

    with patch("app.core.jwt_verify.get_settings", return_value=mock_settings):
        with pytest.raises(JWTVerificationError, match="만료"):
            verify_jwt_locally(token)


def test_verify_tampered_signature_raises():
    """서명이 변조된 토큰은 JWTVerificationError를 발생시킨다"""
    token = _make_token(secret="wrong-secret-aaaaaaaaaaaaaaaaaaaaaaaaa")
    mock_settings = MagicMock()
    mock_settings.supabase_jwt_secret = FAKE_JWT_SECRET
    mock_settings.supabase_issuer = FAKE_ISSUER

    with patch("app.core.jwt_verify.get_settings", return_value=mock_settings):
        with pytest.raises(JWTVerificationError, match="서명"):
            verify_jwt_locally(token)


def test_verify_wrong_audience_raises():
    """aud가 'authenticated'가 아니면 검증 실패한다"""
    token = _make_token(aud="wrong-audience")
    mock_settings = MagicMock()
    mock_settings.supabase_jwt_secret = FAKE_JWT_SECRET
    mock_settings.supabase_issuer = FAKE_ISSUER

    with patch("app.core.jwt_verify.get_settings", return_value=mock_settings):
        with pytest.raises(JWTVerificationError, match="audience"):
            verify_jwt_locally(token)


def test_verify_wrong_issuer_raises():
    """iss가 기대값과 다르면 검증 실패한다"""
    token = _make_token(iss="https://other-project.supabase.co/auth/v1")
    mock_settings = MagicMock()
    mock_settings.supabase_jwt_secret = FAKE_JWT_SECRET
    mock_settings.supabase_issuer = FAKE_ISSUER

    with patch("app.core.jwt_verify.get_settings", return_value=mock_settings):
        with pytest.raises(JWTVerificationError, match="issuer"):
            verify_jwt_locally(token)


def test_verify_no_secret_configured_raises():
    """JWT secret이 설정되지 않으면 JWTVerificationError를 발생시킨다"""
    token = _make_token()
    mock_settings = MagicMock()
    mock_settings.supabase_jwt_secret = None
    mock_settings.supabase_issuer = FAKE_ISSUER

    with patch("app.core.jwt_verify.get_settings", return_value=mock_settings):
        with pytest.raises(JWTVerificationError, match="SUPABASE_JWT_SECRET"):
            verify_jwt_locally(token)


def test_verify_malformed_token_raises():
    """잘못된 형식의 토큰은 JWTVerificationError를 발생시킨다"""
    mock_settings = MagicMock()
    mock_settings.supabase_jwt_secret = FAKE_JWT_SECRET
    mock_settings.supabase_issuer = FAKE_ISSUER

    with patch("app.core.jwt_verify.get_settings", return_value=mock_settings):
        with pytest.raises(JWTVerificationError, match="디코딩"):
            verify_jwt_locally("not.a.valid.jwt")


# ── extract_user_from_payload 테스트 ──


def test_extract_user_from_payload():
    """payload에서 current_user dict를 올바르게 추출한다"""
    payload = {
        "sub": FAKE_USER_ID,
        "email": FAKE_EMAIL,
        "user_metadata": {"name": "테스트교사"},
        "role": "authenticated",
    }
    result = extract_user_from_payload(payload)
    assert result == {
        "id": FAKE_USER_ID,
        "email": FAKE_EMAIL,
        "metadata": {"name": "테스트교사"},
    }


def test_extract_user_missing_metadata_defaults_empty():
    """user_metadata가 없으면 빈 dict로 기본값 처리한다"""
    payload = {
        "sub": FAKE_USER_ID,
        "email": FAKE_EMAIL,
    }
    result = extract_user_from_payload(payload)
    assert result["metadata"] == {}


# ── get_current_user 통합 동작 테스트 ──


def test_get_current_user_local_verify_success():
    """로컬 검증 성공 시 원격 호출 없이 사용자 반환"""
    from app.core.dependencies import get_current_user

    token = _make_token()
    mock_settings = MagicMock()
    mock_settings.auth_local_verify = True
    mock_settings.supabase_jwt_secret = FAKE_JWT_SECRET
    mock_settings.supabase_issuer = FAKE_ISSUER

    mock_supabase = MagicMock()

    with patch("app.core.dependencies.get_settings", return_value=mock_settings), \
         patch("app.core.jwt_verify.get_settings", return_value=mock_settings):
        result = _run_get_current_user(get_current_user, token, mock_supabase)

    assert result["id"] == FAKE_USER_ID
    assert result["email"] == FAKE_EMAIL
    # 원격 호출이 발생하지 않았는지 확인
    mock_supabase.auth.get_user.assert_not_called()


def test_get_current_user_expired_rejected_without_fallback():
    """만료 토큰은 원격 fallback 없이 즉시 거부한다"""
    from app.core.dependencies import get_current_user

    token = _make_token(exp_offset=-10)
    mock_settings = MagicMock()
    mock_settings.auth_local_verify = True
    mock_settings.supabase_jwt_secret = FAKE_JWT_SECRET
    mock_settings.supabase_issuer = FAKE_ISSUER

    mock_supabase = MagicMock()

    with patch("app.core.dependencies.get_settings", return_value=mock_settings), \
         patch("app.core.jwt_verify.get_settings", return_value=mock_settings):
        with pytest.raises(AuthenticationError):
            _run_get_current_user(get_current_user, token, mock_supabase)

    mock_supabase.auth.get_user.assert_not_called()


def test_get_current_user_local_disabled_uses_remote():
    """AUTH_LOCAL_VERIFY=false 시 원격 Auth API를 사용한다"""
    from app.core.dependencies import get_current_user

    token = _make_token()
    mock_settings = MagicMock()
    mock_settings.auth_local_verify = False
    mock_settings.supabase_jwt_secret = FAKE_JWT_SECRET
    mock_settings.supabase_issuer = FAKE_ISSUER

    mock_user = MagicMock()
    mock_user.id = FAKE_USER_ID
    mock_user.email = FAKE_EMAIL
    mock_user.user_metadata = {"name": "테스트교사"}
    mock_response = MagicMock()
    mock_response.user = mock_user
    mock_supabase = MagicMock()
    mock_supabase.auth.get_user.return_value = mock_response

    with patch("app.core.dependencies.get_settings", return_value=mock_settings):
        result = _run_get_current_user(get_current_user, token, mock_supabase)

    assert result["id"] == FAKE_USER_ID
    mock_supabase.auth.get_user.assert_called_once()


def test_get_current_user_no_secret_uses_remote():
    """JWT secret 미설정 시 원격 Auth API로 fallback한다"""
    from app.core.dependencies import get_current_user

    token = _make_token()
    mock_settings = MagicMock()
    mock_settings.auth_local_verify = True
    mock_settings.supabase_jwt_secret = None
    mock_settings.supabase_issuer = FAKE_ISSUER

    mock_user = MagicMock()
    mock_user.id = FAKE_USER_ID
    mock_user.email = FAKE_EMAIL
    mock_user.user_metadata = {"name": "테스트교사"}
    mock_response = MagicMock()
    mock_response.user = mock_user
    mock_supabase = MagicMock()
    mock_supabase.auth.get_user.return_value = mock_response

    with patch("app.core.dependencies.get_settings", return_value=mock_settings):
        result = _run_get_current_user(get_current_user, token, mock_supabase)

    assert result["id"] == FAKE_USER_ID
    mock_supabase.auth.get_user.assert_called_once()


def test_get_current_user_iss_mismatch_falls_back_to_remote():
    """issuer 불일치 시 원격 Auth API로 fallback한다"""
    from app.core.dependencies import get_current_user

    token = _make_token(iss="https://other-project.supabase.co/auth/v1")
    mock_settings = MagicMock()
    mock_settings.auth_local_verify = True
    mock_settings.supabase_jwt_secret = FAKE_JWT_SECRET
    mock_settings.supabase_issuer = FAKE_ISSUER

    mock_user = MagicMock()
    mock_user.id = FAKE_USER_ID
    mock_user.email = FAKE_EMAIL
    mock_user.user_metadata = {}
    mock_response = MagicMock()
    mock_response.user = mock_user
    mock_supabase = MagicMock()
    mock_supabase.auth.get_user.return_value = mock_response

    with patch("app.core.dependencies.get_settings", return_value=mock_settings), \
         patch("app.core.jwt_verify.get_settings", return_value=mock_settings):
        result = _run_get_current_user(get_current_user, token, mock_supabase)

    assert result["id"] == FAKE_USER_ID
    mock_supabase.auth.get_user.assert_called_once()


# ── 헬퍼 ──


def _run_get_current_user(func, token: str, mock_supabase):
    """get_current_user를 직접 호출하기 위한 헬퍼

    FastAPI Depends 대신 직접 인자를 전달한다.
    """
    from fastapi.security import HTTPAuthorizationCredentials

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )
    import asyncio
    return asyncio.run(func(credentials=credentials, supabase=mock_supabase))
