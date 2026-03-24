import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Layers, Plus, Trash2, Play, Save, ChevronRight, ArrowRight } from 'lucide-react';
import { toast } from 'sonner';

const INDICATORS = [
  { id: 'price_above', label: 'Price Above', type: 'price' },
  { id: 'price_below', label: 'Price Below', type: 'price' },
  { id: 'change_gt', label: '24h Change >', type: 'percent' },
  { id: 'change_lt', label: '24h Change <', type: 'percent' },
  { id: 'volume_gt', label: 'Volume >', type: 'number' },
];

const ACTIONS = ['BUY', 'SELL', 'ALERT'];

const TEMPLATES = [
  {
    name: 'Dip Buyer',
    desc: 'Buy when 24h change drops below -5%',
    rules: [{ indicator: 'change_lt', value: '-5', action: 'BUY' }],
  },
  {
    name: 'Breakout Catcher',
    desc: 'Alert when price breaks above key level',
    rules: [{ indicator: 'price_above', value: '70000', action: 'ALERT' }],
  },
  {
    name: 'Momentum Trader',
    desc: 'Buy on strong upward momentum (>8% 24h)',
    rules: [{ indicator: 'change_gt', value: '8', action: 'BUY' }],
  },
  {
    name: 'High Volume Play',
    desc: 'Alert on unusual volume spikes',
    rules: [{ indicator: 'volume_gt', value: '1000000000', action: 'ALERT' }],
  },
];

