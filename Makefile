# Nuri-GPT 개발 서버 시작 스크립트
# Usage: make dev | make backend | make frontend

.PHONY: dev backend frontend stop install-deps

# 기본 포트 설정
BACKEND_PORT=8001
FRONTEND_PORT=5173

# 의존성 설치 (초기 실행 시 자동 호출)
install-deps:
	@if [ ! -d "nuri-gpt-backend/venv" ]; then \
		echo "📦 Creating Python virtual environment..."; \
		cd nuri-gpt-backend && python3 -m venv venv && ./venv/bin/pip install -r requirements.txt; \
	fi
	@if [ ! -d "nuri-gpt-frontend/frontend/node_modules" ]; then \
		echo "📦 Installing npm dependencies..."; \
		cd nuri-gpt-frontend/frontend && npm install; \
	fi

# 포트 불일치 자동 수정
check-ports:
	@echo "🔍 Checking port configurations..."
	@grep -q "PORT=8001" nuri-gpt-backend/.env && echo "✓ Backend port: 8001" || echo "⚠ Check backend .env PORT setting"
	@grep -q "target: 'http://127.0.0.1:8001'" nuri-gpt-frontend/frontend/vite.config.ts && echo "✓ Frontend proxy: 8001" || (echo "⚠ Fixing frontend proxy config..." && $(MAKE) fix-proxy)

# 프론트엔드 프록시 설정 자동 수정 (8000 → 8001)
fix-proxy:
	@sed -i "s|target: 'http://127.0.0.1:8000'|target: 'http://127.0.0.1:8001'|g" nuri-gpt-frontend/frontend/vite.config.ts
	@echo "✓ Fixed vite.config.ts proxy to port 8001"

# 백엔드 + 프론트엔드 동시 시작 (추천)
dev: install-deps check-ports
	@bash dev.sh

# 백엔드만 시작
backend:
	@echo "🚀 Starting backend server on port $(BACKEND_PORT)..."
	@cd nuri-gpt-backend && ./venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port $(BACKEND_PORT)

# 프론트엔드만 시작
frontend: install-deps
	@echo "🚀 Starting frontend dev server on port $(FRONTEND_PORT)..."
	@cd nuri-gpt-frontend/frontend && npm run dev

# 실행 중인 서버 종료
stop:
	@echo "🛑 Stopping servers..."
	@pkill -f "uvicorn.*main:app" 2>/dev/null || true
	@fuser -k $(FRONTEND_PORT)/tcp 2>/dev/null || true
	@pkill -f "node_modules/.bin/vite" 2>/dev/null || true
	@echo "✓ Servers stopped"
