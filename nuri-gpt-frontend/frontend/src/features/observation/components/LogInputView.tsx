import { ArrowLeft, Sparkles, ChevronDown, ChevronRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useState } from 'react';
import { PathBreadcrumb } from './PathBreadcrumb';
import { getFlatFields, DAYS, type FlatField, type Day } from '../../../utils/objectUtils';

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

  // 아코디언 상태 관리
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const [expandedDays, setExpandedDays] = useState<Set<string>>(new Set(['월요일'])); // 월요일 기본 펼침

  // 단일 필드 렌더링 (재사용)
  // isDayField: true면 중분류 키만 표시 (아코디언 내부), false면 전체 경로 표시
  const renderField = (field: FlatField, index: number, isDayField = false) => (
    <div
      key={field.flatKey}
      className="flat-field-card fade-in"
      style={{ animationDelay: `${index * 0.03}s` }}
    >
      <PathBreadcrumb
        path={field.path}
        visibleFromIndex={isDayField ? field.path.length - 1 : 0}
      />
      <div className="flat-field-header">
        <button
          onClick={() => triggerUpload(field.flatKey)}
          disabled={isGenerating}
          className="ocr-btn"
        >
          OCR 업로드
        </button>
      </div>
      <textarea
        className="input-textarea"
        placeholder={field.value}
        value={manualInputs[field.flatKey] || ''}
        onChange={(e) => onManualInputChange(field.flatKey, e.target.value)}
      />
    </div>
  );

  // 중분류 아코디언 토글
  const toggleCategory = (categoryKey: string) => {
    const newSet = new Set(expandedCategories);
    if (newSet.has(categoryKey)) {
      newSet.delete(categoryKey);
    } else {
      newSet.add(categoryKey);
    }
    setExpandedCategories(newSet);
  };

  // 요일 아코디언 토글
  const toggleDay = (dayKey: string) => {
    const newSet = new Set(expandedDays);
    if (newSet.has(dayKey)) {
      newSet.delete(dayKey);
    } else {
      newSet.add(dayKey);
    }
    setExpandedDays(newSet);
  };

  // 중분류 아코디언 렌더링 (요일 필드 그룹)
  const renderCategoryAccordion = (
    categoryKey: string,
    categoryPath: string[],
    fields: FlatField[],
    index: number
  ) => {
    // 요일별로 필드 분리
    const dayMap = new Map<Day, FlatField[]>();
    for (const field of fields) {
      const lastSegment = field.path[field.path.length - 1];
      const day = lastSegment as Day;
      if (DAYS.includes(day)) {
        const dayFields = dayMap.get(day) || [];
        dayFields.push(field);
        dayMap.set(day, dayFields);
      }
    }

    return (
      <div
        key={categoryKey}
        className="category-accordion fade-in"
        style={{ animationDelay: `${index * 0.03}s` }}
      >
        {/* 중분류 헤더 */}
        <button
          onClick={() => toggleCategory(categoryKey)}
          className="category-accordion-header"
        >
          {expandedCategories.has(categoryKey) ? (
            <ChevronDown className="w-4 h-4" />
          ) : (
            <ChevronRight className="w-4 h-4" />
          )}
          <span className="category-path">
            {categoryPath.join(' › ')}
          </span>
        </button>

        {/* 중분류 내용 - 요일별 아코디언 */}
        {expandedCategories.has(categoryKey) && (
          <div className="category-accordion-content">
            {DAYS.map((day) => {
              const dayFields = dayMap.get(day);
              if (!dayFields || dayFields.length === 0) return null;

              const dayKey = `${categoryKey}.${day}`;
              return (
                <div key={day} className="day-accordion">
                  {/* 요일 헤더 */}
                  <button
                    onClick={() => toggleDay(dayKey)}
                    className="day-accordion-header"
                  >
                    {expandedDays.has(dayKey) ? (
                      <ChevronDown className="w-3 h-3" />
                    ) : (
                      <ChevronRight className="w-3 h-3" />
                    )}
                    <span className="day-label">{day}</span>
                  </button>

                  {/* 요일 내용 - 실제 필드들 (중분류 키만 표시) */}
                  {expandedDays.has(dayKey) && (
                    <div className="day-accordion-content">
                      {dayFields.map((field, fieldIndex) => renderField(
                        field,
                        index + fieldIndex,
                        true
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  };

  // 요일별 그룹핑된 필드 렌더링 (JSON 원래 순서 유지)
  const renderDayGroupedFields = (data: Record<string, unknown>) => {
    const flatFields = getFlatFields(data);
    const result: React.ReactNode[] = [];

    let currentCategoryKey: string | null = null;
    let currentCategoryPath: string[] = [];
    let currentCategoryFields: FlatField[] = [];
    let renderedCount = 0;

    for (let i = 0; i < flatFields.length; i++) {
      const field = flatFields[i];
      const lastSegment = field.path[field.path.length - 1];

      if (DAYS.includes(lastSegment as Day)) {
        // 요일 필드
        const categoryPath = field.path.slice(0, -1);
        const categoryKey = categoryPath.join('.');

        if (categoryKey !== currentCategoryKey) {
          // 새로운 중분류 시작 - 이전 중분류 마무리
          if (currentCategoryKey && currentCategoryFields.length > 0) {
            result.push(renderCategoryAccordion(
              currentCategoryKey,
              currentCategoryPath,
              currentCategoryFields,
              renderedCount
            ));
            renderedCount += currentCategoryFields.length;
          }
          currentCategoryKey = categoryKey;
          currentCategoryPath = categoryPath;
          currentCategoryFields = [field];
        } else {
          // 같은 중분류 계속
          currentCategoryFields.push(field);
        }
      } else {
        // 비요일 필드 - 이전 중분류 마무리 후 바로 렌더링
        if (currentCategoryKey && currentCategoryFields.length > 0) {
          result.push(renderCategoryAccordion(
            currentCategoryKey,
            currentCategoryPath,
            currentCategoryFields,
            renderedCount
          ));
          renderedCount += currentCategoryFields.length;
          currentCategoryKey = null;
          currentCategoryFields = [];
        }
        result.push(renderField(field, renderedCount, false));
        renderedCount++;
      }
    }

    // 마지막 중분류 마무리
    if (currentCategoryKey && currentCategoryFields.length > 0) {
      result.push(renderCategoryAccordion(
        currentCategoryKey,
        currentCategoryPath,
        currentCategoryFields,
        renderedCount
      ));
    }

    return <div className="mode-switch-fade">{result}</div>;
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

      <div className="mode-switch-fade">
        {mode === 'manual' && semanticJson ? (
          renderDayGroupedFields(semanticJson)
        ) : mode === 'manual' ? (
          <div className="text-center text-[var(--color-on-surface-variant)] py-8">
            템플릿 구조를 불러올 수 없습니다.
          </div>
        ) : (
          <section className="relative">
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
      </div>

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
