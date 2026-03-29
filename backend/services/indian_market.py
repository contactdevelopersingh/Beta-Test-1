"""Indian Market Extended Service - Combines Yahoo Finance v8 + yfinance + Black-Scholes
Attempts multiple data sources for maximum coverage of Indian stocks."""
import requests
import logging
import time
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional
import yfinance as yf

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=4)
_cache: Dict[str, dict] = {}

YF_HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# Complete NIFTY 500 major stocks (BSE codes + NSE symbols)
NIFTY500_TOP = [
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","BHARTIARTL","ITC","WIPRO",
    "HINDUNILVR","BAJFINANCE","HCLTECH","MARUTI","ADANIENT","AXISBANK","KOTAKBANK",
    "LT","TITAN","SUNPHARMA","ULTRACEMCO","TECHM","ASIANPAINT","M&M","POWERGRID",
    "NTPC","ONGC","COALINDIA","JSWSTEEL","TATASTEEL","TATAMOTORS","BAJAJFINSV",
    "NESTLEIND","DRREDDY","CIPLA","DIVISLAB","HEROMOTOCO","EICHERMOT","BRITANNIA",
    "DABUR","GODREJCP","INDUSINDBK","GRASIM","HINDALCO","BPCL","TATACONSUM",
    "APOLLOHOSP","SBILIFE","HDFCLIFE","VEDL","ZOMATO","PAYTM","NYKAA","IRCTC",
    "TRENT","DMART","PIIND","SIEMENS","HAVELLS","ABB","TORNTPHARM","MPHASIS",
    "PERSISTENT","COFORGE","LTIM","MANKIND","POLYCAB","SOLARINDS","DEEPAKNITRO",
    "AUROPHARMA","LUPIN","BIOCON","MAXHEALTH","FORTIS","MUTHOOTFIN","BAJAJHLDNG",
    "CHOLAFIN","SHRIRAMFIN","BANDHANBNK","IDFCFIRSTB","PNB","BANKBARODA","CANBK",
    "UNIONBANK","IOB","FEDERALBNK","RBLBANK","HDFC","ADANIPORTS","ADANIGREEN",
    "ADANIPOWER","ADANITRANS","AMBUJACEM","ACC","GAIL","IOC","HPCL","SAIL",
    "NMDC","NHPC","PFC","RECLTD","SJVN","IRFC","BEL","HAL","BHEL","CONCOR",
]

def _fetch_yf_v8_batch(symbols: list) -> dict:
    """Fetch real-time data using Yahoo Finance v8 chart API"""
    results = {}
    for sym in symbols:
        yf_sym = f"{sym}.NS"
        cache_key = f"yf8_{yf_sym}"
        if cache_key in _cache and time.time() - _cache[cache_key]['time'] < 120:
            results[sym] = _cache[cache_key]['data']
            continue
        try:
            r = requests.get(
                f"https://query2.finance.yahoo.com/v8/finance/chart/{yf_sym}?interval=1d&range=5d",
                headers=YF_HEADERS, timeout=8
            )
            if r.status_code == 200:
                d = r.json()
                meta = d.get('chart', {}).get('result', [{}])[0].get('meta', {})
                price = meta.get('regularMarketPrice', 0)
                prev = meta.get('chartPreviousClose', meta.get('previousClose', price))
                change = round(price - prev, 2) if price and prev else 0
                change_pct = round((change / prev) * 100, 2) if prev else 0
                
                result = {
                    'symbol': sym,
                    'price': price,
                    'prev_close': prev,
                    'change': change,
                    'change_pct': change_pct,
                    'exchange': meta.get('exchangeName', 'NSE'),
                    'currency': meta.get('currency', 'INR'),
                    'type': meta.get('instrumentType', 'EQUITY'),
                }
                results[sym] = result
                _cache[cache_key] = {'data': result, 'time': time.time()}
        except Exception as e:
            logger.debug(f"YF v8 failed for {sym}: {e}")
    return results

def _fetch_market_movers() -> dict:
    """Fetch gainers, losers using yfinance"""
    try:
        tickers_str = ' '.join([f"{s}.NS" for s in NIFTY500_TOP[:50]])
        tickers = yf.Tickers(tickers_str)
        movers = []
        for sym in NIFTY500_TOP[:50]:
            yf_sym = f"{sym}.NS"
            try:
                t = tickers.tickers.get(yf_sym)
                if not t: continue
                info = t.fast_info
                price = float(info.get('lastPrice', info.get('last_price', 0)))
                prev = float(info.get('previousClose', info.get('previous_close', price)))
                if price and prev:
                    change_pct = round((price - prev) / prev * 100, 2)
                    movers.append({
                        'symbol': sym, 'price': round(price, 2),
                        'change_pct': change_pct,
                        'volume': int(info.get('lastVolume', info.get('last_volume', 0))),
                    })
            except: continue
        
        movers.sort(key=lambda x: x['change_pct'], reverse=True)
        return {
            'gainers': movers[:10],
            'losers': movers[-10:][::-1],
            'most_active': sorted(movers, key=lambda x: x.get('volume', 0), reverse=True)[:10],
        }
    except Exception as e:
        logger.error(f"Market movers failed: {e}")
        return {'gainers': [], 'losers': [], 'most_active': []}

async def get_all_nifty_stocks() -> list:
    """Get all NIFTY 500 top stocks with current price"""
    loop = asyncio.get_event_loop()
    # Fetch in batches of 20
    all_results = {}
    for i in range(0, min(len(NIFTY500_TOP), 100), 20):
        batch = NIFTY500_TOP[i:i+20]
        batch_results = await loop.run_in_executor(_executor, _fetch_yf_v8_batch, batch)
        all_results.update(batch_results)
    
    stocks = []
    for sym in NIFTY500_TOP:
        if sym in all_results:
            d = all_results[sym]
            stocks.append({
                'symbol': d['symbol'],
                'price': d['price'],
                'change_pct': d['change_pct'],
                'exchange': d.get('exchange', 'NSE'),
            })
    return stocks

async def get_market_movers() -> dict:
    cache_key = 'market_movers'
    if cache_key in _cache and time.time() - _cache[cache_key]['time'] < 180:
        return _cache[cache_key]['data']
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(_executor, _fetch_market_movers)
    _cache[cache_key] = {'data': data, 'time': time.time()}
    return data

async def get_stock_quote(symbol: str) -> dict:
    """Get detailed quote for a single stock"""
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(_executor, _fetch_yf_v8_batch, [symbol])
    return results.get(symbol, {'error': f'No data for {symbol}'})
