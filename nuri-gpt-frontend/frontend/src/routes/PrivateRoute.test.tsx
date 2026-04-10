import { afterEach, describe, expect, it } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { render, screen } from '@testing-library/react';

import { PrivateRoute } from './PrivateRoute';
import { useAuthStore } from '../store/authStore';

afterEach(() => {
  useAuthStore.setState({
    isAuthenticated: false,
    accessToken: null,
    user: null,
  });
  localStorage.clear();
});

describe('PrivateRoute', () => {
  it('현재 구현에서는 인증 여부와 무관하게 하위 라우트를 렌더링한다', () => {
    useAuthStore.setState({
      isAuthenticated: false,
      accessToken: null,
      user: null,
    });

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Routes>
          <Route element={<PrivateRoute />}>
            <Route path="/dashboard" element={<div>DASHBOARD_PAGE</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('DASHBOARD_PAGE')).toBeInTheDocument();
  });
});
