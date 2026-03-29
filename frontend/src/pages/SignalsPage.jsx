import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useMarketStream } from '../hooks/useMarketStream';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Input } from '../components/ui/input';
import { Zap, Target, ShieldAlert, TrendingUp, TrendingDown, Clock, Loader2, CheckCircle2, XCircle, BarChart3, Layers, Brain, Crosshair, Timer, AlertTriangle, ChevronDown, ChevronUp, ArrowUpRight, Plus, Trash2, Lock } from 'lucide-react';
import { toast } from 'sonner';

const CRYPTO_ASSETS = [
  { id: 'bitcoin', name: 'Bitcoin (BTC)' }, { id: 'ethereum', name: 'Ethereum (ETH)' },
  { id: 'solana', name: 'Solana (SOL)' }, { id: 'binancecoin', name: 'BNB' },
  { id: 'ripple', name: 'XRP' }, { id: 'cardano', name: 'Cardano (ADA)' },
  { id: 'dogecoin', name: 'Dogecoin (DOGE)' }, { id: 'polkadot', name: 'Polkadot (DOT)' },
];

const FOREX_ASSETS = [
  { id: 'eurusd', name: 'EUR/USD' }, { id: 'gbpusd', name: 'GBP/USD' },
  { id: 'usdjpy', name: 'USD/JPY' }, { id: 'xauusd', name: 'Gold (XAU/USD)' },
  { id: 'xagusd', name: 'Silver (XAG/USD)' }, { id: 'gbpjpy', name: 'GBP/JPY' },
  { id: 'audusd', name: 'AUD/USD' }, { id: 'usdchf', name: 'USD/CHF' },
  { id: 'usdcad', name: 'USD/CAD' }, { id: 'nzdusd', name: 'NZD/USD' },
  { id: 'eurgbp', name: 'EUR/GBP' }, { id: 'eurjpy', name: 'EUR/JPY' },
  { id: 'audjpy', name: 'AUD/JPY' }, { id: 'cadjpy', name: 'CAD/JPY' },
  { id: 'gbpchf', name: 'GBP/CHF' }, { id: 'euraud', name: 'EUR/AUD' },
  { id: 'eurchf', name: 'EUR/CHF' }, { id: 'gbpaud', name: 'GBP/AUD' },
  { id: 'gbpnzd', name: 'GBP/NZD' }, { id: 'audnzd', name: 'AUD/NZD' },
];

const INDIAN_ASSETS = [
  { id: 'nifty50', name: 'NIFTY 50' }, { id: 'sensex', name: 'SENSEX' },
  { id: 'banknifty', name: 'NIFTY Bank' }, { id: 'niftyit', name: 'NIFTY IT' },
  { id: 'niftypharma', name: 'NIFTY Pharma' }, { id: 'niftyauto', name: 'NIFTY Auto' },
  { id: 'reliance', name: 'Reliance Industries' }, { id: 'tcs', name: 'TCS' },
  { id: 'infy', name: 'Infosys' }, { id: 'hdfcbank', name: 'HDFC Bank' },
  { id: 'sbin', name: 'State Bank of India' }, { id: 'icicibank', name: 'ICICI Bank' },
  { id: 'bhartiartl', name: 'Bharti Airtel' }, { id: 'wipro', name: 'Wipro' },
  { id: 'bajfinance', name: 'Bajaj Finance' }, { id: 'adanient', name: 'Adani Enterprises' },
  { id: 'tatamotors', name: 'Tata Motors' }, { id: 'maruti', name: 'Maruti Suzuki' },
  { id: 'sunpharma', name: 'Sun Pharma' }, { id: 'lt', name: 'Larsen & Toubro' },
  { id: 'titan', name: 'Titan Company' }, { id: 'axisbank', name: 'Axis Bank' },
  { id: 'kotakbank', name: 'Kotak Bank' }, { id: 'hcltech', name: 'HCL Tech' },
  { id: 'ntpc', name: 'NTPC' }, { id: 'ongc', name: 'ONGC' },
  { id: 'coalindia', name: 'Coal India' }, { id: 'jswsteel', name: 'JSW Steel' },
  { id: 'tatasteel', name: 'Tata Steel' }, { id: 'nestleind', name: 'Nestle India' },
  { id: 'drreddy', name: "Dr Reddy's" }, { id: 'cipla', name: 'Cipla' },
  { id: 'hindunilvr', name: 'Hindustan Unilever' }, { id: 'asianpaint', name: 'Asian Paints' },
  { id: 'powergrid', name: 'Power Grid' }, { id: 'ultracemco', name: 'UltraTech Cement' },
];

const ALL_TIMEFRAMES = ['1m', '3m', '5m', '10m', '15m', '30m', '1H', '2H', '3H', '4H', '1D', '3D', '1W', '1M', '3M', '6M', '12M'];

const ConfidenceRing = ({ value }) => {
  const r = 28, c = 2 * Math.PI * r;
  const color = value >= 80 ? '#10B981' : value >= 60 ? '#6366F1' : value >= 40 ? '#F59E0B' : '#EF4444';
  return (
    <div className="relative w-16 h-16 sm:w-20 sm:h-20 flex items-center justify-center flex-shrink-0">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 64 64">
        <circle cx="32" cy="32" r={r} fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth="3.5" />
        <circle cx="32" cy="32" r={r} fill="none" stroke={color} strokeWidth="3.5" strokeLinecap="round"
          strokeDasharray={`${(value/100)*c} ${c}`} style={{ transition: 'stroke-dasharray 0.6s ease' }} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-base sm:text-xl font-semibold font-data text-white">{value}%</span>
      </div>
    </div>
  );
};

