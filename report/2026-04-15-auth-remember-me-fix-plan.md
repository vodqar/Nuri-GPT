## Problem

`로그인 유지` 체크박스를 선택해도 새로고침/서버 재시작 시 로그인이 풀리는 것으로 체감된다.
현재 구현에서 체크박스 값(`remember`)은 실제 인증 세션 지속 정책에 반영되지 않고 이메일 기억(localStorage)에만 사용된다.

## Context

- 프론트는 `access_token`을 메모리(Zustand)에만 저장한다.
- 새로고침 복원은 `/api/auth/refresh` + `refresh_token` 쿠키에 의존한다.
- 백엔드는 로그인 시 항상 `refresh_token`을 7일 persistent cookie로 발급한다.
- 따라서 `remember` 값과 백엔드 쿠키 정책이 분리되어 UX/동작 불일치가 발생한다.

## Scope

- 백엔드 로그인/리프레시/로그아웃 쿠키 정책에 `remember`를 반영한다.
- 프론트 로그인 폼 훅에서 `remember`를 실제 로그인 유지 옵션으로만 다루도록 정리한다.
- 관련 테스트를 수정/추가해 회귀를 방지한다.
- 관련 문서(API/개발 가이드)를 업데이트한다.

## Non-Goals

- 인증 아키텍처 전면 개편(JWT 저장 위치 변경, OAuth 도입 등)
- UI 대규모 변경(체크박스 추가/분리 등)
- Supabase 설정 자체 변경

## Proposed Change

1. 백엔드 `LoginRequest`에 `remember: bool` 필드를 추가한다.
2. 로그인 시 `remember=true`면 기존처럼 persistent cookie(`max_age=7d`)를 발급하고, `remember=false`면 session cookie로 발급한다.
3. 리프레시 회전 시에도 동일 정책을 유지하기 위해 `remember_me` 보조 쿠키를 같이 관리한다.
4. 프론트 `useLoginForm`에서 이메일 기억(localStorage) 로직을 제거하고 `remember` 값만 로그인 API에 전달한다.
5. 백엔드/프론트 테스트를 보강한다.

## Verification

- Backend: `venv/bin/pytest -q` (최소 auth 관련 테스트 포함)
- Frontend: `npm run test -- PrivateRoute` 또는 auth 관련 대상 테스트, 필요 시 `npm run lint`
- Manual:
  1) `remember=true` 로그인 → 새로고침 후 복원 성공
  2) `remember=false` 로그인 → 브라우저 완전 종료 후 재접속 시 재로그인 필요

## Approval

사용자 요청("내용바탕으로 수정 진행해")으로 구현 진행 승인됨.
