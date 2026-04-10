"""Auth API Endpoints

인증/인가 관련 API 엔드포인트
- POST /api/auth/login: 로그인 (access_token + httpOnly refresh_token 쿠키)
- POST /api/auth/refresh: 토큰 갱신 (httpOnly 쿠키 기반)
- POST /api/auth/logout: 로그아웃 (쿠키 삭제)
"""

from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from gotrue.errors import AuthApiError
from supabase import Client

from app.core.config import get_settings
from app.db.connection import get_supabase_client
from app.schemas.auth import LoginRequest, LogoutResponse, SignupRequest, TokenResponse, UserAuthInfo
from app.utils.exceptions import AuthenticationError

router = APIRouter(tags=["Authentication"])

# 쿠키 설정 상수
REFRESH_TOKEN_COOKIE_NAME = "refresh_token"
COOKIE_MAX_AGE = 7 * 24 * 60 * 60  # 7일
COOKIE_PATH = "/api/auth"


@router.post("/signup", response_model=TokenResponse)
async def signup(
    request: SignupRequest,
    response: Response,
    supabase: Client = Depends(get_supabase_client),
) -> TokenResponse:
    """회원가입

    - Supabase Auth에 사용자 생성
    - 자동 로그인 처리 (access_token + refresh_token 쿠키)
    """
    try:
        # Supabase Auth에 사용자 생성
        auth_response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {
                    "name": request.name,
                    "kindergarten_name": request.kindergarten_name or "",
                }
            }
        })

        if not auth_response.user:
            raise AuthenticationError("회원가입에 실패했습니다")

        # 세션이 자동 생성되면 쿠키 설정
        if auth_response.session:
            session = auth_response.session
            user = auth_response.user

            # TODO: [배포 전 필수] HTTPS 환경에서는 아래 두 값을 변경할 것
            # secure=True, samesite="strict"
            response.set_cookie(
                key=REFRESH_TOKEN_COOKIE_NAME,
                value=session.refresh_token,
                httponly=True,
                secure=False,   # 개발/베타: HTTP localhost 환경
                samesite="lax", # 개발/베타: 프론트-백 포트 분리 환경
                max_age=COOKIE_MAX_AGE,
                path=COOKIE_PATH,
            )

            return TokenResponse(
                access_token=session.access_token,
                token_type="bearer",
                expires_in=session.expires_in,
                user=UserAuthInfo(
                    id=user.id,
                    email=user.email or "",
                    name=user.user_metadata.get("name", "") if user.user_metadata else "",
                ),
            )
        else:
            # 이메일 확인이 필요한 경우 (Supabase 설정에 따라)
            raise AuthenticationError("이메일 확인이 필요합니다. 메일을 확인해주세요.")

    except AuthApiError as e:
        if "User already registered" in str(e):
            raise AuthenticationError("이미 등록된 이메일입니다")
        raise AuthenticationError(f"회원가입 중 오류가 발생했습니다: {str(e)}")
    except Exception as e:
        raise AuthenticationError(f"회원가입 중 오류가 발생했습니다: {str(e)}")


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    response: Response,
    supabase: Client = Depends(get_supabase_client),
) -> TokenResponse:
    """사용자 로그인

    - access_token은 응답 바디에 포함 (프론트 메모리 저장)
    - refresh_token은 httpOnly Secure SameSite 쿠키로 발급
    """
    try:
        # Supabase Auth로 로그인
        auth_response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password,
        })

        if not auth_response.session:
            raise AuthenticationError("로그인 세션 생성에 실패했습니다")

        session = auth_response.session
        user = auth_response.user

        if not user:
            raise AuthenticationError("사용자 정보를 찾을 수 없습니다")

        # refresh_token을 httpOnly 쿠키로 설정
        # SameSite=Strict로 CSRF 방어, Path 제한으로 /api/auth/* 에서만 사용
        # TODO: [배포 전 필수] HTTPS 환경에서는 아래 두 값을 변경할 것
        # secure=True, samesite="strict"
        response.set_cookie(
            key=REFRESH_TOKEN_COOKIE_NAME,
            value=session.refresh_token,
            httponly=True,
            secure=False,   # 개발/베타: HTTP localhost 환경
            samesite="lax", # 개발/베타: 프론트-백 포트 분리 환경
            max_age=COOKIE_MAX_AGE,
            path=COOKIE_PATH,
        )

        return TokenResponse(
            access_token=session.access_token,
            token_type="bearer",
            expires_in=session.expires_in,
            user=UserAuthInfo(
                id=user.id,
                email=user.email or "",
                name=user.user_metadata.get("name", "") if user.user_metadata else "",
            ),
        )

    except AuthApiError as e:
        if "Invalid login" in str(e) or "Invalid email" in str(e):
            raise AuthenticationError("이메일 또는 비밀번호가 올바르지 않습니다")
        raise AuthenticationError(f"로그인 중 오류가 발생했습니다: {str(e)}")
    except Exception as e:
        raise AuthenticationError(f"로그인 중 오류가 발생했습니다: {str(e)}")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    response: Response,
    refresh_token: Optional[str] = Cookie(None, alias=REFRESH_TOKEN_COOKIE_NAME),
    supabase: Client = Depends(get_supabase_client),
) -> TokenResponse:
    """토큰 갱신

    - httpOnly 쿠키에서 refresh_token을 읽어 새 토큰 발급
    - 새 refresh_token도 쿠키에 재설정 (rotation)
    """
    if not refresh_token:
        raise AuthenticationError("리프레시 토큰이 없습니다. 다시 로그인해주세요.")

    try:
        # refresh_token으로 새 세션 생성
        auth_response = supabase.auth.refresh_session(refresh_token)

        if not auth_response.session:
            raise AuthenticationError("세션 갱신에 실패했습니다")

        session = auth_response.session
        user = auth_response.user

        if not user:
            raise AuthenticationError("사용자 정보를 찾을 수 없습니다")

        # TODO: [배포 전 필수] HTTPS 환경에서는 아래 두 값을 변경할 것
        # secure=True, samesite="strict"
        # 새 refresh_token으로 쿠키 업데이트 (token rotation)
        response.set_cookie(
            key=REFRESH_TOKEN_COOKIE_NAME,
            value=session.refresh_token,
            httponly=True,
            secure=False,   # 개발/베타: HTTP localhost 환경
            samesite="lax", # 개발/베타: 프론트-백 포트 분리 환경
            max_age=COOKIE_MAX_AGE,
            path=COOKIE_PATH,
        )

        return TokenResponse(
            access_token=session.access_token,
            token_type="bearer",
            expires_in=session.expires_in,
            user=UserAuthInfo(
                id=user.id,
                email=user.email or "",
                name=user.user_metadata.get("name", "") if user.user_metadata else "",
            ),
        )

    except AuthApiError:
        # 쿠키 삭제 및 재로그인 요청
        response.delete_cookie(key=REFRESH_TOKEN_COOKIE_NAME, path=COOKIE_PATH)
        raise AuthenticationError("세션이 만료되었습니다. 다시 로그인해주세요.")
    except Exception as e:
        raise AuthenticationError(f"토큰 갱신 중 오류가 발생했습니다: {str(e)}")


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    response: Response,
    refresh_token: Optional[str] = Cookie(None, alias=REFRESH_TOKEN_COOKIE_NAME),
    supabase: Client = Depends(get_supabase_client),
) -> LogoutResponse:
    """사용자 로그아웃

    - Supabase 세션 무효화
    - httpOnly 쿠키 삭제
    """
    try:
        # refresh_token이 있으면 Supabase 세션도 무효화
        if refresh_token:
            try:
                supabase.auth.sign_out()
            except Exception:
                # 이미 만료된 세션이면 무시
                pass

        # 쿠키 삭제
        response.delete_cookie(
            key=REFRESH_TOKEN_COOKIE_NAME,
            path=COOKIE_PATH,
        )

        return LogoutResponse(message="로그아웃되었습니다")

    except Exception as e:
        # 쿠키는 삭제하고 에러 반환
        response.delete_cookie(key=REFRESH_TOKEN_COOKIE_NAME, path=COOKIE_PATH)
        raise AuthenticationError(f"로그아웃 중 오류가 발생했습니다: {str(e)}")
