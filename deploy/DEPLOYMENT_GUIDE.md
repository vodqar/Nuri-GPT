# Nuri-GPT 라이브 배포 가이드 (복붙 전용)

이 문서는 복사-붙여넣기만으로 배포할 수 있도록 모든 경로와 명령어를 완전히展開한 가이드입니다.

---

## 사전 확인 사항

다음 항목이 이미 준비되어 있어야 합니다:

- [ ] Cloudflare DNS: `nuri-gpt.vodqar.com` A 레코드 → 집 공인IP (또는 `*.vodqar.com` 와일드카드)
- [ ] 공유기/라우터: 외부 443 포트 → 로컬 머신 443 포트 포워딩
- [ ] Supabase 프로젝트의 `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_KEY`, `SUPABASE_JWT_SECRET` 준비
- [ ] Gemini API 키 준비
- [ ] Dify API 키 준비

---

## Step 1: 환경 변수 파일 생성

아래 명령어를 그대로 터미널에 붙여넣어 `.env.production` 파일을 복사합니다.

```bash
cp /home/kj/Projects/Nuri-GPT/nuri-gpt-backend/.env.production.example /home/kj/Projects/Nuri-GPT/nuri-gpt-backend/.env.production
```

그런 다음 편집기로 열어 실제 값을 입력합니다:

```bash
nano /home/kj/Projects/Nuri-GPT/nuri-gpt-backend/.env.production
```

**반드시 수정해야 하는 항목:**

| 항목 | 설명 |
|------|------|
| `SUPABASE_URL` | Supabase 프로젝트 URL |
| `SUPABASE_KEY` | Supabase anon key |
| `SUPABASE_SERVICE_KEY` | Supabase service_role key |
| `SUPABASE_JWT_SECRET` | Supabase JWT secret (Auth → Settings → JWT Settings) |
| `GEMINI_API_KEY` | Google Gemini API 키 |
| `DIFY_API_KEY` | Dify 일지 생성용 API 키 |
| `DIFY_GREETING_API_KEY` | Dify 인삿말 생성용 API 키 |
| `KMA_API_KEY` | 기상청 단기예보 API 키 |
| `KMA_MID_API_KEY` | 기상청 중기예보 API 키 |
| `KMA_SPECIAL_DAY_API_KEY` | 한국천문연구원 특일정보 API 키 |

**Dify URL 선택 (둘 중 하나):**

```
# 옵션 A: Cloudflare 경유 (설정 변경 없음, 지연 약간 증가)
DIFY_API_URL=https://dify.vodqar.com/v1
DIFY_REGENERATE_API_URL=https://dify.vodqar.com/v1
DIFY_GREETING_API_URL=https://dify.vodqar.com/v1

# 옵션 B: 컨테이너→호스트 직접 (지연 최소화, host.docker.internal 필요)
DIFY_API_URL=http://host.docker.internal:8080/v1
DIFY_REGENERATE_API_URL=http://host.docker.internal:8080/v1
DIFY_GREETING_API_URL=http://host.docker.internal:8080/v1
```

수정 완료 후 저장: `Ctrl+O` → `Enter` → `Ctrl+X`

---

## Step 2: 호스트 nginx 설정 적용

### 2-1. 설정 파일 복사

```bash
sudo cp /home/kj/Projects/Nuri-GPT/deploy/nginx-nuri-gpt.conf /etc/nginx/sites-available/nuri-gpt
```

### 2-2. 심볼릭 링크 생성 (활성화)

```bash
sudo ln -sf /etc/nginx/sites-available/nuri-gpt /etc/nginx/sites-enabled/nuri-gpt
```

### 2-3. 설정 검증 및 nginx 리로드

```bash
sudo nginx -t && sudo systemctl reload nginx
```

정상 출력 예시:
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

---

## Step 3: Supabase Dashboard 설정

브라우저에서 Supabase 프로젝트 대시보드로 접속합니다.

1. 왼쪽 메뉴 → **Authentication** → **URL Configuration**
2. **Site URL** 필드에 추가:
   ```
   https://nuri-gpt.vodqar.com
   ```
3. **Redirect URLs**에 추가:
   ```
   https://nuri-gpt.vodqar.com/**
   ```
4. 오른쪽 상단 **Save** 클릭

---

## Step 4: Cloudflare DNS 확인

Cloudflare Dashboard → DNS → Records:

- `nuri-gpt.vodqar.com` 또는 `*.vodqar.com` A 레코드가 집 공인IP를 가리키고 있는지 확인
- 프록시 상태 (주황색 구름)가 **켜져 있으면** SSL/TLS → Overview → **Full (strict)** 모드인지 확인

---

## Step 5: Docker 이미지 빌드

프로젝트 루트에서 아래 명령어를 실행합니다.

```bash
cd /home/kj/Projects/Nuri-GPT
make build-docker
```

또는 docker compose 직접 실행:

```bash
cd /home/kj/Projects/Nuri-GPT
docker compose build --no-cache
```

빌드 완료까지 약 3~5분 소요 (frontend npm install + backend pip install).

---

## Step 6: 컨테이너 실행

```bash
cd /home/kj/Projects/Nuri-GPT
make up
```

또는 docker compose 직접 실행:

```bash
cd /home/kj/Projects/Nuri-GPT
docker compose up -d
```

실행 상태 확인:

```bash
cd /home/kj/Projects/Nuri-GPT
docker compose ps
```

