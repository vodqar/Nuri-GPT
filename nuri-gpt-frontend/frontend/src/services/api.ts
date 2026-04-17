import axios, { type AxiosRequestConfig, type InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '../store/authStore';
import type { RegenerateLogRequest, RegenerateLogResponse, JournalListResponse, JournalResponse } from '../types/api';
import { showToast } from '../components/global/ToastContainer';

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

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
 * FormData 업로드 공통 옵션
 *
 * 업로드 요청에서는 axios 인스턴스의 기본 `Content-Type: application/json`을
 * 제거해야 브라우저가 FormData boundary를 포함한 `multipart/form-data`
 * 헤더를 자동으로 설정한다. axios v1에서는 `Content-Type`을 `undefined`로
 * 전달하면 헤더가 제거된다.
 */
const UPLOAD_CONFIG: AxiosRequestConfig = {
  timeout: 60_000,
  headers: {
    // axios v1: undefined는 해당 헤더 제거를 의미. 브라우저가 boundary를 붙여 설정하도록 위임.
    'Content-Type': undefined,
  },
};

const uploadFormData = async <T = unknown>(path: string, formData: FormData): Promise<T> => {
  const response = await api.post<T>(path, formData, UPLOAD_CONFIG);
  return response.data;
};

/**
 * OCR 메모 업로드 (JWT에서 user_id 추출)
 */
export const uploadOcr = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  return uploadFormData('/upload/memo', formData);
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
 * 템플릿 업로드 (JWT에서 user_id 추출) — deprecated: createTemplate 사용 권장
 */
export const uploadTemplate = async (file: File, templateName: string) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('template_name', templateName);
  return uploadFormData('/upload/template', formData);
};

/**
 * 템플릿 이미지 분석 전용 (저장 없음)
 * structure_json만 반환
 */
export const analyzeTemplateImage = async (file: File): Promise<{ structure_json: Record<string, unknown> }> => {
  const formData = new FormData();
  formData.append('file', file);
  return uploadFormData<{ structure_json: Record<string, unknown> }>('/upload/template/analyze', formData);
};

/**
 * 템플릿 생성 (저장 전용)
 * structure_json + 선택적 이미지. 이미지 없으면 수동 트랙.
 */
export const createTemplate = async (params: {
  templateName: string;
  structureJson: Record<string, unknown>;
  file?: File;
}) => {
  const formData = new FormData();
  formData.append('template_name', params.templateName);
  formData.append('structure_json', JSON.stringify(params.structureJson));
  if (params.file) {
    formData.append('file', params.file);
  }
  return uploadFormData('/templates/', formData);
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

/**
 * 현재 사용자 할당량/사용량 조회
 */
export const getUserUsage = async <T>(): Promise<T> => {
  const response = await api.get<T>('/users/me/usage');
  return response.data;
};

/**
 * 앱 부팅용 통합 조회 (user + templates + usage, 1 RTT)
 */
export const getBootstrap = async <T>(): Promise<T> => {
  const response = await api.get<T>('/users/me/bootstrap');
  return response.data;
};
