# 파이프라인 리디자인 계획서: 일지 작성 및 결과 화면

일지 작성 페이지(`log_generation`)와 결과 페이지(`log_result`)를 템플릿 선택 화면과 디자인 언어를 통일하여 재설계한다. 계층적 JSON 구조를 시각적으로 명확히 표현하고, 기존 기능(OCR 업로드, 코멘트 재생성, 히스토리 관리)을 모두 유지한다.

**⚠️ 구현 범위**: SPA 뷰만 제공. 불필요한 사이드바, 헤더, 네비게이션은 제외.

---

## 1. 디자인 언어 분석 (기준: template-selection-mockup.html)

### 1.1 색상 팔레트 (CSS Variables)
| 토큰 | HEX | 용도 |
|------|-----|------|
| `primary` | `#436834` | 주요 액션, 선택 상태 |
| `primary-dim` | `#375c29` | 그라디언트 끝 |
| `primary-container` | `#c3efad` | 성공/마일스톤 강조 |
| `surface` | `#f8faf8` | 기본 배경 |
| `surface-container-low` | `#f1f4f2` | 카드/섹션 배경 |
| `surface-container` | `#eaefec` | 중첩 사이드바 |
| `surface-container-lowest` | `#ffffff` | 플로팅 요소 (Glass) |
| `on-surface` | `#2d3432` | 기본 텍스트 |
| `on-surface-variant` | `#59615f` | 보조 레이블 |
| `outline-variant` | `#acb3b1` | Ghost Border (15% opacity) |

### 1.2 타이포그래피
- **Headline**: Manrope, `letter-spacing: -0.02em`, Bold
- **Body**: Inter, 기본 0.875rem
- **계층**: Display → Section → Field → Helper

### 1.3 레이아웃 규칙
- **No-Line**: 1px solid border 금지, 배경색 전환으로 구분
- **Glass Panel**: `backdrop-filter: blur(12px)`, 70% opacity
- **Corner Radius**: 메인 컨테이너 `rounded-3xl` (1.5rem)
- **Spacing**: 섹션 간 `spacing-6` (2rem), 카드 내부 `p-6`

---

## 2. 페이지 구조

### 2.1 일지 작성 페이지 (Observation Writing Page)

**파일**: `prototypes/observation-writing-mockup.html`

