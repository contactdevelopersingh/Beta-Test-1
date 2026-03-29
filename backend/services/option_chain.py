"""Indian Market Option Chain Service - Black-Scholes based calculator + expanded stock universe"""
import math
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict

logger = logging.getLogger(__name__)

# Risk-free rate (India 10Y bond ~7%)
RISK_FREE_RATE = 0.07
# Default IV if VIX not available
DEFAULT_IV = 0.15

# F&O stocks (stocks that have options trading)
FNO_STOCKS = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "BHARTIARTL",
    "ITC", "WIPRO", "HINDUNILVR", "BAJFINANCE", "HCLTECH", "MARUTI", "ADANIENT",
    "AXISBANK", "KOTAKBANK", "LT", "TITAN", "SUNPHARMA", "ULTRACEMCO",
    "TECHM", "ASIANPAINT", "POWERGRID", "NTPC", "ONGC", "COALINDIA",
    "JSWSTEEL", "TATASTEEL", "TATAMOTORS", "BAJAJFINSV", "NESTLEIND",
    "DRREDDY", "CIPLA", "DIVISLAB", "HEROMOTOCO", "EICHERMOT", "BRITANNIA",
    "DABUR", "M&M", "INDUSINDBK", "GRASIM", "HINDALCO", "BPCL",
    "TATACONSUM", "APOLLOHOSP", "SBILIFE", "HDFCLIFE", "VEDL", "ZOMATO",
]

# Index options
FNO_INDICES = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]

# Lot sizes
LOT_SIZES = {
    "NIFTY": 50, "BANKNIFTY": 15, "FINNIFTY": 25, "MIDCPNIFTY": 50,
    "RELIANCE": 250, "TCS": 150, "INFY": 300, "HDFCBANK": 550,
    "ICICIBANK": 700, "SBIN": 750, "BHARTIARTL": 475, "ITC": 1600,
    "BAJFINANCE": 125, "TATAMOTORS": 575, "ADANIENT": 250, "AXISBANK": 600,
    "LT": 150, "MARUTI": 50, "SUNPHARMA": 300, "WIPRO": 1500,
}

def black_scholes_call(S, K, T, r, sigma):
    """Black-Scholes Call option price"""
    if T <= 0 or sigma <= 0:
        return max(S - K, 0)
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    N_d1 = 0.5 * (1 + math.erf(d1 / math.sqrt(2)))
    N_d2 = 0.5 * (1 + math.erf(d2 / math.sqrt(2)))
    return S * N_d1 - K * math.exp(-r * T) * N_d2

def black_scholes_put(S, K, T, r, sigma):
    """Black-Scholes Put option price"""
    if T <= 0 or sigma <= 0:
        return max(K - S, 0)
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    N_neg_d1 = 0.5 * (1 + math.erf(-d1 / math.sqrt(2)))
    N_neg_d2 = 0.5 * (1 + math.erf(-d2 / math.sqrt(2)))
    return K * math.exp(-r * T) * N_neg_d2 - S * N_neg_d1

def calc_greeks(S, K, T, r, sigma, option_type="CE"):
    """Calculate option Greeks"""
    if T <= 0 or sigma <= 0:
        return {"delta": 1 if option_type == "CE" else -1, "gamma": 0, "theta": 0, "vega": 0}
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    N_d1 = 0.5 * (1 + math.erf(d1 / math.sqrt(2)))
    n_d1 = math.exp(-0.5 * d1 ** 2) / math.sqrt(2 * math.pi)
    
    if option_type == "CE":
        delta = round(N_d1, 4)
    else:
        delta = round(N_d1 - 1, 4)
    gamma = round(n_d1 / (S * sigma * math.sqrt(T)), 6)
    theta = round((-S * n_d1 * sigma / (2 * math.sqrt(T)) - r * K * math.exp(-r * T) * (0.5 * (1 + math.erf(d2 / math.sqrt(2))) if option_type == "CE" else 0.5 * (1 + math.erf(-d2 / math.sqrt(2))))) / 365, 2)
    vega = round(S * n_d1 * math.sqrt(T) / 100, 2)
    return {"delta": delta, "gamma": gamma, "theta": theta, "vega": vega}

def generate_strike_prices(spot_price: float, num_strikes: int = 15, step: float = None) -> List[float]:
    """Generate strike prices around spot price"""
    if step is None:
        if spot_price > 50000:
            step = 500
        elif spot_price > 10000:
            step = 100
        elif spot_price > 1000:
            step = 50
        elif spot_price > 100:
            step = 10
        else:
            step = 5
    
    atm = round(spot_price / step) * step
    strikes = []
    for i in range(-num_strikes, num_strikes + 1):
        strikes.append(atm + i * step)
    return [s for s in strikes if s > 0]

