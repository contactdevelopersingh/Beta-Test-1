# Titan Trade - Product Requirements Document

## Overview
AI-powered trading intelligence platform for Crypto, Forex & Indian Markets (formerly SignalBeast Pro, rebranded Mar 24, 2026).

## Core Architecture
- **Backend:** FastAPI + MongoDB (motor) + OANDA API + Kraken API + yfinance
- **Frontend:** React + Tailwind CSS + shadcn/ui + lightweight-charts
- **AI:** OpenAI GPT-4o via Emergent LLM Key (branded as "Titan AI")
- **Auth:** JWT (email/password) + Google OAuth2

## Admin Access
- **Email:** contact.developersingh@gmail.com
- **Password:** admin123
- **Route:** `/admin` (hidden from sidebar, accessible via URL only)

## Implemented Features

### Rebrand: SignalBeast Pro → Titan Trade (Completed: Mar 24, 2026)
- All UI references updated: landing page, auth, sidebar, chat, pricing, settings, footer, SEO
- "Beast AI" → "Titan AI" throughout
- Emergent badge hidden via CSS
- localStorage key renamed to titan_trade_token

### Plan Management System (Completed: Mar 24, 2026)
- Admin can assign plans (free/basic/pro/titan) to users by email
- Billing cycles: weekly (7 days) or monthly (30 days)
- Custom duration in days or hours
- Auto-expiry when plan duration ends
- Admin can view/revoke user plans
- Users can check their own plan via GET /api/user/plan

### Pricing (Completed: Mar 24, 2026)
- Weekly/Monthly toggle
- Basic: INR 499/week, INR 1,499/month
- Pro: INR 999/week, INR 3,499/month
- Titan: INR 1,999/week, INR 6,999/month
- Contact: +91 8102126223, +91 8867678750

### Advanced Signal Generation (Completed: Mar 24, 2026)
- Multi-timeframe analysis (3+ TFs: 1m, 5m, 15m, 1H, 4H, 1D, 1W)
- 10 trading strategies
- SL, TP1, TP2, TP3 levels
- Holding duration estimates, confluence scoring, risk:reward

### Platform Features (Completed: Mar 24, 2026)
- Trade Journal (CRUD + emotions + star ratings + P&L)
- Admin Panel (hidden, stats/users/plans/signals/system tabs)
- Professional UI with animations, glassmorphism, SEO

### Previously Completed
- JWT + Google OAuth, real-time data, market hours, price alerts, notifications
- TradingView charts, portfolio, strategy builder, Titan AI Chat

## Key API Endpoints
- `POST /api/admin/plans/assign` - Assign plan to user by email
- `GET /api/admin/plans` - List all plans (admin)
- `DELETE /api/admin/plans/{user_id}` - Revoke plan (admin)
- `GET /api/user/plan` - Get current user's plan
- `GET /api/signals/strategies` - 10 trading strategies
- `POST /api/signals/generate` - Multi-TF AI signal generation
- `GET /api/journal` + CRUD - Trade journal
- `GET /api/admin/stats|users|system` - Admin endpoints

## Database Collections
- users, signals, trade_journal, alerts, notifications, chat_history, portfolio, watchlist, user_plans

## Backlog
- P1: OANDA WebSocket streaming (replace polling)
- P1: One-click trade execution via OANDA
- P2: Plan-based feature gating (restrict features by plan)
- P2: Advanced SEO (schema markup, sitemap)
- P3: Community features, leaderboards, mobile optimization
