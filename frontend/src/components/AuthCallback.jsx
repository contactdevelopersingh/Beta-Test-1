import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const AuthCallback = () => {
  const hasProcessed = useRef(false);
  const navigate = useNavigate();
  const { processSession } = useAuth();

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const hash = window.location.hash;
    const sessionId = new URLSearchParams(hash.substring(1)).get('session_id');

    if (!sessionId) {
      navigate('/auth', { replace: true });
      return;
    }

    const exchange = async () => {
      try {
        const userData = await processSession(sessionId);
        navigate('/dashboard', { replace: true, state: { user: userData } });
      } catch (err) {
        console.error('Auth callback failed:', err);
        navigate('/auth', { replace: true });
      }
    };
    exchange();
  }, [navigate, processSession]);

  return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: '#050505' }}>
      <div className="text-center">
        <div className="w-12 h-12 border-2 border-[#6366F1] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-white/60 text-sm font-data" data-testid="auth-callback-loading">Authenticating...</p>
      </div>
    </div>
  );
};