const RiskBadge = ({ riskReward }) => {
  if (!riskReward) return null;
  const ratio = parseFloat(riskReward.split(':')[1]) || 0;
  const level = ratio >= 2.5 ? 'low' : ratio >= 1.5 ? 'medium' : 'high';
  const label = level === 'low' ? 'Low Risk' : level === 'medium' ? 'Med Risk' : 'High Risk';
  return (
    <span className={`risk-${level} text-[10px] sm:text-[11px] font-medium px-2 py-0.5 rounded-full`} data-testid="risk-badge">
      {label}
    </span>
  );
};

const ConfluenceDots = ({ score = 0, max = 6 }) => (
  <div className="flex gap-1 items-center">
    {Array.from({ length: max }).map((_, i) => (
      <div key={i} className={`w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full transition-all ${i < score ? 'bg-[#10B981] shadow-[0_0_3px_rgba(16,185,129,0.5)]' : 'bg-white/8'}`} />
    ))}
    <span className="text-[9px] sm:text-[10px] text-white/40 ml-1">{score}/{max}</span>
  </div>
);

export default function SignalsPage() {
  const { api } = useAuth();
  const navigate = useNavigate();
  const { crypto, forex, indian } = useMarketStream(true, 800);
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [assetType, setAssetType] = useState('crypto');
  const [assetId, setAssetId] = useState('bitcoin');
  const [selectedTimeframes, setSelectedTimeframes] = useState(['15m', '1H', '4H']);
  const [strategy, setStrategy] = useState('auto');
  const [selectedStrategies, setSelectedStrategies] = useState([]);
  const [comboMode, setComboMode] = useState(false);
  const [profitTarget, setProfitTarget] = useState('');
  const [riskReward, setRiskReward] = useState('');
  const [filter, setFilter] = useState('all');
  const [expandedSignals, setExpandedSignals] = useState({});
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [planUsage, setPlanUsage] = useState(null);
  const [availableStrategies, setAvailableStrategies] = useState([]);
  const [executingSignal, setExecutingSignal] = useState(null);
  const [tradingMode, setTradingMode] = useState('swing');
  const [numTpLevels, setNumTpLevels] = useState(3);
  const [deletingSignal, setDeletingSignal] = useState(null);

  const assets = assetType === 'crypto' ? CRYPTO_ASSETS : assetType === 'forex' ? FOREX_ASSETS : INDIAN_ASSETS;
  const allPrices = [...crypto, ...forex, ...indian];

  useEffect(() => { fetchSignals(); fetchPlanUsage(); }, []);

  // Auto-refresh signals every 10s to pick up TP/SL lock updates
  useEffect(() => {
    const interval = setInterval(fetchSignals, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    setAssetId(assets[0]?.id || '');
    fetchStrategies();
    setSelectedStrategies([]);
    setStrategy('auto');
  }, [assetType]);

  const fetchPlanUsage = async () => {
    try {
      const res = await api.get('/user/plan-usage');
      setPlanUsage(res.data);
    } catch (e) { console.error(e); }
  };

  const fetchStrategies = async () => {
    try {
      const res = await api.get(`/signals/strategies?market=${assetType}`);
      setAvailableStrategies(res.data.strategies || []);
    } catch (e) { console.error(e); }
  };

  const fetchSignals = async () => {
    try {
      const res = await api.get('/signals');
      setSignals(res.data.signals || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const toggleTimeframe = (tf) => {
    setSelectedTimeframes(prev => {
      if (prev.includes(tf)) {
        if (prev.length <= 1) return prev;
        return prev.filter(t => t !== tf);
      }
      const maxTf = planUsage?.plan_name === 'free' ? 2 : 13;
      if (prev.length >= maxTf) {
        toast.error(`${planUsage?.plan_name || 'free'} plan allows max ${maxTf} timeframes`);
        return prev;
      }
      return [...prev, tf];
    });
  };

  const toggleComboStrategy = (id) => {
    setSelectedStrategies(prev => {
      if (prev.includes(id)) return prev.filter(s => s !== id);
      return [...prev, id];
    });
  };

  const toggleExpanded = (id) => {
    setExpandedSignals(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const generateSignal = async () => {
    const asset = assets.find(a => a.id === assetId);
    if (!asset && assetType !== 'indian') return;
    if (assetType === 'indian' && !assetId) return;
    if (selectedTimeframes.length < 1) {
      toast.error('Select at least 1 timeframe');
      return;
    }
    setGenerating(true);
    try {
      let actualAssetName = asset ? asset.name : assetId;
      let actualAssetId = assetId;
      if (assetType === 'indian' && !asset) {
        if (!assetId.startsWith('NSE:') && !assetId.startsWith('BSE:')) {
          actualAssetId = 'NSE:' + assetId.toUpperCase();
        }
      }
      const payload = {
        asset_id: actualAssetId,
        asset_name: actualAssetName,
        asset_type: assetType,
        timeframe: selectedTimeframes[Math.floor(selectedTimeframes.length / 2)] || selectedTimeframes[0],
        timeframes: selectedTimeframes,
        strategy: comboMode ? selectedStrategies[0] || 'auto' : strategy,
        trading_mode: tradingMode,
        num_tp_levels: numTpLevels,
      };
      if (comboMode && selectedStrategies.length > 0) {
        payload.strategies = selectedStrategies;
      }
      if (profitTarget && !isNaN(parseFloat(profitTarget))) {
        payload.profit_target = parseFloat(profitTarget);
      }
      if (riskReward.trim()) {
        payload.risk_reward = riskReward.trim();
      }
      const res = await api.post('/signals/generate', payload);
      setSignals(prev => [res.data, ...prev]);
      toast.success(`Signal generated for ${asset.name}`);
      fetchPlanUsage();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to generate signal');
    }
    setGenerating(false);
  };

  const executeSignal = async (signalId) => {
    setExecutingSignal(signalId);
    try {
      await api.post(`/signals/${signalId}/execute?units=1000`);
      toast.success('Trade executed from signal!');
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to execute trade');
    }
    setExecutingSignal(null);
  };

  const deleteSignal = async (signalId) => {
    setDeletingSignal(signalId);
    try {
      await api.delete(`/signals/${signalId}`);
      setSignals(prev => prev.filter(s => s.signal_id !== signalId));
      toast.success('Signal deleted');
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to delete');
    }
    setDeletingSignal(null);
  };

  const buyCount = signals.filter(s => s.direction === 'BUY').length;
  const sellCount = signals.filter(s => s.direction === 'SELL').length;

  return (
    <div className="space-y-6 page-enter" data-testid="signals-page">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-bold text-white" style={{ fontFamily: 'Manrope' }}>AI Trading Signals</h1>
          <p className="text-sm text-white/40 mt-1">Multi-timeframe institutional-grade signals with SL/TP & holding duration</p>
        </div>
        {planUsage && (
          <div className="flex items-center gap-2" data-testid="signal-usage-badge">
            <Badge variant="outline" className="border-[#6366F1]/30 text-[#6366F1] bg-[#6366F1]/5 text-xs capitalize">{planUsage.plan_name} plan</Badge>
            <span className="text-xs text-white/40 font-data">
              {planUsage.limits.signals_per_day === -1 ? 'Unlimited' : `${planUsage.usage.signals_today}/${planUsage.limits.signals_per_day}`} signals today
            </span>
          </div>
        )}
      </div>

      {/* Generate Signal Card */}
      <Card className="glass-panel border-white/10 border-l-2 border-l-[#6366F1] animate-border-glow" data-testid="signal-generator-card">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm text-white/80 flex items-center gap-2">
            <Zap className="w-4 h-4 text-[#6366F1]" /> Generate New Signal
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Row 1: Market + Asset + Strategy */}
          <div className="flex flex-wrap items-end gap-4">
            <div>
              <label className="text-xs text-white/40 mb-1.5 block">Market</label>
              <Select value={assetType} onValueChange={setAssetType}>
                <SelectTrigger className="w-[130px] bg-black/50 border-white/10 text-white text-sm" data-testid="market-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-[#09090B] border-white/10">
                  <SelectItem value="crypto">Crypto</SelectItem>
                  <SelectItem value="forex">Forex</SelectItem>
                  <SelectItem value="indian">Indian</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-xs text-white/40 mb-1.5 block">Asset {assetType === 'indian' ? '(Search)' : ''}</label>
              {assetType === 'indian' ? (
                <div className="relative">
                  <Input
                    placeholder="e.g. NSE:RELIANCE or search..."
                    value={assetId}
                    onChange={e => {
                      const val = e.target.value;
                      setAssetId(val);
                    }}
                    className="w-[200px] bg-black/50 border-white/10 text-white text-sm"
                    data-testid="asset-search-input"
                    list="indian-assets-list"
                  />
                  <datalist id="indian-assets-list">
                    {assets.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
                  </datalist>
                </div>
              ) : (
                <Select value={assetId} onValueChange={setAssetId}>
                  <SelectTrigger className="w-[200px] bg-black/50 border-white/10 text-white text-sm" data-testid="asset-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-[#09090B] border-white/10 max-h-[300px]">
                    {assets.map(a => <SelectItem key={a.id} value={a.id}>{a.name}</SelectItem>)}
                  </SelectContent>
                </Select>
              )}
            </div>
            <div>
              <label className="text-xs text-white/40 mb-1.5 block">Strategy</label>
              {!comboMode ? (
                <Select value={strategy} onValueChange={setStrategy}>
                  <SelectTrigger className="w-[200px] bg-black/50 border-white/10 text-white text-sm" data-testid="strategy-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-[#09090B] border-white/10 max-h-[300px]">
                    {availableStrategies.map(s => <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>)}
                  </SelectContent>
                </Select>
              ) : (
                <div className="text-xs text-[#6366F1]">{selectedStrategies.length} selected</div>
              )}
            </div>
            <button
              onClick={() => { setComboMode(!comboMode); setSelectedStrategies([]); }}
              className={`px-3 py-2 rounded-md text-[10px] font-medium border transition-all ${comboMode ? 'bg-[#6366F1]/20 border-[#6366F1]/50 text-[#6366F1]' : 'bg-white/5 border-white/10 text-white/40 hover:text-white/60'}`}
              data-testid="combo-mode-toggle"
            >
              <Plus className="w-3 h-3 inline mr-1" />
              {comboMode ? 'Combo ON' : 'Combo'}
            </button>
          </div>

          {/* Row 2: Timeframes (multi-select toggle) */}
          <div>
            <label className="text-xs text-white/40 mb-2 block">
              Timeframes {planUsage?.plan_name === 'free' ? '(max 2 for free plan)' : '(select 3+ for best confluence)'}
            </label>
            <div className="flex flex-wrap gap-2" data-testid="timeframe-toggles">
              {ALL_TIMEFRAMES.map(tf => (
                <button key={tf} onClick={() => toggleTimeframe(tf)}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium border transition-all ${
                    selectedTimeframes.includes(tf)
                      ? 'bg-[#6366F1]/20 border-[#6366F1]/50 text-[#6366F1] shadow-[0_0_8px_rgba(99,102,241,0.2)]'
                      : 'bg-white/5 border-white/10 text-white/40 hover:border-white/20 hover:text-white/60'
                  }`}
                  data-testid={`tf-${tf}`}
                >
                  {tf}
                </button>
              ))}
              <span className="text-[10px] text-white/30 self-center ml-2">
                {selectedTimeframes.length} selected
              </span>
            </div>
          </div>

          {/* Combo Strategy Selector */}
          {comboMode && (
            <div>
              <label className="text-xs text-white/40 mb-2 block">Select strategies to combine (e.g. SMC + ICT + CRT)</label>
              <div className="flex flex-wrap gap-1.5" data-testid="combo-strategies">
                {availableStrategies.filter(s => s.id !== 'auto').map(s => (
                  <button key={s.id} onClick={() => toggleComboStrategy(s.id)}
                    className={`px-2.5 py-1 rounded-md text-[10px] font-medium border transition-all ${
                      selectedStrategies.includes(s.id)
                        ? 'bg-[#6366F1]/20 border-[#6366F1]/50 text-[#6366F1]'
                        : 'bg-white/5 border-white/10 text-white/40 hover:text-white/60'
                    }`}
                  >
                    {s.name}
                  </button>
                ))}
              </div>
              {selectedStrategies.length > 0 && (
                <p className="text-[10px] text-[#6366F1] mt-1">
                  Combo: {selectedStrategies.map(id => availableStrategies.find(s => s.id === id)?.name || id).join(' + ')}
                </p>
              )}
            </div>
          )}

          {/* Trading Mode & TP Levels */}
          <div className="flex flex-wrap items-end gap-4">
            <div>
              <label className="text-xs text-white/40 mb-1.5 block">Trading Mode</label>
              <div className="flex gap-1" data-testid="trading-mode-selector">
                {[
                  { id: 'scalping', label: 'Scalp' },
                  { id: 'day_trading', label: 'Day' },
                  { id: 'swing', label: 'Swing' },
                  { id: 'position', label: 'Position' },
                  { id: 'investing', label: 'Investing' },
                ].map(m => (
                  <button key={m.id} onClick={() => setTradingMode(m.id)}
                    className={`px-3 py-1.5 rounded-md text-[10px] font-medium border transition-all ${
                      tradingMode === m.id
                        ? 'bg-[#6366F1]/20 border-[#6366F1]/50 text-[#6366F1]'
                        : 'bg-white/5 border-white/10 text-white/40 hover:text-white/60'
                    }`}
                  >
                    {m.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-xs text-white/40 mb-1.5 block">Take Profit Levels</label>
              <div className="flex gap-1" data-testid="tp-count-selector">
                {[1, 2, 3].map(n => (
                  <button key={n} onClick={() => setNumTpLevels(n)}
                    className={`px-3 py-1.5 rounded-md text-xs font-medium border transition-all ${
                      numTpLevels === n
                        ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400'
                        : 'bg-white/5 border-white/10 text-white/40 hover:text-white/60'
                    }`}
                  >
                    {n} TP{n > 1 ? 's' : ''}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Advanced options toggle */}
          <button onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-xs text-[#6366F1]/70 hover:text-[#6366F1] flex items-center gap-1 transition-colors"
            data-testid="advanced-toggle"
          >
            {showAdvanced ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            {showAdvanced ? 'Hide' : 'Show'} Advanced Options
          </button>

          {showAdvanced && (
            <div className="flex flex-wrap items-end gap-4 p-3 rounded-lg bg-white/[0.02] border border-white/5">
              <div>
                <label className="text-xs text-white/40 mb-1.5 block">Profit Target (%)</label>
                <Input
                  type="number" placeholder="e.g. 5"
                  value={profitTarget} onChange={e => setProfitTarget(e.target.value)}
                  className="w-[120px] bg-black/50 border-white/10 text-white text-sm"
                  data-testid="profit-target-input"
                />
              </div>
              <div>
                <label className="text-xs text-white/40 mb-1.5 block">Risk:Reward Ratio</label>
                <Input
                  type="text" placeholder="e.g. 1:2.5"
                  value={riskReward} onChange={e => setRiskReward(e.target.value)}
                  className="w-[120px] bg-black/50 border-white/10 text-white text-sm"
                  data-testid="rr-ratio-input"
                />
              </div>
              <p className="text-[10px] text-white/30 self-center">
                Set custom R:R and profit target for tailored signals
              </p>
            </div>
          )}

          {/* Generate Button */}
          <Button
            className="bg-[#6366F1] hover:bg-[#4F46E5] text-white text-xs shadow-[0_0_15px_rgba(99,102,241,0.4)] active:scale-95 uppercase tracking-wide font-semibold px-8 py-2.5 btn-glow btn-ripple pulse-glow btn-hover-effect"
            onClick={generateSignal} disabled={generating}
            data-testid="generate-signal-btn"
          >
            {generating ? (
              <><Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" /> Analyzing {selectedTimeframes.length} Timeframes...</>
            ) : (
              <><Zap className="w-3.5 h-3.5 mr-2" /> Generate Multi-TF Signal</>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Signal Stats & Filter */}
      {signals.length > 0 && (
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5 text-xs text-white/40">
              <BarChart3 className="w-3.5 h-3.5" />
              <span className="font-data">{signals.length} signals</span>
              <span className="text-white/20">|</span>
              <span className="font-data text-[#10B981]">{buyCount} BUY</span>
              <span className="font-data text-[#EF4444]">{sellCount} SELL</span>
            </div>
          </div>
          <div className="flex gap-1">
            {['all', 'BUY', 'SELL'].map(f => (
              <button key={f} onClick={() => setFilter(f)}
                className={`px-2.5 py-1 rounded text-[10px] font-medium transition-all ${filter === f ? 'bg-[#6366F1] text-white' : 'bg-white/5 text-white/40 hover:text-white/60'}`}
                data-testid={`filter-${f}`}>
                {f === 'all' ? 'All' : f}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Signals List */}
      {loading ? (
        <div className="space-y-4">{[1,2,3].map(i => <div key={i} className="h-48 rounded-xl skeleton-shimmer" />)}</div>
      ) : signals.length === 0 ? (
        <Card className="glass-panel border-white/10">
          <CardContent className="py-16 text-center">
            <Zap className="w-12 h-12 text-white/10 mx-auto mb-3" />
            <h3 className="text-white/60 text-sm font-medium mb-1">No Signals Yet</h3>
            <p className="text-white/30 text-xs">Generate your first AI trading signal above</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {signals.filter(sig => filter === 'all' || sig.direction === filter).map((sig, i) => {
            const liveItem = allPrices.find(p => p.id === sig.asset_id);
            const currentPrice = liveItem?.price;
            const entryPrice = sig.entry_price;
            const isExpanded = expandedSignals[sig.signal_id];
            // Use database-locked TP/SL status (persisted), fallback to live check
            const hitTP1 = sig.tp1_hit || false;
            const hitTP2 = sig.tp2_hit || false;
            const hitTP3 = sig.tp3_hit || false;
            const hitSL = sig.sl_hit || false;
            const isClosed = sig.status === 'stopped_out' || sig.status === 'all_tp_hit';
            let pnlPct = null;
            if (currentPrice && entryPrice && entryPrice > 0) {
              pnlPct = sig.direction === 'BUY'
                ? ((currentPrice - entryPrice) / entryPrice) * 100
                : ((entryPrice - currentPrice) / entryPrice) * 100;
            }
            return (
              <Card key={sig.signal_id || i}
                className={`glass-panel border-white/10 card-hover overflow-hidden slide-up-fade stagger-${(i % 4) + 1} ${sig.direction === 'BUY' ? 'signal-card-buy' : 'signal-card-sell'}`}
                data-testid={`signal-card-${sig.signal_id}`}
              >
                <CardContent className="p-5">
                  <div className="flex flex-col md:flex-row md:items-start gap-5">
                    <ConfidenceRing value={sig.confidence || 0} />
                    <div className="flex-1 space-y-3 min-w-0">
                      {/* Header Row */}
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="text-sm sm:text-base font-semibold text-white">{sig.asset_name}</h3>
                        <Badge data-testid={`signal-direction-${sig.signal_id}`}
                          className={`text-[11px] font-semibold ${sig.direction === 'BUY' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'}`}>
                          {sig.direction}
                        </Badge>
                        {isClosed && (
                          <Badge className={`text-[10px] font-semibold ${sig.status === 'all_tp_hit' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                            {sig.status === 'all_tp_hit' ? 'TP Hit' : 'SL Hit'}
                          </Badge>
                        )}
                        {sig.trading_mode && (
                          <Badge variant="outline" className="text-[9px] border-cyan-500/25 text-cyan-400 capitalize">{sig.trading_mode?.replace('_', ' ')}</Badge>
                        )}
                        <Badge variant="outline" className="text-[10px] border-[#6366F1]/30 text-[#6366F1]">Grade: {sig.grade}</Badge>
                        {sig.signal_strength && (
                          <Badge variant="outline" className="text-[9px] border-amber-500/20 text-amber-400/80 font-data">{sig.signal_strength}/10</Badge>
                        )}
                        <RiskBadge riskReward={sig.risk_reward} />
                        {sig.market_regime && (
                          <Badge variant="outline" className="text-[9px] border-cyan-500/20 text-cyan-400/80">{sig.market_regime?.replace('_', ' ')}</Badge>
                        )}
                        <Badge variant="outline" className="text-[10px] border-white/15 text-white/45">{sig.market_condition}</Badge>
                        {sig.strategy_used && sig.strategy_used !== 'auto' && (
                          <Badge variant="outline" className="text-[10px] border-amber-500/25 text-amber-400">
                            {availableStrategies.find(s => s.id === sig.strategy_used)?.name || sig.strategy_used}
                          </Badge>
                        )}
                        {pnlPct !== null && (
                          <Badge className={`text-[10px] font-data ${pnlPct >= 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                            {pnlPct >= 0 ? '+' : ''}{pnlPct.toFixed(2)}% P&L
                          </Badge>
                        )}
                        {/* Delete button */}
                        <button
                          onClick={(e) => { e.stopPropagation(); deleteSignal(sig.signal_id); }}
                          disabled={deletingSignal === sig.signal_id}
                          className="ml-auto text-white/20 hover:text-red-400 transition-colors p-1"
                          data-testid={`delete-signal-${sig.signal_id}`}
                        >
                          {deletingSignal === sig.signal_id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
                        </button>
                      </div>

                      {/* Meta Row: Timeframes, Duration, Confluence */}
                      <div className="flex items-center gap-4 flex-wrap text-[10px]">
                        {sig.timeframes_analyzed && sig.timeframes_analyzed.length > 0 && (
                          <div className="flex items-center gap-1.5">
                            <Layers className="w-3 h-3 text-[#6366F1]" />
                            <span className="text-white/40">TFs:</span>
                            <div className="flex gap-1">
                              {sig.timeframes_analyzed.map(tf => (
                                <span key={tf} className="px-1.5 py-0.5 rounded bg-[#6366F1]/10 text-[#6366F1] text-[9px] font-medium">{tf}</span>
                              ))}
                            </div>
                          </div>
                        )}
                        {sig.holding_duration && (
                          <div className="flex items-center gap-1">
                            <Timer className="w-3 h-3 text-[#F59E0B]" />
                            <span className="text-white/40">Hold:</span>
                            <span className="text-white/70 font-medium">{sig.holding_duration}</span>
                          </div>
                        )}
                        {sig.confluence_score && (
                          <div className="flex items-center gap-1">
                            <Crosshair className="w-3 h-3 text-[#10B981]" />
                            <span className="text-white/40">Confluence:</span>
                            <ConfluenceDots score={sig.confluence_score} max={6} />
                          </div>
                        )}
                      </div>

                      {/* Price Levels Grid */}
                      <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 sm:gap-3">
                        <div>
                          <p className="text-[10px] text-white/40 flex items-center gap-1"><Target className="w-3 h-3" /> Entry</p>
                          <p className="text-sm sm:text-base font-data font-semibold text-white" data-testid={`entry-${sig.signal_id}`}>{entryPrice || 'N/A'}</p>
                        </div>
                        <div className={hitTP1 ? 'bg-emerald-500/5 rounded-lg p-1 -m-1' : ''}>
                          <p className="text-[10px] text-white/40 flex items-center gap-1">
                            {hitTP1 ? <><Lock className="w-3 h-3 text-emerald-400" /> <span className="text-emerald-400">TP1</span></> : <><TrendingUp className="w-3 h-3" /> TP1</>}
                          </p>
                          <p className={`text-sm sm:text-base font-data font-semibold ${hitTP1 ? 'text-emerald-400' : 'text-emerald-500/80'}`}>{sig.take_profit_1 || 'N/A'}</p>
                          {sig.risk_reward_1 && <p className="text-[8px] text-[#6366F1]/60 font-data">{sig.risk_reward_1}</p>}
                          {hitTP1 && <p className="text-[8px] text-emerald-400/60">LOCKED</p>}
                        </div>
                        {(sig.num_tp_levels || 3) >= 2 && (
                        <div className={hitTP2 ? 'bg-emerald-500/5 rounded-lg p-1 -m-1' : ''}>
                          <p className="text-[10px] text-white/40 flex items-center gap-1">
                            {hitTP2 ? <><Lock className="w-3 h-3 text-emerald-400" /> <span className="text-emerald-400">TP2</span></> : <><TrendingUp className="w-3 h-3" /> TP2</>}
                          </p>
                          <p className={`text-sm sm:text-base font-data font-semibold ${hitTP2 ? 'text-emerald-400' : 'text-emerald-500/80'}`}>{sig.take_profit_2 || 'N/A'}</p>
                          {sig.risk_reward_2 && <p className="text-[8px] text-[#6366F1]/60 font-data">{sig.risk_reward_2}</p>}
                          {hitTP2 && <p className="text-[8px] text-emerald-400/60">LOCKED</p>}
                        </div>
                        )}
                        {(sig.num_tp_levels || 3) >= 3 && (
                        <div className={hitTP3 ? 'bg-emerald-500/5 rounded-lg p-1 -m-1' : ''}>
                          <p className="text-[10px] text-white/40 flex items-center gap-1">
                            {hitTP3 ? <><Lock className="w-3 h-3 text-emerald-400" /> <span className="text-emerald-400">TP3</span></> : <><TrendingUp className="w-3 h-3" /> TP3</>}
                          </p>
                          <p className={`text-sm sm:text-base font-data font-semibold ${hitTP3 ? 'text-emerald-400' : 'text-emerald-500/60'}`}>{sig.take_profit_3 || 'N/A'}</p>
                          {sig.risk_reward_3 && <p className="text-[8px] text-[#6366F1]/60 font-data">{sig.risk_reward_3}</p>}
                          {hitTP3 && <p className="text-[8px] text-emerald-400/60">LOCKED</p>}
                        </div>
                        )}
                        <div className={hitSL ? 'bg-red-500/5 rounded-lg p-1 -m-1' : ''}>
                          <p className="text-[10px] text-white/40 flex items-center gap-1">
                            {hitSL ? <><Lock className="w-3 h-3 text-red-400" /> <span className="text-red-400">SL</span></> : <><ShieldAlert className="w-3 h-3" /> SL</>}
                          </p>
                          <p className={`text-sm sm:text-base font-data font-semibold ${hitSL ? 'text-red-400' : 'text-red-500/80'}`}>{sig.stop_loss || 'N/A'}</p>
                          {hitSL && <p className="text-[8px] text-red-400/60">STOPPED OUT</p>}
                        </div>
                        <div>
                          <p className="text-[10px] text-white/40 flex items-center gap-1"><Clock className="w-3 h-3" /> R:R</p>
                          <p className="text-sm sm:text-base font-data font-semibold text-white">{sig.risk_reward || 'N/A'}</p>
                        </div>
                      </div>

                      {/* Live price + TP/SL hit badges */}
                      {currentPrice && (
                        <div className="flex items-center gap-2 text-[10px]">
                          <span className="text-white/30">Live:</span>
                          <span className="font-data text-white/70">${currentPrice.toLocaleString()}</span>
                          {hitTP1 && <Badge className="bg-[#10B981]/10 text-[#10B981] text-[9px]"><CheckCircle2 className="w-2.5 h-2.5 mr-0.5" />TP1</Badge>}
                          {hitTP2 && <Badge className="bg-[#10B981]/10 text-[#10B981] text-[9px]"><CheckCircle2 className="w-2.5 h-2.5 mr-0.5" />TP2</Badge>}
                          {hitTP3 && <Badge className="bg-[#10B981]/10 text-[#10B981] text-[9px]"><CheckCircle2 className="w-2.5 h-2.5 mr-0.5" />TP3</Badge>}
                          {hitSL && <Badge className="bg-[#EF4444]/10 text-[#EF4444] text-[9px]"><XCircle className="w-2.5 h-2.5 mr-0.5" />SL Hit</Badge>}
                        </div>
                      )}

                      {/* Trade Logic */}
                      {sig.trade_logic && (
                        <div className="p-2.5 rounded-lg bg-[#6366F1]/[0.04] border border-[#6366F1]/10">
                          <p className="text-[10px] text-[#6366F1]/70 uppercase tracking-wider font-medium mb-1">Trade Logic</p>
                          <p className="text-xs text-white/70">{sig.trade_logic}</p>
                        </div>
                      )}

                      {/* Trade Reason */}
                      {sig.trade_reason && (
                        <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/5">
                          <p className="text-[10px] text-white/40 uppercase tracking-wider font-medium mb-1">Signal Trigger</p>
                          <p className="text-xs text-white/60">{sig.trade_reason}</p>
                        </div>
                      )}

                      {/* Expand/Collapse for additional details */}
                      <button onClick={() => toggleExpanded(sig.signal_id)}
                        className="text-[10px] text-[#6366F1]/60 hover:text-[#6366F1] flex items-center gap-1"
                        data-testid={`expand-${sig.signal_id}`}
                      >
                        {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                        {isExpanded ? 'Less' : 'More'} Details
                      </button>

                      {isExpanded && (
                        <div className="space-y-2 animate-in fade-in slide-in-from-top-2 duration-200">
                          {/* Market Regime */}
                          {sig.market_regime && (
                            <div className="flex items-center gap-2 text-[10px]">
                              <span className="text-white/40">Market Regime:</span>
                              <Badge variant="outline" className={`text-[9px] ${sig.market_regime?.includes('TREND') ? 'border-emerald-500/30 text-emerald-400' : sig.market_regime === 'RANGING' ? 'border-yellow-500/30 text-yellow-400' : 'border-orange-500/30 text-orange-400'}`}>
                                {sig.market_regime}
                              </Badge>
                            </div>
                          )}

                          {/* Indicators Used */}
                          {sig.indicators_used && typeof sig.indicators_used === 'object' && (
                            <div className="p-2.5 rounded-lg bg-[#6366F1]/[0.03] border border-[#6366F1]/10">
                              <p className="text-[10px] text-[#6366F1]/70 uppercase tracking-wider font-medium mb-1.5">Indicators</p>
                              <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-4 gap-y-1">
                                {Object.entries(sig.indicators_used).map(([k, v]) => (
                                  <div key={k} className="flex items-center justify-between text-[10px]">
                                    <span className="text-white/40 uppercase">{k}</span>
                                    <span className="font-data text-white/70 text-[9px]">{v}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {sig.analysis && (
                            <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/5">
                              <p className="text-[10px] text-white/40 uppercase tracking-wider font-medium mb-1">Analysis</p>
                              <p className="text-xs text-white/50 leading-relaxed">{sig.analysis}</p>
                            </div>
                          )}

                          {/* Scenario Analysis */}
                          {(sig.scenario_bull || sig.scenario_bear) && (
                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                              {sig.scenario_bull && (
                                <div className="p-2 rounded-lg bg-emerald-500/[0.03] border border-emerald-500/10">
                                  <p className="text-[9px] text-emerald-400/70 uppercase font-medium mb-0.5">Bull Case</p>
                                  <p className="text-[10px] text-emerald-400/60">{sig.scenario_bull}</p>
                                </div>
                              )}
                              {sig.scenario_base && (
                                <div className="p-2 rounded-lg bg-white/[0.02] border border-white/5">
                                  <p className="text-[9px] text-white/40 uppercase font-medium mb-0.5">Base Case</p>
                                  <p className="text-[10px] text-white/40">{sig.scenario_base}</p>
                                </div>
                              )}
                              {sig.scenario_bear && (
                                <div className="p-2 rounded-lg bg-red-500/[0.03] border border-red-500/10">
                                  <p className="text-[9px] text-red-400/70 uppercase font-medium mb-0.5">Bear Case</p>
                                  <p className="text-[10px] text-red-400/60">{sig.scenario_bear}</p>
                                </div>
                              )}
                            </div>
                          )}

                          {/* Confluence Checkmarks */}
                          {sig.confluence_check && typeof sig.confluence_check === 'object' && (
                            <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/5">
                              <p className="text-[10px] text-white/40 uppercase tracking-wider font-medium mb-1.5">Confluence Check ({sig.confluence_score || 0}/6)</p>
                              <div className="grid grid-cols-2 sm:grid-cols-3 gap-1">
                                {[
                                  { key: 'higher_tf_trend', label: 'Higher TF Trend' },
                                  { key: 'momentum_confirm', label: 'Momentum' },
                                  { key: 'volume_confirm', label: 'Volume' },
                                  { key: 'price_structure', label: 'Price Structure' },
                                  { key: 'volatility_suitable', label: 'Volatility' },
                                  { key: 'entry_timing', label: 'Entry Timing' },
                                ].map(c => (
                                  <div key={c.key} className="flex items-center gap-1.5 text-[10px]">
                                    {sig.confluence_check[c.key] ? (
                                      <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                                    ) : (
                                      <XCircle className="w-3 h-3 text-red-400/50" />
                                    )}
                                    <span className={sig.confluence_check[c.key] ? 'text-white/60' : 'text-white/30'}>{c.label}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Trade Management */}
                          {sig.trade_management && (
                            <div className="p-2 rounded-lg bg-amber-500/[0.03] border border-amber-500/10">
                              <p className="text-[9px] text-amber-400/70 uppercase font-medium mb-0.5">Trade Management</p>
                              <p className="text-[10px] text-amber-400/60">{sig.trade_management}</p>
                            </div>
                          )}

                          {sig.higher_tf_bias && (
                            <div className="flex items-center gap-2 text-[10px]">
                              <span className="text-white/40">Higher TF Bias:</span>
                              <span className={`font-medium ${sig.higher_tf_bias?.toLowerCase().includes('bullish') ? 'text-[#10B981]' : sig.higher_tf_bias?.toLowerCase().includes('bearish') ? 'text-[#EF4444]' : 'text-white/60'}`}>
                                {sig.higher_tf_bias}
                              </span>
                            </div>
                          )}
                          {sig.confluence_factors && sig.confluence_factors.length > 0 && (
                            <div>
                              <p className="text-[10px] text-white/40 mb-1">Confluence Factors:</p>
                              <div className="flex flex-wrap gap-1">
                                {sig.confluence_factors.map((f, idx) => (
                                  <span key={idx} className="px-2 py-0.5 rounded-full bg-[#6366F1]/10 text-[#6366F1] text-[9px]">{f}</span>
                                ))}
                              </div>
                            </div>
                          )}
                          {sig.invalidation && (
                            <div className="flex items-start gap-1.5 text-[10px]">
                              <AlertTriangle className="w-3 h-3 text-[#EAB308] flex-shrink-0 mt-0.5" />
                              <span className="text-white/40">Invalidation: <span className="text-[#EAB308]">{sig.invalidation}</span></span>
                            </div>
                          )}
                          {sig.key_levels && sig.key_levels.length > 0 && (
                            <div className="flex items-center gap-2 text-[10px] flex-wrap">
                              <span className="text-white/40">Key Levels:</span>
                              {sig.key_levels.map((lv, idx) => (
                                <span key={idx} className="font-data text-white/60">{lv}</span>
                              ))}
                            </div>
                          )}
                          {/* Push to Trade */}
                          {sig.asset_type === 'forex' && planUsage?.limits?.trade_execution && (
                            <Button
                              size="sm"
                              className="bg-[#6366F1] hover:bg-[#4F46E5] text-white text-[10px] mt-2"
                              onClick={() => executeSignal(sig.signal_id)}
                              disabled={executingSignal === sig.signal_id}
                              data-testid={`execute-signal-${sig.signal_id}`}
                            >
                              {executingSignal === sig.signal_id ? (
                                <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                              ) : (
                                <ArrowUpRight className="w-3 h-3 mr-1" />
                              )}
                              Execute as Trade
                            </Button>
                          )}
                        </div>
                      )}
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
