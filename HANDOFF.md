# Handoff Document — Nuri-GPT Frontend (Template Structure Editor)

*Last Updated: 2026-04-14*

---

## 🎯 Goal

템플릿 생성 화면(`TemplateStructureEditor`)을 기존 flat list 들여쓰기 방식에서 **카드 기반 중첩 UI**로 리디자인합니다. 교사가 "대분류 안에 소분류, 그 안에 항목"이 있다는 계층 구조를 직관적으로 파악하고 편집할 수 있어야 합니다.

---

## ✅ 완료된 작업

### 구현 완료

| 파일 | 내용 |
|------|------|
| `features/observation/components/TemplateStructureEditor.tsx` | 카드 UI 편집기 전면 재작성 |
| `features/observation/utils/templateStructureUtils.ts` | `TreeNode` 타입 및 변환 함수 추가 |
| `frontend/docs/GUARDRAILS.md` | 레이아웃 오버플로우 가드레일 문서 신규 생성 |
| `frontend/agents.md` | ToC·DoD 업데이트 |

### 카드 UI 구조

```
┌──────────────────────────────────┐  ← CategoryCard (대분류)
│ 📁 놀이                   [🗑] │    FolderOpen 아이콘 + 배경색 카드
│                                 │
│  ┌─ > 실내 놀이 ───────── [🗑] │  ← SubcategoryCard (소분류)
│  │    ≡ 놀이 내용    [🗑]     │  ← ItemRow (항목)
│  │    + 항목 추가             │
│  └──────────────────────────── │
│  + 소분류 추가                  │
└──────────────────────────────────┘
+ 카테고리 추가
```

### 데이터 모델

- **`TreeNode`**: `{ id: string, label: string, children: TreeNode[] }` — 카드 UI 전용
- **`structureToTreeNodes`**: 백엔드 `structure_json` → `TreeNode[]` 변환 (이미지 트랙 분석 결과 수신 시 사용)
- **`treeNodesToStructure`**: `TreeNode[]` → `structure_json` 변환 (저장 전 호출)
- **`FlatItem` / `flatToTree` / `treeToFlat`**: 기존 유틸 유지 (하위 호환)

### 주요 UX 동작

- **인라인 편집**: 이름 클릭 → input 전환 → Enter 저장 / ESC 취소
- **삭제**: 호버 시 🗑 버튼 표시
- **추가**: 3단계 별도 버튼 (카테고리 / 소분류 / 항목)
- **예시 오버레이**: 수동 트랙에서 tree가 비어 있을 때 반투명 예시 카드 표시 (`pointer-events-none`)
- **localStorage 자동저장**: 수동 트랙 전용, 500ms 디바운스, 키: `nuri_template_draft_v2`
- **저장**: `POST /templates/` 호출 (`createTemplate` API 함수), 이미지 트랙이면 파일 함께 전송

---

## ✅ 해결된 문제

### 1. 수동 템플릿 생성 후 결과 화면 비어있음 (2026-04-14 수정)
- **원인**: `generate_journal_content`에서 LLM이 중첩된 JSON(`{"놀이.실내 놀이": {"놀이 내용": "..."}}`)을 반환하지만, 코드가 `parsed_data.get("놀이.실내 놀이.놀이 내용")`로 평면 키를 조회하여 빈 문자열 반환
- **수정**: `_flatten_dict` 헬퍼 추가하여 중첩된 dict를 점(.) 표기법 평면 dict로 변환 후 태그 매칭
- **파일**: `nuri-gpt-backend/app/services/llm.py` (line 234-244, 799-805)

### 2. 카드 컴포넌트 너비 오버플로우 (2026-04-14 수정)
- **원인**: `SubcategoryCard`, `CategoryCard` 내 flex 자식에 `w-full` / `overflow-hidden` 미적용
- **수정**: 각 카드 컴포넌트 루트 `<div>`에 `w-full overflow-hidden` 추가

### 3. 예시 오버레이 컨테이너 오버플로우 (2026-04-14 수정)
- **원인**: `ExampleOverlay`의 콘텐츠(놀이+일상생활 카드)가 부모 컨테이너 높이를 초과하여 하단 버튼("취소"/"저장하기")과 겹침
- **수정**: 카드 목록 컨테이너(`relative space-y-4`)와 `ExampleOverlay` 루트 div 양쪽에 `overflow-hidden` 추가
- **참고**: `frontend/docs/GUARDRAILS.md` — UI Layout Overflow 섹션

---

## 📋 Next Steps

### 이후 작업 (기존 미완)
- [ ] 프론트엔드 로그인 페이지 연동
- [ ] 로그아웃 구현
- [ ] 프로덕션 HTTPS 쿠키 설정

---

## 🔗 관련 문서

- `nuri-gpt-frontend/frontend/docs/GUARDRAILS.md` — 레이아웃 오버플로우 가드레일
- `nuri-gpt-frontend/frontend/docs/DEVELOPMENT.md` — 변경이력 (2026-04-14 섹션)
- `nuri-gpt-frontend/agents.md` — DoD 체크리스트
