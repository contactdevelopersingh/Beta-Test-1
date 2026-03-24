import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Check, X, Zap, Crown, Rocket, ArrowRight } from 'lucide-react';

const PLANS = [
  {
    id: 'basic',
    name: 'Basic',
    weeklyPrice: '499',
    monthlyPrice: '1,499',
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
      { text: 'Titan AI Chat', included: false },
      { text: 'Priority support', included: false },
    ],
    cta: 'Get Started',
  },
  {
    id: 'pro',
    name: 'Pro',
    weeklyPrice: '999',
    monthlyPrice: '3,499',
    description: 'Advanced tools for serious traders',
    color: '#10B981',
    popular: true,
    features: [
      { text: '25 AI Signals per day', included: true },
      { text: 'All markets (Crypto + Forex + Indian)', included: true },
      { text: 'Multi-timeframe analysis (3+ TFs)', included: true },
      { text: '10 Strategy templates', included: true },
      { text: 'SL/TP & holding duration', included: true },
      { text: 'Trade Journal with analytics', included: true },
      { text: 'Titan AI Chat (100 msgs/day)', included: true },
      { text: 'Unlimited price alerts', included: true },
      { text: 'Priority support', included: true },
    ],
    cta: 'Go Pro',
  },
  {
    id: 'titan',
    name: 'Titan',
    weeklyPrice: '1,999',
    monthlyPrice: '6,999',
    description: 'Institutional-grade trading intelligence',
    color: '#F59E0B',
    features: [
      { text: 'Unlimited AI Signals', included: true },
      { text: 'All markets + real-time streaming', included: true },
      { text: 'All timeframes + confluence scoring', included: true },
      { text: 'All strategies + custom strategies', included: true },
      { text: 'Advanced SL/TP with invalidation levels', included: true },
      { text: 'Trade Journal + AI analysis', included: true },
      { text: 'Unlimited Titan AI Chat', included: true },
      { text: 'Portfolio analytics + P&L tracking', included: true },
      { text: 'Dedicated support + early features', included: true },
    ],
    cta: 'Go Titan',
  },
];

export default function PricingPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [billingCycle, setBillingCycle] = useState('weekly');

  const getPrice = (plan) => billingCycle === 'weekly' ? plan.weeklyPrice : plan.monthlyPrice;

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
        <span className={`text-sm ${billingCycle === 'weekly' ? 'text-white' : 'text-white/40'}`}>Weekly</span>
        <button onClick={() => setBillingCycle(prev => prev === 'weekly' ? 'monthly' : 'weekly')}
          className="relative w-12 h-6 rounded-full bg-white/10 border border-white/20 transition-colors"
          data-testid="billing-switch">
          <div className={`absolute top-0.5 w-5 h-5 rounded-full transition-all ${
            billingCycle === 'monthly' ? 'left-6 bg-[#10B981]' : 'left-0.5 bg-white/60'
          }`} />
        </button>
        <span className={`text-sm ${billingCycle === 'monthly' ? 'text-white' : 'text-white/40'}`}>
          Monthly <Badge className="bg-[#10B981]/10 text-[#10B981] text-[9px] ml-1">Best Value</Badge>
        </span>
      </div>

      {/* Plans Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
        {PLANS.map(plan => (
          <Card key={plan.id}
            className={`glass-panel border-white/10 relative overflow-hidden transition-all hover:scale-[1.02] hover:shadow-lg ${
              plan.popular ? 'border-[#10B981]/30 shadow-[0_0_20px_rgba(0,255,148,0.1)]' : ''
            }`}
            data-testid={`plan-${plan.id}`}
          >
            {plan.popular && (
              <div className="absolute top-0 right-0 bg-[#10B981] text-black text-[10px] font-bold px-3 py-1 rounded-bl-lg uppercase tracking-wider">
                Most Popular
              </div>
            )}
            <CardContent className="p-6 flex flex-col h-full">
              <div className="mb-6">
                <div className="flex items-center gap-2 mb-2">
                  {plan.id === 'basic' && <Rocket className="w-5 h-5" style={{ color: plan.color }} />}
                  {plan.id === 'pro' && <Zap className="w-5 h-5" style={{ color: plan.color }} />}
                  {plan.id === 'titan' && <Crown className="w-5 h-5" style={{ color: plan.color }} />}
                  <h3 className="text-lg font-bold text-white">{plan.name}</h3>
                </div>
                <p className="text-xs text-white/40 mb-4">{plan.description}</p>
                <div className="flex items-baseline gap-1">
                  <span className="text-xs text-white/40">INR</span>
                  <span className="text-4xl font-bold font-data text-white">{getPrice(plan)}</span>
                  <span className="text-sm text-white/40">/{billingCycle === 'weekly' ? 'week' : 'month'}</span>
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
                className="w-full text-sm font-semibold gap-2"
                style={{
                  backgroundColor: plan.popular ? plan.color : 'transparent',
                  color: plan.popular ? '#000' : plan.color,
                  border: plan.popular ? 'none' : `1px solid ${plan.color}40`,
                }}
                onClick={() => {
                  if (user) {
                    window.open(`https://wa.me/918102126223?text=Hi! I'm interested in the Titan Trade ${plan.name} plan (INR ${getPrice(plan)}/${billingCycle === 'weekly' ? 'week' : 'month'}).`, '_blank');
                  } else {
                    navigate('/auth');
                  }
                }}
                data-testid={`plan-cta-${plan.id}`}
              >
                <svg viewBox="0 0 24 24" className="w-4 h-4 fill-current"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
                {plan.cta}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Contact Section */}
      <Card className="glass-panel border-white/10 max-w-2xl mx-auto" data-testid="contact-section">
        <CardContent className="p-6 text-center space-y-4">
          <h3 className="text-lg font-bold text-white">Ready to upgrade?</h3>
          <p className="text-xs text-white/40">Get in touch to activate your premium plan instantly</p>
          <div className="flex items-center justify-center gap-3 flex-wrap">
            <a href="https://wa.me/918102126223?text=Hi! I'm interested in Titan Trade premium plans."
              target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-2 px-5 py-3 rounded-lg bg-[#25D366]/10 border border-[#25D366]/25 text-[#25D366] text-sm font-medium hover:bg-[#25D366]/20 transition-colors"
              data-testid="contact-whatsapp-1">
              <svg viewBox="0 0 24 24" className="w-5 h-5 fill-current"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
              WhatsApp 1
            </a>
            <a href="https://wa.me/918867678750?text=Hi! I'm interested in Titan Trade premium plans."
              target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-2 px-5 py-3 rounded-lg bg-[#25D366]/10 border border-[#25D366]/25 text-[#25D366] text-sm font-medium hover:bg-[#25D366]/20 transition-colors"
              data-testid="contact-whatsapp-2">
              <svg viewBox="0 0 24 24" className="w-5 h-5 fill-current"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
              WhatsApp 2
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
