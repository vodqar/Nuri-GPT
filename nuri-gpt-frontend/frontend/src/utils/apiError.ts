import axios from 'axios';

/**
 * API 에러로부터 사용자 친화 메시지를 추출한다.
 *
 * 지원 형태:
 * - AxiosError: `response.data.message`, `response.data.detail`
 * - fetch 기반 `Error('메시지')`
 * - 그 외 알 수 없는 값
 */
export function extractApiErrorMessage(err: unknown, fallback: string): string {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data as { message?: unknown; detail?: unknown } | undefined;
    const message = data?.message;
    if (typeof message === 'string' && message.length > 0) {
      return message;
    }
    const detail = data?.detail;
    if (typeof detail === 'string' && detail.length > 0) {
      return detail;
    }
    if (err.message) {
      return err.message;
    }
  }

  if (err instanceof Error && err.message) {
    return err.message;
  }

  return fallback;
}
