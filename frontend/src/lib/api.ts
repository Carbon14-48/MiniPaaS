import axios from 'axios';
import type {
  TokenResponse,
  User,
  LoginRequest,
  RegisterRequest,
} from '../types/auth';

const API_BASE = 'http://localhost:8001';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const authApi = {
  register: async (data: RegisterRequest): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/auth/register', data);
    return response.data;
  },

  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/auth/login', data);
    return response.data;
  },

  githubAuthUrl: async (): Promise<{ url: string }> => {
    const response = await api.get<{ url: string }>('/auth/github');
    return response.data;
  },

  githubCallback: async (code: string): Promise<TokenResponse> => {
    const response = await api.get<TokenResponse>('/auth/callback', { params: { code } });
    return response.data;
  },

  getMe: async (accessToken: string): Promise<User> => {
    const response = await api.get<User>('/auth/me', {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });
    return response.data;
  },

  refreshToken: async (refreshToken: string): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/auth/refresh', { refresh_token: refreshToken });
    return response.data;
  },

  health: async (): Promise<{ status: string; service: string }> => {
    const response = await api.get<{ status: string; service: string }>('/health/');
    return response.data;
  },
};

export default api;
