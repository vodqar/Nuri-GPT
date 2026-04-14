"""Upload API Schemas

메모/템플릿 업로드 API 요청/응답 스키마
"""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.storage import StorageUploadResponse


class MemoUploadResponse(BaseModel):
    """수기 메모 이미지 업로드 응답 스키마"""

    storage_info: StorageUploadResponse = Field(..., description="Storage 저장 결과")
    extracted_text: str = Field(..., description="OCR로 추출된 원본 텍스트")
    normalized_text: str = Field(..., description="정규화된 텍스트")


class TextMemoRequest(BaseModel):
    """텍스트 직접 입력 요청 스키마"""

    text: str = Field(..., min_length=1, description="교사가 직접 입력한 메모 텍스트")
    child_name: Optional[str] = Field(None, max_length=50, description="아동 이름 (선택)")


class TextMemoResponse(BaseModel):
    """텍스트 메모 정규화 응답 스키마"""

    original_text: str = Field(..., description="입력된 원본 텍스트")
    normalized_text: str = Field(..., description="정규화된 텍스트")
    child_name: Optional[str] = Field(None, description="아동 이름 (선택)")


class TemplateUploadResponse(BaseModel):
    """템플릿 이미지 업로드 응답 스키마"""

    storage_info: StorageUploadResponse = Field(..., description="Storage 저장 결과")
    template_id: UUID = Field(..., description="DB에 등록된 템플릿 ID")
    template_name: str = Field(..., description="템플릿 이름")
    structure_json: dict = Field(..., description="Vision LLM에서 추출한 계층 구조 JSON 데이터")

class TemplateAnalyzeResponse(BaseModel):
    """템플릿 이미지 분석 응답 스키마 (저장 없이 structure_json만 반환)"""

    structure_json: dict = Field(..., description="Vision LLM에서 추출한 계층 구조 JSON 데이터")


class SemanticActivity(BaseModel):
    """Semantic JSON 내 활동 스키마"""
    target_id: Optional[str] = Field(None, description="수정 대상 텍스트 노드 타겟 ID")
    current_text: str = Field(..., description="현재 텍스트 내용")


class SemanticTemplateData(BaseModel):
    """Semantic JSON 데이터 스키마"""
    document_type: str = Field(..., description="문서 종류")
    date: str = Field(..., description="문서 날짜")
    activities: List[SemanticActivity] = Field(default_factory=list, description="활동 목록")
