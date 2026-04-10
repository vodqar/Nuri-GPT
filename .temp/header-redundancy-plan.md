# 관찰일지 페이지 헤더 중복 문제 - 해결 계획

## 문제 요약

ObservationPage.tsx에서 **상단 페이지 헤더**와 **메인 컨테이너 헤더**에 유사한 제목이 중복 표시됨:

| 위치 | 태그 | 스타일 | 내용 |
|------|------|--------|------|
| 페이지 상단 | `<h1>` | `text-3xl font-extrabold` | "관찰일지 작성" |
| 메인 컨테이너 | `<h2>` | `text-3xl font-extrabold` | 템플릿명 (예: "보육일지") |

## 해결 옵션

### 옵션 A: 상단 헤더 제거 (추천)
- **변경**: 페이지 상단 `<header>` 영역의 `<h1>` 및 `<p>` 제거
- **효과**: 메인 컨테이너가 유일한 헤더가 됨, 깔끔한 UI
- **영향**: i18n 키 `observation.title` 사용 중단 가능성

### 옵션 B: 상단 헤더 역할 축소
- **변경**: `<h1>` → 작은 브레드크럼브 스타일로 변경 (예: "보육일지 > 작성")
- **스타일**: `text-sm text-[var(--color-on-surface-variant)]` 등으로 다운그레이드
- **효과**: 위치 표시 역할만 유지, 메인 헤더 강조

### 옵션 C: 메인 컨테이너 헤더 제목 변경
- **변경**: 메인 헤더의 `<h2>` 텍스트를 "{템플릿명} 작성" 또는 단순 "작성"으로 변경
- **효과**: "보육일지 작성" → "보육일지" 대신 "보육일지 템플릿으로 작성" 등 구체화
- **단점**: 템플릿명이 길어질 수 있음

### 옵션 D: 상태별 헤더 분기
- **변경**: viewState('template_selection'|'template_creation'|'log_generation'|'log_result')별로 상단 헤더 내용 동적 변경
- **효과**: template_selection에서는 "관찰일지 작성", log_generation에서는 숨김/축소
- **복잡도**: 중간

## 추천안: 옵션 A (상단 헤더 제거)

**근거:**
1. 메인 컨테이너 헤더가 이미 뒤로가기 버튼 + 템플릿명 + 토글들을 포함해 정보가 충분함
2. 상단 헤더의 `sessionLabel`은 현재 `invisible` 클래스로 숨겨져 있어 실제 기능 없음
3. glass-panel 내부 헤더가 자연스러운 시각적 계층을 제공함

**구현 변경:**
```tsx
// 제거 대상 (461-471라인)
<header className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
  <div>
    <h1 className="text-3xl font-extrabold text-[var(--color-on-surface)] tracking-tight font-headline">
      {t('observation.title')}
    </h1>
    <p className="text-[var(--color-on-surface-variant)] flex items-center gap-2 mt-1 invisible">
      <Clock className="w-4 h-4" />
      {t('observation.sessionLabel')}
    </p>
  </div>
</header>

// 단순히 <header> 블록을 제거하고 mb-8 여백도 함께 정리
```

## 검증 기준
- [ ] 상단 중복 헤더 제거 후 메인 컨테이너 헤더만 표시됨
- [ ] 뷰 전환 시에도 헤더 구조 일관성 유지
- [ ] 모바일/데스크톱 반응형 문제 없음
