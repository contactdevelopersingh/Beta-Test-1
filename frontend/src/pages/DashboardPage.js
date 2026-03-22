import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown, Zap, Eye, ArrowUpRight, Activity } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const formatNum = (n) => {
  if (!n) return '$0';
  if (n >= 1e12) return `$${(n/1e12).toFixed(2)}T`;
  if (n >= 1e9) return `$${(n/1e9).toFixed(2)}B`;
  if (n >= 1e6) return `$${(n/1e6).toFixed(2)}M`;
  return `$${n.toLocaleString()}`;
};

const formatPrice = (p) => {
  if (!p) return '$0.00';
  return p >= 1 ? `$${p.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : `$${p.toFixed(6)}`;
};

const SentimentGauge = ({ value, label }) => {
  const angle = (value / 100) * 180 - 90;
  const color = value < 25 ? '#FF2E2E' : value < 45 ? '#F97316' : value < 55 ? '#EAB308' : value < 75 ? '#22C55E' : '#00FF94';
  return (
    <div className="flex flex-col items-center">
      <svg width="140" height="80" viewBox="0 0 140 80">
        <path d="M 10 75 A 60 60 0 0 1 130 75" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="8" strokeLinecap="round" />
        <path d="M 10 75 A 60 60 0 0 1 130 75" fill="none" stroke={color} strokeWidth="8" strokeLinecap="round" strokeDasharray={`${(value/100)*188} 188`} />
        <line x1="70" y1="75" x2={70 + 40 * Math.cos(angle * Math.PI / 180)} y2={75 - 40 * Math.sin(angle * Math.PI / 180)} stroke="white" strokeWidth="2" strokeLinecap="round" />
        <circle cx="70" cy="75" r="4" fill={color} />
      </svg>
      <span className="font-data text-2xl font-bold text-white mt-1">{value}</span>
      <span className="text-xs text-white/40 mt-0.5">{label}</span>
    </div>
  );
};

export default function DashboardPage() {
  const { api } = useAuth();
  const navigate = useNavigate();
  const [coins, setCoins] = useState([]);
  const [sentiment, setSentiment] = useState(null);
  const [signals, setSignals] = useState([]);
  const [portfolio, setPortfolio] = useState({ total_invested: 0, holdings_count: 0 });
  const [btcChart, setBtcChart] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [coinsRes, sentRes, sigRes, portRes, chartRes] = await Promise.allSettled([
          api.get('/market/crypto/top?limit=10'),
          api.get('/market/sentiment'),
          api.get('/signals'),
          api.get('/portfolio/summary'),
          api.get('/market/crypto/bitcoin/chart?days=7'),
        ]);
        if (coinsRes.status === 'fulfilled') setCoins(coinsRes.value.data.coins || []);
        if (sentRes.status === 'fulfilled') setSentiment(sentRes.value.data);
        if (sigRes.status === 'fulfilled') setSignals(sigRes.value.data.signals?.slice(0, 3) || []);
        if (portRes.status === 'fulfilled') setPortfolio(portRes.value.data);
        if (chartRes.status === 'fulfilled') {
          const prices = chartRes.value.data.prices || [];
          setBtcChart(prices.filter((_, i) => i % 4 === 0).map(([t, p]) => ({ time: new Date(t).toLocaleDateString('en', { month: 'short', day: 'numeric' }), price: p })));
        }
      } catch (e) { console.error(e); }
      setLoading(false);
    };
    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, [api]);

  if (loading) {
    return (
      <div className="space-y-6" data-testid="dashboard-loading">
        {[1,2,3].map(i => <div key={i} className="h-32 rounded-xl skeleton-shimmer" />)}
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="dashboard-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white" style={{ fontFamily: 'Manrope' }}>Dashboard</h1>
          <p className="text-sm text-white/40 mt-1">Market overview & trading intelligence</p>
        </div>
        <Button className="bg-[#6366F1] hover:bg-[#4F46E5] text-white text-xs shadow-[0_0_15px_rgba(99,102,241,0.4)] active:scale-95" onClick={() => navigate('/signals')} data-testid="generate-signal-cta">
          <Zap className="w-3.5 h-3.5 mr-1.5" /> Generate Signal
        </Button>
      </div>

      {/* Top Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="glass-panel border-white/10 card-hover" data-testid="portfolio-summary-card">
          <CardContent className="p-5">
            <p className="text-xs text-white/40 mb-1">Portfolio Value</p>
            <p className="text-2xl font-bold text-white font-data">{formatNum(portfolio.total_invested)}</p>
            <div className="flex items-center gap-2 mt-2">
              <Badge variant="outline" className="bg-[#00FF94]/10 text-[#00FF94] border-[#00FF94]/20 text-[10px]">{portfolio.holdings_count} Holdings</Badge>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-panel border-white/10 card-hover" data-testid="signals-summary-card">
          <CardContent className="p-5">
            <p className="text-xs text-white/40 mb-1">Active Signals</p>
            <p className="text-2xl font-bold text-white font-data">{signals.length}</p>
            <div className="flex items-center gap-2 mt-2">
              <Badge variant="outline" className="bg-[#6366F1]/10 text-[#6366F1] border-[#6366F1]/20 text-[10px]">AI Powered</Badge>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-panel border-white/10 card-hover" data-testid="market-summary-card">
          <CardContent className="p-5">
            <p className="text-xs text-white/40 mb-1">Total Market Cap</p>
            <p className="text-2xl font-bold text-white font-data">{sentiment ? formatNum(sentiment.total_market_cap) : '...'}</p>
            <div className="flex items-center gap-2 mt-2">
              {sentiment && (
                <span className={`text-xs font-data ${sentiment.market_cap_change_24h >= 0 ? 'text-[#00FF94]' : 'text-[#FF2E2E]'}`}>
                  {sentiment.market_cap_change_24h >= 0 ? '+' : ''}{sentiment.market_cap_change_24h?.toFixed(2)}% 24h
                </span>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* BTC Chart + Top Coins (2 cols) */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="glass-panel border-white/10" data-testid="btc-chart-card">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-white/80 flex items-center gap-2">
                <Activity className="w-4 h-4 text-[#6366F1]" /> Bitcoin 7D Price
              </CardTitle>
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
                  <Tooltip contentStyle={{ background: 'rgba(9,9,11,0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', fontSize: '12px', fontFamily: 'JetBrains Mono' }} formatter={v => [`$${v.toLocaleString()}`, 'Price']} />
                  <Area type="monotone" dataKey="price" stroke="#6366F1" strokeWidth={2} fillOpacity={1} fill="url(#btcGrad)" />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card className="glass-panel border-white/10" data-testid="top-coins-card">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm text-white/80">Top Cryptocurrencies</CardTitle>
                <Button variant="ghost" size="sm" className="text-[#6366F1] text-xs" onClick={() => navigate('/markets')} data-testid="view-all-markets-btn">
                  View All <ArrowUpRight className="w-3 h-3 ml-1" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-white/5">
                {coins.slice(0, 6).map((coin, i) => (
                  <div key={coin.id} className="flex items-center justify-between px-5 py-3 market-row" data-testid={`coin-row-${coin.id}`}>
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-white/30 w-4 font-data">{i + 1}</span>
                      {coin.image && <img src={coin.image} alt={coin.name} className="w-6 h-6 rounded-full" />}
                      <div>
                        <p className="text-sm text-white font-medium">{coin.name}</p>
                        <p className="text-[10px] text-white/40 uppercase font-data">{coin.symbol}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-white font-data">{formatPrice(coin.current_price)}</p>
                      <p className={`text-[10px] font-data flex items-center justify-end gap-0.5 ${coin.price_change_percentage_24h >= 0 ? 'text-[#00FF94]' : 'text-[#FF2E2E]'}`}>
                        {coin.price_change_percentage_24h >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                        {coin.price_change_percentage_24h?.toFixed(2)}%
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Sidebar Widgets */}
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
                  <div className="text-center">
                    <p className="text-[10px] text-white/40">BTC Dom</p>
                    <p className="text-sm font-data text-white">{sentiment.btc_dominance?.toFixed(1)}%</p>
                  </div>
                  <div className="text-center">
                    <p className="text-[10px] text-white/40">ETH Dom</p>
                    <p className="text-sm font-data text-white">{sentiment.eth_dominance?.toFixed(1)}%</p>
                  </div>
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
                  <Eye className="w-3 h-3 mr-1" /> View All
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {signals.length === 0 ? (
                <div className="text-center py-6">
                  <Zap className="w-8 h-8 text-white/10 mx-auto mb-2" />
                  <p className="text-xs text-white/30">No signals yet</p>
                  <Button size="sm" className="mt-3 bg-[#6366F1] hover:bg-[#4F46E5] text-white text-xs" onClick={() => navigate('/signals')} data-testid="generate-first-signal-btn">
                    Generate First Signal
                  </Button>
                </div>
              ) : (
                <div className="space-y-3">
                  {signals.map(sig => (
                    <div key={sig.signal_id} className={`p-3 rounded-lg bg-white/[0.02] border border-white/5 ${sig.direction === 'BUY' ? 'signal-card-buy' : 'signal-card-sell'}`}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-medium text-white">{sig.asset_name}</span>
                        <Badge className={`text-[10px] ${sig.direction === 'BUY' ? 'bg-[#00FF94]/10 text-[#00FF94]' : 'bg-[#FF2E2E]/10 text-[#FF2E2E]'}`}>
                          {sig.direction}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-white/40">Confidence:</span>
                        <span className="text-xs font-data text-[#6366F1]">{sig.confidence}%</span>
                        <span className="text-[10px] text-white/30">|</span>
                        <span className="text-xs font-data text-white/60">{sig.grade}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
