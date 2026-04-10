import axios, { type InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '../store/authStore';
import type { RegenerateLogRequest, RegenerateLogResponse, JournalListResponse, JournalResponse } from '../types/api';
import { showToast } from '../components/global/ToastContainer';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30_000, // 일반 API: 30초
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // httpOnly 쿠키 전송
});

// 토큰 갱신 중인지 추적
let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

function subscribeTokenRefresh(callback: (token: string) => void) {
  refreshSubscribers.push(callback);
}

function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach((callback) => callback(token));
  refreshSubscribers = [];
}

// Request Interceptor: Add Authorization header if token exists
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response Interceptor: Handle 401 with auto-refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (!error.response) {
      // 네트워크 오류
      if (error.code === 'ECONNABORTED' || error.message?.includes('Network Error')) {
        showToast('네트워크 연결을 확인해주세요', 'error');
      }
      return Promise.reject(error);
    }

    const status = error.response.status;

    // 401 Unauthorized 처리
    if (status === 401 && !originalRequest._retry) {
      // 이미 갱신 중이면 대기열에 추가
      if (isRefreshing) {
        return new Promise((resolve) => {
          subscribeTokenRefresh((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            resolve(api(originalRequest));
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // 토큰 갱신 시도
        const refreshed = await useAuthStore.getState().refreshAccessToken();

        if (refreshed) {
          const newToken = useAuthStore.getState().accessToken;
          if (newToken) {
            // 대기 중인 요청들 처리
            onTokenRefreshed(newToken);
            // 현재 요청 재시도
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            return api(originalRequest);
          }
        }

        // 갱신 실패 - 로그아웃 및 리다이렉트
        useAuthStore.getState().logout();
        window.dispatchEvent(new CustomEvent('auth:unauthorized'));
        return Promise.reject(error);
      } catch (refreshError) {
        useAuthStore.getState().logout();
        window.dispatchEvent(new CustomEvent('auth:unauthorized'));
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    // 다른 HTTP 에러 처리
    if (status === 403) {
      showToast('접근 권한이 없습니다', 'error');
    } else if (status === 408 || status === 504) {
      showToast('서버 응답 시간 초과', 'error');
    } else if (status === 429) {
      showToast('요청이 너무 많습니다. 잠시 후 시도해주세요', 'error');
    } else if (status >= 500) {
      showToast('서버 오류가 발생했습니다', 'error');
    }

    return Promise.reject(error);
  }
);

/**
 * 템플릿 목록 조회 (JWT에서 user_id 추출)
 */
export const getTemplates = async () => {
  const response = await api.get('/templates/');
  return response.data;
};

/**
 * FormData 전용 fetch 헬퍼 (인증 + 401 갱신 로직 포함)
 */
const fetchFormData = async (path: string, formData: FormData, retry = true): Promise<unknown> => {
  const token = useAuthStore.getState().accessToken;
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 60_000);

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST',
      headers,
      body: formData,
      signal: controller.signal,
      credentials: 'include', // httpOnly 쿠키 전송
    });

    // 401 처리 - 토큰 갱신 후 재시도
    if (response.status === 401 && retry) {
      const refreshed = await useAuthStore.getState().refreshAccessToken();
      if (refreshed) {
        // 재시도 (retry=false로 무한루프 방지)
        return fetchFormData(path, formData, false);
      }
      // 갱신 실패
      useAuthStore.getState().logout();
      window.dispatchEvent(new CustomEvent('auth:unauthorized'));
      throw new Error('인증이 만료되었습니다. 다시 로그인해주세요.');
    }

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      const detail = errorBody?.detail || `HTTP ${response.status}`;
      throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
    }

    return await response.json();
  } catch (error) {
    if ((error as Error).name === 'AbortError') {
      showToast('업로드 시간이 초과되었습니다', 'error');
      throw new Error('Timeout');
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
};

/**
 * OCR 메모 업로드 (JWT에서 user_id 추출)
 */
export const uploadOcr = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  return fetchFormData('/upload/memo', formData);
};

/**
 * 관찰일지 생성
 */
export const generateLog = async (data: Record<string, unknown>) => {
  const response = await api.post('/generate/log', data, {
    timeout: 120_000, // 120초
  });
  return response.data;
};

/**
 * 템플릿 업로드 (JWT에서 user_id 추출)
 */
export const uploadTemplate = async (file: File, templateName: string) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('template_name', templateName);
  return fetchFormData('/upload/template', formData);
};

/**
 * 관찰일지 재생성
 */
export const regenerateLog = async (data: RegenerateLogRequest): Promise<RegenerateLogResponse> => {
  const response = await api.post('/generate/regenerate', data, {
    timeout: 120_000,
  });
  return response.data;
};

/**
 * 템플릿 삭제
 */
export const deleteTemplate = async (templateId: string) => {
  const response = await api.delete(`/templates/${templateId}`);
  return response.data;
};

/**
 * 템플릿 수정
 */
export const updateTemplate = async (templateId: string, data: { name?: string }) => {
  const response = await api.patch(`/templates/${templateId}`, data);
  return response.data;
};

/**
 * 템플릿 순서 변경
 */
export const updateTemplateOrder = async (orders: { id: string; sort_order: number }[]) => {
  const response = await api.put('/templates/order', { orders });
  return response.data;
};

/**
 * 관찰일지 목록 조회
 */
export const getJournals = async (limit = 20, offset = 0): Promise<JournalListResponse> => {
  const response = await api.get('/journals', { params: { limit, offset } });
  return response.data;
};

/**
 * 관찰일지 그룹 히스토리 조회
 */
export const getJournalGroupHistory = async (groupId: string): Promise<JournalResponse[]> => {
  const response = await api.get(`/journals/group/${groupId}`);
  return response.data;
};

/**
 * 관찰일지 그룹 삭제
 */
export const deleteJournalGroup = async (groupId: string): Promise<void> => {
  await api.delete(`/journals/group/${groupId}`);
};

/**
 * 로그인 API
 */
export const login = async (email: string, password: string) => {
  const response = await api.post('/auth/login', { email, password });
  return response.data;
};

/**
 * 로그아웃 API
 */
export const logout = async () => {
  const response = await api.post('/auth/logout');
  return response.data;
};

/**
 * 현재 사용자 정보 조회
 */
export const getCurrentUser = async () => {
  const response = await api.get('/users/me');
  return response.data;
};
