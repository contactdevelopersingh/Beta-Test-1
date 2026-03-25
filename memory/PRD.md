# Titan Trade - Product Requirements Document

## Overview
AI-powered trading intelligence platform for Crypto, Forex & Indian Markets.
Rebranded from "SignalBeast Pro" to "Titan Trade" on Mar 24, 2026.

## Core Architecture
- **Backend:** FastAPI + MongoDB (motor) + OANDA API + Kraken API + yfinance
- **Frontend:** React + Tailwind CSS + shadcn/ui + lightweight-charts
- **AI:** OpenAI GPT-4o via Emergent LLM Key (branded as "Titan AI")
- **Auth:** JWT (email/password) + Google OAuth2 + TOTP 2FA
- **Email:** Gmail SMTP (contact.developersingh@gmail.com)

## Admin Access
- **Admin 1:** contact.developersingh@gmail.com / admin123
- **Admin 2:** infinityanirudra@gmail.com / admin456
- **Route:** `/admin` (hidden from sidebar)

## Implemented Features

### Trading Strategies (Completed: Mar 25, 2026)
**29 Forex Strategies:** ICT, SMC, MSNR, CRT, FVG+OB, BOS, CHoCH, Liquidity Grab, Inducement, Premium/Discount Zones, Kill Zones, SMT Divergence, Breaker Block, Mitigation Block, Supply & Demand, S/R Flip, Trendline Liquidity, EQH/EQL, Asian Range + London Breakout, Session Bias, EMA Crossover, RSI Divergence, MACD, Bollinger, Ichimoku, Fibonacci, Price Action, VWAP + Auto

**29 Crypto Strategies:** On-Chain Analysis, Whale Activity, Order Book, Liquidity Heatmaps, Funding Rate, Open Interest, Long/Short Ratio, Liquidation Zones, Perp Futures Imbalance, Market Maker, Breakout+Fakeout, Range Scalping, Trend Following, Volume Profile, VWAP Bounce, RSI Divergence, Momentum Scalping, News Volatility, Altcoin Rotation, BTC Dominance + shared strategies

**Combo Mode:** Users can select multiple strategies to combine (e.g., SMC + ICT + CRT)

### Extended Timeframes (Completed: Mar 25, 2026)
13 timeframes: 1m, 3m, 5m, 10m, 15m, 30m, 1H, 2H, 3H, 4H, 1D, 3D, 1W
- Free users: max 2 timeframes
- Pro/Titan: unlimited

### Manual Risk:Reward Ratio (Completed: Mar 25, 2026)
- Users can specify custom R:R (e.g., 1:2.5) in signal generation

### Two-Factor Authentication (Completed: Mar 25, 2026)
- TOTP-based 2FA with QR code setup
- Google Authenticator / Authy compatible
- Enable/Disable from Settings page

### Custom Strategy Builder (Completed: Mar 25, 2026)
- Create/save custom combo strategies
- Select multiple techniques to combine
- Filter by market type
- Full CRUD via /strategies/custom

### Signal-to-Trade Push (Completed: Mar 25, 2026)
- "Execute as Trade" button on forex signals
- Pushes signal parameters directly to OANDA
- Requires Titan plan

### USD-Based Trading (Completed: Mar 25, 2026)
- Trade by units OR USD amount
- Toggle between sizing modes on Trade page

### Auth Page Rebranding (Completed: Mar 25, 2026)
- "LOG IN TO Titan Trade" branding on login page

### Plan-Based Feature Gating (Completed: Mar 25, 2026)
- Free: 3 signals/day, 10 chat, 2 TF max, 5 alerts, basic strategies
- Basic: 5 signals/day, 50 chat, 4 strategies, 10 alerts
- Pro: 25 signals/day, 100 chat, multi-TF, all strategies, 50 alerts
- Titan: Unlimited, trade execution, all features

### OANDA Trade Execution (Completed: Mar 25, 2026)
- MARKET/LIMIT/STOP orders, positions, account summary
- Practice account: $100K USD

### Community & Leaderboard (Completed: Mar 25, 2026)
- Leaderboard, badges, tiers, community stats

### Full Rebrand, Email, SEO, UI/UX
- All completed in previous sessions

## Key API Endpoints
- Strategies: GET /api/signals/strategies?market=forex|crypto|indian
- Custom: GET/POST/DELETE /api/strategies/custom
- 2FA: POST /api/auth/2fa/setup|verify|disable, GET /api/auth/2fa/status
- Signal Execute: POST /api/signals/{id}/execute
- Trade: POST /api/trade/order (units + usd_amount)
- Plan: GET /api/user/plan-usage

## Database Collections
users, signals, trade_journal, alerts, notifications, chat_history, portfolio, watchlist, user_plans, trade_executions, user_sessions, custom_strategies

## Known Platform Limitations
- Google OAuth consent screen branding is platform-level (auth.emergentagent.com)
- Preview URL subdomain is platform-level
