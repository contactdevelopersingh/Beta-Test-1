import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { TrendingUp, TrendingDown, Search, ArrowLeft, CheckCircle2, XCircle, BarChart3, PieChart, Users, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

const MetricRow = ({ label, value, suffix = '', good, tooltip }) => (
  <div className="flex items-center justify-between py-1.5 border-b border-white/5 last:border-0">
    <span className="text-xs text-white/50" title={tooltip}>{label}</span>
    <span className={`text-sm font-data font-medium ${good === true ? 'text-emerald-400' : good === false ? 'text-red-400' : 'text-white'}`}>
      {value !== null && value !== undefined ? `${value}${suffix}` : '—'}
    </span>
  </div>
);

export default function StockAnalysisPage() {
  const { symbol } = useParams();
  const navigate = useNavigate();
  const { api } = useAuth();
  const [data, setData] = useState(null);
  const [peers, setPeers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [stockList, setStockList] = useState([]);
  const [showSearch, setShowSearch] = useState(!symbol);
  const [tab, setTab] = useState('overview');

  useEffect(() => {
    api.get('/stocks/list').then(r => setStockList(r.data.stocks || [])).catch(() => {});
  }, [api]);

  useEffect(() => {
    if (symbol) { fetchAnalysis(symbol); setShowSearch(false); }
    else { setLoading(false); setShowSearch(true); }
  }, [symbol]);

  const fetchAnalysis = async (sym) => {
    setLoading(true);
    try {
      const [res, peersRes] = await Promise.all([
        api.get(`/stocks/analysis/${sym}`),
        api.get(`/stocks/peers/${sym}`).catch(() => ({ data: { peers: [] } })),
      ]);
      setData(res.data);
      setPeers(peersRes.data?.peers || []);
    } catch (e) {
      toast.error(`Failed to load ${sym}`);
    }
    setLoading(false);
  };

  const filtered = stockList.filter(s =>
    s.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.name.toLowerCase().includes(searchQuery.toLowerCase())
  ).slice(0, 15);

  const f = data?.fundamentals || {};
  const tabs = ['overview', 'financials', 'quarterly', 'balance_sheet', 'cash_flow', 'shareholding', 'peers'];

  if (showSearch || !symbol) {
    return (
      <div className="space-y-6 page-enter" data-testid="stock-search-page">
        <h1 className="text-2xl font-bold text-white">Stock Analysis</h1>
        <p className="text-sm text-white/40">Search any Indian stock for deep fundamental analysis</p>
        <div className="relative max-w-xl">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
          <Input
            placeholder="Search by symbol or company name (e.g. RELIANCE, TCS)..."
            value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
            className="pl-10 bg-white/[0.03] border-white/10 text-white" autoFocus
            data-testid="stock-search-input"
          />
        </div>
        {searchQuery && (
          <div className="space-y-1 max-w-xl">
            {filtered.map(s => (
              <button key={s.symbol} onClick={() => navigate(`/stock-analysis/${s.symbol.toLowerCase()}`)}
                className="w-full flex items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/5 hover:bg-white/[0.05] transition-all text-left"
                data-testid={`stock-${s.symbol}`}
              >
                <div>
                  <span className="text-sm font-medium text-white">{s.symbol}</span>
                  <span className="text-xs text-white/40 ml-2">{s.name}</span>
                </div>
                <Badge variant="outline" className="text-[9px] border-white/10 text-white/30">{s.sector}</Badge>
              </button>
            ))}
          </div>
        )}
      </div>
    );
  }

  if (loading) return <div className="flex items-center justify-center min-h-[60vh]"><Loader2 className="w-8 h-8 text-[#6366F1] animate-spin" /></div>;
  if (!data) return <div className="text-center py-20 text-white/40">No data found</div>;

  return (
    <div className="space-y-4 page-enter" data-testid="stock-analysis-page">
      {/* Header */}
      <div className="flex items-center gap-3 mb-2">
        <Button variant="ghost" size="sm" onClick={() => { setShowSearch(true); navigate('/stock-analysis'); }} className="text-white/40"><ArrowLeft className="w-4 h-4" /></Button>
        <div>
          <h1 className="text-xl font-bold text-white">{data.name} <span className="text-[#6366F1]">({data.symbol})</span></h1>
          <p className="text-xs text-white/40">{data.sector} · {data.industry} · {data.exchange}</p>
        </div>
        <div className="ml-auto text-right">
          <p className="text-2xl font-bold font-data text-white">₹{data.price?.toLocaleString()}</p>
          <p className={`text-sm font-data ${data.change >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            {data.change >= 0 ? '+' : ''}{data.change} ({data.change_pct}%)
          </p>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
        {[
          { l: 'Market Cap', v: `₹${data.market_cap_cr?.toLocaleString()} Cr` },
          { l: 'P/E', v: f.pe_ratio },
          { l: 'ROE', v: f.roe ? `${f.roe}%` : '—' },
          { l: 'D/E', v: f.debt_to_equity },
          { l: '52W High', v: `₹${data.week_52_high}` },
          { l: '52W Low', v: `₹${data.week_52_low}` },
        ].map(s => (
          <div key={s.l} className="p-2 rounded-lg bg-white/[0.02] border border-white/5 text-center">
            <p className="text-[9px] text-white/30 uppercase">{s.l}</p>
            <p className="text-sm font-data font-semibold text-white">{s.v || '—'}</p>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 overflow-x-auto pb-1">
        {tabs.map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-3 py-1.5 rounded-md text-[11px] font-medium border whitespace-nowrap transition-all ${tab === t ? 'bg-[#6366F1]/20 border-[#6366F1]/50 text-[#6366F1]' : 'bg-white/5 border-white/10 text-white/40'}`}
          >{t.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}</button>
        ))}
      </div>

      {/* Overview Tab */}
      {tab === 'overview' && (
        <div className="grid md:grid-cols-2 gap-4">
          <Card className="bg-[#0A0A0F] border-white/5">
            <CardHeader className="pb-2"><CardTitle className="text-sm text-white">Valuation</CardTitle></CardHeader>
            <CardContent>
              <MetricRow label="P/E Ratio" value={f.pe_ratio} tooltip="Price to Earnings" />
              <MetricRow label="P/B Ratio" value={f.pb_ratio} tooltip="Price to Book" />
              <MetricRow label="EV/EBITDA" value={f.ev_ebitda} />
              <MetricRow label="Price/Sales" value={f.price_to_sales} />
              <MetricRow label="PEG Ratio" value={f.peg_ratio} />
              <MetricRow label="EPS" value={f.eps} suffix=" ₹" />
              <MetricRow label="Book Value" value={f.book_value} suffix=" ₹" />
            </CardContent>
          </Card>
          <Card className="bg-[#0A0A0F] border-white/5">
            <CardHeader className="pb-2"><CardTitle className="text-sm text-white">Profitability</CardTitle></CardHeader>
            <CardContent>
              <MetricRow label="ROE" value={f.roe} suffix="%" good={f.roe > 15} />
              <MetricRow label="ROA" value={f.roa} suffix="%" good={f.roa > 8} />
              <MetricRow label="OPM" value={f.opm} suffix="%" good={f.opm > 15} />
              <MetricRow label="NPM" value={f.npm} suffix="%" good={f.npm > 10} />
              <MetricRow label="Dividend Yield" value={f.dividend_yield} suffix="%" good={f.dividend_yield > 2} />
              <MetricRow label="Revenue Growth" value={f.revenue_growth} suffix="%" good={f.revenue_growth > 10} />
              <MetricRow label="Earnings Growth" value={f.earnings_growth} suffix="%" good={f.earnings_growth > 10} />
            </CardContent>
          </Card>
          <Card className="bg-[#0A0A0F] border-white/5">
            <CardHeader className="pb-2"><CardTitle className="text-sm text-white">Financial Health</CardTitle></CardHeader>
            <CardContent>
              <MetricRow label="Debt/Equity" value={f.debt_to_equity} good={f.debt_to_equity !== null ? f.debt_to_equity < 0.5 : undefined} />
              <MetricRow label="Current Ratio" value={f.current_ratio} good={f.current_ratio > 1.5} />
              <MetricRow label="Free Cash Flow" value={f.free_cash_flow} suffix=" Cr" good={f.free_cash_flow > 0} />
              <MetricRow label="Total Debt" value={f.total_debt_cr} suffix=" Cr" />
              <MetricRow label="Total Cash" value={f.total_cash_cr} suffix=" Cr" />
            </CardContent>
          </Card>
          <Card className="bg-[#0A0A0F] border-white/5">
            <CardHeader className="pb-2"><CardTitle className="text-sm text-white">Analyst</CardTitle></CardHeader>
            <CardContent>
              <MetricRow label="Recommendation" value={data.analyst?.recommendation?.toUpperCase()} />
              <MetricRow label="Target (Mean)" value={data.analyst?.target_mean} suffix=" ₹" />
              <MetricRow label="Target (High)" value={data.analyst?.target_high} suffix=" ₹" />
              <MetricRow label="Target (Low)" value={data.analyst?.target_low} suffix=" ₹" />
              <MetricRow label="Analysts" value={data.analyst?.num_analysts} />
            </CardContent>
          </Card>

          {/* Pros & Cons */}
          {(data.pros?.length > 0 || data.cons?.length > 0) && (
            <Card className="md:col-span-2 bg-[#0A0A0F] border-white/5">
              <CardHeader className="pb-2"><CardTitle className="text-sm text-white">Pros & Cons</CardTitle></CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    {data.pros?.map((p, i) => (
                      <div key={i} className="flex items-start gap-2 text-xs"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 mt-0.5 shrink-0" /><span className="text-emerald-400/80">{p}</span></div>
                    ))}
                  </div>
                  <div className="space-y-1.5">
                    {data.cons?.map((c, i) => (
                      <div key={i} className="flex items-start gap-2 text-xs"><XCircle className="w-3.5 h-3.5 text-red-400 mt-0.5 shrink-0" /><span className="text-red-400/80">{c}</span></div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Quarterly Results */}
      {tab === 'quarterly' && (
        <Card className="bg-[#0A0A0F] border-white/5">
          <CardHeader className="pb-2"><CardTitle className="text-sm text-white">Quarterly Results</CardTitle></CardHeader>
          <CardContent>
            {data.quarterly_results?.length > 0 ? (
              <div className="overflow-x-auto"><table className="w-full text-xs">
                <thead><tr className="border-b border-white/10">
                  <th className="text-left py-2 text-white/40 font-medium">Quarter</th>
                  {Object.keys(data.quarterly_results[0]).filter(k => k !== 'quarter').slice(0, 8).map(k => (
                    <th key={k} className="text-right py-2 text-white/40 font-medium px-2">{k.replace(/_/g, ' ').slice(0, 15)}</th>
                  ))}
                </tr></thead>
                <tbody>{data.quarterly_results.map((q, i) => (
                  <tr key={i} className="border-b border-white/5 hover:bg-white/[0.02]">
                    <td className="py-2 text-white font-medium">{q.quarter}</td>
                    {Object.entries(q).filter(([k]) => k !== 'quarter').slice(0, 8).map(([k, v]) => (
                      <td key={k} className="text-right py-2 px-2 font-data text-white/70">{typeof v === 'number' ? (Math.abs(v) > 1e6 ? `${(v/1e7).toFixed(1)}Cr` : v.toLocaleString()) : v}</td>
                    ))}
                  </tr>
                ))}</tbody>
              </table></div>
            ) : <p className="text-white/30 text-sm text-center py-8">No quarterly data available</p>}
          </CardContent>
        </Card>
      )}

      {/* Financials (Annual P&L) */}
      {tab === 'financials' && (
        <Card className="bg-[#0A0A0F] border-white/5">
          <CardHeader className="pb-2"><CardTitle className="text-sm text-white">Annual Profit & Loss</CardTitle></CardHeader>
          <CardContent>
            {data.annual_pl?.length > 0 ? (
              <div className="overflow-x-auto"><table className="w-full text-xs">
                <thead><tr className="border-b border-white/10">
                  <th className="text-left py-2 text-white/40">Year</th>
                  {Object.keys(data.annual_pl[0]).filter(k => k !== 'year').slice(0, 8).map(k => (
                    <th key={k} className="text-right py-2 text-white/40 px-2">{k.replace(/_/g, ' ').slice(0, 15)}</th>
                  ))}
                </tr></thead>
                <tbody>{data.annual_pl.map((a, i) => (
                  <tr key={i} className="border-b border-white/5 hover:bg-white/[0.02]">
                    <td className="py-2 text-white font-medium">{a.year}</td>
                    {Object.entries(a).filter(([k]) => k !== 'year').slice(0, 8).map(([k, v]) => (
                      <td key={k} className="text-right py-2 px-2 font-data text-white/70">{typeof v === 'number' ? (Math.abs(v) > 1e6 ? `${(v/1e7).toFixed(1)}Cr` : v.toLocaleString()) : v}</td>
                    ))}
                  </tr>
                ))}</tbody>
              </table></div>
            ) : <p className="text-white/30 text-sm text-center py-8">No annual data available</p>}
          </CardContent>
        </Card>
      )}

      {/* Balance Sheet */}
      {tab === 'balance_sheet' && (
        <Card className="bg-[#0A0A0F] border-white/5">
          <CardHeader className="pb-2"><CardTitle className="text-sm text-white">Balance Sheet</CardTitle></CardHeader>
          <CardContent>
            {data.balance_sheet?.length > 0 ? (
              <div className="overflow-x-auto"><table className="w-full text-xs">
                <thead><tr className="border-b border-white/10">
                  <th className="text-left py-2 text-white/40">Year</th>
                  {Object.keys(data.balance_sheet[0]).filter(k => k !== 'year').slice(0, 8).map(k => (
                    <th key={k} className="text-right py-2 text-white/40 px-2">{k.replace(/_/g, ' ').slice(0, 15)}</th>
                  ))}
                </tr></thead>
                <tbody>{data.balance_sheet.map((b, i) => (
                  <tr key={i} className="border-b border-white/5 hover:bg-white/[0.02]">
                    <td className="py-2 text-white font-medium">{b.year}</td>
                    {Object.entries(b).filter(([k]) => k !== 'year').slice(0, 8).map(([k, v]) => (
                      <td key={k} className="text-right py-2 px-2 font-data text-white/70">{typeof v === 'number' ? (Math.abs(v) > 1e6 ? `${(v/1e7).toFixed(1)}Cr` : v.toLocaleString()) : v}</td>
                    ))}
                  </tr>
                ))}</tbody>
              </table></div>
            ) : <p className="text-white/30 text-sm text-center py-8">No balance sheet data available</p>}
          </CardContent>
        </Card>
      )}

      {/* Cash Flow */}
      {tab === 'cash_flow' && (
        <Card className="bg-[#0A0A0F] border-white/5">
          <CardHeader className="pb-2"><CardTitle className="text-sm text-white">Cash Flow Statement</CardTitle></CardHeader>
          <CardContent>
            {data.cash_flow?.length > 0 ? (
              <div className="overflow-x-auto"><table className="w-full text-xs">
                <thead><tr className="border-b border-white/10">
                  <th className="text-left py-2 text-white/40">Year</th>
                  {Object.keys(data.cash_flow[0]).filter(k => k !== 'year').slice(0, 8).map(k => (
                    <th key={k} className="text-right py-2 text-white/40 px-2">{k.replace(/_/g, ' ').slice(0, 15)}</th>
                  ))}
                </tr></thead>
                <tbody>{data.cash_flow.map((c, i) => (
                  <tr key={i} className="border-b border-white/5 hover:bg-white/[0.02]">
                    <td className="py-2 text-white font-medium">{c.year}</td>
                    {Object.entries(c).filter(([k]) => k !== 'year').slice(0, 8).map(([k, v]) => (
                      <td key={k} className={`text-right py-2 px-2 font-data ${v < 0 ? 'text-red-400/70' : 'text-white/70'}`}>{typeof v === 'number' ? (Math.abs(v) > 1e6 ? `${(v/1e7).toFixed(1)}Cr` : v.toLocaleString()) : v}</td>
                    ))}
                  </tr>
                ))}</tbody>
              </table></div>
            ) : <p className="text-white/30 text-sm text-center py-8">No cash flow data available</p>}
          </CardContent>
        </Card>
      )}

      {/* Shareholding */}
      {tab === 'shareholding' && data.shareholding && (
        <Card className="bg-[#0A0A0F] border-white/5">
          <CardHeader className="pb-2"><CardTitle className="text-sm text-white flex items-center gap-2"><Users className="w-4 h-4 text-[#6366F1]" /> Shareholding Pattern</CardTitle></CardHeader>
          <CardContent>
            <div className="grid sm:grid-cols-2 gap-6">
              <div className="space-y-3">
                {[
                  { label: 'Promoters', value: data.shareholding.promoters, color: '#6366F1' },
                  { label: 'FII/FPI', value: data.shareholding.fii, color: '#10B981' },
                  { label: 'DII', value: data.shareholding.dii, color: '#F59E0B' },
                  { label: 'Public/Retail', value: data.shareholding.public, color: '#EF4444' },
                ].map(s => (
                  <div key={s.label}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-white/60">{s.label}</span>
                      <span className="font-data text-white font-medium">{s.value}%</span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-white/5">
                      <div className="h-full rounded-full transition-all duration-500" style={{ width: `${s.value}%`, background: s.color }} />
                    </div>
                  </div>
                ))}
              </div>
              <div className="flex items-center justify-center">
                <div className="relative w-40 h-40">
                  <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
                    {[
                      { pct: data.shareholding.promoters, color: '#6366F1', offset: 0 },
                      { pct: data.shareholding.fii, color: '#10B981', offset: data.shareholding.promoters },
                      { pct: data.shareholding.dii, color: '#F59E0B', offset: data.shareholding.promoters + data.shareholding.fii },
                      { pct: data.shareholding.public, color: '#EF4444', offset: data.shareholding.promoters + data.shareholding.fii + data.shareholding.dii },
                    ].map((s, i) => (
                      <circle key={i} cx="18" cy="18" r="15.9" fill="none" stroke={s.color} strokeWidth="3"
                        strokeDasharray={`${s.pct} ${100 - s.pct}`} strokeDashoffset={`-${s.offset}`} />
                    ))}
                  </svg>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Peers */}
      {tab === 'peers' && (
        <Card className="bg-[#0A0A0F] border-white/5">
          <CardHeader className="pb-2"><CardTitle className="text-sm text-white">Peer Comparison — {data.sector}</CardTitle></CardHeader>
          <CardContent>
            {peers.length > 0 ? (
              <div className="overflow-x-auto"><table className="w-full text-xs">
                <thead><tr className="border-b border-white/10">
                  {['Company', 'Price', 'M.Cap(Cr)', 'P/E', 'P/B', 'ROE%', 'OPM%', 'NPM%', 'D/E', 'Div%'].map(h => (
                    <th key={h} className="text-right py-2 text-white/40 font-medium px-2 first:text-left">{h}</th>
                  ))}
                </tr></thead>
                <tbody>
                  {/* Current company row highlighted */}
                  <tr className="border-b border-[#6366F1]/20 bg-[#6366F1]/5">
                    <td className="py-2 text-[#6366F1] font-medium">{data.symbol}</td>
                    <td className="text-right py-2 px-2 font-data text-white">₹{data.price}</td>
                    <td className="text-right py-2 px-2 font-data text-white">{data.market_cap_cr?.toLocaleString()}</td>
                    <td className="text-right py-2 px-2 font-data text-white">{f.pe_ratio || '—'}</td>
                    <td className="text-right py-2 px-2 font-data text-white">{f.pb_ratio || '—'}</td>
                    <td className="text-right py-2 px-2 font-data text-white">{f.roe || '—'}</td>
                    <td className="text-right py-2 px-2 font-data text-white">{f.opm || '—'}</td>
                    <td className="text-right py-2 px-2 font-data text-white">{f.npm || '—'}</td>
                    <td className="text-right py-2 px-2 font-data text-white">{f.debt_to_equity || '—'}</td>
                    <td className="text-right py-2 px-2 font-data text-white">{f.dividend_yield || '—'}</td>
                  </tr>
                  {peers.map((p, i) => (
                    <tr key={i} className="border-b border-white/5 hover:bg-white/[0.02] cursor-pointer" onClick={() => navigate(`/stock-analysis/${p.symbol.toLowerCase()}`)}>
                      <td className="py-2 text-white font-medium">{p.symbol}</td>
                      <td className="text-right py-2 px-2 font-data text-white/70">₹{p.price}</td>
                      <td className="text-right py-2 px-2 font-data text-white/70">{p.market_cap_cr?.toLocaleString()}</td>
                      <td className={`text-right py-2 px-2 font-data ${p.pe_ratio && f.pe_ratio && p.pe_ratio < f.pe_ratio ? 'text-emerald-400' : 'text-white/70'}`}>{p.pe_ratio || '—'}</td>
                      <td className="text-right py-2 px-2 font-data text-white/70">{p.pb_ratio || '—'}</td>
                      <td className={`text-right py-2 px-2 font-data ${p.roe && f.roe && p.roe > f.roe ? 'text-emerald-400' : 'text-white/70'}`}>{p.roe || '—'}</td>
                      <td className="text-right py-2 px-2 font-data text-white/70">{p.opm || '—'}</td>
                      <td className="text-right py-2 px-2 font-data text-white/70">{p.npm || '—'}</td>
                      <td className={`text-right py-2 px-2 font-data ${p.debt_to_equity !== null && f.debt_to_equity !== null && p.debt_to_equity < f.debt_to_equity ? 'text-emerald-400' : 'text-white/70'}`}>{p.debt_to_equity || '—'}</td>
                      <td className="text-right py-2 px-2 font-data text-white/70">{p.dividend_yield || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table></div>
            ) : <p className="text-white/30 text-sm text-center py-8">Loading peers...</p>}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
