import { useState } from 'react';
import { useAuthStore } from '../../../store/authStore';
import { GreetingService } from '../services/greetingService';
import type { GreetingRequest } from '../types';

export function useGreeting() {
  const { accessToken, user } = useAuthStore();
  const [isGenerating, setIsGenerating] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const generateGreeting = async (data: GreetingRequest) => {
    if (!accessToken) {
      setError('인증이 필요합니다.');
      return;
    }

    setIsGenerating(true);
    setError(null);
    setResult(null);

    try {
      const greeting = await GreetingService.generateGreeting(accessToken, {
        ...data,
        user_input: data.user_input || '',
        enabled_contexts: data.enabled_contexts || []
      });
      setResult(greeting);
    } catch (err: any) {
      setError(err.message || '인삿말 생성에 실패했습니다.');
    } finally {
      setIsGenerating(false);
    }
  };

  return {
    isGenerating,
    result,
    error,
    generateGreeting,
    preferredRegion: user?.preferred_region || null
  };
}
