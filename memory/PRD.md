# SignalBeast Pro - Product Requirements Document

## Original Problem Statement
Build a complete, working advanced trading intelligence platform named "SignalBeast Pro" based on the uploaded specification document. The platform provides live data and charts for Cryptocurrency, Forex, and the full Indian market (including all indices), with AI-powered signal generation and a trading assistant chat.

## Core Requirements
- **Real-Time Data Feeds:** Live prices for Crypto (25), Forex (12), Indian (44) assets refreshing every 1-2 seconds
- **Market Hours Awareness:** Show open/closed status for Forex (Sun 5PM ET - Fri 5PM ET) and Indian (Mon-Fri 9:15 AM - 3:30 PM IST); no fake price movements on closed markets
- **AI Features:** GPT-4o powered signal generation with confidence scores, grades, market analysis; Beast AI Chat assistant
- **Authentication:** JWT (email/password) + Google OAuth social login
- **Professional UI:** Dark theme, glass-morphism panels, live ticker tape, TradingView charts

## Architecture
- **Backend:** FastAPI + MongoDB (motor) + yfinance + CoinGecko + Emergent LLM
- **Frontend:** React + Tailwind CSS + shadcn/ui + lightweight-charts v5 + Recharts
- **Real-Time:** HTTP polling via useMarketStream hook (1.5s interval)
- **Background Tasks:** Price ticker loop (1s) + Alert checker (every 5 ticks)
- **Market Hours:** Backend detects open/closed status; _tick() only moves prices for open markets

## Pages (10 total)
1. Landing Page - Hero, features, CTA
2. Auth Page - Login/Register tabs + Google OAuth
3. Dashboard - Live ticker tape, market status bar, summary cards, BTC chart, gainers/losers, top crypto, forex panel
4. Signals - AI signal generation, confidence ring, BUY/SELL filter, live P&L tracking
5. Markets - Crypto/Forex/Indian tabs with CLOSED badges, search, clickable rows → chart
6. Portfolio - Add/delete holdings, allocation chart, live P&L
7. Alerts - Create/manage price alerts, active/triggered status, monitoring indicator
8. Chart Page - TradingView lightweight charts, line/candle toggle, period selector (1D/7D/1M/3M/1Y)
9. Strategy Builder - Quick templates, rule builder (IF conditions), save/delete
10. Beast AI Chat - Conversational AI with session continuity
11. Settings - Profile, notifications, appearance, security

## Key API Endpoints
- POST /api/auth/register, /api/auth/login, GET /api/auth/me
- GET /api/market/live (includes market_status), /api/market/chart/:type/:id
- POST /api/signals/generate, GET /api/signals
- GET/POST/DELETE /api/alerts, /api/notifications, /api/watchlist, /api/portfolio

## What's Implemented (March 22, 2026)
- [x] Full MVP with 10 pages
- [x] Real-time price streaming (81 assets, 1-2s refresh)
- [x] Market hours awareness - closed markets show static prices with CLOSED badges
- [x] AI signal generation with performance tracking (live P&L, TP/SL hit indicators)
- [x] TradingView chart integration (lightweight-charts v5, line/candle, 5 periods)
- [x] Price alert system with background monitoring + notifications
- [x] Notification bell with unread count and dropdown
- [x] Strategy builder with 4 templates and custom rule engine
- [x] Portfolio management with live P&L
- [x] Beast AI Chat with session continuity
- [x] JWT + Google OAuth authentication
- [x] CoinGecko rate limit handling with retry backoff

## Test Status (Iteration 5)
- Backend: 100% (14/14 market hours tests + 31/31 feature tests)
- Frontend: 100% (all pages and features verified)
- Market hours fix: Verified forex/indian prices stable on Sunday

## Future Enhancements (Backlog)
- P1: Community & social features (signal sharing, leaderboards)
- P1: Email/push notifications for triggered alerts
- P2: Gamified onboarding tour for new users
- P2: Customizable dashboard widget layout
- P2: Advanced technical indicators (RSI, MACD, Bollinger)
- P2: Strategy backtesting with historical data
- P3: Mobile-optimized responsive improvements
- P3: Multi-language support
