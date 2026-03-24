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
- SignalBeast Pro -> Titan Trade (all pages, SEO, metadata)
- Beast AI -> Titan AI (chat, sidebar, backend prompts)
- Custom splash screen, Emergent badge hidden
- localStorage token key: titan_trade_token

### Plan Management + Email (Completed: Mar 24, 2026)
- Admin assigns plans (free/basic/pro/titan) by email
- Billing cycles: weekly (7d) or monthly (30d)
- Custom duration in days or hours
- Auto-expiry, revoke capability
- Professional HTML email sent via Gmail SMTP

### Plan-Based Feature Gating (Completed: Mar 25, 2026)
- Free: 3 signals/day, 10 chat msgs/day, no multi-TF, 5 alerts
- Basic: 5 signals/day, 50 chat msgs/day, 4 strategies, 10 alerts
- Pro: 25 signals/day, 100 chat msgs/day, multi-TF, all strategies, 50 alerts
- Titan: Unlimited signals, unlimited chat, multi-TF, trade execution, unlimited alerts
- Plan usage badge shown on Signals page and enforced on backend endpoints

### OANDA Trade Execution (Completed: Mar 25, 2026)
- Place MARKET/LIMIT/STOP orders via OANDA REST API
- View open positions with unrealized P&L
- Close positions per instrument
- Account summary (balance, NAV, margin)
- Trade execution history tracking
- Requires Titan plan
- Practice account: $100,000 USD

### Community & Leaderboard (Completed: Mar 25, 2026)
- Leaderboard page ranking traders by total P&L
- Tier system: bronze, silver, gold, platinum, diamond
- Badge system: First Trade, Active Trader, Veteran Trader, Winning Streak, 1K Club, 10K Club, Signal Hunter, Sharpshooter
- Community stats: total traders, signals generated, win rate
- Personal stats with rank and earned badges

### SEO Implementation (Completed: Mar 25, 2026)
- XML Sitemap at /api/sitemap.xml
- robots.txt in frontend public
- JSON-LD schema markup (SoftwareApplication)
- Canonical URL, meta tags, Open Graph, Twitter Cards

### Pricing (Updated: Mar 24, 2026)
- Weekly/Monthly toggle
- Basic: INR 499/week, INR 1,499/month
- Pro: INR 999/week, INR 3,499/month
- Titan: INR 1,999/week, INR 6,999/month

### Advanced Signal Generation
- Multi-timeframe analysis (3+ TFs)
- 10 trading strategies, SL/TP1/TP2/TP3, holding duration, confluence scoring
- Plan gating on strategies and multi-TF

### Platform Features
- Trade Journal (CRUD + emotions + star ratings + P&L)
- Admin Panel (hidden, stats/users/plans/signals/system tabs)
- Mobile-first responsive SaaS UI with dark theme
- Logout, WhatsApp CTAs on pricing, splash screen

## Key API Endpoints
- Plan Management: POST /api/admin/plans/assign, GET /api/admin/plans, DELETE /api/admin/plans/{user_id}, GET /api/user/plan, GET /api/user/plan-usage
- Signals: GET /api/signals/strategies, POST /api/signals/generate, GET /api/signals
- Journal: GET/POST/PUT/DELETE /api/journal, GET /api/journal/stats
- Admin: GET /api/admin/stats|users|system|signals
- Trade: POST /api/trade/order, GET /api/trade/positions, GET /api/trade/account, POST /api/trade/close/{instrument}, GET /api/trade/history
- Community: GET /api/community/leaderboard, GET /api/community/stats, GET /api/community/my-stats
- SEO: GET /api/sitemap.xml

## Database Collections
users, signals, trade_journal, alerts, notifications, chat_history, portfolio, watchlist, user_plans, trade_executions, user_sessions

## Code Architecture
```
/app/backend/
  server.py          # Main FastAPI app with all routes
  models/schemas.py  # Extracted Pydantic models
  services/email_service.py  # Email sending service
  routes/             # Future route extraction
  tests/              # pytest test files

/app/frontend/src/
  App.js              # Router
  context/AuthContext.js
  components/AppLayout.js
  pages/
    DashboardPage.js, SignalsPage.js, MarketsPage.js,
    PortfolioPage.js, AlertsPage.js, ChartPage.js,
    StrategyPage.js, ChatPage.js, JournalPage.js,
    AdminPage.js, PricingPage.js, SettingsPage.js,
    LeaderboardPage.js, TradePage.js, LandingPage.js
```

## Credentials
- Admin: contact.developersingh@gmail.com / admin123
- Gmail SMTP: App Password in backend/.env
- OANDA API: in backend/.env

## Known Platform Limitations
- Google OAuth consent screen shows "Signal Beast Pro" / "Emergent" - platform-level, cannot change from app code
- Preview URL subdomain is platform-level, cannot change
