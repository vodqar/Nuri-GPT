import { useState, useEffect, useRef, useCallback } from 'react';
import { Trash2, Loader2, History, RefreshCw } from 'lucide-react';
import { getJournals, getJournalGroupHistory, deleteJournalGroup } from '../../../services/api';
import type { JournalResponse, GenerateLogResponse } from '../../../types/api';
import { LogGenerationResultView } from './LogGenerationResultView';
import { ViewHeader } from './ViewHeader';
import { showToast } from '../../../components/global/ToastContainer';
import { useViewTransition } from '../hooks/useViewTransition';

const MAX_RETRIES = 3;
const RETRY_DELAYS = [1000, 2000, 4000]; // exponential backoff

export function JournalHistoryPage() {
  const { viewState, exitingView, transitionTo } = useViewTransition<'list' | 'detail'>('list');
  const [journals, setJournals] = useState<JournalResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [isFailed, setIsFailed] = useState(false);
  const retryCountRef = useRef(0);
  const [hasMore, setHasMore] = useState(true);
  const [offset, setOffset] = useState(0);
  const [selectedGroup, setSelectedGroup] = useState<JournalResponse[] | null>(null);
  const [groupHistory, setGroupHistory] = useState<GenerateLogResponse[]>([]);
  const [currentDetailIndex, setCurrentDetailIndex] = useState(0);
  const [deletingGroupId, setDeletingGroupId] = useState<string | null>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);
  const isFetchingRef = useRef(false);
  const limit = 20;

  const loadJournals = useCallback(async (currentOffset: number, isRetry = false) => {
    // 중복 호출 방지
    if (isFetchingRef.current) return;
    isFetchingRef.current = true;

    try {
      setLoading(true);
      setIsFailed(false);
      if (!isRetry) {
        retryCountRef.current = 0;
      }
      const response = await getJournals(limit, currentOffset);

      if (currentOffset === 0) {
        setJournals(response.items);
      } else {
        setJournals((prev) => [...prev, ...response.items]);
      }

      setHasMore(response.items.length === limit);
      setOffset(currentOffset + response.items.length);
    } catch (error) {
      console.error('Failed to load journals:', error);
      
      // 재시도 로직
      const currentRetry = isRetry ? retryCountRef.current : 0;
      if (currentRetry < MAX_RETRIES - 1) {
        const nextRetry = currentRetry + 1;
        retryCountRef.current = nextRetry;
        showToast(`일지 목록을 불러오는 중 오류가 발생했습니다. 재시도 중... (${nextRetry}/${MAX_RETRIES})`, 'info');
        
        // exponential backoff
        await new Promise(resolve => setTimeout(resolve, RETRY_DELAYS[currentRetry]));
        isFetchingRef.current = false;
        return loadJournals(currentOffset, true);
      }
      
      showToast('일지 목록을 불러오는 중 오류가 발생했습니다.', 'error');
      setIsFailed(true);
      setHasMore(false); // 무한 스크롤 중단
    } finally {
      setLoading(false);
      isFetchingRef.current = false;
    }
  }, [hasMore, limit]);

  const loadMoreJournals = useCallback(() => {
    if (!loading && !isFailed && hasMore) {
      loadJournals(offset);
    }
  }, [loading, isFailed, hasMore, offset, loadJournals]);

  // 무한 스크롤을 위한 ref
  const lastItemRef = useCallback((node: HTMLDivElement | null) => {
    if (loading || isFailed) return;
    if (observerRef.current) observerRef.current.disconnect();

    observerRef.current = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && hasMore) {
        loadMoreJournals();
      }
    });

    if (node) observerRef.current.observe(node);
  }, [loading, isFailed, hasMore, loadMoreJournals]);

  // 수동 재시도
  const handleRetry = () => {
    setIsFailed(false);
    retryCountRef.current = 0;
    loadJournals(0, false);
  };

  useEffect(() => {
    loadJournals(0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleDelete = async (e: React.MouseEvent, groupId: string) => {
    e.stopPropagation();
    if (!window.confirm('이 생성 기록을 삭제하시겠습니까?')) return;

    try {
      setDeletingGroupId(groupId);
      await deleteJournalGroup(groupId);
      setJournals((prev) => prev.filter((j) => j.group_id !== groupId));
      showToast('생성 기록이 삭제되었습니다.', 'success');
    } catch (error) {
      showToast('삭제 중 오류가 발생했습니다.', 'error');
      console.error('Failed to delete journal group:', error);
    } finally {
      setDeletingGroupId(null);
    }
  };

  const handleJournalClick = async (journal: JournalResponse) => {
    try {
      const history = await getJournalGroupHistory(journal.group_id);

      // GenerateLogResponse 형식으로 변환
      const mappedHistory: GenerateLogResponse[] = history.map((j) => ({
        log_id: j.id,
        updated_activities: j.updated_activities || [],
        template_mapping: j.template_mapping || {},
        semantic_json: j.semantic_json || {},
        status: 'success',
        message: '성공',
        observation_content: j.observation_content,
        evaluation_content: j.evaluation_content,
        development_areas: j.development_areas,
        version: j.version,
      }));

      setGroupHistory(mappedHistory);
      setSelectedGroup(history);
      setCurrentDetailIndex(0);
      transitionTo('detail');
    } catch (error) {
      showToast('히스토리를 불러오는 중 오류가 발생했습니다.', 'error');
      console.error('Failed to load journal group history:', error);
    }
  };

  const handleBackToList = () => {
    transitionTo('list');
    // 애니메이션이 완료된 후 데이터를 초기화하고 싶다면 timeout을 사용하거나 유지할 수 있음
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${month}/${day} ${hours}:${minutes}`;
  };

  const getFirstSentence = (journal: JournalResponse) => {
    // 1. observation_content 우선
    if (journal.observation_content) {
      const sentences = journal.observation_content.split(/[.!?]/).filter((s) => s.trim());
      if (sentences[0]?.trim()) return sentences[0].trim();
    }

    // 2. template_mapping에서 첫 유효 값 찾기
    if (journal.template_mapping) {
      for (const value of Object.values(journal.template_mapping)) {
        if (typeof value === 'string' && value.trim()) {
          const sentences = value.split(/[.!?]/).filter((s) => s.trim());
          if (sentences[0]?.trim()) return sentences[0].trim();
        }
      }
    }

    // 3. updated_activities에서 첫 유효 텍스트 찾기
    if (journal.updated_activities && journal.updated_activities.length > 0) {
      for (const activity of journal.updated_activities) {
        const text = activity.updated_text as string | undefined;
        if (text?.trim()) {
          const sentences = text.split(/[.!?]/).filter((s) => s.trim());
          if (sentences[0]?.trim()) return sentences[0].trim();
        }
      }
    }

    return '내용 없음';
  };

  return (
    <div className="p-4 sm:p-6 md:p-10 w-full max-w-4xl mx-auto">
      <div className="glass-panel rounded-[1.5rem] p-5 sm:p-8 shadow-sm border border-white/40 relative overflow-hidden min-h-[520px]">
        {/* Header - View specific */}
        {viewState === 'detail' && (
          <ViewHeader
            title={`${selectedGroup ? formatDate(selectedGroup[0].created_at) : ''} 생성 기록`}
            backIcon="arrowLeft"
            onBack={handleBackToList}
          />
        )}

        {viewState === 'list' && (
          <ViewHeader title="생성 기록" backIcon="none" />
        )}

        {/* Content - Animated */}
        <div className={exitingView ? 'animate-view-exit' : viewState === 'list' ? '' : 'animate-view-enter'}>
          {viewState === 'detail' && selectedGroup && groupHistory.length > 0 && (
            <LogGenerationResultView
              history={groupHistory}
              currentIndex={currentDetailIndex}
              onNavigateHistory={setCurrentDetailIndex}
              onRegenerate={async () => {}}
              isRegenerating={false}
            />
          )}

          {viewState === 'list' && (
            <>
              <div className="space-y-3">
                {journals.map((journal, index) => {
                  const isLastItem = index === journals.length - 1;
                  const isDeleting = deletingGroupId === journal.group_id;

                  return (
                    <div
                      key={journal.id}
                      ref={isLastItem ? lastItemRef : null}
                      onClick={() => handleJournalClick(journal)}
                      className="template-card rounded-xl p-4 cursor-pointer flex items-center gap-4 bg-[var(--color-surface-container-lowest)] hover:bg-[var(--color-surface-container-low)]"
                    >
                      {/* 카드 아이콘 */}
                      <div className="card-icon hidden sm:flex w-12 h-12 rounded-xl bg-[var(--color-surface-container)] items-center justify-center text-[var(--color-on-surface-variant)] flex-shrink-0">
                        <History className="w-6 h-6" />
                      </div>

                      {/* 일지 정보 */}
                      <div className="flex-1 min-w-0">
                        <h3 className="template-name font-semibold truncate text-[var(--color-on-surface)]">
                          {getFirstSentence(journal)}
                        </h3>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-sm text-[var(--color-on-surface-variant)]">
                            {formatDate(journal.created_at)}
                          </span>
                          <span className="text-xs px-2 py-0.5 rounded-full bg-[var(--color-surface-container-high)] text-[var(--color-on-surface-variant)]">
                            v{journal.version}
                          </span>
                        </div>
                      </div>

                      {/* 액션 버튼 */}
                      <div className="action-buttons flex items-center gap-2">
                        <button
                          onClick={(e) => handleDelete(e, journal.group_id)}
                          disabled={isDeleting}
                          className="action-btn delete-btn p-2 rounded-lg transition-all"
                          title="삭제"
                        >
                          {isDeleting ? (
                            <Loader2 className="w-5 h-5 animate-spin" />
                          ) : (
                            <Trash2 className="w-5 h-5" />
                          )}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>

              {loading && (
                <div className="flex justify-center py-8 animate-fade-in">
                  <Loader2 className="w-8 h-8 animate-spin text-[var(--color-primary)]" />
                </div>
              )}

              {/* 실패 상태 UI */}
              {isFailed && (
                <div className="flex flex-col items-center justify-center py-12 gap-4 animate-fade-in">
                  <div className="text-center">
                    <p className="text-[var(--color-on-surface)] font-semibold mb-2">
                      일지 목록을 불러올 수 없습니다
                    </p>
                    <p className="text-sm text-[var(--color-on-surface-variant)]">
                      네트워크 연결을 확인하고 다시 시도해주세요
                    </p>
                  </div>
                  <button
                    onClick={handleRetry}
                    className="flex items-center gap-2 px-4 py-2 bg-[var(--color-primary)] text-white rounded-lg hover:opacity-90 transition-opacity"
                  >
                    <RefreshCw className="w-4 h-4" />
                    다시 시도
                  </button>
                </div>
              )}

              {!loading && !isFailed && journals.length === 0 && (
                <div className="text-center py-12 text-[var(--color-on-surface-variant)] animate-fade-in">
                  생성된 일지가 없습니다.
                </div>
              )}

              {!hasMore && journals.length > 0 && (
                <div className="text-center py-8 text-[var(--color-on-surface-variant)] text-sm opacity-60 animate-fade-in">
                  모든 기록을 불러왔습니다.
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
