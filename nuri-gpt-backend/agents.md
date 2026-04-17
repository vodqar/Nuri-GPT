## 문서 목록

| 경로 | 설명 |
|------|------|
| `docs/OVERVIEW.md` | 프로젝트 목적·기술 스택·환경 설정·실행 방법 |
| `docs/ARCHITECTURE.md` | 계층 구조·모듈 의존성·데이터 흐름 다이어그램 |
| `docs/API_REFERENCE.md` | 전체 REST API 엔드포인트 목록 및 파라미터 정의 |
| `docs/DEVELOPMENT.md` | DI 구조·기능 추가 체크리스트·디버깅 가이드·테스트 구조 |
| `docs/DYNAMIC_UI_PLAN.md` | 템플릿 구조 JSON을 프론트엔드에서 동적으로 렌더링하는 방식 설계 |
| `docs/SECURITY.md` | 인증·인가 보안 정책 및 구현 가이드 |

---

## 개발 규칙

### 1. 의존성 및 검증 (Macro Guardrails)
- 버전 지정: `>=` 또는 `~=` 사용 (`==` 하드코딩 금지)
- 충돌 발생 시 `pip install <pkg>` 단독 설치로 우회 금지 → `requirements.txt`에서 근본 해소
- 코드 편집 후 턴 종료 전, 반드시 `python -m py_compile` 등으로 구문(Syntax) 무결성을 증명할 것.
- 외부 API 연동 시 과거 지식에 예측하여 짜지 말고, 문서를 살피고 `curl` 등으로 동작/타임아웃을 증명할 것.

### 2. 테스트 격리
- 모든 Service 모듈: `unittest.mock`으로 외부 인프라 없이 단위 테스트 가능해야 함
- 테스트/모듈 실행 시 명시적 가상환경 경로 사용 (예: `venv/bin/pytest`)

### 3. DB 스키마 관리 (Supabase)
- 스키마 변경(컬럼 추가·수정·삭제): Supabase MCP 도구로 직접 적용
- 컬럼 추가 후 PostgREST 캐시 즉시 갱신:
  ```sql
  notify pgrst, 'reload schema';
  ```

### 4. 프레임워크 스펙
- 구버전 학습 데이터 기반 코드 패턴 사용 금지
- 현재 환경(Python 3.11+, FastAPI 0.104+)의 최신 시그니처 및 타입 힌팅 적용

### 5. 계약 안정성
- 외부 서비스나 LLM 출력이 다른 계층의 렌더링/API 동작에 영향을 주면, 어느 계층이 안정된 계약을 보장할지 먼저 분명히 한다
- 반복해서 드러나는 구조적 제약은 handoff에만 두지 말고 관련 `docs/` 또는 `agents.md`에 반영한다

### 6. 완료 기준 (Definition of Done)

| 항목 | 기준 |
|------|------|
| 테스트 | `venv/bin/pytest -q` — 기존·신규 100% 통과 (Skipped 제외) |
| 패키지 | 추가 패키지가 `requirements.txt`에 올바른 문법으로 반영됨 |
| 문서 | 변경 사항은 문서 본문에 녹여내고, 최하단에는 **별도의 변경 이력(Change-log)을 추가하지 말고** 업데이트 날짜(`*Last Updated: YYYY-MM-DD*`)만 단일 줄로 갱신 |

> 문서가 업데이트되지 않았으면 작업 완료가 아닙니다.
> 문서 경로: `/home/mbk7990/workspace/Nuri-GPT/nuri-gpt-backend/docs`
