from typing import Optional

from fastapi import HTTPException, status


class AuthenticationError(HTTPException):
    """인증 실패 예외"""

    def __init__(self, detail: str = "인증에 실패했습니다"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(HTTPException):
    """권한 부족 예외"""

    def __init__(self, detail: str = "접근 권한이 없습니다"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class ResourceNotFoundError(HTTPException):
    """리소스 미존재 예외"""

    def __init__(self, resource: str = "리소스", detail: Optional[str] = None):
        message = detail or f"{resource}를 찾을 수 없습니다"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message,
        )


class ValidationError(HTTPException):
    """입력 데이터 검증 실패 예외"""

    def __init__(self, detail: str = "입력 데이터가 유효하지 않습니다"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )


class ExternalAPIError(HTTPException):
    """외부 API 호출 실패 예외"""

    def __init__(self, service: str = "외부 서비스", detail: Optional[str] = None):
        message = detail or f"{service} 연결에 실패했습니다"
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=message,
        )
