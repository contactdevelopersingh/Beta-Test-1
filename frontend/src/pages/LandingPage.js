import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Zap, TrendingUp, Shield, BarChart3, Activity, ArrowRight, ChevronRight, Layers, Brain, Target, BookOpen, Clock, Crosshair } from 'lucide-react';

const features = [
  { icon: Brain, title: 'Multi-Timeframe AI Signals', desc: 'Analyze 3+ timeframes simultaneously with confluence scoring. Institutional-grade entry, SL, TP1/TP2/TP3 levels.' },
  { icon: TrendingUp, title: '3 Markets, 80+ Assets', desc: 'Crypto (Kraken), Forex (OANDA), Indian stocks (NSE/BSE). Real-time bid/ask spreads and live ticks.' },
  { icon: Layers, title: '10 Trading Strategies', desc: 'EMA Crossover, RSI Divergence, Smart Money Concepts, VWAP, Ichimoku, Fibonacci, and more.' },
  { icon: Target, title: 'SL/TP & Risk Management', desc: 'Every signal comes with calculated Stop Loss, 3 Take Profit levels, Risk:Reward ratio, and invalidation level.' },
  { icon: BookOpen, title: 'Trade Journal & Analytics', desc: 'Log trades with P&L tracking, emotion tags, quality ratings, win rate analytics, and AI analysis.' },
  { icon: Clock, title: 'Holding Duration Estimates', desc: 'AI calculates optimal trade holding time based on your profit targets and market volatility.' },
];

const markets = [
  { name: 'Crypto', pairs: '20 Pairs', source: 'Kraken Exchange', color: '#F59E0B', items: ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'ADA'] },
  { name: 'Forex', pairs: '21 Pairs', source: 'OANDA (Institutional)', color: '#10B981', items: ['EUR/USD', 'GBP/USD', 'XAU/USD', 'GBP/JPY'] },
  { name: 'Indian', pairs: '44 Assets', source: 'NSE/BSE Live', color: '#EF4444', items: ['NIFTY 50', 'SENSEX', 'RELIANCE', 'TCS'] },
];

