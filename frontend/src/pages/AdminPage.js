import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Shield, Users, Zap, Activity, Bell, Trash2, Server, Database, Wifi, WifiOff, BarChart3, CreditCard, Clock, UserCheck } from 'lucide-react';
import { toast } from 'sonner';

const ADMIN_EMAIL = "contact.developersingh@gmail.com";

export default function AdminPage() {
  const { api, user } = useAuth();
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [signals, setSignals] = useState([]);
  const [system, setSystem] = useState(null);
  const [plans, setPlans] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);

  // Plan assignment form
  const [planForm, setPlanForm] = useState({
    email: '', plan_name: 'basic', billing_cycle: 'weekly',
    duration_days: '', duration_hours: ''
  });

  const isAdmin = user?.email === ADMIN_EMAIL;

  useEffect(() => {
    if (isAdmin) fetchData();
    else setLoading(false);
  }, [isAdmin]);

  const fetchData = async () => {
    try {
      const [statsRes, usersRes, signalsRes, systemRes, plansRes] = await Promise.all([
        api.get('/admin/stats'),
        api.get('/admin/users'),
        api.get('/admin/signals?limit=30'),
        api.get('/admin/system'),
        api.get('/admin/plans'),
      ]);
      setStats(statsRes.data);
      setUsers(usersRes.data.users || []);
      setSignals(signalsRes.data.signals || []);
      setSystem(systemRes.data);
      setPlans(plansRes.data.plans || []);
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
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed to delete user'); }
  };

  const assignPlan = async () => {
    if (!planForm.email) { toast.error('Enter user email'); return; }
    try {
      const payload = {
        email: planForm.email,
        plan_name: planForm.plan_name,
        billing_cycle: planForm.billing_cycle,
      };
      if (planForm.duration_days) payload.duration_days = parseInt(planForm.duration_days);
      if (planForm.duration_hours) payload.duration_hours = parseInt(planForm.duration_hours);
      await api.post('/admin/plans/assign', payload);
      toast.success(`Plan assigned to ${planForm.email}`);
      setPlanForm({ email: '', plan_name: 'basic', billing_cycle: 'weekly', duration_days: '', duration_hours: '' });
      fetchData();
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed to assign plan'); }
  };

  const revokePlan = async (userId) => {
    if (!window.confirm('Revoke this user\'s plan?')) return;
    try {
      await api.delete(`/admin/plans/${userId}`);
      toast.success('Plan revoked');
      fetchData();
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed to revoke plan'); }
  };

  if (!isAdmin) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]" data-testid="admin-access-denied">
        <Card className="glass-panel border-white/10 max-w-md">
          <CardContent className="py-12 text-center">
            <Shield className="w-12 h-12 text-[#EF4444]/30 mx-auto mb-4" />
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
    { id: 'plans', label: 'Plans', icon: CreditCard },
    { id: 'signals', label: 'Signals', icon: Zap },
    { id: 'system', label: 'System', icon: Server },
  ];

  return (
    <div className="space-y-6 page-enter" data-testid="admin-page">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2" style={{ fontFamily: 'Manrope' }}>
          <Shield className="w-6 h-6 text-[#EF4444]" /> Admin Panel
        </h1>
        <p className="text-sm text-white/40 mt-1">Titan Trade platform management</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-white/10 pb-0" data-testid="admin-tabs">
        {tabs.map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium border-b-2 transition-all ${
              activeTab === tab.id
                ? 'border-[#EF4444] text-white bg-[#EF4444]/5'
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
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            <StatCard label="Total Users" value={stats.total_users} icon={Users} color="#6366F1" />
            <StatCard label="Total Signals" value={stats.total_signals} icon={Zap} color="#10B981" />
            <StatCard label="Total Trades" value={stats.total_trades} icon={BarChart3} color="#F59E0B" />
            <StatCard label="Active Alerts" value={stats.active_alerts} icon={Bell} color="#EF4444" />
            <StatCard label="Active Plans" value={plans.filter(p => p.status === 'active').length} icon={CreditCard} color="#00FFB2" />
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
                    <Badge className={stats.system_health.ticker_running ? 'bg-[#10B981]/10 text-[#10B981]' : 'bg-[#EF4444]/10 text-[#EF4444]'}>
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
          {users.map(u => {
            const userPlan = plans.find(p => p.user_id === u.user_id && p.status === 'active');
            return (
              <Card key={u.user_id} className="glass-panel border-white/10" data-testid={`admin-user-${u.user_id}`}>
                <CardContent className="p-4 flex items-center justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <p className="text-sm text-white font-medium">{u.name || 'Unnamed'}</p>
                      <Badge variant="outline" className="text-[9px] border-white/20 text-white/40">{u.auth_type || 'jwt'}</Badge>
                      {u.email === ADMIN_EMAIL && <Badge className="bg-[#EF4444]/10 text-[#EF4444] text-[9px]">Admin</Badge>}
                      {userPlan && (
                        <Badge className="bg-[#F59E0B]/10 text-[#F59E0B] text-[9px] capitalize">{userPlan.plan_name}</Badge>
                      )}
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
            );
          })}
        </div>
      )}

      {/* Plans Tab */}
      {activeTab === 'plans' && (
        <div className="space-y-6">
          {/* Assign Plan Form */}
          <Card className="glass-panel border-white/10 border-l-2 border-l-[#F59E0B]" data-testid="assign-plan-form">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm text-white/80 flex items-center gap-2">
                <UserCheck className="w-4 h-4 text-[#F59E0B]" /> Assign Plan to User
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                <div className="col-span-2 sm:col-span-1">
                  <label className="text-[10px] text-white/40 mb-1 block">User Email</label>
                  <Input value={planForm.email} onChange={e => setPlanForm(p => ({...p, email: e.target.value}))}
                    placeholder="user@email.com" className="bg-black/50 border-white/10 text-white text-sm" data-testid="plan-email-input" />
                </div>
                <div>
                  <label className="text-[10px] text-white/40 mb-1 block">Plan</label>
                  <Select value={planForm.plan_name} onValueChange={v => setPlanForm(p => ({...p, plan_name: v}))}>
                    <SelectTrigger className="bg-black/50 border-white/10 text-white text-sm" data-testid="plan-name-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-[#09090B] border-white/10">
                      <SelectItem value="free">Free</SelectItem>
                      <SelectItem value="basic">Basic</SelectItem>
                      <SelectItem value="pro">Pro</SelectItem>
                      <SelectItem value="titan">Titan</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-[10px] text-white/40 mb-1 block">Billing Cycle</label>
                  <Select value={planForm.billing_cycle} onValueChange={v => setPlanForm(p => ({...p, billing_cycle: v}))}>
                    <SelectTrigger className="bg-black/50 border-white/10 text-white text-sm" data-testid="plan-cycle-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-[#09090B] border-white/10">
                      <SelectItem value="weekly">Weekly (7 days)</SelectItem>
                      <SelectItem value="monthly">Monthly (30 days)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-[10px] text-white/40 mb-1 block">Custom Days</label>
                  <Input type="number" value={planForm.duration_days} onChange={e => setPlanForm(p => ({...p, duration_days: e.target.value, duration_hours: ''}))}
                    placeholder="Optional" className="bg-black/50 border-white/10 text-white text-sm" data-testid="plan-days-input" />
                </div>
                <div>
                  <label className="text-[10px] text-white/40 mb-1 block">Custom Hours</label>
                  <Input type="number" value={planForm.duration_hours} onChange={e => setPlanForm(p => ({...p, duration_hours: e.target.value, duration_days: ''}))}
                    placeholder="Optional" className="bg-black/50 border-white/10 text-white text-sm" data-testid="plan-hours-input" />
                </div>
              </div>
              <Button onClick={assignPlan} className="bg-[#F59E0B] hover:bg-[#F59E0B]/80 text-black text-xs font-semibold px-6"
                data-testid="assign-plan-btn">
                <UserCheck className="w-3.5 h-3.5 mr-1.5" /> Assign Plan
              </Button>
            </CardContent>
          </Card>

          {/* Active Plans List */}
          <div className="space-y-3">
            <p className="text-xs text-white/40">{plans.length} plan assignments</p>
            {plans.length === 0 ? (
              <Card className="glass-panel border-white/10">
                <CardContent className="py-8 text-center">
                  <CreditCard className="w-8 h-8 text-white/10 mx-auto mb-2" />
                  <p className="text-xs text-white/40">No plans assigned yet</p>
                </CardContent>
              </Card>
            ) : (
              plans.map(plan => (
                <Card key={plan.user_id} className="glass-panel border-white/10" data-testid={`plan-${plan.user_id}`}>
                  <CardContent className="p-4 flex items-center justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <p className="text-sm text-white font-medium">{plan.email}</p>
                        <Badge className={`text-[9px] capitalize ${
                          plan.plan_name === 'titan' ? 'bg-[#F59E0B]/10 text-[#F59E0B]' :
                          plan.plan_name === 'pro' ? 'bg-[#10B981]/10 text-[#10B981]' :
                          plan.plan_name === 'basic' ? 'bg-[#6366F1]/10 text-[#6366F1]' :
                          'bg-white/10 text-white/40'
                        }`}>{plan.plan_name}</Badge>
                        <Badge variant="outline" className="text-[9px] border-white/20 text-white/40">{plan.billing_cycle}</Badge>
                        <Badge className={`text-[9px] ${
                          plan.status === 'active' ? 'bg-[#10B981]/10 text-[#10B981]' :
                          plan.status === 'expired' ? 'bg-[#EAB308]/10 text-[#EAB308]' :
                          'bg-[#EF4444]/10 text-[#EF4444]'
                        }`}>{plan.status}</Badge>
                      </div>
                      <div className="flex items-center gap-3 text-[10px] text-white/30">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" /> Starts: {new Date(plan.starts_at).toLocaleString()}
                        </span>
                        <span className="flex items-center gap-1">
                          Expires: {new Date(plan.expires_at).toLocaleString()}
                        </span>
                      </div>
                    </div>
                    {plan.status === 'active' && (
                      <Button variant="ghost" size="sm" onClick={() => revokePlan(plan.user_id)}
                        className="text-white/30 hover:text-red-400 hover:bg-red-500/10"
                        data-testid={`revoke-plan-${plan.user_id}`}>
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    )}
                  </CardContent>
                </Card>
              ))
            )}
          </div>
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
                      <Badge className={`text-[9px] ${sig.direction === 'BUY' ? 'bg-[#10B981]/10 text-[#10B981]' : 'bg-[#EF4444]/10 text-[#EF4444]'}`}>
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
                    {feed.status === 'active' ? <Wifi className="w-4 h-4 text-[#10B981]" /> : <WifiOff className="w-4 h-4 text-[#EF4444]" />}
                    <div>
                      <p className="text-sm text-white font-medium capitalize">{key}</p>
                      <p className="text-[10px] text-white/40">{feed.pairs || feed.assets} instruments | Refresh: {feed.refresh_rate}</p>
                    </div>
                  </div>
                  <Badge className={feed.status === 'active' ? 'bg-[#10B981]/10 text-[#10B981]' : 'bg-[#EF4444]/10 text-[#EF4444]'}>
                    {feed.status}
                  </Badge>
                </div>
              ))}
            </CardContent>
          </Card>
          <Card className="glass-panel border-white/10">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-white/80 flex items-center gap-2">
                <Activity className="w-4 h-4 text-[#F59E0B]" /> Market Status
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                {Object.entries(system.market_status).map(([market, status]) => (
                  <div key={market} className="text-center p-3 rounded-lg bg-white/[0.02] border border-white/5">
                    <p className="text-xs text-white/40 uppercase mb-1">{market}</p>
                    <Badge className={status.open ? 'bg-[#10B981]/10 text-[#10B981]' : 'bg-[#EF4444]/10 text-[#EF4444]'}>
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
