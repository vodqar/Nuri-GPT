"""Upload API Endpoints

메모/템플릿 업로드 API 엔드포인트
- POST /upload/memo       : 수기 메모 이미지 업로드 + OCR
- POST /upload/memo/text  : 텍스트 직접 입력 + 정규화
- POST /upload/template   : 빈 템플릿 이미지 업로드 + 파싱 검증 + DB 등록
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, status

from app.core.dependencies import (
    get_current_user,
    get_ocr_service,
    get_storage_service,
    get_template_repository,
    get_vision_service,
    get_usage_service,
)
from app.db.models.template import TemplateCreate
from app.db.repositories.template_repository import TemplateRepository
from app.schemas.upload import (
    MemoUploadResponse,
    TemplateAnalyzeResponse,
    TemplateUploadResponse,
    TextMemoRequest,
    TextMemoResponse,
)
from app.services.ocr import OcrService
from app.services.vision import VisionService
from app.services.storage import StorageService
from app.services.usage_service import UsageService
from app.utils.exceptions import ExternalAPIError, ValidationError
from app.core.rate_limiter import limiter

router = APIRouter()


@router.post(
    "/upload/memo",
    response_model=MemoUploadResponse,
    summary="수기 메모 이미지 업로드",
    description="수기 메모 이미지를 Storage에 저장하고 OCR로 텍스트를 추출합니다.",
)
@limiter.limit("20/minute")
async def upload_memo(
    request: Request,
    file: UploadFile,
    current_user: dict = Depends(get_current_user),
    storage_service: StorageService = Depends(get_storage_service),
    ocr_service: OcrService = Depends(get_ocr_service),
    usage_service: UsageService = Depends(get_usage_service),
):
    """수기 메모 이미지 업로드 + OCR 텍스트 추출"""
    from uuid import UUID
    from app.utils.file_validator import FileType, validate_file

    user_id = UUID(current_user["id"])

    # 1. 할당량 확인
    is_available = await usage_service.check_quota_available(user_id, "vision_analyze")
    if not is_available:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="일일 분석 할당량을 모두 소진했습니다. 내일 다시 시도해주세요."
        )

    # 파일 유효성 사전 검증
    valid, error_msg = await validate_file(file, FileType.MEMO)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_msg or "유효하지 않은 파일입니다.",
        )

    # 파일 내용 읽기
    file_bytes = await file.read()

    # Storage에 업로드 (UploadFile 객체 재구성)
    from io import BytesIO
    file.file = BytesIO(file_bytes)
    file.file.seek(0)

    try:
        storage_result = await storage_service.upload_memo(file=file, user_id=user_id)
        
        # OCR 텍스트 추출
        mime_type = file.content_type or "image/jpeg"
        extracted_text = ocr_service.extract_text_from_image(file_bytes, mime_type=mime_type)
        normalized_text = ocr_service.normalize_text(extracted_text)

        # 성공 시 사용량 증가
        await usage_service.increment_usage(user_id, "vision_analyze", status="success")

        return MemoUploadResponse(
            storage_info=storage_result,
            extracted_text=extracted_text,
            normalized_text=normalized_text,
        )

    except Exception as e:
        # 실패 시 실패 카운트 증가
        await usage_service.increment_usage(user_id, "vision_analyze", status="fail")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="업로드 또는 OCR 처리에 실패했습니다.",
        )


@router.post(
    "/upload/memo/text",
    response_model=TextMemoResponse,
    summary="텍스트 메모 정규화",
    description="교사가 직접 입력한 텍스트를 정규화합니다.",
)
async def upload_memo_text(
    request: TextMemoRequest,
    current_user: dict = Depends(get_current_user),
    ocr_service: OcrService = Depends(get_ocr_service),
):
    """텍스트 직접 입력 → 정규화 처리"""
    normalized_text = ocr_service.normalize_text(request.text)

    return TextMemoResponse(
        original_text=request.text,
        normalized_text=normalized_text,
        child_name=request.child_name,
    )


@router.post(
    "/upload/template/analyze",
    response_model=TemplateAnalyzeResponse,
    summary="템플릿 이미지 분석 (저장 없음)",
    description="템플릿 이미지를 Vision API로 분석하여 계층 구조 JSON만 반환합니다. 저장은 하지 않습니다.",
)
@limiter.limit("10/minute")
async def analyze_template(
    request: Request,
    file: UploadFile,
    current_user: dict = Depends(get_current_user),
    vision_service: VisionService = Depends(get_vision_service),
    usage_service: UsageService = Depends(get_usage_service),
):
    """템플릿 이미지 업로드 + Vision LLM 파싱 → structure_json 반환 (저장 X)"""
    from app.utils.file_validator import FileType, validate_file
    user_id = UUID(current_user["id"])

    # 할당량 확인
    is_available = await usage_service.check_quota_available(user_id, "vision_analyze")
    if not is_available:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="일일 분석 할당량을 모두 소진했습니다. 내일 다시 시도해주세요."
        )

    valid, error_msg = await validate_file(file, FileType.TEMPLATE)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_msg or "유효하지 않은 파일입니다.",
        )

    file_bytes = await file.read()
    mime_type = file.content_type or "image/jpeg"

    try:
        structure_json = vision_service.extract_template_structure(file_bytes, mime_type)
        # 성공 시 사용량 증가
        await usage_service.increment_usage(user_id, "vision_analyze", status="success")
        return TemplateAnalyzeResponse(structure_json=structure_json)
    except Exception as e:
        # 실패 시 실패 카운트 증가
        await usage_service.increment_usage(user_id, "vision_analyze", status="fail")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="템플릿 구조 추출에 실패했습니다.",
        )


@router.post(
    "/upload/template",
    response_model=TemplateUploadResponse,
    summary="템플릿 이미지 업로드",
    description="템플릿 이미지를 Storage에 저장하고 Vision API를 통해 계층 구조를 추출한 뒤 DB에 등록합니다.",
)
async def upload_template(
    file: UploadFile,
    template_name: str = Form(
        ..., min_length=1, max_length=100, description="템플릿 이름"
    ),
    current_user: dict = Depends(get_current_user),
    storage_service: StorageService = Depends(get_storage_service),
    template_repo: TemplateRepository = Depends(get_template_repository),
    vision_service: VisionService = Depends(get_vision_service),
    usage_service: UsageService = Depends(get_usage_service),
):
    """빈 템플릿 이미지 업로드 + Vision LLM 파싱 + DB 등록"""
    from uuid import UUID
    from app.utils.file_validator import FileType, validate_file

    user_id = UUID(current_user["id"])

    # 할당량 확인
    is_available = await usage_service.check_quota_available(user_id, "vision_analyze")
    if not is_available:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="일일 분석 할당량을 모두 소진했습니다. 내일 다시 시도해주세요."
        )

    valid, error_msg = await validate_file(file, FileType.TEMPLATE)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_msg or "유효하지 않은 파일입니다.",
        )

    file_bytes = await file.read()
    mime_type = file.content_type or "image/jpeg"

    try:
        # Vision LLM을 통한 구조 추출
        structure_json = vision_service.extract_template_structure(file_bytes, mime_type)

        # Storage에 원본 이미지 업로드 (UploadFile 객체 재구성)
        from io import BytesIO
        file.file = BytesIO(file_bytes)
        file.file.seek(0)
        
        storage_result = await storage_service.upload_template(file=file, user_id=user_id)

        # DB에 템플릿 메타 등록
        template_data = TemplateCreate(
            user_id=user_id,
            name=template_name,
            template_type="observation_log",
            structure_json=structure_json,
            file_storage_path=storage_result.file_path,
            is_default=False,
        )

        template_in_db = await template_repo.create(template_data)
        
        # 성공 시 사용량 증가
        await usage_service.increment_usage(user_id, "vision_analyze", status="success")

        return TemplateUploadResponse(
            storage_info=storage_result,
            template_id=template_in_db.id,
            template_name=template_in_db.name,
            structure_json=structure_json,
        )

    except Exception as e:
        # 실패 시 실패 카운트 증가
        await usage_service.increment_usage(user_id, "vision_analyze", status="fail")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="템플릿 처리 및 등록에 실패했습니다.",
        )
