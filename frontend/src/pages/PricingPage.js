import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Check, X, Zap, Crown, Rocket, Phone, MessageCircle, ArrowRight } from 'lucide-react';

const PLANS = [
  {
    id: 'basic',
    name: 'Basic',
    price: '999',
    period: '/month',
    description: 'Essential tools for beginner traders',
    color: '#6366F1',
    features: [
      { text: '5 AI Signals per day', included: true },
      { text: 'Basic market data (Crypto + Forex)', included: true },
      { text: 'Single timeframe analysis', included: true },
      { text: 'Price alerts (up to 10)', included: true },
      { text: 'Trade Journal', included: true },
      { text: 'Multi-timeframe analysis', included: false },
      { text: 'Strategy selection', included: false },
      { text: 'Beast AI Chat', included: false },
      { text: 'Admin dashboard', included: false },
    ],
    cta: 'Get Started',
  },
  {
    id: 'pro',
    name: 'Pro',
    price: '2,499',
    period: '/month',
    description: 'Advanced tools for serious traders',
    color: '#00FF94',
    popular: true,
    features: [
      { text: '25 AI Signals per day', included: true },
      { text: 'All markets (Crypto + Forex + Indian)', included: true },
      { text: 'Multi-timeframe analysis (3+ TFs)', included: true },
      { text: '10 Strategy templates', included: true },
      { text: 'SL/TP & holding duration', included: true },
      { text: 'Trade Journal with analytics', included: true },
      { text: 'Beast AI Chat (100 msgs/day)', included: true },
      { text: 'Unlimited price alerts', included: true },
      { text: 'Priority support', included: true },
    ],
    cta: 'Go Pro',
  },
  {
    id: 'beast',
    name: 'Beast Mode',
    price: '4,999',
    period: '/month',
    description: 'Institutional-grade trading intelligence',
    color: '#FFD700',
    features: [
      { text: 'Unlimited AI Signals', included: true },
      { text: 'All markets + real-time streaming', included: true },
      { text: 'All timeframes + confluence scoring', included: true },
      { text: 'All strategies + custom strategies', included: true },
      { text: 'Advanced SL/TP with invalidation levels', included: true },
      { text: 'Trade Journal + AI analysis', included: true },
      { text: 'Unlimited Beast AI Chat', included: true },
      { text: 'Portfolio analytics + P&L tracking', included: true },
      { text: 'Dedicated support + early features', included: true },
    ],
    cta: 'Unleash the Beast',
  },
];