#### 레이아웃 구조
```
┌─────────────────────────────────────────────────────────┐
│  [뒤로가기]          Nuri GPT              [사용자]      │  ← Glass Header
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  📋 템플릿명: "일상생활 관찰일지"                  │   │  ← Template Badge
│  │  대상 연령: [0-5세 드롭다운]                      │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  🌳 계층적 폼 트리                                │   │  ← Dynamic Form
│  │                                                 │   │
│  │  ▼ 놀이 .......................... [섹션 Depth 1] │   │
│  │    ├─ ▼ 활동 .................... [섹션 Depth 2] │   │
│  │    │   └─ 내용 [Textarea + 📎 OCR]              │   │
│  │    └─ ▼ 실내놀이 ............... [섹션 Depth 2] │   │
│  │        ├─ 놀이상황 [Textarea + 📎 OCR]          │   │
│  │        └─ 놀이지원 [Textarea + 📎 OCR]          │   │
│  │                                                 │   │
│  │  ▼ 일상생활 ...................... [섹션 Depth 1] │   │
│  │    ├─ 간식 [Textarea + 📎 OCR]                  │   │
│  │    └─ 점심식사 [Textarea + 📎 OCR]              │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  📝 추가 지침 (선택사항)                          │   │
│  │  [Textarea: 전체적인 작성 방향을 입력하세요...]   │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│         [✨ 일지 생성하기]                               │  ← Primary CTA
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### 컴포넌트 스펙

**A. 페이지 헤더 (Glass Header)**
- 고정 위치, `glass-panel` 클래스 적용
- 좌: 뒤로가기 버튼 (원형, `surface-container-low` 배경)
- 중: "Nuri GPT" 로고/타이틀
- 우: 사용자 아바타/메뉴

**B. 템플릿 정보 카드**
- `surface-container-low` 배경, `rounded-2xl`
- 템플릿 아이콘 + 이름 표시 (읽기 전용)
- 연령 선택: 드롭다운 (0-5세), 필수 입력

**C. 계층적 폼 트리 (DynamicTemplateForm 리디자인)**

| Depth | 시각적 표현 | 인터랙션 |
|-------|------------|----------|
| 0 (Root) | 전체 컨테이너 `surface` 배경 | - |
| 1 (섹션) | `surface-container-low` 배경, 좌측 4px `primary` 보더 | 접기/펼치기 가능 |
| 2 (하위 섹션) | 들여쓰기 + `primary/20` 보더 | 부모와 연동 접힘 |
| 3+ (필드) | 추가 들여쓰기, Ghost border로 분리 | - |

**필드 입력 영역:**
- 레이블: `primary` 색상, `uppercase`, `tracking-wider`
- Textarea: `surface-container-low` 배경, `rounded-xl`, `min-h-[120px]`
- OCR 버튼: 필드 우측 상단, `secondary-container/30` 배경, `FileText` 아이콘
- Placeholder: 원본 템플릿 값 표시 `(예시: ${originalValue})`

**D. 추가 지침 영역**
- Collapsible 섹션 (기본 펼침)
- `surface-container-low` 배경
- Textarea: `min-h-[80px]`

**E. 생성 버튼 (Fixed Bottom CTA)**
- 화면 하단 고정, `glass-panel` 적용
- 버튼: `primary` → `primary-dim` 그라디언트
- 상태: 기본 → 로딩(스피너) → 완료
- 검증 실패 시: 빈 필드 목록 모달 (`EmptyFieldsModal` 재사용)

---

### 2.2 결과 페이지 (Log Result Page)

**파일**: `prototypes/log-result-mockup.html`

#### 레이아웃 구조
```
┌─────────────────────────────────────────────────────────┐
│  [뒤로가기]          생성 결과              [보내기 ▼] │  ← Glass Header
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  📊 버전 히스토리  [v1] [v2] [v3] [현재]        │   │  ← History Nav
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  📄 생성된 일지 내용                            │   │
│  │                                                 │   │
│  │  ┌─────────────────────────────────────────┐   │   │
│  │  │ 놀이 > 활동 > 내용                     │💬│📋│   │   │  ← Result Block
│  │  │                                         │   │   │
│  │  │ 종이의 질감을 탐색하고 접는 과정을...   │   │   │
│  │  └─────────────────────────────────────────┘   │   │
│  │                                  [📝 코멘트 1]   │   │  ← Comment Badge
│  │                                                 │   │
│  │  ┌─────────────────────────────────────────┐   │   │
│  │  │ 놀이 > 실내놀이 > 놀이상황              │💬│📋│   │   │
│  │  │                                         │   │   │
│  │  │ 다양한 크기의 블록을 활용하여...        │   │   │
│  │  └─────────────────────────────────────────┘   │   │
│  │                                                 │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│         [🔄 최종 수정본 받기]  (코멘트 있을 때만)         │  ← Floating Action
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### 컴포넌트 스펙

**A. 버전 히스토리 네비게이션**
- `surface-container-low` 배경, `rounded-full` 컨테이너
- 버튼: `v1`, `v2`, `v3`... 현재 버전은 `primary` 강조
- 슬라이드 애니메이션으로 버전 전환

**B. 결과 블록 카드**
- `surface` 배경, `rounded-2xl`, `border-outline/10`
- 헤더: 계층 경로 표시 (`놀이 > 활동 > 내용`)
- 액션: 코멘트 버튼(💬), 복사 버튼(📋)
- 본문: `on-surface` 텍스트, `leading-relaxed`

**상태 변화:**
| 상태 | 시각적 표현 |
|------|------------|
| 기본 | `border-outline/10` |
| 코멘트 있음 | `border-amber-400/50`, `bg-amber-50/10` |
| 활성(코멘트 편집중) | `ring-2 ring-primary` |

**C. 코멘트 오버레이 (인라인)**
- 카드 하단에 슬라이드 인 (`animate-in slide-in-from-top-2`)
- 아이콘: `MessageSquarePlus`, `amber-100` 배경
- 입력: `zinc-50` 배경 Textarea
- 액션: 삭제/확인 버튼

