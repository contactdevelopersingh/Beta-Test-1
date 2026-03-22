import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Zap, TrendingUp, Shield, BarChart3, Activity, ArrowRight, ChevronRight } from 'lucide-react';

const features = [
  { icon: Zap, title: 'AI-Powered Signals', desc: 'Institutional-grade trading signals with confidence scores powered by advanced AI analysis.' },
  { icon: TrendingUp, title: 'Multi-Market Coverage', desc: 'Crypto, Forex, and Indian stock markets. All in one platform with real-time data.' },
  { icon: Shield, title: 'Smart Risk Management', desc: 'Position sizing, stop-loss calculations, and portfolio risk analytics built-in.' },
  { icon: BarChart3, title: 'Live Market Data', desc: 'Real-time prices, charts, sentiment indicators, and market depth analysis.' },
];

const stats = [
  { value: '50K+', label: 'Signals Generated' },
  { value: '99.9%', label: 'Uptime SLA' },
  { value: '3', label: 'Market Types' },
  { value: '<100ms', label: 'Signal Latency' },
];

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen" style={{ background: '#050505' }}>
      {/* Nav */}
      <nav className="fixed top-0 w-full z-50 bg-[#050505]/80 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Activity className="w-6 h-6 text-[#6366F1]" />
            <span className="text-lg font-bold text-white tracking-tight" style={{ fontFamily: 'Manrope' }}>SignalBeast</span>
            <span className="text-[9px] bg-[#6366F1]/20 text-[#6366F1] px-1.5 py-0.5 rounded font-bold tracking-widest">PRO</span>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="ghost" className="text-white/60 hover:text-white text-sm hidden sm:flex" onClick={() => navigate('/auth')} data-testid="nav-login-btn">
              Log In
            </Button>
            <Button
              className="bg-[#6366F1] hover:bg-[#4F46E5] text-white text-sm shadow-[0_0_15px_rgba(99,102,241,0.4)] active:scale-95"
              onClick={() => navigate('/auth')}
              data-testid="nav-get-started-btn"
            >
              Get Started <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative pt-32 pb-24 px-6 hero-gradient overflow-hidden">
        <div className="absolute inset-0 opacity-30" style={{ backgroundImage: 'radial-gradient(circle at 20% 50%, rgba(99, 102, 241, 0.08) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(0, 255, 148, 0.05) 0%, transparent 40%)' }} />
        <div className="max-w-5xl mx-auto relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-[#6366F1]/30 bg-[#6366F1]/10 mb-8 animate-fade-in-up">
            <div className="w-1.5 h-1.5 rounded-full bg-[#00FF94] animate-pulse" />
            <span className="text-xs text-[#6366F1] font-medium">Live Trading Intelligence</span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-white leading-[1.1] tracking-tight mb-6 animate-fade-in-up" style={{ fontFamily: 'Manrope' }}>
            Retail Interface.<br />
            <span className="text-[#6366F1]">Hedge Fund</span> Intelligence.
          </h1>

          <p className="text-base md:text-lg text-white/50 max-w-2xl mb-10 animate-fade-in-up stagger-2 leading-relaxed">
            AI-powered trading signals across Crypto, Forex, and Indian markets.
            Institutional-grade analytics made accessible for every trader.
          </p>

          <div className="flex flex-wrap gap-4 animate-fade-in-up stagger-3">
            <Button
              size="lg"
              className="bg-[#6366F1] hover:bg-[#4F46E5] text-white shadow-[0_0_20px_rgba(99,102,241,0.4)] active:scale-95 text-sm font-semibold tracking-wide uppercase px-8"
              onClick={() => navigate('/auth')}
              data-testid="hero-get-started-btn"
            >
              Start Trading <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="border-white/20 text-white hover:bg-white/5 hover:border-white/40 text-sm"
              onClick={() => navigate('/auth')}
              data-testid="hero-demo-btn"
            >
              View Live Demo
            </Button>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-16 px-6 border-y border-white/5">
        <div className="max-w-5xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((s, i) => (
            <div key={i} className="text-center animate-fade-in-up" style={{ animationDelay: `${i * 0.1}s` }}>
              <div className="text-2xl sm:text-3xl font-bold text-white font-data" style={{ fontFamily: 'JetBrains Mono' }}>{s.value}</div>
              <div className="text-xs text-white/40 mt-1 uppercase tracking-wider">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-base md:text-lg font-bold text-white mb-2" style={{ fontFamily: 'Manrope' }}>
            Built for Serious Traders
          </h2>
          <p className="text-sm text-white/40 mb-12 max-w-lg">
            Everything you need to make informed trading decisions, powered by AI and institutional-grade data.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {features.map(({ icon: Icon, title, desc }, i) => (
              <div
                key={i}
                className="glass-panel rounded-xl p-6 card-hover animate-fade-in-up"
                style={{ animationDelay: `${i * 0.1}s` }}
              >
                <div className="w-10 h-10 rounded-lg bg-[#6366F1]/10 flex items-center justify-center mb-4">
                  <Icon className="w-5 h-5 text-[#6366F1]" />
                </div>
                <h3 className="text-sm font-semibold text-white mb-2">{title}</h3>
                <p className="text-xs text-white/40 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <div className="glass-panel rounded-2xl p-12 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-b from-[#6366F1]/5 to-transparent" />
            <div className="relative z-10">
              <h2 className="text-base md:text-lg font-bold text-white mb-3" style={{ fontFamily: 'Manrope' }}>
                Ready to Trade Smarter?
              </h2>
              <p className="text-sm text-white/40 mb-8 max-w-md mx-auto">
                Join thousands of traders using AI-powered signals for better decision making.
              </p>
              <Button
                size="lg"
                className="bg-[#6366F1] hover:bg-[#4F46E5] text-white shadow-[0_0_20px_rgba(99,102,241,0.4)] active:scale-95 text-sm font-semibold uppercase tracking-wide px-10"
                onClick={() => navigate('/auth')}
                data-testid="cta-get-started-btn"
              >
                Get Started Free <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8 px-6">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-[#6366F1]" />
            <span className="text-sm text-white/40">SignalBeast Pro</span>
          </div>
          <p className="text-xs text-white/20">Not financial advice. Always DYOR. &copy; 2026 SignalBeast Pro.</p>
        </div>
      </footer>
    </div>
  );
}
