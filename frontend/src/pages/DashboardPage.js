import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useMarketStream } from '../hooks/useMarketStream';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown, Zap, Eye, ArrowUpRight, Activity, Wifi, WifiOff } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const fmtNum = (n) => {
  if (!n) return '$0';
  if (n >= 1e12) return `$${(n/1e12).toFixed(2)}T`;
  if (n >= 1e9) return `$${(n/1e9).toFixed(2)}B`;
  if (n >= 1e6) return `$${(n/1e6).toFixed(2)}M`;
  return `$${n.toLocaleString()}`;
};

const fmtPrice = (p) => {
  if (!p) return '$0.00';
  if (p >= 1) return `$${p.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}`;
  return `$${p.toFixed(6)}`;
};

const SentimentGauge = ({ value, label }) => {
  const angle = (value / 100) * 180 - 90;
  const c = value < 25 ? '#FF2E2E' : value < 45 ? '#F97316' : value < 55 ? '#EAB308' : value < 75 ? '#22C55E' : '#00FF94';
  return (
    <div className="flex flex-col items-center">
      <svg width="130" height="75" viewBox="0 0 140 80">
        <path d="M 10 75 A 60 60 0 0 1 130 75" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="8" strokeLinecap="round" />
        <path d="M 10 75 A 60 60 0 0 1 130 75" fill="none" stroke={c} strokeWidth="8" strokeLinecap="round" strokeDasharray={`${(value/100)*188} 188`} />
        <line x1="70" y1="75" x2={70 + 40 * Math.cos(angle * Math.PI / 180)} y2={75 - 40 * Math.sin(angle * Math.PI / 180)} stroke="white" strokeWidth="2" strokeLinecap="round" />
        <circle cx="70" cy="75" r="3.5" fill={c} />
      </svg>
      <span className="font-data text-xl font-bold text-white mt-1">{value}</span>
      <span className="text-[10px] text-white/40">{label}</span>
    </div>
  );
};