정상 출력 예시:
```
NAME                  IMAGE                    COMMAND                  SERVICE    CREATED         STATUS         PORTS
nuri-gpt-backend      nuri-gpt-backend         "python -m uvicorn ..."   backend    5 seconds ago   Up 3 seconds   
nuri-gpt-frontend     nuri-gpt-frontend        "/docker-entrypoint..."   frontend   5 seconds ago   Up 3 seconds   0.0.0.0:8082->80/tcp
```

---

## Step 7: 배포 검증

### 7-1. 헬스체크

```bash
curl -s https://nuri-gpt.vodqar.com/api/health | python3 -m json.tool
```

정상 응답 예시:
```json
{
    "status": "healthy",
    "app_name": "Nuri-GPT",
    "version": "0.1.0",
    "uptime_seconds": 12.34
}
```

### 7-2. 컨테이너 내부 통신 확인

```bash
docker exec nuri-gpt-frontend wget -qO- http://backend:8000/api/health
```

정상 응답 예시:
```
{"status":"healthy","app_name":"Nuri-GPT","version":"0.1.0","uptime_seconds":45.67}
```

### 7-3. 프론트엔드 SPA 라우팅 확인

브라우저에서 다음 URL들이 모두 `200 OK` 또는 정상 표시되는지 확인:

- `https://nuri-gpt.vodqar.com/` (홈)
- `https://nuri-gpt.vodqar.com/login` (로그인 페이지, 새로고침 시에도 정상)

새로고침 시 404가 뜨면 nginx frontend 컨테이너의 `try_files` 설정 문제입니다. `nuri-gpt-frontend/frontend/nginx.conf`를 확인하세요.

### 7-4. 로그인 흐름 확인

1. `https://nuri-gpt.vodqar.com` 접속
2. 회원가입 또는 로그인
3. 로그인 후 메인 화면으로 정상 이동하는지 확인
4. **네트워크 탭**에서 CORS 오류(`Access-Control-Allow-Origin`)가 없는지 확인

### 7-5. Dify 연동 확인

인삿말 생성 또는 관찰일지 생성 API 호출 시 500/timeout이 발생하지 않는지 확인.
발생 시 `.env.production`의 `DIFY_API_URL`이 올바른지 (옵션 A vs 옵션 B) 점검.

---

## Step 8: 운영 (이후 업데이트 시 재배포)

### 코드 업데이트 후 재배포

```bash
cd /home/kj/Projects/Nuri-GPT
git pull origin main   # 또는 git fetch + rebase
make down
make build-docker
make up
```

### 컨테이너만 재시작 (빌드 없이)

```bash
cd /home/kj/Projects/Nuri-GPT
docker compose restart
```

### 로그 확인

```bash
cd /home/kj/Projects/Nuri-GPT
make logs
```

또는 백엔드 로그만:

```bash
docker logs -f nuri-gpt-backend
```

### 완전 삭제 (데이터 보존, 이미지/컨테이너 제거)

```bash
cd /home/kj/Projects/Nuri-GPT
docker compose down
```

---

## 문제 해결

### nginx 설정 오류

```bash
sudo nginx -t
```
오류 메시지의 파일 경로와 라인 번호를 확인하고 수정.

### SSL 인증서 경로 오류

```bash
ls -la /etc/letsencrypt/live/vodqar.com/
```
파일이 없으면 certbot 재발급:

```bash
sudo certbot certificates
sudo certbot renew --dry-run
```

### 502 Bad Gateway

- 컨테이너가 실행 중인지 확인: `docker compose ps`
- 호스트 nginx가 8082 포트로 프록시하는지 확인: `cat /etc/nginx/sites-available/nuri-gpt | grep 8082`

### CORS 오류 (개발자도구 → 콘솔)

- 백엔드 `.env.production`의 `CORS_ORIGINS`가 `https://nuri-gpt.vodqar.com`인지 확인
- Supabase URL Configuration의 Redirect URL이 정확한지 확인
- 백엔드 재시작: `docker compose restart backend`

### 파일 업로드 실패 (413 Payload Too Large)

두 곳 모두 확인:
- 호스트 nginx: `client_max_body_size 10M;` (이미 설정되어 있음)
- frontend nginx: `client_max_body_size 10M;` (이미 설정되어 있음)

---

## 관련 파일 경로 정리

| 파일 | 절대 경로 |
|------|----------|
| docker-compose.yml | `/home/kj/Projects/Nuri-GPT/docker-compose.yml` |
| Backend Dockerfile | `/home/kj/Projects/Nuri-GPT/nuri-gpt-backend/Dockerfile` |
| Frontend Dockerfile | `/home/kj/Projects/Nuri-GPT/nuri-gpt-frontend/frontend/Dockerfile` |
| Frontend nginx.conf | `/home/kj/Projects/Nuri-GPT/nuri-gpt-frontend/frontend/nginx.conf` |
| 호스트 nginx 템플릿 | `/home/kj/Projects/Nuri-GPT/deploy/nginx-nuri-gpt.conf` |
| .env.production 예시 | `/home/kj/Projects/Nuri-GPT/nuri-gpt-backend/.env.production.example` |
| .env.production (실제) | `/home/kj/Projects/Nuri-GPT/nuri-gpt-backend/.env.production` |
| Makefile | `/home/kj/Projects/Nuri-GPT/Makefile` |
| 배포 가이드 | `/home/kj/Projects/Nuri-GPT/deploy/DEPLOYMENT_GUIDE.md` |
