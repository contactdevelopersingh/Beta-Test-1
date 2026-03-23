import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useMarketStream } from '../hooks/useMarketStream';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Zap, Target, ShieldAlert, TrendingUp, TrendingDown, Clock, Loader2, CheckCircle2, XCircle, BarChart3 } from 'lucide-react';
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
  { id: 'tatamotors', name: 'Tata Motors' }, { id: 'bhartiartl', name: 'Bharti Airtel' },
  { id: 'bajfinance', name: 'Bajaj Finance' }, { id: 'adanient', name: 'Adani Enterprises' },
];

const TIMEFRAMES = ['5m', '15m', '1H', '4H', '1D', '1W'];

const ConfidenceRing = ({ value }) => {
  const r = 28, c = 2 * Math.PI * r;
  const color = value >= 80 ? '#00FF94' : value >= 60 ? '#6366F1' : value >= 40 ? '#EAB308' : '#FF2E2E';
  return (
    <div className="relative w-20 h-20 flex items-center justify-center">
      <svg className="w-20 h-20 -rotate-90" viewBox="0 0 64 64">
        <circle cx="32" cy="32" r={r} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="4" />
        <circle cx="32" cy="32" r={r} fill="none" stroke={color} strokeWidth="4" strokeLinecap="round"
          strokeDasharray={`${(value/100)*c} ${c}`} className="confidence-ring" />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-lg font-bold font-data text-white">{value}%</span>
      </div>
    </div>
  );
};

