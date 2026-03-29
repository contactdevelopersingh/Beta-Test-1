# Titan Trade - Changelog

## Mar 29, 2026 - Indian Market Option Chain + Full F&O (Fork Job 10)
### Live Option Chain (/option-chain)
- Black-Scholes option pricing engine with live spot prices from OANDA/yfinance
- 49 F&O stocks + 4 indices (NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY)
- Full chain table: CE/PE LTP, OI, Volume, IV, Greeks (Delta/Gamma/Theta/Vega)
- PCR, Max Pain, multiple expiry dates, ATM highlighting, ITM/OTM coloring
- Lot sizes for all F&O instruments
- Note: NSE blocks cloud IPs, so prices are Black-Scholes estimated

## Mar 29, 2026 - MASTER TRADING PROMPT Integration (Fork Job 8)
### Signal Engine Upgrade (60-70% of 150KB+ trading knowledge integrated)
- 10-step signal generation framework: Market Regime → MTF Analysis → Strategy → Indicators → Candlestick → Market Structure → Confluence → Risk → Scenarios → Quality
- Market Regime Detection: ADX-based (STRONG_TREND/MODERATE/RANGING/VOLATILE)
- Complete indicator analysis with actual values: RSI, MACD, EMA alignment, Bollinger state, ADX strength, Volume
- Candlestick pattern recognition rules (Single/Double/Triple patterns)
- Market Structure (SMC): BOS, CHoCH, Order Blocks, FVG, Liquidity, Premium/Discount
- Confluence Scoring: 1 signal=50% → 5+ signals=85%+ probability mapping
- Scenario Analysis: Bull/Base/Bear cases with probability %
- Risk Management: Position sizing formula, ATR-based SL, 40/30/30% TP exit strategy
- New signal fields: market_regime, indicators_used (object), candlestick_pattern, chart_pattern, scenario_bull/base/bear, position_sizing_note
- Frontend: Indicators panel, scenario cards (green/grey/red), market regime badge, all in expanded signal view

## Mar 26, 2026 - Indian Stock Analysis Module (Fork Job 7)
### Stock Analysis Page (/stock-analysis)
- Deep fundamental analysis for 40+ Indian stocks (NIFTY 50 components)
- Valuation metrics: P/E, P/B, EV/EBITDA, Price/Sales, PEG, EPS, Book Value
- Profitability: ROE, ROA, OPM, NPM, Dividend Yield, Revenue/Earnings Growth
- Financial Health: Debt/Equity, Current Ratio, FCF, Total Debt, Total Cash
- Quarterly Results: Last 6-8 quarters with sortable table
- Annual P&L: 5-10 years with all line items
- Balance Sheet: 4-10 years with assets/liabilities breakdown
- Cash Flow: 5-10 years with CFO/CFI/CFF
- Shareholding Pattern: Promoters/FII/DII/Public with donut chart + progress bars
- Peer Comparison: Sector peers with color-coded comparison table
- Auto Pros & Cons: AI-generated green/red highlights based on metrics
- Analyst Recommendations: Target prices, buy/sell consensus
- Data source: yfinance (live, 5min cache)

### Stock Screener (/screener)
- 8 configurable filters: P/E, ROE, D/E, Market Cap, Dividend Yield, OPM etc.
- 7 pre-built presets: Warren Buffett, Benjamin Graham, Peter Lynch, Dividend Aristocrats, Debt Free, High Promoter, Value Picks
- Sortable results table with color-coded metrics
- Click any result to open full analysis

## Mar 26, 2026 - TradingView API Integration (Fork Job 6)
### TradingView Microservice
- Node.js service at /app/backend/tv_service/ (port 8099, supervisor-managed)
- Uses @mathieuc/tradingview library to get REAL computed indicator values
- 56 symbols mapped (crypto, forex, Indian stocks)
- GET /ta/{assetId} returns: oscillators, moving averages, overall rating per timeframe (1m-1M)
- Summary: bias (Bullish/Bearish/Neutral), confluence count, label
- 30-second cache to avoid over-requesting

