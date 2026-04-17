"""JWT 로컬 검증 모듈

Supabase JWT를 로컬에서 서명 검증하여 원격 Auth API 호출을 생략한다.
검증 실패 시 원격 fallback은 호출부에서 처리한다.
"""

import time
from typing import Any, Dict, Optional

import jwt

from app.core.config import get_settings

# Supabase JWT 기본 클레임
SUPABASE_AUDIENCE = "authenticated"
ALLOWED_ALGORITHMS = ["HS256"]


class JWTVerificationError(Exception):
    """JWT 검증 실패 시 발생하는 예외"""
    pass


def verify_jwt_locally(token: str) -> Dict[str, Any]:
    """Supabase JWT를 로컬에서 서명 검증하고 클레임을 반환한다.

    검증 항목:
    - 서명 (HS256 + JWT secret)
    - 만료 (exp)
    - 수신자 (aud = "authenticated")
    - 발급자 (iss = {SUPABASE_URL}/auth/v1, 설정 시)

    Args:
        token: JWT access token 문자열

    Returns:
        검증된 JWT 클레임 dict

    Raises:
        JWTVerificationError: 검증 실패 시
    """
    settings = get_settings()

    if not settings.supabase_jwt_secret:
        raise JWTVerificationError("SUPABASE_JWT_SECRET이 설정되지 않았습니다")

    verify_options: Dict[str, bool] = {
        "require": ["exp", "aud", "sub"],
    }

    try:
        payload = jwt.decode(
            jwt=token,
            key=settings.supabase_jwt_secret,
            algorithms=ALLOWED_ALGORITHMS,
            audience=SUPABASE_AUDIENCE,
            issuer=settings.supabase_issuer,
            options=verify_options,
        )
    except jwt.ExpiredSignatureError as e:
        raise JWTVerificationError(f"토큰이 만료되었습니다: {e}") from e
    except jwt.InvalidAudienceError as e:
        raise JWTVerificationError(f"잘못된 audience: {e}") from e
    except jwt.InvalidIssuerError as e:
        raise JWTVerificationError(f"잘못된 issuer: {e}") from e
    except jwt.InvalidSignatureError as e:
        raise JWTVerificationError(f"서명 검증 실패: {e}") from e
    except jwt.DecodeError as e:
        raise JWTVerificationError(f"JWT 디코딩 실패: {e}") from e
    except jwt.InvalidTokenError as e:
        raise JWTVerificationError(f"유효하지 않은 토큰: {e}") from e

    return payload


def extract_user_from_payload(payload: Dict[str, Any]) -> Dict[str, str]:
    """JWT payload에서 current_user dict를 구성한다.

    get_current_user가 반환하는 형식과 동일하게 맞춘다:
    {"id": ..., "email": ..., "metadata": ...}
    """
    sub = payload.get("sub", "")
    email = payload.get("email", "")

    # Supabase JWT: user_metadata가 최상위 또는 app_metadata 내에 존재 가능
    metadata = payload.get("user_metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}

    return {
        "id": sub,
        "email": email,
        "metadata": metadata,
    }
