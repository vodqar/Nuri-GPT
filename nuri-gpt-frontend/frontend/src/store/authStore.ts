import { create } from 'zustand';

export type UserRole = 'admin' | 'org_manager' | 'user';

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  preferences: Record<string, any>;
}

interface AuthState {
  isAuthenticated: boolean;
  accessToken: string | null;
  user: User | null;
  login: (accessToken: string, user: User) => void;
  logout: () => void;
  setToken: (accessToken: string) => void;
  refreshAccessToken: () => Promise<boolean>;
  updatePreferences: (preferences: Record<string, any>) => void;
}

/**
 * Auth Store - 메모리 기반 인증 상태 관리
 *
 * 보안 설계:
 * - access_token은 메모리(Zustand store)에만 저장
 * - localStorage 사용하지 않음 (XSS 공격 방지)
 * - refresh_token은 httpOnly 쿠키로 백엔드에서만 관리
 */
export const useAuthStore = create<AuthState>()((set, get) => ({
  isAuthenticated: false,
  accessToken: null,
  user: null,

  login: (accessToken: string, user: User) =>
    set({ isAuthenticated: true, accessToken, user }),

  logout: () =>
    set({ isAuthenticated: false, accessToken: null, user: null }),

  setToken: (accessToken: string) => set({ accessToken }),

  updatePreferences: (preferences: Record<string, any>) =>
    set((state) => ({
      user: state.user ? { ...state.user, preferences } : state.user,
    })),

  /**
   * 토큰 갱신 요청
   * refresh_token은 httpOnly 쿠키로 자동 전송됨
   *
   * 이 호출만 의도적으로 axios 인스턴스를 사용하지 않는다.
   * 이유: `services/api.ts`의 axios 응답 인터셉터가 401을 받으면 이 함수를
   * 호출하여 토큰을 갱신하고 원 요청을 재시도한다. 만약 이 함수 자체를
   * axios로 호출하면, `/auth/refresh`가 401을 반환할 때 인터셉터가 다시
   * 이 함수를 호출하는 순환이 발생할 수 있다. 따라서 fetch로 격리한다.
   *
   * @returns 성공 여부
   */
  refreshAccessToken: async () => {
    try {
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        credentials: 'include', // httpOnly 쿠키 전송
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        // 401이면 세션 만료 - 로그아웃
        if (response.status === 401) {
          get().logout();
        }
        return false;
      }

      const data = await response.json();
      if (data.access_token) {
        const update: Partial<AuthState> = { accessToken: data.access_token, isAuthenticated: true };
        if (data.user) {
          update.user = data.user as User;
        }
        set(update);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return false;
    }
  },
}));
