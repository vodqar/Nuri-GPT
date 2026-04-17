# 서버 실행 가이드

## 서버 실행

### 통합 실행 (Makefile) - 추천

루트 디렉토리(`Nuri-GPT/`)에서 한 번에 백엔드와 프론트엔드를 실행:

```bash
# 백엔드 + 프론트엔드 동시 시작 (Ctrl+C로 둘 다 종료)
make dev

# 개별 실행
make backend   # 백엔드만 (8001번 포트)
make frontend  # 프론트엔드만 (5173번 포트)
make stop      # 실행 중인 서버 모두 종료
```

> **참고**: `make dev`는 자동으로 포트 설정을 확인하고, 필요시 프록시 설정을 수정합니다.

### 백엔드 (FastAPI)

```bash
# 위치: nuri-gpt-backend/
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

| 엔드포인트 | URL |
|-----------|-----|
| Swagger | http://localhost:8000/docs |
| 헬스체크 | http://localhost:8000/health |

### 프론트엔드 (Vite/React)

```bash
# 위치: nuri-gpt-frontend/frontend/
npm run dev
```

접속: http://localhost:5173 (포트 충돌 시 5174 등으로 자동 변경될 수 있음)

## 포트 설정 주의

> [!IMPORTANT]
> 프론트엔드 `.env`는 **8000**번, 백엔드 `.env` 기본값은 **8001**번. 백엔드 실행 시 `--port 8000` 옵션 필수 또는 백엔드 `.env`의 `PORT=8000`으로 수정.

- **CORS**: 백엔드 `CORS_ORIGINS`에 현재 프론트 Origin(`http://localhost:5173` 또는 `http://localhost:5174`) 포함 여부 확인

## 트러블슈팅

| 오류 | 조치 |
|------|------|
| Makefile 명령 실패 | `make fix-proxy`로 vite.config.ts 프록시 포트 자동 수정 |
| `ERR_CONNECTION_REFUSED` | 서버 실행 여부 확인. VS Code Remote 환경이면 [Ports] 탭에서 `8000`, `5173`(또는 실제 Vite 포트) Forwarded 상태 확인 |
| `No 'Access-Control-Allow-Origin' header` | 백엔드 `CORS_ORIGINS`에 현재 프론트 Origin(`localhost:5173/5174`)이 포함되었는지 확인 후 서버 재시작 |
| `404 Not Found` | 모든 API 경로는 `/api` 접두사 필요 (예: `/api/generate/log`) |
| `net::ERR_FAILED` / `Failed to fetch` (MSW) | MSW 핸들러 경로와 실제 API 호출 경로 불일치 확인. 특히 `/templates` vs `/templates/` (슬래시 유무) 일치 여부 체크 |
| MSW가 요청을 가로챔 | `src/mocks/handlers.ts`의 핸들러 경로가 `api.ts`의 요청 경로와 **정확히** 일치하는지 확인 |

## 로그인 상태 확인 (인증)

현재 `PrivateRoute.tsx`는 실제 `authStore`의 `isAuthenticated` 상태를 기반으로 인증 여부를 확인합니다.

- **위치**: `src/routes/PrivateRoute.tsx` 
- **로직**: 미인증 시 `/login`으로 리디렉션하며, 새로고침 시 `refreshAccessToken`을 통해 세션 복원을 시도합니다.

*Last Updated: 2026-04-15*
