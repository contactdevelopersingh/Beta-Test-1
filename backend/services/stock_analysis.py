"""Stock Analysis Service - Deep fundamentals, screener, peers, IPO for Indian stocks"""
import yfinance as yf
import logging
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=4)
_cache: Dict[str, dict] = {}
CACHE_TTL = 300  # 5 min for fundamentals

# Full Indian stock universe
STOCK_UNIVERSE = {
    "RELIANCE.NS": {"symbol": "RELIANCE", "name": "Reliance Industries", "sector": "Energy"},
    "TCS.NS": {"symbol": "TCS", "name": "Tata Consultancy Services", "sector": "IT"},
    "INFY.NS": {"symbol": "INFY", "name": "Infosys", "sector": "IT"},
    "HDFCBANK.NS": {"symbol": "HDFCBANK", "name": "HDFC Bank", "sector": "Banking"},
    "ICICIBANK.NS": {"symbol": "ICICIBANK", "name": "ICICI Bank", "sector": "Banking"},
    "SBIN.NS": {"symbol": "SBIN", "name": "State Bank of India", "sector": "Banking"},
    "ITC.NS": {"symbol": "ITC", "name": "ITC Limited", "sector": "FMCG"},
    "BHARTIARTL.NS": {"symbol": "BHARTIARTL", "name": "Bharti Airtel", "sector": "Telecom"},
    "WIPRO.NS": {"symbol": "WIPRO", "name": "Wipro", "sector": "IT"},
    "HINDUNILVR.NS": {"symbol": "HINDUNILVR", "name": "Hindustan Unilever", "sector": "FMCG"},
    "BAJFINANCE.NS": {"symbol": "BAJFINANCE", "name": "Bajaj Finance", "sector": "Finance"},
    "HCLTECH.NS": {"symbol": "HCLTECH", "name": "HCL Technologies", "sector": "IT"},
    "MARUTI.NS": {"symbol": "MARUTI", "name": "Maruti Suzuki", "sector": "Auto"},
    "ADANIENT.NS": {"symbol": "ADANIENT", "name": "Adani Enterprises", "sector": "Conglomerate"},
    "AXISBANK.NS": {"symbol": "AXISBANK", "name": "Axis Bank", "sector": "Banking"},
    "KOTAKBANK.NS": {"symbol": "KOTAKBANK", "name": "Kotak Mahindra Bank", "sector": "Banking"},
    "LT.NS": {"symbol": "LT", "name": "Larsen & Toubro", "sector": "Infrastructure"},
    "TITAN.NS": {"symbol": "TITAN", "name": "Titan Company", "sector": "Consumer"},
    "SUNPHARMA.NS": {"symbol": "SUNPHARMA", "name": "Sun Pharma", "sector": "Pharma"},
    "ULTRACEMCO.NS": {"symbol": "ULTRACEMCO", "name": "UltraTech Cement", "sector": "Cement"},
    "TECHM.NS": {"symbol": "TECHM", "name": "Tech Mahindra", "sector": "IT"},
    "ASIANPAINT.NS": {"symbol": "ASIANPAINT", "name": "Asian Paints", "sector": "Consumer"},
    "M&M.NS": {"symbol": "M&M", "name": "Mahindra & Mahindra", "sector": "Auto"},
    "POWERGRID.NS": {"symbol": "POWERGRID", "name": "Power Grid Corp", "sector": "Power"},
    "NTPC.NS": {"symbol": "NTPC", "name": "NTPC Limited", "sector": "Power"},
    "ONGC.NS": {"symbol": "ONGC", "name": "ONGC", "sector": "Energy"},
    "COALINDIA.NS": {"symbol": "COALINDIA", "name": "Coal India", "sector": "Mining"},
    "JSWSTEEL.NS": {"symbol": "JSWSTEEL", "name": "JSW Steel", "sector": "Steel"},
    "TATASTEEL.NS": {"symbol": "TATASTEEL", "name": "Tata Steel", "sector": "Steel"},
    "TATAMOTORS.NS": {"symbol": "TATAMOTORS", "name": "Tata Motors", "sector": "Auto"},
    "BAJAJFINSV.NS": {"symbol": "BAJAJFINSV", "name": "Bajaj Finserv", "sector": "Finance"},
    "NESTLEIND.NS": {"symbol": "NESTLEIND", "name": "Nestle India", "sector": "FMCG"},
    "DRREDDY.NS": {"symbol": "DRREDDY", "name": "Dr Reddy's", "sector": "Pharma"},
    "CIPLA.NS": {"symbol": "CIPLA", "name": "Cipla", "sector": "Pharma"},
    "DIVISLAB.NS": {"symbol": "DIVISLAB", "name": "Divi's Labs", "sector": "Pharma"},
    "HEROMOTOCO.NS": {"symbol": "HEROMOTOCO", "name": "Hero MotoCorp", "sector": "Auto"},
    "EICHERMOT.NS": {"symbol": "EICHERMOT", "name": "Eicher Motors", "sector": "Auto"},
    "BRITANNIA.NS": {"symbol": "BRITANNIA", "name": "Britannia Industries", "sector": "FMCG"},
    "DABUR.NS": {"symbol": "DABUR", "name": "Dabur India", "sector": "FMCG"},
    "GODREJCP.NS": {"symbol": "GODREJCP", "name": "Godrej Consumer", "sector": "FMCG"},
}

