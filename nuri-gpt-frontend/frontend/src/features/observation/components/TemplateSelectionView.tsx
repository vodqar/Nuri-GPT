import { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { FileText, Check, Trash2, GripVertical, Plus, RefreshCw } from 'lucide-react';
import Sortable from 'sortablejs';
import type { Template } from '../../../types/api';
import { Modal } from '../../../components/global/Modal';

import { getTemplateBadge } from '../utils/templateUtils';
import { badgeStyles } from '../utils/templateUtils';


interface TemplateSelectionViewProps {
  templates: Template[];
  selectedTemplateId: string;
  onSelectTemplate: (templateId: string) => void;
  onCreateNew: () => void;
  onStart: () => void;
  onTemplatesChange: (templates: Template[]) => void;
  onDeleteTemplate: (templateId: string) => Promise<void>;
  onUpdateTemplate: (templateId: string, data: { name?: string }) => Promise<void>;
  isManageMode: boolean;
  onManageModeChange: (isManageMode: boolean) => void;
  hasChanges: boolean;
  onHasChangesChange: (hasChanges: boolean) => void;
  isLoading?: boolean;
  isFailed?: boolean;
  onRetry?: () => void;
}

export function TemplateSelectionView({
  templates,
  selectedTemplateId,
  onSelectTemplate,
  onCreateNew,
  onStart,
  onTemplatesChange,
  onDeleteTemplate,
  onUpdateTemplate,
  isManageMode,
  onManageModeChange,
  hasChanges,
  onHasChangesChange,
  isLoading,
  isFailed,
  onRetry,
}: TemplateSelectionViewProps) {
  const { t } = useTranslation();
  const [showCancelModal, setShowCancelModal] = useState(false);
  const originalTemplatesRef = useRef<Template[] | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState('');
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

  // 템플릿 드래그 앤 드롭 정렬 처리
  function handleReorder(oldIndex: number, newIndex: number) {
    const newTemplates = [...templates];
    const [moved] = newTemplates.splice(oldIndex, 1);
    newTemplates.splice(newIndex, 0, moved);

    const reordered = newTemplates.map((t, idx) => ({
      ...t,
      sort_order: idx,
    }));

    onTemplatesChange(reordered);
    onHasChangesChange(true);
  }

  // SortableJS 연동
  useEffect(() => {
    if (!isManageMode || !listRef.current) return;

    const sortable = Sortable.create(listRef.current, {
      handle: '.drag-handle',
      animation: 300,
      ghostClass: 'sortable-ghost',
      dragClass: 'sortable-drag',
      onEnd: (evt) => {
        if (evt.oldIndex === evt.newIndex) return;
        handleReorder(evt.oldIndex!, evt.newIndex!);
      },
    });

    return () => sortable.destroy();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isManageMode]);

  // 관리 모드에서 변경사항 있을 때 페이지 이탈 방지
  useEffect(() => {
    if (!isManageMode || !hasChanges) return;

    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = '';
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [isManageMode, hasChanges]);


  const exitManageModeWithoutSaving = () => {
    if (originalTemplatesRef.current) {
      onTemplatesChange(originalTemplatesRef.current);
    }
    onManageModeChange(false);
    setEditingId(null);
    onHasChangesChange(false);
    originalTemplatesRef.current = null;
  };

  const startEditing = (template: Template) => {
    if (!isManageMode) return;
    setEditingId(template.id);
    setEditingName(template.name);
  };

  const saveNameEdit = async () => {
    if (editingId && editingName.trim()) {
      try {
        await onUpdateTemplate(editingId, { name: editingName.trim() });
        const updated = templates.map((t) =>
          t.id === editingId ? { ...t, name: editingName.trim() } : t
        );
        onTemplatesChange(updated);
        setEditingId(null);
        onHasChangesChange(true);
      } catch {
        window.dispatchEvent(new CustomEvent('toast', { detail: { message: '이름 수정 중 오류가 발생했습니다.', type: 'error' } }));
      }
    }
  };

  const handleDelete = (templateId: string) => {
    setDeleteTargetId(templateId);
    setShowDeleteModal(true);
  };

  const executeDelete = async () => {
    if (!deleteTargetId) return;
    try {
      await onDeleteTemplate(deleteTargetId);
      const filtered = templates.filter((t) => t.id !== deleteTargetId);
      onTemplatesChange(filtered);
      if (selectedTemplateId === deleteTargetId && filtered.length > 0) {
        onSelectTemplate(filtered[0].id);
      }
      setDeleteTargetId(null);
      setShowDeleteModal(false);
      onHasChangesChange(true);
    } catch {
      window.dispatchEvent(new CustomEvent('toast', { detail: { message: '삭제 중 오류가 발생했습니다.', type: 'error' } }));
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      saveNameEdit();
    } else if (e.key === 'Escape') {
      setEditingId(null);
    }
  };

  return (
    <div className="min-h-[440px] max-sm:min-h-0 flex flex-col relative">
      {isLoading && (
        <div className="absolute inset-0 z-10 bg-white/50 backdrop-blur-sm rounded-[1.5rem] flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {/* 실패 상태 UI */}
      {isFailed && (
        <div className="absolute inset-0 z-10 bg-white/80 backdrop-blur-sm rounded-[1.5rem] flex flex-col items-center justify-center gap-4">
          <div className="text-center">
            <p className="text-[var(--color-on-surface)] font-semibold mb-2">
              템플릿을 불러올 수 없습니다
            </p>
            <p className="text-sm text-[var(--color-on-surface-variant)]">
              네트워크 연결을 확인하고 다시 시도해주세요
            </p>
          </div>
          {onRetry && (
            <button
              onClick={onRetry}
              className="flex items-center gap-2 px-4 py-2 bg-[var(--color-primary)] text-white rounded-lg hover:opacity-90 transition-opacity"
            >
              <RefreshCw className="w-4 h-4" />
              다시 시도
            </button>
          )}
        </div>
      )}

      {/* 템플릿 리스트 */}
      <div
        ref={listRef}
        className={`template-scroll-area space-y-3 flex-1 ${isManageMode ? 'edit-mode-active' : ''}`}
      >
        {templates.length === 0 ? (
          <div className="text-center text-[var(--color-on-surface-variant)] py-12">
            {t('observation.noTemplates')}
            <br />
            <span className="text-[var(--color-primary)] font-medium">
              {t('observation.createTemplatePrompt')}
            </span>
          </div>
        ) : (
          templates.map((template) => {
            const badge = getTemplateBadge(template, templates, t);
            return (
              <div
                key={template.id}
                onClick={() => !isManageMode && onSelectTemplate(template.id)}
                className={`template-card rounded-xl p-4 cursor-pointer flex items-center gap-4 ${
                  selectedTemplateId === template.id && !isManageMode
                    ? 'selected'
                    : 'bg-[var(--color-surface-container-lowest)] hover:bg-[var(--color-surface-container-low)]'
                } ${isManageMode ? 'edit-mode-card' : ''}`}
              >
                {/* 드래그 핸들 (관리 모드에서만 표시) */}
                <div
                  className="drag-handle hidden-handle"
                  onClick={(e) => e.stopPropagation()}
                >
                  <GripVertical className="w-5 h-5" />
                </div>

                {/* 카드 아이콘 */}
                <div className="card-icon hidden sm:flex w-12 h-12 rounded-xl bg-[var(--color-surface-container)] items-center justify-center text-[var(--color-on-surface-variant)] flex-shrink-0">
                  <FileText className="w-6 h-6" />
                </div>

                {/* 템플릿 정보 */}
                <div className="flex-1 min-w-0">
                  {editingId === template.id ? (
                    <input
                      type="text"
                      value={editingName}
                      onChange={(e) => setEditingName(e.target.value)}
                      onBlur={saveNameEdit}
                      onKeyDown={handleKeyDown}
                      className="name-input"
                      autoFocus
                    />
                  ) : (
                    <h3
                      className={`template-name font-semibold truncate ${
                        isManageMode ? 'text-[var(--color-on-surface)]' : ''
                      }`}
                      onClick={(e) => {
                        if (isManageMode) {
                          e.stopPropagation();
                          startEditing(template);
                        }
                      }}
                    >
                      {template.name}
                    </h3>
                  )}
                  <p className="text-sm text-[var(--color-on-surface-variant)]">
                    {template.created_at
                      ? `생성일: ${new Date(template.created_at).toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' })}`
                      : ''}
                  </p>
                </div>

                {/* 배지 (일반 모드) */}
                {!isManageMode && badge && (
                  <span className={`card-badge px-3 py-1 rounded-full text-xs font-semibold ${badgeStyles[badge.type]}`}>
                    {badge.label}
                  </span>
                )}

                {/* 선택 인디케이터 (일반 모드) */}
                <div
                  className={`selection-indicator w-8 h-8 rounded-full bg-[var(--color-primary)] text-white flex items-center justify-center flex-shrink-0 ${
                    selectedTemplateId === template.id ? 'opacity-100' : ''
                  }`}
                >
                  <Check className="w-5 h-5" />
                </div>

                {/* 액션 버튼 (관리 모드) */}
                <div className="action-buttons hidden-handle flex items-center gap-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(template.id);
                    }}
                    className="action-btn delete-btn"
                    title="삭제"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* 새 템플릿 버튼 (일반 모드) */}
      <button
        onClick={onCreateNew}
        className={`new-template-btn w-full mt-6 p-6 rounded-xl border-2 border-dashed border-[var(--color-outline-variant)] text-[var(--color-on-surface-variant)] font-semibold hover:border-[var(--color-primary)] hover:text-[var(--color-primary)] transition-all flex items-center justify-center gap-2 ${
          isManageMode ? 'opacity-0 invisible max-h-0 pt-0 pb-0 mt-0 pointer-events-none' : ''
        }`}
      >
        <Plus className="w-5 h-5" />
        {t('observation.newTemplate')}
      </button>

      {/* 하단 액션 버튼 (일반 모드) */}
      <footer
        className={`mt-8 pt-6 border-t border-[var(--color-outline-variant)]/30 transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] ${
          isManageMode ? 'opacity-0 invisible max-h-0 mt-0 mb-0 pt-0 pb-0 pointer-events-none' : 'max-h-[200px]'
        }`}
      >
        <button
          onClick={onStart}
          disabled={!selectedTemplateId || templates.length === 0}
          className="start-btn w-full py-4 text-white font-bold rounded-2xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {t('observation.templateStart')}
        </button>
      </footer>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        title={t('observation.deleteTemplateTitle')}
        description={t('observation.deleteTemplateConfirm')}
        primaryAction={{
          label: t('observation.delete'),
          onClick: executeDelete,
          variant: 'danger',
        }}
        secondaryAction={{
          label: t('observation.cancel'),
          onClick: () => setShowDeleteModal(false),
        }}
      />

      {/* Cancel Manage Mode Confirmation Modal */}
      <Modal
        isOpen={showCancelModal}
        onClose={() => setShowCancelModal(false)}
        title="변경사항이 저장되지 않습니다"
        description="관리 모드를 종료하면 변경사항이 사라집니다. 계속하시겠습니까?"
        primaryAction={{
          label: '종료',
          onClick: () => {
            setShowCancelModal(false);
            exitManageModeWithoutSaving();
          },
          variant: 'danger',
        }}
        secondaryAction={{
          label: t('observation.cancel'),
          onClick: () => setShowCancelModal(false),
        }}
      />
    </div>
  );
}
