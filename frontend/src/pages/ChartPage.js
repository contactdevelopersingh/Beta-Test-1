import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useMarketStream } from '../hooks/useMarketStream';
import { TradingChart } from '../components/TradingChart';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { ArrowLeft, Star, Bell, TrendingUp, TrendingDown, BarChart3 } from 'lucide-react';
import { toast } from 'sonner';

const PERIODS = [
  { label: '1D', value: '1d' },
  { label: '7D', value: '7d' },
  { label: '1M', value: '1mo' },
  { label: '3M', value: '3mo' },
  { label: '1Y', value: '1y' },
];

export default function ChartPage() {
  const { assetType, assetId } = useParams();
  const { api } = useAuth();
  const navigate = useNavigate();
  const { crypto, forex, indian, priceChanges } = useMarketStream(true, 1500);
  const [candles, setCandles] = useState([]);
  const [period, setPeriod] = useState('1mo');
  const [loading, setLoading] = useState(true);

  const allPrices = [...crypto, ...forex, ...indian];
  const asset = allPrices.find(p => p.id === assetId);

  useEffect(() => {
    const fetchChart = async () => {
      setLoading(true);
      try {
        const res = await api.get(`/market/chart/${assetType}/${assetId}?period=${period}`);
        setCandles(res.data.candles || []);
      } catch (e) { console.error(e); }
      setLoading(false);
    };
    fetchChart();
  }, [assetType, assetId, period, api]);

  const addToWatchlist = async () => {
    try {
      await api.post('/watchlist', { asset_id: assetId, asset_name: asset?.name || assetId, asset_type: assetType });
      toast.success('Added to watchlist');
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed'); }
  };

  const fmtPrice = (p) => {
    if (!p) return '-';
    return p >= 1 ? `$${p.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}` : `$${p.toFixed(6)}`;
  };

  return (
    <div className="space-y-6" data-testid="chart-page">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" className="w-8 h-8 text-white/50 hover:text-white" onClick={() => navigate(-1)} data-testid="chart-back-btn">
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            {asset?.image && <img src={asset.image} alt="" className="w-8 h-8 rounded-full" />}
            <div>
              <h1 className="text-xl font-bold text-white" style={{ fontFamily: 'Manrope' }}>{asset?.name || assetId}</h1>
              <div className="flex items-center gap-2 mt-0.5">
                <Badge variant="outline" className="text-[9px] border-white/10 text-white/30 py-0 h-4">{assetType}</Badge>
                <span className="text-[10px] text-white/40 font-data">{asset?.symbol}</span>
              </div>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" className="border-white/10 text-white/50 hover:text-white text-xs" onClick={addToWatchlist} data-testid="chart-watchlist-btn">
            <Star className="w-3.5 h-3.5 mr-1" /> Watchlist
          </Button>
          <Button variant="outline" size="sm" className="border-white/10 text-white/50 hover:text-white text-xs" onClick={() => navigate(`/alerts`)} data-testid="chart-alert-btn">
            <Bell className="w-3.5 h-3.5 mr-1" /> Alert
          </Button>
        </div>
      </div>

      {/* Price Card */}
      {asset && (
        <div className="flex items-end gap-4">
          <span className={`text-3xl font-bold font-data ${priceChanges[assetId] === 'up' ? 'text-[#00FF94]' : priceChanges[assetId] === 'down' ? 'text-[#FF2E2E]' : 'text-white'}`} data-testid="chart-live-price">
            {fmtPrice(asset.price)}
          </span>
          <span className={`text-sm font-data font-medium ${asset.change_24h >= 0 ? 'text-[#00FF94]' : 'text-[#FF2E2E]'}`}>
            {asset.change_24h >= 0 ? <TrendingUp className="w-3.5 h-3.5 inline mr-0.5" /> : <TrendingDown className="w-3.5 h-3.5 inline mr-0.5" />}
            {asset.change_24h >= 0 ? '+' : ''}{asset.change_24h?.toFixed(2)}%
          </span>
        </div>
      )}

      {/* Chart */}
      <Card className="glass-panel border-white/10" data-testid="chart-card">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm text-white/80 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-[#6366F1]" /> Price Chart
            </CardTitle>
            <div className="flex gap-1">
              {PERIODS.map(p => (
                <button key={p.value} onClick={() => setPeriod(p.value)}
                  className={`px-2.5 py-1 rounded text-[10px] font-medium ${period === p.value ? 'bg-[#6366F1] text-white' : 'bg-white/5 text-white/40 hover:text-white/60'}`}
                  data-testid={`period-${p.value}`}>
                  {p.label}
                </button>
              ))}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="h-[350px] skeleton-shimmer rounded-lg" />
          ) : candles.length === 0 ? (
            <div className="h-[350px] flex items-center justify-center text-sm text-white/30">No chart data available</div>
          ) : (
            <TradingChart data={candles} symbol={asset?.symbol || assetId} height={350} showVolume={true} />
          )}
        </CardContent>
      </Card>

      {/* Stats */}
      {asset && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {asset.high && (
            <Card className="glass-panel border-white/10">
              <CardContent className="p-4">
                <p className="text-[10px] text-white/40 uppercase">24h High</p>
                <p className="text-sm font-data text-[#00FF94] font-medium">{fmtPrice(asset.high)}</p>
              </CardContent>
            </Card>
          )}
          {asset.low && (
            <Card className="glass-panel border-white/10">
              <CardContent className="p-4">
                <p className="text-[10px] text-white/40 uppercase">24h Low</p>
                <p className="text-sm font-data text-[#FF2E2E] font-medium">{fmtPrice(asset.low)}</p>
              </CardContent>
            </Card>
          )}
          {asset.volume > 0 && (
            <Card className="glass-panel border-white/10">
              <CardContent className="p-4">
                <p className="text-[10px] text-white/40 uppercase">Volume</p>
                <p className="text-sm font-data text-white font-medium">{asset.volume >= 1e9 ? `$${(asset.volume/1e9).toFixed(1)}B` : asset.volume >= 1e6 ? `$${(asset.volume/1e6).toFixed(1)}M` : asset.volume.toLocaleString()}</p>
              </CardContent>
            </Card>
          )}
          {asset.market_cap > 0 && (
            <Card className="glass-panel border-white/10">
              <CardContent className="p-4">
                <p className="text-[10px] text-white/40 uppercase">Market Cap</p>
                <p className="text-sm font-data text-white font-medium">{asset.market_cap >= 1e12 ? `$${(asset.market_cap/1e12).toFixed(2)}T` : `$${(asset.market_cap/1e9).toFixed(1)}B`}</p>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
