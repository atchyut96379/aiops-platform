import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { api, clearAuth, getStoredToken, setAuthToken, storeAuth } from '../api/client';
import type { User } from '../api/types';

interface AuthContextValue {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string, totpCode?: string) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
}

interface RegisterPayload {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  organization_name: string;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(getStoredToken());
  const [loading, setLoading] = useState(true);

  const loadProfile = useCallback(async () => {
    const stored = getStoredToken();
    if (!stored) {
      setLoading(false);
      return;
    }
    setAuthToken(stored);
    try {
      const { data } = await api.get('/api/v1/users/me');
      setUser(data);
      setToken(stored);
    } catch {
      clearAuth();
      setUser(null);
      setToken(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadProfile();
  }, [loadProfile]);

  const login = async (email: string, password: string, totpCode?: string) => {
    const { data } = await api.post('/api/v1/auth/login', {
      email,
      password,
      totp_code: totpCode || undefined,
    });
    storeAuth(data.access_token, data.refresh_token);
    setToken(data.access_token);
    const profile = await api.get('/api/v1/users/me');
    setUser(profile.data);
  };

  const register = async (payload: RegisterPayload) => {
    const { data } = await api.post('/api/v1/auth/register', payload);
    storeAuth(data.tokens.access_token, data.tokens.refresh_token);
    setToken(data.tokens.access_token);
    setUser(data.user);
  };

  const logout = () => {
    clearAuth();
    setUser(null);
    setToken(null);
  };

  const value = useMemo(
    () => ({ user, token, loading, login, register, logout }),
    [user, token, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
