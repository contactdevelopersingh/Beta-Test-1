import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Activity, Mail, Lock, User, ArrowLeft } from 'lucide-react';
import { toast } from 'sonner';
import { Toaster } from '../components/ui/sonner';

export default function AuthPage() {
  const { loginWithCredentials, register, loginWithGoogle } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const [loginData, setLoginData] = useState({ email: '', password: '' });
  const [regData, setRegData] = useState({ name: '', email: '', password: '' });

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await loginWithCredentials(loginData.email, loginData.password);
      toast.success('Welcome back!');
      navigate('/dashboard', { replace: true });
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await register(regData.email, regData.password, regData.name);
      toast.success('Account created!');
      navigate('/dashboard', { replace: true });
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 hero-gradient" style={{ background: '#050505' }}>
      <Toaster position="top-right" theme="dark" />
      <div className="w-full max-w-md">
        <button onClick={() => navigate('/')} className="flex items-center gap-2 text-white/40 hover:text-white text-sm mb-8 group" data-testid="back-to-home-btn">
          <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1" style={{ transition: 'transform 0.2s' }} />
          Back to home
        </button>

        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl bg-[#6366F1] flex items-center justify-center neon-glow">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white" style={{ fontFamily: 'Manrope' }}>SignalBeast Pro</h1>
            <p className="text-xs text-white/40">Trading Intelligence Platform</p>
          </div>
        </div>

        <div className="glass-panel rounded-2xl p-8">
          <Tabs defaultValue="login">
            <TabsList className="w-full bg-white/5 mb-6">
              <TabsTrigger value="login" className="flex-1 text-xs data-[state=active]:bg-[#6366F1] data-[state=active]:text-white" data-testid="login-tab">Log In</TabsTrigger>
              <TabsTrigger value="register" className="flex-1 text-xs data-[state=active]:bg-[#6366F1] data-[state=active]:text-white" data-testid="register-tab">Sign Up</TabsTrigger>
            </TabsList>

            <TabsContent value="login">
              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <Label className="text-xs text-white/60 mb-1.5 block">Email</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
                    <Input
                      type="email" required placeholder="you@example.com"
                      className="pl-10 bg-black/50 border-white/10 focus:border-[#6366F1] text-white text-sm"
                      value={loginData.email} onChange={e => setLoginData({ ...loginData, email: e.target.value })}
                      data-testid="login-email-input"
                    />
                  </div>
                </div>
                <div>
                  <Label className="text-xs text-white/60 mb-1.5 block">Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
                    <Input
                      type="password" required placeholder="Enter password"
                      className="pl-10 bg-black/50 border-white/10 focus:border-[#6366F1] text-white text-sm"
                      value={loginData.password} onChange={e => setLoginData({ ...loginData, password: e.target.value })}
                      data-testid="login-password-input"
                    />
                  </div>
                </div>
                <Button type="submit" disabled={loading} className="w-full bg-[#6366F1] hover:bg-[#4F46E5] text-white shadow-[0_0_15px_rgba(99,102,241,0.4)] active:scale-95" data-testid="login-submit-btn">
                  {loading ? 'Logging in...' : 'Log In'}
                </Button>
              </form>
            </TabsContent>

            <TabsContent value="register">
              <form onSubmit={handleRegister} className="space-y-4">
                <div>
                  <Label className="text-xs text-white/60 mb-1.5 block">Full Name</Label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
                    <Input
                      type="text" required placeholder="John Doe"
                      className="pl-10 bg-black/50 border-white/10 focus:border-[#6366F1] text-white text-sm"
                      value={regData.name} onChange={e => setRegData({ ...regData, name: e.target.value })}
                      data-testid="register-name-input"
                    />
                  </div>
                </div>
                <div>
                  <Label className="text-xs text-white/60 mb-1.5 block">Email</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
                    <Input
                      type="email" required placeholder="you@example.com"
                      className="pl-10 bg-black/50 border-white/10 focus:border-[#6366F1] text-white text-sm"
                      value={regData.email} onChange={e => setRegData({ ...regData, email: e.target.value })}
                      data-testid="register-email-input"
                    />
                  </div>
                </div>
                <div>
                  <Label className="text-xs text-white/60 mb-1.5 block">Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
                    <Input
                      type="password" required placeholder="Min 6 characters" minLength={6}
                      className="pl-10 bg-black/50 border-white/10 focus:border-[#6366F1] text-white text-sm"
                      value={regData.password} onChange={e => setRegData({ ...regData, password: e.target.value })}
                      data-testid="register-password-input"
                    />
                  </div>
                </div>
                <Button type="submit" disabled={loading} className="w-full bg-[#6366F1] hover:bg-[#4F46E5] text-white shadow-[0_0_15px_rgba(99,102,241,0.4)] active:scale-95" data-testid="register-submit-btn">
                  {loading ? 'Creating account...' : 'Create Account'}
                </Button>
              </form>
            </TabsContent>
          </Tabs>

          <div className="mt-6 pt-6 border-t border-white/10">
            <Button
              variant="outline"
              className="w-full border-white/20 text-white hover:bg-white/5 hover:border-white/40 text-sm"
              onClick={loginWithGoogle}
              data-testid="google-login-btn"
            >
              <svg className="w-4 h-4 mr-2" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
              Continue with Google
            </Button>
          </div>
        </div>

        <p className="text-[11px] text-white/20 text-center mt-6">
          Not financial advice. By signing up you agree to our Terms of Service.
        </p>
      </div>
    </div>
  );
}
