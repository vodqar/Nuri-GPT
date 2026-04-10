import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { showToast } from '../components/global/ToastContainer';

export const useAuthInterceptor = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const handleUnauthorized = () => {
      showToast('세션이 만료되었습니다. 다시 로그인해주세요.', 'error');
      navigate('/login', { replace: true });
    };

    window.addEventListener('auth:unauthorized', handleUnauthorized);

    return () => {
      window.removeEventListener('auth:unauthorized', handleUnauthorized);
    };
  }, [navigate]);
};
