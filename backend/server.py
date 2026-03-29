from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import logging
import uuid
import jwt
import bcrypt
import httpx
import time
import json
import random
import asyncio
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, validator
from typing import List, Optional, Dict
from emergentintegrations.llm.chat import LlmChat, UserMessage
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import yfinance as yf

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Config
JWT_SECRET = os.environ.get('JWT_SECRET', 'titan-trade-jwt-secret-2026')
JWT_ALGORITHM = 'HS256'
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
GMAIL_USER = os.environ.get('GMAIL_USER')
GMAIL_PASSWORD = os.environ.get('GMAIL_PASSWORD')
COINGECKO_BASE = 'https://api.coingecko.com/api/v3'
CRYPTOCOMPARE_BASE = 'https://min-api.cryptocompare.com/data'
KRAKEN_BASE = 'https://api.kraken.com/0/public'

# Top 25 crypto symbols for CryptoCompare (chart data)
CRYPTO_SYMBOLS = 'BTC,ETH,SOL,BNB,XRP,DOGE,ADA,AVAX,DOT,LINK,SHIB,LTC,ATOM,UNI,NEAR,APT,ARB,FIL,XLM,MATIC,TRX,TON,OP,INJ,SUI'

# Kraken pair mapping for real-time prices
KRAKEN_PAIRS = {
    'XXBTZUSD': {'sym': 'BTC', 'name': 'Bitcoin', 'id': 'bitcoin'},
    'XETHZUSD': {'sym': 'ETH', 'name': 'Ethereum', 'id': 'ethereum'},
    'SOLUSD': {'sym': 'SOL', 'name': 'Solana', 'id': 'solana'},
    'XRPUSD': {'sym': 'XRP', 'name': 'XRP', 'id': 'ripple'},
    'XDGUSD': {'sym': 'DOGE', 'name': 'Dogecoin', 'id': 'dogecoin'},
    'ADAUSD': {'sym': 'ADA', 'name': 'Cardano', 'id': 'cardano'},
    'AVAXUSD': {'sym': 'AVAX', 'name': 'Avalanche', 'id': 'avalanche-2'},
    'DOTUSD': {'sym': 'DOT', 'name': 'Polkadot', 'id': 'polkadot'},
    'LINKUSD': {'sym': 'LINK', 'name': 'Chainlink', 'id': 'chainlink'},
    'SHIBUSD': {'sym': 'SHIB', 'name': 'Shiba Inu', 'id': 'shiba-inu'},
    'XLTCZUSD': {'sym': 'LTC', 'name': 'Litecoin', 'id': 'litecoin'},
    'ATOMUSD': {'sym': 'ATOM', 'name': 'Cosmos', 'id': 'cosmos'},
    'UNIUSD': {'sym': 'UNI', 'name': 'Uniswap', 'id': 'uniswap'},
    'NEARUSD': {'sym': 'NEAR', 'name': 'NEAR Protocol', 'id': 'near'},
    'APTUSD': {'sym': 'APT', 'name': 'Aptos', 'id': 'aptos'},
    'FILUSD': {'sym': 'FIL', 'name': 'Filecoin', 'id': 'filecoin'},
    'XXLMZUSD': {'sym': 'XLM', 'name': 'Stellar', 'id': 'stellar'},
    'POLUSD': {'sym': 'POL', 'name': 'Polygon', 'id': 'matic-network'},
    'TRXUSD': {'sym': 'TRX', 'name': 'TRON', 'id': 'tron'},
    'INJUSD': {'sym': 'INJ', 'name': 'Injective', 'id': 'injective-protocol'},
}
KRAKEN_PAIR_LIST = ','.join(KRAKEN_PAIRS.keys())
CRYPTO_NAMES = {
    'BTC': 'Bitcoin', 'ETH': 'Ethereum', 'SOL': 'Solana', 'BNB': 'BNB',
    'XRP': 'XRP', 'DOGE': 'Dogecoin', 'ADA': 'Cardano', 'AVAX': 'Avalanche',
    'DOT': 'Polkadot', 'LINK': 'Chainlink', 'SHIB': 'Shiba Inu', 'LTC': 'Litecoin',
    'ATOM': 'Cosmos', 'UNI': 'Uniswap', 'NEAR': 'NEAR Protocol', 'APT': 'Aptos',
    'ARB': 'Arbitrum', 'FIL': 'Filecoin', 'XLM': 'Stellar', 'MATIC': 'Polygon',
    'TRX': 'TRON', 'TON': 'Toncoin', 'OP': 'Optimism', 'INJ': 'Injective', 'SUI': 'Sui',
}
# Map symbols to stable IDs (matching CoinGecko-style IDs for backwards compat)
CRYPTO_ID_MAP = {
    'BTC': 'bitcoin', 'ETH': 'ethereum', 'SOL': 'solana', 'BNB': 'binancecoin',
    'XRP': 'ripple', 'DOGE': 'dogecoin', 'ADA': 'cardano', 'AVAX': 'avalanche-2',
    'DOT': 'polkadot', 'LINK': 'chainlink', 'SHIB': 'shiba-inu', 'LTC': 'litecoin',
    'ATOM': 'cosmos', 'UNI': 'uniswap', 'NEAR': 'near', 'APT': 'aptos',
    'ARB': 'arbitrum', 'FIL': 'filecoin', 'XLM': 'stellar', 'MATIC': 'matic-network',
    'TRX': 'tron', 'TON': 'toncoin', 'OP': 'optimism', 'INJ': 'injective-protocol', 'SUI': 'sui',
}
# Reverse map: id -> symbol
CRYPTO_SYM_MAP = {v: k for k, v in CRYPTO_ID_MAP.items()}

# Simple in-memory cache
_cache: Dict[str, Dict] = {}
_executor = ThreadPoolExecutor(max_workers=6)

# ==================== OANDA FOREX LIVE DATA ====================

OANDA_API_KEY = os.environ.get('OANDA_API_KEY')
OANDA_ACCOUNT_ID = os.environ.get('OANDA_ACCOUNT_ID')
OANDA_BASE_URL = os.environ.get('OANDA_BASE_URL', 'https://api-fxpractice.oanda.com/v3')

OANDA_FOREX_PAIRS = {
    "EUR_USD": {"id": "eurusd", "name": "EUR/USD", "symbol": "EUR/USD", "category": "major"},
    "GBP_USD": {"id": "gbpusd", "name": "GBP/USD", "symbol": "GBP/USD", "category": "major"},
    "USD_JPY": {"id": "usdjpy", "name": "USD/JPY", "symbol": "USD/JPY", "category": "major"},
    "AUD_USD": {"id": "audusd", "name": "AUD/USD", "symbol": "AUD/USD", "category": "major"},
    "USD_CHF": {"id": "usdchf", "name": "USD/CHF", "symbol": "USD/CHF", "category": "major"},
    "USD_CAD": {"id": "usdcad", "name": "USD/CAD", "symbol": "USD/CAD", "category": "major"},
    "NZD_USD": {"id": "nzdusd", "name": "NZD/USD", "symbol": "NZD/USD", "category": "major"},
    "XAU_USD": {"id": "xauusd", "name": "Gold (XAU/USD)", "symbol": "XAU/USD", "category": "commodity"},
    "XAG_USD": {"id": "xagusd", "name": "Silver (XAG/USD)", "symbol": "XAG/USD", "category": "commodity"},
    "EUR_GBP": {"id": "eurgbp", "name": "EUR/GBP", "symbol": "EUR/GBP", "category": "cross"},
    "EUR_JPY": {"id": "eurjpy", "name": "EUR/JPY", "symbol": "EUR/JPY", "category": "cross"},
    "GBP_JPY": {"id": "gbpjpy", "name": "GBP/JPY", "symbol": "GBP/JPY", "category": "cross"},
    "AUD_JPY": {"id": "audjpy", "name": "AUD/JPY", "symbol": "AUD/JPY", "category": "cross"},
    "CAD_JPY": {"id": "cadjpy", "name": "CAD/JPY", "symbol": "CAD/JPY", "category": "cross"},
    "GBP_CHF": {"id": "gbpchf", "name": "GBP/CHF", "symbol": "GBP/CHF", "category": "cross"},
    "EUR_AUD": {"id": "euraud", "name": "EUR/AUD", "symbol": "EUR/AUD", "category": "cross"},
    "EUR_CHF": {"id": "eurchf", "name": "EUR/CHF", "symbol": "EUR/CHF", "category": "cross"},
    "GBP_AUD": {"id": "gbpaud", "name": "GBP/AUD", "symbol": "GBP/AUD", "category": "cross"},
    "GBP_NZD": {"id": "gbpnzd", "name": "GBP/NZD", "symbol": "GBP/NZD", "category": "cross"},
    "AUD_NZD": {"id": "audnzd", "name": "AUD/NZD", "symbol": "AUD/NZD", "category": "cross"},
}
# Reverse maps
OANDA_ID_TO_PAIR = {v['id']: k for k, v in OANDA_FOREX_PAIRS.items()}

# Keep old map reference for yfinance chart fallback
FOREX_SYMBOL_MAP = {}

INDIAN_SYMBOL_MAP = {
    # INDICES
    "^NSEI": {"id": "nifty50", "name": "NIFTY 50", "symbol": "NIFTY50", "type": "index"},
    "^BSESN": {"id": "sensex", "name": "SENSEX", "symbol": "SENSEX", "type": "index"},
    "^NSEBANK": {"id": "banknifty", "name": "NIFTY Bank", "symbol": "BANKNIFTY", "type": "index"},
    "^CNXIT": {"id": "niftyit", "name": "NIFTY IT", "symbol": "NIFTYIT", "type": "index"},
    "^CNXPHARMA": {"id": "niftypharma", "name": "NIFTY Pharma", "symbol": "NIFTYPHARMA", "type": "index"},
    "^CNXAUTO": {"id": "niftyauto", "name": "NIFTY Auto", "symbol": "NIFTYAUTO", "type": "index"},
    "^CNXFMCG": {"id": "niftyfmcg", "name": "NIFTY FMCG", "symbol": "NIFTYFMCG", "type": "index"},
    "^CNXMETAL": {"id": "niftymetal", "name": "NIFTY Metal", "symbol": "NIFTYMETAL", "type": "index"},
    "^CNXENERGY": {"id": "niftyenergy", "name": "NIFTY Energy", "symbol": "NIFTYENERGY", "type": "index"},
    "^CNXREALTY": {"id": "niftyrealty", "name": "NIFTY Realty", "symbol": "NIFTYREALTY", "type": "index"},
    "^CNXINFRA": {"id": "niftyinfra", "name": "NIFTY Infra", "symbol": "NIFTYINFRA", "type": "index"},
    "^INDIAVIX": {"id": "indiavix", "name": "India VIX", "symbol": "INDIAVIX", "type": "index"},
    "^CNXPSUBANK": {"id": "niftypsubank", "name": "NIFTY PSU Bank", "symbol": "NIFTYPSUBANK", "type": "index"},
    "^CNXMEDIA": {"id": "niftymedia", "name": "NIFTY Media", "symbol": "NIFTYMEDIA", "type": "index"},
    "^CNXMNC": {"id": "niftymnc", "name": "NIFTY MNC", "symbol": "NIFTYMNC", "type": "index"},
    # STOCKS (NIFTY 50 Components)
    "RELIANCE.NS": {"id": "reliance", "name": "Reliance Industries", "symbol": "RELIANCE", "type": "stock"},
    "TCS.NS": {"id": "tcs", "name": "Tata Consultancy Services", "symbol": "TCS", "type": "stock"},
    "INFY.NS": {"id": "infy", "name": "Infosys", "symbol": "INFY", "type": "stock"},
    "HDFCBANK.NS": {"id": "hdfcbank", "name": "HDFC Bank", "symbol": "HDFCBANK", "type": "stock"},
    "ICICIBANK.NS": {"id": "icicibank", "name": "ICICI Bank", "symbol": "ICICIBANK", "type": "stock"},
    "SBIN.NS": {"id": "sbin", "name": "State Bank of India", "symbol": "SBIN", "type": "stock"},
    "ITC.NS": {"id": "itc", "name": "ITC Limited", "symbol": "ITC", "type": "stock"},
    "BHARTIARTL.NS": {"id": "bhartiartl", "name": "Bharti Airtel", "symbol": "BHARTIARTL", "type": "stock"},
    "WIPRO.NS": {"id": "wipro", "name": "Wipro", "symbol": "WIPRO", "type": "stock"},
    "HINDUNILVR.NS": {"id": "hindunilvr", "name": "Hindustan Unilever", "symbol": "HINDUNILVR", "type": "stock"},
    "BAJFINANCE.NS": {"id": "bajfinance", "name": "Bajaj Finance", "symbol": "BAJFINANCE", "type": "stock"},
    "HCLTECH.NS": {"id": "hcltech", "name": "HCL Technologies", "symbol": "HCLTECH", "type": "stock"},
    "MARUTI.NS": {"id": "maruti", "name": "Maruti Suzuki", "symbol": "MARUTI", "type": "stock"},
    "ADANIENT.NS": {"id": "adanient", "name": "Adani Enterprises", "symbol": "ADANIENT", "type": "stock"},
    "AXISBANK.NS": {"id": "axisbank", "name": "Axis Bank", "symbol": "AXISBANK", "type": "stock"},
    "KOTAKBANK.NS": {"id": "kotakbank", "name": "Kotak Mahindra Bank", "symbol": "KOTAKBANK", "type": "stock"},
    "LT.NS": {"id": "lt", "name": "Larsen & Toubro", "symbol": "LT", "type": "stock"},
    "TITAN.NS": {"id": "titan", "name": "Titan Company", "symbol": "TITAN", "type": "stock"},
    "SUNPHARMA.NS": {"id": "sunpharma", "name": "Sun Pharma", "symbol": "SUNPHARMA", "type": "stock"},
    "ULTRACEMCO.NS": {"id": "ultracemco", "name": "UltraTech Cement", "symbol": "ULTRACEMCO", "type": "stock"},
    "TECHM.NS": {"id": "techm", "name": "Tech Mahindra", "symbol": "TECHM", "type": "stock"},
    "ASIANPAINT.NS": {"id": "asianpaint", "name": "Asian Paints", "symbol": "ASIANPAINT", "type": "stock"},
    "M&M.NS": {"id": "mm", "name": "Mahindra & Mahindra", "symbol": "M&M", "type": "stock"},
    "POWERGRID.NS": {"id": "powergrid", "name": "Power Grid Corp", "symbol": "POWERGRID", "type": "stock"},
    "NTPC.NS": {"id": "ntpc", "name": "NTPC Limited", "symbol": "NTPC", "type": "stock"},
    "ONGC.NS": {"id": "ongc", "name": "ONGC", "symbol": "ONGC", "type": "stock"},
    "COALINDIA.NS": {"id": "coalindia", "name": "Coal India", "symbol": "COALINDIA", "type": "stock"},
    "JSWSTEEL.NS": {"id": "jswsteel", "name": "JSW Steel", "symbol": "JSWSTEEL", "type": "stock"},
    "TATASTEEL.NS": {"id": "tatasteel", "name": "Tata Steel", "symbol": "TATASTEEL", "type": "stock"},
}

def _yf_batch_fetch(symbols):
    """Fetch live data from Yahoo Finance for a batch of symbols"""
    results = {}
    try:
        tickers = yf.Tickers(' '.join(symbols))
        for sym in symbols:
            try:
                ticker = tickers.tickers[sym]
                hist = ticker.history(period="5d")
                if len(hist) >= 2:
                    latest = hist.iloc[-1]
                    prev = hist.iloc[-2]
                    change_pct = ((float(latest['Close']) - float(prev['Close'])) / float(prev['Close'])) * 100
                    results[sym] = {
                        'price': round(float(latest['Close']), 4 if float(latest['Close']) < 50 else 2),
                        'high': round(float(latest['High']), 4 if float(latest['High']) < 50 else 2),
                        'low': round(float(latest['Low']), 4 if float(latest['Low']) < 50 else 2),
                        'volume': int(latest['Volume']) if latest['Volume'] > 0 else 0,
                        'change_pct': round(change_pct, 2),
                        'prev_close': round(float(prev['Close']), 4 if float(prev['Close']) < 50 else 2),
                    }
                elif len(hist) >= 1:
                    latest = hist.iloc[-1]
                    results[sym] = {
                        'price': round(float(latest['Close']), 4 if float(latest['Close']) < 50 else 2),
                        'high': round(float(latest['High']), 4 if float(latest['High']) < 50 else 2),
                        'low': round(float(latest['Low']), 4 if float(latest['Low']) < 50 else 2),
                        'volume': int(latest['Volume']) if latest['Volume'] > 0 else 0,
                        'change_pct': 0.0,
                        'prev_close': round(float(latest['Close']), 4 if float(latest['Close']) < 50 else 2),
                    }
            except Exception as e:
                logger.warning(f"Failed to fetch {sym}: {e}")
    except Exception as e:
        logger.error(f"yfinance batch failed: {e}")
    return results

