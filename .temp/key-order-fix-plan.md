# 생성 기록 일지 키 순서 뒤죽박죽 문제 수정 계획

## 문제점

`LogGenerationResultView.tsx`에서 `updated_activities` **배열**을 `resultData` **객체**로 변환한 후 `Object.entries()`로 순회합니다.

```typescript
// 현재 코드 (문제)
currentResult.updated_activities.forEach((activity, index) => {
  const key = activity.target_id || `필드_${index + 1}`;
  resultData[key] = activity.updated_text || '';  // 객체로 변환
});
// ...
{Object.entries(resultData).map(([key, value]) => ...)}  // 순서 보장 안 됨
```

JavaScript 객체의 키 순서는:
- 정수 키: 오름차순 정렬
- 문자열 키: 삽입 순서 (대부분의 엔진)

`target_id`가 문자열이므로 삽입 순서를 따라야 하지만, `Object.entries()`는 엔진마다 다를 수 있어 순서가 뒤죽박죽이 됩니다.

## 해결 방법

`updated_activities` **배열을 그대로 사용**하여 순서를 유지합니다.

### 수정 범위

`/home/kj/Projects/Nuri-GPT/nuri-gpt-frontend/frontend/src/features/observation/components/LogGenerationResultView.tsx`

1. **데이터 구조 변경**: `resultData` 대신 `resultItems` 배열 사용
2. **렌더링 로직**: `Object.entries()` 대신 배열 `map()` 사용

### 수정 내용

```typescript
// 변경 후
interface ResultItem {
  id: string;
  value: string;
}

let resultItems: ResultItem[] = [];

if (currentResult.updated_activities && Array.isArray(currentResult.updated_activities) && currentResult.updated_activities.length > 0) {
  resultItems = currentResult.updated_activities.map((activity, index) => ({
    id: activity.target_id || `필드_${index + 1}`,
    value: activity.updated_text || '',
  }));
} else if (currentResult.template_mapping && Object.keys(currentResult.template_mapping).length > 0) {
  // template_mapping은 객체이므로 그대로 사용 (순서 중요도 낮음)
  resultItems = Object.entries(currentResult.template_mapping).map(([key, value]) => ({
    id: key,
    value: value as string,
  }));
} else if (currentResult.observation_content) {
  resultItems = [
    { id: '관찰 내용', value: currentResult.observation_content },
    { id: '평가 및 지원계획', value: currentResult.evaluation_content || '' },
    { id: '발달 영역', value: Array.isArray(currentResult.development_areas) ? currentResult.development_areas.join(', ') : (currentResult.development_areas || '') },
  ];
}

// 렌더링
{resultItems.map((item) => {
  if (!item.value) return null;
  // ... 기존 로직에서 key -> item.id, value -> item.value로 변경
})}
```

## 영향 범위

- `LogGenerationResultView.tsx` 내부 로직만 변경
- 외부 API 타입 변경 없음
- 재생성 기능에 영향 없음 (comments 키는 `target_id` 사용)

## 검증 방법

1. 생성 기록 페이지 진입
2. 일지 상세 보기에서 필드 순서가 `updated_activities` 배열 순서와 일치하는지 확인
