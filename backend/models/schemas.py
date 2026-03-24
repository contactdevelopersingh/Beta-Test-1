from pydantic import BaseModel
from typing import List, Optional

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
    profit_target: Optional[float] = None

class AlertCreate(BaseModel):
    asset_id: str
    asset_name: str
    asset_type: str
    condition: str
    target_price: float
    note: Optional[str] = None

class TradeJournalEntry(BaseModel):
    asset_id: str
    asset_name: str
    asset_type: str
    direction: str
    entry_price: float
    exit_price: Optional[float] = None
    quantity: float
    timeframe: str = "1D"
    strategy: Optional[str] = None
    signal_trigger: Optional[str] = None
    entry_reasoning: Optional[str] = None
    pre_trade_confidence: Optional[int] = None
    emotion_tag: Optional[str] = None
    post_reflection: Optional[str] = None
    lesson_learned: Optional[str] = None
    quality_rating: Optional[int] = None
    status: str = "open"

class TradeJournalUpdate(BaseModel):
    exit_price: Optional[float] = None
    post_reflection: Optional[str] = None
    lesson_learned: Optional[str] = None
    quality_rating: Optional[int] = None
    emotion_tag: Optional[str] = None
    status: Optional[str] = None

class PlanAssignment(BaseModel):
    email: str
    plan_name: str
    billing_cycle: str
    duration_days: Optional[int] = None
    duration_hours: Optional[int] = None

class PlanUpdate(BaseModel):
    plan_name: Optional[str] = None
    billing_cycle: Optional[str] = None
    duration_days: Optional[int] = None
    duration_hours: Optional[int] = None
    status: Optional[str] = None

class OrderRequest(BaseModel):
    instrument: str
    units: int
    order_type: str = "MARKET"
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
