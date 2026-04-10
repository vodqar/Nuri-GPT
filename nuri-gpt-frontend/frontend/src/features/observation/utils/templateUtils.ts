import type { Template } from '../../../types/api';

// 템플릿의 모든 텍스트 입력 단말 노드의 경로(키)를 추출합니다
export function getTemplateLeafKeys(data: Record<string, unknown>, currentPath: string = ''): string[] {
  let keys: string[] = [];
  
  if (typeof data === 'object' && data !== null && !Array.isArray(data)) {
    for (const [key, value] of Object.entries(data)) {
      const newPath = currentPath ? `${currentPath}.${key}` : key;
      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        keys = [...keys, ...getTemplateLeafKeys(value as Record<string, unknown>, newPath)];
      } else {
        keys.push(newPath);
      }
    }
  }
  
  return keys;
}

export const RECENT_DAYS = 7; // 7일 이내 = 최근

export type BadgeType = { type: 'recently_used' | 'recently_created' | 'default'; label: string } | null;

export const getTemplateBadge = (template: Template, allTemplates: Template[], t: (key: string) => string): BadgeType => {
  const now = new Date();
  const recentThreshold = new Date(now.getTime() - RECENT_DAYS * 24 * 60 * 60 * 1000);

  // 1. 최근 사용 체크 (우선순위 1)
  if (template.last_used_at) {
    const mostRecentUsed = allTemplates
      .filter(t => t.last_used_at)
      .sort((a, b) => new Date(b.last_used_at!).getTime() - new Date(a.last_used_at!).getTime())[0];

    if (mostRecentUsed?.id === template.id) {
      return { type: 'recently_used', label: t('observation.recentlyUsedBadge') };
    }
  }

  // 2. 최근 생성 체크 (우선순위 2)
  if (template.created_at) {
    const createdAt = new Date(template.created_at);
    if (createdAt >= recentThreshold) {
      return { type: 'recently_created', label: t('observation.recentlyCreatedBadge') };
    }
  }

  // 3. 기본값 뱃지
  if (template.is_default) {
    return { type: 'default', label: t('observation.defaultBadge') };
  }

  return null;
};

export const badgeStyles = {
  recently_used: 'bg-[#e8f5e0] text-[#436834] border border-[#c3efad]',
  recently_created: 'bg-[#e8f4fc] text-[#0060ad] border border-[#b8d9f5]',
  default: 'bg-[var(--color-surface-container)] text-[var(--color-on-surface-variant)]',
};