export default function SignalsPage() {
  const { api } = useAuth();
  const { crypto, forex, indian } = useMarketStream(true, 2000);
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [assetType, setAssetType] = useState('crypto');
  const [assetId, setAssetId] = useState('bitcoin');
  const [timeframe, setTimeframe] = useState('1D');
  const [filter, setFilter] = useState('all');

  const assets = assetType === 'crypto' ? CRYPTO_ASSETS : assetType === 'forex' ? FOREX_ASSETS : INDIAN_ASSETS;
  const allPrices = [...crypto, ...forex, ...indian];

  useEffect(() => {
    fetchSignals();
  }, []);

  useEffect(() => {
    setAssetId(assets[0]?.id || '');
  }, [assetType]);

  const fetchSignals = async () => {
    try {
      const res = await api.get('/signals');
      setSignals(res.data.signals || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const generateSignal = async () => {
    const asset = assets.find(a => a.id === assetId);
    if (!asset) return;
    setGenerating(true);
    try {
      const res = await api.post('/signals/generate', {
        asset_id: assetId, asset_name: asset.name,
        asset_type: assetType, timeframe
      });
      setSignals(prev => [res.data, ...prev]);
      toast.success(`Signal generated for ${asset.name}`);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to generate signal');
    }
    setGenerating(false);
  };

  return (
    <div className="space-y-6" data-testid="signals-page">
      <div>
        <h1 className="text-2xl font-bold text-white" style={{ fontFamily: 'Manrope' }}>AI Trading Signals</h1>
        <p className="text-sm text-white/40 mt-1">Generate institutional-grade signals powered by AI</p>
      </div>

      {/* Generate Signal */}
      <Card className="glass-panel border-white/10 border-l-2 border-l-[#6366F1]" data-testid="signal-generator-card">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm text-white/80 flex items-center gap-2">
            <Zap className="w-4 h-4 text-[#6366F1]" /> Generate New Signal
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-end gap-4">
            <div>
              <label className="text-xs text-white/40 mb-1.5 block">Market</label>
              <Select value={assetType} onValueChange={setAssetType}>
                <SelectTrigger className="w-[140px] bg-black/50 border-white/10 text-white text-sm" data-testid="market-select">
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
              <label className="text-xs text-white/40 mb-1.5 block">Asset</label>
              <Select value={assetId} onValueChange={setAssetId}>
                <SelectTrigger className="w-[200px] bg-black/50 border-white/10 text-white text-sm" data-testid="asset-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-[#09090B] border-white/10">
                  {assets.map(a => <SelectItem key={a.id} value={a.id}>{a.name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-xs text-white/40 mb-1.5 block">Timeframe</label>
              <Select value={timeframe} onValueChange={setTimeframe}>
                <SelectTrigger className="w-[100px] bg-black/50 border-white/10 text-white text-sm" data-testid="timeframe-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-[#09090B] border-white/10">
                  {TIMEFRAMES.map(tf => <SelectItem key={tf} value={tf}>{tf}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <Button
              className="bg-[#6366F1] hover:bg-[#4F46E5] text-white text-xs shadow-[0_0_15px_rgba(99,102,241,0.4)] active:scale-95 uppercase tracking-wide font-semibold px-6"
              onClick={generateSignal} disabled={generating}
              data-testid="generate-signal-btn"
            >
              {generating ? <><Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" /> Analyzing...</> : <><Zap className="w-3.5 h-3.5 mr-1.5" /> Generate Signal</>}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Signal Stats & Filter */}
      {signals.length > 0 && (
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5 text-xs text-white/40">
              <BarChart3 className="w-3.5 h-3.5" />
              <span className="font-data">{signals.length} signals</span>
              <span className="text-white/20">|</span>
              <span className="font-data text-[#00FF94]">{signals.filter(s => s.direction === 'BUY').length} BUY</span>
              <span className="font-data text-[#FF2E2E]">{signals.filter(s => s.direction === 'SELL').length} SELL</span>
            </div>
          </div>
          <div className="flex gap-1">
            {['all', 'BUY', 'SELL'].map(f => (
              <button key={f} onClick={() => setFilter(f)}
                className={`px-2.5 py-1 rounded text-[10px] font-medium ${filter === f ? 'bg-[#6366F1] text-white' : 'bg-white/5 text-white/40 hover:text-white/60'}`}
                data-testid={`filter-${f}`}>
                {f === 'all' ? 'All' : f}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Signals List */}
      {loading ? (
        <div className="space-y-4">{[1,2,3].map(i => <div key={i} className="h-40 rounded-xl skeleton-shimmer" />)}</div>
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
            let pnlPct = null;
            let hitTP1 = false, hitTP2 = false, hitSL = false;
            if (currentPrice && entryPrice && entryPrice > 0) {
              if (sig.direction === 'BUY') {
                pnlPct = ((currentPrice - entryPrice) / entryPrice) * 100;
                hitTP1 = sig.take_profit_1 && currentPrice >= sig.take_profit_1;
                hitTP2 = sig.take_profit_2 && currentPrice >= sig.take_profit_2;
                hitSL = sig.stop_loss && currentPrice <= sig.stop_loss;
              } else {
                pnlPct = ((entryPrice - currentPrice) / entryPrice) * 100;
                hitTP1 = sig.take_profit_1 && currentPrice <= sig.take_profit_1;
                hitTP2 = sig.take_profit_2 && currentPrice <= sig.take_profit_2;
                hitSL = sig.stop_loss && currentPrice >= sig.stop_loss;
              }
            }
            return (
            <Card key={sig.signal_id || i} className={`glass-panel border-white/10 card-hover ${sig.direction === 'BUY' ? 'signal-card-buy' : 'signal-card-sell'}`} data-testid={`signal-card-${sig.signal_id}`}>
              <CardContent className="p-5">
                <div className="flex flex-col md:flex-row md:items-center gap-5">
                  <ConfidenceRing value={sig.confidence || 0} />
                  <div className="flex-1 space-y-3">
                    <div className="flex items-center gap-3 flex-wrap">
                      <h3 className="text-base font-semibold text-white">{sig.asset_name}</h3>
                      <Badge className={`text-xs ${sig.direction === 'BUY' ? 'bg-[#00FF94]/10 text-[#00FF94] border-[#00FF94]/20' : 'bg-[#FF2E2E]/10 text-[#FF2E2E] border-[#FF2E2E]/20'}`}>
                        {sig.direction}
                      </Badge>
                      <Badge variant="outline" className="text-[10px] border-[#6366F1]/30 text-[#6366F1]">Grade: {sig.grade}</Badge>
                      <Badge variant="outline" className="text-[10px] border-white/20 text-white/50">{sig.market_condition}</Badge>
                      {pnlPct !== null && (
                        <Badge className={`text-[10px] ${pnlPct >= 0 ? 'bg-[#00FF94]/10 text-[#00FF94]' : 'bg-[#FF2E2E]/10 text-[#FF2E2E]'}`}>
                          {pnlPct >= 0 ? '+' : ''}{pnlPct.toFixed(2)}% P&L
                        </Badge>
                      )}
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                      <div>
                        <p className="text-[10px] text-white/40 flex items-center gap-1"><Target className="w-3 h-3" /> Entry</p>
                        <p className="text-sm font-data text-white">{entryPrice || 'N/A'}</p>
                      </div>
                      <div>
                        <p className="text-[10px] text-white/40 flex items-center gap-1">
                          {hitTP1 ? <CheckCircle2 className="w-3 h-3 text-[#00FF94]" /> : <TrendingUp className="w-3 h-3" />} TP1
                        </p>
                        <p className={`text-sm font-data ${hitTP1 ? 'text-[#00FF94] font-bold' : 'text-[#00FF94]'}`}>{sig.take_profit_1 || 'N/A'}</p>
                      </div>
                      <div>
                        <p className="text-[10px] text-white/40 flex items-center gap-1">
                          {hitTP2 ? <CheckCircle2 className="w-3 h-3 text-[#00FF94]" /> : <TrendingUp className="w-3 h-3" />} TP2
                        </p>
                        <p className={`text-sm font-data ${hitTP2 ? 'text-[#00FF94] font-bold' : 'text-[#00FF94]'}`}>{sig.take_profit_2 || 'N/A'}</p>
                      </div>
                      <div>
                        <p className="text-[10px] text-white/40 flex items-center gap-1">
                          {hitSL ? <XCircle className="w-3 h-3 text-[#FF2E2E]" /> : <ShieldAlert className="w-3 h-3" />} Stop Loss
                        </p>
                        <p className={`text-sm font-data ${hitSL ? 'text-[#FF2E2E] font-bold' : 'text-[#FF2E2E]'}`}>{sig.stop_loss || 'N/A'}</p>
                      </div>
                      <div>
                        <p className="text-[10px] text-white/40 flex items-center gap-1"><Clock className="w-3 h-3" /> R:R</p>
                        <p className="text-sm font-data text-white">{sig.risk_reward || 'N/A'}</p>
                      </div>
                    </div>
                    {currentPrice && (
                      <div className="flex items-center gap-2 text-[10px]">
                        <span className="text-white/30">Live:</span>
                        <span className="font-data text-white/70">${currentPrice.toLocaleString()}</span>
                        {hitTP1 && <Badge className="bg-[#00FF94]/10 text-[#00FF94] text-[9px]"><CheckCircle2 className="w-2.5 h-2.5 mr-0.5" />TP1 Hit</Badge>}
                        {hitTP2 && <Badge className="bg-[#00FF94]/10 text-[#00FF94] text-[9px]"><CheckCircle2 className="w-2.5 h-2.5 mr-0.5" />TP2 Hit</Badge>}
                        {hitSL && <Badge className="bg-[#FF2E2E]/10 text-[#FF2E2E] text-[9px]"><XCircle className="w-2.5 h-2.5 mr-0.5" />SL Hit</Badge>}
                      </div>
                    )}
                    {sig.trade_logic && (
                      <div className="mt-2 p-2.5 rounded-lg bg-[#6366F1]/[0.04] border border-[#6366F1]/10">
                        <p className="text-[10px] text-[#6366F1]/70 uppercase tracking-wider font-medium mb-1">Trade Logic</p>
                        <p className="text-xs text-white/70">{sig.trade_logic}</p>
                      </div>
                    )}
                    {sig.trade_reason && (
                      <div className="mt-1.5 p-2.5 rounded-lg bg-white/[0.02] border border-white/5">
                        <p className="text-[10px] text-white/40 uppercase tracking-wider font-medium mb-1">Signal Trigger</p>
                        <p className="text-xs text-white/60">{sig.trade_reason}</p>
                      </div>
                    )}
                    {sig.analysis && <p className="text-xs text-white/50 leading-relaxed mt-2">{sig.analysis}</p>}
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
