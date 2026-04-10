import { useState, useEffect } from 'react';
import { showToast } from '../components/global/ToastContainer';

export const useNetworkStatus = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      showToast('인터넷 연결이 복구되었습니다.', 'success');
    };
    
    const handleOffline = () => {
      setIsOnline(false);
      showToast('인터넷 연결이 끊어졌습니다. 오프라인 상태입니다.', 'error');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return isOnline;
};
