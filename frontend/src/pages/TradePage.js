import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useMarketStream } from '../hooks/useMarketStream';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { ArrowUpRight, ArrowDownRight, DollarSign, TrendingUp, TrendingDown, Loader2, Shield, AlertTriangle, X, RefreshCw, Lock } from 'lucide-react';
import { toast } from 'sonner';

const INSTRUMENTS = [
  { value: 'EUR_USD', label: 'EUR/USD' },
  { value: 'GBP_USD', label: 'GBP/USD' },
  { value: 'USD_JPY', label: 'USD/JPY' },
  { value: 'AUD_USD', label: 'AUD/USD' },
  { value: 'USD_CHF', label: 'USD/CHF' },
  { value: 'USD_CAD', label: 'USD/CAD' },
  { value: 'NZD_USD', label: 'NZD/USD' },
  { value: 'XAU_USD', label: 'Gold (XAU/USD)' },
  { value: 'XAG_USD', label: 'Silver (XAG/USD)' },
  { value: 'EUR_GBP', label: 'EUR/GBP' },
  { value: 'EUR_JPY', label: 'EUR/JPY' },
  { value: 'GBP_JPY', label: 'GBP/JPY' },
];

export default function TradePage() {
  const { api } = useAuth();
  const { data: marketData } = useMarketStream();
  const [instrument, setInstrument] = useState('EUR_USD');
  const [units, setUnits] = useState('1000');
  const [usdAmount, setUsdAmount] = useState('');
  const [sizeMode, setSizeMode] = useState('units'); // units or usd
  const [leverage, setLeverage] = useState('1');
  const [orderType, setOrderType] = useState('MARKET');
  const [stopLoss, setStopLoss] = useState('');
  const [takeProfit, setTakeProfit] = useState('');
  const [limitPrice, setLimitPrice] = useState('');
  const [placing, setPlacing] = useState(false);
  const [positions, setPositions] = useState([]);
  const [account, setAccount] = useState(null);
  const [tradeHistory, setTradeHistory] = useState([]);
  const [planUsage, setPlanUsage] = useState(null);
  const [closing, setClosing] = useState(null);

  const loadData = useCallback(async () => {
    try {
      const [pos, acct, hist, usage] = await Promise.all([
        api.get('/trade/positions'),
        api.get('/trade/account'),
        api.get('/trade/history'),
        api.get('/user/plan-usage'),
      ]);
      setPositions(pos.data.positions || []);
      setAccount(acct.data);
      setTradeHistory(hist.data.trades || []);
      setPlanUsage(usage.data);
    } catch (e) {
      console.error(e);
    }
  }, [api]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, [loadData]);

  const currentPrice = marketData?.forex?.find(f => {
    const id = instrument.toLowerCase().replace('_', '');
    return f.id === id;
  });

  const canTrade = planUsage?.limits?.trade_execution;

  const placeOrder = async (direction) => {
    if (!canTrade) {
      toast.error('Trade execution requires Titan plan');
      return;
    }
    setPlacing(true);
    try {
      const lev = parseInt(leverage) || 1;
      const u = sizeMode === 'units' ? parseInt(units) * lev * (direction === 'SELL' ? -1 : 1) : undefined;
      const usd = sizeMode === 'usd' ? parseFloat(usdAmount) * lev * (direction === 'SELL' ? -1 : 1) : undefined;
      const body = {
        instrument,
        units: u || undefined,
        usd_amount: usd || undefined,
        order_type: orderType,
        stop_loss: stopLoss ? parseFloat(stopLoss) : null,
        take_profit: takeProfit ? parseFloat(takeProfit) : null,
        price: limitPrice && orderType !== 'MARKET' ? parseFloat(limitPrice) : null,
      };
      await api.post('/trade/order', body);
      toast.success(`${direction} order placed for ${instrument}`);
      loadData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Order failed');
    } finally {
      setPlacing(false);
    }
  };

  const closePosition = async (inst) => {
    setClosing(inst);
    try {
      await api.post(`/trade/close/${inst}`);
      toast.success(`Position closed for ${inst}`);
      loadData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to close');
    } finally {
      setClosing(null);
    }
  };

  return (
    <div className="space-y-6" data-testid="trade-page">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">Trade Execution</h1>
        <p className="text-sm text-white/50 mt-1">Execute trades directly via OANDA</p>
      </div>

      {!canTrade && (
        <Card className="bg-yellow-500/5 border-yellow-500/20">
          <CardContent className="p-4 flex items-center gap-3">
            <Lock className="w-5 h-5 text-yellow-500 shrink-0" />
            <div>
              <p className="text-sm font-medium text-yellow-500">Titan Plan Required</p>
              <p className="text-xs text-white/40">Upgrade to Titan plan to execute live trades. Current plan: {planUsage?.plan_name || 'free'}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Account Summary */}
      {account && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: 'Balance', value: `$${account.balance?.toLocaleString(undefined, { minimumFractionDigits: 2 })}`, icon: DollarSign },
            { label: 'Unrealized P&L', value: `${account.unrealized_pnl >= 0 ? '+' : ''}$${account.unrealized_pnl?.toFixed(2)}`, icon: TrendingUp, color: account.unrealized_pnl >= 0 },
            { label: 'NAV', value: `$${account.nav?.toLocaleString(undefined, { minimumFractionDigits: 2 })}`, icon: Shield },
            { label: 'Open Trades', value: account.open_trade_count, icon: ArrowUpRight },
          ].map(s => (
            <Card key={s.label} className="bg-[#0A0A0F] border-white/5">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 mb-1">
                  <s.icon className="w-3.5 h-3.5 text-[#6366F1]" />
                  <span className="text-[10px] text-white/40 uppercase tracking-wider">{s.label}</span>
                </div>
                <p className={`text-lg font-bold font-data ${s.color !== undefined ? (s.color ? 'text-emerald-400' : 'text-red-400') : 'text-white'}`}>{s.value}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Order Form */}
        <Card className="bg-[#0A0A0F] border-white/5 lg:col-span-1">
          <CardHeader className="pb-3">
            <CardTitle className="text-base text-white">Place Order</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-[11px] text-white/40 uppercase mb-1.5 block">Instrument</label>
              <Select value={instrument} onValueChange={setInstrument}>
                <SelectTrigger className="bg-white/[0.03] border-white/10 text-white" data-testid="instrument-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {INSTRUMENTS.map(i => (
                    <SelectItem key={i.value} value={i.value}>{i.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {currentPrice && (
              <div className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/5">
                <span className="text-xs text-white/40">Current Price</span>
                <span className="text-base font-bold font-data text-white">{currentPrice.price}</span>
              </div>
            )}

            <div>
              <label className="text-[11px] text-white/40 uppercase mb-1.5 block">Order Type</label>
              <Select value={orderType} onValueChange={setOrderType}>
                <SelectTrigger className="bg-white/[0.03] border-white/10 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="MARKET">Market</SelectItem>
                  <SelectItem value="LIMIT">Limit</SelectItem>
                  <SelectItem value="STOP">Stop</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {orderType !== 'MARKET' && (
              <div>
                <label className="text-[11px] text-white/40 uppercase mb-1.5 block">Price</label>
                <Input type="number" step="0.00001" value={limitPrice} onChange={e => setLimitPrice(e.target.value)} placeholder="Enter price" className="bg-white/[0.03] border-white/10 text-white" />
              </div>
            )}

            <div>
              <label className="text-[11px] text-white/40 uppercase mb-1.5 block">Size Mode</label>
              <div className="flex gap-1">
                <button onClick={() => setSizeMode('units')} className={`flex-1 px-3 py-1.5 rounded text-xs font-medium border ${sizeMode === 'units' ? 'bg-[#6366F1]/20 border-[#6366F1]/50 text-[#6366F1]' : 'bg-white/5 border-white/10 text-white/40'}`}>Units</button>
                <button onClick={() => setSizeMode('usd')} className={`flex-1 px-3 py-1.5 rounded text-xs font-medium border ${sizeMode === 'usd' ? 'bg-[#6366F1]/20 border-[#6366F1]/50 text-[#6366F1]' : 'bg-white/5 border-white/10 text-white/40'}`}>USD</button>
              </div>
            </div>

            <div>
              <label className="text-[11px] text-white/40 uppercase mb-1.5 block">Leverage</label>
              <div className="flex gap-1" data-testid="leverage-selector">
                {['1', '10', '50', '100'].map(lev => (
                  <button key={lev} onClick={() => setLeverage(lev)}
                    className={`flex-1 px-2 py-1.5 rounded text-xs font-medium border transition-all ${
                      leverage === lev
                        ? 'bg-[#6366F1]/20 border-[#6366F1]/50 text-[#6366F1] shadow-[0_0_6px_rgba(99,102,241,0.15)]'
                        : 'bg-white/5 border-white/10 text-white/40 hover:text-white/60'
                    }`}
                    data-testid={`leverage-${lev}`}
                  >
                    1:{lev}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="text-[11px] text-white/40 uppercase mb-1.5 block">{sizeMode === 'units' ? 'Units' : 'USD Amount'}</label>
              {sizeMode === 'units' ? (
                <Input type="number" value={units} onChange={e => setUnits(e.target.value)} placeholder="1000" className="bg-white/[0.03] border-white/10 text-white" data-testid="units-input" />
              ) : (
                <Input type="number" value={usdAmount} onChange={e => setUsdAmount(e.target.value)} placeholder="100.00" className="bg-white/[0.03] border-white/10 text-white" data-testid="usd-input" />
              )}
              {parseInt(leverage) > 1 && (
                <p className="text-[10px] text-[#6366F1] mt-1 font-data" data-testid="effective-size">
                  Effective size: {sizeMode === 'units'
                    ? `${(parseInt(units || 0) * parseInt(leverage)).toLocaleString()} units`
                    : `$${(parseFloat(usdAmount || 0) * parseInt(leverage)).toLocaleString()}`
                  } (1:{leverage} leverage)
                </p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] text-white/40 uppercase mb-1.5 block">Stop Loss</label>
                <Input type="number" step="0.00001" value={stopLoss} onChange={e => setStopLoss(e.target.value)} placeholder="Optional" className="bg-white/[0.03] border-white/10 text-white text-sm" />
              </div>
              <div>
                <label className="text-[11px] text-white/40 uppercase mb-1.5 block">Take Profit</label>
                <Input type="number" step="0.00001" value={takeProfit} onChange={e => setTakeProfit(e.target.value)} placeholder="Optional" className="bg-white/[0.03] border-white/10 text-white text-sm" />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 pt-2">
              <Button
                onClick={() => placeOrder('BUY')}
                disabled={placing || !canTrade}
                className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold"
                data-testid="buy-btn"
              >
                {placing ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowUpRight className="w-4 h-4 mr-1" />}
                BUY
              </Button>
              <Button
                onClick={() => placeOrder('SELL')}
                disabled={placing || !canTrade}
                className="bg-red-600 hover:bg-red-700 text-white font-semibold"
                data-testid="sell-btn"
              >
                {placing ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowDownRight className="w-4 h-4 mr-1" />}
                SELL
              </Button>
            </div>

            <p className="text-[10px] text-white/25 text-center">Practice account. Not financial advice.</p>
          </CardContent>
        </Card>

        {/* Open Positions */}
        <Card className="bg-[#0A0A0F] border-white/5 lg:col-span-2">
          <CardHeader className="pb-3 flex flex-row items-center justify-between">
            <CardTitle className="text-base text-white">Open Positions</CardTitle>
            <Button variant="ghost" size="sm" onClick={loadData} className="text-white/40 hover:text-white">
              <RefreshCw className="w-3.5 h-3.5" />
            </Button>
          </CardHeader>
          <CardContent>
            {positions.length === 0 ? (
              <div className="text-center py-8">
                <TrendingUp className="w-10 h-10 text-white/10 mx-auto mb-2" />
                <p className="text-sm text-white/40">No open positions</p>
              </div>
            ) : (
              <div className="space-y-2">
                {positions.map((p, i) => (
                  <div key={`${p.instrument}-${p.direction}-${i}`} className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/5" data-testid={`position-${i}`}>
                    <div className="flex items-center gap-3">
                      <Badge variant="outline" className={p.direction === 'LONG' ? 'border-emerald-500/30 text-emerald-400 bg-emerald-500/10' : 'border-red-500/30 text-red-400 bg-red-500/10'}>
                        {p.direction}
                      </Badge>
                      <div>
                        <p className="text-sm font-medium text-white">{p.name || p.instrument}</p>
                        <p className="text-[11px] text-white/40">{p.units} units @ {p.avg_price}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`text-sm font-bold font-data ${p.unrealized_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {p.unrealized_pnl >= 0 ? '+' : ''}${p.unrealized_pnl}
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => closePosition(p.instrument)}
                        disabled={closing === p.instrument}
                        className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                      >
                        {closing === p.instrument ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <X className="w-3.5 h-3.5" />}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Trade History */}
      {tradeHistory.length > 0 && (
        <Card className="bg-[#0A0A0F] border-white/5">
          <CardHeader className="pb-3">
            <CardTitle className="text-base text-white">Recent Executions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {tradeHistory.slice(0, 10).map((t, i) => (
                <div key={t.trade_id || i} className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/5">
                  <div className="flex items-center gap-3">
                    <Badge variant="outline" className={t.units > 0 ? 'border-emerald-500/30 text-emerald-400' : 'border-red-500/30 text-red-400'}>
                      {t.units > 0 ? 'BUY' : 'SELL'}
                    </Badge>
                    <div>
                      <p className="text-sm text-white">{t.instrument}</p>
                      <p className="text-[10px] text-white/30">{t.created_at?.slice(0, 16)}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-data text-white">{Math.abs(t.units)} units</p>
                    <Badge variant="outline" className="text-[9px] border-white/10 text-white/40">{t.status}</Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
