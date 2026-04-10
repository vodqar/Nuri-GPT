---
description: 개발 서버 시작 (백엔드 + 프론트엔드)
---

# 개발 서버 시작

Nuri-GPT 개발 서버(백엔드 + 프론트엔드)를 시작하는 절차입니다.

## 절차

1. **실행 중인 서비스 확인**
   ```bash
   ps aux | grep -E "(uvicorn|vite)" | grep -v grep
   ```

2. **실행 중인 서비스 중지** (필요 시)
   ```bash
   make stop
   ```

3. **서버 시작**
   ```bash
   make dev
   ```
   - 백엔드(8001) + 프론트엔드(5173) 동시 시작
   - Ctrl+C로 동시 종료

## 개별 실행 (필요 시)

- 백엔드만:
  ```bash
  make backend
  ```
- 프론트엔드만:
  ```bash
  make frontend
  ```
- 수동 실행:
  ```bash
  # 백엔드
  cd /home/kj/Projects/Nuri-GPT/nuri-gpt-backend
  ./venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

  # 프론트엔드
  cd /home/kj/Projects/Nuri-GPT/nuri-gpt-frontend/frontend
  npm run dev
  ```

## 참고

- 기본 포트: 백엔드 8001, 프론트엔드 5173 (Makefile 참조)
