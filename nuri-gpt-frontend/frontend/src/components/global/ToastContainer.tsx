import { useState, useCallback, useRef, useEffect } from 'react';
import { Toast, type ToastItem } from './Toast';

interface ToastState extends ToastItem {
  isLeaving: boolean;
}

export function ToastContainer() {
  const [toasts, setToasts] = useState<ToastState[]>([]);
  const toastIdRef = useRef(0);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) =>
      prev.map((t) => (t.id === id ? { ...t, isLeaving: true } : t))
    );

    // 애니메이션 후 완전 제거
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 300);
  }, []);

  const addToast = useCallback((message: string, type: ToastItem['type'] = 'info') => {
    const id = `toast-${++toastIdRef.current}`;
    const newToast: ToastState = {
      id,
      message,
      type,
      isLeaving: false,
    };

    // 안드로이드 방식: 기존 토스트 제거 후 새 토스트만 표시
    setToasts([newToast]);

    // 3초 후 자동 닫힘
    setTimeout(() => {
      removeToast(id);
    }, 3000);
  }, [removeToast]);



  // 전역 접근을 위한 메서드 노출
  useEffect(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (window as any).addToast = addToast;
    return () => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      delete (window as any).addToast;
    };
  }, [addToast]);

  return (
    <div className="toast-container">
      {toasts.map((toast) => (
        <Toast
          key={toast.id}
          toast={toast}
          onClose={removeToast}
          isLeaving={toast.isLeaving}
        />
      ))}
    </div>
  );
}

// 유틸리티 함수
// eslint-disable-next-line react-refresh/only-export-components
export function showToast(message: string, type: ToastItem['type'] = 'info') {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  if ((window as any).addToast) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (window as any).addToast(message, type);
  }
}
