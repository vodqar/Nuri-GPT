# Frontend Overview

## 서비스 목적

보육교사가 AI 관찰일지 생성 기능을 직관적으로 사용할 수 있는 UI/UX 제공.

## 핵심 기능

| 기능 | 설명 |
|------|------|
| 템플릿 업로드 | 빈 템플릿 이미지 업로드 → AI 분석 구조 확인·승인 |
| 일지 생성 | 텍스트 입력 및 이미지 OCR(크롭·회전 지원) 후 AI 생성 결과 확인 |
| 편집 & 내보내기 | 생성된 일지 검토·수정 후 HWPX 다운로드 |
| 인증 | JWT 로그인/로그아웃, 세션 유지 (Zustand) |
| 이미지 편집 | 템플릿 등록 및 OCR 업로드 시 이미지 크롭·회전 유틸리티 제공 |

## 기술 스택

| 레이어 | 기술 | 용도 |
|--------|------|------|
| Framework | React 19 + Vite | UI 라이브러리, 고속 빌드 |
| Language | TypeScript | 정적 타입 |
| Styling | Tailwind CSS v4 | 유틸리티 클래스 반응형 UI |
| State | Zustand | 전역 상태 관리 |
| Form | React Hook Form + Zod | 폼 상태 & 스키마 검증 |
| Routing | React Router v6 | 클라이언트 사이드 라우팅 |
| Network | Axios | API 통신 |
| Mocking | MSW | 백엔드 없이 독립 개발 |

## 설치 및 실행

```bash
# 설치
cd nuri-gpt-frontend/frontend && npm install

# 개발 (Vite Dev Server + MSW)
npm run dev

# 빌드 / 프리뷰
npm run build
npm run preview
```

*마지막 업데이트: 2026-04-09 (이미지 크롭 및 편집 모듈 통합)*