const stats = [
  { value: '83+', label: 'Live Assets' },
  { value: '10', label: 'AI Strategies' },
  { value: '3', label: 'Markets' },
  { value: '5s', label: 'Data Refresh' },
];

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen noise-overlay" style={{ background: '#050505' }}>
      {/* Nav */}
      <nav className="fixed top-0 w-full z-50 backdrop-blur-xl backdrop-saturate-150 bg-black/70 border-b border-white/5" data-testid="landing-nav">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Activity className="w-6 h-6 text-[#6366F1]" />
            <span className="text-lg font-extrabold text-white tracking-tight uppercase" style={{ fontFamily: 'Manrope' }}>Titan Trade</span>
            <span className="text-[9px] bg-[#6366F1]/20 text-[#6366F1] px-1.5 py-0.5 rounded font-bold tracking-widest">PRO</span>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="ghost" className="text-white/60 hover:text-white text-sm hidden sm:flex" onClick={() => navigate('/auth')} data-testid="nav-login-btn">
              Log In
            </Button>
            <Button
              className="bg-[#6366F1] hover:bg-[#4F46E5] text-white text-sm shadow-[0_0_15px_rgba(99,102,241,0.4)] active:scale-95 font-mono uppercase tracking-wider"
              onClick={() => navigate('/auth')}
              data-testid="nav-get-started-btn"
            >
              Get Started <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative pt-32 pb-24 px-6 overflow-hidden" data-testid="hero-section">
        <div className="absolute inset-0 hero-glow" />
        <div className="absolute top-20 right-0 w-96 h-96 bg-[#6366F1]/5 rounded-full blur-[120px]" />
        <div className="absolute bottom-0 left-0 w-72 h-72 bg-[#10B981]/3 rounded-full blur-[100px]" />
        <div className="max-w-5xl mx-auto relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-[#6366F1]/30 bg-[#6366F1]/10 mb-8 stagger-item">
            <div className="w-1.5 h-1.5 rounded-full bg-[#10B981] animate-pulse" />
            <span className="text-xs text-[#6366F1] font-medium font-mono">LIVE TRADING INTELLIGENCE</span>
          </div>

          <h1 className="text-3xl sm:text-4xl lg:text-6xl font-extrabold text-white leading-[1.08] tracking-tight mb-6 stagger-item uppercase" style={{ fontFamily: 'Manrope', letterSpacing: '-0.02em' }}>
            Retail Interface.<br />
            <span className="text-[#6366F1]">Institutional</span> Edge.
          </h1>

          <p className="text-sm sm:text-base text-white/50 max-w-xl mb-8 sm:mb-10 stagger-item leading-relaxed" style={{ fontFamily: 'Sora' }}>
            Multi-timeframe AI signals with SL/TP levels, confluence scoring, and 10 trading strategies across Crypto, Forex & Indian markets.
          </p>

          <div className="flex flex-wrap gap-4 stagger-item">
            <Button
              size="lg"
              className="bg-[#6366F1] hover:bg-[#4F46E5] text-white shadow-[0_0_20px_rgba(99,102,241,0.4)] active:scale-95 text-xs font-mono font-semibold tracking-wider uppercase px-8"
              onClick={() => navigate('/auth')}
              data-testid="hero-get-started-btn"
            >
              Start Trading Free <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="border-white/20 text-white hover:bg-white/5 hover:border-white/40 text-xs font-mono uppercase tracking-wider"
              onClick={() => navigate('/auth')}
              data-testid="hero-demo-btn"
            >
              View Live Markets
            </Button>
          </div>
        </div>
      </section>

      {/* Stats Bar */}
      <section className="py-12 px-6 border-y border-white/5" data-testid="stats-section">
        <div className="max-w-5xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((s, i) => (
            <div key={i} className="text-center stagger-item">
              <div className="text-3xl sm:text-4xl font-bold text-white" style={{ fontFamily: 'JetBrains Mono' }}>{s.value}</div>
              <div className="text-[10px] text-white/40 mt-1.5 uppercase tracking-widest font-mono">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Markets */}
      <section className="py-20 px-6" data-testid="markets-section">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-base font-extrabold text-white mb-1 uppercase tracking-tight" style={{ fontFamily: 'Manrope' }}>
            Markets We Cover
          </h2>
          <p className="text-xs text-white/40 mb-10 font-mono">INSTITUTIONAL DATA FEEDS</p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {markets.map((m, i) => (
              <div key={i} className="glass-panel rounded-lg p-6 glow-card stagger-item" style={{ borderColor: `${m.color}15` }}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-bold text-white uppercase" style={{ fontFamily: 'Manrope' }}>{m.name}</h3>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded" style={{ color: m.color, backgroundColor: `${m.color}10` }}>{m.pairs}</span>
                </div>
                <p className="text-[10px] text-white/30 mb-3 font-mono">{m.source}</p>
                <div className="flex flex-wrap gap-1.5">
                  {m.items.map((item, j) => (
                    <span key={j} className="text-[10px] px-2 py-1 rounded bg-white/5 text-white/50 font-mono">{item}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-6" data-testid="features-section">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-base font-extrabold text-white mb-1 uppercase tracking-tight" style={{ fontFamily: 'Manrope' }}>
            Trading Intelligence
          </h2>
          <p className="text-xs text-white/40 mb-10 font-mono">FEATURES BUILT FOR PROFESSIONAL TRADERS</p>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {features.map(({ icon: Icon, title, desc }, i) => (
              <div key={i} className="glass-panel rounded-lg p-5 glow-card stagger-item group">
                <div className="w-9 h-9 rounded-md bg-[#6366F1]/10 flex items-center justify-center mb-3 group-hover:bg-[#6366F1]/20 transition-colors">
                  <Icon className="w-4.5 h-4.5 text-[#6366F1]" />
                </div>
                <h3 className="text-xs font-bold text-white mb-1.5 uppercase tracking-wide" style={{ fontFamily: 'Manrope' }}>{title}</h3>
                <p className="text-[11px] text-white/40 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6" data-testid="cta-section">
        <div className="max-w-3xl mx-auto text-center">
          <div className="glass-panel rounded-xl p-12 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-b from-[#6366F1]/5 to-transparent" />
            <div className="absolute -top-20 -right-20 w-40 h-40 bg-[#6366F1]/10 rounded-full blur-[60px]" />
            <div className="relative z-10">
              <h2 className="text-base font-extrabold text-white mb-3 uppercase tracking-tight" style={{ fontFamily: 'Manrope' }}>
                Start Trading with AI
              </h2>
              <p className="text-xs text-white/40 mb-8 max-w-md mx-auto">
                Free account. No credit card. Instant access to AI signals, live markets, and trade journal.
              </p>
              <Button
                size="lg"
                className="bg-[#6366F1] hover:bg-[#4F46E5] text-white shadow-[0_0_20px_rgba(99,102,241,0.4)] active:scale-95 text-xs font-mono font-semibold uppercase tracking-wider px-10"
                onClick={() => navigate('/auth')}
                data-testid="cta-get-started-btn"
              >
                Create Free Account <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8 px-6" data-testid="landing-footer">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-[#6366F1]" />
            <span className="text-sm text-white/40 font-mono">Titan Trade</span>
          </div>
          <p className="text-[10px] text-white/20 font-mono">Not financial advice. Always DYOR. &copy; 2026 Titan Trade.</p>
        </div>
      </footer>
    </div>
  );
}