export default function StrategyPage() {
  const [strategies, setStrategies] = useState([]);
  const [building, setBuilding] = useState(false);
  const [name, setName] = useState('');
  const [rules, setRules] = useState([{ indicator: 'price_above', value: '', action: 'BUY' }]);

  const addRule = () => {
    setRules([...rules, { indicator: 'price_above', value: '', action: 'BUY' }]);
  };

  const removeRule = (idx) => {
    setRules(rules.filter((_, i) => i !== idx));
  };

  const updateRule = (idx, field, value) => {
    setRules(rules.map((r, i) => i === idx ? { ...r, [field]: value } : r));
  };

  const saveStrategy = () => {
    if (!name) { toast.error('Enter a strategy name'); return; }
    if (rules.some(r => !r.value)) { toast.error('Fill all rule values'); return; }
    const strat = {
      id: Date.now().toString(),
      name,
      rules: [...rules],
      created: new Date().toISOString(),
      status: 'active',
    };
    setStrategies([strat, ...strategies]);
    setBuilding(false);
    setName('');
    setRules([{ indicator: 'price_above', value: '', action: 'BUY' }]);
    toast.success('Strategy saved');
  };

  const applyTemplate = (template) => {
    setName(template.name);
    setRules([...template.rules]);
    setBuilding(true);
  };

  const deleteStrategy = (id) => {
    setStrategies(strategies.filter(s => s.id !== id));
    toast.success('Strategy deleted');
  };

  return (
    <div className="space-y-6" data-testid="strategy-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white" style={{ fontFamily: 'Manrope' }}>Strategy Builder</h1>
          <p className="text-sm text-white/40 mt-1">Build rule-based trading strategies</p>
        </div>
        {!building && (
          <Button className="bg-[#6366F1] hover:bg-[#4F46E5] text-white text-xs shadow-[0_0_15px_rgba(99,102,241,0.4)] active:scale-95" onClick={() => setBuilding(true)} data-testid="new-strategy-btn">
            <Plus className="w-3.5 h-3.5 mr-1.5" /> New Strategy
          </Button>
        )}
      </div>

      {/* Templates */}
      {!building && strategies.length === 0 && (
        <div>
          <h2 className="text-sm text-white/60 mb-3 font-medium">Quick Templates</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {TEMPLATES.map((t, i) => (
              <Card key={i} className="glass-panel border-white/10 card-hover cursor-pointer" onClick={() => applyTemplate(t)} data-testid={`template-${i}`}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-white font-medium">{t.name}</p>
                      <p className="text-[10px] text-white/40 mt-0.5">{t.desc}</p>
                    </div>
                    <ChevronRight className="w-4 h-4 text-white/20" />
                  </div>
                  <div className="flex gap-1.5 mt-2">
                    {t.rules.map((r, ri) => (
                      <Badge key={ri} variant="outline" className="text-[9px] border-[#6366F1]/20 text-[#6366F1]">
                        {INDICATORS.find(ind => ind.id === r.indicator)?.label} {r.value} {ArrowRight && '→'} {r.action}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Builder */}
      {building && (
        <Card className="glass-panel border-white/10 border-l-2 border-l-[#6366F1]" data-testid="strategy-builder">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-white/80 flex items-center gap-2">
              <Layers className="w-4 h-4 text-[#6366F1]" /> Build Strategy
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label className="text-xs text-white/60">Strategy Name</Label>
              <Input className="bg-black/50 border-white/10 text-white text-sm mt-1 max-w-sm" placeholder="e.g., BTC Dip Buyer" value={name} onChange={e => setName(e.target.value)} data-testid="strategy-name-input" />
            </div>

            <div className="space-y-3">
              <Label className="text-xs text-white/60">Rules (IF conditions)</Label>
              {rules.map((rule, idx) => (
                <div key={idx} className="flex items-center gap-2 p-3 rounded-lg bg-white/[0.02] border border-white/5">
                  <span className="text-[10px] text-white/30 w-6 shrink-0">IF</span>
                  <Select value={rule.indicator} onValueChange={v => updateRule(idx, 'indicator', v)}>
                    <SelectTrigger className="w-[160px] bg-black/50 border-white/10 text-white text-xs" data-testid={`rule-indicator-${idx}`}><SelectValue /></SelectTrigger>
                    <SelectContent className="bg-[#09090B] border-white/10">
                      {INDICATORS.map(ind => <SelectItem key={ind.id} value={ind.id}>{ind.label}</SelectItem>)}
                    </SelectContent>
                  </Select>
                  <Input type="number" step="any" className="w-[120px] bg-black/50 border-white/10 text-white text-xs" placeholder="Value" value={rule.value} onChange={e => updateRule(idx, 'value', e.target.value)} data-testid={`rule-value-${idx}`} />
                  <ArrowRight className="w-3.5 h-3.5 text-white/20 shrink-0" />
                  <Select value={rule.action} onValueChange={v => updateRule(idx, 'action', v)}>
                    <SelectTrigger className="w-[100px] bg-black/50 border-white/10 text-white text-xs" data-testid={`rule-action-${idx}`}><SelectValue /></SelectTrigger>
                    <SelectContent className="bg-[#09090B] border-white/10">
                      {ACTIONS.map(a => <SelectItem key={a} value={a}>{a}</SelectItem>)}
                    </SelectContent>
                  </Select>
                  {rules.length > 1 && (
                    <Button variant="ghost" size="icon" className="w-7 h-7 text-white/30 hover:text-[#EF4444] shrink-0" onClick={() => removeRule(idx)}>
                      <Trash2 className="w-3 h-3" />
                    </Button>
                  )}
                </div>
              ))}
              <Button variant="outline" size="sm" className="border-dashed border-white/10 text-white/40 text-xs" onClick={addRule} data-testid="add-rule-btn">
                <Plus className="w-3 h-3 mr-1" /> Add Rule
              </Button>
            </div>

            <div className="flex gap-2 pt-2">
              <Button className="bg-[#6366F1] hover:bg-[#4F46E5] text-white text-xs active:scale-95" onClick={saveStrategy} data-testid="save-strategy-btn">
                <Save className="w-3.5 h-3.5 mr-1.5" /> Save Strategy
              </Button>
              <Button variant="outline" className="border-white/10 text-white/50 text-xs" onClick={() => setBuilding(false)} data-testid="cancel-strategy-btn">
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Saved Strategies */}
      {strategies.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-sm text-white/60 font-medium">Your Strategies</h2>
          {strategies.map(strat => (
            <Card key={strat.id} className="glass-panel border-white/10" data-testid={`strategy-${strat.id}`}>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-white font-medium">{strat.name}</span>
                      <Badge className="bg-[#10B981]/10 text-[#10B981] text-[9px]">{strat.status}</Badge>
                    </div>
                    <div className="flex gap-1.5 mt-1.5">
                      {strat.rules.map((r, ri) => (
                        <Badge key={ri} variant="outline" className="text-[9px] border-white/10 text-white/40">
                          {INDICATORS.find(ind => ind.id === r.indicator)?.label} {r.value} → {r.action}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <Button variant="ghost" size="icon" className="w-7 h-7 text-white/30 hover:text-[#EF4444]" onClick={() => deleteStrategy(strat.id)}>
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