**D. 플로팅 액션 바 (FAB)**
- 하단 중앙 고정, `zinc-900` 배경, `rounded-full`
- 코멘트 카운트 배지 + "최종 수정본 받기" 버튼
- 애니메이션: `slide-in-from-bottom-10`

**E. 재생성 로딩 오버레이**
- 전체 결과 영역 블러 + 백드롭
- 중앙: 스피너 + "코멘트를 반영하여 재생성 중..."

---

## 3. JSON 계층 구조 시각화 전략

### 3.1 현재 구조 예시
```json
{
  "보육일지": {
    "놀이": {
      "활동": { "내용": "..." },
      "실내놀이": {
        "놀이상황": "...",
        "놀이지원": "..."
      }
    },
    "일상생활": {
      "간식": "...",
      "점심식사": "..."
    }
  }
}
```

### 3.2 UI 매핑
| JSON Depth | UI Depth | 배경 | 들여쓰기 | 보더 |
|------------|----------|------|----------|------|
| 0 | Root Container | `surface` | 0 | - |
| 1 | Section | `surface-container-low` | 0 | 좌측 4px `primary` |
| 2 | Sub-section | `surface-container-low/50` | 16px | 좌측 2px `primary/30` |
| 3 | Field | `surface-container-lowest` | 32px | Ghost border |

### 3.3 계층 인지 요소
1. **들여쓰기**: 각 Depth마다 16px 추가
2. **보더 강도**: 상위로 갈수록 보더 두께/색상 강조
3. **타이포그래피**: 상위 섹션은 Bold+크게, 하위는 Regular
4. **배경 톤**: 상위로 갈수록 더 어두운 `surface` 계열

---

## 4. 인터랙션 상세

### 4.1 일지 작성 페이지

**섹션 접기/펼치기:**
- 클릭: 섹션 헤더
- 애니메이션: `height` transition 200ms ease
- 아이콘: `ChevronDown` → `ChevronRight` 회전

**OCR 업로드:**
- 클릭: 필드 우측 "OCR 업로드" 버튼
- 파일 선택 후: 해당 textarea에 텍스트 append
- 로딩: 버튼에 `Loader2` 스피너

**검증 및 제출:**
1. "일지 생성하기" 클릭
2. 연령 미선택 시: 필드 강조 + 토스트
3. 빈 필드 있을 시: `EmptyFieldsModal` 표시
4. 모든 확인 완료: API 호출 → 결과 페이지 이동

### 4.2 결과 페이지

**버전 전환:**
- 클릭: 히스토리 버튼
- 애니메이션: fade + slight slide
- 현재 버전: `primary` 배경 강조

**코멘트 추가:**
1. 카드 클릭 또는 💬 버튼 클릭
2. 인라인 오버레이 슬라이드 인
3. 텍스트 입력
4. 확인: 오버레이 닫힘 + 코멘트 배지 표시
5. 삭제: 코멘트 제거

**재생성:**
1. 하나 이상 코멘트 작성 시 FAB 표시
2. "최종 수정본 받기" 클릭
3. 로딩 오버레이 표시
4. 새 버전 추가 → 자동 전환

---

## 5. 구현 체크리스트

### 5.1 목업 파일 작성
- [ ] `prototypes/observation-writing-mockup.html` - 정적 HTML+CSS
- [ ] `prototypes/log-result-mockup.html` - 정적 HTML+CSS

### 5.2 목업 검증
- [ ] 템플릿 선택 화면과 디자인 일관성 확인
- [ ] 모바일/데스크톱 반응형 테스트
- [ ] 계층 구조 가독성 확인

### 5.3 React 컴포넌트 구현
- [ ] `DynamicTemplateForm` 스타일 업데이트
- [ ] `LogGenerationResultView` 스타일 업데이트
- [ ] `ObservationPage` 레이아웃 조정

---

## 6. 파일 구조

```
prototypes/
├── template-selection-mockup.html    (기존 - 디자인 기준)
├── observation-writing-mockup.html   (신규 - 본 계획)
└── log-result-mockup.html              (신규 - 본 계획)
```

---

*계획 작성일: 2026-03-30*
*기준 디자인: template-selection-mockup.html (Ethereal Academic)*
*대상 기능: 일지 작성, 결과 표시, 코멘트 재생성, 히스토리 관리*
