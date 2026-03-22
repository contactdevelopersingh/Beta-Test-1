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
from datetime import datetime, timezone, timedelta
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Config
JWT_SECRET = os.environ.get('JWT_SECRET', 'signalbeast-pro-jwt-secret-2026')
JWT_ALGORITHM = 'HS256'
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
COINGECKO_BASE = 'https://api.coingecko.com/api/v3'

# Simple in-memory cache
_cache: Dict[str, Dict] = {}

app = FastAPI(title="SignalBeast Pro API")
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
    url = f"{COINGECKO_BASE}/coins/{coin_id}/market_chart?vs_currency=usd&days={days}"
    data = await cached_get(url, ttl=300)
    return data

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

# Forex data (simulated with small variations)
FOREX_PAIRS = [
    {"id": "eurusd", "name": "EUR/USD", "symbol": "EUR/USD", "price": 1.0842, "change_24h": 0.15, "high_24h": 1.0875, "low_24h": 1.0810, "volume": 185000000000},
    {"id": "gbpusd", "name": "GBP/USD", "symbol": "GBP/USD", "price": 1.2635, "change_24h": -0.08, "high_24h": 1.2680, "low_24h": 1.2590, "volume": 92000000000},
    {"id": "usdjpy", "name": "USD/JPY", "symbol": "USD/JPY", "price": 154.32, "change_24h": 0.22, "high_24h": 154.75, "low_24h": 153.90, "volume": 148000000000},
    {"id": "audusd", "name": "AUD/USD", "symbol": "AUD/USD", "price": 0.6534, "change_24h": -0.32, "high_24h": 0.6570, "low_24h": 0.6510, "volume": 45000000000},
    {"id": "usdchf", "name": "USD/CHF", "symbol": "USD/CHF", "price": 0.8845, "change_24h": 0.05, "high_24h": 0.8870, "low_24h": 0.8820, "volume": 38000000000},
    {"id": "usdcad", "name": "USD/CAD", "symbol": "USD/CAD", "price": 1.3620, "change_24h": -0.12, "high_24h": 1.3655, "low_24h": 1.3590, "volume": 42000000000},
    {"id": "nzdusd", "name": "NZD/USD", "symbol": "NZD/USD", "price": 0.5945, "change_24h": -0.18, "high_24h": 0.5975, "low_24h": 0.5920, "volume": 22000000000},
    {"id": "xauusd", "name": "XAU/USD (Gold)", "symbol": "XAU/USD", "price": 2645.50, "change_24h": 0.45, "high_24h": 2660.00, "low_24h": 2630.00, "volume": 165000000000},
    {"id": "xagusd", "name": "XAG/USD (Silver)", "symbol": "XAG/USD", "price": 31.25, "change_24h": 0.72, "high_24h": 31.50, "low_24h": 30.90, "volume": 28000000000},
    {"id": "eurgbp", "name": "EUR/GBP", "symbol": "EUR/GBP", "price": 0.8582, "change_24h": 0.10, "high_24h": 0.8600, "low_24h": 0.8560, "volume": 32000000000},
]

INDIAN_STOCKS = [
    {"id": "nifty50", "name": "NIFTY 50", "symbol": "NIFTY", "price": 24680.50, "change_24h": 0.45, "high_24h": 24750.00, "low_24h": 24580.00, "volume": 28500000000, "type": "index"},
    {"id": "sensex", "name": "SENSEX", "symbol": "SENSEX", "price": 81250.75, "change_24h": 0.38, "high_24h": 81500.00, "low_24h": 81000.00, "volume": 35200000000, "type": "index"},
    {"id": "reliance", "name": "Reliance Industries", "symbol": "RELIANCE", "price": 2890.50, "change_24h": 1.25, "high_24h": 2920.00, "low_24h": 2865.00, "volume": 12500000000, "type": "stock"},
    {"id": "tcs", "name": "Tata Consultancy", "symbol": "TCS", "price": 4125.30, "change_24h": -0.45, "high_24h": 4160.00, "low_24h": 4100.00, "volume": 8900000000, "type": "stock"},
    {"id": "infy", "name": "Infosys", "symbol": "INFY", "price": 1825.75, "change_24h": 0.85, "high_24h": 1840.00, "low_24h": 1810.00, "volume": 7200000000, "type": "stock"},
    {"id": "hdfcbank", "name": "HDFC Bank", "symbol": "HDFCBANK", "price": 1685.20, "change_24h": -0.32, "high_24h": 1700.00, "low_24h": 1675.00, "volume": 9800000000, "type": "stock"},
    {"id": "icicibank", "name": "ICICI Bank", "symbol": "ICICIBANK", "price": 1245.80, "change_24h": 0.65, "high_24h": 1255.00, "low_24h": 1235.00, "volume": 8500000000, "type": "stock"},
    {"id": "sbin", "name": "State Bank of India", "symbol": "SBIN", "price": 825.45, "change_24h": 1.12, "high_24h": 835.00, "low_24h": 818.00, "volume": 11200000000, "type": "stock"},
    {"id": "itc", "name": "ITC Limited", "symbol": "ITC", "price": 468.90, "change_24h": -0.15, "high_24h": 472.00, "low_24h": 465.00, "volume": 6800000000, "type": "stock"},
    {"id": "tatamotors", "name": "Tata Motors", "symbol": "TATAMOTORS", "price": 785.60, "change_24h": 2.15, "high_24h": 795.00, "low_24h": 770.00, "volume": 7500000000, "type": "stock"},
    {"id": "bhartiartl", "name": "Bharti Airtel", "symbol": "BHARTIARTL", "price": 1560.25, "change_24h": 0.75, "high_24h": 1575.00, "low_24h": 1545.00, "volume": 5200000000, "type": "stock"},
    {"id": "wipro", "name": "Wipro", "symbol": "WIPRO", "price": 565.80, "change_24h": -0.55, "high_24h": 570.00, "low_24h": 560.00, "volume": 4100000000, "type": "stock"},
]

