import { useEffect, useState } from 'react';
import { X, CheckCircle, AlertCircle, Info } from 'lucide-react';
import { cn } from '../../utils/cn';

export interface ToastItem {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info';
}

interface ToastProps {
  toast: ToastItem;
  onClose: (id: string) => void;
  isLeaving?: boolean;
}

const iconMap = {
  success: CheckCircle,
  error: AlertCircle,
  info: Info,
};

const colorMap = {
  success: '#22c55e',
  error: '#ef4444',
  info: '#3b82f6',
};

export function Toast({ toast, onClose, isLeaving }: ToastProps) {
  const Icon = iconMap[toast.type];
  const color = colorMap[toast.type];
  const [isVisible, setIsVisible] = useState(false);

  // 애니메이션 트리거를 위한 지연 visible 클래스 추가
  useEffect(() => {
    const raf = requestAnimationFrame(() => {
      setIsVisible(true);
    });
    return () => cancelAnimationFrame(raf);
  }, []);

  return (
    <div
      className={cn('toast', isLeaving && 'hiding', isVisible && 'visible')}
      role="alert"
    >
      <Icon className="toast-icon" style={{ color }} />
      <span className="flex-1">{toast.message}</span>
      <button
        onClick={() => onClose(toast.id)}
        className="ml-2 p-1 rounded-full hover:bg-white/20 transition-colors"
        aria-label="닫기"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}
