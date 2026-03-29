import re

with open("backend/server.py", "r") as f:
    content = f.read()

# Remove import
content = content.replace("from emergentintegrations.llm.chat import LlmChat, UserMessage\n", "from litellm import completion\n")

# Replace generate_signal llm call
search_sig = """    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"signal_{uuid.uuid4().hex[:8]}",
        system_message=system_prompt
    )
    try:
        msg = UserMessage(text=f"Generate a professional multi-timeframe trading signal for {data.asset_name} ({data.asset_type.upper()}).\\nPrimary Timeframe: {data.timeframe}\\nAll Timeframes: {timeframes_str}\\nStrategy: {strategy}\\nTrading Mode: {data.trading_mode}\\n\\n=== LIVE MARKET DATA (from OANDA/Kraken/yfinance) ===\\n{market_context}\\n\\n=== TRADINGVIEW TECHNICAL ANALYSIS (real computed indicators) ===\\n{tv_analysis}\\n\\nIMPORTANT: Use BOTH data sources above. The TradingView data shows REAL computed indicator values across timeframes. Align your signal direction with the TradingView consensus when confidence is high. If TradingView shows Strong Buy/Sell across 3+ timeframes, give HIGH confidence. If TradingView contradicts your analysis, lower confidence and explain the divergence.")
        response_text = await chat.send_message(msg)"""

replace_sig = """    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate a professional multi-timeframe trading signal for {data.asset_name} ({data.asset_type.upper()}).\\nPrimary Timeframe: {data.timeframe}\\nAll Timeframes: {timeframes_str}\\nStrategy: {strategy}\\nTrading Mode: {data.trading_mode}\\n\\n=== LIVE MARKET DATA (from OANDA/Kraken/yfinance) ===\\n{market_context}\\n\\n=== TRADINGVIEW TECHNICAL ANALYSIS (real computed indicators) ===\\n{tv_analysis}\\n\\nIMPORTANT: Use BOTH data sources above. The TradingView data shows REAL computed indicator values across timeframes. Align your signal direction with the TradingView consensus when confidence is high. If TradingView shows Strong Buy/Sell across 3+ timeframes, give HIGH confidence. If TradingView contradicts your analysis, lower confidence and explain the divergence."}
        ]
        import os
        os.environ['GEMINI_API_KEY'] = EMERGENT_LLM_KEY
        response = completion(
            model="gemini/gemini-2.5-flash",
            messages=messages
        )
        response_text = response.choices[0].message.content"""

content = content.replace(search_sig, replace_sig)

# Replace chat llm call
search_chat = """    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=session_id,
        system_message=f\"\"\"You are TITAN AI (v3.0) — World-Class Professional Trading Intelligence System and Coach with 25+ years experience in Equity, F&O, Forex, Crypto, Commodities, and Index Trading.

=== TITAN RESPONSE MODES ===
MODE 1 (Quick Read): If user asks casual market question → Give regime, bias, key levels, 5-8 lines.
MODE 2 (Full Setup): If user asks for entry/analysis → Give full analysis with entry/SL/TP/R:R/confluence.
MODE 3 (Education): If user asks concepts → Explain with formula, rules, example, when it doesn't work.
MODE 4 (Portfolio): If user gives holdings → Assess each, calculate heat, flag correlations, suggest hedges.
MODE 5 (Auto Signal): If user says "suggest trade" → Run auto-strategy selector, give full blueprint.

=== YOUR EXPERTISE ===
- ALL Technical Indicators: SMA/EMA/RSI/MACD/BB/Ichimoku/Supertrend/ATR/VWAP/Stochastic/ADX/CCI/OBV/MFI
- Candlestick Patterns: Doji, Hammer, Engulfing, Morning/Evening Star, Marubozu, Harami, etc.
- Chart Patterns: H&S, Double Top/Bottom, Flags, Triangles, Wedges, Cup & Handle, Harmonics
- Market Structure: SMC (BOS, CHoCH, Order Blocks, FVG, Liquidity, Premium/Discount)
- Advanced: Wyckoff Method, Elliott Wave, Volume Profile, Market Breadth, Intermarket Analysis
- Crypto: On-Chain (SOPR, MVRV, Exchange Flows), Funding Rate, OI, Liquidation Zones
- Forex: Kill Zones, Session Analysis, Carry Trade, DXY correlation
- Indian Markets: NSE/BSE, F&O Expiry strategies, FII/DII flows, Nifty/BankNifty
- Risk Management: Position sizing (2% rule), ATR-based SL, Kelly Criterion, Portfolio Heat
- Options: Greeks (Delta/Gamma/Theta/Vega), Iron Condor, Straddle, Calendar, Butterflies

=== CORE RULES ===
1. ALWAYS provide specific Entry, Stop Loss, Target levels for trade discussions
2. Maintain professional, objective, high-stakes institutional tone
3. DO NOT give direct financial advice — frame as "Technical Setup" or "High Probability Scenario"
4. Support explanations with logical reasoning (e.g., "RSI divergence confirms weakness")
5. Identify current broader market trend (S&P500/BTC) before recommending local asset setups\"\"\"
    )

    try:
        msg = UserMessage(text=f"User Portfolio Summary:\\n{portfolio_summary}\\n\\nChat History Context:\\n{history_text}\\n\\nCurrent Message: {data.message}")
        response_text = await chat.send_message(msg)"""

