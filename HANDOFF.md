# Handoff Document — Manual Template Empty Result Bug Fix

*Last Updated: 2026-04-14*

---

## 🎯 Issue

사용자가 수동으로 생성한 템플릿을 활용하여 일지를 작성하고 생성하면 결과 화면이 비어있는 상태로 보이는 문제가 발생합니다. 생성 파이프라인 자체는 정상 작동하며 LLM 쿼리와 출력도 올바르게 생성됩니다.

---

## 🔍 Root Cause

### 데이터 흐름 분석

1. **템플릿 구조**: 사용자가 수동으로 생성한 템플릿은 중첩 구조
   ```json
   {
     "놀이": {
       "실내 놀이": {"놀이 내용": ""},
       "실외 놀이": {"놀이 내용": ""}
     }
   }
   ```

2. **태그 추출**: 백엔드 `generate.py`의 `get_leaf_paths()` 함수가 leaf 노드 경로를 추출
   - 태그: `["놀이.실내 놀이.놀이 내용", "놀이.실외 놀이.놀이 내용"]`

3. **LLM 응답**: Dify/LLM이 중첩된 JSON 반환
   ```json
   {
     "놀이.실내 놀이": {
       "놀이 내용": "...",
       "놀이 평가": "...",
       "놀이 지원": "..."
     },
     "놀이.실외 놀이": {...}
   }
   ```

4. **매칭 실패**: `generate_journal_content` (llm.py:786-789)에서 평면 키로 조회
   ```python
   for tag in tags:
       result[tag] = str(parsed_data.get(tag, ""))  # tag="놀이.실내 놀이.놀이 내용"
   ```
   - `parsed_data.get("놀이.실내 놀이.놀이 내용")` → `""` (해당 키가 존재하지 않음)
   - 모든 태그가 빈 문자열로 매핑 → 결과 화면 비어있음

---

## ✅ Solution

### 수정된 파일
- `nuri-gpt-backend/app/services/llm.py`

### 변경 사항

1. **`_flatten_dict` 헬퍼 추가** (line 234-244)
   ```python
   @staticmethod
   def _flatten_dict(data: Dict[str, Any], prefix: str = "") -> Dict[str, str]:
       """중첩된 dict를 점(.) 표기법 평면 dict로 변환합니다."""
       result: Dict[str, str] = {}
       for key, value in data.items():
           full_key = f"{prefix}.{key}" if prefix else key
           if isinstance(value, dict):
               result.update(LlmService._flatten_dict(value, full_key))
           else:
               result[full_key] = str(value) if value is not None else ""
       return result
   ```

2. **`generate_journal_content` 매핑 로직 수정** (line 799-805)
   ```python
   # Flatten nested LLM response to dot-notation keys for tag matching
   flat_data = self._flatten_dict(parsed_data)

   result = {}
   for tag in tags:
       result[tag] = flat_data.get(tag, str(parsed_data.get(tag, "")))
   return result
   ```

### 동작 원리
- LLM 응답 `{"놀이.실내 놀이": {"놀이 내용": "..."}}` → 플래튼 `{"놀이.실내 놀이.놀이 내용": "..."}`
- 태그 `"놀이.실내 놀이.놀이 내용"`이 올바르게 매칭

---

## 🧪 Verification

### 테스트 케이스
1. 수동 템플릿 생성: `{"놀이": {"실내 놀이": {"놀이 내용": ""}}}`
2. 관찰 메모 입력: "민준이가 오줌쌌다."
3. 일지 생성 요청
4. 결과 화면에 생성된 내용이 정상 표시되는지 확인

### 예상 결과
- `result["놀이.실내 놀이.놀이 내용"]`에 LLM이 생성한 텍스트가 포함
- 프론트엔드 `LogGenerationResultView`에서 내용이 정상 렌더링

---

## 📋 Related Files

- `nuri-gpt-backend/app/api/endpoints/generate.py` — 템플릿 기반 생성 엔드포인트
- `nuri-gpt-backend/app/services/llm.py` — LLM 서비스 (수정됨)
- `nuri-gpt-frontend/frontend/src/features/observation/components/LogGenerationResultView.tsx` — 결과 렌더링
- `nuri-gpt-frontend/frontend/src/features/observation/utils/templateStructureUtils.ts` — 템플릿 구조 유틸
