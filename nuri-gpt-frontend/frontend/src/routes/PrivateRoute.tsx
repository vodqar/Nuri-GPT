import { Outlet, Navigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { useEffect, useState } from 'react';

export const PrivateRoute = () => {
  const { isAuthenticated, refreshAccessToken } = useAuthStore();
  // 초기 인증 복원 진행 중 여부 (새로고침 시 즉시 /login 리디렉션 방지)
  const [isInitializing, setIsInitializing] = useState(!isAuthenticated);

  useEffect(() => {
    // 이미 인증된 경우 초기화 불필요
    if (isAuthenticated) {
      setIsInitializing(false);
      return;
    }

    // 새로고침 시 httpOnly 쿠키의 refresh_token으로 access_token 복원 시도
    refreshAccessToken().finally(() => {
      setIsInitializing(false);
    });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // 복원 시도 중: 로딩 표시 (빈 화면 또는 스피너)
  if (isInitializing) {
    return null;
  }

  // 복원 실패 또는 미인증: 로그인 페이지로 이동
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
};
