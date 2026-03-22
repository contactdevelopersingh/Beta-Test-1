import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('signalbeast_token'));

  const api = useCallback(() => {
    const instance = axios.create({ baseURL: API, withCredentials: true });
    instance.interceptors.request.use(config => {
      const t = localStorage.getItem('signalbeast_token');
      if (t) config.headers.Authorization = `Bearer ${t}`;
      return config;
    });
    return instance;
  }, []);

  const checkAuth = useCallback(async () => {
    try {
      const resp = await api().get('/auth/me');
      setUser(resp.data);
    } catch {
      setUser(null);
      localStorage.removeItem('signalbeast_token');
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    // CRITICAL: If returning from OAuth callback, skip the /me check.
    // AuthCallback will exchange the session_id and establish the session first.
    if (window.location.hash?.includes('session_id=')) {
      setLoading(false);
      return;
    }
    checkAuth();
  }, [checkAuth]);

  const loginWithCredentials = async (email, password) => {
    const resp = await api().post('/auth/login', { email, password });
    localStorage.setItem('signalbeast_token', resp.data.token);
    setToken(resp.data.token);
    setUser(resp.data);
    return resp.data;
  };

  const register = async (email, password, name) => {
    const resp = await api().post('/auth/register', { email, password, name });
    localStorage.setItem('signalbeast_token', resp.data.token);
    setToken(resp.data.token);
    setUser(resp.data);
    return resp.data;
  };

  const loginWithGoogle = () => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = window.location.origin + '/dashboard';
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  const processSession = async (sessionId) => {
    const resp = await api().post('/auth/session', { session_id: sessionId });
    localStorage.setItem('signalbeast_token', resp.data.token);
    setToken(resp.data.token);
    setUser(resp.data);
    return resp.data;
  };

  const logout = async () => {
    try { await api().post('/auth/logout'); } catch {}
    localStorage.removeItem('signalbeast_token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, token, api: api(), loginWithCredentials, register, loginWithGoogle, processSession, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
};
