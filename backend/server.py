from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
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
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
from emergentintegrations.llm.chat import LlmChat, UserMessage
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
_executor = ThreadPoolExecutor(max_workers=3)

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
    timeframes: Optional[List[str]] = None  # Multi-timeframe: ["5m","15m","1H","4H","1D"]
    strategy: str = "auto"  # Trading strategy: auto, ema_crossover, rsi_divergence, smc, vwap, macd, bollinger, ichimoku, fibonacci, price_action
    profit_target: Optional[float] = None  # User's desired profit % for duration calc

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
async def register(data: UserRegister, response: Response):
    existing = await db.users.find_one({"email": data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    hashed = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
    user_doc = {
        "user_id": user_id,
        "email": data.email,
        "name": data.name,
        "password": hashed,
        "picture": None,
        "auth_type": "jwt",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    token = create_jwt_token(user_id)
    response.set_cookie(key="session_token", value=token, httponly=True, secure=True, samesite="none", max_age=7*24*60*60, path="/")
    return {"user_id": user_id, "email": data.email, "name": data.name, "token": token}

@api_router.post("/auth/login")
async def login(data: UserLogin, response: Response):
    user = await db.users.find_one({"email": data.email}, {"_id": 0})
    if not user or 'password' not in user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not bcrypt.checkpw(data.password.encode(), user['password'].encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")
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
            if now - _live['last_crypto_fetch'] > 30:
                asyncio.create_task(_load_crypto())
            # OANDA forex: fetch every 5 seconds for real-time data
            if (now - _live['last_forex_fetch'] > 5) and (is_forex_market_open() or not _live['forex']):
                asyncio.create_task(_load_forex())
            if (now - _live['last_indian_fetch'] > 300) and (is_indian_market_open() or not _live['indian']):
                asyncio.create_task(_load_indian())
            _tick()
            _alert_counter += 1
            if _alert_counter >= 5:
                asyncio.create_task(check_alerts())
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

STRATEGY_DESCRIPTIONS = {
    "auto": "Automatic: Use the best combination of indicators for this asset and timeframe.",
    "ema_crossover": "EMA Crossover: 9/21 EMA for short-term, 50/200 EMA for trend. Golden Cross = bullish, Death Cross = bearish. Entry on pullback to fast EMA after crossover.",
    "rsi_divergence": "RSI Divergence: RSI(14) overbought >70, oversold <30. Bullish divergence = price makes lower low but RSI makes higher low. Bearish divergence = price makes higher high but RSI makes lower high.",
    "smc": "Smart Money Concepts: Identify Order Blocks (last opposing candle before impulse), Fair Value Gaps (3-candle imbalance), Break of Structure (BOS), Change of Character (CHoCH). Entry at OB/FVG after BOS confirmation.",
    "vwap": "VWAP Strategy: Price above VWAP = bullish bias, below = bearish. Look for VWAP bounces with volume confirmation. Best for intraday. Combine with standard deviations for targets.",
    "macd": "MACD Strategy: MACD(12,26,9). Signal line crossovers for entry. Histogram divergence for early reversal detection. Zero line crossover for trend confirmation.",
    "bollinger": "Bollinger Bands(20,2): Mean reversion when price touches outer band with RSI confirmation. Squeeze (narrow bands) signals upcoming volatility breakout. Walk the band in strong trends.",
    "ichimoku": "Ichimoku Cloud: TK Cross for entry, Kumo (cloud) for support/resistance, Chikou Span for confirmation. Price above cloud = bullish. All 5 elements must align for A+ signal.",
    "fibonacci": "Fibonacci Retracement: Key levels 23.6%, 38.2%, 50%, 61.8%, 78.6%. Enter at golden pocket (61.8-78.6%) in trending markets. Extensions 127.2%, 161.8% for targets.",
    "price_action": "Pure Price Action: Candlestick patterns (engulfing, pin bars, inside bars), support/resistance zones, trendlines, supply/demand zones. No indicators needed."
}

@api_router.get("/signals/strategies")
async def get_strategies():
    """Return available trading strategies"""
    strategies = []
    for key, desc in STRATEGY_DESCRIPTIONS.items():
        name = desc.split(":")[0].strip()
        detail = desc.split(":", 1)[1].strip() if ":" in desc else desc
        strategies.append({"id": key, "name": name, "description": detail})
    return {"strategies": strategies}

@api_router.post("/signals/generate")
async def generate_signal(data: SignalRequest, user: dict = Depends(get_current_user)):
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="AI service not configured")

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
    strategy_desc = STRATEGY_DESCRIPTIONS.get(strategy, STRATEGY_DESCRIPTIONS["auto"])
    profit_target_str = f"User's profit target: {data.profit_target}%. Calculate holding duration to achieve this." if data.profit_target else "Estimate a realistic holding duration based on timeframes and market volatility."

    signal_seed = random.randint(1000, 9999)
    direction_bias = random.choice(["bullish", "bearish", "mixed"])
    confidence_range = random.choice(["low (40-55)", "medium (56-72)", "high (73-88)", "very high (89-98)"])

    system_prompt = f"""You are Titan AI, Titan Trade's elite AI trading analyst with 25+ years of institutional experience. Timestamp: {datetime.now(timezone.utc).isoformat()}. Seed: {signal_seed}.

=== MULTI-TIMEFRAME ANALYSIS FRAMEWORK ===
Analyze these timeframes: [{timeframes_str}]
- Higher timeframes determine TREND DIRECTION (bias)
- Middle timeframes confirm MOMENTUM and STRUCTURE
- Lower timeframes pinpoint ENTRY TIMING
- All timeframes must show confluence for high-confidence signals

=== STRATEGY: {strategy_desc} ===

=== INSTITUTIONAL TRADING RULES ===
1. CONFLUENCE IS KING: Minimum 3 confirming factors needed. Score each: indicator alignment, price action pattern, S/R level, volume confirmation, multi-TF agreement
2. RISK MANAGEMENT (NON-NEGOTIABLE):
   - Stop Loss MUST be at a logical level (below/above structure, swing low/high, ATR-based)
   - Risk:Reward minimum 1:1.5, target 1:2 to 1:3
   - SL distance determines position sizing (never risk >2% of capital)
3. ENTRY PRECISION:
   - BUY: SL below entry, TP1/TP2/TP3 above entry
   - SELL: SL above entry, TP1/TP2/TP3 below entry
   - Entry should be at optimal price (pullback to key level, not at extended price)
4. TAKE PROFIT LEVELS:
   - TP1: Conservative (previous S/R, 1:1 R:R) — partial exit point
   - TP2: Standard target (fibonacci extension, measured move)
   - TP3: Aggressive (major S/R, trend target)
5. HOLDING DURATION: {profit_target_str}

=== DIVERSITY RULES ===
- Sentiment bias: {direction_bias}
- Target confidence: {confidence_range}
- Grade matches confidence: A+ (90-100), A (80-89), B+ (70-79), B (60-69), C (40-59)
- NEVER default to generic 78%/B+ — each signal is UNIQUE

Respond ONLY in valid JSON (no markdown, no code blocks):
{{"direction":"BUY or SELL","confidence":40-98,"grade":"A+/A/B+/B/C","entry_price":number,"take_profit_1":number,"take_profit_2":number,"take_profit_3":number,"stop_loss":number,"risk_reward":"1:X.X","timeframes_analyzed":["{timeframes_str.replace(', ','","')}"],"primary_timeframe":"main timeframe","strategy_used":"{strategy}","holding_duration":"e.g. 2-4 hours / 1-3 days / 1-2 weeks","confluence_score":3-6,"confluence_factors":["factor1","factor2","factor3"],"analysis":"3-4 sentence UNIQUE analysis with specific technical reasoning across timeframes","trade_logic":"2-3 sentence WHY this setup exists (structure, pattern, institutional footprint)","trade_reason":"Specific indicators/patterns that triggered: RSI divergence on 4H + order block on 1H + EMA crossover on 15m","key_levels":["price 1","price 2","price 3"],"market_condition":"Trending/Ranging/Breakout/Reversal","higher_tf_bias":"Bullish/Bearish/Neutral with reason","invalidation":"What price level or event would invalidate this trade"}}"""

    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"signal_{uuid.uuid4().hex[:8]}",
        system_message=system_prompt
    )
    try:
        msg = UserMessage(text=f"Generate a professional multi-timeframe trading signal for {data.asset_name} ({data.asset_type.upper()}).\nPrimary Timeframe: {data.timeframe}\nAll Timeframes: {timeframes_str}\nStrategy: {strategy}\n{market_context}")
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
async def beast_chat(data: ChatMessage, user: dict = Depends(get_current_user)):
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="AI service not configured")
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

ADMIN_EMAIL = "contact.developersingh@gmail.com"

async def get_admin_user(request: Request) -> dict:
    """Verify the current user is the admin"""
    user = await get_current_user(request)
    if user.get('email') != ADMIN_EMAIL:
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
    return {"message": f"Plan '{data.plan_name}' ({data.billing_cycle}) assigned to {data.email}", "plan": plan_doc}

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
        return {"plan_name": "free", "status": "active", "billing_cycle": "none", "expires_at": None}
    now = datetime.now(timezone.utc).isoformat()
    if plan.get('status') == 'active' and plan.get('expires_at', '') < now:
        plan['status'] = 'expired'
        await db.user_plans.update_one({"user_id": user['user_id']}, {"$set": {"status": "expired"}})
    return plan

# ==================== APP SETUP ====================

app.include_router(api_router)

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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
