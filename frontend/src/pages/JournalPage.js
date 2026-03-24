import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { BookOpen, Plus, TrendingUp, TrendingDown, DollarSign, Target, Clock, Brain, Star, Trash2, Edit3, X, Check, BarChart3, Frown, Smile, AlertTriangle, Zap, Heart } from 'lucide-react';
import { toast } from 'sonner';

const EMOTIONS = [
  { id: 'calm', label: 'Calm', color: '#00FF94' },
  { id: 'confident', label: 'Confident', color: '#6366F1' },
  { id: 'fear', label: 'Fear', color: '#EAB308' },
  { id: 'greed', label: 'Greed', color: '#FF2E2E' },
  { id: 'fomo', label: 'FOMO', color: '#FF6B35' },
  { id: 'revenge', label: 'Revenge', color: '#DC2626' },
];

const StarRating = ({ value, onChange, readonly = false }) => (
  <div className="flex gap-0.5">
    {[1,2,3,4,5].map(i => (
      <button key={i} onClick={() => !readonly && onChange?.(i)}
        className={`${readonly ? 'cursor-default' : 'cursor-pointer hover:scale-110'} transition-transform`}
        disabled={readonly}>
        <Star className={`w-4 h-4 ${i <= value ? 'fill-[#FFD700] text-[#FFD700]' : 'text-white/20'}`} />
      </button>
    ))}
  </div>
);

