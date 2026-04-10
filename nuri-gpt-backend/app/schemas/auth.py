"""Authentication Schemas

인증/인가 관련 API 요청/응답 스키마
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """로그인 요청 스키마"""

    email: EmailStr = Field(..., description="사용자 이메일")
    password: str = Field(..., min_length=8, description="사용자 비밀번호")


class SignupRequest(BaseModel):
    """회원가입 요청 스키마"""

    email: EmailStr = Field(..., description="사용자 이메일")
    password: str = Field(..., min_length=8, description="사용자 비밀번호")
    name: str = Field(..., min_length=1, max_length=100, description="사용자 이름")
    kindergarten_name: Optional[str] = Field(None, description="유치원/어린이집 이름")


class UserAuthInfo(BaseModel):
    """인증 응답에 포함되는 사용자 정보"""

    id: UUID = Field(..., description="사용자 ID")
    email: EmailStr = Field(..., description="사용자 이메일")
    name: str = Field(..., description="사용자 이름")


class TokenResponse(BaseModel):
    """로그인/토큰 갱신 응답 스키마

    access_token은 응답 바디에 포함 (메모리 저장용)
    refresh_token은 httpOnly 쿠키로만 발급 (보안)
    """

    access_token: str = Field(..., description="JWT 액세스 토큰")
    token_type: str = Field(default="bearer", description="토큰 타입")
    expires_in: int = Field(..., description="토큰 만료까지 초 단위 시간")
    user: UserAuthInfo = Field(..., description="사용자 정보")


class LogoutResponse(BaseModel):
    """로그아웃 응답 스키마"""

    message: str = Field(default="로그아웃되었습니다", description="로그아웃 성공 메시지")


class TokenPayload(BaseModel):
    """JWT 토큰 페이로드 스키마 (검증용)"""

    sub: str = Field(..., description="사용자 ID (subject)")
    email: Optional[str] = Field(None, description="사용자 이메일")
    exp: Optional[datetime] = Field(None, description="만료 시간")
    iat: Optional[datetime] = Field(None, description="발급 시간")
