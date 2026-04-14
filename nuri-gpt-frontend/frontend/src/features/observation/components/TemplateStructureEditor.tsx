import React, { useState, useEffect, useRef } from 'react';
import { Plus, Trash2, Check, X, Loader2, FolderOpen, ChevronRight, List } from 'lucide-react';
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

        {/* 카드 목록 컨테이너 */}
        <div className="relative space-y-4">
          {tree.map((category) => (
            <CategoryCard
              key={category.id}
              node={category}
              editingId={editingId}
              editingLabel={editingLabel}
              editInputRef={editingId?.startsWith(category.id) ? editInputRef : undefined}
              onEditStart={(id, label) => startEdit(id, label)}
              onEditChange={setEditingLabel}
              onEditCommit={commitEdit}
              onEditCancel={cancelEdit}
              onAddSubcategory={() => addSubcategory(category.id)}
              onAddItem={(subId) => addItem(subId)}
              onDelete={(id) => deleteNode(id)}
            />
          ))}

          {/* + 카테고리 추가 버튼 */}
          <button
            type="button"
            onClick={addCategory}
            className="w-full py-4 px-5 flex items-center justify-center gap-2 rounded-2xl border-2 border-dashed border-[var(--color-outline-variant)] hover:border-[var(--color-primary)]/50 hover:bg-[var(--color-surface-container-low)] transition-all text-[var(--color-on-surface-variant)] hover:text-[var(--color-primary)]"
          >
            <Plus className="w-5 h-5" />
            <span className="font-medium">카테고리 추가</span>
          </button>

        </div>
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
// 카테고리 카드 컴포넌트 (대분류)
// ─────────────────────────────────────────
interface CategoryCardProps {
  node: TreeNode;
  editingId: string | null;
  editingLabel: string;
  editInputRef?: React.RefObject<HTMLInputElement | null>;
  onEditStart: (id: string, label: string) => void;
  onEditChange: (val: string) => void;
  onEditCommit: () => void;
  onEditCancel: () => void;
  onAddSubcategory: () => void;
  onAddItem: (subcategoryId: string) => void;
  onDelete: (id: string) => void;
}

