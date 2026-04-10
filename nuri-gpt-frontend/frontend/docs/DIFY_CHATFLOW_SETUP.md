# Dify Chatflow 설정 가이드

재생성(Regenerate) API를 위한 Dify Chatflow 설정 방법을 안내합니다.

---

## 개요

재생성 API는 기본 생성 API와 별도의 Chatflow를 사용하여, 코멘트 기반 부분 수정에 최적화된 응답을 생성합니다.

| API | 환경 변수 | 용도 |
|-----|----------|------|
| 기본 생성 | `DIFY_API_KEY` | 교사 메모 기반 보육일지 최초 생성 |
| 재생성 | `DIFY_REGENERATE_API_KEY` | 코멘트 기반 부분 수정 |

---

## 1. Chatflow 생성

### 옵션 A: 신규 Chatflow 생성 (권장)

1. Dify 대시보드에서 **새 Chatflow 생성**
2. 다음 System Prompt 입력:

```
당신은 유아 보육일지 작성 전문가입니다. 제공된 [원본 교사 메모], [현재 생성된 보육일지], 
그리고 교사가 남긴 [수정 코멘트]를 분석하세요.

1. 코멘트가 달린 target_id 항목은 코멘트의 요청에 맞게 텍스트를 수정하세요.
2. 코멘트가 없는 항목이라도, 수정된 다른 항목들로 인해 전체적인 맥락이나 평가 내용이 
   어색해진다면 이를 자연스럽게 재작성하세요.
3. 반드시 이전과 동일한 구조의 updated_activities JSON 형태로 전체 항목을 모두 반환해야 합니다.

입력 변수:
- original_semantic_json: 원본 템플릿 구조
- current_activities: 현재 생성된 활동 목록
- comments: 수정 요청 코멘트 목록 (target_id, comment 쌍)
```

3. 입력 변수 설정:
   - `original_semantic_json` (Object)
   - `current_activities` (Array)
   - `comments` (Array)

4. API Key 발급 후 `.env`에 설정

### 옵션 B: 기존 Chatflow 재사용

기존 생성용 Chatflow를 그대로 사용하려면 `DIFY_REGENERATE_API_KEY`를 설정하지 않으면 자동으로 기본 `DIFY_API_KEY`로 fallback됩니다.

**주의**: 기존 Chatflow는 코멘트 처리 로직이 없을 수 있어, 재생성 품질이 떨어질 수 있습니다.

---

## 2. 환경 변수 설정

### 백엔드 `.env`

```env
# 기본 생성용
DIFY_API_KEY=app-xxxxxxxxxxxxxx
DIFY_API_URL=https://your-dify-instance/v1

# 재생성용 (선택사항 - 미설정 시 DIFY_API_KEY 사용)
DIFY_REGENERATE_API_KEY=app-yyyyyyyyyyyyyy
DIFY_REGENERATE_API_URL=https://your-dify-instance/v1
```

### 설정 우선순위

1. `DIFY_REGENERATE_API_KEY`가 설정되어 있으면 재생성용 Chatflow 사용
2. 미설정 시 `DIFY_API_KEY`로 fallback

---

## 3. 응답 형식

재생성 Chatflow는 다음 JSON 형식으로 응답해야 합니다:

```json
{
  "updated_activities": [
    {
      "target_id": "activity_1",
      "updated_text": "수정된 활동 내용..."
    },
    {
      "target_id": "activity_2",
      "updated_text": "다른 활동 내용..."
    }
  ]
}
```

**필수 사항**:
- 모든 `target_id`가 응답에 포함되어야 함
- 누락된 항목은 백엔드에서 원본으로 자동 보존

---

## 4. 테스트 방법

```bash
curl -X POST http://localhost:8000/api/generate/regenerate \
  -H "Content-Type: application/json" \
  -d '{
    "original_semantic_json": {"activities": [...]},
    "current_activities": [{"target_id": "act_1", "updated_text": "원본 텍스트"}],
    "comments": [{"target_id": "act_1", "comment": "더 구체적으로 작성해주세요"}]
  }'
```

---

*Last Updated: 2026-03-27 (재생성 파이프라인 구현 완료)*
