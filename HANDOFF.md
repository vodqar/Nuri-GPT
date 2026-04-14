# Handoff Document — Quota Management System Implementation

*Last Updated: 2026-04-15*

---

## 🎯 Goal

사용자별 AI 서비스(관찰일지 생성, 이미지 분석 등)의 사용량을 추적하고, 요금제별 할당량에 따라 사용을 제한하는 시스템을 구축했습니다. 관리자가 손쉽게 할당량을 조절할 수 있는 기반을 마련하고, 사용자에게는 투명한 사용 현황을 제공합니다.

---

## ✅ Progress Summary

### 1. 백엔드 시스템 구축
- **데이터베이스 (Supabase)**:
  - `plan_quotas`: 요금제별(Trial, Basic, Premium) 기능별 할당량 정의.
  - `user_usages`: 사용자별 성공(`success_count`) 및 실패(`fail_count`) 횟수 추적.
- **서비스 및 의존성**:
  - `UsageRepository`: DB 연동 CRUD.
  - `UsageService`: KST 기준 날짜 계산, 할당량 초과 확인, 사용량 증가 로직.
- **API 통합**:
  - `GET /api/users/me/usage`: 현재 사용자 사용량 정보 제공.
  - LLM 호출 API(`generate/log`, `generate/regenerate`, `upload/memo`, `upload/template`)에 Quota Check 및 Increment 로직 통합 완료.

### 2. 프론트엔드 연동
- **[AccountPage.tsx](file:///home/mbk7990/workspace/Nuri-GPT/nuri-gpt-frontend/frontend/src/features/settings/pages/AccountPage.tsx)**:
  - 백엔드 API로부터 실시간 할당량 데이터를 호출하여 프로그레스 바 렌더링.
  - 관찰일지 생성(Text)과 이미지 분석(Vision)을 구분하여 시각화.

### 3. 문서화 업데이트
- `API_REFERENCE.md`, `ARCHITECTURE.md`, `OVERVIEW.md`에 할당량 관련 명세 및 정책 반영 완료.

---

## 🔧 Policy Details

1. **미차감 정책 (Success-only)**: LLM 처리가 성공한 경우에만 사용량을 차감합니다. 실패 건은 수집되지만 사용자 할당량에는 영향이 없습니다.
2. **KST 00:00 리셋**: 모든 일일 할당량은 한국 표준시(KST) 자정을 기준으로 리셋됩니다.
3. **HTTP 429 응답**: 할당량 소진 시 `429 Too Many Requests`를 반환하며, 프론트엔드에서는 안내 메시지를 표시합니다.

---

## 📋 Next Steps

- **관리자 UI**: 현재는 Supabase 콘솔에서 `plan_quotas` 테이블을 직접 수정해야 합니다. 추후 관리자 대시보드에서 이를 조절하는 기능을 추가할 수 있습니다.
- **알림 기능**: 할당량이 80% 이상 소진되었을 때 시스템 알림을 보낼 수 있는 로직을 검토 중입니다.
- **주간 할당량 검증**: 현재 일일 할당량 위주로 동작하며, 주간 할당량은 DB에는 존재하나 실제 API 검증 로직에 추가 연동이 가능합니다.

---

## 🏷️ Key Files Related

| 파일 | 역할 |
|------|------|
| `backend/app/services/usage_service.py` | 핵심 할당량 로직 |
| `backend/app/db/repositories/usage_repository.py` | DB 액세스 레이어 |
| `backend/app/api/endpoints/user.py` | 사용량 조회 API |
| `frontend/src/features/settings/pages/AccountPage.tsx` | 사용량 시각화 UI |

---
*시스템이 정상적으로 구축되었으며, 모든 테스트 준비가 완료되었습니다.*