export default function JournalPage() {
  const { api } = useAuth();
  const [trades, setTrades] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [filter, setFilter] = useState('all');

  const [form, setForm] = useState({
    asset_name: '', asset_id: '', asset_type: 'crypto', direction: 'BUY',
    entry_price: '', exit_price: '', quantity: '', timeframe: '1D',
    strategy: '', signal_trigger: '', entry_reasoning: '',
    pre_trade_confidence: 5, emotion_tag: 'calm',
    post_reflection: '', lesson_learned: '', quality_rating: 3, status: 'open'
  });

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const [tradesRes, statsRes] = await Promise.all([
        api.get('/journal'), api.get('/journal/stats')
      ]);
      setTrades(tradesRes.data.trades || []);
      setStats(statsRes.data);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const resetForm = () => {
    setForm({
      asset_name: '', asset_id: '', asset_type: 'crypto', direction: 'BUY',
      entry_price: '', exit_price: '', quantity: '', timeframe: '1D',
      strategy: '', signal_trigger: '', entry_reasoning: '',
      pre_trade_confidence: 5, emotion_tag: 'calm',
      post_reflection: '', lesson_learned: '', quality_rating: 3, status: 'open'
    });
    setShowForm(false);
    setEditingId(null);
  };

  const handleSubmit = async () => {
    if (!form.asset_name || !form.entry_price || !form.quantity) {
      toast.error('Fill required fields: Asset Name, Entry Price, Quantity');
      return;
    }
    try {
      if (editingId) {
        await api.put(`/journal/${editingId}`, {
          exit_price: form.exit_price ? parseFloat(form.exit_price) : null,
          post_reflection: form.post_reflection || null,
          lesson_learned: form.lesson_learned || null,
          quality_rating: form.quality_rating,
          emotion_tag: form.emotion_tag,
          status: form.status,
        });
        toast.success('Trade updated');
      } else {
        await api.post('/journal', {
          ...form,
          asset_id: form.asset_id || form.asset_name.toLowerCase().replace(/[^a-z0-9]/g, ''),
          entry_price: parseFloat(form.entry_price),
          exit_price: form.exit_price ? parseFloat(form.exit_price) : null,
          quantity: parseFloat(form.quantity),
          pre_trade_confidence: parseInt(form.pre_trade_confidence),
        });
        toast.success('Trade logged');
      }
      resetForm();
      fetchData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to save trade');
    }
  };

  const handleEdit = (trade) => {
    setEditingId(trade.trade_id);
    setForm({
      ...trade,
      entry_price: trade.entry_price?.toString() || '',
      exit_price: trade.exit_price?.toString() || '',
      quantity: trade.quantity?.toString() || '',
    });
    setShowForm(true);
  };

  const handleDelete = async (tradeId) => {
    try {
      await api.delete(`/journal/${tradeId}`);
      toast.success('Trade deleted');
      fetchData();
    } catch (e) { toast.error('Failed to delete'); }
  };

  const filteredTrades = trades.filter(t => {
    if (filter === 'all') return true;
    if (filter === 'open') return t.status === 'open';
    if (filter === 'closed') return t.status === 'closed';
    if (filter === 'wins') return t.pnl > 0;
    if (filter === 'losses') return t.pnl < 0;
    return true;
  });

  return (
    <div className="space-y-6" data-testid="journal-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white" style={{ fontFamily: 'Manrope' }}>Trade Journal</h1>
          <p className="text-sm text-white/40 mt-1">Log, track, and improve your trading performance</p>
        </div>
        <Button onClick={() => { resetForm(); setShowForm(true); }}
          className="bg-[#6366F1] hover:bg-[#4F46E5] text-white text-xs"
          data-testid="new-trade-btn">
          <Plus className="w-3.5 h-3.5 mr-1.5" /> Log Trade
        </Button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3" data-testid="journal-stats">
          <Card className="glass-panel border-white/10">
            <CardContent className="p-4">
              <p className="text-[10px] text-white/40 uppercase tracking-wider">Total Trades</p>
              <p className="text-2xl font-bold font-data text-white mt-1">{stats.total_trades}</p>
            </CardContent>
          </Card>
          <Card className="glass-panel border-white/10">
            <CardContent className="p-4">
              <p className="text-[10px] text-white/40 uppercase tracking-wider">Win Rate</p>
              <p className={`text-2xl font-bold font-data mt-1 ${stats.win_rate >= 50 ? 'text-[#00FF94]' : 'text-[#FF2E2E]'}`}>
                {stats.win_rate}%
              </p>
            </CardContent>
          </Card>
          <Card className="glass-panel border-white/10">
            <CardContent className="p-4">
              <p className="text-[10px] text-white/40 uppercase tracking-wider">Total P&L</p>
              <p className={`text-2xl font-bold font-data mt-1 ${stats.total_pnl >= 0 ? 'text-[#00FF94]' : 'text-[#FF2E2E]'}`}>
                ${stats.total_pnl.toLocaleString()}
              </p>
            </CardContent>
          </Card>
          <Card className="glass-panel border-white/10">
            <CardContent className="p-4">
              <p className="text-[10px] text-white/40 uppercase tracking-wider">W / L</p>
              <p className="text-2xl font-bold font-data text-white mt-1">
                <span className="text-[#00FF94]">{stats.wins}</span>
                <span className="text-white/30 mx-1">/</span>
                <span className="text-[#FF2E2E]">{stats.losses}</span>
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Trade Entry Form */}
      {showForm && (
        <Card className="glass-panel border-white/10 border-l-2 border-l-[#FFD700]" data-testid="trade-form">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm text-white/80 flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-[#FFD700]" /> {editingId ? 'Edit Trade' : 'Log New Trade'}
              </CardTitle>
              <button onClick={resetForm} className="text-white/40 hover:text-white"><X className="w-4 h-4" /></button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div>
                <label className="text-[10px] text-white/40 mb-1 block">Asset Name *</label>
                <Input value={form.asset_name} onChange={e => setForm(p => ({...p, asset_name: e.target.value}))}
                  placeholder="BTC, EUR/USD..." className="bg-black/50 border-white/10 text-white text-sm" data-testid="journal-asset-name" />
              </div>
              <div>
                <label className="text-[10px] text-white/40 mb-1 block">Direction</label>
                <Select value={form.direction} onValueChange={v => setForm(p => ({...p, direction: v}))}>
                  <SelectTrigger className="bg-black/50 border-white/10 text-white text-sm"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-[#09090B] border-white/10">
                    <SelectItem value="BUY">BUY (Long)</SelectItem>
                    <SelectItem value="SELL">SELL (Short)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-[10px] text-white/40 mb-1 block">Entry Price *</label>
                <Input type="number" value={form.entry_price} onChange={e => setForm(p => ({...p, entry_price: e.target.value}))}
                  placeholder="0.00" className="bg-black/50 border-white/10 text-white text-sm" data-testid="journal-entry-price" />
              </div>
              <div>
                <label className="text-[10px] text-white/40 mb-1 block">Quantity *</label>
                <Input type="number" value={form.quantity} onChange={e => setForm(p => ({...p, quantity: e.target.value}))}
                  placeholder="0.00" className="bg-black/50 border-white/10 text-white text-sm" data-testid="journal-quantity" />
              </div>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div>
                <label className="text-[10px] text-white/40 mb-1 block">Exit Price</label>
                <Input type="number" value={form.exit_price} onChange={e => setForm(p => ({...p, exit_price: e.target.value}))}
                  placeholder="0.00" className="bg-black/50 border-white/10 text-white text-sm" data-testid="journal-exit-price" />
              </div>
              <div>
                <label className="text-[10px] text-white/40 mb-1 block">Market</label>
                <Select value={form.asset_type} onValueChange={v => setForm(p => ({...p, asset_type: v}))}>
                  <SelectTrigger className="bg-black/50 border-white/10 text-white text-sm"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-[#09090B] border-white/10">
                    <SelectItem value="crypto">Crypto</SelectItem>
                    <SelectItem value="forex">Forex</SelectItem>
                    <SelectItem value="indian">Indian</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-[10px] text-white/40 mb-1 block">Timeframe</label>
                <Select value={form.timeframe} onValueChange={v => setForm(p => ({...p, timeframe: v}))}>
                  <SelectTrigger className="bg-black/50 border-white/10 text-white text-sm"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-[#09090B] border-white/10">
                    {['1m','5m','15m','1H','4H','1D','1W'].map(tf => <SelectItem key={tf} value={tf}>{tf}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-[10px] text-white/40 mb-1 block">Status</label>
                <Select value={form.status} onValueChange={v => setForm(p => ({...p, status: v}))}>
                  <SelectTrigger className="bg-black/50 border-white/10 text-white text-sm"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-[#09090B] border-white/10">
                    <SelectItem value="open">Open</SelectItem>
                    <SelectItem value="closed">Closed</SelectItem>
                    <SelectItem value="cancelled">Cancelled</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-[10px] text-white/40 mb-1 block">Entry Reasoning</label>
                <Input value={form.entry_reasoning} onChange={e => setForm(p => ({...p, entry_reasoning: e.target.value}))}
                  placeholder="Why did you enter?" className="bg-black/50 border-white/10 text-white text-sm" />
              </div>
              <div>
                <label className="text-[10px] text-white/40 mb-1 block">Strategy Used</label>
                <Input value={form.strategy} onChange={e => setForm(p => ({...p, strategy: e.target.value}))}
                  placeholder="EMA Crossover, SMC..." className="bg-black/50 border-white/10 text-white text-sm" />
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-[10px] text-white/40 mb-1 block">Post-Trade Reflection</label>
                <Input value={form.post_reflection} onChange={e => setForm(p => ({...p, post_reflection: e.target.value}))}
                  placeholder="What went right/wrong?" className="bg-black/50 border-white/10 text-white text-sm" />
              </div>
              <div>
                <label className="text-[10px] text-white/40 mb-1 block">Lesson Learned</label>
                <Input value={form.lesson_learned} onChange={e => setForm(p => ({...p, lesson_learned: e.target.value}))}
                  placeholder="Key takeaway..." className="bg-black/50 border-white/10 text-white text-sm" />
              </div>
            </div>
            <div className="flex items-center gap-6 flex-wrap">
              <div>
                <label className="text-[10px] text-white/40 mb-2 block">Emotion</label>
                <div className="flex gap-1.5">
                  {EMOTIONS.map(em => (
                    <button key={em.id} onClick={() => setForm(p => ({...p, emotion_tag: em.id}))}
                      className={`px-2 py-1 rounded-md text-[10px] font-medium border transition-all ${
                        form.emotion_tag === em.id
                          ? `border-[${em.color}]/50 text-white` : 'border-white/10 text-white/40'
                      }`}
                      style={form.emotion_tag === em.id ? { backgroundColor: `${em.color}20`, borderColor: `${em.color}80` } : {}}
                      data-testid={`emotion-${em.id}`}>
                      {em.label}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-[10px] text-white/40 mb-2 block">Quality Rating</label>
                <StarRating value={form.quality_rating} onChange={v => setForm(p => ({...p, quality_rating: v}))} />
              </div>
            </div>
            <Button onClick={handleSubmit} className="bg-[#FFD700] hover:bg-[#FFD700]/80 text-black text-xs font-semibold px-6"
              data-testid="submit-trade-btn">
              <Check className="w-3.5 h-3.5 mr-1.5" /> {editingId ? 'Update Trade' : 'Log Trade'}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Filter Tabs */}
      <div className="flex gap-1 flex-wrap">
        {['all', 'open', 'closed', 'wins', 'losses'].map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-md text-[10px] font-medium transition-all ${
              filter === f ? 'bg-[#6366F1] text-white' : 'bg-white/5 text-white/40 hover:text-white/60'
            }`}
            data-testid={`journal-filter-${f}`}>
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Trades List */}
      {loading ? (
        <div className="space-y-3">{[1,2,3].map(i => <div key={i} className="h-24 rounded-xl skeleton-shimmer" />)}</div>
      ) : filteredTrades.length === 0 ? (
        <Card className="glass-panel border-white/10">
          <CardContent className="py-12 text-center">
            <BookOpen className="w-10 h-10 text-white/10 mx-auto mb-3" />
            <h3 className="text-white/60 text-sm font-medium mb-1">No trades logged</h3>
            <p className="text-white/30 text-xs">Start logging your trades to track performance</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredTrades.map(trade => {
            const emotionData = EMOTIONS.find(e => e.id === trade.emotion_tag);
            return (
              <Card key={trade.trade_id} className="glass-panel border-white/10 card-hover" data-testid={`trade-${trade.trade_id}`}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 space-y-2 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="text-sm font-semibold text-white">{trade.asset_name}</h3>
                        <Badge className={`text-[10px] ${trade.direction === 'BUY' ? 'bg-[#00FF94]/10 text-[#00FF94]' : 'bg-[#FF2E2E]/10 text-[#FF2E2E]'}`}>
                          {trade.direction}
                        </Badge>
                        <Badge variant="outline" className={`text-[10px] ${
                          trade.status === 'open' ? 'border-[#EAB308]/30 text-[#EAB308]' :
                          trade.status === 'closed' ? 'border-white/20 text-white/50' :
                          'border-white/10 text-white/30'}`}>
                          {trade.status}
                        </Badge>
                        {trade.pnl !== null && trade.pnl !== undefined && (
                          <Badge className={`text-[10px] ${trade.pnl >= 0 ? 'bg-[#00FF94]/10 text-[#00FF94]' : 'bg-[#FF2E2E]/10 text-[#FF2E2E]'}`}>
                            {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toLocaleString()}
                          </Badge>
                        )}
                        {emotionData && (
                          <span className="text-[9px] px-1.5 py-0.5 rounded-full" style={{ backgroundColor: `${emotionData.color}15`, color: emotionData.color }}>
                            {emotionData.label}
                          </span>
                        )}
                        {trade.quality_rating && <StarRating value={trade.quality_rating} readonly />}
                      </div>
                      <div className="flex items-center gap-4 text-[10px] text-white/40">
                        <span>Entry: <span className="text-white/70 font-data">${trade.entry_price}</span></span>
                        {trade.exit_price && <span>Exit: <span className="text-white/70 font-data">${trade.exit_price}</span></span>}
                        <span>Qty: <span className="text-white/70 font-data">{trade.quantity}</span></span>
                        <span>{trade.timeframe}</span>
                        {trade.strategy && <span className="text-[#6366F1]">{trade.strategy}</span>}
                      </div>
                      {trade.entry_reasoning && <p className="text-[10px] text-white/40">{trade.entry_reasoning}</p>}
                      {trade.lesson_learned && (
                        <p className="text-[10px] text-[#FFD700]/70 flex items-center gap-1">
                          <Brain className="w-3 h-3" /> {trade.lesson_learned}
                        </p>
                      )}
                    </div>
                    <div className="flex gap-1 flex-shrink-0">
                      <button onClick={() => handleEdit(trade)} className="p-1.5 rounded-md bg-white/5 hover:bg-white/10 text-white/40 hover:text-white"
                        data-testid={`edit-trade-${trade.trade_id}`}>
                        <Edit3 className="w-3.5 h-3.5" />
                      </button>
                      <button onClick={() => handleDelete(trade.trade_id)} className="p-1.5 rounded-md bg-white/5 hover:bg-red-500/20 text-white/40 hover:text-red-400"
                        data-testid={`delete-trade-${trade.trade_id}`}>
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
