import { afterEach, describe, expect, it } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { render, screen } from '@testing-library/react';

import { PublicRoute } from './PublicRoute';
import { useAuthStore } from '../store/authStore';

afterEach(() => {
  useAuthStore.setState({
    isAuthenticated: false,
    accessToken: null,
    user: null,
  });
  localStorage.clear();
});

describe('PublicRoute', () => {
  it('인증되지 않은 사용자는 로그인 화면에 접근할 수 있다', () => {
    useAuthStore.setState({
      isAuthenticated: false,
      accessToken: null,
      user: null,
    });

    render(
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/login" element={<PublicRoute />}>
            <Route index element={<div>LOGIN_PAGE</div>} />
          </Route>
          <Route path="/observations" element={<div>OBSERVATIONS_PAGE</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('LOGIN_PAGE')).toBeInTheDocument();
  });

  it('인증된 사용자는 관찰일지 화면으로 리다이렉트된다', () => {
    useAuthStore.setState({
      isAuthenticated: true,
      accessToken: 'token',
      user: { id: '1', email: 'test@example.com', name: '테스트', role: 'user' as const, preferences: {} },
    });

    render(
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/login" element={<PublicRoute />}>
            <Route index element={<div>LOGIN_PAGE</div>} />
          </Route>
          <Route path="/observations" element={<div>OBSERVATIONS_PAGE</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('OBSERVATIONS_PAGE')).toBeInTheDocument();
  });
});
