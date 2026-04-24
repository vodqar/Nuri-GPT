# 사용자 계정 생성 가이드

## 개요

개발/테스트 목적으로 새 사용자 계정을 직접 생성하는 방법입니다.

## 방법 1: Python 스크립트 사용 (권장)

백엔드 디렉토리에서 임시 스크립트를 작성하여 실행합니다.

```python
#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client, Client
from app.core.config import get_settings

async def create_user():
    settings = get_settings()
    supabase: Client = create_client(settings.supabase_url, settings.supabase_service_key)
    
    email = "user@example.com"
    password = "SecurePassword123!"
    name = "User Name"
    
    # Supabase Auth에 사용자 생성
    auth_response = supabase.auth.sign_up({
        "email": email,
        "password": password,
        "options": {"data": {"name": name}}
    })
    
    user_id = auth_response.user.id
    
    # public.users에 레코드 생성
    supabase.table('users').insert({
        'id': user_id,
        'email': email,
        'name': name,
        'subscription_plan': 'basic',
        'subscription_status': 'active',
        'role': 'user'
    }).execute()
    
    # 이메일 확인 완료 처리
    supabase.auth.admin.update_user_by_id(user_id, {'email_confirm': True})
    
    print(f"User created: {email}")

asyncio.run(create_user())
```

실행:
```bash
venv/bin/python create_user.py
```

## 방법 2: SQL 직접 실행

Supabase MCP 도구로 직접 SQL을 실행합니다.

```sql
-- 1. auth.users에 사용자 생성 (Supabase Auth)
-- 이 방법은 권장되지 않음. 대신 Python 스크립트 사용 권장

-- 2. public.users에 레코드 생성
INSERT INTO public.users (id, email, name, subscription_plan, subscription_status, role)
VALUES (
  '<user_id_from_auth>',
  'user@example.com',
  'User Name',
  'basic',
  'active',
  'user'
);

-- 3. 이메일 확인 완료 처리
UPDATE auth.users 
SET email_confirmed_at = now()
WHERE email = 'user@example.com';
```

## 주의사항

1. **이메일 확인**: Supabase Auth로 사용자 생성 시 `email_confirmed_at`이 null이면 로그인이 불가능합니다. 반드시 이메일 확인 처리가 필요합니다.
2. **public.users 레코드**: auth.users와 public.users 두 테이블 모두에 사용자가 있어야 로그인이 정상 작동합니다.
3. **서비스 키 사용**: 사용자 생성 시 `supabase_service_key`를 사용하여 관리자 권한으로 접근해야 합니다.
4. **임시 스크립트 삭제**: 사용 후 임시 스크립트는 보안상 삭제해야 합니다.

## 계정 등급

- `subscription_plan`: `basic`, `premium`, `enterprise`
- `subscription_status`: `trial`, `active`, `cancelled`, `expired`
- `role`: `user`, `org_manager`, `admin`