const TickerTape = ({ crypto, priceChanges }) => {
  if (!crypto || crypto.length === 0) return null;
  const items = [...crypto, ...crypto];
  return (
    <div className="overflow-hidden border-b border-white/5 bg-[#09090B]/60 -mx-4 md:-mx-6 lg:-mx-8 px-4 md:px-6 lg:px-8 mb-6">
      <div className="ticker-tape py-2">
        {items.map((c, i) => (
          <div key={`${c.id}-${i}`} className="flex items-center gap-2 shrink-0">
            {c.image && <img src={c.image} alt="" className="w-4 h-4 rounded-full" />}
            <span className="text-[11px] text-white/60">{c.symbol}</span>
            <span className={`text-[11px] font-data font-medium price-value ${priceChanges[c.id] === 'up' ? 'text-[#00FF94]' : priceChanges[c.id] === 'down' ? 'text-[#FF2E2E]' : 'text-white'}`}>
              {fmtPrice(c.price)}
            </span>
            <span className={`text-[10px] font-data ${c.change_24h >= 0 ? 'text-[#00FF94]' : 'text-[#FF2E2E]'}`}>
              {c.change_24h >= 0 ? '+' : ''}{c.change_24h?.toFixed(2)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

const MoverCard = ({ items, title, isGainer }) => (
  <Card className="glass-panel border-white/10">
    <CardHeader className="pb-2">
      <CardTitle className="text-xs text-white/60 flex items-center gap-2">
        {isGainer ? <TrendingUp className="w-3.5 h-3.5 text-[#00FF94]" /> : <TrendingDown className="w-3.5 h-3.5 text-[#FF2E2E]" />}
        {title}
      </CardTitle>
    </CardHeader>
    <CardContent className="space-y-1.5">
      {items.map((item, i) => (
        <div key={item.id} className="flex items-center justify-between py-1">
          <div className="flex items-center gap-2">
            {item.image && <img src={item.image} alt="" className="w-4 h-4 rounded-full" />}
            <span className="text-xs text-white font-medium truncate max-w-[80px]">{item.symbol || item.name}</span>
            <Badge variant="outline" className="text-[8px] border-white/10 text-white/30 py-0 h-4">{item.market}</Badge>
          </div>
          <span className={`text-xs font-data font-medium ${item.change_24h >= 0 ? 'text-[#00FF94]' : 'text-[#FF2E2E]'}`}>
            {item.change_24h >= 0 ? '+' : ''}{item.change_24h?.toFixed(2)}%
          </span>
        </div>
      ))}
    </CardContent>
  </Card>
);

export default function DashboardPage() {
  const { api } = useAuth();
  const navigate = useNavigate();
  const { crypto, forex, indian, gainers, losers, connected, tick, priceChanges, market_status } = useMarketStream(true, 1500);
  const [sentiment, setSentiment] = useState(null);
  const [signals, setSignals] = useState([]);
  const [portfolio, setPortfolio] = useState({ total_invested: 0, holdings_count: 0, holdings: [] });
  const [btcChart, setBtcChart] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [sentRes, sigRes, portRes, chartRes] = await Promise.allSettled([
          api.get('/market/sentiment'),
          api.get('/signals'),
          api.get('/portfolio/summary'),
          api.get('/market/crypto/bitcoin/chart?days=7'),
        ]);
        if (sentRes.status === 'fulfilled') setSentiment(sentRes.value.data);
        if (sigRes.status === 'fulfilled') setSignals(sigRes.value.data.signals?.slice(0, 4) || []);
        if (portRes.status === 'fulfilled') setPortfolio(portRes.value.data);
        if (chartRes.status === 'fulfilled') {
          const prices = chartRes.value.data.prices || [];
          setBtcChart(prices.filter((_, i) => i % 4 === 0).map(([t, p]) => ({
            time: new Date(t).toLocaleDateString('en', { month: 'short', day: 'numeric' }), price: p
          })));
        }
      } catch (e) { console.error(e); }
      setLoading(false);
    };
    fetchData();
  }, [api]);

  // Calculate live portfolio value
  const livePortfolioValue = portfolio.holdings?.reduce((sum, h) => {
    const allPrices = [...crypto, ...forex, ...indian];
    const liveItem = allPrices.find(p => p.id === h.asset_id);
    const currentPrice = liveItem ? liveItem.price : h.buy_price;
    return sum + (h.quantity * currentPrice);
  }, 0) || portfolio.total_invested;

  const portfolioPnL = livePortfolioValue - portfolio.total_invested;
  const portfolioPnLPct = portfolio.total_invested > 0 ? (portfolioPnL / portfolio.total_invested) * 100 : 0;

  if (loading && crypto.length === 0) {
    return <div className="space-y-6" data-testid="dashboard-loading">{[1,2,3].map(i => <div key={i} className="h-32 rounded-xl skeleton-shimmer" />)}</div>;
  }

  return (
    <div className="space-y-6" data-testid="dashboard-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white" style={{ fontFamily: 'Manrope' }}>Dashboard</h1>
          <p className="text-sm text-white/40 mt-1">Real-time market intelligence</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/5 border border-white/10" data-testid="live-indicator">
            <div className={`live-dot ${connected ? '' : 'bg-red-500'}`} />
            <span className="text-[10px] font-data text-white/50">{connected ? 'LIVE' : 'OFFLINE'}</span>
            {connected && <span className="text-[10px] font-data text-white/20">#{tick}</span>}
          </div>
          <Button className="bg-[#6366F1] hover:bg-[#4F46E5] text-white text-xs shadow-[0_0_15px_rgba(99,102,241,0.4)] active:scale-95" onClick={() => navigate('/signals')} data-testid="generate-signal-cta">
            <Zap className="w-3.5 h-3.5 mr-1.5" /> Generate Signal
          </Button>
        </div>
      </div>

      {/* Ticker Tape */}
      <TickerTape crypto={crypto} priceChanges={priceChanges} />

      {/* Market Status Bar */}
      {market_status && (!market_status.forex?.open || !market_status.indian?.open) && (
        <div className="flex flex-wrap items-center gap-3 px-4 py-2.5 rounded-lg bg-[#EAB308]/[0.04] border border-[#EAB308]/15" data-testid="market-status-bar">
          <span className="text-[10px] text-[#EAB308]/70 font-medium uppercase tracking-wider">Market Hours</span>
          <div className="flex items-center gap-1.5"><div className="w-1.5 h-1.5 rounded-full bg-[#00FF94]" /><span className="text-[10px] text-white/50 font-data">Crypto 24/7</span></div>
          <div className="flex items-center gap-1.5"><div className={`w-1.5 h-1.5 rounded-full ${market_status.forex?.open ? 'bg-[#00FF94]' : 'bg-[#EAB308]'}`} /><span className={`text-[10px] font-data ${market_status.forex?.open ? 'text-white/50' : 'text-[#EAB308]/70'}`}>Forex {market_status.forex?.label}</span></div>
          <div className="flex items-center gap-1.5"><div className={`w-1.5 h-1.5 rounded-full ${market_status.indian?.open ? 'bg-[#00FF94]' : 'bg-[#EAB308]'}`} /><span className={`text-[10px] font-data ${market_status.indian?.open ? 'text-white/50' : 'text-[#EAB308]/70'}`}>NSE {market_status.indian?.label}</span></div>
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="glass-panel border-white/10 card-hover" data-testid="portfolio-value-card">
          <CardContent className="p-5">
            <p className="text-[10px] text-white/40 uppercase tracking-wider mb-1">Portfolio Value</p>
            <p className="text-xl font-bold text-white font-data">{fmtNum(livePortfolioValue)}</p>
            {portfolio.total_invested > 0 && (
              <p className={`text-xs font-data mt-1 ${portfolioPnL >= 0 ? 'text-[#00FF94]' : 'text-[#FF2E2E]'}`}>
                {portfolioPnL >= 0 ? '+' : ''}{fmtNum(Math.abs(portfolioPnL))} ({portfolioPnLPct.toFixed(2)}%)
              </p>
            )}
          </CardContent>
        </Card>

        <Card className="glass-panel border-white/10 card-hover" data-testid="signals-count-card">
          <CardContent className="p-5">
            <p className="text-[10px] text-white/40 uppercase tracking-wider mb-1">Active Signals</p>
            <p className="text-xl font-bold text-white font-data">{signals.length}</p>
            <Badge variant="outline" className="mt-1 bg-[#6366F1]/10 text-[#6366F1] border-[#6366F1]/20 text-[10px]">AI Powered</Badge>
          </CardContent>
        </Card>

        <Card className="glass-panel border-white/10 card-hover" data-testid="total-assets-card">
          <CardContent className="p-5">
            <p className="text-[10px] text-white/40 uppercase tracking-wider mb-1">Tracked Assets</p>
            <p className="text-xl font-bold text-white font-data">{crypto.length + forex.length + indian.length}</p>
            <span className="text-[10px] text-white/30 font-data">{crypto.length}C / {forex.length}F / {indian.length}I</span>
          </CardContent>
        </Card>

        <Card className="glass-panel border-white/10 card-hover" data-testid="market-cap-card">
          <CardContent className="p-5">
            <p className="text-[10px] text-white/40 uppercase tracking-wider mb-1">Crypto Market Cap</p>
            <p className="text-xl font-bold text-white font-data">{sentiment ? fmtNum(sentiment.total_market_cap) : '...'}</p>
            {sentiment && <span className={`text-[10px] font-data ${sentiment.market_cap_change_24h >= 0 ? 'text-[#00FF94]' : 'text-[#FF2E2E]'}`}>
              {sentiment.market_cap_change_24h >= 0 ? '+' : ''}{sentiment.market_cap_change_24h?.toFixed(2)}% 24h
            </span>}
          </CardContent>
        </Card>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2/3) */}
        <div className="lg:col-span-2 space-y-6">
          {/* BTC Chart */}
          <Card className="glass-panel border-white/10" data-testid="btc-chart-card">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm text-white/80 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-[#6366F1]" /> Bitcoin 7D
                  {crypto.find(c => c.id === 'bitcoin') && (
                    <span className={`font-data text-sm ml-2 ${priceChanges['bitcoin'] === 'up' ? 'text-[#00FF94]' : priceChanges['bitcoin'] === 'down' ? 'text-[#FF2E2E]' : 'text-white'}`}>
                      {fmtPrice(crypto.find(c => c.id === 'bitcoin')?.price)}
                    </span>
                  )}
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={btcChart}>
                  <defs>
                    <linearGradient id="btcGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366F1" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#6366F1" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="time" tick={{ fill: '#52525B', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#52525B', fontSize: 10 }} axisLine={false} tickLine={false} domain={['auto', 'auto']} tickFormatter={v => `$${(v/1000).toFixed(0)}K`} />
                  <Tooltip contentStyle={{ background: 'rgba(9,9,11,0.95)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', fontSize: '12px', fontFamily: 'JetBrains Mono' }} formatter={v => [`$${v.toLocaleString()}`, 'Price']} />
                  <Area type="monotone" dataKey="price" stroke="#6366F1" strokeWidth={2} fillOpacity={1} fill="url(#btcGrad)" />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Top Gainers / Losers */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <MoverCard items={gainers} title="Top Gainers" isGainer={true} />
            <MoverCard items={losers} title="Top Losers" isGainer={false} />
          </div>

          {/* Live Top Coins */}
          <Card className="glass-panel border-white/10" data-testid="live-coins-card">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm text-white/80 flex items-center gap-2">
                  Top Crypto <div className="live-dot ml-1" />
                </CardTitle>
                <Button variant="ghost" size="sm" className="text-[#6366F1] text-xs" onClick={() => navigate('/markets')} data-testid="view-all-markets-btn">
                  View All <ArrowUpRight className="w-3 h-3 ml-1" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-white/5">
                {crypto.slice(0, 8).map((coin, i) => (
                  <div key={coin.id} className={`flex items-center justify-between px-5 py-2.5 market-row ${priceChanges[coin.id] === 'up' ? 'price-flash-up' : priceChanges[coin.id] === 'down' ? 'price-flash-down' : ''}`} data-testid={`live-coin-${coin.id}`}>
                    <div className="flex items-center gap-3">
                      <span className="text-[10px] text-white/20 w-4 font-data">{i+1}</span>
                      {coin.image && <img src={coin.image} alt="" className="w-5 h-5 rounded-full" />}
                      <div>
                        <p className="text-sm text-white font-medium">{coin.name}</p>
                        <p className="text-[10px] text-white/30 font-data">{coin.symbol}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-white font-data price-value">{fmtPrice(coin.price)}</p>
                      <p className={`text-[10px] font-data ${coin.change_24h >= 0 ? 'text-[#00FF94]' : 'text-[#FF2E2E]'}`}>
                        {coin.change_24h >= 0 ? '+' : ''}{coin.change_24h?.toFixed(2)}%
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column (1/3) */}
        <div className="space-y-6">
          {/* Sentiment */}
          {sentiment && (
            <Card className="glass-panel border-white/10" data-testid="sentiment-card">
              <CardHeader className="pb-0">
                <CardTitle className="text-sm text-white/80">Fear & Greed Index</CardTitle>
              </CardHeader>
              <CardContent className="pt-4">
                <SentimentGauge value={sentiment.fear_greed_index} label={sentiment.fear_greed_label} />
                <div className="grid grid-cols-2 gap-3 mt-4">
                  <div className="text-center"><p className="text-[10px] text-white/40">BTC Dom</p><p className="text-sm font-data text-white">{sentiment.btc_dominance?.toFixed(1)}%</p></div>
                  <div className="text-center"><p className="text-[10px] text-white/40">ETH Dom</p><p className="text-sm font-data text-white">{sentiment.eth_dominance?.toFixed(1)}%</p></div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Latest Signals */}
          <Card className="glass-panel border-white/10" data-testid="latest-signals-card">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm text-white/80">Latest Signals</CardTitle>
                <Button variant="ghost" size="sm" className="text-[#6366F1] text-xs" onClick={() => navigate('/signals')} data-testid="view-all-signals-btn">
                  <Eye className="w-3 h-3 mr-1" /> All
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {signals.length === 0 ? (
                <div className="text-center py-6">
                  <Zap className="w-8 h-8 text-white/10 mx-auto mb-2" />
                  <p className="text-xs text-white/30">No signals yet</p>
                  <Button size="sm" className="mt-3 bg-[#6366F1] hover:bg-[#4F46E5] text-white text-xs" onClick={() => navigate('/signals')} data-testid="generate-first-signal-btn">Generate First Signal</Button>
                </div>
              ) : (
                <div className="space-y-2.5">
                  {signals.map(sig => (
                    <div key={sig.signal_id} className={`p-3 rounded-lg bg-white/[0.02] border border-white/5 ${sig.direction === 'BUY' ? 'signal-card-buy' : 'signal-card-sell'}`}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-medium text-white">{sig.asset_name}</span>
                        <div className="flex items-center gap-1.5">
                          <Badge className={`text-[10px] ${sig.direction === 'BUY' ? 'bg-[#00FF94]/10 text-[#00FF94]' : 'bg-[#FF2E2E]/10 text-[#FF2E2E]'}`}>{sig.direction}</Badge>
                          <span className="text-[10px] font-data text-[#6366F1]">{sig.confidence}%</span>
                          <span className="text-[10px] font-data text-white/40">{sig.grade}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Live Forex Quick */}
          <Card className="glass-panel border-white/10" data-testid="live-forex-mini">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-white/80 flex items-center gap-2">
                Forex
                {market_status?.forex?.open ? (
                  <div className="live-dot ml-1" />
                ) : (
                  <Badge variant="outline" className="ml-1 text-[8px] border-[#EAB308]/30 text-[#EAB308] py-0 h-4">CLOSED</Badge>
                )}
                <span className="text-[8px] text-[#6366F1]/60 ml-auto">OANDA</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-1.5">
              {!market_status?.forex?.open && (
                <p className="text-[10px] text-white/30 mb-2">Showing last closing prices</p>
              )}
              {forex.slice(0, 6).map(pair => (
                <div key={pair.id} className={`flex items-center justify-between py-1.5 ${priceChanges[pair.id] === 'up' ? 'price-flash-up' : priceChanges[pair.id] === 'down' ? 'price-flash-down' : ''}`}>
                  <span className="text-xs text-white/60">{pair.symbol}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-data text-white/40">{pair.bid ? (pair.bid < 50 ? pair.bid.toFixed(5) : pair.bid.toFixed(2)) : ''}</span>
                    <span className="text-xs font-data text-white price-value font-medium">{pair.ask ? (pair.ask < 50 ? pair.ask.toFixed(5) : pair.ask.toFixed(2)) : (pair.price < 50 ? pair.price.toFixed(4) : pair.price.toFixed(2))}</span>
                    <span className={`text-[10px] font-data ${pair.change_24h >= 0 ? 'text-[#00FF94]' : 'text-[#FF2E2E]'}`}>
                      {pair.change_24h >= 0 ? '+' : ''}{pair.change_24h?.toFixed(2)}%
                    </span>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
