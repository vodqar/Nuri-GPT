"""Upload API Endpoints

메모/템플릿 업로드 API 엔드포인트
- POST /upload/memo       : 수기 메모 이미지 업로드 + OCR
- POST /upload/memo/text  : 텍스트 직접 입력 + 정규화
- POST /upload/template   : 빈 템플릿 이미지 업로드 + 파싱 검증 + DB 등록
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status

from app.core.dependencies import (
    get_current_user,
    get_ocr_service,
    get_storage_service,
    get_template_repository,
    get_vision_service,
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
from app.utils.exceptions import ExternalAPIError, ValidationError

router = APIRouter()


@router.post(
    "/upload/memo",
    response_model=MemoUploadResponse,
    summary="수기 메모 이미지 업로드",
    description="수기 메모 이미지를 Storage에 저장하고 OCR로 텍스트를 추출합니다.",
)
async def upload_memo(
    file: UploadFile,
    current_user: dict = Depends(get_current_user),
    storage_service: StorageService = Depends(get_storage_service),
    ocr_service: OcrService = Depends(get_ocr_service),
):
    """수기 메모 이미지 업로드 + OCR 텍스트 추출"""
    from uuid import UUID
    from app.utils.file_validator import FileType, validate_file

    user_id = UUID(current_user["id"])

    # 파일 유효성 사전 검증
    valid, error_msg = await validate_file(file, FileType.MEMO)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_msg or "유효하지 않은 파일입니다.",
        )

    # 파일 내용 읽기 (Storage 업로드 및 OCR 모두에 재사용)
    file_bytes = await file.read()

    # Storage에 업로드 (UploadFile 객체 재구성)
    from io import BytesIO
    from fastapi import UploadFile as FastAPIUploadFile
    from starlette.datastructures import Headers

    file.file = BytesIO(file_bytes)
    file.file.seek(0)

    try:
        storage_result = await storage_service.upload_memo(file=file, user_id=user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"파일 Storage 저장 실패: {str(e)}",
        )

    # OCR 텍스트 추출
    mime_type = file.content_type or "image/jpeg"
    try:
        extracted_text = ocr_service.extract_text_from_image(file_bytes, mime_type=mime_type)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OCR 처리 실패: {str(e)}",
        )

    normalized_text = ocr_service.normalize_text(extracted_text)

    return MemoUploadResponse(
        storage_info=storage_result,
        extracted_text=extracted_text,
        normalized_text=normalized_text,
    )


@router.post(
    "/upload/memo/text",
    response_model=TextMemoResponse,
    summary="텍스트 메모 정규화",
    description="교사가 직접 입력한 텍스트를 정규화합니다.",
)
async def upload_memo_text(
    request: TextMemoRequest,
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
async def analyze_template(
    file: UploadFile,
    current_user: dict = Depends(get_current_user),
    vision_service: VisionService = Depends(get_vision_service),
):
    """템플릿 이미지 업로드 + Vision LLM 파싱 → structure_json 반환 (저장 X)"""
    from app.utils.file_validator import FileType, validate_file

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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"템플릿 구조 추출 실패: {str(e)}",
        )

    return TemplateAnalyzeResponse(structure_json=structure_json)


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
):
    """빈 템플릿 이미지 업로드 + Vision LLM 파싱 + DB 등록"""
    from uuid import UUID
    from app.utils.file_validator import FileType, validate_file

    user_id = UUID(current_user["id"])

    valid, error_msg = await validate_file(file, FileType.TEMPLATE)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_msg or "유효하지 않은 파일입니다.",
        )

    file_bytes = await file.read()
    mime_type = file.content_type or "image/jpeg"

    # Vision LLM을 통한 구조 추출
    try:
        structure_json = vision_service.extract_template_structure(file_bytes, mime_type)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"템플릿 구조 추출 실패: {str(e)}",
        )

    # Storage에 원본 이미지 업로드 (UploadFile 객체 재구성)
    from io import BytesIO
    file.file = BytesIO(file_bytes)
    file.file.seek(0)
    
    try:
        storage_result = await storage_service.upload_template(file=file, user_id=user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"파일 Storage 저장 실패: {str(e)}",
        )

    # DB에 템플릿 메타 등록
    template_data = TemplateCreate(
        user_id=user_id,
        name=template_name,
        template_type="observation_log",
        structure_json=structure_json,
        file_storage_path=storage_result.file_path,
        is_default=False,
    )

    try:
        template_in_db = await template_repo.create(template_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"템플릿 DB 등록 실패: {str(e)}",
        )

    return TemplateUploadResponse(
        storage_info=storage_result,
        template_id=template_in_db.id,
        template_name=template_in_db.name,
        structure_json=structure_json,
    )
