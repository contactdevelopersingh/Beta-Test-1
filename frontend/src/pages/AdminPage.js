import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Shield, Users, Zap, Activity, Bell, Trash2, Server, Database, Wifi, WifiOff, BarChart3, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';

const ADMIN_EMAIL = "contact.developersingh@gmail.com";

export default function AdminPage() {
  const { api, user } = useAuth();
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [signals, setSignals] = useState([]);
  const [system, setSystem] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);

  const isAdmin = user?.email === ADMIN_EMAIL;

  useEffect(() => {
    if (isAdmin) fetchData();
    else setLoading(false);
  }, [isAdmin]);

  const fetchData = async () => {
    try {
      const [statsRes, usersRes, signalsRes, systemRes] = await Promise.all([
        api.get('/admin/stats'),
        api.get('/admin/users'),
        api.get('/admin/signals?limit=30'),
        api.get('/admin/system'),
      ]);
      setStats(statsRes.data);
      setUsers(usersRes.data.users || []);
      setSignals(signalsRes.data.signals || []);
      setSystem(systemRes.data);
    } catch (e) {
      console.error(e);
      toast.error('Failed to load admin data');
    }
    setLoading(false);
  };

  const deleteUser = async (userId) => {
    if (!window.confirm('Delete this user and all their data? This cannot be undone.')) return;
    try {
      await api.delete(`/admin/users/${userId}`);
      toast.success('User deleted');
      fetchData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to delete user');
    }
  };

  if (!isAdmin) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]" data-testid="admin-access-denied">
        <Card className="glass-panel border-white/10 max-w-md">
          <CardContent className="py-12 text-center">
            <Shield className="w-12 h-12 text-[#FF2E2E]/30 mx-auto mb-4" />
            <h2 className="text-lg font-bold text-white mb-2">Access Denied</h2>
            <p className="text-sm text-white/40">Admin panel is restricted to authorized personnel only.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (loading) {
    return <div className="space-y-4">{[1,2,3,4].map(i => <div key={i} className="h-32 rounded-xl skeleton-shimmer" />)}</div>;
  }

  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'users', label: 'Users', icon: Users },
    { id: 'signals', label: 'Signals', icon: Zap },
    { id: 'system', label: 'System', icon: Server },
  ];

  return (
    <div className="space-y-6" data-testid="admin-page">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2" style={{ fontFamily: 'Manrope' }}>
          <Shield className="w-6 h-6 text-[#FF2E2E]" /> Admin Panel
        </h1>
        <p className="text-sm text-white/40 mt-1">Platform management & monitoring</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-white/10 pb-0" data-testid="admin-tabs">
        {tabs.map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium border-b-2 transition-all ${
              activeTab === tab.id
                ? 'border-[#FF2E2E] text-white bg-[#FF2E2E]/5'
                : 'border-transparent text-white/40 hover:text-white/60'
            }`}
            data-testid={`admin-tab-${tab.id}`}>
            <tab.icon className="w-3.5 h-3.5" /> {tab.label}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && stats && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <StatCard label="Total Users" value={stats.total_users} icon={Users} color="#6366F1" />
            <StatCard label="Total Signals" value={stats.total_signals} icon={Zap} color="#00FF94" />
            <StatCard label="Total Trades" value={stats.total_trades} icon={BarChart3} color="#FFD700" />
            <StatCard label="Active Alerts" value={stats.active_alerts} icon={Bell} color="#FF2E2E" />
          </div>
          {stats.system_health && (
            <Card className="glass-panel border-white/10">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-white/80">System Health</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
                  <div>
                    <p className="text-white/40">Crypto Pairs</p>
                    <p className="text-white font-data text-lg">{stats.system_health.crypto_pairs}</p>
                  </div>
                  <div>
                    <p className="text-white/40">Forex Pairs</p>
                    <p className="text-white font-data text-lg">{stats.system_health.forex_pairs}</p>
                  </div>
                  <div>
                    <p className="text-white/40">Indian Assets</p>
                    <p className="text-white font-data text-lg">{stats.system_health.indian_assets}</p>
                  </div>
                  <div>
                    <p className="text-white/40">Ticker Status</p>
                    <Badge className={stats.system_health.ticker_running ? 'bg-[#00FF94]/10 text-[#00FF94]' : 'bg-[#FF2E2E]/10 text-[#FF2E2E]'}>
                      {stats.system_health.ticker_running ? 'Running' : 'Stopped'}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Users Tab */}
      {activeTab === 'users' && (
        <div className="space-y-3">
          <p className="text-xs text-white/40">{users.length} registered users</p>
          {users.map(u => (
            <Card key={u.user_id} className="glass-panel border-white/10" data-testid={`admin-user-${u.user_id}`}>
              <CardContent className="p-4 flex items-center justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <p className="text-sm text-white font-medium">{u.name || 'Unnamed'}</p>
                    <Badge variant="outline" className="text-[9px] border-white/20 text-white/40">{u.auth_type || 'jwt'}</Badge>
                    {u.email === ADMIN_EMAIL && <Badge className="bg-[#FF2E2E]/10 text-[#FF2E2E] text-[9px]">Admin</Badge>}
                  </div>
                  <p className="text-[10px] text-white/40">{u.email}</p>
                  <p className="text-[10px] text-white/30">ID: {u.user_id} | Joined: {new Date(u.created_at).toLocaleDateString()}</p>
                </div>
                {u.email !== ADMIN_EMAIL && (
                  <Button variant="ghost" size="sm" onClick={() => deleteUser(u.user_id)}
                    className="text-white/30 hover:text-red-400 hover:bg-red-500/10"
                    data-testid={`delete-user-${u.user_id}`}>
                    <Trash2 className="w-4 h-4" />
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Signals Tab */}
      {activeTab === 'signals' && (
        <div className="space-y-3">
          <p className="text-xs text-white/40">Last {signals.length} signals generated</p>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-white/40 border-b border-white/10">
                  <th className="text-left py-2 px-3">Asset</th>
                  <th className="text-left py-2 px-3">Direction</th>
                  <th className="text-left py-2 px-3">Confidence</th>
                  <th className="text-left py-2 px-3">Grade</th>
                  <th className="text-left py-2 px-3">Strategy</th>
                  <th className="text-left py-2 px-3">User</th>
                  <th className="text-left py-2 px-3">Date</th>
                </tr>
              </thead>
              <tbody>
                {signals.map(sig => (
                  <tr key={sig.signal_id} className="border-b border-white/5 hover:bg-white/[0.02]">
                    <td className="py-2 px-3 text-white">{sig.asset_name}</td>
                    <td className="py-2 px-3">
                      <Badge className={`text-[9px] ${sig.direction === 'BUY' ? 'bg-[#00FF94]/10 text-[#00FF94]' : 'bg-[#FF2E2E]/10 text-[#FF2E2E]'}`}>
                        {sig.direction}
                      </Badge>
                    </td>
                    <td className="py-2 px-3 font-data text-white/70">{sig.confidence}%</td>
                    <td className="py-2 px-3 text-[#6366F1]">{sig.grade}</td>
                    <td className="py-2 px-3 text-white/50">{sig.strategy_used || '-'}</td>
                    <td className="py-2 px-3 text-white/40">{sig.user_id?.slice(0, 15)}</td>
                    <td className="py-2 px-3 text-white/30">{new Date(sig.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* System Tab */}
      {activeTab === 'system' && system && (
        <div className="space-y-4">
          <Card className="glass-panel border-white/10">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-white/80 flex items-center gap-2">
                <Database className="w-4 h-4 text-[#6366F1]" /> Data Feeds
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {Object.entries(system.data_feeds).map(([key, feed]) => (
                <div key={key} className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/5">
                  <div className="flex items-center gap-3">
                    {feed.status === 'active' ? <Wifi className="w-4 h-4 text-[#00FF94]" /> : <WifiOff className="w-4 h-4 text-[#FF2E2E]" />}
                    <div>
                      <p className="text-sm text-white font-medium capitalize">{key}</p>
                      <p className="text-[10px] text-white/40">{feed.pairs || feed.assets} instruments | Refresh: {feed.refresh_rate}</p>
                    </div>
                  </div>
                  <Badge className={feed.status === 'active' ? 'bg-[#00FF94]/10 text-[#00FF94]' : 'bg-[#FF2E2E]/10 text-[#FF2E2E]'}>
                    {feed.status}
                  </Badge>
                </div>
              ))}
            </CardContent>
          </Card>
          <Card className="glass-panel border-white/10">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-white/80 flex items-center gap-2">
                <Activity className="w-4 h-4 text-[#FFD700]" /> Market Status
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                {Object.entries(system.market_status).map(([market, status]) => (
                  <div key={market} className="text-center p-3 rounded-lg bg-white/[0.02] border border-white/5">
                    <p className="text-xs text-white/40 uppercase mb-1">{market}</p>
                    <Badge className={status.open ? 'bg-[#00FF94]/10 text-[#00FF94]' : 'bg-[#FF2E2E]/10 text-[#FF2E2E]'}>
                      {status.label}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value, icon: Icon, color }) {
  return (
    <Card className="glass-panel border-white/10">
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-2">
          <p className="text-[10px] text-white/40 uppercase tracking-wider">{label}</p>
          <Icon className="w-4 h-4" style={{ color }} />
        </div>
        <p className="text-2xl font-bold font-data text-white">{value?.toLocaleString()}</p>
      </CardContent>
    </Card>
  );
}
