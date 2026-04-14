import { useState, useEffect, useRef } from 'react';
import { Plus, Trash2, Loader2 } from 'lucide-react';
import { showToast } from '../../../components/global/ToastContainer';
import { createTemplate } from '../../../services/api';
import type { TreeNode } from '../utils/templateStructureUtils';
import {
  createTreeNode,
  structureToTreeNodes,
  treeNodesToStructure,
} from '../utils/templateStructureUtils';

const DRAFT_STORAGE_KEY = 'nuri_template_draft_v2';

// 예시 초기 구조 (manual 트랙 진입 시 사전 입력)
function buildExampleTree(): TreeNode[] {
  const item1 = createTreeNode('놀이 내용');
  const item2 = createTreeNode('놀이 내용');
  const sub1 = { ...createTreeNode('실내 놀이'), children: [item1] };
  const sub2 = { ...createTreeNode('실외 놀이'), children: [item2] };
  const cat1 = { ...createTreeNode('놀이'), children: [sub1, sub2] };

  const sub3 = createTreeNode('식사');
  const sub4 = createTreeNode('수면');
  const cat2 = { ...createTreeNode('일상생활'), children: [sub3, sub4] };

  return [cat1, cat2];
}

interface TemplateStructureEditorProps {
  initialStructure?: Record<string, unknown>;
  initialTemplateName?: string;
  track: 'image' | 'manual';
  sourceImageFile?: File;
  onSuccess: () => void;
  onCancel: () => void;
}

