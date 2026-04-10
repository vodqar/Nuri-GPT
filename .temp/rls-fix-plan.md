# RLS 위반 문제 해결 계획

## 문제점
- **오류**: `new row violates row-level security policy`
- **발생 위치**: 템플릿 생성 시 Storage 업로드 (`storage_service.upload_template`)
- **원인**: 현재 백엔드는 `SUPABASE_KEY`(anon key)를 사용하여 Supabase 클라이언트를 생성하지만, Storage bucket의 RLS 정책이 anon 사용자의 업로드를 차단함

## 해결 방법
1. **StorageService에 service_role 클라이언트 추가**
   - `app/db/connection.py`에 `get_supabase_admin_client()` 함수 추가
   - `SUPABASE_SERVICE_KEY`를 사용하여 관리자 권한 클라이언트 생성

2. **StorageService 수정**
   - `StorageService`에 service_role 클라이언트를 사용하는 속성 추가
   - Storage 업로드/삭제 등 관리 작업에서는 service_role 클라이언트 사용
   - 다운로드/조회 등 읽기 작업은 기존 anon 클라이언트 유지

## 수정 파일
- `app/db/connection.py`: service_role 클라이언트 생성 함수 추가
- `app/services/storage.py`: StorageService에 admin 클라이언트 속성 추가 및 업로드 메서드 수정

## 검증 방법
- 템플릿 생성 테스트 수행
- Storage 업로드 성공 확인
