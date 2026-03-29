import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Loader2, TrendingUp, TrendingDown, Activity } from 'lucide-react';
import { toast } from 'sonner';

export default function OptionChainPage() {
  const { api } = useAuth();
  const [symbol, setSymbol] = useState('NIFTY');
  const [chain, setChain] = useState(null);
  const [fnoList, setFnoList] = useState({ stocks: [], indices: [] });
  const [loading, setLoading] = useState(true);
  const [expiryIdx, setExpiryIdx] = useState(0);

  useEffect(() => { api.get('/options/fno-list').then(r => setFnoList(r.data)).catch(() => {}); }, [api]);
  useEffect(() => { fetchChain(); }, [symbol, expiryIdx]);

  const fetchChain = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/options/chain/${symbol}?expiry=${expiryIdx}`);
      setChain(res.data);
    } catch (e) { toast.error(`Failed to load option chain for ${symbol}`); }
    setLoading(false);
  };

  const d = chain;
  const allData = d?.data || [];
  const atmIdx = allData.findIndex(s => Math.abs(s.strikePrice - (d?.underlyingValue || 0)) < (d?.underlyingValue > 10000 ? 100 : 50));

  return (
    <div className="space-y-4 page-enter" data-testid="option-chain-page">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-bold text-white">Live Option Chain</h1>
          <p className="text-sm text-white/40">Indian Market F&O — Black-Scholes Estimated</p>
        </div>
        <div className="flex gap-2">
          <Select value={symbol} onValueChange={s => { setSymbol(s); setExpiryIdx(0); }}>
            <SelectTrigger className="w-[180px] bg-white/[0.03] border-white/10 text-white" data-testid="oc-symbol-select">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="max-h-[300px]">
              <SelectItem value="__indices" disabled className="text-[#6366F1] text-xs font-bold">— INDICES —</SelectItem>
              {fnoList.indices?.map(i => <SelectItem key={i} value={i}>{i}</SelectItem>)}
              <SelectItem value="__stocks" disabled className="text-[#6366F1] text-xs font-bold">— F&O STOCKS —</SelectItem>
              {fnoList.stocks?.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
            </SelectContent>
          </Select>
          {d?.expiryDates && (
            <Select value={String(expiryIdx)} onValueChange={v => setExpiryIdx(parseInt(v))}>
              <SelectTrigger className="w-[150px] bg-white/[0.03] border-white/10 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {d.expiryDates.map((exp, i) => <SelectItem key={i} value={String(i)}>{exp}</SelectItem>)}
              </SelectContent>
            </Select>
          )}
        </div>
      </div>

      {/* Summary Stats */}
      {d && (
        <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-2 stagger-item">
          {[
            { l: 'Spot Price', v: d.underlyingValue?.toLocaleString(), c: 'text-white' },
            { l: 'PCR', v: `${d.pcr} (${d.pcrLabel})`, c: d.pcr > 1.2 ? 'text-emerald-400' : d.pcr < 0.8 ? 'text-red-400' : 'text-yellow-400' },
            { l: 'Max Pain', v: d.maxPainStrike?.toLocaleString() },
            { l: 'IV', v: `${d.iv}%` },
            { l: 'Lot Size', v: d.lotSize },
            { l: 'Expiry', v: d.expiryDate },
          ].map(s => (
            <div key={s.l} className="p-2 rounded-lg bg-white/[0.02] border border-white/5 text-center">
              <p className="text-[9px] text-white/30 uppercase">{s.l}</p>
              <p className={`text-sm font-data font-semibold ${s.c || 'text-white'}`}>{s.v}</p>
            </div>
          ))}
        </div>
      )}

      {/* Option Chain Table */}
      {loading ? (
        <div className="flex items-center justify-center py-20"><Loader2 className="w-8 h-8 text-[#6366F1] animate-spin" /></div>
      ) : d && allData.length > 0 ? (
        <Card className="bg-[#0A0A0F] border-white/5 overflow-hidden">
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-[10px]">
                <thead>
                  <tr className="border-b border-white/10">
                    <th colSpan={6} className="bg-emerald-500/5 text-center py-2 text-emerald-400 font-semibold text-xs">CALLS (CE)</th>
                    <th className="bg-[#6366F1]/10 text-center py-2 text-[#6366F1] font-bold text-xs">STRIKE</th>
                    <th colSpan={6} className="bg-red-500/5 text-center py-2 text-red-400 font-semibold text-xs">PUTS (PE)</th>
                  </tr>
                  <tr className="border-b border-white/10 text-white/40">
                    <th className="py-1.5 px-1 text-right">OI</th>
                    <th className="py-1.5 px-1 text-right">Chg OI</th>
                    <th className="py-1.5 px-1 text-right">Vol</th>
                    <th className="py-1.5 px-1 text-right">IV</th>
                    <th className="py-1.5 px-1 text-right">LTP</th>
                    <th className="py-1.5 px-1 text-right">Delta</th>
                    <th className="py-1.5 px-1 text-center font-bold text-white/60">STRIKE</th>
                    <th className="py-1.5 px-1 text-right">Delta</th>
                    <th className="py-1.5 px-1 text-right">LTP</th>
                    <th className="py-1.5 px-1 text-right">IV</th>
                    <th className="py-1.5 px-1 text-right">Vol</th>
                    <th className="py-1.5 px-1 text-right">Chg OI</th>
                    <th className="py-1.5 px-1 text-right">OI</th>
                  </tr>
                </thead>
                <tbody>
                  {allData.map((row, i) => {
                    const isATM = i === atmIdx;
                    const ceITM = row.CE.inTheMoney;
                    const peITM = row.PE.inTheMoney;
                    return (
                      <tr key={row.strikePrice} className={`border-b border-white/5 hover:bg-white/[0.02] transition-colors ${isATM ? 'bg-[#6366F1]/10 border-[#6366F1]/20' : ''}`}>
                        <td className={`py-1 px-1 text-right font-data ${ceITM ? 'bg-emerald-500/5' : ''}`}>{(row.CE.openInterest / 1000).toFixed(0)}K</td>
                        <td className={`py-1 px-1 text-right font-data ${row.CE.changeinOpenInterest > 0 ? 'text-emerald-400' : 'text-red-400'} ${ceITM ? 'bg-emerald-500/5' : ''}`}>{(row.CE.changeinOpenInterest / 1000).toFixed(0)}K</td>
                        <td className={`py-1 px-1 text-right font-data text-white/50 ${ceITM ? 'bg-emerald-500/5' : ''}`}>{row.CE.volume}</td>
                        <td className={`py-1 px-1 text-right font-data text-white/50 ${ceITM ? 'bg-emerald-500/5' : ''}`}>{row.CE.impliedVolatility}%</td>
                        <td className={`py-1 px-1 text-right font-data font-medium text-white ${ceITM ? 'bg-emerald-500/5' : ''}`}>{row.CE.lastPrice}</td>
                        <td className={`py-1 px-1 text-right font-data text-emerald-400/70 ${ceITM ? 'bg-emerald-500/5' : ''}`}>{row.CE.delta}</td>
                        <td className={`py-1 px-1 text-center font-data font-bold ${isATM ? 'text-[#6366F1] text-sm' : 'text-white/80'}`}>{row.strikePrice}</td>
                        <td className={`py-1 px-1 text-right font-data text-red-400/70 ${peITM ? 'bg-red-500/5' : ''}`}>{row.PE.delta}</td>
                        <td className={`py-1 px-1 text-right font-data font-medium text-white ${peITM ? 'bg-red-500/5' : ''}`}>{row.PE.lastPrice}</td>
                        <td className={`py-1 px-1 text-right font-data text-white/50 ${peITM ? 'bg-red-500/5' : ''}`}>{row.PE.impliedVolatility}%</td>
                        <td className={`py-1 px-1 text-right font-data text-white/50 ${peITM ? 'bg-red-500/5' : ''}`}>{row.PE.volume}</td>
                        <td className={`py-1 px-1 text-right font-data ${row.PE.changeinOpenInterest > 0 ? 'text-emerald-400' : 'text-red-400'} ${peITM ? 'bg-red-500/5' : ''}`}>{(row.PE.changeinOpenInterest / 1000).toFixed(0)}K</td>
                        <td className={`py-1 px-1 text-right font-data ${peITM ? 'bg-red-500/5' : ''}`}>{(row.PE.openInterest / 1000).toFixed(0)}K</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="text-center py-20 text-white/40">No data available for {symbol}</div>
      )}

      <p className="text-[9px] text-white/20 text-center">Option prices estimated via Black-Scholes model. Actual NSE prices may differ. Not financial advice.</p>
    </div>
  );
}
