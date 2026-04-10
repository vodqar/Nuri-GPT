# 1. 백엔드 폴더로 이동
cd ~/Projects/Nuri-GPT/nuri-gpt-backend
# 2. 가상환경 활성화
source venv/bin/activate
# 3. 백엔드 서버 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

## 5. Task Tracking (Notion Kanban Board)

**Update the Notion task tracker ONLY for substantive coding tasks or multi-step changes. DO NOT use this for simple questions, quick code lookups, or trivial one-line edits.**

- **Database URL:** `https://www.notion.so/b5b89b8b5a5d47a3941854c12deca507`
- **Data Source ID:** `4ebb1cda-d62f-4581-beab-69cd48db48fa`
- **Action Required (for substantive tasks only):**
  1. **Before starting work:** Use the `notion-create-pages` MCP tool to register the new task FIRST.
     - Set `parent` to `{"data_source_id": "4ebb1cda-d62f-4581-beab-69cd48db48fa"}`.
     - Fill out the properties:
       - `작업명` (title): Concise summary of the task.
       - `상태` (status): Set to `In progress`.
       - `비고` (text): Briefly explain what will be done.
  2. **When work is completed:** ONLY when the user explicitly indicates the task is finished (e.g., "완료", "done"), use the `notion-update-page` MCP tool to mark the task as complete.
     - Update the `상태` (status) property to `Done`.
     - Update the `비고` (text) property with a summary of what was actually changed, fixed, or created.
  - This ensures the user has a visual, up-to-date Trello-like board of major AI agent activities without cluttering it with trivial queries.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

@HANDOFF.md 마지막 작업 후 관찰일지 최종 생성에서 수정하고자 하는 곳 코멘트 달고 재생성 누르면 다음과 같은 에러로 재생성이 되지 않음

프론트엔드:
재생성 중 오류가 발생했습니다.

브라우저 콘솔:
Failed to load resource: the server responded with a status of 422 (Unprocessable Content)
ObservationPage.tsx:177 Regeneration failed: AxiosError: Request failed with status code 422
    at async regenerateLog (api.ts:104:20)
    at async handleRegenerate (ObservationPage.tsx:168:25)
The FetchEvent for "http://localhost:5173/observations" resulted in a network error response: the promise was rejected.
mockServiceWorker.js:238 
 Uncaught (in promise) TypeError: Failed to fetch
    at passthrough (mockServiceWorker.js:238:12)
    at getResponse (mockServiceWorker.js:275:14)
    at async handleRequest (mockServiceWorker.js:127:20)
passthrough	@	mockServiceWorker.js:238
getResponse	@	mockServiceWorker.js:275

네트워크 로그:
Request URL
http://127.0.0.1:8000/api/generate/regenerate
Request Method
POST
Status Code
422 Unprocessable Content (from service worker)
Referrer Policy
strict-origin-when-cross-origin