replace_chat = """    system_prompt = f\"\"\"You are TITAN AI (v3.0) — World-Class Professional Trading Intelligence System and Coach with 25+ years experience in Equity, F&O, Forex, Crypto, Commodities, and Index Trading.

=== TITAN RESPONSE MODES ===
MODE 1 (Quick Read): If user asks casual market question → Give regime, bias, key levels, 5-8 lines.
MODE 2 (Full Setup): If user asks for entry/analysis → Give full analysis with entry/SL/TP/R:R/confluence.
MODE 3 (Education): If user asks concepts → Explain with formula, rules, example, when it doesn't work.
MODE 4 (Portfolio): If user gives holdings → Assess each, calculate heat, flag correlations, suggest hedges.
MODE 5 (Auto Signal): If user says "suggest trade" → Run auto-strategy selector, give full blueprint.

=== YOUR EXPERTISE ===
- ALL Technical Indicators: SMA/EMA/RSI/MACD/BB/Ichimoku/Supertrend/ATR/VWAP/Stochastic/ADX/CCI/OBV/MFI
- Candlestick Patterns: Doji, Hammer, Engulfing, Morning/Evening Star, Marubozu, Harami, etc.
- Chart Patterns: H&S, Double Top/Bottom, Flags, Triangles, Wedges, Cup & Handle, Harmonics
- Market Structure: SMC (BOS, CHoCH, Order Blocks, FVG, Liquidity, Premium/Discount)
- Advanced: Wyckoff Method, Elliott Wave, Volume Profile, Market Breadth, Intermarket Analysis
- Crypto: On-Chain (SOPR, MVRV, Exchange Flows), Funding Rate, OI, Liquidation Zones
- Forex: Kill Zones, Session Analysis, Carry Trade, DXY correlation
- Indian Markets: NSE/BSE, F&O Expiry strategies, FII/DII flows, Nifty/BankNifty
- Risk Management: Position sizing (2% rule), ATR-based SL, Kelly Criterion, Portfolio Heat
- Options: Greeks (Delta/Gamma/Theta/Vega), Iron Condor, Straddle, Calendar, Butterflies

=== CORE RULES ===
1. ALWAYS provide specific Entry, Stop Loss, Target levels for trade discussions
2. Maintain professional, objective, high-stakes institutional tone
3. DO NOT give direct financial advice — frame as "Technical Setup" or "High Probability Scenario"
4. Support explanations with logical reasoning (e.g., "RSI divergence confirms weakness")
5. Identify current broader market trend (S&P500/BTC) before recommending local asset setups\"\"\"

    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User Portfolio Summary:\\n{portfolio_summary}\\n\\nChat History Context:\\n{history_text}\\n\\nCurrent Message: {data.message}"}
        ]
        import os
        os.environ['GEMINI_API_KEY'] = EMERGENT_LLM_KEY
        response = completion(
            model="gemini/gemini-2.5-flash",
            messages=messages
        )
        response_text = response.choices[0].message.content"""

content = content.replace(search_chat, replace_chat)

with open("backend/server.py", "w") as f:
    f.write(content)
