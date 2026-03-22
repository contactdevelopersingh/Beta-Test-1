import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useMarketStream } from '../hooks/useMarketStream';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Bell, Plus, Trash2, ArrowUp, ArrowDown, CheckCircle2, Clock, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';

const ALERT_ASSETS = {
  crypto: [
    { id: 'bitcoin', name: 'Bitcoin' }, { id: 'ethereum', name: 'Ethereum' },
    { id: 'solana', name: 'Solana' }, { id: 'binancecoin', name: 'BNB' },
    { id: 'ripple', name: 'XRP' }, { id: 'dogecoin', name: 'Dogecoin' },
    { id: 'cardano', name: 'Cardano' }, { id: 'tether', name: 'Tether' },
  ],
  forex: [
    { id: 'eurusd', name: 'EUR/USD' }, { id: 'gbpusd', name: 'GBP/USD' },
    { id: 'usdjpy', name: 'USD/JPY' }, { id: 'xauusd', name: 'Gold (XAU/USD)' },
    { id: 'xagusd', name: 'Silver (XAG/USD)' },
  ],
  indian: [
    { id: 'nifty50', name: 'NIFTY 50' }, { id: 'sensex', name: 'SENSEX' },
    { id: 'banknifty', name: 'NIFTY Bank' }, { id: 'reliance', name: 'Reliance' },
    { id: 'tcs', name: 'TCS' }, { id: 'infy', name: 'Infosys' },
    { id: 'hdfcbank', name: 'HDFC Bank' }, { id: 'sbin', name: 'SBI' },
  ],
};

