import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useMarketStream } from '../hooks/useMarketStream';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { AreaChart, Area, ResponsiveContainer } from 'recharts';
import { Search, TrendingUp, TrendingDown, Star, RefreshCw, Wifi } from 'lucide-react';
import { toast } from 'sonner';

const fmtPrice = (p, dec) => {
  if (!p) return '0';
  return p >= 1 ? p.toLocaleString(undefined, {minimumFractionDigits: dec||2, maximumFractionDigits: dec||2}) : p.toFixed(6);
};
const fmtVol = (v) => {
  if (!v) return '-';
  if (v >= 1e12) return `${(v/1e12).toFixed(1)}T`;
  if (v >= 1e9) return `${(v/1e9).toFixed(1)}B`;
  if (v >= 1e6) return `${(v/1e6).toFixed(1)}M`;
  return v.toLocaleString();
};

const MiniChart = ({ data, positive }) => {
  if (!data || data.length < 5) return null;
  const pts = data.filter((_, i) => i % Math.ceil(data.length / 20) === 0).map(v => ({ v }));
  const col = positive ? '#00FF94' : '#FF2E2E';
  return (
    <ResponsiveContainer width={80} height={28}>
      <AreaChart data={pts}>
        <defs><linearGradient id={`mc${positive?'g':'r'}`} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={col} stopOpacity={0.2}/><stop offset="100%" stopColor={col} stopOpacity={0}/></linearGradient></defs>
        <Area type="monotone" dataKey="v" stroke={col} strokeWidth={1.5} fill={`url(#mc${positive?'g':'r'})`} dot={false} />
      </AreaChart>
    </ResponsiveContainer>
  );
};

