import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Layers, Plus, Trash2, Save, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

export default function StrategyBuilderPage() {
  const { api } = useAuth();
  const [customStrategies, setCustomStrategies] = useState([]);
  const [availableStrategies, setAvailableStrategies] = useState([]);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [marketType, setMarketType] = useState('all');
  const [selectedIds, setSelectedIds] = useState([]);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    api.get(`/signals/strategies?market=${marketType === 'all' ? 'forex' : marketType}`)
      .then(r => setAvailableStrategies(r.data.strategies || []))
      .catch(() => {});
  }, [marketType, api]);

  const loadData = async () => {
    try {
      const [cs, strats] = await Promise.all([
        api.get('/strategies/custom'),
        api.get('/signals/strategies?market=forex'),
      ]);
      setCustomStrategies(cs.data.strategies || []);
      setAvailableStrategies(strats.data.strategies || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const toggleStrategy = (id) => {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(s => s !== id) : [...prev, id]);
  };

  const saveStrategy = async () => {
    if (!name.trim()) { toast.error('Enter a strategy name'); return; }
    if (selectedIds.length < 2) { toast.error('Select at least 2 strategies to combine'); return; }
    setSaving(true);
    try {
      const res = await api.post('/strategies/custom', {
        name: name.trim(),
        description: description.trim() || `Custom combo: ${selectedIds.join(' + ')}`,
        strategies: selectedIds,
        market_type: marketType,
      });
      setCustomStrategies(prev => [res.data, ...prev]);
      setName('');
      setDescription('');
      setSelectedIds([]);
      toast.success('Custom strategy saved!');
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to save');
    }
    setSaving(false);
  };

  const deleteStrategy = async (id) => {
    try {
      await api.delete(`/strategies/custom/${id}`);
      setCustomStrategies(prev => prev.filter(s => s.strategy_id !== id));
      toast.success('Strategy deleted');
    } catch (e) {
      toast.error('Failed to delete');
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center min-h-[60vh]"><div className="w-8 h-8 border-2 border-[#6366F1] border-t-transparent rounded-full animate-spin" /></div>;
  }

  return (
    <div className="space-y-6 page-enter" data-testid="strategy-builder-page">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">Strategy Builder</h1>
        <p className="text-sm text-white/50 mt-1">Create custom combo strategies by combining multiple techniques</p>
      </div>

      {/* Builder */}
      <Card className="bg-[#0A0A0F] border-white/5 border-l-2 border-l-[#6366F1]">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm text-white flex items-center gap-2">
            <Plus className="w-4 h-4 text-[#6366F1]" /> New Custom Strategy
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="text-[11px] text-white/40 uppercase mb-1.5 block">Name</label>
              <Input value={name} onChange={e => setName(e.target.value)} placeholder="e.g. ICT + SMC Combo" className="bg-white/[0.03] border-white/10 text-white text-sm" data-testid="strategy-name-input" />
            </div>
            <div>
              <label className="text-[11px] text-white/40 uppercase mb-1.5 block">Description</label>
              <Input value={description} onChange={e => setDescription(e.target.value)} placeholder="Optional description" className="bg-white/[0.03] border-white/10 text-white text-sm" />
            </div>
            <div>
              <label className="text-[11px] text-white/40 uppercase mb-1.5 block">Market</label>
              <Select value={marketType} onValueChange={setMarketType}>
                <SelectTrigger className="bg-white/[0.03] border-white/10 text-white text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Markets</SelectItem>
                  <SelectItem value="forex">Forex</SelectItem>
                  <SelectItem value="crypto">Crypto</SelectItem>
                  <SelectItem value="indian">Indian</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div>
            <label className="text-[11px] text-white/40 uppercase mb-2 block">Select strategies to combine ({selectedIds.length} selected)</label>
            <div className="flex flex-wrap gap-1.5" data-testid="strategy-selector">
              {availableStrategies.filter(s => s.id !== 'auto').map(s => (
                <button key={s.id} onClick={() => toggleStrategy(s.id)}
                  className={`px-2.5 py-1.5 rounded-md text-[10px] font-medium border transition-all ${
                    selectedIds.includes(s.id) ? 'bg-[#6366F1]/20 border-[#6366F1]/50 text-[#6366F1]' : 'bg-white/5 border-white/10 text-white/40 hover:text-white/60'
                  }`}
                >
                  {s.name}
                </button>
              ))}
            </div>
            {selectedIds.length > 0 && (
              <p className="text-[10px] text-[#6366F1] mt-2">
                Combo: {selectedIds.map(id => availableStrategies.find(s => s.id === id)?.name || id).join(' + ')}
              </p>
            )}
          </div>

          <Button onClick={saveStrategy} disabled={saving} className="bg-[#6366F1] hover:bg-[#4F46E5] text-white text-xs" data-testid="save-strategy-btn">
            {saving ? <Loader2 className="w-3 h-3 mr-1 animate-spin" /> : <Save className="w-3 h-3 mr-1" />}
            Save Custom Strategy
          </Button>
        </CardContent>
      </Card>

      {/* Saved Strategies */}
      <Card className="bg-[#0A0A0F] border-white/5">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm text-white flex items-center gap-2">
            <Layers className="w-4 h-4 text-[#6366F1]" /> Your Custom Strategies
          </CardTitle>
        </CardHeader>
        <CardContent>
          {customStrategies.length === 0 ? (
            <div className="text-center py-8">
              <Layers className="w-10 h-10 text-white/10 mx-auto mb-2" />
              <p className="text-sm text-white/40">No custom strategies yet</p>
              <p className="text-xs text-white/25 mt-1">Create your first combo strategy above</p>
            </div>
          ) : (
            <div className="space-y-2">
              {customStrategies.map(cs => (
                <div key={cs.strategy_id} className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/5" data-testid={`custom-strategy-${cs.strategy_id}`}>
                  <div>
                    <p className="text-sm font-medium text-white">{cs.name}</p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {cs.strategies?.map(s => (
                        <Badge key={s} variant="outline" className="text-[9px] border-[#6366F1]/20 text-[#6366F1]/70">{s}</Badge>
                      ))}
                    </div>
                    <p className="text-[10px] text-white/30 mt-1">{cs.description}</p>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => deleteStrategy(cs.strategy_id)} className="text-red-400 hover:text-red-300 hover:bg-red-500/10">
                    <Trash2 className="w-3.5 h-3.5" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
