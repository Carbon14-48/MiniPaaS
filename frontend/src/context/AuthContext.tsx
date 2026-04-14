import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import type { User, TokenResponse } from '../types/auth';
import { authApi } from '../lib/api';

interface AuthContextType {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => void;
  refreshAccessToken: () => Promise<boolean>;
  clearError: () => void;
  fetchUser: () => Promise<void>;
  completeGitHubLogin: (code: string) => Promise<void>;
  onTokenRefresh: (callback: (token: string) => void) => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

const TOKEN_KEY = 'minipaas_access_token';
const REFRESH_KEY = 'minipaas_refresh_token';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [refreshToken, setRefreshToken] = useState<string | null>(() => localStorage.getItem(REFRESH_KEY));
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const refreshCallbacksRef = useRef<((token: string) => void)[]>([]);

  const isAuthenticated = !!accessToken;

  const notifyTokenRefresh = useCallback((token: string) => {
    refreshCallbacksRef.current.forEach(cb => cb(token));
  }, []);

  const clearError = useCallback(() => setError(null), []);

  const fetchUser = useCallback(async () => {
    if (!accessToken) return;
    try {
      const userData = await authApi.getMe(accessToken);
      setUser(userData);
    } catch {
      logout();
    }
  }, [accessToken]);

  useEffect(() => {
    if (accessToken && !user) {
      fetchUser();
    }
  }, [accessToken, user, fetchUser]);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const tokens = await authApi.login({ email, password });
      setTokens(tokens);
      const userData = await authApi.getMe(tokens.access_token);
      setUser(userData);
    } catch (err: unknown) {
      const message = err instanceof Error && 'response' in err 
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Login failed'
        : 'Login failed';
      setError(message);
      throw new Error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (email: string, password: string, name: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const tokens = await authApi.register({ email, password, name });
      setTokens(tokens);
      const userData = await authApi.getMe(tokens.access_token);
      setUser(userData);
    } catch (err: unknown) {
      const message = err instanceof Error && 'response' in err 
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Registration failed'
        : 'Registration failed';
      setError(message);
      throw new Error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    setAccessToken(null);
    setRefreshToken(null);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
  };

  const onTokenRefresh = (callback: (token: string) => void) => {
    refreshCallbacksRef.current.push(callback);
  };

  const refreshAccessToken = async (): Promise<boolean> => {
    if (!refreshToken) {
      logout();
      return false;
    }
    try {
      const tokens = await authApi.refreshToken(refreshToken);
      setTokens(tokens);
      notifyTokenRefresh(tokens.access_token);
      const userData = await authApi.getMe(tokens.access_token);
      setUser(userData);
      return true;
    } catch {
      logout();
      return false;
    }
  };

  const completeGitHubLogin = async (code: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const tokens = await authApi.githubCallback(code);
      setTokens(tokens);
      const userData = await authApi.getMe(tokens.access_token);
      setUser(userData);
    } catch (err: unknown) {
      const message = err instanceof Error && 'response' in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'GitHub login failed'
        : 'GitHub login failed';
      setError(message);
      throw new Error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const setTokens = (tokens: TokenResponse) => {
    setAccessToken(tokens.access_token);
    setRefreshToken(tokens.refresh_token);
    localStorage.setItem(TOKEN_KEY, tokens.access_token);
    localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken,
        refreshToken,
        isAuthenticated,
        isLoading,
        error,
        login,
        register,
        logout,
        refreshAccessToken,
        clearError,
        fetchUser,
        completeGitHubLogin,
        onTokenRefresh,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
