# Handoff Document — User Account Settings & Quota Management UI

*Last Updated: 2024-04-15*

---

## 🎯 Goal

사용자가 자신의 프로필을 관리하고, 서비스 이용량(할당량) 및 구독 정보를 시각적으로 확인할 수 있는 프리미엄 계정 설정 화면을 구현합니다. 향후 추가될 구독, 결제, 할당량 제한 기능을 위한 확장성 있는 UI 기반을 마련합니다.

---

## ✅ Current Progress

### 1. 신규 페이지 구현
- **[AccountPage.tsx](file:///home/mbk7990/workspace/Nuri-GPT/nuri-gpt-frontend/frontend/src/features/settings/pages/AccountPage.tsx)**: 
  - 카드 기반 레이아웃의 계정 설정 메인 화면.
  - 프로필 관리 섹션 (이름, 이메일, 역할 표시).
  - 구독 및 결제 세션 (현재 플랜, 갱신일, 결제 수단 플레이스홀더).
  - 이용 현황 및 할당량 섹션 (일간/주간 프로그레스 바 시각화).
  - 계정 삭제(Danger Zone) 섹션 추가.

### 2. 라우팅 및 내비게이션 연결
- **[App.tsx](file:///home/mbk7990/workspace/Nuri-GPT/nuri-gpt-frontend/frontend/src/App.tsx)**: `/settings/account` 경로 추가.
- **[SideNavBar.tsx](file:///home/mbk7990/workspace/Nuri-GPT/nuri-gpt-frontend/frontend/src/components/layout/SideNavBar.tsx)**: '설정 > 계정' 메뉴 클릭 시 해당 페이지로 연결되도록 수정.

### 3. 문서화 완료
- `OVERVIEW.md`, `ARCHITECTURE.md`, `DESIGN.md`, `DEVELOPMENT.md`, `README.md`, `SUMMARY.md`, `SERVER_GUIDE.md` 등 모든 관련 문서에 최신 변경 사항 반영 완료.

---

## 🔧 What Worked

1. **디자인 일관성**: 기존 `Material Symbols`와 `Tailwind v4` 테마 변수를 활용하여 기존 UI와 완벽하게 어우러지는 프리미엄 디자인 구현.
2. **반응형 최적화**: 데스크탑의 2열 그리드와 모바일의 1열 스택 레이아웃을 성공적으로 적용.
3. **Zustand 연동**: `authStore`에서 사용자 정보를 가져와 프로필 섹션에 동적으로 표시.

---

## ⚠️ Notes / Pending Logic

1. **할당량(Quota) 데이터**: 현재 표시되는 이용량(7/10 등)은 프론트엔드 모크 데이터입니다. 백엔드의 실제 사용량 추적 API가 구현되면 연동이 필요합니다.
2. **구독/결제 로직**: 현재는 UI 플레이스홀더만 존재하며, 실제 스트라이프(Stripe)나 포트원(PortOne) 등 결제 게이트웨이 연동이 수반되어야 합니다.
3. **할당량 초기화**: 일간/주간 할당량 초기화 안내 문구가 포함되어 있으나, 실제 백엔드 크론탭(Crontab) 등의 스케줄러 작업이 필요합니다.

---

## 📋 Next Steps

### 1. 백엔드 연동
- [ ] `GET /api/users/me/usage` 등 사용량 조회 API 설계 및 연동.
- [ ] 사용자 등급(Role)에 따른 할당량 차등 적용 로직 검증.

### 2. 구독 시스템 구축
- [ ] 결제 수단 등록/수정 모달 작업.
- [ ] 구독 플랜 업그레이드/다운그레이드 흐름 구현.

---

## 🏷️ Key Files Related

| 파일 | 역할 |
|------|------|
| `nuri-gpt-frontend/frontend/src/features/settings/pages/AccountPage.tsx` | **주요 신규 파일** - 계정 설정 화면 UI |
| `nuri-gpt-frontend/frontend/src/components/layout/SideNavBar.tsx` | 내비게이션 연결 |
| `nuri-gpt-frontend/frontend/src/App.tsx` | 라우트 등록 |
| `nuri-gpt-frontend/frontend/src/store/authStore.ts` | 사용자 상태 관리 참고 |

---
*Next agent should check the `AccountPage.tsx` component to understand the UI structure before implementing backend integration.*