def generate_expiry_dates() -> List[str]:
    """Generate upcoming Thursday expiry dates"""
    today = datetime.now(timezone.utc)
    expiries = []
    d = today
    while len(expiries) < 6:
        d += timedelta(days=1)
        if d.weekday() == 3:  # Thursday
            expiries.append(d.strftime("%Y-%m-%d"))
    return expiries

def build_option_chain(symbol: str, spot_price: float, iv: float = None, expiry_idx: int = 0) -> dict:
    """Build complete option chain for a symbol"""
    if iv is None:
        iv = DEFAULT_IV
    
    expiries = generate_expiry_dates()
    expiry_date = expiries[min(expiry_idx, len(expiries) - 1)]
    expiry_dt = datetime.strptime(expiry_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    T = max((expiry_dt - datetime.now(timezone.utc)).days / 365, 0.001)
    
    strikes = generate_strike_prices(spot_price)
    lot_size = LOT_SIZES.get(symbol, 100)
    
    chain_data = []
    total_ce_oi = 0
    total_pe_oi = 0
    max_pain_strike = strikes[len(strikes) // 2]
    
    for strike in strikes:
        ce_price = round(black_scholes_call(spot_price, strike, T, RISK_FREE_RATE, iv), 2)
        pe_price = round(black_scholes_put(spot_price, strike, T, RISK_FREE_RATE, iv), 2)
        ce_greeks = calc_greeks(spot_price, strike, T, RISK_FREE_RATE, iv, "CE")
        pe_greeks = calc_greeks(spot_price, strike, T, RISK_FREE_RATE, iv, "PE")
        
        # Estimate OI based on distance from ATM
        distance = abs(strike - spot_price) / spot_price
        oi_factor = max(0.1, 1 - distance * 10)
        ce_oi = int(5000 * oi_factor * (1 + 0.3 * (strike < spot_price)))
        pe_oi = int(5000 * oi_factor * (1 + 0.3 * (strike > spot_price)))
        total_ce_oi += ce_oi
        total_pe_oi += pe_oi
        
        itm_ce = strike < spot_price
        itm_pe = strike > spot_price
        
        chain_data.append({
            "strikePrice": strike,
            "CE": {
                "lastPrice": ce_price,
                "openInterest": ce_oi * lot_size,
                "changeinOpenInterest": int(ce_oi * 0.1 * lot_size),
                "impliedVolatility": round(iv * 100 * (1 + distance * 0.5), 2),
                "volume": int(ce_oi * 0.3),
                "bidPrice": round(ce_price * 0.98, 2),
                "askPrice": round(ce_price * 1.02, 2),
                "inTheMoney": itm_ce,
                **ce_greeks,
            },
            "PE": {
                "lastPrice": pe_price,
                "openInterest": pe_oi * lot_size,
                "changeinOpenInterest": int(pe_oi * 0.1 * lot_size),
                "impliedVolatility": round(iv * 100 * (1 + distance * 0.5), 2),
                "volume": int(pe_oi * 0.3),
                "bidPrice": round(pe_price * 0.98, 2),
                "askPrice": round(pe_price * 1.02, 2),
                "inTheMoney": itm_pe,
                **pe_greeks,
            },
        })
    
    pcr = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi > 0 else 1.0
    
    return {
        "symbol": symbol,
        "underlyingValue": spot_price,
        "expiryDate": expiry_date,
        "expiryDates": expiries,
        "lotSize": lot_size,
        "totalCEOI": total_ce_oi * lot_size,
        "totalPEOI": total_pe_oi * lot_size,
        "pcr": pcr,
        "pcrLabel": "Bullish" if pcr > 1.2 else "Bearish" if pcr < 0.8 else "Neutral",
        "maxPainStrike": max_pain_strike,
        "atmStrike": round(spot_price / (strikes[1] - strikes[0]) if len(strikes) > 1 else 1) * (strikes[1] - strikes[0]) if len(strikes) > 1 else spot_price,
        "iv": round(iv * 100, 2),
        "data": chain_data,
        "dataSource": "estimated_black_scholes",
        "disclaimer": "Option prices are estimated using Black-Scholes model. Actual NSE prices may differ.",
    }

def get_fno_list():
    return {"stocks": FNO_STOCKS, "indices": FNO_INDICES, "lot_sizes": LOT_SIZES}