# Map internal ID to yfinance symbol
ID_TO_YF = {}
for yf_sym, meta in STOCK_UNIVERSE.items():
    ID_TO_YF[meta['symbol'].lower()] = yf_sym

def _safe_get(info, key, default=None):
    try:
        v = info.get(key, default)
        if v is None or v == 'N/A':
            return default
        return v
    except Exception:
        return default

def _fetch_stock_fundamentals(yf_symbol: str) -> dict:
    """Fetch comprehensive fundamentals from yfinance"""
    try:
        ticker = yf.Ticker(yf_symbol)
        info = ticker.info or {}
        hist = ticker.history(period="1y")
        
        price = _safe_get(info, 'currentPrice', _safe_get(info, 'regularMarketPrice', 0))
        prev_close = _safe_get(info, 'previousClose', 0)
        change = round(price - prev_close, 2) if price and prev_close else 0
        change_pct = round((change / prev_close) * 100, 2) if prev_close else 0
        
        market_cap = _safe_get(info, 'marketCap', 0)
        market_cap_cr = round(market_cap / 1e7, 2) if market_cap else 0

        # Get quarterly financials
        quarterly = []
        try:
            qf = ticker.quarterly_financials
            if qf is not None and not qf.empty:
                for col in qf.columns[:8]:
                    q = {"quarter": col.strftime("%b %Y")}
                    for row in qf.index:
                        q[row.replace(' ', '_').lower()] = round(float(qf.loc[row, col]), 2) if not qf.loc[row, col] != qf.loc[row, col] else 0
                    quarterly.append(q)
        except Exception:
            pass

        # Get annual financials
        annual_pl = []
        try:
            af = ticker.financials
            if af is not None and not af.empty:
                for col in af.columns[:10]:
                    a = {"year": col.strftime("%Y")}
                    for row in af.index:
                        a[row.replace(' ', '_').lower()] = round(float(af.loc[row, col]), 2) if not af.loc[row, col] != af.loc[row, col] else 0
                    annual_pl.append(a)
        except Exception:
            pass

        # Balance sheet
        balance_sheet = []
        try:
            bs = ticker.balance_sheet
            if bs is not None and not bs.empty:
                for col in bs.columns[:10]:
                    b = {"year": col.strftime("%Y")}
                    for row in bs.index:
                        b[row.replace(' ', '_').lower()] = round(float(bs.loc[row, col]), 2) if not bs.loc[row, col] != bs.loc[row, col] else 0
                    balance_sheet.append(b)
        except Exception:
            pass

        # Cash flow
        cash_flow = []
        try:
            cf = ticker.cashflow
            if cf is not None and not cf.empty:
                for col in cf.columns[:10]:
                    c = {"year": col.strftime("%Y")}
                    for row in cf.index:
                        c[row.replace(' ', '_').lower()] = round(float(cf.loc[row, col]), 2) if not cf.loc[row, col] != cf.loc[row, col] else 0
                    cash_flow.append(c)
        except Exception:
            pass

        # Shareholding (from major holders)
        shareholding = {"promoters": 0, "fii": 0, "dii": 0, "public": 0}
        try:
            mh = ticker.major_holders
            if mh is not None and not mh.empty:
                for _, row in mh.iterrows():
                    pct = float(str(row.iloc[0]).replace('%', ''))
                    label = str(row.iloc[1]).lower()
                    if 'insider' in label or 'promoter' in label:
                        shareholding['promoters'] = round(pct, 2)
                    elif 'institution' in label:
                        shareholding['dii'] = round(pct, 2)
        except Exception:
            pass
        shareholding['public'] = round(100 - shareholding['promoters'] - shareholding['fii'] - shareholding['dii'], 2)

        # Build pros and cons
        pros = []
        cons = []
        pe = _safe_get(info, 'trailingPE', 0)
        roe = _safe_get(info, 'returnOnEquity', 0)
        if roe: roe = round(roe * 100, 2)
        de = _safe_get(info, 'debtToEquity', 0)
        if de: de = round(de / 100, 2) if de > 5 else round(de, 2)
        cr = _safe_get(info, 'currentRatio', 0)
        dy = _safe_get(info, 'dividendYield', 0)
        if dy: dy = round(dy * 100, 2)
        opm = _safe_get(info, 'operatingMargins', 0)
        if opm: opm = round(opm * 100, 2)
        npm = _safe_get(info, 'profitMargins', 0)
        if npm: npm = round(npm * 100, 2)
        rev_growth = _safe_get(info, 'revenueGrowth', 0)
        if rev_growth: rev_growth = round(rev_growth * 100, 2)

        if pe and pe < 25: pros.append(f"P/E ratio ({pe:.1f}) is reasonable")
        if pe and pe > 40: cons.append(f"P/E ratio ({pe:.1f}) is expensive")
        if roe and roe > 15: pros.append(f"Strong ROE of {roe:.1f}%")
        if roe and roe < 8: cons.append(f"Low ROE of {roe:.1f}%")
        if de is not None and de < 0.5: pros.append(f"Low debt (D/E: {de:.2f})")
        if de is not None and de > 1: cons.append(f"High debt (D/E: {de:.2f})")
        if cr and cr > 1.5: pros.append(f"Good current ratio ({cr:.2f})")
        if cr and cr < 1: cons.append(f"Weak current ratio ({cr:.2f})")
        if dy and dy > 2: pros.append(f"Good dividend yield ({dy:.1f}%)")
        if opm and opm > 20: pros.append(f"High operating margin ({opm:.1f}%)")
        if opm and opm < 5: cons.append(f"Low operating margin ({opm:.1f}%)")
        if npm and npm > 10: pros.append(f"Healthy net margin ({npm:.1f}%)")
        if npm and npm < 3: cons.append(f"Very low net margin ({npm:.1f}%)")
        if rev_growth and rev_growth > 10: pros.append(f"Revenue growing at {rev_growth:.1f}%")
        if rev_growth and rev_growth < 0: cons.append(f"Revenue declining ({rev_growth:.1f}%)")
        if shareholding['promoters'] > 50: pros.append(f"High promoter holding ({shareholding['promoters']}%)")
        if shareholding['promoters'] < 30: cons.append(f"Low promoter holding ({shareholding['promoters']}%)")

        result = {
            "symbol": yf_symbol.replace('.NS', ''),
            "name": _safe_get(info, 'longName', _safe_get(info, 'shortName', '')),
            "sector": _safe_get(info, 'sector', ''),
            "industry": _safe_get(info, 'industry', ''),
            "exchange": "NSE",
            "price": price,
            "prev_close": prev_close,
            "change": change,
            "change_pct": change_pct,
            "day_high": _safe_get(info, 'dayHigh', 0),
            "day_low": _safe_get(info, 'dayLow', 0),
            "week_52_high": _safe_get(info, 'fiftyTwoWeekHigh', 0),
            "week_52_low": _safe_get(info, 'fiftyTwoWeekLow', 0),
            "volume": _safe_get(info, 'volume', 0),
            "avg_volume": _safe_get(info, 'averageVolume', 0),
            "market_cap_cr": market_cap_cr,
            "face_value": _safe_get(info, 'faceValue', 10),
            "isin": _safe_get(info, 'isin', ''),
            "fundamentals": {
                "pe_ratio": round(pe, 2) if pe else None,
                "pb_ratio": round(_safe_get(info, 'priceToBook', 0), 2) or None,
                "ev_ebitda": round(_safe_get(info, 'enterpriseToEbitda', 0), 2) or None,
                "price_to_sales": round(_safe_get(info, 'priceToSalesTrailing12Months', 0), 2) or None,
                "peg_ratio": round(_safe_get(info, 'pegRatio', 0), 2) or None,
                "eps": round(_safe_get(info, 'trailingEps', 0), 2) or None,
                "book_value": round(_safe_get(info, 'bookValue', 0), 2) or None,
                "roe": roe or None,
                "roce": round(_safe_get(info, 'returnOnAssets', 0) * 100, 2) if _safe_get(info, 'returnOnAssets') else None,
                "roa": round(_safe_get(info, 'returnOnAssets', 0) * 100, 2) if _safe_get(info, 'returnOnAssets') else None,
                "opm": opm or None,
                "npm": npm or None,
                "debt_to_equity": de,
                "current_ratio": round(cr, 2) if cr else None,
                "dividend_yield": dy or None,
                "dividend_per_share": round(_safe_get(info, 'dividendRate', 0), 2) or None,
                "payout_ratio": round(_safe_get(info, 'payoutRatio', 0) * 100, 2) if _safe_get(info, 'payoutRatio') else None,
                "revenue_growth": rev_growth or None,
                "earnings_growth": round(_safe_get(info, 'earningsGrowth', 0) * 100, 2) if _safe_get(info, 'earningsGrowth') else None,
                "free_cash_flow": round(_safe_get(info, 'freeCashflow', 0) / 1e7, 2) if _safe_get(info, 'freeCashflow') else None,
                "total_debt_cr": round(_safe_get(info, 'totalDebt', 0) / 1e7, 2) if _safe_get(info, 'totalDebt') else None,
                "total_cash_cr": round(_safe_get(info, 'totalCash', 0) / 1e7, 2) if _safe_get(info, 'totalCash') else None,
            },
            "shareholding": shareholding,
            "pros": pros,
            "cons": cons,
            "quarterly_results": quarterly,
            "annual_pl": annual_pl,
            "balance_sheet": balance_sheet,
            "cash_flow": cash_flow,
            "analyst": {
                "target_mean": round(_safe_get(info, 'targetMeanPrice', 0), 2) or None,
                "target_high": round(_safe_get(info, 'targetHighPrice', 0), 2) or None,
                "target_low": round(_safe_get(info, 'targetLowPrice', 0), 2) or None,
                "recommendation": _safe_get(info, 'recommendationKey', ''),
                "num_analysts": _safe_get(info, 'numberOfAnalystOpinions', 0),
            },
        }
        return result
    except Exception as e:
        logger.error(f"Fundamentals fetch failed for {yf_symbol}: {e}")
        return {"error": str(e), "symbol": yf_symbol}

