export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface User {
  id: number;
  email: string;
  name: string;
  oauth_provider: string | null;
  has_password: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}

export interface GitHubCallbackRequest {
  code: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}
