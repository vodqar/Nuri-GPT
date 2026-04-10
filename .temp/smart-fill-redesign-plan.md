# 스마트 채우기 메뉴 디자인 개선 계획

## 1. 문제점 분석

### 현재 디자인 (`ObservationPage.tsx` 533-551행, `index.css` 1254-1374행)

```tsx
<div className={cn("ai-toggle-card", isAggressiveMode && "active")}>
  <div className="ai-toggle-info">
    <div className="ai-toggle-icon">
      <Sparkles className="w-4 h-4" />
    </div>
    <div className="ai-toggle-text">
      <h4>스마트 채우기</h4>
      <p>빈 칸 자동 완성</p>
    </div>
  </div>
  <label className="ai-switch">...</label>
</div>
```

### 디자인 시스템과의 불일치

| 문제 | 현재 상태 | 디자인 시스템 원칙 |
|------|----------|-------------------|
| 카드 형태 | 별도 배경 + 테두리 + border-radius | No-Line 규칙: 테두리 금지, 배경색 전환으로 구분 |
| 아이콘 스타일 | 32px 원형 배경 + 별도 강조 | 심플한 인라인 아이콘 |
| 활성화 효과 | 그라디언트 + 박스 쉐도우 | 레이어링 우선, shadow 최소화 |
| 시각적 무게 | 카드로 인해 과도하게 강조됨 | 주변 UI와 조화 |

### 구체적 CSS 문제

```css
/* 현재 - 과도하게 튀는 디자인 */
.ai-toggle-card {
  background: var(--color-surface-container-lowest);
  border: 1px solid rgba(67, 104, 52, 0.1);  /* ← 테두리 사용 */
  border-radius: 1rem;                        /* ← 카드 형태 */
  padding: 0.75rem 1rem;
}

.ai-toggle-card.active {
  background: linear-gradient(135deg, ...);   /* ← 그라디언트 */
  border-color: rgba(67, 104, 52, 0.3);
  box-shadow: 0 4px 12px rgba(67, 104, 52, 0.05); /* ← 쉐도우 */
}

.ai-toggle-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;                         /* ← 원형 배경 */
  background: var(--color-surface-container);
}
```

---

## 2. 개선 방향

### 목표
- 디자인 시스템의 "No-Line" 규칙 준수
- 주변 UI (mode-toggle, 버튼들)와 시각적 조화
- 기능은 유지하되 시각적 무게 감소

### 제안 디자인

**Before:**
```
┌─────────────────────────────────┐
│ ✨ 스마트 채우기          [토글] │  ← 카드 형태, 테두리
│    빈 칸 자동 완성               │
└─────────────────────────────────┘
```

**After:**
```
스마트 채우기 ✨  [토글]              ← 인라인, 배경 없음
```

### 변경 사항

1. **카드 제거**: 별도 배경/테두리 없이 인라인 요소로 변경
2. **아이콘 단순화**: 원형 배경 제거, 텍스트 옆에 작은 아이콘만 배치
3. **활성화 표시**: 그라디언트/쉐도우 대신 텍스트 색상 변화만 사용
4. **레이아웃**: `mode-toggle`과 같은 행에 자연스럽게 배치

---

## 3. 구체적 변경 계획

### 3.1 TSX 변경 (`ObservationPage.tsx`)

```tsx
// Before
<div className={cn("ai-toggle-card", isAggressiveMode && "active")}>
  <div className="ai-toggle-info">
    <div className="ai-toggle-icon">
      <Sparkles className="w-4 h-4" />
    </div>
    <div className="ai-toggle-text">
      <h4>스마트 채우기</h4>
      <p>빈 칸 자동 완성</p>
    </div>
  </div>
  <label className="ai-switch">...</label>
</div>

// After
<div className="smart-fill-toggle">
  <label className="smart-fill-label">
    <span className={cn("smart-fill-text", isAggressiveMode && "active")}>
      스마트 채우기
    </span>
    <Sparkles className={cn("smart-fill-icon", isAggressiveMode && "active")} />
  </label>
  <label className="smart-fill-switch">
    <input type="checkbox" checked={isAggressiveMode} onChange={...} />
    <span className="smart-fill-slider"></span>
  </label>
</div>
```

### 3.2 CSS 변경 (`index.css`)

```css
/* 기존 ai-toggle-card 관련 스타일 삭제 */

/* 새로운 심플한 스타일 */
.smart-fill-toggle {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0;
}

.smart-fill-label {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  cursor: pointer;
}

.smart-fill-text {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-on-surface-variant);
  transition: color 0.2s ease;
}

.smart-fill-text.active {
  color: var(--color-primary);
  font-weight: 600;
}

.smart-fill-icon {
  width: 1rem;
  height: 1rem;
  color: var(--color-on-surface-variant);
  transition: color 0.2s ease;
}

.smart-fill-icon.active {
  color: var(--color-primary);
}

/* 스위치는 기존 스타일 유지하되 클래스명만 변경 */
.smart-fill-switch { /* 기존 ai-switch와 동일 */ }
.smart-fill-slider { /* 기존 ai-slider와 동일 */ }
```

### 3.3 하단 힌트 변경 (693-696행)

```tsx
// Before
<div className={cn("ai-active-hint", isAggressiveMode && "visible")}>
  <Sparkles className="w-4 h-4 animate-pulse text-[var(--color-primary)]" />
  <span>AI 공동 작성 모드가 활성화되어 있습니다</span>
</div>

// After (더 심플하게)
{isAggressiveMode && (
  <div className="smart-fill-hint">
    <Sparkles className="w-3.5 h-3.5" />
    <span>자동 완성 활성화</span>
  </div>
)}
```

---

## 4. 영향 범위

- `ObservationPage.tsx`: 533-551행, 693-696행
- `index.css`: 1254-1374행 (기존 스타일 삭제, 새 스타일 추가)

---

## 5. 승인 요청

위 계획대로 진행해도 될까요?

- [ ] TSX 변경 승인
- [ ] CSS 변경 승인
