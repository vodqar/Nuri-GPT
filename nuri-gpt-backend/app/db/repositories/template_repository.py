"""Template Repository

템플릿 CRUD 리포지토리
"""

from typing import List, Optional
from uuid import UUID

from supabase import Client

from app.db.async_wrap import run_sync
from app.db.models.template import (
    TemplateCreate,
    TemplateFilter,
    TemplateResponse,
    TemplateUpdate,
)


class TemplateRepository:
    """템플릿 데이터 접근 객체"""

    def __init__(self, client: Client):
        self.client = client
        self.table = "templates"

    async def create(self, template_data: TemplateCreate) -> TemplateResponse:
        """새 템플릿 생성"""
        data = template_data.model_dump(mode="json", exclude_none=True)
        result = await run_sync(lambda: self.client.table(self.table).insert(data).execute())

        if not result.data:
            raise ValueError("템플릿 생성 실패")

        return TemplateResponse(**result.data[0])

    async def get_by_id(self, template_id: UUID) -> Optional[TemplateResponse]:
        """ID로 템플릿 조회"""
        result = await run_sync(lambda: self.client.table(self.table).select("*").eq("id", str(template_id)).execute())

        if not result.data:
            return None

        return TemplateResponse(**result.data[0])

    async def get_by_user(self, user_id: UUID) -> List[TemplateResponse]:
        """사용자의 템플릿 목록 조회"""
        result = await run_sync(lambda: self.client.table(self.table).select("*").eq("user_id", str(user_id)).execute())
        return [TemplateResponse(**template) for template in result.data]

    async def get_default_by_user(self, user_id: UUID) -> Optional[TemplateResponse]:
        """사용자의 기본 템플릿 조회"""
        result = await run_sync(lambda: (
            self.client.table(self.table)
            .select("*")
            .eq("user_id", str(user_id))
            .eq("is_default", True)
            .limit(1)
            .execute()
        ))

        if not result.data:
            return None

        return TemplateResponse(**result.data[0])

    async def update(
        self, template_id: UUID, template_update: TemplateUpdate
    ) -> Optional[TemplateResponse]:
        """템플릿 업데이트"""
        data = template_update.model_dump(exclude_unset=True, exclude_none=True)

        if not data:
            return await self.get_by_id(template_id)

        result = await run_sync(lambda: self.client.table(self.table).update(data).eq("id", str(template_id)).execute())

        if not result.data:
            return None

        return TemplateResponse(**result.data[0])

    async def delete(self, template_id: UUID) -> bool:
        """템플릿 삭제 (하드 삭제)"""
        result = await run_sync(lambda: self.client.table(self.table).delete().eq("id", str(template_id)).execute())
        return len(result.data) > 0

    async def soft_delete(self, template_id: UUID) -> bool:
        """템플릿 소프트 삭제 (is_active=False)"""
        result = await run_sync(lambda: (
            self.client.table(self.table)
            .update({"is_active": False})
            .eq("id", str(template_id))
            .execute()
        ))
        return len(result.data) > 0

    async def update_order(self, orders: List[dict]) -> int:
        """템플릿 순서 일괄 업데이트

        Args:
            orders: [{"id": UUID, "sort_order": int}, ...]

        Returns:
            업데이트된 레코드 수
        """
        updated_count = 0
        for item in orders:
            result = await run_sync(lambda i=item: (
                self.client.table(self.table)
                .update({"sort_order": i["sort_order"]})
                .eq("id", str(i["id"]))
                .execute()
            ))
            if result.data:
                updated_count += 1
        return updated_count

    async def set_default(self, user_id: UUID, template_id: UUID) -> bool:
        """기본 템플릿 설정"""
        # 기존 기본 템플릿 해제
        await run_sync(lambda: (
            self.client.table(self.table).update({"is_default": False}).eq(
                "user_id", str(user_id)
            ).execute()
        ))

        # 새 기본 템플릿 설정
        result = await run_sync(lambda: (
            self.client.table(self.table)
            .update({"is_default": True})
            .eq("id", str(template_id))
            .execute()
        ))
        return len(result.data) > 0

    async def update_last_used_at(self, template_id: UUID) -> bool:
        """템플릿의 마지막 사용 시간을 현재 시간으로 업데이트

        Args:
            template_id: 업데이트할 템플릿 ID

        Returns:
            업데이트 성공 여부
        """
        from datetime import datetime, timezone

        ts = datetime.now(timezone.utc).isoformat()
        result = await run_sync(lambda: (
            self.client.table(self.table)
            .update({"last_used_at": ts})
            .eq("id", str(template_id))
            .execute()
        ))
        return len(result.data) > 0

    async def get_by_filter(self, filter_params: TemplateFilter) -> List[TemplateResponse]:
        """필터 조건으로 템플릿 조회"""
        query = self.client.table(self.table).select("*")

        if filter_params.user_id:
            query = query.eq("user_id", str(filter_params.user_id))

        if filter_params.template_type:
            query = query.eq("template_type", filter_params.template_type)

        if filter_params.is_default is not None:
            query = query.eq("is_default", filter_params.is_default)

        # is_active 필터 (기본적으로 활성화된 템플릿만 조회)
        if filter_params.is_active is not None:
            query = query.eq("is_active", filter_params.is_active)

        # sort_order 기준 정렬
        query = query.order("sort_order", desc=False)

        result = await run_sync(lambda: query.execute())
        return [TemplateResponse(**template) for template in result.data]
