# Titan Trade - Changelog

## Mar 25, 2026 - Massive Strategy & Feature Expansion (Fork Job 2)
### Expanded Trading Strategies
- 29 Forex Strategies: ICT, SMC, MSNR, CRT, FVG+OB, BOS, CHoCH, Liquidity Grab, Inducement, Premium/Discount Zones, Kill Zones, SMT Divergence, Breaker Block, Mitigation Block, Supply & Demand, S/R Flip, Trendline Liquidity, EQH/EQL, Asian+London, Session Bias + universal strategies
- 29 Crypto Strategies: On-Chain, Whale Activity, Order Book, Liquidity Heatmaps, Funding Rate, Open Interest, Long/Short Ratio, Liquidation Zones, Perp Imbalance, Market Maker, Breakout+Fakeout, Range Scalping, Trend Following, Volume Profile, VWAP Bounce, Momentum Scalping, News Volatility, Altcoin Rotation, BTC Dominance + universal
- Market-specific strategy filtering via ?market= parameter
- Combo Strategy Mode: Select multiple strategies to combine

### Extended Timeframes
- Added: 1m, 3m, 10m, 30m, 2H, 3H, 3D (total 13 timeframes)
- Free user limit: max 2 timeframes

### Manual Risk:Reward Ratio
- New input in Advanced Options for custom R:R (e.g., 1:2.5)
- Passed to AI prompt for strict enforcement

### Two-Factor Authentication (2FA)
- TOTP-based using pyotp + qrcode
- Endpoints: setup, verify, disable, status
- Full UI flow in Settings with QR code display

### Custom Strategy Builder
- Replaced old Strategy page with full builder
- Create/save/delete custom combo strategies
- Select from all available strategies per market

### Signal-to-Trade Push
- "Execute as Trade" button on forex signals
- POST /api/signals/{id}/execute pushes to OANDA
- Maps signal direction, SL, TP to order

### USD-Based Trading
- Units/USD toggle on Trade page
- Backend converts USD to units based on live price

### Auth Page Rebranding
- "LOG IN TO Titan Trade" branding

## Mar 25, 2026 - Feature Expansion (Fork Job 1)
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