function CategoryCard({
  node,
  editingId,
  editingLabel,
  editInputRef,
  onEditStart,
  onEditChange,
  onEditCommit,
  onEditCancel,
  onAddSubcategory,
  onAddItem,
  onDelete,
}: CategoryCardProps) {
  const isEditing = editingId === node.id;

  return (
    <div className="w-full overflow-hidden rounded-2xl bg-[var(--color-surface-container)] border border-[var(--color-outline-variant)]/50">
      {/* 카드 헤더 (대분류 이름) */}
      <div className="px-4 py-3 bg-[var(--color-primary)]/5 border-b border-[var(--color-outline-variant)]/30 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-[var(--color-primary)]/15 flex items-center justify-center shrink-0">
          <FolderOpen className="w-4 h-4 text-[var(--color-primary)]" />
        </div>

        {isEditing ? (
          <input
            ref={editInputRef}
            type="text"
            value={editingLabel}
            onChange={(e) => onEditChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') onEditCommit();
              if (e.key === 'Escape') onEditCancel();
            }}
            onBlur={onEditCommit}
            placeholder="카테고리 이름"
            className="flex-1 px-3 py-1.5 text-sm font-bold rounded-lg bg-white border border-[var(--color-primary)]/30 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/30"
          />
        ) : (
          <button
            type="button"
            onClick={() => onEditStart(node.id, node.label)}
            className="flex-1 text-left font-bold text-[var(--color-on-surface)] hover:text-[var(--color-primary)] transition-colors truncate"
          >
            {node.label || <span className="text-[var(--color-on-surface-variant)]/50 italic">카테고리 이름</span>}
          </button>
        )}

        {isEditing ? (
          <div className="flex items-center gap-1 shrink-0">
            <button
              type="button"
              onClick={onEditCommit}
              className="p-1.5 rounded-lg text-[var(--color-primary)] hover:bg-[var(--color-primary)]/10"
            >
              <Check className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={onEditCancel}
              className="p-1.5 rounded-lg text-[var(--color-on-surface-variant)] hover:bg-[var(--color-surface-container-high)]"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => onDelete(node.id)}
            className="p-1.5 rounded-lg text-[var(--color-error)] hover:bg-[var(--color-error-container)] opacity-0 hover:opacity-100 focus:opacity-100 transition-opacity shrink-0"
            title="카테고리 삭제"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* 카드 본문 (소분류 목록) */}
      <div className="p-3 space-y-3">
        {node.children.map((sub) => (
          <SubcategoryCard
            key={sub.id}
            node={sub}
            editingId={editingId}
            editingLabel={editingLabel}
            onEditStart={onEditStart}
            onEditChange={onEditChange}
            onEditCommit={onEditCommit}
            onEditCancel={onEditCancel}
            onAddItem={() => onAddItem(sub.id)}
            onDelete={onDelete}
          />
        ))}

        {/* 소분류 추가 버튼 */}
        <button
          type="button"
          onClick={onAddSubcategory}
          className="w-full py-2.5 px-3 flex items-center gap-2 rounded-xl border border-dashed border-[var(--color-outline-variant)] hover:border-[var(--color-primary)]/40 hover:bg-[var(--color-primary)]/5 transition-all text-sm text-[var(--color-on-surface-variant)] hover:text-[var(--color-primary)]"
        >
          <Plus className="w-4 h-4" />
          <span>소분류 추가</span>
        </button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────
// 소분류 미니카드 컴포넌트
// ─────────────────────────────────────────
interface SubcategoryCardProps {
  node: TreeNode;
  editingId: string | null;
  editingLabel: string;
  onEditStart: (id: string, label: string) => void;
  onEditChange: (val: string) => void;
  onEditCommit: () => void;
  onEditCancel: () => void;
  onAddItem: () => void;
  onDelete: (id: string) => void;
}

function SubcategoryCard({
  node,
  editingId,
  editingLabel,
  onEditStart,
  onEditChange,
  onEditCommit,
  onEditCancel,
  onAddItem,
  onDelete,
}: SubcategoryCardProps) {
  const isEditing = editingId === node.id;

  return (
    <div className="w-full overflow-hidden rounded-xl bg-[var(--color-surface)] border border-[var(--color-outline-variant)]/30">
      {/* 소분류 헤더 */}
      <div className="px-3 py-2 border-b border-[var(--color-outline-variant)]/20 flex items-center gap-2">
        <ChevronRight className="w-4 h-4 text-[var(--color-on-surface-variant)]/50 shrink-0" />

        {isEditing ? (
          <input
            type="text"
            value={editingLabel}
            onChange={(e) => onEditChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') onEditCommit();
              if (e.key === 'Escape') onEditCancel();
            }}
            onBlur={onEditCommit}
            placeholder="소분류 이름"
            className="flex-1 px-2 py-1 text-sm rounded-md bg-[var(--color-surface-container-low)] border border-[var(--color-primary)]/30 focus:outline-none"
          />
        ) : (
          <button
            type="button"
            onClick={() => onEditStart(node.id, node.label)}
            className="flex-1 text-left text-sm font-medium text-[var(--color-on-surface)] hover:text-[var(--color-primary)] transition-colors truncate"
          >
            {node.label || <span className="text-[var(--color-on-surface-variant)]/50 italic">소분류 이름</span>}
          </button>
        )}

        {isEditing ? (
          <div className="flex items-center gap-0.5 shrink-0">
            <button
              type="button"
              onClick={onEditCommit}
              className="p-1 rounded text-[var(--color-primary)] hover:bg-[var(--color-primary)]/10"
            >
              <Check className="w-3.5 h-3.5" />
            </button>
            <button
              type="button"
              onClick={onEditCancel}
              className="p-1 rounded text-[var(--color-on-surface-variant)] hover:bg-[var(--color-surface-container-high)]"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => onDelete(node.id)}
            className="p-1 rounded text-[var(--color-error)] hover:bg-[var(--color-error-container)] opacity-0 hover:opacity-100 focus:opacity-100 transition-opacity shrink-0"
            title="소분류 삭제"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* 항목 목록 */}
      <div className="p-2 space-y-1">
        {node.children.map((item) => (
          <ItemRow
            key={item.id}
            node={item}
            isEditing={editingId === item.id}
            editingLabel={editingLabel}
            onEditStart={() => onEditStart(item.id, item.label)}
            onEditChange={onEditChange}
            onEditCommit={onEditCommit}
            onEditCancel={onEditCancel}
            onDelete={() => onDelete(item.id)}
          />
        ))}

        {/* 항목 추가 버튼 */}
        <button
          type="button"
          onClick={onAddItem}
          className="w-full py-2 px-2 flex items-center gap-2 rounded-lg hover:bg-[var(--color-surface-container-low)] transition-colors text-sm text-[var(--color-on-surface-variant)] hover:text-[var(--color-primary)]"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>항목 추가</span>
        </button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────
// 항목 라인 컴포넌트 (leaf)
// ─────────────────────────────────────────
interface ItemRowProps {
  node: TreeNode;
  isEditing: boolean;
  editingLabel: string;
  onEditStart: () => void;
  onEditChange: (val: string) => void;
  onEditCommit: () => void;
  onEditCancel: () => void;
  onDelete: () => void;
}

function ItemRow({
  node,
  isEditing,
  editingLabel,
  onEditStart,
  onEditChange,
  onEditCommit,
  onEditCancel,
  onDelete,
}: ItemRowProps) {
  return (
    <div className="flex items-center gap-2 py-1.5 px-2 rounded-lg hover:bg-[var(--color-surface-container-low)] group">
      <List className="w-3.5 h-3.5 text-[var(--color-on-surface-variant)]/40 shrink-0" />

      {isEditing ? (
        <input
          type="text"
          value={editingLabel}
          onChange={(e) => onEditChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') onEditCommit();
            if (e.key === 'Escape') onEditCancel();
          }}
          onBlur={onEditCommit}
          placeholder="항목 이름"
          className="flex-1 px-2 py-0.5 text-sm rounded bg-[var(--color-surface-container-low)] border border-[var(--color-primary)]/30 focus:outline-none"
        />
      ) : (
        <button
          type="button"
          onClick={onEditStart}
          className="flex-1 text-left text-sm text-[var(--color-on-surface)] hover:text-[var(--color-primary)] transition-colors truncate"
        >
          {node.label || <span className="text-[var(--color-on-surface-variant)]/50 italic">항목 이름</span>}
        </button>
      )}

      {isEditing ? (
        <div className="flex items-center gap-0.5 shrink-0">
          <button
            type="button"
            onClick={onEditCommit}
            className="p-0.5 rounded text-[var(--color-primary)] hover:bg-[var(--color-primary)]/10"
          >
            <Check className="w-3 h-3" />
          </button>
          <button
            type="button"
            onClick={onEditCancel}
            className="p-0.5 rounded text-[var(--color-on-surface-variant)] hover:bg-[var(--color-surface-container-high)]"
          >
            <X className="w-3 h-3" />
          </button>
        </div>
      ) : (
        <button
          type="button"
          onClick={onDelete}
          className="p-0.5 rounded text-[var(--color-error)] hover:bg-[var(--color-error-container)] opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity shrink-0"
          title="항목 삭제"
        >
          <Trash2 className="w-3 h-3" />
        </button>
      )}
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
