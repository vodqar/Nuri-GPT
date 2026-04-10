import { Outlet } from 'react-router-dom';

export const PublicRoute = () => {
  // 수동 입력으로 /login 접근 가능하도록 리다이렉트 제거
  return <Outlet />;
};
