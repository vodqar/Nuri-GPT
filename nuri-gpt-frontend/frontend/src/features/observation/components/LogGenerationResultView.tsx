import { useState, useEffect } from 'react';
import { Copy, Check, MessageSquarePlus, RefreshCw } from 'lucide-react';
import type { GenerateLogResponse } from '../../../types/api';
import { showToast } from '../../../components/global/ToastContainer';
import { ScrollToTop } from '../../../components/global/ScrollToTop';
import { DAYS, type Day } from '../../../utils/objectUtils';

interface LogGenerationResultViewProps {
  history: GenerateLogResponse[];
  currentIndex: number;
  onNavigateHistory: (index: number) => void;
  onRegenerate: (comments: Record<string, string>) => Promise<void>;
  isRegenerating: boolean;
}

export function LogGenerationResultView({
  history,
  currentIndex,
  onNavigateHistory,
  onRegenerate,
  isRegenerating,
}: LogGenerationResultViewProps) {
  const [copiedStates, setCopiedStates] = useState<Record<string, boolean>>({});
  const [comments, setComments] = useState<Record<string, string>>({});
  const [activeCommentId, setActiveCommentId] = useState<string | null>(null);

  // 버전 히스토리가 변경되거나(재생성 포함), 새로운 버전이 생성되면 코멘트 등 초기화
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setComments({});
    setActiveCommentId(null);
  }, [currentIndex]);

  const currentResult = history[currentIndex];

  if (!currentResult) return null;

  // semantic_json의 키 순서를 추출하는 함수
  const getSemanticJsonKeyOrder = (semanticJson: Record<string, unknown>): string[] => {
    const keys: string[] = [];
    const extractKeys = (obj: Record<string, unknown>, prefix = '') => {
      for (const [key, value] of Object.entries(obj)) {
        const fullKey = prefix ? `${prefix}.${key}` : key;
        if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
          extractKeys(value as Record<string, unknown>, fullKey);
        } else {
          keys.push(fullKey);
        }
      }
    };
    extractKeys(semanticJson);
    return keys;
  };

  // 결과 데이터를 중첩 구조로 변환 (LogInputView와 동일한 로직)
  const buildNestedResultData = (): Record<string, unknown> => {
    const result: Record<string, unknown> = {};

    if (currentResult.updated_activities && Array.isArray(currentResult.updated_activities) && currentResult.updated_activities.length > 0) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      for (const activity of currentResult.updated_activities) {
        const id = activity.target_id as string | undefined;
        const value = activity.updated_text || '';
        if (id && value) {
          const parts = id.split('.');
          let current = result;
          for (let i = 0; i < parts.length; i++) {
            const part = parts[i];
            if (i === parts.length - 1) {
              current[part] = value;
            } else {
              if (!(part in current)) {
                current[part] = {};
              }
              current = current[part] as Record<string, unknown>;
            }
          }
        }
      }
    } else if (currentResult.template_mapping && Object.keys(currentResult.template_mapping).length > 0) {
      const mapping = currentResult.template_mapping;
      // semantic_json 순서 유지를 위해 정렬
      if (currentResult.semantic_json && Object.keys(currentResult.semantic_json).length > 0) {
        const keyOrder = getSemanticJsonKeyOrder(currentResult.semantic_json);
        const sortedKeys = keyOrder.filter(key => key in mapping);
        const remainingKeys = Object.keys(mapping).filter(key => !keyOrder.includes(key));
        for (const key of [...sortedKeys, ...remainingKeys]) {
          const parts = key.split('.');
          let current = result;
          for (let i = 0; i < parts.length; i++) {
            const part = parts[i];
            if (i === parts.length - 1) {
              current[part] = mapping[key];
            } else {
              if (!(part in current)) {
                current[part] = {};
              }
              current = current[part] as Record<string, unknown>;
            }
          }
        }
      } else {
        for (const [key, value] of Object.entries(mapping)) {
          const parts = key.split('.');
          let current = result;
          for (let i = 0; i < parts.length; i++) {
            const part = parts[i];
            if (i === parts.length - 1) {
              current[part] = value;
            } else {
              if (!(part in current)) {
                current[part] = {};
              }
              current = current[part] as Record<string, unknown>;
            }
          }
        }
      }
    } else if (currentResult.observation_content) {
      result['관찰 내용'] = currentResult.observation_content;
      if (currentResult.evaluation_content) {
        result['평가 및 지원계획'] = currentResult.evaluation_content;
      }
      if (currentResult.development_areas) {
        result['발달 영역'] = Array.isArray(currentResult.development_areas) ? currentResult.development_areas.join(', ') : currentResult.development_areas;
      }
    }

    return result;
  };

  const nestedData = buildNestedResultData();

  const handleCopy = async (text: string, id: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedStates(prev => ({ ...prev, [id]: true }));
      showToast('복사되었습니다', 'success');
    } catch {
      // Fallback: execCommand
      const textarea = document.createElement('textarea');
      textarea.value = text;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      setCopiedStates(prev => ({ ...prev, [id]: true }));
      showToast('복사되었습니다', 'success');
    }
    setTimeout(() => {
      setCopiedStates(prev => ({ ...prev, [id]: false }));
    }, 2000);
  };

  const handleCommentChange = (id: string, text: string) => {
    setComments(prev => ({ ...prev, [id]: text }));
  };

  const handleRegenerateClick = async () => {
    setActiveCommentId(null);
    try {
      await onRegenerate(comments);
    } catch (err) {
      console.error('Regenerate failed:', err);
    }
  };

  // 빈 문자열이나 공백만 있는 코멘트는 제외하고 카운트
  const commentCount = Object.values(comments).filter(text => text?.trim()).length;

  // 결과 행 렌더링 (코멘트 UI 포함) - LogInputView의 renderSubRow와 유사
  const renderResultSubRow = (
    subKey: string,
    flatKey: string,
    value: string,
    isFirst: boolean,
    innerLabel?: string,
    hideSubKey?: boolean
  ) => {
    const hasComment = !!comments[flatKey];
    const isActive = activeCommentId === flatKey;

    return (
      <div
        key={flatKey}
        className="flex flex-1"
        style={isFirst ? undefined : { borderTop: '1px solid rgba(150, 160, 155, 0.25)' }}
      >
        <div className="doc-sub-header-col">{hideSubKey ? '' : subKey}</div>
        <div
          className={`doc-content-col result-content-col ${isActive ? 'active' : ''} ${hasComment ? 'has-comment' : ''}`}
          onClick={() => setActiveCommentId(isActive ? null : flatKey)}
        >
          {innerLabel && <span className="doc-inner-label">{innerLabel}</span>}

          {/* 액션 버튼들 */}
          <div className="result-actions">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setActiveCommentId(isActive ? null : flatKey);
              }}
              className={`result-action-btn comment-trigger ${hasComment || isActive ? 'active' : ''}`}
              title="수정 요청"
            >
              <MessageSquarePlus className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleCopy(value, flatKey);
              }}
              className="result-action-btn"
              title="복사"
            >
              {copiedStates[flatKey] ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          </div>

          {/* 결과 텍스트 */}
          <div className="result-text">{value}</div>

          {/* 코멘트 입력 영역 */}
          {isActive && (
            <div className="comment-section-result" onClick={(e) => e.stopPropagation()}>
              <textarea
                value={comments[flatKey] || ''}
                onChange={(e) => handleCommentChange(flatKey, e.target.value)}
                placeholder="수정 요청사항을 입력하세요..."
                className="comment-input"
                autoFocus
              />
            </div>
          )}

          {/* 코멘트 뱃지 */}
          {!isActive && hasComment && (
            <div className="comment-badge-result">
              <MessageSquarePlus className="w-3 h-3 shrink-0" />
              <span className="truncate">{comments[flatKey]}</span>
            </div>
          )}
        </div>
      </div>
    );
  };

  // 대분류 행 렌더링 - LogInputView의 renderDocRow와 동일
  const renderResultDocRow = (topKey: string, topValue: Record<string, unknown>) => {
    const subEntries = Object.entries(topValue);
    const subRows: React.ReactNode[] = [];

    subEntries.forEach(([subKey, subValue], subIdx) => {
      if (typeof subValue === 'object' && subValue !== null && !Array.isArray(subValue)) {
        // 3단계 구조: subValue의 키가 요일인지 확인
        const innerEntries = Object.entries(subValue as Record<string, unknown>);
        const hasOnlyDayKeys = innerEntries.every(([k]) => DAYS.includes(k as Day));

        if (hasOnlyDayKeys) {
          // 요일 필드 → subKey를 헤더 셀, 요일을 innerLabel로 상단 표시
          innerEntries.forEach(([dayKey, dayValue], dayIdx) => {
            const flatKey = `${topKey}.${subKey}.${dayKey}`;
            const isFirst = subIdx === 0 && dayIdx === 0;
            subRows.push(renderResultSubRow(subKey, flatKey, String(dayValue), isFirst, dayKey, dayIdx > 0));
          });
        } else {
          // 일반 3단계 중첩 → subKey를 헤더 셀, innerKey를 innerLabel로 상단 표시
          innerEntries.forEach(([innerKey, innerValue], innerIdx) => {
            const flatKey = `${topKey}.${subKey}.${innerKey}`;
            const isFirst = subIdx === 0 && innerIdx === 0;
            subRows.push(renderResultSubRow(subKey, flatKey, String(innerValue), isFirst, innerKey));
          });
        }
      } else {
        // 2단계 구조: 바로 단말 값
        const flatKey = `${topKey}.${subKey}`;
        subRows.push(renderResultSubRow(subKey, flatKey, String(subValue), subIdx === 0));
      }
    });

    return (
      <div key={topKey} className="doc-row">
        <div className="doc-header-col">{topKey}</div>
        <div className="flex flex-col flex-1">{subRows}</div>
      </div>
    );
  };

  // 테이블 뷰 렌더링 - LogInputView의 renderTableView와 동일
  const renderResultTableView = (data: Record<string, unknown>) => {
    const topEntries = Object.entries(data);
    return (
      <div className="doc-table mode-switch-fade">
        {topEntries.map(([topKey, topValue]) => {
          if (typeof topValue === 'object' && topValue !== null && !Array.isArray(topValue)) {
            return renderResultDocRow(topKey, topValue as Record<string, unknown>);
          }
          // 1단계 단말 (드문 경우)
          const flatKey = topKey;
          const hasComment = !!comments[flatKey];
          const isActive = activeCommentId === flatKey;

          return (
            <div key={topKey} className="doc-row">
              <div className="doc-header-col">{topKey}</div>
              <div
                className={`doc-content-col result-content-col ${isActive ? 'active' : ''} ${hasComment ? 'has-comment' : ''}`}
                onClick={() => setActiveCommentId(isActive ? null : flatKey)}
              >
                <div className="result-actions">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setActiveCommentId(isActive ? null : flatKey);
                    }}
                    className={`result-action-btn comment-trigger ${hasComment || isActive ? 'active' : ''}`}
                    title="수정 요청"
                  >
                    <MessageSquarePlus className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCopy(String(topValue), flatKey);
                    }}
                    className="result-action-btn"
                    title="복사"
                  >
                    {copiedStates[flatKey] ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>

                <div className="result-text">{String(topValue)}</div>

                {isActive && (
                  <div className="comment-section-result" onClick={(e) => e.stopPropagation()}>
                    <textarea
                      value={comments[flatKey] || ''}
                      onChange={(e) => handleCommentChange(flatKey, e.target.value)}
                      placeholder="수정 요청사항을 입력하세요..."
                      className="comment-input"
                      autoFocus
                    />
                  </div>
                )}

                {!isActive && hasComment && (
                  <div className="comment-badge-result">
                    <MessageSquarePlus className="w-3 h-3 shrink-0" />
                    <span className="truncate">{comments[flatKey]}</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <>
      {/* Version History & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 fade-in" style={{ animationDelay: '0.1s' }}>
        <div className="age-select-container !mb-0 !p-0">
          <label className="text-xs font-bold uppercase tracking-wider block mb-2" style={{ color: 'var(--color-on-surface-variant)' }}>
            버전 히스토리
          </label>
          <select
            value={currentIndex}
            onChange={(e) => onNavigateHistory(parseInt(e.target.value, 10))}
            className="age-select"
            style={{ maxWidth: '10rem' }}
          >
            {history.map((item, idx) => (
              <option key={idx} value={idx}>
                V{item.version ?? idx + 1} {idx === 0 ? '(최신)' : ''}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Results Table - Animated on version change */}
      <div
        key={currentIndex}
        className="results-scroll-area flex-1 animate-view-enter"
      >
        {Object.keys(nestedData).length > 0 ? (
          renderResultTableView(nestedData)
        ) : (
          <div className="text-center text-[var(--color-on-surface-variant)] py-8">
            표시할 결과가 없습니다.
          </div>
        )}
      </div>

      {/* Footer Action Bar */}
      <div className="writing-footer fade-in" style={{ animationDelay: '0.2s' }}>
        <div className="flex-1"></div>
        <div className="footer-actions">
          <button
            onClick={handleRegenerateClick}
            disabled={isRegenerating || commentCount === 0}
            className="btn-primary"
            title={commentCount === 0 ? '수정 요청 내용을 입력해주세요' : ''}
          >
            {isRegenerating ? <RefreshCw className="w-5 h-5 animate-spin" /> : null}
            <span>반영하여 다시 만들기</span>
            {commentCount > 0 && !isRegenerating && (
              <span className="ml-1 px-2 py-0.5 text-xs rounded-full bg-white/20">{commentCount}</span>
            )}
          </button>
        </div>
      </div>

      <ScrollToTop />
    </>
  );
}