export function TemplateStructureEditor({
  initialStructure,
  initialTemplateName = '',
  track,
  sourceImageFile,
  onSuccess,
  onCancel,
}: TemplateStructureEditorProps) {
  const [templateName, setTemplateName] = useState(initialTemplateName);
  const [tree, setTree] = useState<TreeNode[]>(() => {
    if (initialStructure && Object.keys(initialStructure).length > 0) {
      return structureToTreeNodes(initialStructure);
    }
    if (track === 'manual') {
      return buildExampleTree();
    }
    return [];
  });
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingLabel, setEditingLabel] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasDraftRestored, setHasDraftRestored] = useState(false);
  const editInputRef = useRef<HTMLInputElement>(null);

  // localStorage 드래프트 복원
  useEffect(() => {
    if (track !== 'manual' || hasDraftRestored) return;
    const draft = localStorage.getItem(DRAFT_STORAGE_KEY);
    if (draft) {
      try {
        const parsed = JSON.parse(draft) as { name: string; tree: TreeNode[] };
        if (parsed.tree?.length > 0) {
          const restore = window.confirm('이전에 편집하던 내용이 있습니다. 복원하시겠습니까?');
          if (restore) {
            setTree(parsed.tree);
            if (parsed.name) setTemplateName(parsed.name);
          } else {
            localStorage.removeItem(DRAFT_STORAGE_KEY);
          }
        }
      } catch {
        localStorage.removeItem(DRAFT_STORAGE_KEY);
      }
    }
    setHasDraftRestored(true);
  }, [track, hasDraftRestored]);

  // localStorage 디바운스 자동저장
  useEffect(() => {
    if (track !== 'manual') return;
    const timer = setTimeout(() => {
      if (tree.length > 0) {
        localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify({ name: templateName, tree }));
      }
    }, 800);
    return () => clearTimeout(timer);
  }, [tree, templateName, track]);

  // 편집 모드 진입 시 input focus
  useEffect(() => {
    if (editingId && editInputRef.current) {
      editInputRef.current.focus();
      editInputRef.current.select();
    }
  }, [editingId]);

  const startEdit = (nodeId: string, currentLabel: string) => {
    setEditingId(nodeId);
    setEditingLabel(currentLabel);
  };

  const commitEdit = () => {
    const trimmed = editingLabel.trim();
    if (!trimmed) {
      setEditingId(null);
      return;
    }
    setTree((prev) => updateNodeLabel(prev, editingId!, trimmed));
    setEditingId(null);
  };

  const cancelEdit = () => setEditingId(null);

  // 카테고리(대분류) 추가
  const addCategory = () => {
    const newNode = createTreeNode('');
    setTree((prev) => [...prev, newNode]);
    setEditingId(newNode.id);
    setEditingLabel('');
  };

  // 소분류 추가 (특정 카테고리 내)
  const addSubcategory = (categoryId: string) => {
    const newNode = createTreeNode('');
    setTree((prev) => addChildToNode(prev, categoryId, newNode));
    setEditingId(newNode.id);
    setEditingLabel('');
  };

  // 항목 추가 (특정 소분류 내)
  const addItem = (subcategoryId: string) => {
    const newNode = createTreeNode('');
    setTree((prev) => addChildToNode(prev, subcategoryId, newNode));
    setEditingId(newNode.id);
    setEditingLabel('');
  };

  // 노드 삭제
  const deleteNode = (nodeId: string) => {
    setTree((prev) => removeNode(prev, nodeId));
  };

  const handleSave = async () => {
    if (!templateName.trim()) {
      setError('템플릿 이름을 입력해주세요.');
      return;
    }
    const validTree = tree.filter((n) => n.label.trim());
    if (validTree.length === 0) {
      setError('카테고리를 1개 이상 추가해주세요.');
      return;
    }

    const structureJson = treeNodesToStructure(validTree);

    try {
      setIsSaving(true);
      setError(null);
      await createTemplate({
        templateName: templateName.trim(),
        structureJson,
        file: sourceImageFile,
      });
      localStorage.removeItem(DRAFT_STORAGE_KEY);
      showToast('템플릿 생성이 완료되었습니다', 'success');
      onSuccess();
    } catch (err) {
      console.error('Failed to create template:', err);
      setError('템플릿 저장에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleClearAll = () => {
    if (window.confirm('모든 항목을 지우고 처음부터 시작할까요?')) {
      setTree([]);
      localStorage.removeItem(DRAFT_STORAGE_KEY);
    }
  };

  return (
    <div className="space-y-6 animate-view-enter">
      {/* 트랙 1 안내 배너 */}
      {track === 'image' && (
        <div className="px-4 py-3 bg-[var(--color-primary)]/8 border border-[var(--color-primary)]/20 rounded-xl text-sm text-[var(--color-primary)] font-medium">
          AI가 분석한 결과입니다. 항목을 확인하고 필요하면 수정 후 저장해 주세요.
        </div>
      )}

      {/* 에러 */}
      {error && (
        <div className="p-4 bg-[var(--color-error-container)] text-[var(--color-on-error-container)] rounded-xl border border-[var(--color-error)]/20 text-sm font-medium">
          {error}
        </div>
      )}

      {/* 템플릿 이름 */}
      <div className="space-y-2">
        <label className="block text-sm font-bold text-[var(--color-primary)] tracking-wider">
          템플릿 이름
        </label>
        <input
          type="text"
          value={templateName}
          onChange={(e) => setTemplateName(e.target.value)}
          placeholder="예: 관찰일지"
          className="w-full px-5 py-4 rounded-2xl bg-[var(--color-surface-container-low)] text-[var(--color-on-surface)] border-none focus:ring-2 focus:ring-[var(--color-primary)]/50 transition-all placeholder:text-[var(--color-on-surface-variant)]/40"
        />
      </div>

      {/* 구조 편집 영역 */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <label className="block text-sm font-bold text-[var(--color-primary)] tracking-wider">
            항목 구조
          </label>
          <div className="flex items-center gap-3">
            <span className="text-xs text-[var(--color-on-surface-variant)]">
              대분류 → 소분류 → 항목 순서로 구성됩니다
            </span>
            {track === 'manual' && (
              <button
                type="button"
                onClick={handleClearAll}
                className="text-xs text-[var(--color-error)] hover:underline"
              >
                모두 지우기
              </button>
            )}
          </div>
        </div>

        {/* 표 형태 구조 편집 테이블 */}
        <div className="doc-table">
          {tree.map((category) => (
            <div key={category.id} className="doc-row">
              {/* 대분류 헤더 컬럼 */}
              <div className="doc-header-col">
                <EditableLabel
                  label={category.label}
                  isEditing={editingId === category.id}
                  editingValue={editingLabel}
                  placeholder="대분류"
                  onStartEdit={() => startEdit(category.id, category.label)}
                  onChange={setEditingLabel}
                  onCommit={commitEdit}
                  onCancel={cancelEdit}
                  onDelete={() => deleteNode(category.id)}
                />
              </div>

              {/* 소분류 및 항목 영역 */}
              <div className="flex flex-col flex-1">
                {category.children.map((sub, subIdx) => (
                  <div
                    key={sub.id}
                    className="flex"
                    style={subIdx === 0 ? undefined : { borderTop: '1px solid rgba(150, 160, 155, 0.25)' }}
                  >
                    {/* 소분류 헤더 컬럼 */}
                    <div className="doc-sub-header-col">
                      <EditableLabel
                        label={sub.label}
                        isEditing={editingId === sub.id}
                        editingValue={editingLabel}
                        placeholder="소분류"
                        onStartEdit={() => startEdit(sub.id, sub.label)}
                        onChange={setEditingLabel}
                        onCommit={commitEdit}
                        onCancel={cancelEdit}
                        onDelete={() => deleteNode(sub.id)}
                      />
                    </div>

                    {/* 항목 리스트 컬럼 */}
                    <div className="doc-content-col">
                      {sub.children.length > 0 ? (
                        <div className="flex flex-col">
                          {sub.children.map((item) => (
                            <div key={item.id} className="doc-edit-row">
                              <EditableLabel
                                label={item.label}
                                isEditing={editingId === item.id}
                                editingValue={editingLabel}
                                placeholder="항목"
                                onStartEdit={() => startEdit(item.id, item.label)}
                                onChange={setEditingLabel}
                                onCommit={commitEdit}
                                onCancel={cancelEdit}
                                onDelete={() => deleteNode(item.id)}
                              />
                            </div>
                          ))}
                        </div>
                      ) : null}

                      {/* 항목 추가 버튼 */}
                      <button
                        type="button"
                        onClick={() => addItem(sub.id)}
                        className="doc-add-item-btn"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        <span>항목 추가</span>
                      </button>
                    </div>
                  </div>
                ))}

                {/* 소분류 추가 버튼 */}
                <button
                  type="button"
                  onClick={() => addSubcategory(category.id)}
                  className="doc-add-item-btn"
                  style={{ margin: '0.5rem 0.75rem', justifyContent: 'center' }}
                >
                  <Plus className="w-4 h-4" />
                  <span>소분류 추가</span>
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* + 카테고리(대분류) 추가 버튼 */}
        <button type="button" onClick={addCategory} className="doc-add-category-btn">
          <Plus className="w-5 h-5" />
          <span>카테고리(대분류) 추가</span>
        </button>
      </div>

      {/* 푸터 버튼 */}
      <footer className="pt-4 border-t border-[var(--color-outline-variant)]/30 flex gap-3">
        <button
          type="button"
          onClick={onCancel}
          disabled={isSaving}
          className="flex-1 py-3.5 rounded-2xl text-[var(--color-on-surface-variant)] font-bold hover:bg-[var(--color-surface-container)] transition-all disabled:opacity-50"
        >
          취소
        </button>
        <button
          type="button"
          onClick={handleSave}
          disabled={isSaving}
          className="start-btn flex-[2] py-3.5 text-white font-bold rounded-2xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isSaving && <Loader2 className="w-5 h-5 animate-spin" />}
          <span>{isSaving ? '저장 중...' : '저장하기'}</span>
        </button>
      </footer>
    </div>
  );
}

// ─────────────────────────────────────────
// 인라인 라벨 편집 컴포넌트
// ─────────────────────────────────────────
interface EditableLabelProps {
  label: string;
  isEditing: boolean;
  editingValue: string;
  placeholder?: string;
  onStartEdit: () => void;
  onChange: (val: string) => void;
  onCommit: () => void;
  onCancel: () => void;
  onDelete: () => void;
}

function EditableLabel({
  label,
  isEditing,
  editingValue,
  placeholder = '항목',
  onStartEdit,
  onChange,
  onCommit,
  onCancel,
  onDelete,
}: EditableLabelProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  if (isEditing) {
    return (
      <div className="flex items-center w-full">
        <input
          ref={inputRef}
          type="text"
          value={editingValue}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') onCommit();
            if (e.key === 'Escape') onCancel();
          }}
          onBlur={onCommit}
          placeholder={placeholder}
          className="doc-edit-input"
        />
        <button
          type="button"
          onClick={onDelete}
          className="doc-delete-btn ml-2"
          title="삭제"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center w-full group">
      <button
        type="button"
        onClick={onStartEdit}
        className={`doc-edit-label flex-1 text-left ${!label ? 'doc-edit-label-empty' : ''}`}
      >
        {label || `${placeholder} 입력...`}
      </button>
      <div className="doc-edit-actions">
        <button
          type="button"
          onClick={onDelete}
          className="doc-delete-btn"
          title="삭제"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────
// 트리 조작 유틸리티 함수들
// ─────────────────────────────────────────

function updateNodeLabel(nodes: TreeNode[], targetId: string, newLabel: string): TreeNode[] {
  return nodes.map((node) => {
    if (node.id === targetId) {
      return { ...node, label: newLabel };
    }
    if (node.children.length > 0) {
      return { ...node, children: updateNodeLabel(node.children, targetId, newLabel) };
    }
    return node;
  });
}

function addChildToNode(nodes: TreeNode[], parentId: string, newChild: TreeNode): TreeNode[] {
  return nodes.map((node) => {
    if (node.id === parentId) {
      return { ...node, children: [...node.children, newChild] };
    }
    if (node.children.length > 0) {
      return { ...node, children: addChildToNode(node.children, parentId, newChild) };
    }
    return node;
  });
}

function removeNode(nodes: TreeNode[], targetId: string): TreeNode[] {
  return nodes
    .filter((node) => node.id !== targetId)
    .map((node) => ({
      ...node,
      children: removeNode(node.children, targetId),
    }));
}