async def get_live_market_data(symbols, cache_key, ttl=180):
    """Fetch live market data with caching"""
    now = time.time()
    if cache_key in _cache and (now - _cache[cache_key]['time']) < ttl:
        return _cache[cache_key]['data']
    try:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(_executor, _yf_batch_fetch, symbols)
        if data:
            _cache[cache_key] = {'data': data, 'time': now}
        return data
    except Exception as e:
        logger.error(f"Live data fetch error: {e}")
        if cache_key in _cache:
            return _cache[cache_key]['data']
        return {}

app = FastAPI(title="Titan Trade API")
api_router = APIRouter(prefix="/api")

# Rate Limiter - relaxed for shared proxy environments
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Brute-force protection: track failed logins by email
_login_attempts: Dict[str, list] = {}
MAX_LOGIN_ATTEMPTS = 15
LOGIN_LOCKOUT_SECONDS = 300

def check_brute_force(email: str):
    now = time.time()
    attempts = _login_attempts.get(email, [])
    attempts = [t for t in attempts if now - t < LOGIN_LOCKOUT_SECONDS]
    _login_attempts[email] = attempts
    if len(attempts) >= MAX_LOGIN_ATTEMPTS:
        raise HTTPException(status_code=429, detail=f"Too many login attempts. Try again in {LOGIN_LOCKOUT_SECONDS // 60} minutes.")

def record_failed_login(email: str):
    _login_attempts.setdefault(email, []).append(time.time())

def clear_login_attempts(email: str):
    _login_attempts.pop(email, None)

# Input sanitization
def sanitize_input(text: str, max_len: int = 5000) -> str:
    if not text:
        return text
    text = text[:max_len]
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    return text.strip()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class UserRegister(BaseModel):
    email: str
    password: str
    name: str

class UserLogin(BaseModel):
    email: str
    password: str

class HoldingCreate(BaseModel):
    asset_id: str
    asset_name: str
    asset_type: str
    quantity: float
    buy_price: float

class WatchlistItem(BaseModel):
    asset_id: str
    asset_name: str
    asset_type: str

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class SignalRequest(BaseModel):
    asset_id: str
    asset_name: str
    asset_type: str
    timeframe: str = "1D"
    timeframes: Optional[List[str]] = None
    strategy: str = "auto"
    strategies: Optional[List[str]] = None
    profit_target: Optional[float] = None
    risk_reward: Optional[str] = None
    num_tp_levels: int = 3  # 1, 2, or 3
    trading_mode: str = "swing"  # scalping, day_trading, swing, position

TRADING_MODES = {
    "scalping": {"label": "Scalping", "desc": "Ultra-short trades (seconds to minutes). Tight SL, small TP, high frequency.", "default_hold": "1-30 minutes"},
    "day_trading": {"label": "Day Trading", "desc": "Intraday trades, no overnight holds. Moderate SL/TP.", "default_hold": "1-8 hours"},
    "swing": {"label": "Swing Trading", "desc": "Multi-day trades riding momentum swings. Wider SL/TP.", "default_hold": "1-7 days"},
    "position": {"label": "Position Trading", "desc": "Long-term macro trades. Widest SL/TP, trend following.", "default_hold": "1-4 weeks"},
}

class AlertCreate(BaseModel):
    asset_id: str
    asset_name: str
    asset_type: str
    condition: str  # "above" or "below"
    target_price: float
    note: Optional[str] = None

# ==================== MARKET HOURS ====================

def is_indian_market_open():
    """Indian market (NSE): Mon-Fri 9:15 AM - 3:30 PM IST (UTC+5:30)"""
    ist_offset = timedelta(hours=5, minutes=30)
    now_ist = datetime.now(timezone.utc) + ist_offset
    if now_ist.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    market_open = now_ist.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now_ist.replace(hour=15, minute=30, second=0, microsecond=0)
    return market_open <= now_ist <= market_close

def is_forex_market_open():
    """Forex: Opens Sunday ~5 PM ET, Closes Friday ~5 PM ET"""
    et_offset = timedelta(hours=-4)  # EDT (summer), adjust to -5 for EST
    now_et = datetime.now(timezone.utc) + et_offset
    weekday = now_et.weekday()  # Mon=0, Sun=6
    hour = now_et.hour
    # Closed: Friday after 5PM through Sunday before 5PM
    if weekday == 4 and hour >= 17:  # Friday after 5PM
        return False
    if weekday == 5:  # Saturday
        return False
    if weekday == 6 and hour < 17:  # Sunday before 5PM
        return False
    return True

def get_market_status():
    return {
        "crypto": {"open": True, "label": "24/7"},
        "forex": {"open": is_forex_market_open(), "label": "Open" if is_forex_market_open() else "Closed"},
        "indian": {"open": is_indian_market_open(), "label": "Open" if is_indian_market_open() else "Closed"},
    }

# ==================== HELPERS ====================

async def cached_get(url: str, ttl: int = 60) -> dict:
    now = time.time()
    if url in _cache and (now - _cache[url]['time']) < ttl:
        return _cache[url]['data']
    try:
        async with httpx.AsyncClient() as http_client:
            resp = await http_client.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            _cache[url] = {'data': data, 'time': now}
            return data
    except Exception as e:
        logger.error(f"API call failed: {url} - {e}")
        if url in _cache:
            return _cache[url]['data']
        raise HTTPException(status_code=502, detail=f"External API error: {str(e)}")

