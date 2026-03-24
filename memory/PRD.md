# SignalBeast Pro - Product Requirements Document

## Overview
AI-powered trading intelligence platform for Crypto, Forex & Indian Markets with institutional-grade signal generation.

## Core Architecture
- **Backend:** FastAPI + MongoDB (motor) + OANDA API + Kraken API + yfinance
- **Frontend:** React + Tailwind CSS + shadcn/ui + lightweight-charts
- **AI:** OpenAI GPT-4o via Emergent LLM Key
- **Auth:** JWT (email/password) + Google OAuth2

## Data Sources
- **Forex (20 pairs):** OANDA API - 5s polling, bid/ask/spread
- **Crypto (19 pairs):** Kraken API - 30s polling
- **Indian (44 assets):** yfinance - 5min polling

## Implemented Features

### Phase 1 - Advanced Signal Generation (Completed: Mar 24, 2026)
- Multi-timeframe analysis (user selects 3+ TFs: 1m, 5m, 15m, 1H, 4H, 1D, 1W)
- 10 trading strategies: Auto, EMA Crossover, RSI Divergence, Smart Money (SMC), VWAP, MACD, Bollinger Bands, Ichimoku Cloud, Fibonacci, Price Action
- SL, TP1, TP2, TP3 levels with every signal
- Holding duration estimates based on profit targets
- Confluence scoring (1-6 factors)
- Enhanced trade logic, trade reason, invalidation level, higher TF bias
- Risk:Reward ratio calculation

### Phase 2 - Platform Features (Completed: Mar 24, 2026)
- **Trade Journal:** Full CRUD, P&L tracking, emotion tags (calm/confident/fear/greed/fomo/revenge), star ratings (1-5), entry reasoning, post-trade reflection, lesson learned
- **Admin Panel:** Stats dashboard, user management (CRUD), signal monitoring, system health/data feed status. Admin: contact.developersingh@gmail.com
- **Pricing Page:** 3 plans (Basic INR 999, Pro INR 2,499, Beast Mode INR 4,999), monthly/yearly toggle, phone contacts (8102126223, 8867678750), WhatsApp integration

### Phase 3 - UI/UX Overhaul (Completed: Mar 24, 2026)
- Professional institutional finance dark theme
- Redesigned landing page with markets showcase, features grid, stats bar
- Typography: Manrope (headings), Sora (body), JetBrains Mono (data/numbers)
- CSS animations: page-enter, stagger-item, glow-card, tracing-beam, neon-text, confidence-ring
- Glassmorphism effects, noise overlay, neon accents
- SEO meta tags (og:title, description, keywords, twitter:card)
- Branding removal (CSS-based)

### Previously Completed
- JWT + Google OAuth authentication
- Real-time market data streaming (polling)
- Market hours awareness (open/closed status)
- Price alert system with notifications
- NotificationBell component
- TradingView-style charts (lightweight-charts)
- Portfolio page with live valuations
- Strategy Builder page
- Beast AI Chat

## Key API Endpoints
- `GET /api/signals/strategies` - 10 trading strategies
- `POST /api/signals/generate` - Multi-TF AI signal generation
- `GET /api/journal` / `POST /api/journal` / `PUT /api/journal/{id}` / `DELETE /api/journal/{id}` - Trade journal CRUD
- `GET /api/journal/stats` - Win rate, P&L, emotion breakdown
- `GET /api/admin/stats` / `GET /api/admin/users` / `GET /api/admin/system` - Admin endpoints
- `GET /api/market/live` - Real-time price data
- `GET /api/chart/{market}/{asset_id}` - Candlestick data

## Database Collections
- users, signals, trade_journal, alerts, notifications, chat_history, portfolio, watchlist

## Test Credentials
- Test user: test@test.com / test123
- Admin: contact.developersingh@gmail.com / admin123

## Backlog (P1-P3)
- P1: OANDA WebSocket streaming (replace 5s polling with real-time ticks)
- P1: One-click trade execution via OANDA order API
- P2: Advanced SEO (schema markup, sitemap, keyword optimization)
- P2: Community features & leaderboards
- P3: Mobile app optimization
- P3: Multi-language support
