import { useState } from 'react';
import { useAuthStore } from '../../../store/authStore';
import { GreetingService } from '../services/greetingService';
import { extractApiErrorMessage } from '../../../utils/apiError';
import type { GreetingRequest } from '../types';

export function useGreeting() {
  const { user } = useAuthStore();
  const [isGenerating, setIsGenerating] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const generateGreeting = async (data: GreetingRequest) => {
    setIsGenerating(true);
    setError(null);
    setResult(null);

    try {
      const greeting = await GreetingService.generateGreeting({
        ...data,
        user_input: data.user_input || '',
        enabled_contexts: data.enabled_contexts || []
      });
      setResult(greeting);
    } catch (err) {
      setError(extractApiErrorMessage(err, '인삿말 생성에 실패했습니다.'));
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