async def get_stock_analysis(stock_id: str) -> dict:
    """Get full stock analysis with caching"""
    now = time.time()
    cache_key = f"analysis_{stock_id}"
    if cache_key in _cache and (now - _cache[cache_key]['time']) < CACHE_TTL:
        return _cache[cache_key]['data']
    
    yf_sym = ID_TO_YF.get(stock_id.lower())
    if not yf_sym:
        yf_sym = f"{stock_id.upper()}.NS"
    
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(_executor, _fetch_stock_fundamentals, yf_sym)
    if data and 'error' not in data:
        _cache[cache_key] = {'data': data, 'time': now}
    return data

def _fetch_peers(sector: str, exclude_symbol: str) -> list:
    """Fetch peer companies in same sector"""
    peers = []
    for yf_sym, meta in STOCK_UNIVERSE.items():
        if meta['sector'] == sector and meta['symbol'] != exclude_symbol:
            try:
                t = yf.Ticker(yf_sym)
                info = t.info or {}
                price = _safe_get(info, 'currentPrice', _safe_get(info, 'regularMarketPrice', 0))
                if not price:
                    continue
                mc = _safe_get(info, 'marketCap', 0)
                peers.append({
                    "symbol": meta['symbol'],
                    "name": meta['name'],
                    "price": round(price, 2),
                    "market_cap_cr": round(mc / 1e7, 2) if mc else 0,
                    "pe_ratio": round(_safe_get(info, 'trailingPE', 0), 2) or None,
                    "pb_ratio": round(_safe_get(info, 'priceToBook', 0), 2) or None,
                    "roe": round((_safe_get(info, 'returnOnEquity', 0) or 0) * 100, 2) or None,
                    "opm": round((_safe_get(info, 'operatingMargins', 0) or 0) * 100, 2) or None,
                    "npm": round((_safe_get(info, 'profitMargins', 0) or 0) * 100, 2) or None,
                    "debt_to_equity": round((_safe_get(info, 'debtToEquity', 0) or 0) / 100, 2) if _safe_get(info, 'debtToEquity') and _safe_get(info, 'debtToEquity') > 5 else round(_safe_get(info, 'debtToEquity', 0) or 0, 2),
                    "dividend_yield": round((_safe_get(info, 'dividendYield', 0) or 0) * 100, 2) or None,
                })
            except Exception:
                continue
    return peers[:10]

