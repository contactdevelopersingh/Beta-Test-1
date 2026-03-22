# SignalBeast Pro - PRD

## Original Problem Statement
Build SignalBeast Pro - an advanced trading intelligence platform providing retail traders with institutional-grade tools, AI-powered signals, and market data across Crypto, Forex, and Indian markets.

## Architecture
- **Frontend**: React 19, Tailwind CSS, shadcn/ui, Recharts
- **Backend**: FastAPI (Python), MongoDB (motor async)
- **AI**: OpenAI GPT-5.2 via emergentintegrations (Emergent LLM Key)
- **Market Data**: CoinGecko API (live crypto), Mock data (forex, Indian markets)
- **Auth**: JWT (email/password) + Emergent Google OAuth

## User Personas
1. **Crypto Trader** - Needs live crypto prices, AI signals, portfolio tracking
2. **Forex Trader** - Needs currency pair data, signal generation, risk analysis
3. **Indian Market Investor** - Needs NSE/BSE data, stock signals, portfolio P&L

## Core Requirements (Static)
- Real-time market data across 3 markets (Crypto, Forex, Indian)
- AI-powered trading signal generation with confidence scores
- Portfolio tracking with P&L and allocation charts
- Beast AI Chat assistant for trading queries
- User authentication (JWT + Google OAuth)
- Watchlist management
- Professional dark theme trading terminal UI

## What's Been Implemented (March 22, 2026)
### Pages
- [x] Landing Page - Hero section, features, stats, CTA
- [x] Auth Page - Login/Register with JWT + Google OAuth
- [x] Dashboard - Portfolio summary, BTC chart, top coins, sentiment gauge, latest signals
- [x] Signals Page - AI signal generator (crypto/forex/indian), signal cards with confidence rings
- [x] Markets Page - Crypto/Forex/Indian tabs with LIVE data tables, search, sparklines
- [x] Portfolio Page - Holdings CRUD, allocation pie chart, summary cards
- [x] Beast AI Chat - Conversational AI trading assistant
- [x] Settings Page - Profile, notifications, appearance, security

### Backend APIs
- [x] Auth: register, login, session (Google OAuth), me, logout
- [x] Market Data: crypto/top (CoinGecko LIVE), forex (Yahoo Finance LIVE), indian (Yahoo Finance LIVE with 15 indices + 29 stocks), sentiment
- [x] Signals: list, generate (AI-powered with diverse confidence 40-98% and varied grades)
- [x] Portfolio: CRUD holdings, summary
- [x] Watchlist: CRUD items
- [x] Chat: send message (AI), history

### Live Data Sources (Updated March 22, 2026)
- Crypto: CoinGecko API (live real-time prices, charts, market cap, sentiment)
- Forex: Yahoo Finance via yfinance (EUR/USD, GBP/USD, USD/JPY, AUD/USD, Gold, Silver, + 6 more pairs)
- Indian Market: Yahoo Finance via yfinance (NIFTY 50, SENSEX, Bank Nifty, NIFTY IT, Pharma, Auto, FMCG, Metal, Energy, Realty, Infra, India VIX, PSU Bank, Financial Services, Media, MNC, Commodities + 29 major stocks)

### Design
- Dark theme (#050505 bg, #6366F1 primary, #00FF94 buy, #FF2E2E sell)
- Glassmorphism panels, neon accents, micro-animations
- Fonts: Manrope (headings), Sora (body), JetBrains Mono (data)
- Responsive design (mobile + desktop)

## Test Results
- Backend: 95% pass rate (19/20 tests)
- Frontend: 100% pass rate
- Beast AI Chat budget handling added

## Prioritized Backlog
### P0 (Critical)
- [ ] Add real-time WebSocket price updates
- [ ] Implement actual Forex API integration (currently mocked)
- [ ] Add Indian market real API (currently mocked)

### P1 (Important)
- [ ] Signal history with performance tracking
- [ ] Portfolio P&L with current market prices
- [ ] TradingView chart integration for detailed charts
- [ ] Alert system (price alerts, signal notifications)

### P2 (Nice to have)
- [ ] Strategy builder (no-code)
- [ ] Social trading / signal marketplace
- [ ] Advanced technical indicators
- [ ] Backtesting engine
- [ ] Mobile responsive improvements
- [ ] Email/push notifications

## Next Tasks
1. Integrate real Forex API (Alpha Vantage or similar)
2. Add WebSocket for real-time price streaming
3. Implement portfolio P&L calculation with live prices
4. Add TradingView widget for advanced charting
5. Build alert/notification system
