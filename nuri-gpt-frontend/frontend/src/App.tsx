import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { AppLayout } from './components/layout/AppLayout';
import { ObservationPage } from './features/observation/ObservationPage';
import { JournalHistoryPage } from './features/observation/components/JournalHistoryPage';
import { LoginPage } from './features/auth/pages/LoginPage';
import { PrivateRoute } from './routes/PrivateRoute';
import { PublicRoute } from './routes/PublicRoute';
import { useAuthInterceptor } from './hooks/useAuthInterceptor';
import { ToastContainer } from './components/global/ToastContainer';
import { ErrorBoundary } from './components/global/ErrorBoundary';
import { OfflineBanner } from './components/global/OfflineBanner';

// 별도 컴포넌트로 분리하여 useNavigate hook 사용을 가능하게 함
function AppRoutes() {
  useAuthInterceptor();
  const { t } = useTranslation();

  return (
    <Routes>
      {/* 비로그인 사용자용 라우트 */}
      <Route element={<PublicRoute />}>
        <Route path="/login" element={<LoginPage />} />
      </Route>

      {/* 로그인 사용자 전용 라우트 */}
      <Route element={<PrivateRoute />}>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<div className="p-10"><h1 className="text-2xl font-bold">{t('app.dashboardTitle')}</h1></div>} />
          <Route path="observations" element={<ObservationPage />} />
          <Route path="observations/history" element={<JournalHistoryPage />} />
          <Route path="logs" element={<div className="p-10"><h1 className="text-2xl font-bold">{t('app.logsTitle')}</h1></div>} />
          <Route path="insights" element={<div className="p-10"><h1 className="text-2xl font-bold">{t('app.insightsTitle')}</h1></div>} />
        </Route>
      </Route>
      
      {/* 알 수 없는 경로는 루트로 리다이렉트 (추후 404 페이지로 변경 가능) */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <OfflineBanner />
        <AppRoutes />
        <ToastContainer />
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