async def get_peers(sector: str, exclude_symbol: str) -> list:
    cache_key = f"peers_{sector}"
    now = time.time()
    if cache_key in _cache and (now - _cache[cache_key]['time']) < 600:
        return [p for p in _cache[cache_key]['data'] if p['symbol'] != exclude_symbol]
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(_executor, _fetch_peers, sector, exclude_symbol)
    _cache[cache_key] = {'data': data, 'time': now}
    return data

def _run_screener(filters: dict) -> list:
    """Run stock screener against the universe"""
    results = []
    for yf_sym, meta in STOCK_UNIVERSE.items():
        try:
            t = yf.Ticker(yf_sym)
            info = t.info or {}
            price = _safe_get(info, 'currentPrice', 0)
            if not price:
                continue
            pe = _safe_get(info, 'trailingPE', 0)
            roe = round((_safe_get(info, 'returnOnEquity', 0) or 0) * 100, 2)
            de = _safe_get(info, 'debtToEquity', 0)
            if de and de > 5: de = round(de / 100, 2)
            mc = round((_safe_get(info, 'marketCap', 0) or 0) / 1e7, 2)
            dy = round((_safe_get(info, 'dividendYield', 0) or 0) * 100, 2)
            opm = round((_safe_get(info, 'operatingMargins', 0) or 0) * 100, 2)
            npm = round((_safe_get(info, 'profitMargins', 0) or 0) * 100, 2)
            pb = _safe_get(info, 'priceToBook', 0)

            # Apply filters
            if filters.get('pe_min') and (not pe or pe < filters['pe_min']): continue
            if filters.get('pe_max') and pe and pe > filters['pe_max']: continue
            if filters.get('roe_min') and roe < filters['roe_min']: continue
            if filters.get('de_max') and de and de > filters['de_max']: continue
            if filters.get('mc_min') and mc < filters['mc_min']: continue
            if filters.get('mc_max') and mc > filters['mc_max']: continue
            if filters.get('dy_min') and dy < filters['dy_min']: continue
            if filters.get('opm_min') and opm < filters['opm_min']: continue
            if filters.get('sector') and meta['sector'] != filters['sector']: continue

            results.append({
                "symbol": meta['symbol'], "name": meta['name'], "sector": meta['sector'],
                "price": round(price, 2), "market_cap_cr": mc,
                "pe_ratio": round(pe, 2) if pe else None,
                "pb_ratio": round(pb, 2) if pb else None,
                "roe": roe or None, "opm": opm or None, "npm": npm or None,
                "debt_to_equity": round(de, 2) if de else None,
                "dividend_yield": dy or None,
            })
        except Exception:
            continue
    return sorted(results, key=lambda x: x.get('market_cap_cr', 0), reverse=True)

async def run_screener(filters: dict) -> list:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _run_screener, filters)

def get_all_sectors() -> list:
    return sorted(set(m['sector'] for m in STOCK_UNIVERSE.values()))

def get_stock_list() -> list:
    return [{"symbol": m['symbol'], "name": m['name'], "sector": m['sector']} for m in STOCK_UNIVERSE.values()]
