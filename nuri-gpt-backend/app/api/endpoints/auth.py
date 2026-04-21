"""Auth API Endpoints

인증/인가 관련 API 엔드포인트
- POST /api/auth/login: 로그인 (access_token + httpOnly refresh_token 쿠키)
- POST /api/auth/refresh: 토큰 갱신 (httpOnly 쿠키 기반)
- POST /api/auth/logout: 로그아웃 (쿠키 삭제)
"""

from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from gotrue.errors import AuthApiError
from supabase import Client

from app.db.connection import get_supabase_client
from app.db.repositories.user_preference_repository import UserPreferenceRepository
from app.schemas.auth import LoginRequest, LogoutResponse, SignupRequest, TokenResponse, UserAuthInfo
from app.utils.exceptions import AuthenticationError
from app.core.rate_limiter import limiter

router = APIRouter(tags=["Authentication"])

# 쿠키 설정 상수
REFRESH_TOKEN_COOKIE_NAME = "refresh_token"
REMEMBER_ME_COOKIE_NAME = "remember_me"
COOKIE_MAX_AGE = 7 * 24 * 60 * 60  # 7일
COOKIE_PATH = "/api/auth"


def _set_auth_cookies(response: Response, refresh_token: str, remember: bool) -> None:
    from app.core.config import get_settings
    _settings = get_settings()

    cookie_kwargs = {
        "httponly": True,
        "secure": not _settings.debug,  # 프로덕션: True, 개발: False
        "samesite": "strict" if not _settings.debug else "lax",
        "path": COOKIE_PATH,
    }

    if remember:
        response.set_cookie(
            key=REFRESH_TOKEN_COOKIE_NAME,
            value=refresh_token,
            max_age=COOKIE_MAX_AGE,
            **cookie_kwargs,
        )
        response.set_cookie(
            key=REMEMBER_ME_COOKIE_NAME,
            value="1",
            max_age=COOKIE_MAX_AGE,
            **cookie_kwargs,
        )
        return

    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        value=refresh_token,
        **cookie_kwargs,
    )
    response.set_cookie(
        key=REMEMBER_ME_COOKIE_NAME,
        value="0",
        **cookie_kwargs,
    )


def _delete_auth_cookies(response: Response) -> None:
    response.delete_cookie(key=REFRESH_TOKEN_COOKIE_NAME, path=COOKIE_PATH)
    response.delete_cookie(key=REMEMBER_ME_COOKIE_NAME, path=COOKIE_PATH)


@router.post("/signup", response_model=TokenResponse)
@limiter.limit("5/minute")
async def signup(
    request: Request,
    signup_data: SignupRequest,
    response: Response,
    supabase: Client = Depends(get_supabase_client),
    pref_repo: UserPreferenceRepository = Depends(lambda: UserPreferenceRepository(get_supabase_client())),
) -> TokenResponse:
    """회원가입

    - Supabase Auth에 사용자 생성
    - 자동 로그인 처리 (access_token + refresh_token 쿠키)
    """
    try:
        # Supabase Auth에 사용자 생성
        auth_response = supabase.auth.sign_up({
            "email": signup_data.email,
            "password": signup_data.password,
            "options": {
                "data": {
                    "name": signup_data.name,
                    "kindergarten_name": signup_data.kindergarten_name or "",
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
            _set_auth_cookies(response=response, refresh_token=session.refresh_token, remember=True)

            preferences = await pref_repo.get_all(user.id)
            return TokenResponse(
                access_token=session.access_token,
                token_type="bearer",
                expires_in=session.expires_in,
                user=UserAuthInfo(
                    id=user.id,
                    email=user.email or "",
                    name=user.user_metadata.get("name", "") if user.user_metadata else "",
                    preferences=preferences,
                ),
            )
        else:
            # 이메일 확인이 필요한 경우 (Supabase 설정에 따라)
            raise AuthenticationError("이메일 확인이 필요합니다. 메일을 확인해주세요.")

    except AuthApiError as e:
        if "User already registered" in str(e):
            raise AuthenticationError("이미 등록된 이메일입니다")
        raise AuthenticationError("회원가입 중 오류가 발생했습니다.")
    except Exception as e:
        raise AuthenticationError("회원가입 중 오류가 발생했습니다.")


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    login_data: LoginRequest,
    response: Response,
    supabase: Client = Depends(get_supabase_client),
    pref_repo: UserPreferenceRepository = Depends(lambda: UserPreferenceRepository(get_supabase_client())),
) -> TokenResponse:
    """사용자 로그인

    - access_token은 응답 바디에 포함 (프론트 메모리 저장)
    - refresh_token은 httpOnly Secure SameSite 쿠키로 발급
    """
    try:
        # Supabase Auth로 로그인
        auth_response = supabase.auth.sign_in_with_password({
            "email": login_data.email,
            "password": login_data.password,
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
        _set_auth_cookies(
            response=response,
            refresh_token=session.refresh_token,
            remember=login_data.remember,
        )

        preferences = await pref_repo.get_all(user.id)
        return TokenResponse(
            access_token=session.access_token,
            token_type="bearer",
            expires_in=session.expires_in,
            user=UserAuthInfo(
                id=user.id,
                email=user.email or "",
                name=user.user_metadata.get("name", "") if user.user_metadata else "",
                preferences=preferences,
            ),
        )

    except AuthApiError as e:
        if "Invalid login" in str(e) or "Invalid email" in str(e):
            raise AuthenticationError("이메일 또는 비밀번호가 올바르지 않습니다")
        raise AuthenticationError("로그인 중 오류가 발생했습니다.")
    except Exception as e:
        raise AuthenticationError("로그인 중 오류가 발생했습니다.")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    response: Response,
    refresh_token: Optional[str] = Cookie(None, alias=REFRESH_TOKEN_COOKIE_NAME),
    remember_me: Optional[str] = Cookie(None, alias=REMEMBER_ME_COOKIE_NAME),
    supabase: Client = Depends(get_supabase_client),
    pref_repo: UserPreferenceRepository = Depends(lambda: UserPreferenceRepository(get_supabase_client())),
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
        # remember_me 쿠키가 없으면 기존 사용자 호환을 위해 persistent로 처리
        remember = remember_me != "0"
        _set_auth_cookies(response=response, refresh_token=session.refresh_token, remember=remember)

        preferences = await pref_repo.get_all(user.id)
        return TokenResponse(
            access_token=session.access_token,
            token_type="bearer",
            expires_in=session.expires_in,
            user=UserAuthInfo(
                id=user.id,
                email=user.email or "",
                name=user.user_metadata.get("name", "") if user.user_metadata else "",
                preferences=preferences,
            ),
        )

    except AuthApiError:
        # 쿠키 삭제 및 재로그인 요청
        _delete_auth_cookies(response)
        raise AuthenticationError("세션이 만료되었습니다. 다시 로그인해주세요.")
    except Exception as e:
        raise AuthenticationError("토큰 갱신 중 오류가 발생했습니다.")


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
        _delete_auth_cookies(response)

        return LogoutResponse(message="로그아웃되었습니다")

    except Exception as e:
        # 쿠키는 삭제하고 에러 반환
        _delete_auth_cookies(response)
        raise AuthenticationError("로그아웃 중 오류가 발생했습니다.")
