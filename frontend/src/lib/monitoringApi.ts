import axios from 'axios';

const API_BASE = '';
const TOKEN_KEY = 'minipaas_access_token';

const getToken = (): string | null => localStorage.getItem(TOKEN_KEY);

const monitoringApi = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

monitoringApi.interceptors.request.use((config) => {
  if (!config.headers.Authorization) {
    const token = getToken();
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface Metric {
  app_id: string;
  user_id: number;
  container_name: string;
  cpu_percent: number;
  memory_usage_bytes: number;
  memory_percent: number;
  network_rx_bytes: number;
  network_tx_bytes: number;
  status: string;
  collected_at: string;
}

export interface LogEntry {
  id: string;
  app_id: string;
  user_id: number;
  level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG';
  message: string;
  log_timestamp: string;
  collected_at: string;
}

export interface AppHealth {
  app_id: string;
  status: string;
  healthy: boolean;
  container_name: string | null;
  last_seen: string | null;
  last_cpu_percent: number | null;
  last_memory_percent: number | null;
}

export interface ContainerStatus {
  app_id: string;
  user_id: number;
  container_name: string;
  container_id: string;
  status: string;
  healthy: boolean;
}

export const monitoringApiService = {
  getSummary: async (): Promise<Metric[]> => {
    const response = await monitoringApi.get<Metric[]>('/metrics/summary', {
      withCredentials: true,
    });
    return response.data;
  },

  getAppMetrics: async (appId: string, minutes = 60): Promise<Metric[]> => {
    const response = await monitoringApi.get<Metric[]>(`/metrics/${appId}`, {
      params: { minutes },
      withCredentials: true,
    });
    return response.data;
  },

  getUserMetrics: async (userId: number, minutes = 60): Promise<Metric[]> => {
    const response = await monitoringApi.get<Metric[]>(`/metrics/user/${userId}`, {
      params: { minutes },
      withCredentials: true,
    });
    return response.data;
  },

  getAppLogs: async (
    appId: string,
    options: { minutes?: number; level?: string; limit?: number } = {}
  ): Promise<LogEntry[]> => {
    const response = await monitoringApi.get<LogEntry[]>(`/logs/${appId}`, {
      params: options,
      withCredentials: true,
    });
    return response.data;
  },

  getLiveLogs: async (
    appId: string,
    tail = 100
  ): Promise<{ app_id: string; container: string; source: string; entries: string[] }> => {
    const response = await monitoringApi.get<{
      app_id: string;
      container: string;
      source: string;
      entries: string[];
    }>(`/logs/${appId}/live`, {
      params: { tail },
      withCredentials: true,
    });
    return response.data;
  },

  getHealth: async (appId: string): Promise<AppHealth> => {
    const response = await monitoringApi.get<AppHealth>(`/health/${appId}`, {
      withCredentials: true,
    });
    return response.data;
  },

  getAllContainers: async (): Promise<{
    docker_daemon: string;
    containers: ContainerStatus[];
    total: number;
    running: number;
  }> => {
    const response = await monitoringApi.get<{
      docker_daemon: string;
      containers: ContainerStatus[];
      total: number;
      running: number;
    }>('/health/containers/all', {
      withCredentials: true,
    });
    return response.data;
  },

  getHealthCheck: async (): Promise<{
    status: string;
    service: string;
    port: number;
    database: string;
    docker_daemon: string;
  }> => {
    const response = await monitoringApi.get('/health');
    return response.data;
  },
};

export default monitoringApiService;