# SignalBeast Pro - Product Requirements Document

## Original Problem Statement
Build a complete, working advanced trading intelligence platform named "SignalBeast Pro". The platform provides live data and charts for Cryptocurrency, Forex, and the full Indian market, with AI-powered signal generation and a trading assistant chat.

## Data Sources (Production)
- **Crypto:** Kraken Public API (free, no key, 19 coins, 30s refresh) — real exchange data with 24h OHLCV
- **Forex:** OANDA REST API (institutional-grade, 20 pairs, 5s refresh) — real bid/ask/spread data
- **Indian:** yfinance (44 assets — indices + stocks, 5min refresh when market open)
- **AI:** Emergent LLM Key (GPT-4o) for signal generation and Beast AI Chat

## OANDA Integration
- API Key: configured in backend/.env (OANDA_API_KEY, OANDA_ACCOUNT_ID)
- Practice URL: https://api-fxpractice.oanda.com/v3
- 20 Forex pairs: EUR/USD, GBP/USD, USD/JPY, AUD/USD, USD/CHF, USD/CAD, NZD/USD, XAU/USD, XAG/USD, EUR/GBP, EUR/JPY, GBP/JPY, AUD/JPY, CAD/JPY, GBP/CHF, EUR/AUD, EUR/CHF, GBP/AUD, GBP/NZD, AUD/NZD
- Features: bid/ask spread, category badges (major/commodity/cross), OANDA candle charts

## Architecture
- **Backend:** FastAPI + MongoDB + OANDA + Kraken + yfinance + Emergent LLM
- **Frontend:** React + Tailwind CSS + shadcn/ui + lightweight-charts v5 + Recharts
- **Real-Time:** HTTP polling (1.5s frontend) + OANDA 5s refresh + Kraken 30s refresh
- **Background Tasks:** Price ticker (1s) + OANDA fetch (5s) + Kraken fetch (30s) + Alert checker (5 ticks)

## Pages (11 total)
1. Landing Page 2. Auth (JWT + Google OAuth) 3. Dashboard 4. Signals (with Trade Logic & Reason)
5. Markets (Bid/Ask/Spread for Forex) 6. Chart Page (OANDA/Kraken data) 7. Portfolio
8. Alerts 9. Strategy Builder 10. Beast AI Chat 11. Settings

## What's Implemented (March 23, 2026)
- [x] OANDA forex integration (20 pairs, institutional bid/ask/spread, 5s refresh)
- [x] Kraken crypto integration (19 coins, real exchange data, 30s refresh)
- [x] yfinance Indian market (44 assets)
- [x] TradingView charts with OANDA candles + Kraken OHLC
- [x] Enhanced signal generator with Trade Logic & Trade Reason
- [x] Market hours awareness (CLOSED badges for off-hours)
- [x] Price alerts + notifications system
- [x] Strategy builder with templates
- [x] Portfolio management with live P&L
- [x] Beast AI Chat with session continuity
- [x] 83 total tracked assets

## Test Status (Iteration 7)
- Backend: 100% (18/18 tests passed)
- Frontend: 100% (all features verified)
- OANDA integration: Verified (20 pairs, bid/ask/spread, charts)
- Kraken integration: Verified (19 pairs, OHLC charts)

## Future Enhancements (Backlog)
- P1: Community & social features (signal sharing, leaderboards)
- P1: Email/push notifications for triggered alerts
- P1: OANDA trade execution (BUY/SELL from SignalBeast)
- P2: Gamified onboarding, customizable dashboard
- P2: Advanced technical indicators (RSI, MACD, Bollinger)
- P2: Strategy backtesting with historical data
- P3: Mobile improvements, multi-language support
