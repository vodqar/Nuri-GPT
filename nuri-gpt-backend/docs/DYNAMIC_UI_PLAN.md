# 동적 템플릿 UI 렌더링

## 렌더링 전략 — Depth별 Tailwind 클래스

| Depth | 예시 | 제목 클래스 |
|-------|------|-------------|
| 1 (최상위) | "보육일지" | `text-2xl font-bold mb-6 text-blue-800 border-b-2 border-blue-500 pb-2` |
| 2 (대분류) | "놀이", "일상생활" | `text-xl font-semibold mt-8 mb-4 text-gray-800 bg-gray-50 p-4 rounded-lg border border-gray-200` |
| 3 (중분류) | "활동", "실내놀이" | `text-lg font-medium mt-6 mb-3 text-gray-700 ml-4 border-l-4 border-blue-300 pl-3` |
| 단말 노드 (label) | "내용", "놀이상황" | `block text-sm font-semibold text-gray-600 mb-1 ml-6` |
| 단말 노드 (textarea) | — | `w-full px-4 py-2 ml-6 mb-4 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 transition-colors bg-white` |

- **단말 노드 조건**: value가 빈 문자열(`""`) 등 원시 타입일 때 `<label> + <textarea>`로 렌더링

---

## 재귀 렌더링 — `renderDynamicForm`

JSON 트리를 순회하며 depth에 따라 섹션/입력 필드를 동적 생성합니다.
`textarea.dataset.path`에 경로 배열을 저장해 나중에 JSON 구조 복원에 사용합니다.

```javascript
function renderDynamicForm(data, path = []) {
    const container = document.createElement('div');
    container.className = "flex flex-col gap-2";

    for (const [key, value] of Object.entries(data)) {
        const currentPath = [...path, key];
        const depth = currentPath.length;

        if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
            const section = document.createElement('div');
            section.className = getSectionClass(depth);

            const title = document.createElement('div');
            title.className = getTitleClass(depth);
            title.textContent = key;

            section.appendChild(title);
            section.appendChild(renderDynamicForm(value, currentPath));
            container.appendChild(section);
        } else {
            const fieldWrapper = document.createElement('div');
            fieldWrapper.className = 'mt-2 mb-4';

            const label = document.createElement('label');
            label.className = getLabelClass(depth);
            label.textContent = key;

            const textarea = document.createElement('textarea');
            textarea.className = getTextareaClass(depth);
            textarea.rows = 3;
            textarea.dataset.path = JSON.stringify(currentPath); // 경로 보존
            textarea.value = value || "";
            textarea.placeholder = `${key} 내용을 입력하세요...`;

            fieldWrapper.appendChild(label);
            fieldWrapper.appendChild(textarea);
            container.appendChild(fieldWrapper);
        }
    }
    return container;
}
```

---

## 폼 데이터 수집 — `collectFormData`

DOM의 모든 `textarea`를 순회하며 저장된 경로 배열로 원본 JSON 구조를 복원합니다.

```javascript
function collectFormData(formContainer) {
    const result = {};
    formContainer.querySelectorAll('textarea').forEach(ta => {
        const path = JSON.parse(ta.dataset.path);
        let current = result;
        for (let i = 0; i < path.length - 1; i++) {
            if (!current[path[i]]) current[path[i]] = {};
            current = current[path[i]];
        }
        current[path[path.length - 1]] = ta.value.trim();
    });
    return result;
}
```

---

## 구현 단계

1. **완료** — 렌더링 계획 수립 (본 문서)
2. 계획 승인 확인
3. `poc/index.html`에 `renderDynamicForm` 및 CSS 클래스 함수 구현
4. `collectFormData` 연동
5. 예시 JSON 렌더링 → 입력 → JSON 복원 통합 테스트
```

***