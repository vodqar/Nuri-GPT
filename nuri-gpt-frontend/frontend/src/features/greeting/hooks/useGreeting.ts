import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '../../../store/authStore';
import { GreetingService, type StreamEvent } from '../services/greetingService';
import { extractApiErrorMessage } from '../../../utils/apiError';
import type { GreetingRequest } from '../types';

export type StreamStage = 'idle' | 'weather' | 'context' | 'generating';

export function useGreeting() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const [isGenerating, setIsGenerating] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [stage, setStage] = useState<StreamStage>('idle');
  const generateGreeting = async (data: GreetingRequest) => {
    setIsGenerating(true);
    setError(null);
    setResult(null);
    setStage('weather');

    let completed = false;

    try {
      await GreetingService.generateGreetingStream(
        {
          ...data,
          user_input: data.user_input || '',
          enabled_contexts: data.enabled_contexts || [],
        },
        (event: StreamEvent) => {
          switch (event.event) {
            case 'progress':
              setStage(event.stage as StreamStage);
              break;
            case 'token':
              setStage('generating');
              setResult((prev) => (prev ?? '') + event.text);
              break;
            case 'done':
              completed = true;
              setResult(event.greeting);
              break;
            case 'error':
              completed = true;
              setError(event.message || '인삿말 생성에 실패했습니다.');
              break;
          }
        },
      );
      // 스트림이 done/error 없이 종료된 경우 → 연결 끊김으로 판단
      if (!completed) {
        setError('서버 연결이 끊겼습니다. 다시 시도해주세요.');
        setResult(null);
      }
    } catch (err) {
      setError(extractApiErrorMessage(err, '인삿말 생성에 실패했습니다.'));
    } finally {
      setIsGenerating(false);
      setStage('idle');
      // 생성 성공/실패와 관계없이 사용량 데이터를 즉시 갱신 요청
      queryClient.invalidateQueries({ queryKey: ['usage'] });
    }
  };

  return {
    isGenerating,
    result,
    error,
    stage,
    generateGreeting,
    preferredRegion: (user?.preferences?.['greeting.preferred_region'] as string) || null,
  };
}
