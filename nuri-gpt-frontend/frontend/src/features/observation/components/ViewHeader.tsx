import { ArrowLeft, ChevronLeft, X, Layout, type LucideIcon } from 'lucide-react';

interface ViewHeaderProps {
  title: string;
  onBack?: () => void;
  rightContent?: React.ReactNode;
  backIcon?: 'arrowLeft' | 'chevronLeft' | 'close' | 'none';
  disabled?: boolean;
}

const iconMap: Record<string, LucideIcon> = {
  arrowLeft: ArrowLeft,
  chevronLeft: ChevronLeft,
  close: X,
  none: Layout,
};

export function ViewHeader({
  title,
  onBack,
  rightContent,
  backIcon = 'arrowLeft',
  disabled = false,
}: ViewHeaderProps) {
  const Icon = iconMap[backIcon];
  const isNone = backIcon === 'none';

  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 sm:gap-6 mb-6 sm:mb-8">
      <div className="flex items-center gap-3 min-w-0 shrink">
        {onBack ? (
          <button
            onClick={onBack}
            disabled={disabled}
            className="group flex items-center gap-2 transition-colors disabled:opacity-50 text-[var(--color-on-surface-variant)] hover:text-[var(--color-primary)] shrink-0"
            aria-label="뒤로 가기"
          >
            <div className="w-10 h-10 rounded-full flex items-center justify-center transition-colors bg-[var(--color-surface-container-low)] group-hover:bg-[var(--color-primary)]/10">
              <Icon className="w-5 h-5" />
            </div>
          </button>
        ) : isNone ? (
          <div className="w-10 h-10 rounded-full flex items-center justify-center bg-[var(--color-surface-container-low)] text-[var(--color-primary)]/40 shrink-0">
            <Icon className="w-5 h-5" />
          </div>
        ) : null}
        <h2 className="text-xl sm:text-3xl font-extrabold text-[var(--color-on-surface)] tracking-tight font-headline sm:truncate sm:min-w-0">
          {title}
        </h2>
      </div>
      <div className="w-full sm:w-auto">
        {rightContent}
      </div>
    </div>
  );
}
