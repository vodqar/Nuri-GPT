import { useEffect, useRef, useCallback, useState } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';
import { cn } from '../../utils/cn';

interface ModalAction {
  label: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary' | 'danger';
}

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  children?: React.ReactNode;
  primaryAction?: ModalAction;
  secondaryAction?: ModalAction;
  showCloseButton?: boolean;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl' | '5xl' | 'full';
}

export function Modal({
  isOpen,
  onClose,
  title,
  description,
  children,
  primaryAction,
  secondaryAction,
  showCloseButton = true,
  maxWidth = 'md',
}: ModalProps) {
  const overlayRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const mouseDownOnOverlay = useRef(false);
  const [isExiting, setIsExiting] = useState(false);
  const [shouldRender, setShouldRender] = useState(false);

  // Exit 애니메이션과 함께 닫기
  const triggerClose = useCallback(() => {
    setIsExiting(true);
    setTimeout(() => {
      setIsExiting(false);
      onClose();
    }, 250); // modal exit duration
  }, [onClose]);

  // ESC 키 핸들러
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen && !isExiting) {
        triggerClose();
      }
    },
    [isOpen, isExiting, triggerClose]
  );

  // isOpen 변경에 따른 렌더링 제어
  useEffect(() => {
    if (isOpen) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setShouldRender(true);
       
      setIsExiting(false);
    } else if (!isOpen && !isExiting) {
      // 외부에서 isOpen이 false로 변경된 경우
      setShouldRender(false);
    }
  }, [isOpen, isExiting]);

  useEffect(() => {
    if (shouldRender) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [shouldRender, handleKeyDown]);

  const handleOverlayMouseDown = (e: React.MouseEvent) => {
    if (e.target === overlayRef.current) {
      mouseDownOnOverlay.current = true;
    } else {
      mouseDownOnOverlay.current = false;
    }
  };

  const handleOverlayMouseUp = (e: React.MouseEvent) => {
    if (e.target === overlayRef.current && mouseDownOnOverlay.current && !isExiting) {
      triggerClose();
    }
    mouseDownOnOverlay.current = false;
  };

  const getButtonClasses = (variant: ModalAction['variant'] = 'secondary') => {
    const base =
      'px-5 py-2.5 rounded-xl font-semibold text-sm transition-all duration-200';

    switch (variant) {
      case 'primary':
        return cn(
          base,
          'bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary-dim)]'
        );
      case 'danger':
        return cn(base, 'bg-red-500 text-white hover:bg-red-600');
      default:
        return cn(
          base,
          'bg-[var(--color-surface-container-low)] text-[var(--color-on-surface)] hover:bg-[var(--color-surface-container-high)]'
        );
    }
  };

  if (!shouldRender) return null;

  return createPortal(
    <div
      ref={overlayRef}
      className="fixed inset-0 z-[10000] flex items-center justify-center p-4"
      onMouseDown={handleOverlayMouseDown}
      onMouseUp={handleOverlayMouseUp}
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? 'modal-title' : undefined}
    >
      {/* Backdrop - fade only */}
      <div className={cn(
        "modal-backdrop absolute inset-0 bg-black/40 backdrop-blur-sm",
        isExiting ? "animate-fade-out" : "animate-fade-in"
      )} />

      {/* Modal Content */}
      <div
        ref={contentRef}
        className={cn(
          "modal-content relative bg-white rounded-2xl shadow-2xl w-full overflow-hidden transition-all duration-300",
          {
            'max-w-sm': maxWidth === 'sm',
            'max-w-md': maxWidth === 'md',
            'max-w-lg': maxWidth === 'lg',
            'max-w-xl': maxWidth === 'xl',
            'max-w-2xl': maxWidth === '2xl',
            'max-w-3xl': maxWidth === '3xl',
            'max-w-4xl': maxWidth === '4xl',
            'max-w-5xl': maxWidth === '5xl',
            'max-w-full': maxWidth === 'full',
          },
          isExiting ? "animate-modal-exit" : "animate-modal-enter"
        )}
      >
        {/* Header */}
        {(title || showCloseButton) && (
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
            {title && (
              <h2
                id="modal-title"
                className="text-lg font-bold text-[var(--color-on-surface)]"
              >
                {title}
              </h2>
            )}
            {showCloseButton && (
              <button
                onClick={triggerClose}
                className="p-2 rounded-full hover:bg-gray-100 transition-colors -mr-2"
                aria-label="닫기"
              >
                <X className="w-5 h-5 text-[var(--color-on-surface-variant)]" />
              </button>
            )}
          </div>
        )}

        {/* Body */}
        <div className="px-6 py-5">
          {description && (
            <p className="text-[var(--color-on-surface-variant)] mb-4">
              {description}
            </p>
          )}
          {children}
        </div>

        {/* Footer */}
        {(primaryAction || secondaryAction) && (
          <div className="flex justify-end gap-3 px-6 py-4 bg-gray-50">
            {secondaryAction && (
              <button
                onClick={secondaryAction.onClick}
                className={getButtonClasses(secondaryAction.variant)}
              >
                {secondaryAction.label}
              </button>
            )}
            {primaryAction && (
              <button
                onClick={primaryAction.onClick}
                className={getButtonClasses(primaryAction.variant || 'primary')}
              >
                {primaryAction.label}
              </button>
            )}
          </div>
        )}
      </div>
    </div>,
    document.body
  );
}

