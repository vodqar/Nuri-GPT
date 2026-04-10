import { useState, useRef, useCallback, useEffect } from 'react';
import {
  getTemplates,
  deleteTemplate,
  updateTemplate,
  updateTemplateOrder,
} from '../../../services/api';
import type { Template } from '../../../types/api';

interface UseTemplateManagementProps {
  userId?: string;
  setError: (error: string | null) => void;
}

const MAX_RETRIES = 3;
const RETRY_DELAYS = [1000, 2000, 4000]; // exponential backoff

export function useTemplateManagement({
  userId,
  setError,
}: UseTemplateManagementProps) {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [isManageMode, setIsManageMode] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [isFailed, setIsFailed] = useState(false);
  const retryCountRef = useRef(0);
  const originalTemplatesRef = useRef<Template[] | null>(null);
  const isFetchingRef = useRef(false);
  const hasInitializedRef = useRef(false);

  const fetchTemplates = useCallback(async (isRetry = false) => {
    // 중복 호출 방지
    if (isFetchingRef.current) return;
    isFetchingRef.current = true;

    try {
      setIsLoading(true);
      setIsFailed(false);
      if (!isRetry) {
        retryCountRef.current = 0;
      }
      setError(null);
      const response = await getTemplates(userId);
      if (response && response.length > 0) {
        setTemplates(response);
        setSelectedTemplateId(response[0].id);
      } else {
        setTemplates([]);
        setSelectedTemplateId('');
      }
      // 성공 시 초기화 완료 표시
      hasInitializedRef.current = true;
    } catch (err) {
      console.error('Failed to fetch template:', err);
      
      // 재시도 로직
      const currentRetry = isRetry ? retryCountRef.current : 0;
      if (currentRetry < MAX_RETRIES - 1) {
        const nextRetry = currentRetry + 1;
        retryCountRef.current = nextRetry;
        setError(`템플릿을 불러오는 중 오류가 발생했습니다. 재시도 중... (${nextRetry}/${MAX_RETRIES})`);
        
        // exponential backoff
        await new Promise(resolve => setTimeout(resolve, RETRY_DELAYS[currentRetry]));
        isFetchingRef.current = false;
        return fetchTemplates(true);
      }
      
      // 최종 실패
      setError('템플릿을 불러오는 데 실패했습니다. 네트워크 연결을 확인하고 다시 시도해주세요.');
      setIsFailed(true);
    } finally {
      setIsLoading(false);
      isFetchingRef.current = false;
    }
  }, [userId, setError]);

  // 수동 재시도
  const retryFetch = useCallback(() => {
    retryCountRef.current = 0;
    setIsFailed(false);
    fetchTemplates(false);
  }, [fetchTemplates]);

  const handleDeleteTemplate = useCallback(
    async (templateId: string) => {
      try {
        await deleteTemplate(templateId);
        const filtered = templates.filter((t) => t.id !== templateId);
        setTemplates(filtered);
        if (selectedTemplateId === templateId && filtered.length > 0) {
          setSelectedTemplateId(filtered[0].id);
        }
        setHasChanges(true);
      } catch {
        window.dispatchEvent(new CustomEvent('toast', { detail: { message: '템플릿 삭제 중 오류가 발생했습니다.', type: 'error' } }));
      }
    },
    [templates, selectedTemplateId]
  );

  const handleUpdateTemplate = useCallback(
    async (templateId: string, data: { name?: string }) => {
      try {
        await updateTemplate(templateId, data);
        const updated = templates.map((t) =>
          t.id === templateId ? { ...t, name: data.name ?? t.name } : t
        );
        setTemplates(updated);
        setHasChanges(true);
      } catch {
        window.dispatchEvent(new CustomEvent('toast', { detail: { message: '템플릿 수정 중 오류가 발생했습니다.', type: 'error' } }));
      }
    },
    [templates]
  );

  const handleUpdateOrder = useCallback(
    async (orders: { id: string; sort_order: number }[]) => {
      try {
        await updateTemplateOrder(orders);
      } catch {
        window.dispatchEvent(new CustomEvent('toast', { detail: { message: '순서 저장 중 오류가 발생했습니다.', type: 'error' } }));
      }
    },
    []
  );

  const toggleManageMode = useCallback(() => {
    if (isManageMode) {
      // 관리 모드 종료 시 순서 저장 (비동기)
      const orders = templates.map((t) => ({
        id: t.id,
        sort_order: t.sort_order,
      }));
      handleUpdateOrder(orders).catch(() => window.dispatchEvent(new CustomEvent('toast', { detail: { message: '순서 저장 중 오류가 발생했습니다.', type: 'error' } })));
    }
    setIsManageMode((prev) => !prev);
  }, [isManageMode, templates, handleUpdateOrder]);

  const exitManageModeWithoutSaving = useCallback(() => {
    if (originalTemplatesRef.current) {
      setTemplates(originalTemplatesRef.current);
    }
    setIsManageMode(false);
    setHasChanges(false);
    originalTemplatesRef.current = null;
  }, []);

  // 관리 모드 진입/실패 시 상태 동기화
  useEffect(() => {
    if (isManageMode) {
      // 관리 모드 진입 시 원본 상태 백업 (최초 1회만)
      if (!originalTemplatesRef.current) {
        originalTemplatesRef.current = [...templates];
        setHasChanges(false);
      }
    } else {
      // 관리 모드 종료 시 내부 상태 초기화
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
      const newTemplates = [...templates];
      const [moved] = newTemplates.splice(oldIndex, 1);
      newTemplates.splice(newIndex, 0, moved);

      // sort_order 재할당
      const reordered = newTemplates.map((t, idx) => ({
        ...t,
        sort_order: idx,
      }));

      setTemplates(reordered);
      setHasChanges(true);
    },
    [templates]
  );

  return {
    templates,
    setTemplates,
    selectedTemplateId,
    setSelectedTemplateId,
    isLoading,
    isFailed,
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
