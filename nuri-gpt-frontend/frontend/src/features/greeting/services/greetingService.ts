import { api, API_BASE_URL } from '../../../services/api';
import { useAuthStore } from '../../../store/authStore';
import type { GreetingRequest, GreetingResponse } from '../types';

export type StreamEvent =
  | { event: 'progress'; stage: string }
  | { event: 'token'; text: string }
  | { event: 'done'; greeting: string }
  | { event: 'error'; message: string };

export class GreetingService {
  static async getRegions(): Promise<string[]> {
    const response = await api.get<string[]>('/greeting/regions');
    return response.data;
  }

  static async generateGreeting(data: GreetingRequest): Promise<string> {
    const response = await api.post<GreetingResponse>('/greeting/generate', data, {
      timeout: 120_000, // 날씨 API + Dify LLM 호출로 최대 120초 소요
    });
    return response.data.greeting;
  }

  /**
   * SSE 스트리밍으로 인삿말을 생성한다.
   * 각 이벤트를 onEvent 콜백으로 전달하며, 완료 시 Promise가 resolve된다.
   */
  static async generateGreetingStream(
    data: GreetingRequest,
    onEvent: (event: StreamEvent) => void,
  ): Promise<void> {
    const url = `${API_BASE_URL}/greeting/generate/stream`;

    const doFetch = async (token: string | null): Promise<Response> => {
      return fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: 'include',
        body: JSON.stringify(data),
      });
    };

    let token = useAuthStore.getState().accessToken;
    let response = await doFetch(token);

    // 401 시 토큰 갱신 후 1회 재시도 (axios 인터셉터 미적용이므로 수동 처리)
    if (response.status === 401) {
      const refreshed = await useAuthStore.getState().refreshAccessToken();
      if (refreshed) {
        token = useAuthStore.getState().accessToken;
        response = await doFetch(token);
      }
    }

    if (!response.ok) {
      throw new Error(`스트리밍 요청 실패: ${response.status}`);
    }

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      // 마지막 요소는 불완전할 수 있으므로 버퍼에 유지
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const jsonStr = line.slice(6);
        try {
          const event: StreamEvent = JSON.parse(jsonStr);
          onEvent(event);
          if (event.event === 'done' || event.event === 'error') {
            return;
          }
        } catch {
          // 파싱 실패 시 무시
        }
      }
    }
  }
}