export default function MarketsPage() {
  const { api } = useAuth();
  const { crypto, forex, indian, connected, tick, priceChanges } = useMarketStream(true, 1500);
  const [tab, setTab] = useState('crypto');
  const [search, setSearch] = useState('');
  const [sparklines, setSparklines] = useState({});

  // Fetch sparklines once from CoinGecko (they don't change every second)
  useEffect(() => {
    const fetchSparklines = async () => {
      try {
        const res = await api.get('/market/crypto/top?limit=20');
        const sp = {};
        (res.data.coins || []).forEach(c => { sp[c.id] = c.sparkline_in_7d?.price; });
        setSparklines(sp);
      } catch {}
    };
    fetchSparklines();
  }, [api]);

  const addToWatchlist = async (asset_id, asset_name, asset_type) => {
    try {
      await api.post('/watchlist', { asset_id, asset_name, asset_type });
      toast.success(`${asset_name} added to watchlist`);
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed'); }
  };

  const filteredCrypto = crypto.filter(c => c.name?.toLowerCase().includes(search.toLowerCase()) || c.symbol?.toLowerCase().includes(search.toLowerCase()));
  const filteredForex = forex.filter(p => p.name?.toLowerCase().includes(search.toLowerCase()) || p.symbol?.toLowerCase().includes(search.toLowerCase()));
  const filteredIndian = indian.filter(s => s.name?.toLowerCase().includes(search.toLowerCase()) || s.symbol?.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="space-y-6" data-testid="markets-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white" style={{ fontFamily: 'Manrope' }}>Markets</h1>
          <p className="text-sm text-white/40 mt-1">Real-time prices across all markets</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/5 border border-white/10" data-testid="market-live-indicator">
            <div className={`live-dot ${connected ? '' : 'bg-red-500'}`} />
            <span className="text-[10px] font-data text-white/50">{connected ? 'LIVE' : 'CONNECTING...'}</span>
          </div>
        </div>
      </div>

      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
        <Input className="pl-10 bg-black/50 border-white/10 text-white text-sm" placeholder="Search markets..." value={search} onChange={e => setSearch(e.target.value)} data-testid="market-search-input" />
      </div>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="bg-white/5">
          <TabsTrigger value="crypto" className="text-xs data-[state=active]:bg-[#6366F1] data-[state=active]:text-white" data-testid="crypto-tab">
            <Wifi className="w-3 h-3 mr-1 text-[#00FF94]" /> Crypto ({crypto.length})
          </TabsTrigger>
          <TabsTrigger value="forex" className="text-xs data-[state=active]:bg-[#6366F1] data-[state=active]:text-white" data-testid="forex-tab">
            <Wifi className="w-3 h-3 mr-1 text-[#00FF94]" /> Forex ({forex.length})
          </TabsTrigger>
          <TabsTrigger value="indian" className="text-xs data-[state=active]:bg-[#6366F1] data-[state=active]:text-white" data-testid="indian-tab">
            <Wifi className="w-3 h-3 mr-1 text-[#00FF94]" /> Indian ({indian.length})
          </TabsTrigger>
        </TabsList>

        {/* CRYPTO TAB */}
        <TabsContent value="crypto" className="mt-4">
          <Card className="glass-panel border-white/10 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="sticky top-0 bg-[#09090B]/95 backdrop-blur-sm border-b border-white/5">
                  <tr className="text-[10px] text-white/40 uppercase tracking-wider">
                    <th className="text-left py-3 px-4">#</th>
                    <th className="text-left py-3 px-4">Name</th>
                    <th className="text-right py-3 px-4">Price</th>
                    <th className="text-right py-3 px-4">24h</th>
                    <th className="text-right py-3 px-4 hidden md:table-cell">7d Chart</th>
                    <th className="text-right py-3 px-4 hidden sm:table-cell">Market Cap</th>
                    <th className="text-right py-3 px-4 hidden lg:table-cell">Volume</th>
                    <th className="text-right py-3 px-4"></th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCrypto.map((coin, i) => (
                    <tr key={coin.id} className={`market-row border-b border-white/[0.03] ${priceChanges[coin.id] === 'up' ? 'price-flash-up' : priceChanges[coin.id] === 'down' ? 'price-flash-down' : ''}`} data-testid={`market-crypto-${coin.id}`}>
                      <td className="py-3 px-4 text-xs text-white/30 font-data">{i+1}</td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2.5">
                          {coin.image && <img src={coin.image} alt="" className="w-6 h-6 rounded-full" />}
                          <div><p className="text-sm text-white font-medium">{coin.name}</p><p className="text-[10px] text-white/40 font-data">{coin.symbol}</p></div>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-right text-sm text-white font-data price-value">${fmtPrice(coin.price)}</td>
                      <td className={`py-3 px-4 text-right text-xs font-data ${coin.change_24h >= 0 ? 'text-[#00FF94]' : 'text-[#FF2E2E]'}`}>
                        <span className="flex items-center justify-end gap-0.5">
                          {coin.change_24h >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                          {coin.change_24h?.toFixed(2)}%
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right hidden md:table-cell">
                        <MiniChart data={sparklines[coin.id]} positive={coin.change_24h >= 0} />
                      </td>
                      <td className="py-3 px-4 text-right text-xs text-white/60 font-data hidden sm:table-cell">${fmtVol(coin.market_cap)}</td>
                      <td className="py-3 px-4 text-right text-xs text-white/40 font-data hidden lg:table-cell">${fmtVol(coin.volume)}</td>
                      <td className="py-3 px-4 text-right">
                        <Button variant="ghost" size="icon" className="w-7 h-7 text-white/30 hover:text-[#6366F1]" onClick={() => addToWatchlist(coin.id, coin.name, 'crypto')} data-testid={`watchlist-add-${coin.id}`}>
                          <Star className="w-3.5 h-3.5" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </TabsContent>

        {/* FOREX TAB */}
        <TabsContent value="forex" className="mt-4">
          <Card className="glass-panel border-white/10 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="sticky top-0 bg-[#09090B]/95 backdrop-blur-sm border-b border-white/5">
                  <tr className="text-[10px] text-white/40 uppercase tracking-wider">
                    <th className="text-left py-3 px-4">Pair</th>
                    <th className="text-right py-3 px-4">Price</th>
                    <th className="text-right py-3 px-4">Change</th>
                    <th className="text-right py-3 px-4 hidden sm:table-cell">High</th>
                    <th className="text-right py-3 px-4 hidden sm:table-cell">Low</th>
                    <th className="text-right py-3 px-4 hidden md:table-cell">Prev Close</th>
                    <th className="text-right py-3 px-4"></th>
                  </tr>
                </thead>
                <tbody>
                  {filteredForex.map(pair => (
                    <tr key={pair.id} className={`market-row border-b border-white/[0.03] ${priceChanges[pair.id] === 'up' ? 'price-flash-up' : priceChanges[pair.id] === 'down' ? 'price-flash-down' : ''}`} data-testid={`market-forex-${pair.id}`}>
                      <td className="py-3 px-4">
                        <span className="text-sm text-white font-medium">{pair.symbol}</span>
                        {pair.name !== pair.symbol && <span className="text-[10px] text-white/30 ml-2">{pair.name}</span>}
                      </td>
                      <td className="py-3 px-4 text-right text-sm text-white font-data font-medium price-value">{fmtPrice(pair.price, pair.price < 50 ? 4 : 2)}</td>
                      <td className={`py-3 px-4 text-right text-xs font-data font-medium ${pair.change_24h >= 0 ? 'text-[#00FF94]' : 'text-[#FF2E2E]'}`}>
                        {pair.change_24h >= 0 ? '+' : ''}{pair.change_24h?.toFixed(2)}%
                      </td>
                      <td className="py-3 px-4 text-right text-xs text-white/50 font-data hidden sm:table-cell">{fmtPrice(pair.high, pair.price < 50 ? 4 : 2)}</td>
                      <td className="py-3 px-4 text-right text-xs text-white/50 font-data hidden sm:table-cell">{fmtPrice(pair.low, pair.price < 50 ? 4 : 2)}</td>
                      <td className="py-3 px-4 text-right text-xs text-white/40 font-data hidden md:table-cell">{pair.prev_close ? fmtPrice(pair.prev_close, pair.price < 50 ? 4 : 2) : '-'}</td>
                      <td className="py-3 px-4 text-right">
                        <Button variant="ghost" size="icon" className="w-7 h-7 text-white/30 hover:text-[#6366F1]" onClick={() => addToWatchlist(pair.id, pair.name, 'forex')} data-testid={`watchlist-add-${pair.id}`}>
                          <Star className="w-3.5 h-3.5" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </TabsContent>

        {/* INDIAN TAB */}
        <TabsContent value="indian" className="mt-4">
          <Card className="glass-panel border-white/10 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="sticky top-0 bg-[#09090B]/95 backdrop-blur-sm border-b border-white/5">
                  <tr className="text-[10px] text-white/40 uppercase tracking-wider">
                    <th className="text-left py-3 px-4">Name</th>
                    <th className="text-left py-3 px-4">Symbol</th>
                    <th className="text-right py-3 px-4">Price (INR)</th>
                    <th className="text-right py-3 px-4">Change</th>
                    <th className="text-right py-3 px-4 hidden sm:table-cell">High</th>
                    <th className="text-right py-3 px-4 hidden sm:table-cell">Low</th>
                    <th className="text-right py-3 px-4 hidden md:table-cell">Volume</th>
                    <th className="text-right py-3 px-4"></th>
                  </tr>
                </thead>
                <tbody>
                  {/* Indices */}
                  {filteredIndian.filter(s => s.type === 'index').length > 0 && (
                    <tr><td colSpan={8} className="py-2 px-4 bg-[#6366F1]/5 border-b border-[#6366F1]/10">
                      <span className="text-[10px] font-semibold text-[#6366F1] uppercase tracking-widest">Indices</span>
                    </td></tr>
                  )}
                  {filteredIndian.filter(s => s.type === 'index').map(s => (
                    <tr key={s.id} className={`market-row border-b border-white/[0.03] ${priceChanges[s.id] === 'up' ? 'price-flash-up' : priceChanges[s.id] === 'down' ? 'price-flash-down' : ''}`} data-testid={`market-indian-${s.id}`}>
                      <td className="py-3 px-4"><span className="text-sm text-white font-semibold">{s.name}</span></td>
                      <td className="py-3 px-4 text-xs text-[#6366F1] font-data font-medium">{s.symbol}</td>
                      <td className="py-3 px-4 text-right text-sm text-white font-data font-semibold price-value">{fmtPrice(s.price)}</td>
                      <td className={`py-3 px-4 text-right text-xs font-data font-medium ${s.change_24h >= 0 ? 'text-[#00FF94]' : 'text-[#FF2E2E]'}`}>{s.change_24h >= 0 ? '+' : ''}{s.change_24h?.toFixed(2)}%</td>
                      <td className="py-3 px-4 text-right text-xs text-white/50 font-data hidden sm:table-cell">{fmtPrice(s.high)}</td>
                      <td className="py-3 px-4 text-right text-xs text-white/50 font-data hidden sm:table-cell">{fmtPrice(s.low)}</td>
                      <td className="py-3 px-4 text-right text-xs text-white/40 font-data hidden md:table-cell">{fmtVol(s.volume)}</td>
                      <td className="py-3 px-4 text-right">
                        <Button variant="ghost" size="icon" className="w-7 h-7 text-white/30 hover:text-[#6366F1]" onClick={() => addToWatchlist(s.id, s.name, 'indian')} data-testid={`watchlist-add-${s.id}`}><Star className="w-3.5 h-3.5" /></Button>
                      </td>
                    </tr>
                  ))}
                  {/* Stocks */}
                  {filteredIndian.filter(s => s.type === 'stock').length > 0 && (
                    <tr><td colSpan={8} className="py-2 px-4 bg-[#00FF94]/5 border-b border-[#00FF94]/10">
                      <span className="text-[10px] font-semibold text-[#00FF94] uppercase tracking-widest">Stocks</span>
                    </td></tr>
                  )}
                  {filteredIndian.filter(s => s.type === 'stock').map(s => (
                    <tr key={s.id} className={`market-row border-b border-white/[0.03] ${priceChanges[s.id] === 'up' ? 'price-flash-up' : priceChanges[s.id] === 'down' ? 'price-flash-down' : ''}`} data-testid={`market-indian-${s.id}`}>
                      <td className="py-3 px-4"><span className="text-sm text-white font-medium">{s.name}</span></td>
                      <td className="py-3 px-4 text-xs text-white/50 font-data">{s.symbol}</td>
                      <td className="py-3 px-4 text-right text-sm text-white font-data price-value">{fmtPrice(s.price)}</td>
                      <td className={`py-3 px-4 text-right text-xs font-data ${s.change_24h >= 0 ? 'text-[#00FF94]' : 'text-[#FF2E2E]'}`}>{s.change_24h >= 0 ? '+' : ''}{s.change_24h?.toFixed(2)}%</td>
                      <td className="py-3 px-4 text-right text-xs text-white/50 font-data hidden sm:table-cell">{fmtPrice(s.high)}</td>
                      <td className="py-3 px-4 text-right text-xs text-white/50 font-data hidden sm:table-cell">{fmtPrice(s.low)}</td>
                      <td className="py-3 px-4 text-right text-xs text-white/40 font-data hidden md:table-cell">{fmtVol(s.volume)}</td>
                      <td className="py-3 px-4 text-right">
                        <Button variant="ghost" size="icon" className="w-7 h-7 text-white/30 hover:text-[#6366F1]" onClick={() => addToWatchlist(s.id, s.name, 'indian')} data-testid={`watchlist-add-${s.id}`}><Star className="w-3.5 h-3.5" /></Button>
                      </td>
                    </tr>
                  ))}
                  {filteredIndian.length === 0 && (
                    <tr><td colSpan={8} className="py-8 text-center text-sm text-white/30">Loading Indian market data...</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
