import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { Plus, Trash2, Wallet, TrendingUp, BarChart3 } from 'lucide-react';
import { toast } from 'sonner';

const COLORS = ['#6366F1', '#00FF94', '#FF2E2E', '#EAB308', '#06B6D4', '#F97316', '#8B5CF6', '#EC4899'];

export default function PortfolioPage() {
  const { api } = useAuth();
  const [holdings, setHoldings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState({ asset_id: '', asset_name: '', asset_type: 'crypto', quantity: '', buy_price: '' });

  const fetchPortfolio = async () => {
    try {
      const res = await api.get('/portfolio');
      setHoldings(res.data.holdings || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  useEffect(() => { fetchPortfolio(); }, []);

  const addHolding = async () => {
    if (!form.asset_name || !form.quantity || !form.buy_price) {
      toast.error('Fill all fields');
      return;
    }
    try {
      const res = await api.post('/portfolio/holdings', {
        ...form,
        asset_id: form.asset_name.toLowerCase().replace(/[^a-z0-9]/g, ''),
        quantity: parseFloat(form.quantity),
        buy_price: parseFloat(form.buy_price),
      });
      setHoldings(prev => [...prev, res.data]);
      setDialogOpen(false);
      setForm({ asset_id: '', asset_name: '', asset_type: 'crypto', quantity: '', buy_price: '' });
      toast.success('Holding added');
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to add');
    }
  };

  const deleteHolding = async (holdingId) => {
    try {
      await api.delete(`/portfolio/holdings/${holdingId}`);
      setHoldings(prev => prev.filter(h => h.holding_id !== holdingId));
      toast.success('Holding removed');
    } catch (e) {
      toast.error('Failed to remove');
    }
  };

  const totalInvested = holdings.reduce((sum, h) => sum + (h.quantity * h.buy_price), 0);
  const pieData = holdings.map((h, i) => ({
    name: h.asset_name,
    value: h.quantity * h.buy_price,
    color: COLORS[i % COLORS.length],
  }));

  return (
    <div className="space-y-6" data-testid="portfolio-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white" style={{ fontFamily: 'Manrope' }}>Portfolio</h1>
          <p className="text-sm text-white/40 mt-1">Track your holdings and performance</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-[#6366F1] hover:bg-[#4F46E5] text-white text-xs shadow-[0_0_15px_rgba(99,102,241,0.4)] active:scale-95" data-testid="add-holding-btn">
              <Plus className="w-3.5 h-3.5 mr-1.5" /> Add Holding
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-[#09090B] border-white/10 text-white">
            <DialogHeader>
              <DialogTitle className="text-white">Add New Holding</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div>
                <Label className="text-xs text-white/60">Asset Name</Label>
                <Input className="bg-black/50 border-white/10 text-white text-sm mt-1" placeholder="e.g., Bitcoin, RELIANCE"
                  value={form.asset_name} onChange={e => setForm({ ...form, asset_name: e.target.value })} data-testid="holding-name-input" />
              </div>
              <div>
                <Label className="text-xs text-white/60">Market Type</Label>
                <Select value={form.asset_type} onValueChange={v => setForm({ ...form, asset_type: v })}>
                  <SelectTrigger className="bg-black/50 border-white/10 text-white text-sm mt-1" data-testid="holding-type-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-[#09090B] border-white/10">
                    <SelectItem value="crypto">Crypto</SelectItem>
                    <SelectItem value="forex">Forex</SelectItem>
                    <SelectItem value="indian">Indian Market</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className="text-xs text-white/60">Quantity</Label>
                  <Input type="number" step="any" className="bg-black/50 border-white/10 text-white text-sm mt-1" placeholder="0.00"
                    value={form.quantity} onChange={e => setForm({ ...form, quantity: e.target.value })} data-testid="holding-qty-input" />
                </div>
                <div>
                  <Label className="text-xs text-white/60">Buy Price ($)</Label>
                  <Input type="number" step="any" className="bg-black/50 border-white/10 text-white text-sm mt-1" placeholder="0.00"
                    value={form.buy_price} onChange={e => setForm({ ...form, buy_price: e.target.value })} data-testid="holding-price-input" />
                </div>
              </div>
              <Button className="w-full bg-[#6366F1] hover:bg-[#4F46E5] text-white active:scale-95" onClick={addHolding} data-testid="confirm-add-holding-btn">
                Add to Portfolio
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="glass-panel border-white/10" data-testid="total-invested-card">
          <CardContent className="p-5">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-[#6366F1]/10 flex items-center justify-center">
                <Wallet className="w-5 h-5 text-[#6366F1]" />
              </div>
              <div>
                <p className="text-xs text-white/40">Total Invested</p>
                <p className="text-xl font-bold text-white font-data">${totalInvested.toLocaleString(undefined, { minimumFractionDigits: 2 })}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass-panel border-white/10" data-testid="holdings-count-card">
          <CardContent className="p-5">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-[#00FF94]/10 flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-[#00FF94]" />
              </div>
              <div>
                <p className="text-xs text-white/40">Total Holdings</p>
                <p className="text-xl font-bold text-white font-data">{holdings.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass-panel border-white/10" data-testid="asset-types-card">
          <CardContent className="p-5">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-[#EAB308]/10 flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-[#EAB308]" />
              </div>
              <div>
                <p className="text-xs text-white/40">Asset Types</p>
                <p className="text-xl font-bold text-white font-data">{new Set(holdings.map(h => h.asset_type)).size}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Holdings Table */}
        <div className="lg:col-span-2">
          <Card className="glass-panel border-white/10 overflow-hidden" data-testid="holdings-table-card">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-white/80">Holdings</CardTitle>
            </CardHeader>
            {holdings.length === 0 ? (
              <CardContent className="py-12 text-center">
                <Wallet className="w-10 h-10 text-white/10 mx-auto mb-3" />
                <p className="text-sm text-white/40">No holdings yet</p>
                <p className="text-xs text-white/20 mt-1">Add your first holding to start tracking</p>
              </CardContent>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="border-b border-white/5">
                    <tr className="text-[10px] text-white/40 uppercase tracking-wider">
                      <th className="text-left py-3 px-5">Asset</th>
                      <th className="text-right py-3 px-5">Qty</th>
                      <th className="text-right py-3 px-5">Buy Price</th>
                      <th className="text-right py-3 px-5">Total Value</th>
                      <th className="text-right py-3 px-5"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {holdings.map(h => (
                      <tr key={h.holding_id} className="market-row border-b border-white/[0.03]" data-testid={`holding-row-${h.holding_id}`}>
                        <td className="py-3 px-5">
                          <p className="text-sm text-white font-medium">{h.asset_name}</p>
                          <p className="text-[10px] text-white/40 uppercase">{h.asset_type}</p>
                        </td>
                        <td className="py-3 px-5 text-right text-sm text-white font-data">{h.quantity}</td>
                        <td className="py-3 px-5 text-right text-sm text-white/60 font-data">${h.buy_price?.toLocaleString()}</td>
                        <td className="py-3 px-5 text-right text-sm text-white font-data">${(h.quantity * h.buy_price).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                        <td className="py-3 px-5 text-right">
                          <Button variant="ghost" size="icon" className="w-7 h-7 text-white/30 hover:text-[#FF2E2E]"
                            onClick={() => deleteHolding(h.holding_id)} data-testid={`delete-holding-${h.holding_id}`}>
                            <Trash2 className="w-3.5 h-3.5" />
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </div>

        {/* Allocation Chart */}
        <Card className="glass-panel border-white/10" data-testid="allocation-chart-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-white/80">Allocation</CardTitle>
          </CardHeader>
          <CardContent>
            {pieData.length === 0 ? (
              <div className="py-8 text-center text-xs text-white/30">No data</div>
            ) : (
              <>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" stroke="none">
                      {pieData.map((d, i) => <Cell key={i} fill={d.color} />)}
                    </Pie>
                    <Tooltip contentStyle={{ background: 'rgba(9,9,11,0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', fontSize: '12px' }}
                      formatter={(v) => [`$${v.toLocaleString()}`, '']} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="space-y-2 mt-2">
                  {pieData.map((d, i) => (
                    <div key={i} className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <div className="w-2.5 h-2.5 rounded-full" style={{ background: d.color }} />
                        <span className="text-white/60 truncate max-w-[120px]">{d.name}</span>
                      </div>
                      <span className="text-white font-data">{totalInvested > 0 ? ((d.value / totalInvested) * 100).toFixed(1) : 0}%</span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
