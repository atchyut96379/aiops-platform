import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL ?? '';

export const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

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
