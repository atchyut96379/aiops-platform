import axios, { isAxiosError } from 'axios';

const API_BASE = import.meta.env.VITE_API_URL ?? '';

export const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

export function getApiErrorMessage(error: unknown, fallback = 'Something went wrong'): string {
  if (!isAxiosError(error)) {
    return error instanceof Error ? error.message : fallback;
  }

  const data = error.response?.data as
    | { error?: { message?: string }; detail?: string | { msg?: string }[] }
    | undefined;

  if (data?.error?.message) return data.error.message;

  if (Array.isArray(data?.detail)) {
    return data.detail.map((item) => item.msg ?? String(item)).join('. ');
  }

  if (typeof data?.detail === 'string') return data.detail;

  if (error.message === 'Network Error') {
    return 'Cannot reach the API. Start the backend with: uvicorn main:app --reload --port 8000';
  }

  return fallback;
}

export function setAuthToken(token: string | null) {
  if (token) {
    api.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common.Authorization;
  }
}

export function getStoredToken(): string | null {
  return localStorage.getItem('access_token');
}

export function storeAuth(accessToken: string, refreshToken: string) {
  localStorage.setItem('access_token', accessToken);
  localStorage.setItem('refresh_token', refreshToken);
  setAuthToken(accessToken);
}

export function clearAuth() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  setAuthToken(null);
}

const token = getStoredToken();
if (token) setAuthToken(token);
