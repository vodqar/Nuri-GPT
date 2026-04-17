import { useState, useRef, useCallback, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getTemplates,
  deleteTemplate,
  updateTemplate,
  updateTemplateOrder,
} from '../../../services/api';
import { queryKeys } from '../../../services/queries';
import type { Template } from '../../../types/api';

interface UseTemplateManagementProps {
  setError: (error: string | null) => void;
}

export function useTemplateManagement({
  setError,
}: UseTemplateManagementProps) {
  const queryClient = useQueryClient();

  // React Query로 템플릿 목록 조회 (캐시, 재시도, 중복 제거 자동 처리)
  const {
    data: queryTemplates = [],
    isLoading: isQueryLoading,
    isError: isQueryError,
    refetch,
  } = useQuery({
    queryKey: queryKeys.templates,
    queryFn: getTemplates,
    staleTime: 60_000,
    retry: 3,
  });

  // 관리 모드 로컬 상태 (React Query 캐시와 독립적으로 순서 편집 추적)
  const [localTemplates, setLocalTemplates] = useState<Template[] | null>(null);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('');
  const [isManageMode, setIsManageMode] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const originalTemplatesRef = useRef<Template[] | null>(null);

  // 쿼리 데이터 → 템플릿 목록 동기화
  const templates = localTemplates ?? queryTemplates;

  // 쿼리 데이터가 변경되면 selectedTemplateId 보정
  useEffect(() => {
    if (queryTemplates.length > 0 && !localTemplates) {
      setSelectedTemplateId((prev) =>
        queryTemplates.some((t: Template) => t.id === prev) ? prev : queryTemplates[0].id
      );
    } else if (queryTemplates.length === 0 && !localTemplates) {
      setSelectedTemplateId('');
    }
  }, [queryTemplates, localTemplates]);

  // 쿼리 에러 → 외부 setError 콜백
  useEffect(() => {
    if (isQueryError) {
      setError('템플릿을 불러오는 데 실패했습니다. 네트워크 연결을 확인하고 다시 시도해주세요.');
    } else {
      setError(null);
    }
  }, [isQueryError, setError]);

  // Mutation: 삭제
  const deleteMutation = useMutation({
    mutationFn: deleteTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.templates });
    },
  });

  // Mutation: 수정
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: { name?: string } }) =>
      updateTemplate(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.templates });
    },
  });

  // Mutation: 순서 변경
  const orderMutation = useMutation({
    mutationFn: updateTemplateOrder,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.templates });
    },
  });

  const fetchTemplates = useCallback(async () => {
    await refetch();
  }, [refetch]);

  const retryFetch = useCallback(() => {
    refetch();
  }, [refetch]);

  const handleDeleteTemplate = useCallback(
    async (templateId: string) => {
      try {
        await deleteMutation.mutateAsync(templateId);
        // 관리 모드 중이면 localTemplates에서도 제거
        if (localTemplates) {
          const filtered = localTemplates.filter((t) => t.id !== templateId);
          setLocalTemplates(filtered);
          if (selectedTemplateId === templateId && filtered.length > 0) {
            setSelectedTemplateId(filtered[0].id);
          }
        }
        setHasChanges(true);
      } catch {
        window.dispatchEvent(new CustomEvent('toast', { detail: { message: '템플릿 삭제 중 오류가 발생했습니다.', type: 'error' } }));
      }
    },
    [deleteMutation, localTemplates, selectedTemplateId]
  );

  const handleUpdateTemplate = useCallback(
    async (templateId: string, data: { name?: string }) => {
      try {
        await updateMutation.mutateAsync({ id: templateId, data });
        if (localTemplates) {
          const updated = localTemplates.map((t) =>
            t.id === templateId ? { ...t, name: data.name ?? t.name } : t
          );
          setLocalTemplates(updated);
        }
        setHasChanges(true);
      } catch {
        window.dispatchEvent(new CustomEvent('toast', { detail: { message: '템플릿 수정 중 오류가 발생했습니다.', type: 'error' } }));
      }
    },
    [updateMutation, localTemplates]
  );

  const handleUpdateOrder = useCallback(
    async (orders: { id: string; sort_order: number }[]) => {
      try {
        await orderMutation.mutateAsync(orders);
      } catch {
        window.dispatchEvent(new CustomEvent('toast', { detail: { message: '순서 저장 중 오류가 발생했습니다.', type: 'error' } }));
      }
    },
    [orderMutation]
  );

  const toggleManageMode = useCallback(() => {
    if (isManageMode) {
      // 관리 모드 종료 시 순서 저장 (비동기)
      const orders = templates.map((t: Template) => ({
        id: t.id,
        sort_order: t.sort_order,
      }));
      handleUpdateOrder(orders).catch(() => window.dispatchEvent(new CustomEvent('toast', { detail: { message: '순서 저장 중 오류가 발생했습니다.', type: 'error' } })));
      setLocalTemplates(null);
    } else {
      // 관리 모드 진입 시 쿼리 데이터를 로컬로 복사
      setLocalTemplates([...queryTemplates]);
    }
    setIsManageMode((prev) => !prev);
  }, [isManageMode, templates, queryTemplates, handleUpdateOrder]);

  const exitManageModeWithoutSaving = useCallback(() => {
    setLocalTemplates(null);
    setIsManageMode(false);
    setHasChanges(false);
    originalTemplatesRef.current = null;
  }, []);

  // 관리 모드 진입/실패 시 상태 동기화
  useEffect(() => {
    if (isManageMode) {
      if (!originalTemplatesRef.current) {
        originalTemplatesRef.current = [...templates];
        setHasChanges(false);
      }
    } else {
      setHasChanges(false);
      originalTemplatesRef.current = null;
    }
  }, [isManageMode, templates]);

  // 관리 모드에서 변경사항 있을 때 페이지 이탈 방지
  useEffect(() => {
    if (!isManageMode || !hasChanges) return;

    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = '';
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [isManageMode, hasChanges]);

  const handleReorder = useCallback(
    (oldIndex: number, newIndex: number) => {
      if (!localTemplates) return;
      const newTemplates = [...localTemplates];
      const [moved] = newTemplates.splice(oldIndex, 1);
      newTemplates.splice(newIndex, 0, moved);

      const reordered = newTemplates.map((t, idx) => ({
        ...t,
        sort_order: idx,
      }));

      setLocalTemplates(reordered);
      setHasChanges(true);
    },
    [localTemplates]
  );

  return {
    templates,
    setTemplates: setLocalTemplates,
    selectedTemplateId,
    setSelectedTemplateId,
    isLoading: isQueryLoading,
    isFailed: isQueryError,
    isManageMode,
    hasChanges,
    fetchTemplates,
    retryFetch,
    handleDeleteTemplate,
    handleUpdateTemplate,
    handleUpdateOrder,
    toggleManageMode,
    exitManageModeWithoutSaving,
    handleReorder,
  };
}
