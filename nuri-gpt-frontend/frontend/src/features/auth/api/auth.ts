import { api } from '../../../services/api';
import type { LoginFormValues } from '../schemas/loginSchema';

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id: string;
    email: string;
    name: string;
  };
}

export const loginApi = async (credentials: LoginFormValues): Promise<LoginResponse> => {
  const response = await api.post('/auth/login', credentials);
  return response.data;
};