export default function AlertsPage() {
  const { api } = useAuth();
  const { crypto, forex, indian, connected } = useMarketStream(true, 2000);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState({ asset_type: 'crypto', asset_id: 'bitcoin', condition: 'above', target_price: '', note: '' });

  const fetchAlerts = async () => {
    try {
      const res = await api.get('/alerts');
      setAlerts(res.data.alerts || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  useEffect(() => { fetchAlerts(); }, []);

  const createAlert = async () => {
    if (!form.target_price) { toast.error('Enter a target price'); return; }
    const assets = ALERT_ASSETS[form.asset_type] || [];
    const asset = assets.find(a => a.id === form.asset_id);
    try {
      const res = await api.post('/alerts', {
        asset_id: form.asset_id,
        asset_name: asset?.name || form.asset_id,
        asset_type: form.asset_type,
        condition: form.condition,
        target_price: parseFloat(form.target_price),
        note: form.note || null,
      });
      setAlerts(prev => [res.data, ...prev]);
      setDialogOpen(false);
      setForm({ asset_type: 'crypto', asset_id: 'bitcoin', condition: 'above', target_price: '', note: '' });
      toast.success('Alert created');
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed'); }
  };

  const deleteAlert = async (alertId) => {
    try {
      await api.delete(`/alerts/${alertId}`);
      setAlerts(prev => prev.filter(a => a.alert_id !== alertId));
      toast.success('Alert deleted');
    } catch { toast.error('Failed'); }
  };

  const allPrices = [...crypto, ...forex, ...indian];
  const getCurrentPrice = (assetId) => {
    const item = allPrices.find(p => p.id === assetId);
    return item?.price || null;
  };

  const activeAlerts = alerts.filter(a => a.status === 'active');
  const triggeredAlerts = alerts.filter(a => a.status === 'triggered');
  const currentAssets = ALERT_ASSETS[form.asset_type] || [];

  return (
    <div className="space-y-6" data-testid="alerts-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white" style={{ fontFamily: 'Manrope' }}>Price Alerts</h1>
          <p className="text-sm text-white/40 mt-1">Get notified when prices hit your targets</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-white/5 border border-white/10">
            <div className={`live-dot ${connected ? '' : 'bg-red-500'}`} />
            <span className="text-[10px] font-data text-white/50">{connected ? 'MONITORING' : 'OFFLINE'}</span>
          </div>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-[#6366F1] hover:bg-[#4F46E5] text-white text-xs shadow-[0_0_15px_rgba(99,102,241,0.4)] active:scale-95" data-testid="create-alert-btn">
                <Plus className="w-3.5 h-3.5 mr-1.5" /> New Alert
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-[#09090B] border-white/10 text-white">
              <DialogHeader><DialogTitle className="text-white">Create Price Alert</DialogTitle></DialogHeader>
              <div className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-xs text-white/60">Market</Label>
                    <Select value={form.asset_type} onValueChange={v => setForm({ ...form, asset_type: v, asset_id: ALERT_ASSETS[v]?.[0]?.id || '' })}>
                      <SelectTrigger className="bg-black/50 border-white/10 text-white text-sm mt-1" data-testid="alert-market-select"><SelectValue /></SelectTrigger>
                      <SelectContent className="bg-[#09090B] border-white/10">
                        <SelectItem value="crypto">Crypto</SelectItem>
                        <SelectItem value="forex">Forex</SelectItem>
                        <SelectItem value="indian">Indian</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-xs text-white/60">Asset</Label>
                    <Select value={form.asset_id} onValueChange={v => setForm({ ...form, asset_id: v })}>
                      <SelectTrigger className="bg-black/50 border-white/10 text-white text-sm mt-1" data-testid="alert-asset-select"><SelectValue /></SelectTrigger>
                      <SelectContent className="bg-[#09090B] border-white/10">
                        {currentAssets.map(a => <SelectItem key={a.id} value={a.id}>{a.name}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-xs text-white/60">Condition</Label>
                    <Select value={form.condition} onValueChange={v => setForm({ ...form, condition: v })}>
                      <SelectTrigger className="bg-black/50 border-white/10 text-white text-sm mt-1" data-testid="alert-condition-select"><SelectValue /></SelectTrigger>
                      <SelectContent className="bg-[#09090B] border-white/10">
                        <SelectItem value="above">Price Goes Above</SelectItem>
                        <SelectItem value="below">Price Goes Below</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-xs text-white/60">Target Price ($)</Label>
                    <Input type="number" step="any" className="bg-black/50 border-white/10 text-white text-sm mt-1" placeholder="0.00"
                      value={form.target_price} onChange={e => setForm({ ...form, target_price: e.target.value })} data-testid="alert-price-input" />
                  </div>
                </div>
                {getCurrentPrice(form.asset_id) && (
                  <div className="px-3 py-2 rounded-lg bg-white/5 border border-white/10">
                    <span className="text-[10px] text-white/40">Current Price: </span>
                    <span className="text-sm font-data text-[#6366F1] font-medium">${getCurrentPrice(form.asset_id)?.toLocaleString()}</span>
                  </div>
                )}
                <div>
                  <Label className="text-xs text-white/60">Note (optional)</Label>
                  <Input className="bg-black/50 border-white/10 text-white text-sm mt-1" placeholder="e.g., Breakout entry"
                    value={form.note} onChange={e => setForm({ ...form, note: e.target.value })} data-testid="alert-note-input" />
                </div>
                <Button className="w-full bg-[#6366F1] hover:bg-[#4F46E5] text-white active:scale-95" onClick={createAlert} data-testid="confirm-create-alert-btn">Create Alert</Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="glass-panel border-white/10" data-testid="active-alerts-count">
          <CardContent className="p-5 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-[#6366F1]/10 flex items-center justify-center"><Clock className="w-5 h-5 text-[#6366F1]" /></div>
            <div>
              <p className="text-[10px] text-white/40 uppercase tracking-wider">Active</p>
              <p className="text-lg font-bold text-white font-data">{activeAlerts.length}</p>
            </div>
          </CardContent>
        </Card>
        <Card className="glass-panel border-white/10" data-testid="triggered-alerts-count">
          <CardContent className="p-5 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-[#00FF94]/10 flex items-center justify-center"><CheckCircle2 className="w-5 h-5 text-[#00FF94]" /></div>
            <div>
              <p className="text-[10px] text-white/40 uppercase tracking-wider">Triggered</p>
              <p className="text-lg font-bold text-white font-data">{triggeredAlerts.length}</p>
            </div>
          </CardContent>
        </Card>
        <Card className="glass-panel border-white/10">
          <CardContent className="p-5 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-[#EAB308]/10 flex items-center justify-center"><Bell className="w-5 h-5 text-[#EAB308]" /></div>
            <div>
              <p className="text-[10px] text-white/40 uppercase tracking-wider">Total Alerts</p>
              <p className="text-lg font-bold text-white font-data">{alerts.length}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Active Alerts */}
      <Card className="glass-panel border-white/10" data-testid="active-alerts-list">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm text-white/80 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-[#EAB308]" /> Active Alerts
          </CardTitle>
        </CardHeader>
        <CardContent>
          {activeAlerts.length === 0 ? (
            <div className="py-8 text-center">
              <Bell className="w-8 h-8 text-white/10 mx-auto mb-2" />
              <p className="text-xs text-white/30">No active alerts. Create one to get started.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {activeAlerts.map(alert => {
                const curPrice = getCurrentPrice(alert.asset_id);
                const distPct = curPrice ? ((alert.target_price - curPrice) / curPrice * 100) : null;
                return (
                  <div key={alert.alert_id} className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/5 market-row" data-testid={`alert-${alert.alert_id}`}>
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${alert.condition === 'above' ? 'bg-[#00FF94]/10' : 'bg-[#FF2E2E]/10'}`}>
                        {alert.condition === 'above' ? <ArrowUp className="w-4 h-4 text-[#00FF94]" /> : <ArrowDown className="w-4 h-4 text-[#FF2E2E]" />}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-white font-medium">{alert.asset_name}</span>
                          <Badge variant="outline" className="text-[8px] border-white/10 text-white/30 py-0 h-4">{alert.asset_type}</Badge>
                        </div>
                        <p className="text-[10px] text-white/40">
                          {alert.condition === 'above' ? 'Above' : 'Below'} <span className="font-data text-[#6366F1]">${alert.target_price.toLocaleString()}</span>
                          {curPrice && <span className="ml-2">Now: <span className="font-data text-white/60">${curPrice.toLocaleString()}</span></span>}
                          {distPct !== null && <span className="ml-2 font-data">{distPct > 0 ? '+' : ''}{distPct.toFixed(2)}% away</span>}
                        </p>
                        {alert.note && <p className="text-[10px] text-white/30 mt-0.5">{alert.note}</p>}
                      </div>
                    </div>
                    <Button variant="ghost" size="icon" className="w-7 h-7 text-white/30 hover:text-[#FF2E2E]"
                      onClick={() => deleteAlert(alert.alert_id)} data-testid={`delete-alert-${alert.alert_id}`}>
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Triggered Alerts */}
      {triggeredAlerts.length > 0 && (
        <Card className="glass-panel border-white/10 border-l-2 border-l-[#00FF94]" data-testid="triggered-alerts-list">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-white/80 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-[#00FF94]" /> Triggered Alerts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {triggeredAlerts.map(alert => (
                <div key={alert.alert_id} className="flex items-center justify-between p-3 rounded-lg bg-[#00FF94]/[0.02] border border-[#00FF94]/10" data-testid={`triggered-${alert.alert_id}`}>
                  <div className="flex items-center gap-3">
                    <CheckCircle2 className="w-5 h-5 text-[#00FF94]" />
                    <div>
                      <span className="text-sm text-white font-medium">{alert.asset_name}</span>
                      <p className="text-[10px] text-white/40">
                        {alert.condition === 'above' ? 'Went above' : 'Went below'} ${alert.target_price.toLocaleString()}
                        {alert.triggered_price && <span className="ml-1">at ${alert.triggered_price.toLocaleString()}</span>}
                      </p>
                    </div>
                  </div>
                  <Button variant="ghost" size="icon" className="w-7 h-7 text-white/30 hover:text-[#FF2E2E]"
                    onClick={() => deleteAlert(alert.alert_id)}>
                    <Trash2 className="w-3.5 h-3.5" />
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