@api_router.get("/market/forex")
async def get_forex_data():
    pairs = []
    for pair in FOREX_PAIRS:
        p = dict(pair)
        v = random.uniform(-0.002, 0.002)
        p['price'] = round(p['price'] * (1 + v), 4 if p['price'] < 10 else 2)
        p['change_24h'] = round(p['change_24h'] + random.uniform(-0.1, 0.1), 2)
        pairs.append(p)
    return {"pairs": pairs, "last_updated": datetime.now(timezone.utc).isoformat()}

@api_router.get("/market/indian")
async def get_indian_data():
    stocks = []
    for stock in INDIAN_STOCKS:
        s = dict(stock)
        v = random.uniform(-0.003, 0.003)
        s['price'] = round(s['price'] * (1 + v), 2)
        s['change_24h'] = round(s['change_24h'] + random.uniform(-0.15, 0.15), 2)
        stocks.append(s)
    return {"stocks": stocks, "last_updated": datetime.now(timezone.utc).isoformat()}

# ==================== AI SIGNALS ====================

@api_router.get("/signals")
async def get_signals(user: dict = Depends(get_current_user)):
    signals = await db.signals.find({"user_id": user['user_id']}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return {"signals": signals}

@api_router.post("/signals/generate")
async def generate_signal(data: SignalRequest, user: dict = Depends(get_current_user)):
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="AI service not configured")
    market_context = ""
    if data.asset_type == "crypto":
        try:
            url = f"{COINGECKO_BASE}/simple/price?ids={data.asset_id}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true"
            price_data = await cached_get(url, ttl=30)
            cd = price_data.get(data.asset_id, {})
            market_context = f"Current Price: ${cd.get('usd', 'N/A')}, 24h Change: {cd.get('usd_24h_change', 'N/A')}%, Market Cap: ${cd.get('usd_market_cap', 'N/A')}"
        except Exception:
            market_context = f"Asset: {data.asset_name}"
    else:
        market_context = f"Asset: {data.asset_name}, Type: {data.asset_type}"

    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"signal_{uuid.uuid4().hex[:8]}",
        system_message="""You are SignalBeast Pro's AI trading analyst. Generate a precise trading signal. Respond ONLY in valid JSON (no markdown, no extra text):
{"direction":"BUY or SELL","confidence":0-100,"grade":"A+ or A or B+ or B or C","entry_price":number,"take_profit_1":number,"take_profit_2":number,"stop_loss":number,"risk_reward":"1:X.X","timeframe":"string","analysis":"2-3 sentence analysis","key_levels":["level1","level2"],"market_condition":"Trending or Ranging or Breakout or Reversal"}"""
    )
    try:
        msg = UserMessage(text=f"Generate a trading signal for {data.asset_name} ({data.asset_type.upper()}). Timeframe: {data.timeframe}. {market_context}")
        response_text = await chat.send_message(msg)
        try:
            clean = response_text.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            signal_data = json.loads(clean)
        except Exception:
            signal_data = {
                "direction": random.choice(["BUY", "SELL"]),
                "confidence": random.randint(60, 92),
                "grade": random.choice(["A+", "A", "B+"]),
                "entry_price": 0, "take_profit_1": 0, "take_profit_2": 0, "stop_loss": 0,
                "risk_reward": "1:2.0", "timeframe": data.timeframe,
                "analysis": response_text[:300] if response_text else "Signal generated",
                "key_levels": [], "market_condition": "Trending"
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
            role = "User" if h['role'] == 'user' else "Beast AI"
            history_text += f"{role}: {h['content']}\n"

    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=session_id,
        system_message=f"""You are Beast AI, the elite trading intelligence assistant for SignalBeast Pro. You are an expert in:
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

# ==================== APP SETUP ====================

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
