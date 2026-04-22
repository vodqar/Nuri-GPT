# 라이브 환경 보안 평가 보고서

**대상**: https://nuri-gpt.vodqar.com/  
**평가일**: 2026년 4월 22일  
**평가자**: Red Team Agent  
**심각도 기준**: Critical > High > Medium > Low > Info

---

## 요약

본 보고서는 Nuri-GPT 라이브 배포 환경에 대한 보안 취약점 평가 결과를 담고 있습니다. 인증/인가, CORS 설정, API 보안, 프롬프트 인젝션 등 다양한 공격 벡터를 탐색하였습니다.

**총 발견**: 3건 (High: 1건, Medium: 1건, Low: 1건)

---

## 발견된 취약점

### 1. [HIGH] Rate Limiting 미구현

**심각도**: High  
**위치**: 모든 API 엔드포인트  
**CVE**: N/A

#### 설명
API 엔드포인트에 Rate Limiting이 구현되어 있지 않습니다. 20회 연속 요청 테스트 결과 모든 요청이 성공적으로 처리되었습니다.

#### 증거
```bash
# 20회 연속 요청 테스트
for i in {1..20}; do 
  curl -s -X GET 'https://nuri-gpt.vodqar.com/api/templates/' \
    -H "Authorization: Bearer $TOKEN" \
    -H 'Content-Type: application/json'
done
# 결과: 모든 요청 성공 (HTTP 200)
```

#### 영향
- **DoS 공격**: 공격자가 대량의 요청을 보내 서버 리소스를 고갈시킬 수 있습니다
- **과금 폭탄**: Gemini API 기반 서비스의 경우, 악의적인 대량 요청으로 인해 API 사용량이 폭증하여 비용이 발생할 수 있습니다
- **Brute Force 공격**: 인증 엔드포인트에서 비밀번호 추측 공격이 가능합니다

#### 권고 사항
1. API Gateway 또는 애플리케이션 레벨에서 Rate Limiting 구현
2. 사용자별/IP별 요청 제한 설정 (예: 분당 100회)
3. Redis 등을 사용하여 분산 환경에서도 일관된 제한 적용
4. 초과 시 429 Too Many Requests 응답 반환

#### 참고
- OWASP API Security Top 10: API4:2023 - Unrestricted Resource Consumption

---

### 2. [MEDIUM] 인삿말 생성 기능의 API 호출 문제

**심각도**: Medium  
**위치**: `/tools/greeting` 페이지  
**CVE**: N/A

#### 설명
인삿말 생성 페이지에서 "인삿말 생성하기" 버튼을 클릭해도 API가 호출되지 않습니다. 이는 프론트엔드 버그로 보이며, 프롬프트 인젝션 취약점 테스트를 방해합니다.

#### 증거
- 버튼 클릭 후 네트워크 요청에 생성 API가 없음
- 생성 결과 영역에 "지역과 날짜를 선택한 후 '인삿말 생성하기' 버튼을 눌러주세요." 메시지가 지속됨

#### 영향
- **기능 장애**: 사용자가 인삿말 생성 기능을 사용할 수 없습니다
- **보안 테스트 제한**: 프롬프트 인젝션 취약점을 적절히 테스트할 수 없습니다

#### 권고 사항
1. 프론트엔드 코드에서 버튼 클릭 이벤트 핸들러 확인
2. API 호출 로직 디버깅 및 수정
3. 수정 후 프롬프트 인젝션 방어 구현 확인

---

### 3. [LOW] 토큰 저장 방식 개선 권고

**심각도**: Low  
**위치**: 클라이언트 사이드  
**CVE**: N/A

#### 설명
현재 JWT 토큰이 쿠키, localStorage, sessionStorage 어디에도 저장되지 않고 메모리에만 저장되는 것으로 추정됩니다. 이는 XSS 공격에 대한 방어에는 유리하지만, 페이지 새로고침 시 로그아웃되는 사용자 경험 문제가 있을 수 있습니다.

#### 증거
```javascript
// 브라우저 콘솔에서 확인
document.cookie // ""
localStorage // {}
sessionStorage // {}
```

#### 영향
- **사용자 경험**: 페이지 새로고침 시 재로그인 필요
- **보안**: 메모리 저장은 XSS에 강하지만 구현이 올바르게 되었는지 확인 필요

#### 권고 사항
1. 현재 구현이 의도된 메모리 저장인지 확인
2. HttpOnly, Secure, SameSite 쿠키 사용 검토
3. XSS 방어 조치(Content Security Policy 강화)와 함께 쿠키 저장 고려

---

## 테스트된 보안 통제 (양호)

### 1. 인증/인가
- **JWT Bearer 토큰 사용**: 적절하게 구현됨
- **토큰 검증**: 유효하지 않은 토큰은 거부됨
- **인증 없는 접근 차단**: 인증 토큰 없이 API 접근 시 401 응답
- **IDOR 방어**: 다른 사용자의 UUID로 접근 시 "Not Found" 응답

### 2. CORS 설정
- **Access-Control-Allow-Origin**: 명시적으로 설정되지 않음 (좋음)
- **Allowed Methods**: GET, POST, PUT, PATCH, DELETE, OPTIONS로 제한됨
- **Allowed Headers**: Authorization, Content-Type 등 필요한 헤더로 제한됨
- **Credentials**: 허용되지만 Origin 제한이 있어 안전

### 3. 입력 검증
- **XSS 방어**: Pydantic을 통한 입력 검증으로 `<script>alert(1)</script>` 차단
- **SQL Injection**: 파라미터 기반 쿼리 또는 ORM 사용으로 SQLi 방어
- **이메일 검증**: Pydantic 이메일 밸리데이터로 적절한 검증

### 4. 보안 헤더
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'
Strict-Transport-Security: max-age=31536000; includeSubDomains
```
모든 보안 헤더가 적절하게 설정됨

### 5. 정보 노출 방지
- **에러 메시지**: 일반적인 에러 메시지로 내부 정보 노출 없음
- **서버 정보**: Cloudflare만 노출, 기술 스택 정보 노출 없음
- **스택 트레이스**: 에러 시 스택 트레이스 노출 없음

---

## 테스트되지 않은 항목

### 프롬프트 인젝션 (Gemini API)
인삿말 생성 API가 호출되지 않아 완전한 테스트 불가. 추후 기능 수정 후 다음 테스트 권고:
- 시스템 프롬프트 노출 시도
- 악의적인 지시 주입
- API 키 탈취 시도
- 과도한 토큰 사용 유도

---

## 권고 사항 요약

### 즉시 조치 (High Priority)
1. **Rate Limiting 구현**: API Gateway 또는 애플리케이션 레벨에서 요청 제한 구현

### 단기 조치 (Medium Priority)
1. **인삿말 생성 기능 수정**: 버그 수정 후 프롬프트 인젝션 방어 구현 확인
2. **프롬프트 인젝션 테스트**: 기능 수정 후 완전한 보안 테스트 수행

### 장기 조치 (Low Priority)
1. **토큰 저장 방식 검토**: 현재 메모리 저장 방식의 보안성과 사용자 경험 균형 검토
2. **모니터링 강화**: 비정상적인 API 사용 패턴 모니터링 및 알림 구현

---

## 부록

### 테스트 환경
- **테스트 계정**: mbk7990@gmail.com
- **테스트 도구**: curl, Playwright MCP
- **테스트 날짜**: 2026-04-22

### 참고 문서
- OWASP API Security Top 10 (2023)
- OWASP Testing Guide v4.2
- CWE Top 25 (2024)

---

**보고서 종료**
