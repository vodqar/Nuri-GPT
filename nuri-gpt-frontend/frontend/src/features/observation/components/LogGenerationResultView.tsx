import { useState, useEffect } from 'react';
import { Copy, Check, MessageSquarePlus, RefreshCw } from 'lucide-react';
import type { GenerateLogResponse } from '../../../types/api';
import { showToast } from '../../../components/global/ToastContainer';
import { ScrollToTop } from '../../../components/global/ScrollToTop';
import { PathBreadcrumb } from './PathBreadcrumb';

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

  // 추출 로직은 API 응답 형태에 따라 다름
  // 배열 순서를 유지하기 위해 객체 대신 배열 사용
  interface ResultItem {
    id: string;
    value: string;
  }

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

  let resultItems: ResultItem[] = [];

  if (currentResult.updated_activities && Array.isArray(currentResult.updated_activities) && currentResult.updated_activities.length > 0) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    resultItems = currentResult.updated_activities.map((activity: any, index: number) => ({
      id: activity.target_id || `필드_${index + 1}`,
      value: activity.updated_text || '',
    }));
  } else if (currentResult.template_mapping && Object.keys(currentResult.template_mapping).length > 0) {
    const mapping = currentResult.template_mapping;
    // semantic_json이 있으면 그 순서를 기준으로 정렬
    if (currentResult.semantic_json && Object.keys(currentResult.semantic_json).length > 0) {
      const keyOrder = getSemanticJsonKeyOrder(currentResult.semantic_json);
      const sortedEntries = keyOrder
        .filter(key => key in mapping)
        .map(key => ({ id: key, value: mapping[key] as string }));
      // semantic_json에 없는 키는 뒤에 추가
      const remainingEntries = Object.entries(mapping)
        .filter(([key]) => !keyOrder.includes(key))
        .map(([key, value]) => ({ id: key, value: value as string }));
      resultItems = [...sortedEntries, ...remainingEntries];
    } else {
      resultItems = Object.entries(mapping).map(([key, value]) => ({
        id: key,
        value: value as string,
      }));
    }
  } else if (currentResult.observation_content) {
    resultItems = [
      { id: '관찰 내용', value: currentResult.observation_content },
      { id: '평가 및 지원계획', value: currentResult.evaluation_content || '' },
      { id: '발달 영역', value: Array.isArray(currentResult.development_areas) ? currentResult.development_areas.join(', ') : (currentResult.development_areas || '') },
    ];
  }

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
      // 토스트는 부모에서 처리하거나, 상태 변경 후에 띄우는 것이 더 안정적임
    } catch (err) {
      console.error('Regenerate failed:', err);
    }
  };

  // 빈 문자열이나 공백만 있는 코멘트는 제외하고 카운트
  const commentCount = Object.values(comments).filter(text => text?.trim()).length;

  const getBreadcrumbPath = (key: string): string[] => {
    if (key.includes('.')) {
      return key.split('.');
    }
    if (key.includes('__')) {
      return key.split('__');
    }
    return [key];
  };

  const getResultCardClasses = (hasComment: boolean, isActive: boolean) => {
    const baseClasses = 'result-card';
    const commentClass = hasComment ? 'has-comment' : '';
    const activeClass = isActive ? 'active' : '';
    return [baseClasses, commentClass, activeClass].filter(Boolean).join(' ');
  };

  const getActionBtnClasses = (hasComment: boolean, isActive: boolean) => {
    const baseClasses = 'action-btn comment-trigger';
    const activeClass = hasComment || isActive ? 'active' : '';
    return [baseClasses, activeClass].filter(Boolean).join(' ');
  };

  return (
    <>
      {/* Version History & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8 fade-in" style={{ animationDelay: '0.1s' }}>
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
            {history.map((_, idx) => (
              <option key={idx} value={idx}>
                V{idx + 1} {idx === history.length - 1 ? '(최신)' : ''}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Results Container - Animated on version change */}
      <div
        key={currentIndex}
        className="results-scroll-area space-y-4 flex-1 animate-view-enter"
      >
        {resultItems.map((item) => {
          if (!item.value) return null;

          const hasComment = !!comments[item.id];
          const isActive = activeCommentId === item.id;
          const path = getBreadcrumbPath(item.id);

          return (
            <div
              key={item.id}
              className={getResultCardClasses(hasComment, isActive)}
              onClick={() => setActiveCommentId(isActive ? null : item.id)}
            >
              <div className="flex justify-between items-start mb-3">
                <div className="result-path-container">
                  <PathBreadcrumb path={path} visibleFromIndex={0} />
                </div>
                <div className="card-actions flex items-center gap-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setActiveCommentId(isActive ? null : item.id);
                    }}
                    className={getActionBtnClasses(hasComment, isActive)}
                    title="수정 요청"
                  >
                    <MessageSquarePlus className="w-4 h-4" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCopy(item.value, item.id);
                    }}
                    className="action-btn"
                    title="복사"
                  >
                    {copiedStates[item.id] ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div className="result-content">
                {item.value}
              </div>

              {/* Comment Section */}
              {isActive && (
                <div className="comment-section" onClick={(e) => e.stopPropagation()}>
                  <textarea
                    value={comments[item.id] || ''}
                    onChange={(e) => handleCommentChange(item.id, e.target.value)}
                    placeholder="수정 요청사항을 입력하세요..."
                    className="comment-input"
                    autoFocus
                  />
                </div>
              )}

              {/* Comment Badge */}
              {!isActive && hasComment && (
                <div className="comment-badge">
                  <MessageSquarePlus className="w-3.5 h-3.5 shrink-0" />
                  <span className="truncate">{comments[item.id]}</span>
                </div>
              )}
            </div>
          );
        })}
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