export default function PricingPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [billingCycle, setBillingCycle] = useState('monthly');

  const getPrice = (plan) => {
    if (billingCycle === 'yearly') {
      const monthly = parseInt(plan.price.replace(',', ''));
      return Math.round(monthly * 10).toLocaleString();
    }
    return plan.price;
  };

  return (
    <div className="space-y-8" data-testid="pricing-page">
      <div className="text-center">
        <h1 className="text-3xl sm:text-4xl font-bold text-white" style={{ fontFamily: 'Manrope' }}>
          Choose Your Trading Edge
        </h1>
        <p className="text-sm text-white/40 mt-2 max-w-lg mx-auto">
          Unlock institutional-grade trading signals, multi-timeframe analysis, and AI-powered insights
        </p>
      </div>

      {/* Billing Toggle */}
      <div className="flex items-center justify-center gap-3" data-testid="billing-toggle">
        <span className={`text-sm ${billingCycle === 'monthly' ? 'text-white' : 'text-white/40'}`}>Monthly</span>
        <button onClick={() => setBillingCycle(prev => prev === 'monthly' ? 'yearly' : 'monthly')}
          className="relative w-12 h-6 rounded-full bg-white/10 border border-white/20 transition-colors"
          data-testid="billing-switch">
          <div className={`absolute top-0.5 w-5 h-5 rounded-full transition-all ${
            billingCycle === 'yearly' ? 'left-6 bg-[#00FF94]' : 'left-0.5 bg-white/60'
          }`} />
        </button>
        <span className={`text-sm ${billingCycle === 'yearly' ? 'text-white' : 'text-white/40'}`}>
          Yearly <Badge className="bg-[#00FF94]/10 text-[#00FF94] text-[9px] ml-1">Save 17%</Badge>
        </span>
      </div>

      {/* Plans Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
        {PLANS.map(plan => (
          <Card key={plan.id}
            className={`glass-panel border-white/10 relative overflow-hidden transition-all hover:scale-[1.02] hover:shadow-lg ${
              plan.popular ? 'border-[#00FF94]/30 shadow-[0_0_20px_rgba(0,255,148,0.1)]' : ''
            }`}
            data-testid={`plan-${plan.id}`}
          >
            {plan.popular && (
              <div className="absolute top-0 right-0 bg-[#00FF94] text-black text-[10px] font-bold px-3 py-1 rounded-bl-lg uppercase tracking-wider">
                Most Popular
              </div>
            )}
            <CardContent className="p-6 flex flex-col h-full">
              <div className="mb-6">
                <div className="flex items-center gap-2 mb-2">
                  {plan.id === 'basic' && <Rocket className="w-5 h-5" style={{ color: plan.color }} />}
                  {plan.id === 'pro' && <Zap className="w-5 h-5" style={{ color: plan.color }} />}
                  {plan.id === 'beast' && <Crown className="w-5 h-5" style={{ color: plan.color }} />}
                  <h3 className="text-lg font-bold text-white">{plan.name}</h3>
                </div>
                <p className="text-xs text-white/40 mb-4">{plan.description}</p>
                <div className="flex items-baseline gap-1">
                  <span className="text-xs text-white/40">INR</span>
                  <span className="text-4xl font-bold font-data text-white">{getPrice(plan)}</span>
                  <span className="text-sm text-white/40">{billingCycle === 'yearly' ? '/year' : plan.period}</span>
                </div>
              </div>

              <div className="flex-1 space-y-3 mb-6">
                {plan.features.map((feat, i) => (
                  <div key={i} className="flex items-start gap-2">
                    {feat.included ? (
                      <Check className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: plan.color }} />
                    ) : (
                      <X className="w-4 h-4 text-white/15 flex-shrink-0 mt-0.5" />
                    )}
                    <span className={`text-xs ${feat.included ? 'text-white/70' : 'text-white/25'}`}>{feat.text}</span>
                  </div>
                ))}
              </div>

              <Button
                className="w-full text-sm font-semibold"
                style={{
                  backgroundColor: plan.popular ? plan.color : 'transparent',
                  color: plan.popular ? '#000' : plan.color,
                  border: plan.popular ? 'none' : `1px solid ${plan.color}40`,
                }}
                onClick={() => {
                  if (user) {
                    window.open(`https://wa.me/918102126223?text=Hi! I'm interested in the SignalBeast Pro ${plan.name} plan (INR ${getPrice(plan)}${billingCycle === 'yearly' ? '/year' : plan.period}).`, '_blank');
                  } else {
                    navigate('/auth');
                  }
                }}
                data-testid={`plan-cta-${plan.id}`}
              >
                {plan.cta} <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Contact Section */}
      <Card className="glass-panel border-white/10 max-w-2xl mx-auto" data-testid="contact-section">
        <CardContent className="p-6 text-center space-y-4">
          <h3 className="text-lg font-bold text-white">Ready to upgrade? Contact us</h3>
          <p className="text-xs text-white/40">Get in touch to activate your premium plan instantly</p>
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <a href="tel:+918102126223" className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-[#6366F1]/10 border border-[#6366F1]/30 text-[#6366F1] text-sm hover:bg-[#6366F1]/20 transition-colors"
              data-testid="contact-phone-1">
              <Phone className="w-4 h-4" /> +91 8102126223
            </a>
            <a href="tel:+918867678750" className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-[#6366F1]/10 border border-[#6366F1]/30 text-[#6366F1] text-sm hover:bg-[#6366F1]/20 transition-colors"
              data-testid="contact-phone-2">
              <Phone className="w-4 h-4" /> +91 8867678750
            </a>
          </div>
          <div className="flex items-center justify-center gap-4">
            <a href="https://wa.me/918102126223?text=Hi! I'm interested in SignalBeast Pro premium plans."
              target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-[#25D366]/10 border border-[#25D366]/30 text-[#25D366] text-sm hover:bg-[#25D366]/20 transition-colors"
              data-testid="contact-whatsapp">
              <MessageCircle className="w-4 h-4" /> WhatsApp Us
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
