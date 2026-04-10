import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import './lib/i18n'

// 미처리 Promise 거절 핸들러
window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason);
  if (import.meta.env.DEV) {
    window.dispatchEvent(new CustomEvent('toast', { 
      detail: { message: `[DEV] Unhandled Error: ${event.reason?.message || event.reason}`, type: 'error' } 
    }));
  }
});

// 전역 JavaScript 에러 핸들러
window.addEventListener('error', (event) => {
  console.error('Uncaught error:', event.error);
});

async function enableMocking() {
  // MSW 완전 비활성화 - 실제 백엔드와 통신
  // 개발 중에도 실제 API 서버(8001)와 직접 통신하려면 아래 코드 주석 처리
  return;

  // if (import.meta.env.MODE !== 'development') {
  //   return;
  // }

  // const { worker } = await import('./mocks/browser');
  // return worker.start({
  //   onUnhandledRequest: 'bypass',
  // });
}

enableMocking().then(() => {
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
});
