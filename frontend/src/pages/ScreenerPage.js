import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Filter, Search, Loader2, Download, Star } from 'lucide-react';
import { toast } from 'sonner';

export default function ScreenerPage() {
  const { api } = useAuth();
  const navigate = useNavigate();
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [presets, setPresets] = useState([]);
  const [filters, setFilters] = useState({});
  const [activePreset, setActivePreset] = useState('');

  useEffect(() => {
    api.get('/stocks/screener/presets').then(r => setPresets(r.data.presets || [])).catch(() => {});
  }, [api]);

  const runScreener = async (f = filters) => {
    setLoading(true);
    try {
      const res = await api.post('/stocks/screener', { filters: f });
      setResults(res.data.results || []);
      toast.success(`Found ${res.data.count} stocks`);
    } catch (e) {
      toast.error('Screener failed');
    }
    setLoading(false);
  };

  const applyPreset = (preset) => {
    setFilters(preset.filters);
    setActivePreset(preset.id);
    runScreener(preset.filters);
  };

  const updateFilter = (key, value) => {
    const v = value === '' ? undefined : parseFloat(value);
    setFilters(prev => {
      const next = { ...prev };
      if (v === undefined) delete next[key]; else next[key] = v;
      return next;
    });
    setActivePreset('');
  };

  return (
    <div className="space-y-6 page-enter" data-testid="screener-page">
      <div>
        <h1 className="text-2xl font-bold text-white">Stock Screener</h1>
        <p className="text-sm text-white/40 mt-1">Filter Indian stocks by fundamentals — 40+ stocks</p>
      </div>

      {/* Presets */}
      <div className="flex flex-wrap gap-2">
        {presets.map(p => (
          <Button key={p.id} variant="outline" size="sm"
            onClick={() => applyPreset(p)}
            className={`text-xs ${activePreset === p.id ? 'bg-[#6366F1]/20 border-[#6366F1]/50 text-[#6366F1]' : 'border-white/10 text-white/50 hover:text-white'}`}
            data-testid={`preset-${p.id}`}
          >
            <Star className="w-3 h-3 mr-1" />{p.name}
          </Button>
        ))}
      </div>

      {/* Filters */}
      <Card className="bg-[#0A0A0F] border-white/5">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm text-white flex items-center gap-2">
            <Filter className="w-4 h-4 text-[#6366F1]" /> Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {[
              { key: 'pe_max', label: 'Max P/E', placeholder: '25' },
              { key: 'pe_min', label: 'Min P/E', placeholder: '5' },
              { key: 'roe_min', label: 'Min ROE%', placeholder: '15' },
              { key: 'de_max', label: 'Max D/E', placeholder: '0.5' },
              { key: 'mc_min', label: 'Min MCap(Cr)', placeholder: '1000' },
              { key: 'mc_max', label: 'Max MCap(Cr)', placeholder: '500000' },
              { key: 'dy_min', label: 'Min Div Yield%', placeholder: '2' },
              { key: 'opm_min', label: 'Min OPM%', placeholder: '15' },
            ].map(f => (
              <div key={f.key}>
                <label className="text-[10px] text-white/30 uppercase mb-1 block">{f.label}</label>
                <Input type="number" step="0.1" placeholder={f.placeholder}
                  value={filters[f.key] || ''} onChange={e => updateFilter(f.key, e.target.value)}
                  className="bg-white/[0.03] border-white/10 text-white text-sm h-8"
                />
              </div>
            ))}
          </div>
          <div className="flex gap-2 mt-4">
            <Button onClick={() => runScreener()} disabled={loading} className="bg-[#6366F1] hover:bg-[#4F46E5] text-white text-xs btn-glow" data-testid="run-screener-btn">
              {loading ? <Loader2 className="w-3 h-3 mr-1 animate-spin" /> : <Search className="w-3 h-3 mr-1" />}
              Run Screener
            </Button>
            <Button variant="outline" onClick={() => { setFilters({}); setResults([]); setActivePreset(''); }} className="border-white/10 text-white/50 text-xs">
              Clear
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {results.length > 0 && (
        <Card className="bg-[#0A0A0F] border-white/5">
          <CardHeader className="pb-2 flex flex-row items-center justify-between">
            <CardTitle className="text-sm text-white">{results.length} Stocks Found</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead><tr className="border-b border-white/10">
                  {['Company', 'Sector', 'Price(₹)', 'MCap(Cr)', 'P/E', 'P/B', 'ROE%', 'OPM%', 'NPM%', 'D/E', 'Div%'].map(h => (
                    <th key={h} className="text-right py-2 text-white/40 font-medium px-2 first:text-left whitespace-nowrap">{h}</th>
                  ))}
                </tr></thead>
                <tbody>
                  {results.map((s, i) => (
                    <tr key={i} className="border-b border-white/5 hover:bg-white/[0.02] cursor-pointer stagger-item" onClick={() => navigate(`/stock-analysis/${s.symbol.toLowerCase()}`)} data-testid={`screener-row-${i}`}>
                      <td className="py-2">
                        <span className="text-white font-medium">{s.symbol}</span>
                        <span className="text-white/30 ml-1 text-[10px]">{s.name?.slice(0, 20)}</span>
                      </td>
                      <td className="text-right py-2 px-2"><Badge variant="outline" className="text-[8px] border-white/10 text-white/30">{s.sector}</Badge></td>
                      <td className="text-right py-2 px-2 font-data text-white">₹{s.price?.toLocaleString()}</td>
                      <td className="text-right py-2 px-2 font-data text-white/70">{s.market_cap_cr?.toLocaleString()}</td>
                      <td className={`text-right py-2 px-2 font-data ${s.pe_ratio && s.pe_ratio < 20 ? 'text-emerald-400' : 'text-white/70'}`}>{s.pe_ratio || '—'}</td>
                      <td className="text-right py-2 px-2 font-data text-white/70">{s.pb_ratio || '—'}</td>
                      <td className={`text-right py-2 px-2 font-data ${s.roe && s.roe > 15 ? 'text-emerald-400' : 'text-white/70'}`}>{s.roe || '—'}</td>
                      <td className={`text-right py-2 px-2 font-data ${s.opm && s.opm > 15 ? 'text-emerald-400' : 'text-white/70'}`}>{s.opm || '—'}</td>
                      <td className="text-right py-2 px-2 font-data text-white/70">{s.npm || '—'}</td>
                      <td className={`text-right py-2 px-2 font-data ${s.debt_to_equity !== null && s.debt_to_equity < 0.5 ? 'text-emerald-400' : s.debt_to_equity > 1 ? 'text-red-400' : 'text-white/70'}`}>{s.debt_to_equity || '—'}</td>
                      <td className={`text-right py-2 px-2 font-data ${s.dividend_yield && s.dividend_yield > 2 ? 'text-emerald-400' : 'text-white/70'}`}>{s.dividend_yield || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