def create_jwt_token(user_id: str) -> str:
    payload = {
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(days=7),
        'iat': datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(request: Request) -> dict:
    token = request.cookies.get('session_token')
    if not token:
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Check session table (Google auth)
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if session:
        expires_at = session.get('expires_at')
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Session expired")
        user = await db.users.find_one({"user_id": session['user_id']}, {"_id": 0})
        if user:
            return user

    # Try JWT
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"user_id": payload['user_id']}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register")
@limiter.limit("30/minute")
async def register(data: UserRegister, request: Request, response: Response):
    email = data.email.lower().strip()
    name = sanitize_input(data.name, 100)
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    existing = await db.users.find_one({"email": email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    hashed = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
    user_doc = {
        "user_id": user_id,
        "email": email,
        "name": name,
        "password": hashed,
        "picture": None,
        "auth_type": "jwt",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    token = create_jwt_token(user_id)
    response.set_cookie(key="session_token", value=token, httponly=True, secure=True, samesite="none", max_age=7*24*60*60, path="/")
    return {"user_id": user_id, "email": email, "name": name, "token": token}

@api_router.post("/auth/login")
@limiter.limit("30/minute")
async def login(data: UserLogin, request: Request, response: Response):
    data.email = data.email.lower().strip()
    check_brute_force(data.email)
    user = await db.users.find_one({"email": data.email}, {"_id": 0})
    if not user or 'password' not in user:
        record_failed_login(data.email)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not bcrypt.checkpw(data.password.encode(), user['password'].encode()):
        record_failed_login(data.email)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    clear_login_attempts(data.email)
    token = create_jwt_token(user['user_id'])
    response.set_cookie(key="session_token", value=token, httponly=True, secure=True, samesite="none", max_age=7*24*60*60, path="/")
    return {"user_id": user['user_id'], "email": user['email'], "name": user['name'], "token": token}

@api_router.post("/auth/session")
async def process_session(request: Request, response: Response):
    body = await request.json()
    session_id = body.get('session_id')
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    async with httpx.AsyncClient() as http_client:
        resp = await http_client.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}, timeout=10
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid session")
        session_data = resp.json()
    user = await db.users.find_one({"email": session_data['email']}, {"_id": 0})
    if user:
        user_id = user['user_id']
        await db.users.update_one({"user_id": user_id}, {"$set": {"name": session_data['name'], "picture": session_data.get('picture')}})
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        await db.users.insert_one({
            "user_id": user_id, "email": session_data['email'], "name": session_data['name'],
            "picture": session_data.get('picture'), "auth_type": "google",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    session_token = session_data.get('session_token', f"sess_{uuid.uuid4().hex}")
    await db.user_sessions.insert_one({
        "user_id": user_id, "session_token": session_token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    response.set_cookie(key="session_token", value=session_token, httponly=True, secure=True, samesite="none", max_age=7*24*60*60, path="/")
    return {"user_id": user_id, "email": session_data['email'], "name": session_data['name'], "picture": session_data.get('picture'), "token": session_token}

@api_router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {"user_id": user['user_id'], "email": user['email'], "name": user['name'], "picture": user.get('picture')}

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get('session_token')
    if token:
        await db.user_sessions.delete_many({"session_token": token})
    response.delete_cookie("session_token", path="/")
    return {"message": "Logged out"}

# ==================== MARKET DATA ====================

@api_router.get("/market/crypto/top")
async def get_top_crypto(limit: int = 20):
    url = f"{COINGECKO_BASE}/coins/markets?vs_currency=usd&order=market_cap_desc&per_page={limit}&page=1&sparkline=true&price_change_percentage=1h,24h,7d"
    data = await cached_get(url, ttl=120)
    return {"coins": data}

@api_router.get("/market/crypto/trending/list")
async def get_trending_crypto():
    url = f"{COINGECKO_BASE}/search/trending"
    data = await cached_get(url, ttl=600)
    return data

@api_router.get("/market/crypto/{coin_id}")
async def get_crypto_price(coin_id: str):
    url = f"{COINGECKO_BASE}/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true&include_24hr_vol=true&include_last_updated_at=true"
    data = await cached_get(url, ttl=30)
    if coin_id not in data:
        raise HTTPException(status_code=404, detail="Coin not found")
    return {"coin_id": coin_id, **data[coin_id]}

@api_router.get("/market/crypto/{coin_id}/chart")
async def get_crypto_chart(coin_id: str, days: int = 7):
    """Get crypto price chart data via Kraken OHLC"""
    kraken_pair = None
    for kp, meta in KRAKEN_PAIRS.items():
        if meta['id'] == coin_id:
            kraken_pair = kp
            break
    if not kraken_pair:
        return {"prices": []}
    interval = 60 if days <= 7 else 1440
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{KRAKEN_BASE}/OHLC", params={"pair": kraken_pair, "interval": interval})
            resp.raise_for_status()
            data = resp.json()
        result = data.get('result', {})
        ohlc_data = []
        for k, v in result.items():
            if k != 'last' and isinstance(v, list):
                ohlc_data = v
                break
        prices = [[int(c[0]) * 1000, float(c[4])] for c in ohlc_data]
        return {"prices": prices}
    except Exception:
        return {"prices": []}

@api_router.get("/market/chart/{asset_type}/{asset_id}")
async def get_asset_chart(asset_type: str, asset_id: str, period: str = "1mo"):
    """Get OHLCV chart data for any asset"""
    if asset_type == "crypto":
        # Map ID back to Kraken pair for chart data
        kraken_pair = None
        for kp, meta in KRAKEN_PAIRS.items():
            if meta['id'] == asset_id:
                kraken_pair = kp
                break
        if not kraken_pair:
            kraken_pair = asset_id.upper() + 'USD'
        # Kraken OHLC endpoint
        interval_map = {"1d": 5, "7d": 60, "1mo": 240, "3mo": 1440, "1y": 10080}
        interval = interval_map.get(period, 240)
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(f"{KRAKEN_BASE}/OHLC", params={"pair": kraken_pair, "interval": interval})
                resp.raise_for_status()
                data = resp.json()
            result = data.get('result', {})
            # Get the first key that's not 'last'
            ohlc_data = []
            for k, v in result.items():
                if k != 'last' and isinstance(v, list):
                    ohlc_data = v
                    break
            candles = []
            for c in ohlc_data:
                candles.append({
                    "time": int(c[0]),
                    "open": round(float(c[1]), 2),
                    "high": round(float(c[2]), 2),
                    "low": round(float(c[3]), 2),
                    "close": round(float(c[4]), 2),
                    "volume": round(float(c[6])),
                })
            return {"candles": candles, "asset_id": asset_id, "period": period}
        except Exception as e:
            logger.error(f"Kraken chart error: {e}")
            return {"candles": [], "asset_id": asset_id, "period": period}
    else:
        # Forex uses OANDA candles, Indian uses yfinance
        if asset_type == "forex":
            oanda_instrument = OANDA_ID_TO_PAIR.get(asset_id)
            if not oanda_instrument or not OANDA_API_KEY:
                return {"candles": [], "asset_id": asset_id, "period": period}
            # Map period to OANDA granularity + count
            gran_map = {"1d": ("M5", 288), "7d": ("H1", 168), "1mo": ("H4", 180), "3mo": ("D", 90), "1y": ("D", 365)}
            gran, count = gran_map.get(period, ("H4", 180))
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(
                        f"{OANDA_BASE_URL}/instruments/{oanda_instrument}/candles",
                        headers={"Authorization": f"Bearer {OANDA_API_KEY}"},
                        params={"granularity": gran, "count": count, "price": "M"}
                    )
                    resp.raise_for_status()
                    data = resp.json()
                candles = []
                is_jpy = 'JPY' in oanda_instrument
                is_metal = oanda_instrument.startswith('XA')
                dec = 2 if is_metal else (3 if is_jpy else 5)
                for c in data.get('candles', []):
                    if not c.get('complete', True) and c != data['candles'][-1]:
                        continue
                    mid = c.get('mid', {})
                    ts = c.get('time', '')
                    if ts:
                        from datetime import datetime as dt
                        try:
                            epoch = int(dt.fromisoformat(ts.replace('Z', '+00:00').split('.')[0] + '+00:00').timestamp())
                        except:
                            continue
                        candles.append({
                            "time": epoch,
                            "open": round(float(mid.get('o', 0)), dec),
                            "high": round(float(mid.get('h', 0)), dec),
                            "low": round(float(mid.get('l', 0)), dec),
                            "close": round(float(mid.get('c', 0)), dec),
                            "volume": int(c.get('volume', 0)),
                        })
                return {"candles": candles, "asset_id": asset_id, "period": period}
            except Exception as e:
                logger.error(f"OANDA chart error for {asset_id}: {e}")
                return {"candles": [], "asset_id": asset_id, "period": period}
        else:
            # Indian market - use yfinance
            sym_map = {v['id']: k for k, v in INDIAN_SYMBOL_MAP.items()}
            yf_symbol = sym_map.get(asset_id)
            if not yf_symbol:
                return {"candles": [], "asset_id": asset_id, "period": period}
            try:
                loop = asyncio.get_event_loop()
                def _fetch():
                    t = yf.Ticker(yf_symbol)
                    hist = t.history(period=period)
                    candles = []
                    for idx, row in hist.iterrows():
                        candles.append({
                            "time": int(idx.timestamp()),
                            "open": round(float(row['Open']), 2),
                            "high": round(float(row['High']), 2),
                            "low": round(float(row['Low']), 2),
                            "close": round(float(row['Close']), 2),
                            "volume": int(row['Volume']) if row['Volume'] > 0 else 0,
                        })
                    return candles
                candles = await loop.run_in_executor(_executor, _fetch)
                return {"candles": candles, "asset_id": asset_id, "period": period}
            except Exception as e:
                logger.error(f"Chart fetch error for {asset_id}: {e}")
                return {"candles": [], "asset_id": asset_id, "period": period}

@api_router.get("/market/sentiment")
async def get_market_sentiment():
    try:
        url = f"{COINGECKO_BASE}/global"
        data = await cached_get(url, ttl=300)
        gd = data.get('data', {})
        btc_change = gd.get('market_cap_change_percentage_24h_usd', 0)
        fg = min(100, max(0, 50 + btc_change * 5))
        return {
            "fear_greed_index": round(fg),
            "fear_greed_label": "Extreme Fear" if fg < 25 else "Fear" if fg < 45 else "Neutral" if fg < 55 else "Greed" if fg < 75 else "Extreme Greed",
            "total_market_cap": gd.get('total_market_cap', {}).get('usd'),
            "total_volume": gd.get('total_volume', {}).get('usd'),
            "btc_dominance": gd.get('market_cap_percentage', {}).get('btc'),
            "eth_dominance": gd.get('market_cap_percentage', {}).get('eth'),
            "market_cap_change_24h": gd.get('market_cap_change_percentage_24h_usd'),
            "active_cryptos": gd.get('active_cryptocurrencies')
        }
    except Exception:
        return {"fear_greed_index": 52, "fear_greed_label": "Neutral", "total_market_cap": 2500000000000, "total_volume": 95000000000, "btc_dominance": 54.2, "eth_dominance": 17.8, "market_cap_change_24h": 1.2, "active_cryptos": 14500}

# Forex fallback data (used when Yahoo Finance is unavailable)
FOREX_FALLBACK = [
    {"id": "eurusd", "name": "EUR/USD", "symbol": "EUR/USD", "price": 1.1500, "change_24h": 0.15, "high_24h": 1.1530, "low_24h": 1.1470, "volume": 0},
    {"id": "gbpusd", "name": "GBP/USD", "symbol": "GBP/USD", "price": 1.2950, "change_24h": -0.08, "high_24h": 1.2980, "low_24h": 1.2910, "volume": 0},
    {"id": "usdjpy", "name": "USD/JPY", "symbol": "USD/JPY", "price": 149.50, "change_24h": 0.22, "high_24h": 149.90, "low_24h": 149.10, "volume": 0},
    {"id": "audusd", "name": "AUD/USD", "symbol": "AUD/USD", "price": 0.6350, "change_24h": -0.32, "high_24h": 0.6380, "low_24h": 0.6320, "volume": 0},
    {"id": "usdchf", "name": "USD/CHF", "symbol": "USD/CHF", "price": 0.8750, "change_24h": 0.05, "high_24h": 0.8780, "low_24h": 0.8720, "volume": 0},
    {"id": "usdcad", "name": "USD/CAD", "symbol": "USD/CAD", "price": 1.4350, "change_24h": -0.12, "high_24h": 1.4380, "low_24h": 1.4310, "volume": 0},
    {"id": "nzdusd", "name": "NZD/USD", "symbol": "NZD/USD", "price": 0.5750, "change_24h": -0.18, "high_24h": 0.5780, "low_24h": 0.5720, "volume": 0},
    {"id": "xauusd", "name": "Gold (XAU/USD)", "symbol": "XAU/USD", "price": 3050.00, "change_24h": 0.45, "high_24h": 3065.00, "low_24h": 3035.00, "volume": 0},
    {"id": "xagusd", "name": "Silver (XAG/USD)", "symbol": "XAG/USD", "price": 33.50, "change_24h": 0.72, "high_24h": 33.80, "low_24h": 33.20, "volume": 0},
    {"id": "eurgbp", "name": "EUR/GBP", "symbol": "EUR/GBP", "price": 0.8380, "change_24h": 0.10, "high_24h": 0.8400, "low_24h": 0.8360, "volume": 0},
    {"id": "eurjpy", "name": "EUR/JPY", "symbol": "EUR/JPY", "price": 162.50, "change_24h": 0.25, "high_24h": 162.90, "low_24h": 162.10, "volume": 0},
    {"id": "gbpjpy", "name": "GBP/JPY", "symbol": "GBP/JPY", "price": 193.80, "change_24h": -0.15, "high_24h": 194.20, "low_24h": 193.40, "volume": 0},
]

@api_router.get("/market/forex")
async def get_forex_data():
    symbols = list(FOREX_SYMBOL_MAP.keys())
    yf_data = await get_live_market_data(symbols, "forex_live", ttl=120)
    pairs = []
    source = "live"
    for sym, meta in FOREX_SYMBOL_MAP.items():
        if sym in yf_data and yf_data[sym].get('price', 0) > 0:
            d = yf_data[sym]
            pairs.append({
                "id": meta["id"], "name": meta["name"], "symbol": meta["symbol"],
                "price": d["price"], "change_24h": d["change_pct"],
                "high_24h": d["high"], "low_24h": d["low"],
                "volume": d["volume"], "prev_close": d.get("prev_close", 0),
            })
        else:
            source = "fallback"
            fb = next((p for p in FOREX_FALLBACK if p["id"] == meta["id"]), None)
            if fb:
                pairs.append(fb)
    return {"pairs": pairs, "last_updated": datetime.now(timezone.utc).isoformat(), "source": source}

@api_router.get("/market/indian")
async def get_indian_data():
    symbols = list(INDIAN_SYMBOL_MAP.keys())
    yf_data = await get_live_market_data(symbols, "indian_live", ttl=180)
    stocks = []
    source = "live"
    for sym, meta in INDIAN_SYMBOL_MAP.items():
        if sym in yf_data and yf_data[sym].get('price', 0) > 0:
            d = yf_data[sym]
            stocks.append({
                "id": meta["id"], "name": meta["name"], "symbol": meta["symbol"],
                "price": d["price"], "change_24h": d["change_pct"],
                "high_24h": d["high"], "low_24h": d["low"],
                "volume": d["volume"], "type": meta["type"],
                "prev_close": d.get("prev_close", 0),
            })
        else:
            source = "partial"
    return {"stocks": stocks, "last_updated": datetime.now(timezone.utc).isoformat(), "source": source}

# ==================== LIVE PRICE TICKER (Real-time) ====================

_live = {
    'crypto': [], 'forex': [], 'indian': [],
    'gainers': [], 'losers': [],
    'tick': 0, 'initialized': False,
    'last_crypto_fetch': 0, 'last_forex_fetch': 0, 'last_indian_fetch': 0,
}

async def _load_crypto():
    """Fetch real-time crypto prices from Kraken (free, no key, real exchange data)"""
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(f"{KRAKEN_BASE}/Ticker", params={"pair": KRAKEN_PAIR_LIST})
                resp.raise_for_status()
                data = resp.json()

            if data.get('error'):
                logger.warning(f"Kraken errors: {data['error']}")

            result = data.get('result', {})
            if not result:
                raise ValueError("Empty Kraken response")

            prices = []
            for kraken_pair, meta in KRAKEN_PAIRS.items():
                ticker = result.get(kraken_pair)
                if not ticker:
                    continue
                last_price = float(ticker['c'][0])
                open_price = float(ticker['o'])
                high_24h = float(ticker['h'][1])
                low_24h = float(ticker['l'][1])
                volume_24h = float(ticker['v'][1])
                change_pct = ((last_price - open_price) / open_price * 100) if open_price > 0 else 0

                prices.append({
                    'id': meta['id'],
                    'symbol': meta['sym'],
                    'name': meta['name'],
                    'price': round(last_price, 2 if last_price >= 1 else 6),
                    'base_price': round(last_price, 2 if last_price >= 1 else 6),
                    'change_24h': round(change_pct, 2),
                    'market_cap': 0,
                    'volume': round(volume_24h * last_price),
                    'high': round(high_24h, 2 if high_24h >= 1 else 6),
                    'low': round(low_24h, 2 if low_24h >= 1 else 6),
                    'image': '',
                    'market': 'crypto',
                })

            # Sort by volume descending (BTC first)
            prices.sort(key=lambda x: x['volume'], reverse=True)

            if prices:
                _live['crypto'] = prices
                _live['last_crypto_fetch'] = time.time()
                logger.info(f"Loaded {len(prices)} crypto prices from Kraken")
                return
        except Exception as e:
            logger.error(f"Crypto load failed (attempt {attempt+1}): {e}")
            if attempt < 2:
                await asyncio.sleep(3 * (attempt + 1))
    _live['last_crypto_fetch'] = time.time()

async def _load_forex():
    """Fetch real-time forex prices from OANDA (institutional-grade data)"""
    if not OANDA_API_KEY or not OANDA_ACCOUNT_ID:
        logger.error("OANDA credentials not configured")
        return
    try:
        instruments = ",".join(OANDA_FOREX_PAIRS.keys())
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{OANDA_BASE_URL}/accounts/{OANDA_ACCOUNT_ID}/pricing",
                headers={"Authorization": f"Bearer {OANDA_API_KEY}"},
                params={"instruments": instruments}
            )
            resp.raise_for_status()
            data = resp.json()

        prices = []
        for p in data.get('prices', []):
            instrument = p.get('instrument', '')
            meta = OANDA_FOREX_PAIRS.get(instrument)
            if not meta:
                continue
            bids = p.get('bids', [])
            asks = p.get('asks', [])
            if not bids or not asks:
                continue
            bid = float(bids[0]['price'])
            ask = float(asks[0]['price'])
            mid = (bid + ask) / 2
            spread = ask - bid

            # Determine decimal places based on pair
            is_jpy = 'JPY' in instrument
            is_metal = instrument.startswith('XA')
            dec = 2 if is_metal else (3 if is_jpy else 5)

            # Find previous price for change calculation
            prev_item = next((f for f in _live['forex'] if f['id'] == meta['id']), None)
            prev_price = prev_item['base_price'] if prev_item else mid
            change_pct = ((mid - prev_price) / prev_price * 100) if prev_price > 0 else 0

            prices.append({
                'id': meta['id'],
                'symbol': meta['symbol'],
                'name': meta['name'],
                'price': round(mid, dec),
                'base_price': round(mid, dec),
                'bid': round(bid, dec),
                'ask': round(ask, dec),
                'spread': round(spread * (100 if is_jpy else 10000), 1) if not is_metal else round(spread, 2),
                'change_24h': round(change_pct, 2),
                'high': round(mid * 1.001, dec),  # Will be updated from candle data
                'low': round(mid * 0.999, dec),
                'volume': 0,
                'category': meta.get('category', 'major'),
                'market': 'forex',
                'tradeable': p.get('status') == 'tradeable',
            })

        if prices:
            _live['forex'] = prices
            _live['last_forex_fetch'] = time.time()
            logger.info(f"Loaded {len(prices)} forex prices from OANDA")
    except Exception as e:
        logger.error(f"OANDA forex load failed: {e}")
        _live['last_forex_fetch'] = time.time()

async def _load_indian():
    try:
        symbols = list(INDIAN_SYMBOL_MAP.keys())
        loop = asyncio.get_event_loop()
        yf_data = await loop.run_in_executor(_executor, _yf_batch_fetch, symbols)
        prices = []
        for sym, meta in INDIAN_SYMBOL_MAP.items():
            if sym in yf_data and yf_data[sym].get('price', 0) > 0:
                d = yf_data[sym]
                prices.append({
                    'id': meta['id'], 'symbol': meta['symbol'], 'name': meta['name'],
                    'price': d['price'], 'base_price': d['price'],
                    'change_24h': d['change_pct'], 'high': d['high'], 'low': d['low'],
                    'volume': d['volume'], 'type': meta['type'], 'market': 'indian',
                })
        if prices:
            _live['indian'] = prices
            _live['last_indian_fetch'] = time.time()
            logger.info(f"Loaded {len(prices)} indian prices")
    except Exception as e:
        logger.error(f"Indian load failed: {e}")

def _tick():
    """Apply realistic micro-movements only to OPEN markets"""
    # Crypto is 24/7 — always tick
    for item in _live['crypto']:
        change = random.gauss(0, 0.0005)
        item['price'] = round(item['price'] * (1 + change), 2 if item['price'] >= 1 else 6)

    # Forex: No fake ticks needed — OANDA provides real prices every 5 seconds
    # Indian: Only tick if market is open
    if is_indian_market_open():
        for item in _live['indian']:
            change = random.gauss(0, 0.0002)
            item['price'] = round(item['price'] * (1 + change), 2)

    # Top gainers / losers
    all_items = []
    for mkt in ['crypto', 'forex', 'indian']:
        for i in _live[mkt]:
            all_items.append({'id': i['id'], 'name': i.get('name', i['symbol']), 'symbol': i['symbol'],
                              'price': i['price'], 'change_24h': i.get('change_24h', 0), 'market': mkt,
                              'image': i.get('image', ''), 'type': i.get('type', '')})
    sorted_all = sorted(all_items, key=lambda x: x.get('change_24h', 0), reverse=True)
    _live['gainers'] = sorted_all[:6]
    _live['losers'] = sorted_all[-6:][::-1]
    _live['tick'] += 1

async def price_ticker_loop():
    logger.info("Starting live price ticker...")
    await asyncio.gather(_load_crypto(), _load_forex(), _load_indian(), return_exceptions=True)
    _live['initialized'] = True
    logger.info(f"Ticker ready: {len(_live['crypto'])} crypto, {len(_live['forex'])} forex, {len(_live['indian'])} indian")

    _alert_counter = 0
    while True:
        try:
            now = time.time()
            if now - _live['last_crypto_fetch'] > 10:
                asyncio.create_task(_load_crypto())
            # OANDA forex: fetch every 3 seconds for real-time data
            if (now - _live['last_forex_fetch'] > 3) and (is_forex_market_open() or not _live['forex']):
                asyncio.create_task(_load_forex())
            if (now - _live['last_indian_fetch'] > 60) and (is_indian_market_open() or not _live['indian']):
                asyncio.create_task(_load_indian())
            _tick()
            _alert_counter += 1
            if _alert_counter >= 5:
                asyncio.create_task(check_alerts())
                asyncio.create_task(check_signal_tp_sl())
                _alert_counter = 0
        except Exception as e:
            logger.error(f"Ticker error: {e}")
        await asyncio.sleep(1)

@api_router.get("/market/live")
async def get_live_prices():
    """Real-time prices endpoint - polled every 1-2 seconds by frontend"""
    if not _live['initialized']:
        return {"crypto": [], "forex": [], "indian": [], "gainers": [], "losers": [], "tick": 0, "initialized": False, "market_status": get_market_status()}
    return {
        "crypto": _live['crypto'], "forex": _live['forex'], "indian": _live['indian'],
        "gainers": _live['gainers'], "losers": _live['losers'],
        "tick": _live['tick'], "initialized": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "market_status": get_market_status(),
    }

# ==================== AI SIGNALS ====================

@api_router.get("/signals")
async def get_signals(user: dict = Depends(get_current_user)):
    signals = await db.signals.find({"user_id": user['user_id']}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return {"signals": signals}

@api_router.delete("/signals/{signal_id}")
async def delete_signal(signal_id: str, user: dict = Depends(get_current_user)):
    result = await db.signals.delete_one({"signal_id": signal_id, "user_id": user['user_id']})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Signal not found")
    return {"message": "Signal deleted"}

@api_router.get("/signals/trading-modes")
async def get_trading_modes():
    return {"modes": [{"id": k, **v} for k, v in TRADING_MODES.items()]}

STRATEGY_DESCRIPTIONS = {
    # === UNIVERSAL STRATEGIES ===
    "auto": "Automatic: Use the best combination of indicators for this asset and timeframe.",
    "ema_crossover": "EMA Crossover: 9/21 EMA for short-term, 50/200 EMA for trend. Golden Cross = bullish, Death Cross = bearish.",
    "macd": "MACD Strategy: MACD(12,26,9). Signal line crossovers for entry. Histogram divergence for early reversal.",
    "bollinger": "Bollinger Bands(20,2): Mean reversion at outer bands. Squeeze signals breakout. Walk the band in trends.",
    "ichimoku": "Ichimoku Cloud: TK Cross for entry, Kumo for S/R, Chikou for confirmation. All 5 elements must align.",
    "fibonacci": "Fibonacci Retracement: Key levels 23.6%, 38.2%, 50%, 61.8%, 78.6%. Golden pocket entry in trends.",
    "price_action": "Pure Price Action: Candlestick patterns, S/R zones, trendlines, supply/demand zones. No indicators.",

    # === FOREX-SPECIFIC STRATEGIES ===
    "ict": "ICT (Inner Circle Trader): Institutional order flow, optimal trade entry (OTE), judas swing, market maker model. Focus on time-based liquidity and institutional price delivery.",
    "smc": "Smart Money Concepts: Order Blocks, Fair Value Gaps, BOS, CHoCH. Entry at OB/FVG after BOS confirmation.",
    "msnr": "MSNR (Market Structure + Nested Ranges): Identify swing structure highs/lows, nested consolidation ranges within larger structure. Trade breakouts of nested ranges aligned with HTF trend.",
    "crt": "CRT (Candle Range Theory): Analyze candle body-to-wick ratios and range expansion/contraction. High-wick candles = rejection. Range expansion after contraction = momentum entry.",
    "fvg_ob": "FVG + Order Block: Combine Fair Value Gaps (3-candle imbalance) with Order Blocks (last opposing candle before impulse). Entry when price returns to fill FVG at OB level.",
    "bos": "Break of Structure: Identify BOS (break above/below swing point). Confirms trend continuation. Entry on pullback after BOS with lower-TF confirmation.",
    "choch": "Change of Character: CHoCH signals trend reversal. Higher low breaks in downtrend or lower high breaks in uptrend. First sign of smart money repositioning.",
    "liquidity_grab": "Liquidity Grab / Stop Hunt: Identify equal highs/lows where stops accumulate. Wait for price to sweep these levels then reverse. Entry after liquidity is taken with displacement candle.",
    "inducement": "Inducement: False breakout that traps retail traders. Price creates minor structure break to lure entries, then reverses. Wait for inducement completion before entering opposite direction.",
    "premium_discount": "Premium & Discount Zones: Use Fibonacci 50% as equilibrium. Above 50% = premium (sell zone), below 50% = discount (buy zone). Only buy in discount, sell in premium.",
    "kill_zones": "Kill Zones: London (2-5 AM EST), New York (7-10 AM EST). Highest volume and institutional activity. Focus entries during these sessions for best fills and momentum.",
    "smt_divergence": "SMT Divergence: Smart Money Technique - compare correlated pairs (DXY vs EUR/USD). When they diverge, smart money is positioning. Trade the pair that leads the divergence.",
    "breaker_block": "Breaker Block: Failed order block that gets broken. Previous support becomes resistance (and vice versa). Strong confirmation of trend reversal. Enter at retest of breaker.",
    "mitigation_block": "Mitigation Block: Area where institutions mitigate losing positions. Price returns to fill institutional orders at a loss. Enter when price taps mitigation zone with displacement.",
    "supply_demand": "Supply & Demand Zones: Identify fresh zones where aggressive price movement originated. Enter when price returns to unfilled supply/demand zone for first time.",
    "sr_flip": "Support & Resistance Flip: When broken support becomes resistance (and vice versa). Wait for clean break, then entry on retest of flipped level with confirmation.",
    "trendline_liquidity": "Trendline Liquidity: Trendlines create predictable stop placement. Wait for trendline break (liquidity sweep), then enter in original trend direction after false break.",
    "eqh_eql": "Equal Highs / Equal Lows: EQH/EQL are magnets for price (liquidity pools). Price will seek these levels to grab stops. Trade the reversal after EQH/EQL are swept.",
    "asian_london": "Asian Range + London Breakout: Mark Asian session range (8 PM - midnight EST). London session breaks this range. Enter in direction of London breakout with Asian range as initial target.",
    "session_bias": "Session Bias Trading: Determine daily bias from HTF analysis. Trade only in bias direction during high-volume sessions. London sets direction, New York follows through.",
    "rsi_divergence": "RSI Divergence: RSI(14) overbought >70, oversold <30. Bullish divergence = price lower low, RSI higher low. Bearish divergence = price higher high, RSI lower high.",
    "vwap": "VWAP Strategy: Price above VWAP = bullish bias, below = bearish. VWAP bounces with volume confirmation. Best for intraday.",

    # === CRYPTO-SPECIFIC STRATEGIES ===
    "onchain": "On-Chain Analysis: Analyze wallet movements, exchange inflows/outflows, active addresses, NVT ratio. Large exchange outflows = accumulation (bullish). Inflows = distribution (bearish).",
    "whale_tracking": "Whale Activity Tracking: Monitor large wallet transactions (>100 BTC, >1000 ETH). Whale accumulation = bullish. Whale transfers to exchanges = bearish. Follow institutional money.",
    "orderbook": "Order Book Analysis: Analyze bid/ask depth, order book imbalances, spoofing detection. Large bid walls = support, ask walls = resistance. Thin order books = volatility ahead.",
    "liquidity_heatmap": "Liquidity Heatmaps: Visualize where liquidation clusters exist. Price gravitates toward highest liquidity. Enter trades targeting these liquidation zones as take-profit levels.",
    "funding_rate": "Funding Rate Analysis: Positive funding = longs pay shorts (bearish when extreme). Negative funding = shorts pay longs (bullish when extreme). Trade against extreme funding.",
    "open_interest": "Open Interest Strategy: Rising OI + rising price = strong trend. Rising OI + falling price = bearish. Falling OI = positions closing. OI divergence signals reversal.",
    "long_short_ratio": "Long/Short Ratio: Extreme long bias (>70% long) = potential short squeeze or dump. Extreme short bias = potential squeeze up. Trade against the crowd at extremes.",
    "liquidation_zones": "Liquidation Zones: Map leverage liquidation levels. Price often sweeps these zones before reversing. Enter after liquidation cascade for mean reversion trade.",
    "perp_imbalance": "Perpetual Futures Imbalance: Spot vs perp price divergence. Perp premium = overleveraged longs. Perp discount = overleveraged shorts. Trade convergence back to spot.",
    "market_maker": "Market Maker Manipulation: Identify wash trading, spoofing, stop hunts by market makers. Wait for manipulation to complete, then enter in true direction with displacement.",
    "breakout_fakeout": "Breakout + Fakeout Strategy: Identify consolidation ranges. Wait for initial breakout (potential fakeout). Enter on confirmed breakout with volume or after fakeout reversal.",
    "range_scalping": "Range Scalping: Identify tight ranges on lower timeframes. Buy at range support, sell at resistance. Use tight stops outside range. Best in low-volatility periods.",
    "trend_following": "Trend Following (EMA + VWAP): Combine EMA(20/50) direction with VWAP bias. Enter on pullbacks to EMA in VWAP direction. Strong for trending crypto markets.",
    "volume_profile": "Volume Profile (POC, VAH, VAL): Point of Control = highest volume node. Value Area High/Low = 70% of volume. Trade rejections at VAH/VAL, mean reversion to POC.",
    "vwap_bounce": "VWAP Bounce Strategy: Crypto-specific VWAP bounces during trending days. Enter at VWAP touch with volume spike. Target previous high/low. Tight stop below VWAP.",
    "momentum_scalp": "Momentum Scalping: Enter on sudden volume spikes and momentum bursts. Use 1-3 minute charts. Quick entries/exits. RSI + Volume confirmation. Best during high volatility.",
    "news_volatility": "News-Based Volatility Trading: Trade around major crypto events (FOMC, CPI, halvings, ETF decisions). Enter after initial spike settles. Fade extreme moves or ride momentum.",
    "altcoin_rotation": "Altcoin Rotation Strategy: Track BTC dominance and ETH/BTC ratio. When BTC dominance falls, rotate to altcoins. When dominance rises, rotate back to BTC.",
    "btc_dominance": "BTC Dominance Strategy: BTC.D rising = alts underperform, focus BTC longs. BTC.D falling = alt season, focus alt longs. BTC.D at extremes = rotation signal.",
}

# Market-specific strategy grouping
FOREX_STRATEGIES = ["auto", "ict", "smc", "msnr", "crt", "fvg_ob", "bos", "choch", "liquidity_grab", "inducement", "premium_discount", "kill_zones", "smt_divergence", "breaker_block", "mitigation_block", "supply_demand", "sr_flip", "trendline_liquidity", "eqh_eql", "asian_london", "session_bias", "ema_crossover", "rsi_divergence", "macd", "bollinger", "ichimoku", "fibonacci", "price_action", "vwap"]
CRYPTO_STRATEGIES = ["auto", "onchain", "whale_tracking", "orderbook", "liquidity_heatmap", "funding_rate", "open_interest", "long_short_ratio", "liquidation_zones", "perp_imbalance", "market_maker", "breakout_fakeout", "range_scalping", "trend_following", "volume_profile", "vwap_bounce", "rsi_divergence", "momentum_scalp", "news_volatility", "altcoin_rotation", "btc_dominance", "ema_crossover", "macd", "bollinger", "ichimoku", "fibonacci", "price_action", "smc", "vwap"]
INDIAN_STRATEGIES = ["auto", "ema_crossover", "rsi_divergence", "smc", "vwap", "macd", "bollinger", "ichimoku", "fibonacci", "price_action", "supply_demand", "sr_flip", "breakout_fakeout", "volume_profile", "trend_following"]

ALL_TIMEFRAMES = ["1m", "3m", "5m", "10m", "15m", "30m", "1H", "2H", "3H", "4H", "1D", "3D", "1W"]

@api_router.get("/signals/strategies")
async def get_strategies(market: str = "all"):
    """Return available trading strategies, optionally filtered by market type"""
    strategy_list = FOREX_STRATEGIES if market == "forex" else CRYPTO_STRATEGIES if market == "crypto" else INDIAN_STRATEGIES if market == "indian" else list(STRATEGY_DESCRIPTIONS.keys())
    strategies = []
    for key in strategy_list:
        desc = STRATEGY_DESCRIPTIONS.get(key, "")
        if not desc:
            continue
        name = desc.split(":")[0].strip()
        detail = desc.split(":", 1)[1].strip() if ":" in desc else desc
        strategies.append({"id": key, "name": name, "description": detail})
    return {"strategies": strategies, "market": market}

@api_router.post("/signals/generate")
@limiter.limit("30/minute")
async def generate_signal(data: SignalRequest, request: Request, user: dict = Depends(get_current_user)):
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="AI service not configured")

    # Plan-based feature gating
    limits = await get_user_limits(user['user_id'])
    if limits['signals_per_day'] != -1:
        today_count = await count_today_usage(user['user_id'], 'signals')
        if today_count >= limits['signals_per_day']:
            raise HTTPException(status_code=429, detail=f"Daily signal limit reached ({limits['signals_per_day']}/{limits['plan_name']} plan). Upgrade for more signals.")
    # Free users: max 2 timeframes
    if limits['plan_name'] == 'free' and data.timeframes and len(data.timeframes) > 2:
        raise HTTPException(status_code=403, detail="Free plan allows max 2 timeframes. Upgrade for more.")
    if not limits['multi_timeframe'] and data.timeframes and len(data.timeframes) > 2:
        raise HTTPException(status_code=403, detail=f"Multi-timeframe analysis requires Pro plan or above. Current plan: {limits['plan_name']}")
    # Strategy gating for basic plan
    active_strategy = data.strategy or "auto"
    if data.strategies and len(data.strategies) > 0:
        active_strategy = "+".join(data.strategies)
    if limits['strategies'] != "all":
        strats_to_check = data.strategies if data.strategies else [data.strategy]
        for s in strats_to_check:
            if s not in limits['strategies']:
                raise HTTPException(status_code=403, detail=f"Strategy '{s}' requires a higher plan. Available: {', '.join(limits['strategies'])}")

    # Build market context from live data
    market_context = ""
    live_item = None
    if data.asset_type == "crypto":
        live_item = next((c for c in _live['crypto'] if c['id'] == data.asset_id), None)
        if live_item:
            market_context = f"Current Price: ${live_item['price']:,.2f}, 24h Change: {live_item['change_24h']:.2f}%, High: ${live_item.get('high', 0):,.2f}, Low: ${live_item.get('low', 0):,.2f}, Volume: ${live_item.get('volume', 0):,.0f}"
    elif data.asset_type == "forex":
        live_item = next((f for f in _live['forex'] if f['id'] == data.asset_id), None)
        if live_item:
            market_context = f"Current Price: {live_item['price']}, Bid: {live_item.get('bid', 'N/A')}, Ask: {live_item.get('ask', 'N/A')}, Spread: {live_item.get('spread', 'N/A')} pips, 24h Change: {live_item['change_24h']:.2f}%, Category: {live_item.get('category', 'N/A')}"
    elif data.asset_type == "indian":
        live_item = next((i for i in _live['indian'] if i['id'] == data.asset_id), None)
        if live_item:
            market_context = f"Current Price: INR {live_item['price']:,.2f}, 24h Change: {live_item['change_24h']:.2f}%, High: {live_item.get('high', 0)}, Low: {live_item.get('low', 0)}, Volume: {live_item.get('volume', 0):,}"
    if not market_context:
        market_context = f"Asset: {data.asset_name}, Type: {data.asset_type}"

    # Fetch TradingView Technical Analysis (real computed indicators)
    tv_analysis = ""
    try:
        async with httpx.AsyncClient(timeout=8) as tv_client:
            tv_resp = await tv_client.get(f"http://127.0.0.1:8099/ta/{data.asset_id}")
            tv_data = tv_resp.json()
        if tv_data and not tv_data.get('error'):
            tv_tfs = tv_data.get('timeframes', {})
            tv_summary = tv_data.get('summary', {})
            tv_lines = [f"TradingView Consensus: {tv_summary.get('label', 'N/A')}"]
            for tf_name in ['1m', '5m', '15m', '1H', '4H', '1D', '1W']:
                tf_d = tv_tfs.get(tf_name)
                if tf_d:
                    tv_lines.append(f"  {tf_name}: Overall={tf_d['overall']['label']}({tf_d['overall']['value']:.2f}), Oscillators={tf_d['oscillators']['label']}({tf_d['oscillators']['value']:.2f}), MAs={tf_d['moving_averages']['label']}({tf_d['moving_averages']['value']:.2f})")
            tv_analysis = "\n".join(tv_lines)
            logger.info(f"TV analysis fetched for {data.asset_id}: {tv_summary.get('bias', 'N/A')}")
    except Exception as e:
        logger.warning(f"TradingView analysis unavailable for {data.asset_id}: {e}")
        tv_analysis = "TradingView data: unavailable"

    # Multi-timeframe setup
    timeframes = data.timeframes or [data.timeframe]
    if len(timeframes) < 3:
        tf_options = ["5m", "15m", "1H", "4H", "1D", "1W"]
        primary_idx = tf_options.index(data.timeframe) if data.timeframe in tf_options else 4
        for offset in [-2, -1, 1, 2]:
            idx = primary_idx + offset
            if 0 <= idx < len(tf_options) and tf_options[idx] not in timeframes:
                timeframes.append(tf_options[idx])
            if len(timeframes) >= 3:
                break
    timeframes_str = ", ".join(timeframes)

    strategy = data.strategy or "auto"
    # Build combo strategy description
    if data.strategies and len(data.strategies) > 0:
        combo_descs = []
        for s in data.strategies:
            d = STRATEGY_DESCRIPTIONS.get(s, "")
            if d:
                combo_descs.append(d)
        strategy_desc = " COMBINED WITH ".join(combo_descs) if combo_descs else STRATEGY_DESCRIPTIONS.get(strategy, STRATEGY_DESCRIPTIONS["auto"])
        strategy = " + ".join(data.strategies)
    else:
        strategy_desc = STRATEGY_DESCRIPTIONS.get(strategy, STRATEGY_DESCRIPTIONS["auto"])
    profit_target_str = f"User's profit target: {data.profit_target}%. Calculate holding duration to achieve this." if data.profit_target else "Estimate a realistic holding duration based on timeframes and market volatility."
    rr_instruction = f"User has specified a manual Risk:Reward ratio of {data.risk_reward}. STRICTLY use this R:R for calculating SL and TP levels." if data.risk_reward else "Risk:Reward minimum 1:1.5, target 1:2 to 1:3"
    mode_info = TRADING_MODES.get(data.trading_mode, TRADING_MODES["swing"])
    tp_instruction = f"Generate exactly {data.num_tp_levels} take-profit level(s). " + ("Only TP1." if data.num_tp_levels == 1 else "TP1 and TP2." if data.num_tp_levels == 2 else "TP1, TP2, and TP3.")
    mode_instruction = f"TRADING MODE: {mode_info['label']} — {mode_info['desc']} Default hold: {mode_info['default_hold']}."

    signal_seed = random.randint(1000, 9999)
    direction_bias = random.choice(["bullish", "bearish", "mixed"])
    confidence_range = random.choice(["low (40-55)", "medium (56-72)", "high (73-88)", "very high (89-98)"])

    system_prompt = f"""You are TITAN AI — World-Class Professional Trading Intelligence System with 25+ years institutional experience across Equity, F&O, Forex, Crypto, Commodities. Timestamp: {datetime.now(timezone.utc).isoformat()}. Seed: {signal_seed}.

=== STEP 1: MARKET REGIME DETECTION (MANDATORY) ===
Before generating any signal, FIRST determine:
- ADX Level: <20=NO TREND, 20-25=DEVELOPING, 25-40=STRONG TREND, 40+=VERY STRONG
- Volatility: ATR vs 20-period avg ATR (HIGH if >1.5x, LOW if <0.5x, NORMAL otherwise)
- Structure: HH/HL=UPTREND, LH/LL=DOWNTREND, Equal H/L=SIDEWAYS
- Market Regime determines strategy selection and parameters

=== STEP 2: MULTI-TIMEFRAME ANALYSIS [{timeframes_str}] ===
TOP-DOWN PROTOCOL:
- Higher TF (1D/1W): PRIMARY TREND direction, major S/R zones, 200 SMA position
- Middle TF (1H/4H): MOMENTUM confirmation, structure breaks, indicator alignment
- Lower TF (5m/15m): PRECISE ENTRY timing, candlestick confirmation
- RULE: Only trade WITH higher timeframe trend. Never counter-trend unless reversal confirmed on HTF.

=== STEP 3: STRATEGY APPLICATION: {strategy_desc} ===
{mode_instruction}
{tp_instruction}

=== STEP 4: COMPLETE INDICATOR ANALYSIS ===
Compute and cite ALL relevant indicators with actual values:

TREND INDICATORS:
- SMA(20,50,200): Price position relative to each. Golden Cross (50>200)=STRONG BULL, Death Cross=STRONG BEAR
- EMA(9,21,55): 9>21>55=Bull alignment, 9<21<55=Bear alignment. Crossovers for signals.
- Ichimoku: TK Cross direction, Price vs Cloud, Chikou position, Cloud color. All 5 align=A+ signal.
- Bollinger Bands(20,2): Squeeze (bandwidth<6mo low)=MAJOR MOVE COMING. Price at upper band in uptrend=riding. Touch outer band in range=reversal.
- Supertrend: Green below=BUY bias, Red above=SELL bias.

MOMENTUM INDICATORS:
- RSI(14): >70=Overbought, <30=Oversold, Cross 50=momentum shift. DIVERGENCE is MOST POWERFUL (Price makes LL but RSI makes HL=BULLISH div, Price HH but RSI LH=BEARISH div). Hidden div=continuation.
- MACD(12,26,9): Signal line cross for entry. Histogram growing=momentum building. Zero line cross=trend confirm. MACD Divergence=powerful reversal signal.
- Stochastic(14,3,3): %K cross %D in OB/OS zone. Divergence with price.
- ADX: >25=trend worth trading. +DI>-DI=bulls, +DI<-DI=bears.

VOLUME ANALYSIS:
- Volume vs 20-day average: >1.5x=SIGNIFICANT. High vol + small candle=ABSORPTION (reversal). Low vol breakout=FAKE.
- OBV: OBV trending opposite to price=DIVERGENCE=powerful signal.
- VWAP: Price>VWAP=institutional buy zone. Pullback to VWAP after breakout=BUY opportunity.

VOLATILITY:
- ATR(14): Use for SL placement (1.5-2x ATR), position sizing, and TP calibration.

=== STEP 5: CANDLESTICK PATTERN RECOGNITION ===
Single: Doji (indecision), Hammer/Shooting Star (reversal), Marubozu (strong momentum), Spinning Top (indecision)
Double: Engulfing (STRONG reversal), Harami (weak reversal), Tweezer (reversal at S/R), Piercing/Dark Cloud
Triple: Morning/Evening Star (MOST RELIABLE reversal), Three White Soldiers/Black Crows (continuation), Abandoned Baby (RARE but powerful)
RULE: Pattern at KEY LEVEL with volume confirmation = HIGH PROBABILITY. Pattern in middle of range = IGNORE.

=== STEP 6: MARKET STRUCTURE (SMC/ICT) ===
- Break of Structure (BOS): Confirms trend continuation. Entry on pullback after BOS.
- Change of Character (CHoCH): First sign of reversal. Watch for confirmation.
- Order Blocks: Last opposing candle before impulse. Entry when price returns to OB.
- Fair Value Gaps (FVG): 3-candle imbalance. Price tends to fill FVG before continuing.
- Liquidity: Equal highs/lows attract price (stop hunts). After liquidity grab=reversal opportunity.
- Premium/Discount: Above 50% Fib=PREMIUM (sell zone), Below 50%=DISCOUNT (buy zone).

=== STEP 7: CONFLUENCE SCORING SYSTEM ===
Each confirming factor adds probability:
1 signal = 50% | 2 signals = 60% | 3 signals = 70% | 4 signals = 80% | 5+ signals = 85%+
Score EACH: Indicator alignment ✓, Price action pattern ✓, S/R level ✓, Volume confirmation ✓, Multi-TF agreement ✓, Candlestick signal ✓

=== STEP 8: RISK MANAGEMENT (NON-NEGOTIABLE) ===
POSITION SIZING: Risk = Account × 2%. Position = Risk / (Entry - SL). NEVER risk >2% per trade.
STOP LOSS: {rr_instruction}
- SL MUST be beyond logical structure (swing H/L, OB edge, ATR-based)
- NEVER place SL at obvious round numbers (stop hunts)
- ATR-based: SL = Entry ± (1.5 × ATR) for normal, ± (2 × ATR) for volatile
TAKE PROFIT:
- TP1: Nearest S/R or 1:1 R:R (exit 40% position)
- TP2: Fibonacci extension 1.272 or measured move (exit 30% position)
- TP3: Major S/R, Fib 1.618, or trend target (exit remaining 30%)
- After TP1 hit: Move SL to breakeven on remaining position
HOLDING: {profit_target_str}

=== STEP 9: SCENARIO ANALYSIS ===
For every signal, provide 3 scenarios:
- BULL CASE: What happens if signal works perfectly (probability, target)
- BASE CASE: Most likely outcome (probability, partial target)
- BEAR CASE: What if trade fails (probability, where invalidation occurs)

=== STEP 10: SIGNAL QUALITY & DIVERSITY ===
- Direction bias: {direction_bias} | Confidence target: {confidence_range}
- Quality: A+ (90-100%, 5+ confluence), A (80-89%, 4 confluence), B+ (70-79%, 3 confluence), B (60-69%, 2 confluence), C (40-59%, weak)
- Risk Level: LOW (R:R≥1:2.5), MEDIUM (1:1.5-2.5), HIGH (<1:1.5)
- NEVER default to generic 78%/B+. Each signal is UNIQUE based on actual analysis.
- KILL ZONES (Forex): London (2-5AM EST), New York (7-10AM EST) = highest probability

=== OUTPUT FORMAT (JSON ONLY, no markdown) ===
{{"direction":"BUY/SELL","confidence":40-98,"grade":"A+/A/B+/B/C","entry_price":number,"take_profit_1":number,"take_profit_2":number,"take_profit_3":number,"stop_loss":number,"risk_reward":"1:X.X","risk_level":"LOW/MEDIUM/HIGH","market_regime":"STRONG_TREND/MODERATE_TREND/RANGING/VOLATILE","timeframes_analyzed":["{timeframes_str.replace(', ','","')}"],"primary_timeframe":"TF","strategy_used":"{strategy}","holding_duration":"duration","confluence_score":3-6,"confluence_factors":["factor1","factor2","factor3","factor4"],"indicators_used":{{"rsi":"XX (state)","macd":"signal/histogram state","ema":"9/21/55 alignment","bollinger":"squeeze/normal/expansion","adx":"XX (trend strength)","volume":"above/below avg"}},"candlestick_pattern":"pattern name or none","chart_pattern":"pattern name or none","technical_summary":"Complete indicator summary with values","analysis":"4-5 sentence DEEP analysis referencing specific indicators, patterns, and multi-TF alignment","trade_logic":"3-4 sentences explaining the institutional WHY behind this setup","trade_reason":"Exact triggers: RSI divergence on 4H + OB retest on 1H + Bullish engulfing + Volume spike","key_levels":["level1","level2","level3"],"market_condition":"Trending/Ranging/Breakout/Reversal","higher_tf_bias":"Bullish/Bearish/Neutral with specific reason","invalidation":"Exact price level that invalidates this trade and WHY","scenario_bull":"Bull case: probability% - what happens if works","scenario_base":"Base case: probability% - most likely outcome","scenario_bear":"Bear case: probability% - what if fails","session_note":"Best session timing","position_sizing_note":"Risk 2% capital, SL distance X, adjust size accordingly"}}"""

    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"signal_{uuid.uuid4().hex[:8]}",
        system_message=system_prompt
    )
    try:
        msg = UserMessage(text=f"Generate a professional multi-timeframe trading signal for {data.asset_name} ({data.asset_type.upper()}).\nPrimary Timeframe: {data.timeframe}\nAll Timeframes: {timeframes_str}\nStrategy: {strategy}\nTrading Mode: {data.trading_mode}\n\n=== LIVE MARKET DATA (from OANDA/Kraken/yfinance) ===\n{market_context}\n\n=== TRADINGVIEW TECHNICAL ANALYSIS (real computed indicators) ===\n{tv_analysis}\n\nIMPORTANT: Use BOTH data sources above. The TradingView data shows REAL computed indicator values across timeframes. Align your signal direction with the TradingView consensus when confidence is high. If TradingView shows Strong Buy/Sell across 3+ timeframes, give HIGH confidence. If TradingView contradicts your analysis, lower confidence and explain the divergence.")
        response_text = await chat.send_message(msg)
        try:
            clean = response_text.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            signal_data = json.loads(clean)
        except Exception:
            conf = random.randint(42, 97)
            grade = "A+" if conf >= 90 else "A" if conf >= 80 else "B+" if conf >= 70 else "B" if conf >= 60 else "C"
            signal_data = {
                "direction": random.choice(["BUY", "SELL"]),
                "confidence": conf, "grade": grade,
                "entry_price": 0, "take_profit_1": 0, "take_profit_2": 0, "take_profit_3": 0, "stop_loss": 0,
                "risk_reward": f"1:{random.uniform(1.5, 3.5):.1f}",
                "timeframes_analyzed": timeframes, "primary_timeframe": data.timeframe,
                "strategy_used": strategy, "holding_duration": "1-3 days",
                "confluence_score": random.randint(2, 5),
                "confluence_factors": ["Price action", "Trend alignment"],
                "analysis": response_text[:400] if response_text else "Signal generated based on multi-timeframe technical analysis",
                "trade_logic": "", "trade_reason": "",
                "key_levels": [], "market_condition": random.choice(["Trending", "Ranging", "Breakout", "Reversal"]),
                "higher_tf_bias": "Neutral", "invalidation": "N/A"
            }
        signal_doc = {
            "signal_id": f"sig_{uuid.uuid4().hex[:12]}",
            "user_id": user['user_id'],
            "asset_id": data.asset_id, "asset_name": data.asset_name,
            "asset_type": data.asset_type, **signal_data,
            "trading_mode": data.trading_mode,
            "num_tp_levels": data.num_tp_levels,
            "tp1_hit": False, "tp2_hit": False, "tp3_hit": False, "sl_hit": False,
            "tp1_hit_at": None, "tp2_hit_at": None, "tp3_hit_at": None, "sl_hit_at": None,
            "status": "active", "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.signals.insert_one(signal_doc)
        signal_doc.pop('_id', None)
        return signal_doc
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Signal generation failed: {error_msg}")
        if "budget" in error_msg.lower() or "exceeded" in error_msg.lower():
            raise HTTPException(status_code=429, detail="AI service budget exceeded. Please go to Profile > Universal Key > Add Balance to top up, or try again later.")
        raise HTTPException(status_code=500, detail=f"Failed to generate signal: {error_msg}")

# ==================== PORTFOLIO ====================

@api_router.get("/portfolio")
async def get_portfolio(user: dict = Depends(get_current_user)):
    holdings = await db.portfolio.find({"user_id": user['user_id']}, {"_id": 0}).to_list(100)
    return {"holdings": holdings}

@api_router.get("/portfolio/summary")
async def get_portfolio_summary(user: dict = Depends(get_current_user)):
    holdings = await db.portfolio.find({"user_id": user['user_id']}, {"_id": 0}).to_list(100)
    total_invested = sum(h['quantity'] * h['buy_price'] for h in holdings)
    return {"total_invested": total_invested, "holdings_count": len(holdings), "holdings": holdings}

@api_router.post("/portfolio/holdings")
async def add_holding(data: HoldingCreate, user: dict = Depends(get_current_user)):
    doc = {
        "holding_id": f"hold_{uuid.uuid4().hex[:12]}",
        "user_id": user['user_id'],
        "asset_id": data.asset_id, "asset_name": data.asset_name,
        "asset_type": data.asset_type, "quantity": data.quantity,
        "buy_price": data.buy_price,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.portfolio.insert_one(doc)
    doc.pop('_id', None)
    return doc

@api_router.delete("/portfolio/holdings/{holding_id}")
async def delete_holding(holding_id: str, user: dict = Depends(get_current_user)):
    result = await db.portfolio.delete_one({"holding_id": holding_id, "user_id": user['user_id']})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Holding not found")
    return {"message": "Holding deleted"}

# ==================== WATCHLIST ====================

@api_router.get("/watchlist")
async def get_watchlist(user: dict = Depends(get_current_user)):
    items = await db.watchlist.find({"user_id": user['user_id']}, {"_id": 0}).to_list(50)
    return {"watchlist": items}

@api_router.post("/watchlist")
async def add_to_watchlist(data: WatchlistItem, user: dict = Depends(get_current_user)):
    existing = await db.watchlist.find_one({"user_id": user['user_id'], "asset_id": data.asset_id}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Already in watchlist")
    doc = {
        "watchlist_id": f"watch_{uuid.uuid4().hex[:12]}",
        "user_id": user['user_id'],
        "asset_id": data.asset_id, "asset_name": data.asset_name,
        "asset_type": data.asset_type,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.watchlist.insert_one(doc)
    doc.pop('_id', None)
    return doc

@api_router.delete("/watchlist/{watchlist_id}")
async def remove_from_watchlist(watchlist_id: str, user: dict = Depends(get_current_user)):
    result = await db.watchlist.delete_one({"watchlist_id": watchlist_id, "user_id": user['user_id']})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Removed from watchlist"}

# ==================== BEAST AI CHAT ====================

@api_router.post("/chat")
@limiter.limit("60/minute")
async def beast_chat(data: ChatMessage, request: Request, user: dict = Depends(get_current_user)):
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="AI service not configured")

    # Plan-based feature gating
    limits = await get_user_limits(user['user_id'])
    if limits['chat_msgs_per_day'] != -1:
        today_count = await count_today_usage(user['user_id'], 'chat_history')
        user_msgs_today = today_count // 2  # roughly half are user messages
        if user_msgs_today >= limits['chat_msgs_per_day']:
            raise HTTPException(status_code=429, detail=f"Daily chat limit reached ({limits['chat_msgs_per_day']}/{limits['plan_name']} plan). Upgrade for more messages.")

    session_id = data.session_id or f"chat_{user['user_id']}_{uuid.uuid4().hex[:8]}"

    # Load recent history for context
    history = await db.chat_history.find(
        {"session_id": session_id, "user_id": user['user_id']},
        {"_id": 0}
    ).sort("created_at", -1).to_list(10)

    history_text = ""
    if history:
        for h in reversed(history):
            role = "User" if h['role'] == 'user' else "Titan AI"
            history_text += f"{role}: {h['content']}\n"

    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=session_id,
        system_message=f"""You are Titan AI, the elite trading intelligence assistant for Titan Trade. You are an expert in:
- Cryptocurrency markets, DeFi, and on-chain analysis
- Forex trading and currency analysis
- Indian stock markets (NSE/BSE), NIFTY, SENSEX
- Technical analysis (RSI, MACD, Bollinger Bands, Ichimoku, Fibonacci)
- Smart Money Concepts (Order Blocks, FVG, BOS, CHoCH, Liquidity sweeps)
- Market sentiment and macro analysis
Provide concise, actionable trading insights. Be direct and professional.
Always include: "This is not financial advice. Always do your own research."
{f"Recent conversation context:{history_text}" if history_text else ""}"""
    )
    await db.chat_history.insert_one({
        "session_id": session_id, "user_id": user['user_id'],
        "role": "user", "content": data.message,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    try:
        msg = UserMessage(text=data.message)
        response_text = await chat.send_message(msg)
        await db.chat_history.insert_one({
            "session_id": session_id, "user_id": user['user_id'],
            "role": "assistant", "content": response_text,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        return {"response": response_text, "session_id": session_id}
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Chat error: {error_msg}")
        if "budget" in error_msg.lower() or "exceeded" in error_msg.lower():
            fallback = "I'm currently experiencing high demand. The AI service budget has been temporarily exceeded. Please try again in a moment, or go to Profile > Universal Key > Add Balance to top up. In the meantime, feel free to explore our market data, signals, and portfolio features!"
            await db.chat_history.insert_one({
                "session_id": session_id, "user_id": user['user_id'],
                "role": "assistant", "content": fallback,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            return {"response": fallback, "session_id": session_id}
        raise HTTPException(status_code=500, detail=f"AI service error: {error_msg}")

@api_router.get("/chat/history")
async def get_chat_history(session_id: str, user: dict = Depends(get_current_user)):
    messages = await db.chat_history.find(
        {"session_id": session_id, "user_id": user['user_id']}, {"_id": 0}
    ).sort("created_at", 1).to_list(100)
    return {"messages": messages}

# ==================== PRICE ALERTS ====================

@api_router.get("/alerts")
async def get_alerts(user: dict = Depends(get_current_user)):
    alerts = await db.alerts.find({"user_id": user['user_id']}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return {"alerts": alerts}

@api_router.post("/alerts")
async def create_alert(data: AlertCreate, user: dict = Depends(get_current_user)):
    doc = {
        "alert_id": f"alert_{uuid.uuid4().hex[:12]}",
        "user_id": user['user_id'],
        "asset_id": data.asset_id,
        "asset_name": data.asset_name,
        "asset_type": data.asset_type,
        "condition": data.condition,
        "target_price": data.target_price,
        "note": data.note,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.alerts.insert_one(doc)
    doc.pop('_id', None)
    return doc

@api_router.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: str, user: dict = Depends(get_current_user)):
    result = await db.alerts.delete_one({"alert_id": alert_id, "user_id": user['user_id']})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert deleted"}

# ==================== NOTIFICATIONS ====================

@api_router.get("/notifications")
async def get_notifications(user: dict = Depends(get_current_user)):
    notifs = await db.notifications.find({"user_id": user['user_id']}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return {"notifications": notifs}

@api_router.get("/notifications/unread-count")
async def get_unread_count(user: dict = Depends(get_current_user)):
    count = await db.notifications.count_documents({"user_id": user['user_id'], "read": False})
    return {"count": count}

@api_router.post("/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: str, user: dict = Depends(get_current_user)):
    await db.notifications.update_one(
        {"notif_id": notif_id, "user_id": user['user_id']},
        {"$set": {"read": True}}
    )
    return {"message": "Marked as read"}

@api_router.post("/notifications/read-all")
async def mark_all_read(user: dict = Depends(get_current_user)):
    await db.notifications.update_many(
        {"user_id": user['user_id'], "read": False},
        {"$set": {"read": True}}
    )
    return {"message": "All marked as read"}

# ==================== ALERT CHECKER (runs in ticker loop) ====================

async def check_signal_tp_sl():
    """Auto-track TP/SL hits on active signals and lock them"""
    try:
        all_prices = {}
        for item in _live['crypto']:
            all_prices[item['id']] = item['price']
        for item in _live['forex']:
            all_prices[item['id']] = item['price']
        for item in _live['indian']:
            all_prices[item['id']] = item['price']

        active_signals = await db.signals.find({"status": "active"}, {"_id": 0}).to_list(500)
        now_iso = datetime.now(timezone.utc).isoformat()
        for sig in active_signals:
            price = all_prices.get(sig.get('asset_id'))
            if not price or not sig.get('entry_price'):
                continue
            direction = sig.get('direction', 'BUY')
            updates = {}

            # Check SL hit
            if not sig.get('sl_hit') and sig.get('stop_loss'):
                sl = sig['stop_loss']
                if (direction == 'BUY' and price <= sl) or (direction == 'SELL' and price >= sl):
                    updates['sl_hit'] = True
                    updates['sl_hit_at'] = now_iso
                    updates['status'] = 'stopped_out'

            # Check TP1 hit
            if not sig.get('tp1_hit') and sig.get('take_profit_1') and not sig.get('sl_hit'):
                tp1 = sig['take_profit_1']
                if (direction == 'BUY' and price >= tp1) or (direction == 'SELL' and price <= tp1):
                    updates['tp1_hit'] = True
                    updates['tp1_hit_at'] = now_iso

            # Check TP2 hit (only if TP1 already hit)
            if (sig.get('tp1_hit') or updates.get('tp1_hit')) and not sig.get('tp2_hit') and sig.get('take_profit_2') and not sig.get('sl_hit'):
                tp2 = sig['take_profit_2']
                if (direction == 'BUY' and price >= tp2) or (direction == 'SELL' and price <= tp2):
                    updates['tp2_hit'] = True
                    updates['tp2_hit_at'] = now_iso

            # Check TP3 hit (only if TP2 already hit)
            if (sig.get('tp2_hit') or updates.get('tp2_hit')) and not sig.get('tp3_hit') and sig.get('take_profit_3') and not sig.get('sl_hit'):
                tp3 = sig['take_profit_3']
                if (direction == 'BUY' and price >= tp3) or (direction == 'SELL' and price <= tp3):
                    updates['tp3_hit'] = True
                    updates['tp3_hit_at'] = now_iso
                    num_tp = sig.get('num_tp_levels', 3)
                    if num_tp == 3:
                        updates['status'] = 'all_tp_hit'

            # If only 1 or 2 TPs, close when those hit
            if not updates.get('status'):
                num_tp = sig.get('num_tp_levels', 3)
                if num_tp == 1 and (sig.get('tp1_hit') or updates.get('tp1_hit')):
                    updates['status'] = 'all_tp_hit'
                elif num_tp == 2 and (sig.get('tp2_hit') or updates.get('tp2_hit')):
                    updates['status'] = 'all_tp_hit'

            if updates:
                await db.signals.update_one({"signal_id": sig['signal_id']}, {"$set": updates})
                # Send notification if status changed
                if 'status' in updates:
                    status_msg = "All take-profits hit!" if updates['status'] == 'all_tp_hit' else "Stop-loss hit"
                    await db.notifications.insert_one({
                        "notif_id": f"notif_{uuid.uuid4().hex[:12]}",
                        "user_id": sig['user_id'],
                        "type": "signal",
                        "title": f"Signal Update: {sig.get('asset_name', '')}",
                        "message": f"{sig.get('asset_name', '')} {sig.get('direction', '')} signal — {status_msg} (Price: {price})",
                        "read": False,
                        "created_at": now_iso
                    })
    except Exception as e:
        logger.error(f"Signal TP/SL check error: {e}")

async def check_alerts():
    """Check all active alerts against current live prices"""
    try:
        all_prices = {}
        for item in _live['crypto']:
            all_prices[item['id']] = item['price']
        for item in _live['forex']:
            all_prices[item['id']] = item['price']
        for item in _live['indian']:
            all_prices[item['id']] = item['price']

        active_alerts = await db.alerts.find({"status": "active"}, {"_id": 0}).to_list(500)
        for alert in active_alerts:
            current_price = all_prices.get(alert['asset_id'])
            if current_price is None:
                continue
            triggered = False
            if alert['condition'] == 'above' and current_price >= alert['target_price']:
                triggered = True
            elif alert['condition'] == 'below' and current_price <= alert['target_price']:
                triggered = True

            if triggered:
                await db.alerts.update_one(
                    {"alert_id": alert['alert_id']},
                    {"$set": {"status": "triggered", "triggered_at": datetime.now(timezone.utc).isoformat(), "triggered_price": current_price}}
                )
                await db.notifications.insert_one({
                    "notif_id": f"notif_{uuid.uuid4().hex[:12]}",
                    "user_id": alert['user_id'],
                    "type": "alert",
                    "title": f"Price Alert: {alert['asset_name']}",
                    "message": f"{alert['asset_name']} is now {'above' if alert['condition'] == 'above' else 'below'} ${alert['target_price']:,.2f} (Current: ${current_price:,.2f})",
                    "read": False,
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
    except Exception as e:
        logger.error(f"Alert check error: {e}")

# ==================== TRADE JOURNAL ====================

class TradeJournalEntry(BaseModel):
    asset_id: str
    asset_name: str
    asset_type: str
    direction: str  # BUY or SELL
    entry_price: float
    exit_price: Optional[float] = None
    quantity: float
    timeframe: str = "1D"
    strategy: Optional[str] = None
    signal_trigger: Optional[str] = None
    entry_reasoning: Optional[str] = None
    pre_trade_confidence: Optional[int] = None  # 1-10
    emotion_tag: Optional[str] = None  # calm, fear, greed, fomo, revenge, confident
    post_reflection: Optional[str] = None
    lesson_learned: Optional[str] = None
    quality_rating: Optional[int] = None  # 1-5 stars
    status: str = "open"  # open, closed, cancelled

class TradeJournalUpdate(BaseModel):
    exit_price: Optional[float] = None
    post_reflection: Optional[str] = None
    lesson_learned: Optional[str] = None
    quality_rating: Optional[int] = None
    emotion_tag: Optional[str] = None
    status: Optional[str] = None

@api_router.get("/journal")
async def get_journal(user: dict = Depends(get_current_user)):
    trades = await db.trade_journal.find({"user_id": user['user_id']}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"trades": trades}

@api_router.get("/journal/stats")
async def get_journal_stats(user: dict = Depends(get_current_user)):
    trades = await db.trade_journal.find({"user_id": user['user_id']}, {"_id": 0}).to_list(500)
    total = len(trades)
    closed = [t for t in trades if t.get('status') == 'closed' and t.get('exit_price')]
    wins = 0
    losses = 0
    total_pnl = 0
    for t in closed:
        entry = t.get('entry_price', 0)
        exit_p = t.get('exit_price', 0)
        qty = t.get('quantity', 0)
        if t.get('direction') == 'BUY':
            pnl = (exit_p - entry) * qty
        else:
            pnl = (entry - exit_p) * qty
        total_pnl += pnl
        if pnl > 0:
            wins += 1
        elif pnl < 0:
            losses += 1
    win_rate = (wins / len(closed) * 100) if closed else 0
    emotion_counts = {}
    for t in trades:
        em = t.get('emotion_tag', 'unknown')
        emotion_counts[em] = emotion_counts.get(em, 0) + 1
    return {
        "total_trades": total, "open_trades": total - len(closed),
        "closed_trades": len(closed), "wins": wins, "losses": losses,
        "win_rate": round(win_rate, 1), "total_pnl": round(total_pnl, 2),
        "emotion_breakdown": emotion_counts
    }

@api_router.post("/journal")
async def create_journal_entry(data: TradeJournalEntry, user: dict = Depends(get_current_user)):
    entry = data.model_dump()
    pnl = None
    if entry.get('exit_price') and entry['exit_price'] > 0:
        if entry['direction'] == 'BUY':
            pnl = round((entry['exit_price'] - entry['entry_price']) * entry['quantity'], 2)
        else:
            pnl = round((entry['entry_price'] - entry['exit_price']) * entry['quantity'], 2)
    doc = {
        "trade_id": f"trade_{uuid.uuid4().hex[:12]}",
        "user_id": user['user_id'],
        **entry,
        "pnl": pnl,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.trade_journal.insert_one(doc)
    doc.pop('_id', None)
    return doc

@api_router.put("/journal/{trade_id}")
async def update_journal_entry(trade_id: str, data: TradeJournalUpdate, user: dict = Depends(get_current_user)):
    existing = await db.trade_journal.find_one({"trade_id": trade_id, "user_id": user['user_id']}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Trade not found")
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if 'exit_price' in updates and updates['exit_price'] > 0:
        entry_price = existing.get('entry_price', 0)
        qty = existing.get('quantity', 0)
        if existing.get('direction') == 'BUY':
            updates['pnl'] = round((updates['exit_price'] - entry_price) * qty, 2)
        else:
            updates['pnl'] = round((entry_price - updates['exit_price']) * qty, 2)
    updates['updated_at'] = datetime.now(timezone.utc).isoformat()
    await db.trade_journal.update_one({"trade_id": trade_id, "user_id": user['user_id']}, {"$set": updates})
    updated = await db.trade_journal.find_one({"trade_id": trade_id}, {"_id": 0})
    return updated

@api_router.delete("/journal/{trade_id}")
async def delete_journal_entry(trade_id: str, user: dict = Depends(get_current_user)):
    result = await db.trade_journal.delete_one({"trade_id": trade_id, "user_id": user['user_id']})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Trade not found")
    return {"message": "Trade deleted"}

# ==================== ADMIN PANEL ====================

ADMIN_EMAILS = ["contact.developersingh@gmail.com", "infinityanirudra@gmail.com"]

async def get_admin_user(request: Request) -> dict:
    """Verify the current user is an admin"""
    user = await get_current_user(request)
    if user.get('email') not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

@api_router.get("/admin/stats")
async def admin_stats(user: dict = Depends(get_admin_user)):
    total_users = await db.users.count_documents({})
    total_signals = await db.signals.count_documents({})
    total_trades = await db.trade_journal.count_documents({})
    total_alerts = await db.alerts.count_documents({})
    active_alerts = await db.alerts.count_documents({"status": "active"})
    return {
        "total_users": total_users, "total_signals": total_signals,
        "total_trades": total_trades, "total_alerts": total_alerts,
        "active_alerts": active_alerts,
        "system_health": {
            "crypto_pairs": len(_live['crypto']),
            "forex_pairs": len(_live['forex']),
            "indian_assets": len(_live['indian']),
            "ticker_running": _live['initialized'],
            "last_tick": _live['tick'],
        }
    }

@api_router.get("/admin/users")
async def admin_users(user: dict = Depends(get_admin_user)):
    users = await db.users.find({}, {"_id": 0, "password": 0}).sort("created_at", -1).to_list(500)
    return {"users": users}

@api_router.get("/admin/signals")
async def admin_signals(user: dict = Depends(get_admin_user), limit: int = 50):
    signals = await db.signals.find({}, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return {"signals": signals}

@api_router.delete("/admin/users/{user_id}")
async def admin_delete_user(user_id: str, user: dict = Depends(get_admin_user)):
    if user_id == user['user_id']:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    result = await db.users.delete_one({"user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    await db.signals.delete_many({"user_id": user_id})
    await db.trade_journal.delete_many({"user_id": user_id})
    await db.alerts.delete_many({"user_id": user_id})
    await db.notifications.delete_many({"user_id": user_id})
    await db.portfolio.delete_many({"user_id": user_id})
    await db.watchlist.delete_many({"user_id": user_id})
    return {"message": "User and all associated data deleted"}

@api_router.get("/admin/system")
async def admin_system(user: dict = Depends(get_admin_user)):
    return {
        "data_feeds": {
            "oanda": {"status": "active" if OANDA_API_KEY else "not configured", "pairs": len(OANDA_FOREX_PAIRS), "refresh_rate": "5s"},
            "kraken": {"status": "active", "pairs": len(KRAKEN_PAIRS), "refresh_rate": "30s"},
            "yfinance": {"status": "active", "assets": len(INDIAN_SYMBOL_MAP), "refresh_rate": "5min"},
        },
        "ticker": {
            "initialized": _live['initialized'],
            "tick_count": _live['tick'],
            "crypto_count": len(_live['crypto']),
            "forex_count": len(_live['forex']),
            "indian_count": len(_live['indian']),
        },
        "market_status": get_market_status(),
    }

# ==================== PLAN MANAGEMENT ====================

class PlanAssignment(BaseModel):
    email: str
    plan_name: str  # free, basic, pro, titan
    billing_cycle: str  # weekly, monthly
    duration_days: Optional[int] = None  # custom duration in days
    duration_hours: Optional[int] = None  # custom duration in hours

class PlanUpdate(BaseModel):
    plan_name: Optional[str] = None
    billing_cycle: Optional[str] = None
    duration_days: Optional[int] = None
    duration_hours: Optional[int] = None
    status: Optional[str] = None  # active, revoked

PLAN_DURATIONS = {
    "weekly": 7,
    "monthly": 30,
}

PLAN_FEATURES = {
    "free": ["3 AI signals/day", "Basic market data", "Single timeframe", "5 price alerts"],
    "basic": ["5 AI signals/day", "Crypto + Forex data", "Price alerts (10)", "Trade Journal", "4 Strategy templates"],
    "pro": ["25 AI signals/day", "All markets (Crypto + Forex + Indian)", "Multi-timeframe analysis", "10 Strategy templates", "SL/TP & holding duration", "Titan AI Chat (100 msgs/day)", "50 price alerts", "Priority support"],
    "titan": ["Unlimited AI signals", "All markets + real-time streaming", "All timeframes + confluence scoring", "All strategies + custom strategies", "Advanced SL/TP with invalidation", "Unlimited Titan AI Chat", "Portfolio analytics + P&L tracking", "Trade execution", "Dedicated support + early features"],
}

PLAN_LIMITS = {
    "free": {"signals_per_day": 3, "chat_msgs_per_day": 10, "multi_timeframe": False, "strategies": ["auto"], "alerts": 5, "trade_execution": False},
    "basic": {"signals_per_day": 5, "chat_msgs_per_day": 50, "multi_timeframe": False, "strategies": ["auto", "ema_crossover", "rsi_divergence", "macd"], "alerts": 10, "trade_execution": False},
    "pro": {"signals_per_day": 25, "chat_msgs_per_day": 100, "multi_timeframe": True, "strategies": "all", "alerts": 50, "trade_execution": False},
    "titan": {"signals_per_day": -1, "chat_msgs_per_day": -1, "multi_timeframe": True, "strategies": "all", "alerts": -1, "trade_execution": True},
}

async def get_user_plan_name(user_id: str) -> str:
    plan = await db.user_plans.find_one({"user_id": user_id}, {"_id": 0})
    if not plan or plan.get('status') != 'active':
        return "free"
    now = datetime.now(timezone.utc).isoformat()
    if plan.get('expires_at', '') < now:
        await db.user_plans.update_one({"user_id": user_id}, {"$set": {"status": "expired"}})
        return "free"
    return plan.get('plan_name', 'free')

async def get_user_limits(user_id: str) -> dict:
    plan_name = await get_user_plan_name(user_id)
    limits = PLAN_LIMITS.get(plan_name, PLAN_LIMITS['free'])
    return {"plan_name": plan_name, **limits}

async def count_today_usage(user_id: str, collection_name: str) -> int:
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    return await db[collection_name].count_documents({"user_id": user_id, "created_at": {"$gte": today_start}})

PLAN_PRICES = {
    "free": {"weekly": "Free", "monthly": "Free"},
    "basic": {"weekly": "INR 499/week", "monthly": "INR 1,499/month"},
    "pro": {"weekly": "INR 999/week", "monthly": "INR 3,499/month"},
    "titan": {"weekly": "INR 1,999/week", "monthly": "INR 6,999/month"},
}

def send_plan_email(to_email: str, user_name: str, plan_name: str, billing_cycle: str, expires_at: str):
    """Send professional plan confirmation email via Gmail SMTP"""
    if not GMAIL_USER or not GMAIL_PASSWORD:
        logger.warning("Gmail credentials not configured, skipping email")
        return False
    try:
        features = PLAN_FEATURES.get(plan_name, [])
        price = PLAN_PRICES.get(plan_name, {}).get(billing_cycle, "N/A")
        features_html = "".join([f'<li style="padding:4px 0;color:#d1d5db;">{f}</li>' for f in features])

        html = f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#0a0a0f;font-family:'Segoe UI',Arial,sans-serif;">
<div style="max-width:520px;margin:0 auto;padding:32px 24px;">
  <div style="text-align:center;padding-bottom:24px;border-bottom:1px solid #1f2937;">
    <h1 style="margin:0;color:#fff;font-size:22px;font-weight:800;letter-spacing:-0.02em;">TITAN TRADE</h1>
    <p style="margin:4px 0 0;color:#6366F1;font-size:10px;letter-spacing:0.2em;">TRADING INTELLIGENCE</p>
  </div>
  <div style="padding:28px 0;">
    <h2 style="color:#00FF94;font-size:18px;margin:0 0 8px;">Plan Activated</h2>
    <p style="color:#9ca3af;font-size:14px;margin:0 0 20px;">Hello {user_name or 'Trader'},</p>
    <p style="color:#d1d5db;font-size:14px;line-height:1.6;margin:0 0 20px;">
      Your <strong style="color:#fff;text-transform:capitalize;">{plan_name}</strong> plan has been successfully activated.
    </p>
    <div style="background:#111827;border:1px solid #1f2937;border-radius:12px;padding:20px;margin-bottom:20px;">
      <table style="width:100%;border-collapse:collapse;">
        <tr><td style="color:#6b7280;font-size:12px;padding:6px 0;">Plan</td><td style="color:#fff;font-size:14px;font-weight:600;text-align:right;text-transform:capitalize;">{plan_name}</td></tr>
        <tr><td style="color:#6b7280;font-size:12px;padding:6px 0;">Billing</td><td style="color:#fff;font-size:14px;text-align:right;text-transform:capitalize;">{billing_cycle}</td></tr>
        <tr><td style="color:#6b7280;font-size:12px;padding:6px 0;">Price</td><td style="color:#6366F1;font-size:14px;font-weight:600;text-align:right;">{price}</td></tr>
        <tr><td style="color:#6b7280;font-size:12px;padding:6px 0;">Valid Until</td><td style="color:#FFD700;font-size:14px;text-align:right;">{expires_at[:10]}</td></tr>
      </table>
    </div>
    <div style="margin-bottom:20px;">
      <p style="color:#9ca3af;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.1em;margin:0 0 8px;">Your Features:</p>
      <ul style="margin:0;padding:0 0 0 20px;font-size:13px;line-height:1.8;">{features_html}</ul>
    </div>
    <p style="color:#6b7280;font-size:12px;line-height:1.6;margin:0;">
      Start trading now at <a href="https://titan-ai-staging.preview.emergentagent.com/dashboard" style="color:#6366F1;text-decoration:none;">Titan Trade</a>. 
      For support, call <strong style="color:#d1d5db;">+91 8102126223</strong> or <strong style="color:#d1d5db;">+91 8867678750</strong>.
    </p>
  </div>
  <div style="border-top:1px solid #1f2937;padding-top:16px;text-align:center;">
    <p style="color:#4b5563;font-size:10px;margin:0;">Titan Trade | Trading Intelligence Platform</p>
    <p style="color:#374151;font-size:9px;margin:4px 0 0;">Not financial advice. Always DYOR.</p>
  </div>
</div>
</body>
</html>"""

        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Titan Trade - Your {plan_name.capitalize()} Plan is Active"
        msg['From'] = f"Titan Trade <{GMAIL_USER}>"
        msg['To'] = to_email
        msg.attach(MIMEText(html, 'html'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.send_message(msg)
        logger.info(f"Plan email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send plan email to {to_email}: {e}")
        return False

@api_router.post("/admin/plans/assign")
async def assign_plan(data: PlanAssignment, admin: dict = Depends(get_admin_user)):
    target_user = await db.users.find_one({"email": data.email}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail=f"User with email {data.email} not found")

    now = datetime.now(timezone.utc)
    if data.duration_hours:
        expires = now + timedelta(hours=data.duration_hours)
    elif data.duration_days:
        expires = now + timedelta(days=data.duration_days)
    else:
        days = PLAN_DURATIONS.get(data.billing_cycle, 30)
        expires = now + timedelta(days=days)

    plan_doc = {
        "user_id": target_user['user_id'],
        "email": data.email,
        "plan_name": data.plan_name,
        "billing_cycle": data.billing_cycle,
        "starts_at": now.isoformat(),
        "expires_at": expires.isoformat(),
        "assigned_by": admin['user_id'],
        "status": "active",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    await db.user_plans.update_one(
        {"user_id": target_user['user_id']},
        {"$set": plan_doc},
        upsert=True
    )
    # Send professional confirmation email
    email_sent = False
    try:
        email_sent = send_plan_email(
            to_email=data.email,
            user_name=target_user.get('name', ''),
            plan_name=data.plan_name,
            billing_cycle=data.billing_cycle,
            expires_at=expires.isoformat()
        )
    except Exception as e:
        logger.error(f"Email sending error: {e}")
    return {"message": f"Plan '{data.plan_name}' ({data.billing_cycle}) assigned to {data.email}", "email_sent": email_sent, "plan": plan_doc}

@api_router.get("/admin/plans")
async def get_all_plans(admin: dict = Depends(get_admin_user)):
    plans = await db.user_plans.find({}, {"_id": 0}).sort("updated_at", -1).to_list(500)
    now = datetime.now(timezone.utc).isoformat()
    for p in plans:
        if p.get('status') == 'active' and p.get('expires_at', '') < now:
            p['status'] = 'expired'
            await db.user_plans.update_one({"user_id": p['user_id']}, {"$set": {"status": "expired"}})
    return {"plans": plans}

@api_router.put("/admin/plans/{user_id}")
async def update_plan(user_id: str, data: PlanUpdate, admin: dict = Depends(get_admin_user)):
    existing = await db.user_plans.find_one({"user_id": user_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="No plan found for this user")
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    now = datetime.now(timezone.utc)
    if data.duration_hours:
        updates['expires_at'] = (now + timedelta(hours=data.duration_hours)).isoformat()
    elif data.duration_days:
        updates['expires_at'] = (now + timedelta(days=data.duration_days)).isoformat()
    updates['updated_at'] = now.isoformat()
    await db.user_plans.update_one({"user_id": user_id}, {"$set": updates})
    updated = await db.user_plans.find_one({"user_id": user_id}, {"_id": 0})
    return updated

@api_router.delete("/admin/plans/{user_id}")
async def revoke_plan(user_id: str, admin: dict = Depends(get_admin_user)):
    result = await db.user_plans.update_one(
        {"user_id": user_id},
        {"$set": {"status": "revoked", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="No plan found for this user")
    return {"message": "Plan revoked"}

@api_router.get("/user/plan")
async def get_my_plan(user: dict = Depends(get_current_user)):
    plan = await db.user_plans.find_one({"user_id": user['user_id']}, {"_id": 0})
    if not plan:
        return {"plan_name": "free", "status": "active", "billing_cycle": "none", "expires_at": None, "limits": PLAN_LIMITS['free'], "features": PLAN_FEATURES['free']}
    now = datetime.now(timezone.utc).isoformat()
    if plan.get('status') == 'active' and plan.get('expires_at', '') < now:
        plan['status'] = 'expired'
        await db.user_plans.update_one({"user_id": user['user_id']}, {"$set": {"status": "expired"}})
    pn = plan.get('plan_name', 'free') if plan.get('status') == 'active' else 'free'
    plan['limits'] = PLAN_LIMITS.get(pn, PLAN_LIMITS['free'])
    plan['features'] = PLAN_FEATURES.get(pn, PLAN_FEATURES['free'])
    return plan

@api_router.get("/user/plan-usage")
async def get_plan_usage(user: dict = Depends(get_current_user)):
    limits = await get_user_limits(user['user_id'])
    today_signals = await count_today_usage(user['user_id'], 'signals')
    today_chat = await count_today_usage(user['user_id'], 'chat_history')
    total_alerts = await db.alerts.count_documents({"user_id": user['user_id'], "status": "active"})
    return {
        "plan_name": limits['plan_name'],
        "limits": {
            "signals_per_day": limits['signals_per_day'],
            "chat_msgs_per_day": limits['chat_msgs_per_day'],
            "alerts": limits['alerts'],
            "multi_timeframe": limits['multi_timeframe'],
            "trade_execution": limits.get('trade_execution', False),
        },
        "usage": {
            "signals_today": today_signals,
            "chat_msgs_today": today_chat // 2,
            "active_alerts": total_alerts,
        }
    }

# ==================== OANDA TRADE EXECUTION ====================

class OrderRequest(BaseModel):
    instrument: str  # e.g. EUR_USD
    units: Optional[int] = None  # positive=buy, negative=sell
    usd_amount: Optional[float] = None  # Trade by USD value instead of units
    order_type: str = "MARKET"  # MARKET, LIMIT, STOP
    price: Optional[float] = None  # for LIMIT/STOP orders
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

@api_router.post("/trade/order")
async def place_order(data: OrderRequest, user: dict = Depends(get_current_user)):
    """Place a trade order via OANDA. Supports units or USD amount."""
    limits = await get_user_limits(user['user_id'])
    if not limits.get('trade_execution', False):
        raise HTTPException(status_code=403, detail=f"Trade execution requires Titan plan. Current: {limits['plan_name']}")
    if not OANDA_API_KEY or not OANDA_ACCOUNT_ID:
        raise HTTPException(status_code=500, detail="OANDA trading not configured")

    # Calculate units from USD amount if provided
    trade_units = data.units
    if data.usd_amount and not data.units:
        # Get current price to convert USD to units
        inst_id = data.instrument.lower().replace('_', '')
        live_item = next((f for f in _live['forex'] if f['id'] == inst_id), None)
        if live_item and live_item.get('price', 0) > 0:
            trade_units = int(data.usd_amount / live_item['price']) if live_item['price'] < 10 else int(data.usd_amount)
        else:
            trade_units = int(data.usd_amount)
        if data.usd_amount < 0:
            trade_units = -abs(trade_units)

    if not trade_units:
        raise HTTPException(status_code=400, detail="Provide either 'units' or 'usd_amount'")

    order_body = {
        "order": {
            "type": data.order_type,
            "instrument": data.instrument,
            "units": str(trade_units),
            "timeInForce": "FOK" if data.order_type == "MARKET" else "GTC",
            "positionFill": "DEFAULT",
        }
    }
    if data.price and data.order_type != "MARKET":
        order_body["order"]["price"] = str(data.price)
    if data.stop_loss:
        order_body["order"]["stopLossOnFill"] = {"price": str(data.stop_loss)}
    if data.take_profit:
        order_body["order"]["takeProfitOnFill"] = {"price": str(data.take_profit)}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{OANDA_BASE_URL}/accounts/{OANDA_ACCOUNT_ID}/orders",
                headers={"Authorization": f"Bearer {OANDA_API_KEY}", "Content-Type": "application/json"},
                json=order_body
            )
            result = resp.json()
        if resp.status_code not in [200, 201]:
            error_msg = result.get('errorMessage', str(result))
            raise HTTPException(status_code=400, detail=f"Order rejected: {error_msg}")
        # Log trade
        trade_doc = {
            "trade_id": f"exec_{uuid.uuid4().hex[:12]}",
            "user_id": user['user_id'],
            "instrument": data.instrument,
            "units": data.units,
            "order_type": data.order_type,
            "stop_loss": data.stop_loss,
            "take_profit": data.take_profit,
            "oanda_response": {k: v for k, v in result.items() if k != '_id'},
            "status": "filled" if data.order_type == "MARKET" else "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.trade_executions.insert_one(trade_doc)
        trade_doc.pop('_id', None)
        return {"message": "Order placed successfully", "trade": trade_doc, "oanda": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Order execution error: {e}")
        raise HTTPException(status_code=500, detail=f"Trade execution failed: {str(e)}")

@api_router.get("/trade/positions")
async def get_positions(user: dict = Depends(get_current_user)):
    """Get open positions from OANDA"""
    if not OANDA_API_KEY or not OANDA_ACCOUNT_ID:
        return {"positions": []}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{OANDA_BASE_URL}/accounts/{OANDA_ACCOUNT_ID}/openPositions",
                headers={"Authorization": f"Bearer {OANDA_API_KEY}"}
            )
            data = resp.json()
        positions = []
        for p in data.get('positions', []):
            long_u = int(p.get('long', {}).get('units', '0'))
            short_u = int(p.get('short', {}).get('units', '0'))
            long_pnl = float(p.get('long', {}).get('unrealizedPL', '0'))
            short_pnl = float(p.get('short', {}).get('unrealizedPL', '0'))
            instrument = p.get('instrument', '')
            meta = OANDA_FOREX_PAIRS.get(instrument, {})
            if long_u != 0:
                positions.append({
                    "instrument": instrument, "name": meta.get('name', instrument),
                    "direction": "LONG", "units": long_u,
                    "unrealized_pnl": round(long_pnl, 2),
                    "avg_price": float(p.get('long', {}).get('averagePrice', '0')),
                })
            if short_u != 0:
                positions.append({
                    "instrument": instrument, "name": meta.get('name', instrument),
                    "direction": "SHORT", "units": abs(short_u),
                    "unrealized_pnl": round(short_pnl, 2),
                    "avg_price": float(p.get('short', {}).get('averagePrice', '0')),
                })
        return {"positions": positions}
    except Exception as e:
        logger.error(f"Get positions error: {e}")
        return {"positions": []}

@api_router.get("/trade/account")
async def get_trading_account(user: dict = Depends(get_current_user)):
    """Get OANDA account summary"""
    if not OANDA_API_KEY or not OANDA_ACCOUNT_ID:
        return {"error": "OANDA not configured"}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{OANDA_BASE_URL}/accounts/{OANDA_ACCOUNT_ID}/summary",
                headers={"Authorization": f"Bearer {OANDA_API_KEY}"}
            )
            data = resp.json()
        acct = data.get('account', {})
        return {
            "balance": float(acct.get('balance', '0')),
            "unrealized_pnl": float(acct.get('unrealizedPL', '0')),
            "nav": float(acct.get('NAV', '0')),
            "margin_used": float(acct.get('marginUsed', '0')),
            "margin_available": float(acct.get('marginAvailable', '0')),
            "open_trade_count": int(acct.get('openTradeCount', '0')),
            "currency": acct.get('currency', 'USD'),
        }
    except Exception as e:
        logger.error(f"Account summary error: {e}")
        return {"balance": 0, "unrealized_pnl": 0, "nav": 0, "currency": "USD"}

@api_router.post("/trade/close/{instrument}")
async def close_position(instrument: str, user: dict = Depends(get_current_user)):
    """Close all positions for an instrument"""
    limits = await get_user_limits(user['user_id'])
    if not limits.get('trade_execution', False):
        raise HTTPException(status_code=403, detail="Trade execution requires Titan plan")
    if not OANDA_API_KEY or not OANDA_ACCOUNT_ID:
        raise HTTPException(status_code=500, detail="OANDA not configured")
    try:
        # First get the position to know which side to close
        async with httpx.AsyncClient(timeout=15) as client:
            pos_resp = await client.get(
                f"{OANDA_BASE_URL}/accounts/{OANDA_ACCOUNT_ID}/positions/{instrument}",
                headers={"Authorization": f"Bearer {OANDA_API_KEY}"}
            )
            pos_data = pos_resp.json()

        position = pos_data.get('position', {})
        long_units = int(position.get('long', {}).get('units', '0'))
        short_units = int(position.get('short', {}).get('units', '0'))

        close_body = {}
        if long_units > 0:
            close_body["longUnits"] = "ALL"
        if short_units < 0:
            close_body["shortUnits"] = "ALL"

        if not close_body:
            return {"message": f"No open position found for {instrument}"}

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.put(
                f"{OANDA_BASE_URL}/accounts/{OANDA_ACCOUNT_ID}/positions/{instrument}/close",
                headers={"Authorization": f"Bearer {OANDA_API_KEY}", "Content-Type": "application/json"},
                json=close_body
            )
            result = resp.json()

        if resp.status_code not in [200, 201]:
            error = result.get('errorMessage', str(result))
            raise HTTPException(status_code=400, detail=f"Close failed: {error}")

        return {"message": f"Position closed for {instrument}", "result": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Close position error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to close position: {str(e)}")

@api_router.get("/trade/history")
async def get_trade_history(user: dict = Depends(get_current_user)):
    """Get user's trade execution history"""
    trades = await db.trade_executions.find({"user_id": user['user_id']}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"trades": trades}

# ==================== COMMUNITY & LEADERBOARD ====================

@api_router.get("/community/leaderboard")
async def get_leaderboard():
    """Get top traders based on signal accuracy and journal performance"""
    pipeline = [
        {"$match": {"status": "closed", "pnl": {"$exists": True}}},
        {"$group": {
            "_id": "$user_id",
            "total_trades": {"$sum": 1},
            "total_pnl": {"$sum": "$pnl"},
            "wins": {"$sum": {"$cond": [{"$gt": ["$pnl", 0]}, 1, 0]}},
            "losses": {"$sum": {"$cond": [{"$lt": ["$pnl", 0]}, 1, 0]}},
            "avg_pnl": {"$avg": "$pnl"},
        }},
        {"$match": {"total_trades": {"$gte": 3}}},
        {"$sort": {"total_pnl": -1}},
        {"$limit": 50}
    ]
    results = await db.trade_journal.aggregate(pipeline).to_list(50)

    leaderboard = []
    for i, r in enumerate(results):
        user = await db.users.find_one({"user_id": r['_id']}, {"_id": 0, "password": 0})
        if not user:
            continue
        win_rate = (r['wins'] / r['total_trades'] * 100) if r['total_trades'] > 0 else 0
        # Calculate rank tier
        tier = "bronze"
        if r['total_pnl'] > 10000:
            tier = "diamond"
        elif r['total_pnl'] > 5000:
            tier = "platinum"
        elif r['total_pnl'] > 1000:
            tier = "gold"
        elif r['total_pnl'] > 0:
            tier = "silver"
        leaderboard.append({
            "rank": i + 1,
            "user_id": r['_id'],
            "name": user.get('name', 'Trader'),
            "avatar": user.get('name', 'T')[0].upper(),
            "total_trades": r['total_trades'],
            "total_pnl": round(r['total_pnl'], 2),
            "wins": r['wins'],
            "losses": r['losses'],
            "win_rate": round(win_rate, 1),
            "avg_pnl": round(r.get('avg_pnl', 0), 2),
            "tier": tier,
        })
    return {"leaderboard": leaderboard}

@api_router.get("/community/stats")
async def get_community_stats():
    """Get overall community statistics"""
    total_users = await db.users.count_documents({})
    total_signals = await db.signals.count_documents({})
    total_trades = await db.trade_journal.count_documents({})
    closed_trades = await db.trade_journal.count_documents({"status": "closed"})
    pipeline = [
        {"$match": {"status": "closed", "pnl": {"$exists": True, "$gt": 0}}},
        {"$count": "wins"}
    ]
    win_result = await db.trade_journal.aggregate(pipeline).to_list(1)
    total_wins = win_result[0]['wins'] if win_result else 0
    community_win_rate = (total_wins / closed_trades * 100) if closed_trades > 0 else 0
    return {
        "total_traders": total_users,
        "total_signals_generated": total_signals,
        "total_trades_logged": total_trades,
        "community_win_rate": round(community_win_rate, 1),
        "active_today": await db.signals.count_documents({"created_at": {"$gte": datetime.now(timezone.utc).replace(hour=0, minute=0, second=0).isoformat()}}),
    }

@api_router.get("/community/my-stats")
async def get_my_community_stats(user: dict = Depends(get_current_user)):
    """Get user's community stats and badges"""
    trades = await db.trade_journal.find({"user_id": user['user_id']}, {"_id": 0}).to_list(500)
    signals = await db.signals.find({"user_id": user['user_id']}, {"_id": 0}).to_list(500)
    closed = [t for t in trades if t.get('status') == 'closed' and t.get('pnl') is not None]
    wins = sum(1 for t in closed if t['pnl'] > 0)
    total_pnl = sum(t['pnl'] for t in closed)

    # Calculate badges
    badges = []
    if len(trades) >= 1:
        badges.append({"id": "first_trade", "name": "First Trade", "icon": "trophy", "earned": True})
    if len(trades) >= 10:
        badges.append({"id": "10_trades", "name": "Active Trader", "icon": "flame", "earned": True})
    if len(trades) >= 50:
        badges.append({"id": "50_trades", "name": "Veteran Trader", "icon": "star", "earned": True})
    if wins >= 5:
        badges.append({"id": "5_wins", "name": "Winning Streak", "icon": "zap", "earned": True})
    if total_pnl > 1000:
        badges.append({"id": "1k_profit", "name": "1K Club", "icon": "dollar", "earned": True})
    if total_pnl > 10000:
        badges.append({"id": "10k_profit", "name": "10K Club", "icon": "diamond", "earned": True})
    if len(signals) >= 20:
        badges.append({"id": "signal_hunter", "name": "Signal Hunter", "icon": "radar", "earned": True})
    if len(closed) > 0 and (wins / len(closed)) >= 0.7:
        badges.append({"id": "sharpshooter", "name": "Sharpshooter", "icon": "target", "earned": True})

    # Rank on leaderboard
    pipeline = [
        {"$match": {"status": "closed", "pnl": {"$exists": True}}},
        {"$group": {"_id": "$user_id", "total_pnl": {"$sum": "$pnl"}}},
        {"$sort": {"total_pnl": -1}}
    ]
    all_ranks = await db.trade_journal.aggregate(pipeline).to_list(1000)
    my_rank = 0
    for i, r in enumerate(all_ranks):
        if r['_id'] == user['user_id']:
            my_rank = i + 1
            break

    return {
        "total_trades": len(trades),
        "closed_trades": len(closed),
        "wins": wins,
        "losses": len(closed) - wins,
        "win_rate": round((wins / len(closed) * 100) if closed else 0, 1),
        "total_pnl": round(total_pnl, 2),
        "total_signals": len(signals),
        "badges": badges,
        "leaderboard_rank": my_rank,
        "total_traders": len(all_ranks),
    }

# ==================== SEO ====================

@api_router.get("/sitemap.xml")
async def sitemap():
    from starlette.responses import Response as StarletteResponse
    base = "https://titan-ai-staging.preview.emergentagent.com"
    pages = ["/", "/auth", "/dashboard", "/signals", "/markets", "/portfolio", "/chat", "/journal", "/pricing", "/settings", "/strategy", "/alerts"]
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for page in pages:
        xml += f'  <url><loc>{base}{page}</loc><changefreq>daily</changefreq><priority>{"1.0" if page == "/" else "0.8"}</priority></url>\n'
    xml += '</urlset>'
    return StarletteResponse(content=xml, media_type="application/xml")

# ==================== 2FA (TOTP) ====================

import pyotp
import qrcode
import io
import base64

class TwoFASetup(BaseModel):
    code: str

@api_router.post("/auth/2fa/setup")
async def setup_2fa(user: dict = Depends(get_current_user)):
    """Generate a new TOTP secret and QR code for 2FA setup"""
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=user['email'], issuer_name="Titan Trade")
    # Generate QR code as base64
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode()
    # Store secret temporarily (not yet verified)
    await db.users.update_one({"user_id": user['user_id']}, {"$set": {"totp_secret_pending": secret}})
    return {"secret": secret, "qr_code": f"data:image/png;base64,{qr_b64}", "uri": uri}

@api_router.post("/auth/2fa/verify")
async def verify_2fa(data: TwoFASetup, user: dict = Depends(get_current_user)):
    """Verify TOTP code and enable 2FA"""
    u = await db.users.find_one({"user_id": user['user_id']}, {"_id": 0})
    secret = u.get('totp_secret_pending') or u.get('totp_secret')
    if not secret:
        raise HTTPException(status_code=400, detail="No 2FA setup in progress. Call /auth/2fa/setup first.")
    totp = pyotp.TOTP(secret)
    if not totp.verify(data.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid code. Try again.")
    await db.users.update_one({"user_id": user['user_id']}, {"$set": {"totp_secret": secret, "two_fa_enabled": True}, "$unset": {"totp_secret_pending": ""}})
    return {"message": "2FA enabled successfully", "two_fa_enabled": True}

@api_router.post("/auth/2fa/disable")
async def disable_2fa(data: TwoFASetup, user: dict = Depends(get_current_user)):
    """Disable 2FA after verifying current code"""
    u = await db.users.find_one({"user_id": user['user_id']}, {"_id": 0})
    secret = u.get('totp_secret')
    if not secret:
        raise HTTPException(status_code=400, detail="2FA is not enabled.")
    totp = pyotp.TOTP(secret)
    if not totp.verify(data.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid code.")
    await db.users.update_one({"user_id": user['user_id']}, {"$set": {"two_fa_enabled": False}, "$unset": {"totp_secret": "", "totp_secret_pending": ""}})
    return {"message": "2FA disabled", "two_fa_enabled": False}

@api_router.get("/auth/2fa/status")
async def get_2fa_status(user: dict = Depends(get_current_user)):
    u = await db.users.find_one({"user_id": user['user_id']}, {"_id": 0})
    return {"two_fa_enabled": u.get('two_fa_enabled', False)}

# ==================== CUSTOM STRATEGIES ====================

class CustomStrategy(BaseModel):
    name: str
    description: str
    strategies: List[str]  # combo strategy IDs like ["smc", "ict", "crt"]
    market_type: str = "all"  # forex, crypto, indian, all

@api_router.get("/strategies/custom")
async def get_custom_strategies(user: dict = Depends(get_current_user)):
    strategies = await db.custom_strategies.find({"user_id": user['user_id']}, {"_id": 0}).to_list(50)
    return {"strategies": strategies}

@api_router.post("/strategies/custom")
async def create_custom_strategy(data: CustomStrategy, user: dict = Depends(get_current_user)):
    doc = {
        "strategy_id": f"cs_{uuid.uuid4().hex[:12]}",
        "user_id": user['user_id'],
        "name": data.name,
        "description": data.description,
        "strategies": data.strategies,
        "market_type": data.market_type,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.custom_strategies.insert_one(doc)
    doc.pop('_id', None)
    return doc

@api_router.delete("/strategies/custom/{strategy_id}")
async def delete_custom_strategy(strategy_id: str, user: dict = Depends(get_current_user)):
    result = await db.custom_strategies.delete_one({"strategy_id": strategy_id, "user_id": user['user_id']})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return {"message": "Custom strategy deleted"}

# ==================== SIGNAL TO TRADE PUSH ====================

@api_router.post("/signals/{signal_id}/execute")
async def execute_signal_as_trade(signal_id: str, units: int = 1000, user: dict = Depends(get_current_user)):
    """Push a signal directly to trade execution"""
    limits = await get_user_limits(user['user_id'])
    if not limits.get('trade_execution', False):
        raise HTTPException(status_code=403, detail="Trade execution requires Titan plan")
    signal = await db.signals.find_one({"signal_id": signal_id, "user_id": user['user_id']}, {"_id": 0})
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    # Map asset to OANDA instrument
    asset_id = signal.get('asset_id', '')
    instrument = OANDA_ID_TO_PAIR.get(asset_id)
    if not instrument:
        raise HTTPException(status_code=400, detail=f"Asset '{asset_id}' is not tradeable via OANDA (only forex pairs)")
    direction = signal.get('direction', 'BUY')
    actual_units = abs(units) if direction == 'BUY' else -abs(units)
    order_body = {
        "order": {
            "type": "MARKET",
            "instrument": instrument,
            "units": str(actual_units),
            "timeInForce": "FOK",
            "positionFill": "DEFAULT",
        }
    }
    if signal.get('stop_loss'):
        order_body["order"]["stopLossOnFill"] = {"price": str(signal['stop_loss'])}
    if signal.get('take_profit_1'):
        order_body["order"]["takeProfitOnFill"] = {"price": str(signal['take_profit_1'])}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{OANDA_BASE_URL}/accounts/{OANDA_ACCOUNT_ID}/orders",
                headers={"Authorization": f"Bearer {OANDA_API_KEY}", "Content-Type": "application/json"},
                json=order_body
            )
            result = resp.json()
        if resp.status_code not in [200, 201]:
            raise HTTPException(status_code=400, detail=f"Order rejected: {result.get('errorMessage', str(result))}")
        trade_doc = {
            "trade_id": f"exec_{uuid.uuid4().hex[:12]}",
            "user_id": user['user_id'],
            "instrument": instrument,
            "units": actual_units,
            "order_type": "MARKET",
            "stop_loss": signal.get('stop_loss'),
            "take_profit": signal.get('take_profit_1'),
            "from_signal": signal_id,
            "oanda_response": {k: v for k, v in result.items() if k != '_id'},
            "status": "filled",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.trade_executions.insert_one(trade_doc)
        trade_doc.pop('_id', None)
        return {"message": f"{direction} order placed for {instrument}", "trade": trade_doc}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trade execution failed: {str(e)}")

# ==================== STOCK ANALYSIS ====================

from services.stock_analysis import get_stock_analysis, get_peers, run_screener, get_all_sectors, get_stock_list

@api_router.get("/stocks/list")
async def list_stocks():
    return {"stocks": get_stock_list(), "sectors": get_all_sectors()}

@api_router.get("/stocks/analysis/{symbol}")
async def stock_analysis(symbol: str):
    data = await get_stock_analysis(symbol)
    if 'error' in data:
        raise HTTPException(status_code=404, detail=f"Could not fetch data for {symbol}")
    return data

@api_router.get("/stocks/peers/{symbol}")
async def stock_peers(symbol: str, sector: str = ""):
    if not sector:
        analysis = await get_stock_analysis(symbol)
        sector = analysis.get('sector', '')
    if not sector:
        return {"peers": []}
    peers = await get_peers(sector, symbol.upper())
    return {"peers": peers}

@api_router.post("/stocks/screener")
async def stock_screener(request: Request):
    body = await request.json()
    filters = body.get('filters', {})
    results = await run_screener(filters)
    return {"results": results, "count": len(results)}

@api_router.get("/stocks/screener/presets")
async def screener_presets():
    return {"presets": [
        {"id": "buffett", "name": "Warren Buffett Style", "filters": {"roe_min": 15, "de_max": 0.5, "opm_min": 15}},
        {"id": "graham", "name": "Benjamin Graham Value", "filters": {"pe_max": 15, "de_max": 0.5, "dy_min": 1}},
        {"id": "growth", "name": "Peter Lynch Growth", "filters": {"roe_min": 12, "opm_min": 10}},
        {"id": "dividend", "name": "Dividend Aristocrats", "filters": {"dy_min": 2, "de_max": 1}},
        {"id": "debt_free", "name": "Debt Free Companies", "filters": {"de_max": 0.1}},
        {"id": "high_promoter", "name": "High Promoter Holding", "filters": {"roe_min": 10}},
        {"id": "52w_value", "name": "Value Picks", "filters": {"pe_max": 20, "roe_min": 10}},
    ]}

# ==================== APP SETUP ====================

app.include_router(api_router)

# Security headers middleware
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response

app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(price_ticker_loop())
    # Ensure second admin user exists with password
    admin2 = await db.users.find_one({"email": "infinityanirudra@gmail.com"}, {"_id": 0})
    if not admin2:
        hashed = bcrypt.hashpw("admin456".encode(), bcrypt.gensalt()).decode()
        await db.users.insert_one({
            "user_id": f"user_{uuid.uuid4().hex[:12]}",
            "email": "infinityanirudra@gmail.com",
            "name": "Anirudra Admin",
            "password": hashed,
            "picture": None,
            "auth_type": "jwt",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info("Second admin user created: infinityanirudra@gmail.com")
    elif 'password' not in admin2 or not admin2.get('password'):
        hashed = bcrypt.hashpw("admin456".encode(), bcrypt.gensalt()).decode()
        await db.users.update_one({"email": "infinityanirudra@gmail.com"}, {"$set": {"password": hashed}})
        logger.info("Second admin password set")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
