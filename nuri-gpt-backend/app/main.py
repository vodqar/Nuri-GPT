"""
Nuri-GPT FastAPI 애플리케이션 메인 모듈

보육교사를 위한 AI 기반 관찰일지 자동 작성 서비스
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.bootstrap import router as bootstrap_router
from app.api.endpoints.generate import router as generate_router
from app.api.endpoints.greeting import router as greeting_router
from app.api.endpoints.journals import router as journals_router
from app.api.endpoints.upload import router as upload_router
from app.api.endpoints.template import router as template_router
from app.api.endpoints.user import router as user_router
from app.core.config import get_settings
from app.schemas.health import HealthCheckResponse
from app.utils.exceptions import AuthenticationError, AuthorizationError, ExternalAPIError, ResourceNotFoundError, ValidationError

# 서버 시작 시간 (uptime 계산용)
_start_time: float = 0.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 수명 주기 관리"""
    global _start_time
    # 시작 이벤트
    _start_time = time.time()
    settings = get_settings()
    print(f"🚀 {settings.app_name} v{settings.app_version} 시작")
    print(f"📍 환경: {'개발' if settings.debug else '프로덕션'}")
    yield
    # 종료 이벤트
    print(f"👋 {settings.app_name} 종료")


# FastAPI 애플리케이션 인스턴스 생성
settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="보육교사를 위한 AI 기반 관찰일지 자동 작성 서비스",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS 미들웨어 설정
_cors_origins_list = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
_cors_kwargs: dict = dict(
    allow_origins=_cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)
if settings.debug:
    # 개발 환경: IDE preview 등 127.0.0.1의 임의 포트 허용
    _cors_kwargs["allow_origin_regex"] = r"http://(localhost|127\.0\.0\.1)(:\d+)?"
app.add_middleware(CORSMiddleware, **_cors_kwargs)


# V-09: 보안 헤더 미들웨어
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if not settings.debug:
            response.headers["Content-Security-Policy"] = "default-src 'self'"
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        return response

app.add_middleware(SecurityHeadersMiddleware)


# V-08: Rate Limiting
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from app.core.rate_limiter import limiter

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# 라우터 등록
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(upload_router, prefix="/api", tags=["Upload"])
app.include_router(template_router, prefix="/api/templates", tags=["Template"])
app.include_router(generate_router, prefix="/api/generate", tags=["Generate"])
app.include_router(greeting_router, prefix="/api/greeting", tags=["Greeting"])
app.include_router(journals_router, prefix="/api/journals", tags=["Journal"])
app.include_router(user_router, prefix="/api/users", tags=["User"])
app.include_router(bootstrap_router, prefix="/api/users/me", tags=["Bootstrap"])


# 예외 핸들러 등록
@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(request: Request, exc: AuthenticationError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "type": "authentication_error"},
        headers=exc.headers,
    )


@app.exception_handler(AuthorizationError)
async def authorization_exception_handler(request: Request, exc: AuthorizationError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "type": "authorization_error"},
    )


@app.exception_handler(ResourceNotFoundError)
async def not_found_exception_handler(request: Request, exc: ResourceNotFoundError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "type": "not_found_error"},
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "type": "validation_error"},
    )


@app.exception_handler(ExternalAPIError)
async def external_api_exception_handler(request: Request, exc: ExternalAPIError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "type": "external_api_error"},
    )


# 기본 헬스체크 엔드포인트
@app.get("/", response_model=HealthCheckResponse, tags=["Health"])
@limiter.limit("60/minute")
async def root(request: Request):
    """루트 엔드포인트 - 기본 헬스체크"""
    uptime = time.time() - _start_time if _start_time > 0 else None
    return HealthCheckResponse(
        status="healthy",
        app_name=settings.app_name,
        version=settings.app_version,
        uptime_seconds=uptime,
    )


@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
@limiter.limit("60/minute")
async def health_check(request: Request):
    """헬스체크 엔드포인트"""
    uptime = time.time() - _start_time if _start_time > 0 else None
    return HealthCheckResponse(
        status="healthy",
        app_name=settings.app_name,
        version=settings.app_version,
        uptime_seconds=uptime,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
