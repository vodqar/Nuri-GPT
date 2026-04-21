"""Generate API Endpoints

관찰일지/일일보육일지 생성 엔드포인트
"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.dependencies import (
    get_current_user,
    get_journal_repository,
    get_llm_service,
    get_log_repository,
    get_template_repository,
    get_usage_service,
)
from app.db.models.journal import JournalCreate
from app.db.repositories.journal_repository import JournalRepository
from app.db.repositories.log_repository import LogRepository
from app.db.repositories.template_repository import TemplateRepository
from app.schemas.generate import (
    GenerateLogRequest,
    GenerateLogResponse,
    RegenerateLogRequest,
    RegenerateLogResponse,
    UpdatedActivity,
)
from app.services.llm import LlmService
from app.services.usage_service import UsageService
from app.core.rate_limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/log", response_model=GenerateLogResponse, status_code=status.HTTP_200_OK)
@limiter.limit("20/minute")
async def generate_observation_log(
    request: Request,
    log_request: GenerateLogRequest,
    current_user: dict = Depends(get_current_user),
    llm_service: LlmService = Depends(get_llm_service),
    log_repository: LogRepository = Depends(get_log_repository),
    template_repository: TemplateRepository = Depends(get_template_repository),
    journal_repository: JournalRepository = Depends(get_journal_repository),
    usage_service: UsageService = Depends(get_usage_service),
) -> GenerateLogResponse:
    """
    텍스트 데이터와 가이드라인을 바탕으로 관찰일지 초안을 생성합니다.
    template_id가 주어지면 해당 템플릿의 청사진에 맞춰 일지를 생성합니다.
    """
    from uuid import UUID
    user_id = UUID(current_user["id"])

    # 할당량 확인
    is_available = await usage_service.check_quota_available(user_id, "text_generate")
    if not is_available:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="일일 생성 할당량을 모두 소진했습니다. 내일 다시 시도해주세요."
        )

    try:
        if not log_request.semantic_json and not log_request.template_id and not log_request.ocr_text.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="semantic_json, template_id, ocr_text 중 최소 하나는 제공되어야 합니다.",
            )

        if log_request.semantic_json:
            activities = log_request.semantic_json.activities
            updated_activities = llm_service.generate_updated_activities(
                semantic_json=log_request.semantic_json.model_dump(),
                additional_guidelines=log_request.additional_guidelines or "",
                supplemental_text=log_request.ocr_text,
                child_age=log_request.child_age,
            )

            if not updated_activities:
                updated_activities = [
                    {
                        "target_id": activity.target_id,
                        "updated_text": activity.current_text,
                    }
                    for activity in activities
                    if activity.target_id
                ]

            from uuid import UUID
            user_id = UUID(current_user["id"])

            metadata = {
                "source": "generate_log_api_semantic",
                "activity_count": len(updated_activities),
                "has_guidelines": bool(log_request.additional_guidelines),
                "llm_result": {
                    "updated_activities": updated_activities,
                },
            }

            log_entry = await log_repository.log_action(
                user_id=user_id,
                action="generate_journal_from_semantic",
                metadata=metadata,
            )

            # 자동 저장: observation_journals 테이블에 일지 저장
            journal_data = JournalCreate(
                user_id=user_id,
                source_type="generate_log_api_semantic",
                semantic_json=log_request.semantic_json.model_dump() if log_request.semantic_json else {},
                updated_activities=updated_activities,
                additional_guidelines=log_request.additional_guidelines,
            )
            journal_entry = await journal_repository.create(journal_data)

            response = GenerateLogResponse(
                updated_activities=updated_activities,
                log_id=log_entry.id,
                journal_id=journal_entry.id,
                group_id=journal_entry.group_id,
            )
            await usage_service.increment_usage(user_id, "text_generate", status="success")
            return response

        if log_request.template_id:
            # 1. 템플릿 기반 생성
            template = await template_repository.get_by_id(log_request.template_id)
            if not template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"요청한 템플릿(ID: {log_request.template_id})을 찾을 수 없습니다."
                )
            
            # structure_json의 모든 말단(leaf) 노드 경로를 추출하여 태그로 사용
            def get_leaf_paths(data, current_path=""):
                paths = []
                if isinstance(data, dict):
                    for k, v in data.items():
                        new_path = f"{current_path}.{k}" if current_path else k
                        if isinstance(v, dict):
                            paths.extend(get_leaf_paths(v, new_path))
                        else:
                            paths.append(new_path)
                return paths

            tags = get_leaf_paths(template.structure_json)
            
            if not tags:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="템플릿 구조에서 항목(태그) 정보가 추출되지 않아 일지를 생성할 수 없습니다."
                )
                
            llm_result = llm_service.generate_journal_content(
                ocr_text=log_request.ocr_text,
                tags=tags,
                additional_guidelines=log_request.additional_guidelines,
                is_aggressive=log_request.is_aggressive,
                child_age=log_request.child_age
            )
            
            # DB에 생성 이력 로그 기록
            from uuid import UUID
            user_id = UUID(current_user["id"])
            metadata = {
                "source": "generate_log_api_with_template",
                "template_id": str(log_request.template_id),
                "ocr_text_length": len(log_request.ocr_text),
                "has_guidelines": bool(log_request.additional_guidelines),
                "llm_result": {"template_mapping": llm_result},
            }
            
            log_entry = await log_repository.log_action(
                user_id=user_id,
                action="generate_journal_from_template",
                metadata=metadata
            )
            
            # 키 순서 보장을 위해 template_mapping을 updated_activities 배열로 변환
            updated_activities = [
                {"target_id": key, "updated_text": value}
                for key, value in llm_result.items()
            ]

            # 자동 저장: observation_journals 테이블에 일지 저장
            journal_data = JournalCreate(
                user_id=user_id,
                template_id=log_request.template_id,
                source_type="generate_log_api_with_template",
                template_mapping=llm_result,
                updated_activities=updated_activities,
                ocr_text=log_request.ocr_text,
                additional_guidelines=log_request.additional_guidelines,
            )
            journal_entry = await journal_repository.create(journal_data)
            
            # 템플릿 사용 시간 업데이트
            await template_repository.update_last_used_at(log_request.template_id)

            response = GenerateLogResponse(
                template_mapping=llm_result,
                updated_activities=updated_activities,
                log_id=log_entry.id,
                journal_id=journal_entry.id,
                group_id=journal_entry.group_id,
            )
            await usage_service.increment_usage(user_id, "text_generate", status="success")
            return response
            
        else:
            # 2. 기본 관찰일지 생성
            llm_result = llm_service.generate_observation_log(
                ocr_text=log_request.ocr_text,
                additional_guidelines=log_request.additional_guidelines,
                is_aggressive=log_request.is_aggressive,
                child_age=log_request.child_age
            )

            if not llm_result.get("title") and not llm_result.get("observation_content"):
                logger.warning("LLM generated an empty response")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="관찰일지 생성 중 오류가 발생했습니다. (빈 응답)"
                )

            # DB에 생성 이력 로그 기록
            from uuid import UUID
            user_id = UUID(current_user["id"])
            metadata = {
                "source": "generate_log_api_default",
                "ocr_text_length": len(log_request.ocr_text),
                "has_guidelines": bool(log_request.additional_guidelines),
                "llm_result": llm_result,
            }

            log_entry = await log_repository.log_action(
                user_id=user_id,
                action="generate_log",
                metadata=metadata
            )

            # 자동 저장: observation_journals 테이블에 일지 저장
            journal_data = JournalCreate(
                user_id=user_id,
                title=llm_result.get("title", ""),
                observation_content=llm_result.get("observation_content", ""),
                evaluation_content=llm_result.get("evaluation_content", ""),
                development_areas=llm_result.get("development_areas", []),
                source_type="generate_log_api_default",
                ocr_text=log_request.ocr_text,
                additional_guidelines=log_request.additional_guidelines,
            )
            journal_entry = await journal_repository.create(journal_data)

            response = GenerateLogResponse(
                title=llm_result.get("title", ""),
                observation_content=llm_result.get("observation_content", ""),
                evaluation_content=llm_result.get("evaluation_content", ""),
                development_areas=llm_result.get("development_areas", []),
                log_id=log_entry.id,
                journal_id=journal_entry.id,
                group_id=journal_entry.group_id,
            )
            await usage_service.increment_usage(user_id, "text_generate", status="success")
            return response

    except RuntimeError as e:
        # 실패 시 실패 카운트 증가
        await usage_service.increment_usage(user_id, "text_generate", status="fail")
        logger.error(f"RuntimeError during LLM generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="일지 생성 서비스 오류가 발생했습니다."
        )
    except HTTPException as e:
        # 429 에러(할당량 부족)가 아닌 다른 HTTP 예외인 경우만 실패로 기록 (선택 사항)
        if e.status_code != status.HTTP_429_TOO_MANY_REQUESTS:
            await usage_service.increment_usage(user_id, "text_generate", status="fail")
        raise e
    except Exception as e:
        # 실패 시 실패 카운트 증가
        await usage_service.increment_usage(user_id, "text_generate", status="fail")
        logger.error(f"Unexpected error during log generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="일지 생성 중 예상치 못한 런타임 오류가 발생했습니다."
        )


@router.post("/regenerate", response_model=RegenerateLogResponse, status_code=status.HTTP_200_OK)
@limiter.limit("20/minute")
async def regenerate_observation_log(
    request: Request,
    regen_request: RegenerateLogRequest,
    current_user: dict = Depends(get_current_user),
    llm_service: LlmService = Depends(get_llm_service),
    log_repository: LogRepository = Depends(get_log_repository),
    journal_repository: JournalRepository = Depends(get_journal_repository),
    usage_service: UsageService = Depends(get_usage_service),
) -> RegenerateLogResponse:
    """
    코멘트 기반으로 기존 생성된 관찰일지를 부분 재생성합니다.
    """
    from uuid import UUID
    user_id = UUID(current_user["id"])

    # 할당량 확인
    is_available = await usage_service.check_quota_available(user_id, "text_generate")
    if not is_available:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="일일 재생성 할당량을 모두 소진했습니다. 내일 다시 시도해주세요."
        )

    try:
        # 입력 검증
        if not regen_request.current_activities:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="current_activities는 최소 하나 이상 제공되어야 합니다.",
            )

        # Dify Chatflow 호출
        regenerated_activities = llm_service.generate_regenerated_activities(
            original_semantic_json=regen_request.original_semantic_json or {},
            current_activities=[{"target_id": act.target_id, "updated_text": act.updated_text} for act in regen_request.current_activities],
            comments=[{"target_id": c.target_id, "comment": c.comment} for c in regen_request.comments],
            additional_guidelines=regen_request.additional_guidelines or "",
            is_aggressive=regen_request.is_aggressive,
            child_age=regen_request.child_age,
        )

        # 결과 검증 - 모든 target_id가 포함되었는지 확인
        current_target_ids = {act.target_id for act in regen_request.current_activities}
        result_target_ids = {act["target_id"] for act in regenerated_activities}

        missing_target_ids = current_target_ids - result_target_ids
        if missing_target_ids:
            logger.warning(f"[Regenerate] Missing target_ids in response: {missing_target_ids}")
            # 누락된 항목은 현재 값으로 보존
            for act in regen_request.current_activities:
                if act.target_id in missing_target_ids:
                    regenerated_activities.append({
                        "target_id": act.target_id,
                        "updated_text": act.updated_text,
                    })

        # 응답 스키마 변환
        updated_activities = [
            UpdatedActivity(target_id=act["target_id"], updated_text=act["updated_text"])
            for act in regenerated_activities
        ]

        # DB 로깅
        from uuid import UUID
        user_id = UUID(current_user["id"])
        import hashlib
        semantic_json_str = json.dumps(regen_request.original_semantic_json or {}, sort_keys=True)
        semantic_hash = hashlib.sha256(semantic_json_str.encode()).hexdigest()[:16]

        metadata = {
            "source": "regenerate_api",
            "original_semantic_json_hash": semantic_hash,
            "comment_count": len(regen_request.comments),
            "comments": [{"target_id": c.target_id, "comment": c.comment} for c in regen_request.comments],
            "llm_result": {"updated_activities": [act.model_dump() for act in updated_activities]},
        }

        log_entry = await log_repository.log_action(
            user_id=user_id,
            action="regenerate_journal_from_semantic",
            metadata=metadata,
        )

        # group_id가 제공되면 observation_journals에 새 버전 저장
        new_journal_id = None
        if regen_request.group_id:
            # 기존 버전의 is_final을 False로 설정
            await journal_repository.mark_as_not_final(regen_request.group_id)
            
            # 최대 버전 조회
            max_version = await journal_repository.get_max_version(regen_request.group_id)
            new_version = max_version + 1
            
            # 새 버전 레코드 생성 (기존 journal 데이터 재사용)
            # 원본 journal 조회
            original_journals = await journal_repository.get_by_group_id(regen_request.group_id)
            if original_journals:
                original = original_journals[0]  # 최신 버전 사용
                journal_data = JournalCreate(
                    user_id=user_id,
                    group_id=regen_request.group_id,
                    version=new_version,
                    is_final=True,
                    source_type=original.source_type,
                    semantic_json=original.semantic_json or {},
                    updated_activities=[{"target_id": act.target_id, "updated_text": act.updated_text} for act in updated_activities],
                    additional_guidelines=original.additional_guidelines,
                    template_id=original.template_id,
                    template_mapping=original.template_mapping,
                    observation_content=original.observation_content,
                    evaluation_content=original.evaluation_content,
                    development_areas=original.development_areas,
                )
                new_journal = await journal_repository.create(journal_data)
                new_journal_id = new_journal.id

        response = RegenerateLogResponse(
            updated_activities=updated_activities,
            log_id=log_entry.id,
            journal_id=new_journal_id,
            group_id=regen_request.group_id,
        )
        await usage_service.increment_usage(user_id, "text_generate", status="success")
        return response

    except RuntimeError as e:
        await usage_service.increment_usage(user_id, "text_generate", status="fail")
        logger.error(f"[Regenerate] RuntimeError: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="일지 재생성 서비스 오류가 발생했습니다."
        )
    except HTTPException as e:
        if e.status_code != status.HTTP_429_TOO_MANY_REQUESTS:
            await usage_service.increment_usage(user_id, "text_generate", status="fail")
        raise e
    except Exception as e:
        await usage_service.increment_usage(user_id, "text_generate", status="fail")
        logger.error(f"[Regenerate] Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="일지 재생성 중 예상치 못한 오류가 발생했습니다."
        )
