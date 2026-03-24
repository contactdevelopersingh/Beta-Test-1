import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import { Separator } from '../components/ui/separator';
import { Avatar, AvatarFallback } from '../components/ui/avatar';
import { User, Bell, Shield, Palette, Save, LogOut } from 'lucide-react';
import { toast } from 'sonner';

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState({ signals: true, portfolio: true, news: false, priceAlerts: true });

  const handleSave = () => {
    toast.success('Settings saved');
  };

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <div className="space-y-6 max-w-3xl" data-testid="settings-page">
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
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white">Authentication Method</p>
              <p className="text-xs text-white/30">{user?.auth_type === 'google' ? 'Google OAuth' : 'Email & Password'}</p>
            </div>
            <span className="text-xs text-[#00FF94] bg-[#00FF94]/10 px-2 py-1 rounded">Active</span>
          </div>
          <Separator className="bg-white/5" />
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white">Two-Factor Authentication</p>
              <p className="text-xs text-white/30">Add extra security to your account</p>
            </div>
            <Button variant="outline" size="sm" className="border-white/20 text-white/60 text-xs" disabled data-testid="enable-2fa-btn">Coming Soon</Button>
          </div>
        </CardContent>
      </Card>

      <Button className="bg-[#6366F1] hover:bg-[#4F46E5] text-white shadow-[0_0_15px_rgba(99,102,241,0.4)] active:scale-95 text-xs uppercase tracking-wide font-semibold" onClick={handleSave} data-testid="save-settings-btn">
        <Save className="w-3.5 h-3.5 mr-1.5" /> Save Changes
      </Button>

      {/* Logout */}
      <Card className="glass-panel border-white/10 border-l-2 border-l-[#FF2E2E]" data-testid="logout-card">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm text-white/80 flex items-center gap-2">
            <LogOut className="w-4 h-4 text-[#FF2E2E]" /> Session
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
              className="border-[#FF2E2E]/30 text-[#FF2E2E] hover:bg-[#FF2E2E]/10 hover:border-[#FF2E2E]/50 text-xs"
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
