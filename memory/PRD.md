# Titan Trade - Product Requirements Document

## Overview
AI-powered trading intelligence platform for Crypto, Forex & Indian Markets.
Rebranded from "SignalBeast Pro" to "Titan Trade" on Mar 24, 2026.

## Core Architecture
- **Backend:** FastAPI + MongoDB (motor) + OANDA API + Kraken API + yfinance
- **Frontend:** React + Tailwind CSS + shadcn/ui + lightweight-charts
- **AI:** OpenAI GPT-4o via Emergent LLM Key (branded as "Titan AI")
- **Auth:** JWT (email/password) + Google OAuth2
- **Email:** Gmail SMTP (contact.developersingh@gmail.com)

## Admin Access
- **Email:** contact.developersingh@gmail.com
- **Password:** admin123
- **Route:** `/admin` (hidden from sidebar, URL-only access)

## Implemented Features

### Full Rebrand (Completed: Mar 24, 2026)
- SignalBeast Pro → Titan Trade (all pages, SEO, metadata)
- Beast AI → Titan AI (chat, sidebar, backend prompts)
- Custom Titan Trade splash screen (loading page)
- Emergent badge hidden via CSS + inline styles
- localStorage token key: titan_trade_token

### Plan Management + Email (Completed: Mar 24, 2026)
- Admin assigns plans (free/basic/pro/titan) by email
- Billing cycles: weekly (7d) or monthly (30d)
- Custom duration in days or hours
- Auto-expiry, revoke capability
- Professional HTML email sent on plan assignment via Gmail SMTP
- Users check plan via GET /api/user/plan

### Pricing (Updated: Mar 24, 2026)
- Weekly/Monthly toggle
- Basic: INR 499/week, INR 1,499/month
- Pro: INR 999/week, INR 3,499/month
- Titan: INR 1,999/week, INR 6,999/month
- Contact: +91 8102126223, +91 8867678750

### Settings Page
- Logout button added to Settings page

### Advanced Signal Generation
- Multi-timeframe analysis (3+ TFs)
- 10 trading strategies, SL/TP1/TP2/TP3, holding duration, confluence scoring

### Platform Features
- Trade Journal (CRUD + emotions + star ratings + P&L)
- Admin Panel (hidden, stats/users/plans/signals/system tabs)
- Professional UI with animations, glassmorphism, SEO

## Key API Endpoints
- Plan Management: POST /api/admin/plans/assign, GET /api/admin/plans, DELETE /api/admin/plans/{user_id}, GET /api/user/plan
- Signals: GET /api/signals/strategies, POST /api/signals/generate
- Journal: GET/POST/PUT/DELETE /api/journal
- Admin: GET /api/admin/stats|users|system|signals

## Database Collections
users, signals, trade_journal, alerts, notifications, chat_history, portfolio, watchlist, user_plans

## Credentials
- Admin: contact.developersingh@gmail.com / admin123
- Gmail SMTP: contact.developersingh@gmail.com / App Password in .env
- OANDA API: in backend/.env

## Backlog
- P1: OANDA WebSocket streaming (replace polling)
- P1: One-click trade execution via OANDA
- P2: Plan-based feature gating (restrict features by plan tier)
- P2: Advanced SEO (schema markup, sitemap)
- P3: Community features, leaderboards, mobile optimization
- Note: Google OAuth page shows "Signal Beast Pro" / "Emergent" — this is platform-level (auth.emergentagent.com) and cannot be changed from app code. URL subdomain is also platform-level.
