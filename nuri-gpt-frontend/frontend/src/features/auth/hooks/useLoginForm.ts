import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { useAuthStore } from '../../../store/authStore';
import { loginSchema, type LoginFormValues } from '../schemas/loginSchema';
import { loginApi } from '../api/auth';

export const useLoginForm = () => {
  const login = useAuthStore((state) => state.login);
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
      remember: false,
    },
  });

  const handleSubmit = form.handleSubmit(async (values) => {
    try {
      setIsLoading(true);
      const response = await loginApi(values);
      
      login(response.access_token, { ...response.user, role: 'user' as const });

      navigate('/dashboard');
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || '로그인 중 오류가 발생했습니다.';
      form.setError('root', { type: 'manual', message: errorMessage });
    } finally {
      setIsLoading(false);
    }
  });

  return {
    ...form,
    handleSubmit,
    isLoading,
  };
};
