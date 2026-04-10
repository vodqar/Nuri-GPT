# 사이드바 메뉴 리디자인 계획

## 현재 문제점

1. **주 메뉴 선택 효과**: `border-r-4 border-green-800` 사용 → 메뉴가 오른쪽으로 밀리는 시각적 효과
2. **하위 메뉴 선택 효과**: `border-l-2` 기반 → 비대칭적이고 과도한 시각적 강조

## 참고 디자인: TemplateSelectionView

일지 생성 뷰의 템플릿 카드 디자인 언어:

```
- rounded-xl (12px 둥근 모서리)
- bg-[var(--color-surface-container-lowest)] (기본 배경)
- hover:bg-[var(--color-surface-container-low)] (호버)
- 선택 시: .selected 클래스 (primary 기반 배경/테두리)
- 아이콘: w-12 h-12 rounded-xl bg-[var(--color-surface-container)]
- 선택 인디케이터: 둥근 체크 아이콘 (opacity 전환)
```

## 새 디자인 방향

### 주 메뉴 (카테고리)

| 상태 | 스타일 |
|------|--------|
| 기본 | `rounded-xl bg-transparent text-zinc-600` |
| 호버 | `hover:bg-[var(--color-surface-container-low)]` |
| 선택 | `bg-[var(--color-primary)]/10 text-[var(--color-primary)] font-semibold` |
| 아이콘 | `w-10 h-10 rounded-xl bg-[var(--color-surface-container)]` (선택 시 primary 배경) |

- **제거**: `border-r-4` (밀리는 효과 제거)
- **대체**: subtle한 배경색 전환 + 아이콘 컨테이너 강조

### 하위 메뉴

| 상태 | 스타일 |
|------|--------|
| 기본 | `rounded-lg text-zinc-500` |
| 호버 | `hover:text-[var(--color-primary)] hover:bg-[var(--color-surface-container-low)]` |
| 선택 | `bg-[var(--color-primary)]/10 text-[var(--color-primary)] font-medium rounded-lg` |

- **제거**: `border-l-2` 기반 비대칭 강조
- **대체**: 좌우 대칭 pill-shaped 배경 강조

### 레이아웃 조정

1. **간격**: `space-y-2` → `space-y-1` (더 촘촘하게)
2. **패딩**: 일관된 `p-3` 또는 `px-4 py-3`
3. **들여쓰기**: 하위 메뉴 `pl-12` 유지하되 시각적 균형 맞춤

## 구현 범위

- 파일: `nuri-gpt-frontend/frontend/src/components/layout/SideNavBar.tsx`
- 변경 대상:
  - 주 메뉴 버튼 스타일 (lines 138-163)
  - 하위 메뉴 링크 스타일 (lines 186-198)
  - 전체 nav spacing (line 109)

## 예상 결과

- 사이드바가 일지 생성 뷰의 "glass-panel" 스타일과 시각적 통일성 확보
- 선택 상태가 더 세련되고 덜 "밀리는" 느낌
- Material Design 3 Surface 계층 체계 준수

---
*작성일: 2026-04-05*
