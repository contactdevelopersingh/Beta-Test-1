# Titan Trade - Changelog

## Mar 25, 2026 - Feature Expansion (Fork Job)
### Plan-Based Feature Gating
- Implemented PLAN_LIMITS system: free/basic/pro/titan tiers
- Added daily usage tracking for signals and chat messages
- Backend gating on signal generation, chat, multi-timeframe, and strategy selection
- Added `/api/user/plan-usage` endpoint returning limits + current usage
- Updated `/api/user/plan` to return limits and features
- Frontend: Plan usage badge on Signals page showing signals used/remaining

### OANDA Trade Execution
- `POST /api/trade/order` - Place MARKET/LIMIT/STOP orders
- `GET /api/trade/positions` - View open positions with unrealized P&L
- `GET /api/trade/account` - OANDA account summary (balance, NAV, margin)
- `POST /api/trade/close/{instrument}` - Close positions
- `GET /api/trade/history` - User's trade execution history
- New TradePage.js with order form, account summary, positions view
- Gated to Titan plan only

### Community & Leaderboard
- `GET /api/community/leaderboard` - Top traders by P&L (aggregation pipeline)
- `GET /api/community/stats` - Community-wide statistics
- `GET /api/community/my-stats` - Personal stats with badges and rank
- Tier system: bronze/silver/gold/platinum/diamond
- 8 achievement badges based on trading milestones
- New LeaderboardPage.js with stats, badges, and rankings

### SEO
- XML Sitemap endpoint at /api/sitemap.xml
- robots.txt in frontend public/
- JSON-LD schema markup (SoftwareApplication) in index.html
- Canonical URL added

### Backend Modularization (Partial)
- Created /backend/models/schemas.py with extracted Pydantic models
- Created /backend/services/email_service.py with email logic
- Module structure: routes/, models/, services/ directories ready for future extraction

### Navigation Updates
- Added Trade and Leaderboard links to sidebar navigation
- New routes: /trade, /leaderboard

## Mar 24, 2026 - Initial Build & Rebrand
- Full rebrand: SignalBeast Pro -> Titan Trade
- Advanced signal generation (multi-TF, 10 strategies, SL/TP)
- Trade Journal, Admin Panel, Pricing Page
- Two UI/UX overhaul iterations (finance -> minimal SaaS)
- Gmail SMTP email notifications on plan assignment
- Mobile optimization, splash screen, logout functionality
- WhatsApp CTA buttons on pricing page
