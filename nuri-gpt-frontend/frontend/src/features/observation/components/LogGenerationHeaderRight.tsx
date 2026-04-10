import { CircleHelp, Sparkles } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { cn } from '../../../utils/cn';

interface LogGenerationHeaderRightProps {
  isAggressiveMode: boolean;
  setIsAggressiveMode: (val: boolean) => void;
  mode: 'manual' | 'auto';
  setMode: (mode: 'manual' | 'auto') => void;
}

export function LogGenerationHeaderRight({
  isAggressiveMode,
  setIsAggressiveMode,
  mode,
  setMode,
}: LogGenerationHeaderRightProps) {
  const { t } = useTranslation();

  return (
    <div className="flex items-center gap-4 sm:gap-6 w-full sm:w-auto justify-between sm:justify-end">
      <div className="smart-fill-toggle">
        <div className="smart-fill-info-wrapper">
          <CircleHelp className="smart-fill-help-icon" />
          <div className="smart-fill-tooltip">
            <strong>스마트 채우기</strong>
            <p>
              입력된 내용을 참고해 모든 빈 칸을 적극적으로 채웁니다.{' '}
              <span className="smart-fill-warning">
                입력된 정보가 충분하지 않은 경우 일부 허구가 포함될 수 있습니다
              </span>
              .
            </p>
          </div>
        </div>
        <label
          className="smart-fill-label"
          onClick={() => setIsAggressiveMode(!isAggressiveMode)}
        >
          <span className={cn('smart-fill-text', isAggressiveMode && 'active')}>
            스마트 채우기
          </span>
          <Sparkles className={cn('smart-fill-icon', isAggressiveMode && 'active')} />
        </label>
        <label className="smart-fill-switch">
          <input
            type="checkbox"
            checked={isAggressiveMode}
            onChange={(e) => setIsAggressiveMode(e.target.checked)}
          />
          <span className="smart-fill-slider"></span>
        </label>
      </div>

      <div className="mode-toggle-container">
        <div className="mode-toggle">
          <button
            onClick={() => setMode('manual')}
            className={cn('mode-btn', mode === 'manual' && 'mode-btn-active')}
          >
            {t('observation.modeManual')}
          </button>
          <button
            onClick={() => setMode('auto')}
            className={cn('mode-btn', mode === 'auto' && 'mode-btn-active')}
          >
            {t('observation.modeAuto')}
          </button>
        </div>
      </div>
    </div>
  );
}
