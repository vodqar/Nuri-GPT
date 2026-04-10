import { http, HttpResponse, passthrough } from 'msw';

export const handlers = [
  // 로그인: 실제 백엔드로 통과 (Supabase 연동)
  // pathname만 매칭하여 어떤 origin에서도 가로챌 수 있음
  http.post('*/api/auth/login', () => {
    return passthrough();
  }),

  // 401 Unauthorized 테스트용 핸들러 (test_401=true 쿼리 파라미터 시에만 동작)
  http.get('*/api/templates/', async ({ request }) => {
    const url = new URL(request.url);
    if (url.searchParams.get('test_401') === 'true') {
      return HttpResponse.json(
        { message: 'Unauthorized' },
        { status: 401 }
      );
    }
    // 실제 백엔드로 통과 (passthrough)
    return passthrough();
  }),
];
