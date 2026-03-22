# SignalBeast Pro - Product Requirements Document

## Original Problem Statement
Build a complete, working advanced trading intelligence platform named "SignalBeast Pro" based on the uploaded specification document. The platform provides live data and charts for Cryptocurrency, Forex, and the full Indian market (including all indices), with AI-powered signal generation and a trading assistant chat.

## Core Requirements
- **Real-Time Data Feeds:** Live prices for Crypto (25 via CryptoCompare, refreshed every 30s), Forex (12 via yfinance), Indian (44 via yfinance) with 1-2s micro-movement ticks
- **Market Hours Awareness:** Show open/closed status for Forex (Sun 5PM ET - Fri 5PM ET) and Indian (Mon-Fri 9:15 AM - 3:30 PM IST); no fake price movements on closed markets
- **AI Features:** GPT-4o powered signal generation with live market data from cache; Beast AI Chat assistant
- **Authentication:** JWT (email/password) + Google OAuth social login
- **Professional UI:** Dark theme, glass-morphism panels, live ticker tape, TradingView charts

## Architecture
- **Backend:** FastAPI + MongoDB (motor) + yfinance + CryptoCompare + Emergent LLM
- **Frontend:** React + Tailwind CSS + shadcn/ui + lightweight-charts v5 + Recharts
- **Real-Time:** HTTP polling via useMarketStream hook (1.5s interval)
- **Background Tasks:** Price ticker loop (1s) + CryptoCompare refresh (30s) + Alert checker (every 5 ticks)
- **Market Hours:** Backend detects open/closed; _tick() only moves prices for open markets

## Data Sources
- **Crypto:** CryptoCompare (free, no key, 25 coins, 30s refresh, images, market cap, volume, OHLCV charts)
- **Forex:** yfinance (12 pairs, 5min refresh when market open)
- **Indian:** yfinance (44 assets - indices + stocks, 5min refresh when market open)
- **AI:** Emergent LLM Key (GPT-4o) for signal generation and chat

## Pages (11 total)
1. Landing Page - Hero, features, CTA
2. Auth Page - Login/Register + Google OAuth
3. Dashboard - Live ticker, market status bar, summary cards, BTC 7D chart, gainers/losers, forex panel
4. Signals - AI signal generation, confidence ring, BUY/SELL filter, live P&L tracking
5. Markets - Crypto/Forex/Indian tabs with CLOSED badges, clickable rows → chart
6. Chart Page - TradingView lightweight charts, line/candle toggle, 5 period selectors
7. Portfolio - Add/delete holdings, allocation chart, live P&L
8. Alerts - Price alert CRUD, background monitoring, triggered notifications
9. Strategy Builder - 4 templates + custom rule builder
10. Beast AI Chat - Conversational AI with session continuity
11. Settings - Profile, notifications, appearance, security

## What's Implemented (March 22, 2026)
- [x] Full platform with 11 pages
- [x] Real-time crypto via CryptoCompare (25 coins, 30s refresh, no rate limits)
- [x] Real-time forex/indian via yfinance with market hours awareness
- [x] Market status indicators (CLOSED badges, amber banners, status bar)
- [x] AI signal generation with live P&L tracking
- [x] TradingView chart integration (lightweight-charts v5)
- [x] Price alert system with background monitoring + notifications
- [x] Strategy builder with 4 templates
- [x] Portfolio management with live P&L
- [x] Beast AI Chat with session continuity
- [x] JWT + Google OAuth authentication

## Test Status (Iteration 6)
- Backend: 100% (21/21 tests passed)
- Frontend: 100% (all pages and features verified)
- CryptoCompare integration verified
- Market hours fix verified

## Future Enhancements (Backlog)
- P1: Community & social features (signal sharing, leaderboards)
- P1: Email/push notifications for triggered alerts
- P2: Gamified onboarding tour for new users
- P2: Customizable dashboard widget layout
- P2: Advanced technical indicators (RSI, MACD, Bollinger)
- P2: Strategy backtesting with historical data
- P3: Mobile-optimized responsive improvements
- P3: Multi-language support
- P3: Market calendar with economic events
