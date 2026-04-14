import axios from 'axios';
import type {
  TokenResponse,
  User,
  LoginRequest,
  RegisterRequest,
} from '../types/auth';

const API_BASE = 'http://localhost:8001';
const DEPLOYER_BASE = '';  // Use Vite proxy to avoid CORS issues

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

const deployerApi = axios.create({
  baseURL: DEPLOYER_BASE,
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

export interface Deployment {
  id: string;
  user_id: number;
  app_name: string;
  repo_url: string;
  branch: string;
  status: 'pending' | 'building' | 'deploying' | 'running' | 'stopped' | 'failed' | 'blocked';
  build_job_id?: string;
  image_tag?: string;
  image_url?: string;
  container_id?: string;
  container_url?: string;
  host_port?: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
  started_at?: string;
}

export interface GitHubRepo {
  id: number;
  name: string;
  full_name: string;
  description?: string;
  private: boolean;
  html_url: string;
  default_branch: string;
  updated_at: string;
  language?: string;
}

export interface GitHubBranch {
  name: string;
  commit_sha: string;
  protected: boolean;
}

export const deployerApiService = {
  getRepos: async (accessToken: string): Promise<GitHubRepo[]> => {
    const response = await deployerApi.get<GitHubRepo[]>('/repos/', {
      headers: { Authorization: `Bearer ${accessToken}` },
      withCredentials: true,
    });
    return response.data;
  },

  getBranches: async (accessToken: string, owner: string, repo: string): Promise<GitHubBranch[]> => {
    const response = await deployerApi.get<GitHubBranch[]>(`/repos/${owner}/${repo}/branches`, {
      headers: { Authorization: `Bearer ${accessToken}` },
      withCredentials: true,
    });
    return response.data;
  },

  getDeployments: async (accessToken: string): Promise<{ deployments: Deployment[]; total: number }> => {
    const response = await deployerApi.get<{ deployments: Deployment[]; total: number }>('/deployments/', {
      headers: { Authorization: `Bearer ${accessToken}` },
      withCredentials: true,
    });
    return response.data;
  },

  getDeployment: async (accessToken: string, id: string): Promise<Deployment> => {
    const response = await deployerApi.get<Deployment>(`/deployments/${id}`, {
      headers: { Authorization: `Bearer ${accessToken}` },
      withCredentials: true,
    });
    return response.data;
  },

  createDeployment: async (
    accessToken: string,
    data: { repo_url: string; branch: string; app_name: string }
  ): Promise<Deployment> => {
    const response = await deployerApi.post<Deployment>('/deployments/', data, {
      headers: { Authorization: `Bearer ${accessToken}` },
      withCredentials: true,
    });
    return response.data;
  },

  stopDeployment: async (accessToken: string, id: string): Promise<Deployment> => {
    const response = await deployerApi.post<Deployment>(`/deployments/${id}/stop`, {}, {
      headers: { Authorization: `Bearer ${accessToken}` },
      withCredentials: true,
    });
    return response.data;
  },

  startDeployment: async (accessToken: string, id: string): Promise<Deployment> => {
    const response = await deployerApi.post<Deployment>(`/deployments/${id}/start`, {}, {
      headers: { Authorization: `Bearer ${accessToken}` },
      withCredentials: true,
    });
    return response.data;
  },

  restartDeployment: async (accessToken: string, id: string): Promise<Deployment> => {
    const response = await deployerApi.post<Deployment>(`/deployments/${id}/restart`, {}, {
      headers: { Authorization: `Bearer ${accessToken}` },
      withCredentials: true,
    });
    return response.data;
  },

  deleteDeployment: async (accessToken: string, id: string): Promise<Deployment> => {
    const response = await deployerApi.delete<Deployment>(`/deployments/${id}`, {
      headers: { Authorization: `Bearer ${accessToken}` },
      withCredentials: true,
    });
    return response.data;
  },

  getDeploymentLogs: async (accessToken: string, id: string, tail = 100): Promise<{ logs: string; source: string }> => {
    const response = await deployerApi.get<{ logs: string; source: string }>(
      `/deployments/${id}/logs?tail=${tail}`,
      { headers: { Authorization: `Bearer ${accessToken}` }, withCredentials: true }
    );
    return response.data;
  },
};

export default api;
