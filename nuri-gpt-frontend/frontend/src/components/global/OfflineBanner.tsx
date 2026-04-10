import { useNetworkStatus } from '../../hooks/useNetworkStatus';
import { WifiOff } from 'lucide-react';

export const OfflineBanner = () => {
  const isOnline = useNetworkStatus();

  if (isOnline) return null;

  return (
    <div className="fixed top-0 left-0 w-full z-[9999] bg-red-500 text-white px-4 py-2 flex items-center justify-center gap-2 shadow-md animate-slide-down">
      <WifiOff className="w-4 h-4" />
      <span className="text-sm font-medium">
        인터넷 연결이 끊어졌습니다. 네트워크 상태를 확인해주세요.
      </span>
    </div>
  );
};
