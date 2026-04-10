import { useState, useCallback } from 'react';
import { generateLog, regenerateLog } from '../../../services/api';
import { showToast } from '../../../components/global/ToastContainer';
import type {
  GenerateLogResponse,
  ActivityComment,
  Template,
} from '../../../types/api';

interface UseLogGenerationProps {
  selectedTemplate: Template | undefined;
  childAge: number | null;
  isAggressiveMode: boolean;
  setIsGenerating: (value: boolean) => void;
  setError: (error: string | null) => void;
}

export function useLogGeneration({
  selectedTemplate,
  childAge,
  isAggressiveMode,
  setIsGenerating,
  setError,
}: UseLogGenerationProps) {
  const [generationHistory, setGenerationHistory] = useState<GenerateLogResponse[]>([]);
  const [currentHistoryIndex, setCurrentHistoryIndex] = useState(0);
  const [currentGroupId, setCurrentGroupId] = useState<string | null>(null);

  const generate = useCallback(
    async (payload: {
      template_id: string;
      ocr_text: string;
      child_age: number;
      is_aggressive: string;
    }): Promise<GenerateLogResponse | null> => {
      try {
        setIsGenerating(true);
        setError(null);

        const startTime = Date.now();
        const response = await generateLog(payload);

        // 최소 로딩 시간 보장 (UX) - 800ms
        const elapsedTime = Date.now() - startTime;
        if (elapsedTime < 800) {
          await new Promise((resolve) => setTimeout(resolve, 800 - elapsedTime));
        }

        setGenerationHistory([response]);
        setCurrentHistoryIndex(0);
        setCurrentGroupId(response.group_id || null);

        // 스크롤도 맨 위로
        window.scrollTo({ top: 0, behavior: 'smooth' });

        return response;
      } catch (err) {
        console.error('Generation failed:', err);
        setError('관찰일지 생성에 실패했습니다.');
        return null;
      } finally {
        setIsGenerating(false);
      }
    },
    [setIsGenerating, setError]
  );

  const regenerate = useCallback(
    async (
      comments: Record<string, string>,
      currentResult: GenerateLogResponse,
      setIsRegenerating: (value: boolean) => void
    ): Promise<void> => {
      try {
        setIsRegenerating(true);
        setError(null);

        // current_activities 구성: updated_activities 우선, 없으면 template_mapping 변환
        let currentActivities = currentResult.updated_activities || [];

        if (currentActivities.length === 0 && currentResult.template_mapping) {
          currentActivities = Object.entries(currentResult.template_mapping).map(
            ([key, value]) => ({
              target_id: key,
              updated_text: value as string,
            })
          );
        }

        if (currentActivities.length === 0) {
          setError('재생성할 활동 데이터가 없습니다.');
          setIsRegenerating(false);
          return;
        }

        const payload = {
          original_semantic_json:
            selectedTemplate?.semantic_json || selectedTemplate?.structure_json || {},
          current_activities: currentActivities,
          comments: Object.entries(comments).map(
            ([target_id, comment]): ActivityComment => ({
              target_id,
              comment,
            })
          ),
          additional_guidelines: '',
          child_age: childAge ?? undefined,
          is_aggressive: isAggressiveMode ? 'true' : 'false',
          group_id: currentGroupId || undefined,
        };

        const startTime = Date.now();
        const newResult = await regenerateLog(payload);

        const updatedHistory = [
          ...generationHistory,
          {
            ...currentResult,
            updated_activities: newResult.updated_activities,
            log_id: newResult.log_id,
            journal_id: newResult.journal_id,
            group_id: newResult.group_id,
          },
        ];

        // 최소 로딩 시간 보장 (UX) - 800ms
        const elapsedTime = Date.now() - startTime;
        if (elapsedTime < 800) {
          await new Promise((resolve) => setTimeout(resolve, 800 - elapsedTime));
        }

        setGenerationHistory(updatedHistory);
        setCurrentHistoryIndex(updatedHistory.length - 1);

        // 성공 알림
        showToast('일지가 재생성되었습니다', 'success');

        // 스크롤도 맨 위로
        window.scrollTo({ top: 0, behavior: 'smooth' });
      } catch (err) {
        console.error('Regeneration failed:', err);
        setError('재생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.');
      } finally {
        setIsRegenerating(false);
      }
    },
    [
      childAge,
      isAggressiveMode,
      selectedTemplate,
      generationHistory,
      setError,
      currentGroupId,
    ]
  );

  const navigateHistory = useCallback((index: number) => {
    setCurrentHistoryIndex(index);
  }, []);

  const clearHistory = useCallback(() => {
    setGenerationHistory([]);
    setCurrentHistoryIndex(0);
    setCurrentGroupId(null);
  }, []);

  return {
    generationHistory,
    currentHistoryIndex,
    generate,
    regenerate,
    navigateHistory,
    clearHistory,
  };
  };
