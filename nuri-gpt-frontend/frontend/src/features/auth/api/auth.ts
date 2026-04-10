import { api } from '../../../services/api';
import type { LoginFormValues } from '../schemas/loginSchema';

export interface LoginResponse {
  access_token: string;
  user: {
    id: string;
    email: string;
    [key: string]: unknown;
  };
}

export const loginApi = async (credentials: LoginFormValues): Promise<LoginResponse> => {
  const response = await api.post('/auth/login', credentials);
  return response.data;
};
