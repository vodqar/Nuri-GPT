"""Generate Schemas

관찰일지/일일보육일지 생성 관련 API 스키마
"""

from typing import List, Optional, Dict
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.upload import SemanticTemplateData


class UpdatedActivity(BaseModel):
    """LLM 처리 후 반환되는 활동 텍스트 스키마"""

    target_id: str = Field(..., description="수정 대상 텍스트 노드 타겟 ID")
    updated_text: str = Field(..., description="LLM이 생성/수정한 텍스트")


class ActivityComment(BaseModel):
    """재생성 요청 시 사용자가 남긴 코멘트 스키마"""

    target_id: str = Field(..., description="수정 요청 대상 활동의 target_id")
    comment: str = Field(..., description="사용자의 수정 요청 코멘트")


class GenerateLogRequest(BaseModel):
    """일지 생성 요청 스키마"""
    semantic_json: Optional[SemanticTemplateData] = Field(
        default=None,
        description="Vision API를 통해 추출된 템플릿의 의미론적 구조 데이터",
    )
    template_id: Optional[UUID] = Field(
        default=None,
        description="적용할 템플릿 ID (레거시 호환용)",
    )
    ocr_text: str = Field(
        default="",
        description="OCR로 추출된 메모 내용이나 직접 입력한 텍스트 (레거시 호환용)",
    )
    additional_guidelines: Optional[str] = Field(
        default="",
        description="유치원/어린이집 평가제 가이드라인 등 추가 지시사항"
    )
    child_age: int = Field(
        ...,
        ge=0, le=5,
        description="대상 아동 연령 (만0세~만5세, 필수)"
    )
    is_aggressive: str = Field(
        default="false",
        description="스마트 채우기 활성화 여부 ('true' 또는 'false')"
    )


class RegenerateLogRequest(BaseModel):
    """코멘트 기반 일지 재생성 요청 스키마"""
    original_semantic_json: Optional[Dict] = Field(
        default=None,
        description="교사의 최초 입력값 (컨텍스트 유지용). 템플릿 structure_json 또는 semantic_json 형식",
    )
    current_activities: List[UpdatedActivity] = Field(
        ...,
        description="현재 화면에 렌더링된 버전의 생성 결과",
    )
    comments: List[ActivityComment] = Field(
        ...,
        description="사용자가 남긴 수정 코멘트 목록",
    )
    additional_guidelines: Optional[str] = Field(
        default="",
        description="추가 가이드라인",
    )
    child_age: Optional[int] = Field(
        default=None,
        description="대상 아동 연령 (만0세~만5세)"
    )
    is_aggressive: str = Field(
        default="false",
        description="스마트 채우기 활성화 여부 ('true' 또는 'false')"
    )


class GenerateLogResponse(BaseModel):
    """일지 생성 결과 스키마"""
    title: Optional[str] = Field(default=None, description="관찰일지의 간결한 제목 (기본 생성 시)")
    observation_content: Optional[str] = Field(default=None, description="객관적인 사실 위주의 관찰 내용 상세 서술 (기본 생성 시)")
    evaluation_content: Optional[str] = Field(default=None, description="관찰 내용에 기반한 교사의 해석, 평가 및 향후 지원 계획 (기본 생성 시)")
    development_areas: Optional[List[str]] = Field(default_factory=list, description="해당하는 누리과정 발달 영역 구문 (기본 생성 시)")
    
    template_mapping: Optional[Dict[str, str]] = Field(
        default=None,
        description="템플릿의 셀 ID별 생성된 텍스트 매핑 (템플릿 기반 생성 시)"
    )
    updated_activities: List[UpdatedActivity] = Field(
        default_factory=list,
        description="타겟 ID 기준으로 수정된 텍스트 목록 (신규 파이프라인)",
    )
    
    log_id: UUID = Field(description="해당 생성 액션의 로깅 ID")
    journal_id: Optional[UUID] = Field(default=None, description="저장된 관찰일지 ID")


class RegenerateLogResponse(BaseModel):
    """코멘트 기반 일지 재생성 결과 스키마"""
    updated_activities: List[UpdatedActivity] = Field(
        ...,
        description="재생성된 활동 텍스트 목록",
    )
    log_id: UUID = Field(description="해당 재생성 액션의 로깅 ID")