### Dual-Source Signal Generation
- AI now receives BOTH: OANDA/Kraken/yfinance live data + TradingView computed analysis
- TradingView ratings injected into prompt: "15m: Strong Sell(-0.89), 1H: Sell(-0.45)..."
- AI instructed: Align with TV consensus when confidence high, explain divergence if sources disagree
- New signal fields: technical_summary (RSI=XX, MACD=state), risk_level (LOW/MEDIUM/HIGH), session_note
- Target: Significantly improved signal accuracy by combining institutional data + TradingView indicators

## Mar 26, 2026 - TP/SL Locking, Trading Modes, Signal Fixes (Fork Job 5)
### TP/SL Auto-Locking System
- TP1 locks when hit, then TP2 can lock, then TP3 (sequential)
- SL locks when hit, signal auto-closes as "stopped_out"
- All TPs hit → signal status "all_tp_hit"
- Locked TPs show green highlight + lock icon + "LOCKED" text
- SL hit shows red highlight + lock icon + "STOPPED OUT"
- Notifications sent on signal close (TP/SL hit)
- check_signal_tp_sl() runs every 5 ticks in ticker loop

### Configurable TP Count
- User selects 1, 2, or 3 take-profit levels
- With 1 TP: signal closes after TP1 hit
- With 2 TPs: closes after TP2 hit
- Hidden TP columns for unused levels

### Trading Modes
- Scalping: Ultra-short (1-30min), tight SL/TP
- Day Trading: Intraday (1-8 hours), moderate SL/TP
- Swing Trading: Multi-day (1-7 days), wider SL/TP
- Position Trading: Long-term (1-4 weeks), widest SL/TP
- Timeframes remain fully user-controlled (not auto-changed)

### Signal Deletion
- Delete button (trash icon) on each signal card
- DELETE /api/signals/{signal_id} endpoint
- Signals auto-refresh every 10s for TP/SL status updates

### Trade Close Fix
- Fixed OANDA close position: now GETs position first to determine long/short side, then sends correct close body (was sending both longUnits+shortUnits which OANDA rejected)

## Mar 26, 2026 - Login Fix, Market Speed Boost (Fork Job 4)
### Login/Signup Bug Fix
- Rate limits relaxed: login/register 30/min (was 5/min — blocked all users behind shared proxy)
- Brute-force threshold: 15 attempts (was 5)
- Fixed sanitize_input corrupting email during registration (used local vars instead of mutating Pydantic model)

### Market Data Speed Boost
- Crypto: 10s refresh (was 30s)
- Forex: 3s refresh (was 5s)
- Indian: 60s refresh (was 300s — 5x faster)
- Frontend polling: 800ms (was 1500ms)
- ThreadPoolExecutor: 6 workers (was 3)
- All pages updated to use 800ms polling

## Mar 25, 2026 - Security Hardening, Dual Admin, Enhanced AI Prompt, Animations (Fork Job 3)
### Dual Admin Access
- Primary: contact.developersingh@gmail.com / admin123
- Secondary: infinityanirudra@gmail.com / admin456
- Both can access /admin panel and all admin API endpoints

### Security Hardening
- Rate limiting via slowapi: login (5/min), register (5/min), signals (10/min), chat (20/min)
- Brute-force protection: 5 failed login attempts = 5-minute lockout
- Security headers: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy
- Input sanitization: XSS stripping, HTML escaping, length limits
- Input validation: Email regex, password min 6 chars

### Enhanced AI Signal Prompt (MasterPrompt2.0)
- Comprehensive technical indicators: SMA/EMA crossovers, RSI(14), MACD(12,26,9), Bollinger Bands(20,2), Ichimoku Cloud, Supertrend, ATR, OBV, Stochastic, CCI
- Market structure analysis: BOS, CHoCH, Order Blocks, FVG, Premium/Discount zones, Supply/Demand
- Kill Zone awareness for forex (London/NY sessions)
- Risk level classification: LOW/MEDIUM/HIGH
- Technical summary and session notes in signal output

### Professional Animations
- Page enter transitions (fadeInScale)
- Stagger animations for card grids (blur + scale + translate)
- Button effects: btn-glow (hover shadow), btn-ripple (click effect)
- Card border glow animation on signal generator
- Smooth sidebar transitions with hover backgrounds
- 10+ new CSS animation utilities available

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
