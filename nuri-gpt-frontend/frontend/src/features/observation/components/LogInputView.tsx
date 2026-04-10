import { ArrowLeft, Sparkles, ScanText } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { DAYS, type Day } from '../../../utils/objectUtils';

interface LogInputViewProps {
  semanticJson: Record<string, unknown> | null | undefined;
  isTemplateLoading: boolean;
  isGenerating: boolean;
  childAge: number | null;
  setChildAge: (age: number | null) => void;
  showAgeError: boolean;
  setShowAgeError: (show: boolean) => void;
  mode: 'manual' | 'auto';
  manualInputs: Record<string, string>;
  onManualInputChange: (field: string, value: string) => void;
  autoInput: string;
  setAutoInput: (val: string) => void;
  triggerUpload: (fieldId: string) => void;
  onFinalizeClick: () => void;
  isAggressiveMode: boolean;
}

export function LogInputView({
  semanticJson,
  isTemplateLoading,
  isGenerating,
  childAge,
  setChildAge,
  showAgeError,
  setShowAgeError,
  mode,
  manualInputs,
  onManualInputChange,
  autoInput,
  setAutoInput,
  triggerUpload,
  onFinalizeClick,
  isAggressiveMode,
}: LogInputViewProps) {
  const { t } = useTranslation();

  const toPlaceholder = (value: unknown): string => {
    if (Array.isArray(value)) return value.join(', ');
    if (typeof value === 'object' && value !== null) return '';
    return String(value ?? '');
  };

  // 단일 입력 행 렌더링 (소분류 헤더 + 콘텐츠 셀)
  // innerLabel: 3수준 키, 입력 영역 상단에 표시 (없으면 2수준만 표시)
  const renderSubRow = (subKey: string, flatKey: string, placeholder: string, isFirst: boolean, innerLabel?: string, hideSubKey?: boolean) => (
    <div
      key={flatKey}
      className="flex flex-1"
      style={isFirst ? undefined : { borderTop: '1px solid rgba(150, 160, 155, 0.25)' }}
    >
      <div className="doc-sub-header-col">{hideSubKey ? '' : subKey}</div>
      <div className="doc-content-col">
        {innerLabel && (
          <span className="doc-inner-label">{innerLabel}</span>
        )}
        <button
          onClick={() => triggerUpload(flatKey)}
          disabled={isGenerating}
          className="doc-ocr-btn"
        >
          <ScanText className="w-3.5 h-3.5" />
          OCR 업로드
        </button>
        <textarea
          className="doc-textarea"
          placeholder={placeholder}
          value={manualInputs[flatKey] || ''}
          onChange={(e) => onManualInputChange(flatKey, e.target.value)}
        />
      </div>
    </div>
  );

  // 대분류 행 렌더링: 소분류가 요일 구조이면 행으로 나열, 아니면 소분류별 행
  const renderDocRow = (topKey: string, topValue: Record<string, unknown>) => {
    const subEntries = Object.entries(topValue);
    const subRows: React.ReactNode[] = [];

    subEntries.forEach(([subKey, subValue], subIdx) => {
      if (typeof subValue === 'object' && subValue !== null && !Array.isArray(subValue)) {
        // 3단계 구조: subValue의 키가 요일인지 확인
        const innerEntries = Object.entries(subValue as Record<string, unknown>);
        const hasOnlyDayKeys = innerEntries.every(([k]) => DAYS.includes(k as Day));

        if (hasOnlyDayKeys) {
          // 요일 필드 → subKey를 헤더 셀, 요일을 innerLabel로 상단 표시
          // 같은 subKey 그룹 내 첫 행만 헤더 표시, 나머지는 hideSubKey
          innerEntries.forEach(([dayKey, dayValue], dayIdx) => {
            const flatKey = `${topKey}.${subKey}.${dayKey}`;
            const placeholder = toPlaceholder(dayValue);
            const isFirst = subIdx === 0 && dayIdx === 0;
            subRows.push(renderSubRow(subKey, flatKey, placeholder, isFirst, dayKey, dayIdx > 0));
          });
        } else {
          // 일반 3단계 중첩 → subKey를 헤더 셀, innerKey를 innerLabel로 상단 표시
          innerEntries.forEach(([innerKey, innerValue], innerIdx) => {
            const flatKey = `${topKey}.${subKey}.${innerKey}`;
            const placeholder = toPlaceholder(innerValue);
            const isFirst = subIdx === 0 && innerIdx === 0;
            subRows.push(renderSubRow(subKey, flatKey, placeholder, isFirst, innerKey));
          });
        }
      } else {
        // 2단계 구조: 바로 단말 값
        const flatKey = `${topKey}.${subKey}`;
        const placeholder = toPlaceholder(subValue);
        subRows.push(renderSubRow(subKey, flatKey, placeholder, subIdx === 0));
      }
    });

    return (
      <div key={topKey} className="doc-row">
        <div className="doc-header-col">{topKey}</div>
        <div className="flex flex-col flex-1">{subRows}</div>
      </div>
    );
  };

  // 테이블 뷰 렌더링
  const renderTableView = (data: Record<string, unknown>) => {
    const topEntries = Object.entries(data);
    return (
      <div className="doc-table mode-switch-fade">
        {topEntries.map(([topKey, topValue]) => {
          if (typeof topValue === 'object' && topValue !== null && !Array.isArray(topValue)) {
            return renderDocRow(topKey, topValue as Record<string, unknown>);
          }
          // 1단계 단말 (드문 경우)
          const flatKey = topKey;
          const placeholder = toPlaceholder(topValue);
          return (
            <div key={topKey} className="doc-row">
              <div className="doc-header-col">{topKey}</div>
              <div className="doc-content-col">
                <button
                  onClick={() => triggerUpload(flatKey)}
                  disabled={isGenerating}
                  className="doc-ocr-btn"
                >
                  <ScanText className="w-3.5 h-3.5" />
                  OCR 업로드
                </button>
                <textarea
                  className="doc-textarea"
                  placeholder={placeholder}
                  value={manualInputs[flatKey] || ''}
                  onChange={(e) => onManualInputChange(flatKey, e.target.value)}
                />
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <>
      {isTemplateLoading && (
        <div className="absolute inset-0 z-10 bg-white/50 backdrop-blur-sm rounded-[1.5rem] flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      <p className="text-sm text-[var(--color-on-surface-variant)] mb-8">
        각 항목에 내용을 입력하세요
      </p>

      {/* 연령 선택 */}
      <div className={`age-select-container ${showAgeError && childAge === null ? 'error' : ''}`}>
        <label>대상 아동 연령 (필수)</label>
        <select
          value={childAge ?? ''}
          onChange={(e) => {
            setChildAge(e.target.value === '' ? null : parseInt(e.target.value, 10));
            setShowAgeError(false);
          }}
          className="age-select"
        >
          <option value="">선택하세요</option>
          <option value="0">0세</option>
          <option value="1">1세</option>
          <option value="2">2세</option>
          <option value="3">3세</option>
          <option value="4">4세</option>
          <option value="5">5세</option>
        </select>
      </div>

      {mode === 'manual' && semanticJson ? (
        renderTableView(semanticJson)
      ) : mode === 'manual' ? (
        <div className="text-center text-[var(--color-on-surface-variant)] py-8 mode-switch-fade">
          템플릿 구조를 불러올 수 없습니다.
        </div>
      ) : (
        <section className="relative mode-switch-fade">
          <div className="flat-field-header">
            <button
              onClick={() => triggerUpload('auto')}
              disabled={isGenerating}
              className="ocr-btn"
            >
              {t('observation.ocrUpload')}
            </button>
          </div>
          <textarea
            value={autoInput}
            onChange={(e) => setAutoInput(e.target.value)}
            className="input-textarea auto-textarea"
            placeholder={t('observation.autoPlaceholder')}
          />
        </section>
      )}

      <div className="writing-footer">
        <div className="flex-1">
          {isAggressiveMode && (
            <div className="smart-fill-hint">
              <Sparkles className="w-3.5 h-3.5" />
              <span>스마트 채우기 활성화</span>
            </div>
          )}
        </div>
        <div className="footer-actions">
          <button onClick={onFinalizeClick} disabled={isGenerating} className="btn-primary">
            {isGenerating ? <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" /> : null}
            <span>작성 완료</span>
            <ArrowLeft className="w-5 h-5 rotate-180" />
          </button>
        </div>
      </div>
    </>
  );
}
