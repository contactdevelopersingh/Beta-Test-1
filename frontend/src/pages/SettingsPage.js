import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import { Separator } from '../components/ui/separator';
import { Avatar, AvatarFallback } from '../components/ui/avatar';
import { User, Bell, Shield, Palette, Save, LogOut, Loader2, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';

export default function SettingsPage() {
  const { user, api, logout } = useAuth();
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState({ signals: true, portfolio: true, news: false, priceAlerts: true });
  const [twoFAEnabled, setTwoFAEnabled] = useState(false);
  const [twoFASetup, setTwoFASetup] = useState(null);
  const [twoFACode, setTwoFACode] = useState('');
  const [twoFALoading, setTwoFALoading] = useState(false);
  const [disableCode, setDisableCode] = useState('');

  useEffect(() => {
    api.get('/auth/2fa/status').then(r => setTwoFAEnabled(r.data.two_fa_enabled)).catch(() => {});
  }, [api]);

  const handleSave = () => {
    toast.success('Settings saved');
  };

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const setup2FA = async () => {
    setTwoFALoading(true);
    try {
      const res = await api.post('/auth/2fa/setup');
      setTwoFASetup(res.data);
    } catch (e) {
      toast.error('Failed to setup 2FA');
    }
    setTwoFALoading(false);
  };

  const verify2FA = async () => {
    if (!twoFACode || twoFACode.length !== 6) {
      toast.error('Enter a 6-digit code');
      return;
    }
    setTwoFALoading(true);
    try {
      await api.post('/auth/2fa/verify', { code: twoFACode });
      setTwoFAEnabled(true);
      setTwoFASetup(null);
      setTwoFACode('');
      toast.success('2FA enabled successfully!');
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Invalid code');
    }
    setTwoFALoading(false);
  };

  const disable2FA = async () => {
    if (!disableCode || disableCode.length !== 6) {
      toast.error('Enter your current 2FA code');
      return;
    }
    setTwoFALoading(true);
    try {
      await api.post('/auth/2fa/disable', { code: disableCode });
      setTwoFAEnabled(false);
      setDisableCode('');
      toast.success('2FA disabled');
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Invalid code');
    }
    setTwoFALoading(false);
  };

  return (
    <div className="space-y-6 max-w-3xl page-enter" data-testid="settings-page">
      <div>
        <h1 className="text-2xl font-bold text-white" style={{ fontFamily: 'Manrope' }}>Settings</h1>
        <p className="text-sm text-white/40 mt-1">Manage your account and preferences</p>
      </div>

      {/* Profile */}
      <Card className="glass-panel border-white/10" data-testid="profile-settings-card">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm text-white/80 flex items-center gap-2">
            <User className="w-4 h-4 text-[#6366F1]" /> Profile
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            <Avatar className="w-16 h-16">
              <AvatarFallback className="bg-[#6366F1]/20 text-[#6366F1] text-xl">
                {user?.name?.charAt(0)?.toUpperCase() || 'U'}
              </AvatarFallback>
            </Avatar>
            <div>
              <h3 className="text-base font-semibold text-white">{user?.name || 'User'}</h3>
              <p className="text-sm text-white/40">{user?.email}</p>
              <p className="text-xs text-[#6366F1] mt-1">Pro Account</p>
            </div>
          </div>
          <Separator className="bg-white/5" />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <Label className="text-xs text-white/60">Display Name</Label>
              <Input className="bg-black/50 border-white/10 text-white text-sm mt-1" defaultValue={user?.name || ''} data-testid="display-name-input" />
            </div>
            <div>
              <Label className="text-xs text-white/60">Email</Label>
              <Input className="bg-black/50 border-white/10 text-white/40 text-sm mt-1" value={user?.email || ''} disabled data-testid="email-input" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Notifications */}
      <Card className="glass-panel border-white/10" data-testid="notification-settings-card">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm text-white/80 flex items-center gap-2">
            <Bell className="w-4 h-4 text-[#6366F1]" /> Notifications
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {[
            { key: 'signals', label: 'Signal Alerts', desc: 'Get notified when new AI signals are generated' },
            { key: 'portfolio', label: 'Portfolio Updates', desc: 'Receive P&L change notifications' },
            { key: 'priceAlerts', label: 'Price Alerts', desc: 'Alert when watched assets hit target prices' },
            { key: 'news', label: 'Market News', desc: 'Breaking news and high-impact events' },
          ].map(item => (
            <div key={item.key} className="flex items-center justify-between">
              <div>
                <p className="text-sm text-white">{item.label}</p>
                <p className="text-xs text-white/30">{item.desc}</p>
              </div>
              <Switch
                checked={notifications[item.key]}
                onCheckedChange={v => setNotifications({ ...notifications, [item.key]: v })}
                data-testid={`notification-${item.key}-switch`}
              />
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Appearance */}
      <Card className="glass-panel border-white/10" data-testid="appearance-settings-card">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm text-white/80 flex items-center gap-2">
            <Palette className="w-4 h-4 text-[#6366F1]" /> Appearance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white">Dark Mode</p>
              <p className="text-xs text-white/30">Titan Trade is optimized for dark mode</p>
            </div>
            <Switch checked={true} disabled data-testid="dark-mode-switch" />
          </div>
        </CardContent>
      </Card>

      {/* Security */}
      <Card className="glass-panel border-white/10" data-testid="security-settings-card">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm text-white/80 flex items-center gap-2">
            <Shield className="w-4 h-4 text-[#6366F1]" /> Security
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white">Authentication Method</p>
              <p className="text-xs text-white/30">{user?.auth_type === 'google' ? 'Google OAuth' : 'Email & Password'}</p>
            </div>
            <span className="text-xs text-[#10B981] bg-[#10B981]/10 px-2 py-1 rounded">Active</span>
          </div>
          <Separator className="bg-white/5" />
          <div>
            <div className="flex items-center justify-between mb-3">
              <div>
                <p className="text-sm text-white">Two-Factor Authentication (2FA)</p>
                <p className="text-xs text-white/30">
                  {twoFAEnabled ? 'Your account is protected with 2FA' : 'Add extra security with TOTP authenticator'}
                </p>
              </div>
              {twoFAEnabled ? (
                <span className="flex items-center gap-1 text-xs text-[#10B981] bg-[#10B981]/10 px-2 py-1 rounded">
                  <CheckCircle2 className="w-3 h-3" /> Enabled
                </span>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  className="border-[#6366F1]/30 text-[#6366F1] hover:bg-[#6366F1]/10 text-xs"
                  onClick={setup2FA}
                  disabled={twoFALoading}
                  data-testid="enable-2fa-btn"
                >
                  {twoFALoading ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : null}
                  Enable 2FA
                </Button>
              )}
            </div>

            {/* 2FA Setup Flow */}
            {twoFASetup && !twoFAEnabled && (
              <div className="p-4 rounded-lg bg-white/[0.02] border border-white/10 space-y-3">
                <p className="text-xs text-white/60">1. Scan this QR code with Google Authenticator or Authy:</p>
                <div className="flex justify-center">
                  <img src={twoFASetup.qr_code} alt="2FA QR Code" className="w-40 h-40 rounded-lg" data-testid="2fa-qr-code" />
                </div>
                <p className="text-[10px] text-white/30 text-center break-all">Manual key: {twoFASetup.secret}</p>
                <p className="text-xs text-white/60">2. Enter the 6-digit code from your app:</p>
                <div className="flex gap-2">
                  <Input
                    type="text"
                    maxLength={6}
                    placeholder="000000"
                    value={twoFACode}
                    onChange={e => setTwoFACode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    className="bg-black/50 border-white/10 text-white text-center text-lg tracking-widest font-data w-40"
                    data-testid="2fa-code-input"
                  />
                  <Button
                    onClick={verify2FA}
                    disabled={twoFALoading || twoFACode.length !== 6}
                    className="bg-[#6366F1] hover:bg-[#4F46E5] text-white text-xs"
                    data-testid="verify-2fa-btn"
                  >
                    {twoFALoading ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Verify'}
                  </Button>
                </div>
              </div>
            )}

            {/* Disable 2FA */}
            {twoFAEnabled && (
              <div className="flex items-center gap-2">
                <Input
                  type="text"
                  maxLength={6}
                  placeholder="Enter code to disable"
                  value={disableCode}
                  onChange={e => setDisableCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  className="bg-black/50 border-white/10 text-white text-sm w-48"
                />
                <Button
                  variant="outline"
                  size="sm"
                  className="border-red-500/30 text-red-400 hover:bg-red-500/10 text-xs"
                  onClick={disable2FA}
                  disabled={twoFALoading}
                  data-testid="disable-2fa-btn"
                >
                  Disable 2FA
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <Button className="bg-[#6366F1] hover:bg-[#4F46E5] text-white shadow-[0_0_15px_rgba(99,102,241,0.4)] active:scale-95 text-xs uppercase tracking-wide font-semibold" onClick={handleSave} data-testid="save-settings-btn">
        <Save className="w-3.5 h-3.5 mr-1.5" /> Save Changes
      </Button>

      {/* Logout */}
      <Card className="glass-panel border-white/10 border-l-2 border-l-[#EF4444]" data-testid="logout-card">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm text-white/80 flex items-center gap-2">
            <LogOut className="w-4 h-4 text-[#EF4444]" /> Session
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white">Log Out</p>
              <p className="text-xs text-white/30">Sign out of your Titan Trade account</p>
            </div>
            <Button
              variant="outline"
              className="border-[#EF4444]/30 text-[#EF4444] hover:bg-[#EF4444]/10 hover:border-[#EF4444]/50 text-xs"
              onClick={handleLogout}
              data-testid="logout-btn"
            >
              <LogOut className="w-3.5 h-3.5 mr-1.5" /> Log Out
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
